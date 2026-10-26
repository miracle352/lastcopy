"""Encrypted database backup; private configs/keys stay on their existing host.

This is not a machine image: Enketo link keys, environment configuration and
externally stored attachments require a separate disaster-recovery procedure.
"""
import argparse,hashlib,json,os,re,shutil,sqlite3,subprocess,tarfile,tempfile,time
from pathlib import Path
from datetime import datetime,timezone

MAX_BYTES=2*1024**3

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
    args=parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}',args.postgres_container):raise ValueError('Invalid database container')
    output=args.output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists() or output.with_suffix('.partial').exists():raise ValueError('Backup destination already exists')
    if shutil.disk_usage(output.parent).free<5*1024**3:raise ValueError('Backup requires a 5 GiB free-space reserve')
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix='.lastcopy-backup-',dir=output.parent) as temporary:
        stage=Path(temporary);files=snapshot_databases(args.store,stage)
        dump=stage/'central.pgdump'
        with dump.open('wb') as stream:
            subprocess.run(['docker','exec',args.postgres_container,'pg_dump','-U','odk','-d','odk','-Fc'],stdout=stream,stderr=subprocess.PIPE,check=True,timeout=180)
        with dump.open('rb') as stream:header=stream.read(5)
        if dump.stat().st_size>MAX_BYTES or header!=b'PGDMP':raise ValueError('Invalid/oversized Central database backup')
        files.append(dump.name)
        manifest={'created_at':datetime.now(timezone.utc).isoformat(),'files':{name:sha(stage/name) for name in files},'environment_and_provider_keys_included':False,'scope':'SQLite evidence/attempt ledgers and Central PostgreSQL; not a full machine or Enketo link backup'}
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        archive=stage/'databases.tar.gz'
        with tarfile.open(archive,'w:gz') as tar:
            for name in files+['manifest.json']:tar.add(stage/name,arcname=name,recursive=False)
        partial=output.with_suffix('.partial')
        try:encrypt(archive,partial,args.recipient);os.replace(partial,output)
        finally:partial.unlink(missing_ok=True)
        receipt={'created_at':manifest['created_at'],'encrypted_sha256':sha(output),'encrypted_bytes':output.stat().st_size,'application_databases':len(files)-1,'central_database':True,'provider_or_environment_config_files_exported':False}
        output.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt))

if __name__=='__main__':main()
