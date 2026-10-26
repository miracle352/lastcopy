"""Encrypted database backup; private configs/keys stay on their existing host.

This is not a machine image: environment configuration and externally stored
attachments require a separate disaster-recovery procedure. Enketo is opt-in.
"""
import argparse,hashlib,json,os,re,shutil,sqlite3,subprocess,tarfile,tempfile,time
from pathlib import Path
from datetime import datetime,timezone

MAX_BYTES=2*1024**3
ENKETO_KEYS=('enketo-secret','enketo-less-secret','enketo-api-key')


def snapshot_enketo(stage,secrets_dir=Path('/var/lib/docker/volumes/lastcopy-cloud-odk_secrets/_data')):
    """Operator-approved link recovery only; no application/provider environment."""
    stage=Path(stage);secrets_dir=Path(secrets_dir)
    if any(p.is_symlink() or p.is_junction() for p in [secrets_dir,*secrets_dir.parents]):
        raise ValueError('Enketo backup does not follow links')
    files=[]
    for name in ENKETO_KEYS:
        source=secrets_dir/name
        if source.is_symlink() or not source.is_file() or not 1<=source.stat().st_size<=4096:
            raise ValueError('Invalid Enketo generated key')
        before=sha(source);target=stage/'enketo'/'keys'/name
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        if sha(target)!=before or sha(source)!=before:raise ValueError('Enketo key changed during snapshot')
        os.chmod(target,0o600);files.append(target.relative_to(stage).as_posix())
    # Linux host operation: cap the Docker client's output before it reaches disk.
    def limit_output():
        import resource
        resource.setrlimit(resource.RLIMIT_FSIZE,(32*1024**2,32*1024**2))
    target=stage/'enketo'/'main.rdb'
    with target.open('wb') as output:
        subprocess.run(['docker','exec','lastcopy-cloud-odk-enketo_redis_main-1','redis-cli','--rdb','-'],
            stdout=output,stderr=subprocess.DEVNULL,check=True,timeout=60,preexec_fn=limit_output)
    with target.open('rb') as source:header=source.read(5)
    if header!=b'REDIS' or not 9<=target.stat().st_size<=32*1024**2:raise ValueError('Invalid bounded Enketo Redis snapshot')
    files.append(target.relative_to(stage).as_posix())
    return files

def snapshot_investigations(root,stage):
    """Only immutable sealed evidence; never copy adjacent settings or credentials."""
    root=Path(root).resolve();stage=Path(stage).resolve();files=[];total=0;deadline=time.monotonic()+60
    allowed={'events.jsonl','investigation.json','publication.json','published-rows.json',
             'query-evidence.json','report.json','run-manifest.json','world.jsonl'}
    for seal in root.rglob('seals.json'):
        relative=seal.relative_to(root)
        if 'investigations' not in relative.parts:continue
        if seal.is_symlink() or seal.stat().st_size>2*1024**2:raise ValueError('Invalid investigation seal')
        seals=json.loads(seal.read_bytes())
        if not isinstance(seals,dict) or len(seals)>20000:raise ValueError('Investigation seal exceeds bound')
        for name,expected in list(seals.items())+[(seal.name,sha(seal))]:
            if (name not in allowed|{'seals.json'} and not re.fullmatch(r'(objects/[a-f0-9]{64}|queries/[a-f0-9]{64}\.json)',name)):
                raise ValueError('Unexpected sealed investigation file; private configuration is excluded')
            source=seal.parent/name
            if any(p.is_symlink() or p.is_junction() for p in [source,*source.parents] if p!=root.parent):raise ValueError('Investigation backup does not follow links')
            size=source.stat().st_size;total+=size
            if size>33554432 or total>MAX_BYTES or len(files)>=20000 or time.monotonic()>deadline:raise ValueError('Investigation backup exceeds size/time/count bound')
            target=stage/'application'/source.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
            if sha(target)!=expected or sha(source)!=expected:raise ValueError('Investigation evidence integrity changed')
            files.append(target.relative_to(stage).as_posix())
    return sorted(files)

def snapshot_databases(root,stage):
    root=Path(root).resolve();stage=Path(stage).resolve();files=[];deadline=time.monotonic()+120
    for folder,dirs,names in os.walk(root,followlinks=False):
        if any((Path(folder)/name).is_symlink() for name in dirs+names):raise ValueError('Database backup does not follow links')
        if 'lastcopy.sqlite3' not in names:continue
        source=Path(folder)/'lastcopy.sqlite3';relative=Path('application')/source.relative_to(root)
        if len(files)>=256:raise ValueError('Backup database count exceeds limit')
        target=stage/relative;target.parent.mkdir(parents=True,exist_ok=True)
        def progress(*_):
            if time.monotonic()>deadline or sum(p.stat().st_size for p in stage.rglob('*.sqlite3'))>MAX_BYTES:raise ValueError('Database backup exceeded time/size bound')
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as read,sqlite3.connect(target) as write:
            read.backup(write,pages=128,progress=progress)
            if write.execute('PRAGMA integrity_check').fetchone()!=('ok',):raise ValueError('Database snapshot integrity failed')
        files.append(relative.as_posix())
    if not files:raise ValueError('No application databases found')
    return sorted(files)

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def encrypt(source,target,recipient,openssl='openssl'):
    subprocess.run([openssl,'cms','-encrypt','-binary','-aes-256-gcm','-outform','DER','-in',str(source),'-out',str(target),'-recip',str(recipient)],check=True,timeout=60,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store',type=Path,required=True);parser.add_argument('--recipient',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--postgres-container',default='lastcopy-cloud-odk-postgres14-1')
    parser.add_argument('--include-enketo',action='store_true',help='Explicitly approved generated keys and Redis; excludes provider/application environment')
    args=parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}',args.postgres_container):raise ValueError('Invalid database container')
    output=args.output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists() or output.with_suffix('.partial').exists():raise ValueError('Backup destination already exists')
    if shutil.disk_usage(output.parent).free<5*1024**3:raise ValueError('Backup requires a 5 GiB free-space reserve')
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix='.lastcopy-backup-',dir=output.parent) as temporary:
        stage=Path(temporary);files=snapshot_databases(args.store,stage);database_count=len(files)
        evidence=snapshot_investigations(args.store,stage);files+=evidence
        if args.include_enketo:files+=snapshot_enketo(stage)
        dump=stage/'central.pgdump'
        with dump.open('wb') as stream:
            subprocess.run(['docker','exec',args.postgres_container,'pg_dump','-U','odk','-d','odk','-Fc'],stdout=stream,stderr=subprocess.PIPE,check=True,timeout=180)
        with dump.open('rb') as stream:header=stream.read(5)
        if dump.stat().st_size>MAX_BYTES or header!=b'PGDMP':raise ValueError('Invalid/oversized Central database backup')
        files.append(dump.name)
        if sum((stage/name).stat().st_size for name in files)>MAX_BYTES:raise ValueError('Aggregate backup exceeds 2 GiB')
        manifest={'created_at':datetime.now(timezone.utc).isoformat(),'files':{name:sha(stage/name) for name in files},'environment_and_provider_keys_included':False,'enketo_link_state_included':args.include_enketo,'scope':'SQLite ledgers, sealed investigation evidence and Central PostgreSQL; optional Enketo Redis/generated keys; not a full machine backup'}
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        archive=stage/'databases.tar.gz'
        with tarfile.open(archive,'w:gz') as tar:
            for name in files+['manifest.json']:tar.add(stage/name,arcname=name,recursive=False)
        partial=output.with_suffix('.partial')
        try:encrypt(archive,partial,args.recipient);os.replace(partial,output)
        finally:partial.unlink(missing_ok=True)
        receipt={'created_at':manifest['created_at'],'encrypted_sha256':sha(output),'encrypted_bytes':output.stat().st_size,'application_databases':database_count,'sealed_evidence_files':len(evidence),'central_database':True,'enketo_link_state_included':args.include_enketo,'provider_or_environment_config_files_exported':False}
        output.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt))

if __name__=='__main__':main()
