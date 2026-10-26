"""Verify an approved Enketo RDB in a network-isolated disposable Redis.

Run on the existing AWS host. Never starts Enketo, publishes a port or writes
to a production Redis instance. Keys remain private; only hashes are reported.
"""
import argparse,json,os,re,shutil,subprocess,tempfile,time,uuid
from pathlib import Path
from scripts.backup_databases import ENKETO_KEYS,sha


FINGERPRINT="""
local n=redis.call('DBSIZE');if n>10000 then return redis.error_reply('key limit') end
local keys=redis.call('KEYS','*');table.sort(keys);local out={};local bytes=0
local function add(v) bytes=bytes+#v;if bytes>33554432 then error('byte limit') end;out[#out+1]=#v..':'..v end
for _,k in ipairs(keys) do
 local t=redis.call('TYPE',k).ok;add(k);add(t);add(tostring(redis.call('PEXPIRETIME',k)))
 if t=='string' then add(redis.call('GET',k))
 elseif t=='hash' then
  if redis.call('HLEN',k)>10000 then error('entry limit') end
  local fields=redis.call('HKEYS',k);table.sort(fields);add(tostring(#fields))
  for _,f in ipairs(fields) do add(f);add(redis.call('HGET',k,f)) end
 elseif t=='set' then
  if redis.call('SCARD',k)>10000 then error('entry limit') end
  local values=redis.call('SMEMBERS',k);table.sort(values);add(tostring(#values));for _,v in ipairs(values) do add(v) end
 elseif t=='list' or t=='zset' then
  local count=redis.call(t=='list' and 'LLEN' or 'ZCARD',k);if count>10000 then error('entry limit') end
  local values;if t=='list' then values=redis.call('LRANGE',k,0,-1) else values=redis.call('ZRANGE',k,0,-1,'WITHSCORES') end
  add(tostring(#values));for _,v in ipairs(values) do add(v) end
 else error('unsupported Redis type') end
end
return {#keys,redis.sha1hex(table.concat(out))}
"""


def validate(stage,manifest):
    expected={'enketo/main.rdb',*('enketo/keys/'+name for name in ENKETO_KEYS)}
    if not expected<=manifest.get('files',{}).keys():raise ValueError('Missing Enketo backup scope')
    for name in sorted(expected):
        p=stage/name
        if any(x.is_symlink() or x.is_junction() for x in [p,*p.parents]):raise ValueError('Restore input contains a link')
        if not p.is_file() or not 1<=p.stat().st_size<=32*1024**2 or sha(p)!=manifest['files'][name]:
            raise ValueError('Restore input integrity/size mismatch')
        if name.startswith('enketo/keys/') and p.stat().st_size>4096:raise ValueError('Oversized generated key')
    with (stage/'enketo/main.rdb').open('rb') as source:
        if source.read(5)!=b'REDIS':raise ValueError('Invalid Redis snapshot')
    return {name:manifest['files'][name] for name in sorted(expected)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',type=Path,required=True)
    args=p.parse_args();stage=args.stage.absolute()
    manifest_path=stage/'manifest.json'
    if manifest_path.is_symlink() or manifest_path.stat().st_size>4*1024**2:raise ValueError('Invalid trusted manifest')
    manifest=json.loads(manifest_path.read_bytes());validate(stage,manifest)
    image=subprocess.check_output(['docker','inspect','--format','{{.Image}}','lastcopy-cloud-odk-enketo_redis_main-1'],text=True,timeout=15).strip()
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',image):raise ValueError('Invalid installed Redis image identity')
    name='lastcopy-restore-enketo-'+uuid.uuid4().hex[:12]
    temporary=tempfile.TemporaryDirectory(prefix='lastcopy-enketo-drill-')
    copy=Path(temporary.name)/'dump.rdb';shutil.copyfile(stage/'enketo/main.rdb',copy);os.chmod(copy,0o644)
    command=['docker','run','-d','--pull=never','--name',name,'--network','none','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges:true','--memory','128m','--pids-limit','32','--user','999:999',
        '--mount',f'type=bind,source={copy},target=/data/dump.rdb,readonly',
        image,'redis-server','--save','','--appendonly','no','--dir','/data']
    try:
        subprocess.run(command,check=True,capture_output=True,timeout=30)
        deadline=time.monotonic()+20
        while True:
            ready=subprocess.run(['docker','exec',name,'redis-cli','PING'],capture_output=True,timeout=5)
            if ready.returncode==0 and ready.stdout.strip()==b'PONG':break
            if time.monotonic()>deadline:raise ValueError('Isolated Redis did not load the snapshot')
            time.sleep(.2)
        values={}
        for label,container in [('live','lastcopy-cloud-odk-enketo_redis_main-1'),('restored',name)]:
            raw=subprocess.check_output(['docker','exec',container,'redis-cli','--json','EVAL',FINGERPRINT,'0'],timeout=15)
            result=json.loads(raw)
            if not isinstance(result,list) or len(result)!=2 or not isinstance(result[0],int) or not re.fullmatch('[a-f0-9]{40}',str(result[1])):
                raise ValueError('Invalid bounded Redis fingerprint')
            values[label]={'keys':result[0],'data_fingerprint_sha1':result[1]}
        if values['live']!=values['restored']:raise ValueError('Live Redis changed or restored state differs; no production restore attempted')
        validate(stage,manifest)
        result={'status':'passed','redis_image':image,'network':'none','published_ports':0,'fingerprints':values,
            'source_hashes_unchanged':True,'key_files_verified':len(ENKETO_KEYS),'production_writes':0,
            'scope':'RDB loading and generated-key byte integrity; not a full host or Web Form browser acceptance'}
    finally:
        # The generated name belongs only to this drill, including a lost run ACK.
        try:
            cleanup=subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=15,check=False)
            if cleanup.returncode:raise ValueError('Scratch container cleanup not confirmed')
        finally:temporary.cleanup()
    print(json.dumps(result))


if __name__=='__main__':main()
