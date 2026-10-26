"""Assert restore-fingerprint semantics in disposable, offline synthetic Redis.

Run on the existing Central host. No production keys are read or written.
Only the installed image identity is read from its container.
"""
import json,subprocess,time,uuid
from scripts.verify_enketo_restore import FINGERPRINT


def main():
    image=json.loads(subprocess.check_output(['docker','inspect','lastcopy-cloud-odk-enketo_redis_main-1'],timeout=15))[0]['Image']
    names=['lastcopy-redis-control-'+uuid.uuid4().hex[:12] for _ in range(2)]
    def call(name,*args):return subprocess.check_output(['docker','exec',name,'redis-cli','--json',*args],timeout=10)
    try:
        for name in names:
            subprocess.run(['docker','run','-d','--name',name,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--memory','128m','--pids-limit','32',image,'redis-server','--save','','--appendonly','no'],check=True,capture_output=True,timeout=20)
            deadline=time.monotonic()+15
            while True:
                ready=subprocess.run(['docker','exec',name,'redis-cli','PING'],capture_output=True,timeout=5)
                if ready.returncode==0 and ready.stdout.strip()==b'PONG':break
                if time.monotonic()>deadline:raise ValueError('Synthetic Redis did not start')
                time.sleep(.2)
        for i,name in enumerate(names):
            script="for j=1,600 do local n="+('j' if i==0 else '601-j')+";redis.call('HSET','survey','field'..n,'answer'..n) end;redis.call('SADD','members','b','a');redis.call('RPUSH','ordered','first','second');return 1"
            call(name,'EVAL',script,'0')
        before=[json.loads(call(name,'EVAL',FINGERPRINT,'0')) for name in names];assert before[0]==before[1]
        old="local d=redis.call('DUMP','survey');return redis.sha1hex(d)"
        dump=[json.loads(call(name,'EVAL',old,'0')) for name in names];assert dump[0]!=dump[1]
        call(names[1],'HSET','survey','field1','changed');assert json.loads(call(names[1],'EVAL',FINGERPRINT,'0'))!=before[0]
        call(names[1],'HSET','survey','field1','answer1');call(names[1],'LSET','ordered','0','second');call(names[1],'LSET','ordered','1','first')
        assert json.loads(call(names[1],'EVAL',FINGERPRINT,'0'))!=before[0]
        call(names[1],'LSET','ordered','0','first');call(names[1],'LSET','ordered','1','second')
        assert json.loads(call(names[1],'EVAL',FINGERPRINT,'0'))==before[0]
        call(names[1],'PEXPIREAT','survey','2000000000000');assert json.loads(call(names[1],'EVAL',FINGERPRINT,'0'))!=before[0]
        result={'status':'passed','real_redis':True,'synthetic_only':True,'network':'none','published_ports':0,'checks':['Hash insertion order ignored','Old DUMP fingerprint differs for equal content','Changed answer detected','List occurrence order remains significant','Absolute expiry change detected'],'production_writes':0}
    finally:
        for name in names:
            cleanup=subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=15)
            if cleanup.returncode:raise ValueError('Scratch cleanup not confirmed')
    print(json.dumps(result))


if __name__=='__main__':main()
