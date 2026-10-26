"""Upload only verified CMS ciphertext to the approved private S3 prefix.

No originals, provider keys, deletion, overwrite or production restore. The storage
cap is an application guard, not an AWS billing guarantee after credential theft.
"""
import argparse,base64,hashlib,json,os,re,subprocess,time
from pathlib import Path
from datetime import datetime,timezone

CAP=512*1024**2
MAX_FILE=32*1024**2
PREFIX='daily/'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def error_code(error):
    return getattr(error,'response',{}).get('Error',{}).get('Code')


def verify_remote(client,bucket,key,expected,size):
    result=client.get_object(Bucket=bucket,Key=key)
    if result['ContentLength']!=size:raise ValueError('Remote ciphertext size mismatch')
    total=0;digest=hashlib.sha256();deadline=time.monotonic()+60
    try:
        for chunk in iter(lambda:result['Body'].read(65536),b''):
            total+=len(chunk)
            if total>MAX_FILE or time.monotonic()>deadline:raise ValueError('Remote verification exceeds its bound')
            digest.update(chunk)
    finally:result['Body'].close()
    if total!=size or digest.hexdigest()!=expected:raise ValueError('Remote ciphertext hash mismatch')


def upload(client,bucket,path,receipt,*,cap=CAP):
    path=Path(path)
    if (path.is_symlink() or not re.fullmatch(r'lastcopy-db-\d{8}T\d{6}Z\.cms',path.name)
            or not 1<=path.stat().st_size<=MAX_FILE):raise ValueError('Invalid bounded encrypted backup')
    expected=receipt['encrypted_sha256'];size=path.stat().st_size
    if not re.fullmatch(r'[a-f0-9]{64}',expected) or sha(path)!=expected or size!=receipt['encrypted_bytes']:
        raise ValueError('Local ciphertext receipt mismatch')
    check=subprocess.run(['openssl','cms','-cmsout','-print','-inform','DER','-in',str(path)],
        capture_output=True,timeout=10,check=True)
    if b'contentType: id-smime-ct-authEnvelopedData' not in check.stdout[:256]:
        raise ValueError('Only authenticated encrypted CMS backups may leave the host')
    key=PREFIX+path.name
    try:
        existing=client.head_object(Bucket=bucket,Key=key)
    except Exception as error:
        if error_code(error) not in ('404','NoSuchKey','NotFound'):raise
        existing=None
    if existing:
        verify_remote(client,bucket,key,expected,size)
        return {'state':'verified','uploaded':False,'sha256':expected,'bytes':size}
    used=count=pages=0;deadline=time.monotonic()+60
    for page in client.get_paginator('list_object_versions').paginate(Bucket=bucket,Prefix=PREFIX,PaginationConfig={'PageSize':1000}):
        pages+=1
        if pages>3 or time.monotonic()>deadline:raise ValueError('Off-host inventory exceeds its bound')
        for item in page.get('Versions',[]):
            used+=item['Size'];count+=1
        if count>2000 or used+size>cap:raise ValueError('Off-host storage cap reached; no deletion performed')
    if used+size>cap:raise ValueError('Off-host storage cap reached; no deletion performed')
    try:
        with path.open('rb') as source:
            client.put_object(Bucket=bucket,Key=key,Body=source,ContentLength=size,
                ChecksumSHA256=base64.b64encode(bytes.fromhex(expected)).decode(),
                IfNoneMatch='*',ServerSideEncryption='AES256',Metadata={'ciphertext-sha256':expected})
    except Exception:
        # A lost acknowledgement must be resolved by fresh bytes before any retry.
        verify_remote(client,bucket,key,expected,size)
        return {'state':'verified','uploaded':'uncertain_request_resolved_by_readback','sha256':expected,'bytes':size}
    verify_remote(client,bucket,key,expected,size)
    return {'state':'verified','uploaded':True,'sha256':expected,'bytes':size}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--folder',type=Path,required=True)
    p.add_argument('--credentials',type=Path,required=True);p.add_argument('--health',type=Path,required=True)
    args=p.parse_args();now=datetime.now(timezone.utc).isoformat();result={'state':'failed','observed_at':now}
    try:
        if args.credentials.is_symlink() or args.credentials.stat().st_size>4096 or args.credentials.stat().st_mode&0o077:
            raise ValueError('Private uploader configuration requires mode 0600')
        config=json.loads(args.credentials.read_bytes())
        if (config['bucket']!='lastcopy-private-backups-350353785155-sg' or config['region']!='ap-southeast-1'
                or config['account']!='350353785155' or config['prefix']!=PREFIX):raise ValueError('Unapproved backup destination')
        import boto3
        from botocore.config import Config
        client=boto3.client('s3',region_name=config['region'],aws_access_key_id=config['access_key_id'],
            aws_secret_access_key=config['secret_access_key'],config=Config(connect_timeout=5,read_timeout=15,retries={'max_attempts':1}))
        receipts=sorted(args.folder.glob('lastcopy-db-*.receipt.json'))
        if not receipts:raise ValueError('No encrypted backup receipt')
        selected=receipts[-1]
        if selected.is_symlink() or selected.stat().st_size>4096:raise ValueError('Invalid backup receipt')
        receipt=json.loads(selected.read_bytes());path=selected.with_suffix('').with_suffix('.cms')
        result.update(upload(client,config['bucket'],path,receipt),last_success=now)
    except Exception:
        result['message']='Off-host backup failed or reached its bound. Older copies were retained; no plaintext or keys were exported.'
    args.health.parent.mkdir(parents=True,exist_ok=True)
    temporary=args.health.with_suffix('.tmp');temporary.write_text(json.dumps(result)+'\n');os.chmod(temporary,0o644);os.replace(temporary,args.health)
    print(json.dumps(result))
    return 0 if result['state']=='verified' else 1


if __name__=='__main__':raise SystemExit(main())
