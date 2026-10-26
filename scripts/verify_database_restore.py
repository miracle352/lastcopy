"""Restore a trusted Central dump into a new scratch DB; never restore over odk."""
import argparse,hashlib,json,re,subprocess,uuid,time
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dump',type=Path,required=True);parser.add_argument('--sha256',required=True)
    args=parser.parse_args()
    if not re.fullmatch(r'[a-f0-9]{64}',args.sha256):raise ValueError('Require the trusted backup manifest hash')
    h=hashlib.sha256()
    with args.dump.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    if h.hexdigest()!=args.sha256:raise ValueError('Backup file hash mismatch')
    container='lastcopy-cloud-odk-postgres14-1';name='lastcopy_restore_drill_'+uuid.uuid4().hex[:12]
    assert name.startswith('lastcopy_restore_drill_') and name!='odk'
    command=['docker','exec',container]
    subprocess.run(command+['createdb','-U','odk',name],check=True,timeout=30,capture_output=True)
    try:
        with args.dump.open('rb') as stream:
            subprocess.run(['docker','exec','-i',container,'pg_restore','--exit-on-error','--no-owner','--no-privileges','-U','odk','-d',name],stdin=stream,check=True,timeout=180,capture_output=True)
        fingerprints={}
        for database in ('odk',name):
            values={}
            for table in ('submissions','submission_defs','blobs'):
                # Fixed table names; only digests leave this process.
                sql=f'SET statement_timeout=20000; SELECT row_to_json(t)::text FROM (SELECT * FROM {table} ORDER BY id) t;'
                process=subprocess.Popen(command+['psql','-U','odk','-d',database,'-qAtc',sql],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                result=hashlib.sha256();size=0;deadline=time.monotonic()+30
                try:
                    for chunk in iter(lambda:process.stdout.read(65536),b''):
                        size+=len(chunk)
                        if size>2*1024**3 or time.monotonic()>deadline:raise ValueError('Restore fingerprint exceeded its bound')
                        result.update(chunk)
                    if process.wait(timeout=5):raise ValueError('Database fingerprint request failed')
                finally:
                    if process.poll() is None:process.kill();process.wait(timeout=5)
                values[table]=result.hexdigest()
            fingerprints['live' if database=='odk' else 'restored']=values
        assert fingerprints['live']==fingerprints['restored'],'Restored bytes differ from the current live records; do not overwrite anything'
    finally:subprocess.run(command+['dropdb','-U','odk',name],check=True,timeout=30,capture_output=True)
    print(json.dumps({'status':'passed','scope':'Actual off-host dump restored into an isolated database; full rows of submissions, versions/XML and blobs match current live rows','fingerprints':fingerprints,'live_database_writes':0,'scratch_database_removed':True}))

if __name__=='__main__':main()
