import hashlib,io,os,shutil,subprocess
from pathlib import Path
import pytest
from scripts.backup_offsite import upload
from scripts.backup_databases import encrypt


class Missing(Exception):
    response={'Error':{'Code':'404'}}


class S3:
    def __init__(self):self.files={};self.writes=0;self.lose_ack=False;self.used=0
    def head_object(self,**kw):
        if kw['Key'] not in self.files:raise Missing()
        return {'ContentLength':len(self.files[kw['Key']])}
    def get_object(self,**kw):
        if kw['Key'] not in self.files:raise Missing()
        raw=self.files[kw['Key']];return {'ContentLength':len(raw),'Body':io.BytesIO(raw)}
    def put_object(self,**kw):
        assert kw['IfNoneMatch']=='*' and kw['ServerSideEncryption']=='AES256'
        assert kw['Key'] not in self.files
        self.files[kw['Key']]=kw['Body'].read();self.writes+=1
        if self.lose_ack:raise TimeoutError('Upload succeeded before acknowledgement was lost')
    def get_paginator(self,name):assert name=='list_object_versions';return self
    def paginate(self,**kw):yield {'Versions':[{'Size':self.used}]}


@pytest.fixture
def sealed(tmp_path,monkeypatch):
    openssl=shutil.which('openssl') or 'C:/Program Files/Git/usr/bin/openssl.exe'
    monkeypatch.setenv('PATH',str(Path(openssl).parent)+os.pathsep+os.environ['PATH'])
    key=tmp_path/'key.pem';cert=tmp_path/'recipient.pem';source=tmp_path/'input.txt'
    subprocess.run([openssl,'req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-subj','/CN=Synthetic offsite test','-days','1'],check=True,capture_output=True)
    source.write_bytes(b'untouched synthetic evidence')
    path=tmp_path/'lastcopy-db-20261026T120000Z.cms';encrypt(source,path,cert,openssl)
    receipt={'encrypted_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'encrypted_bytes':path.stat().st_size}
    return path,receipt,source


def test_lost_ack_and_repeated_backup_read_bytes_without_another_upload(sealed):
    path,receipt,original=sealed;before=original.read_bytes();remote=S3();remote.lose_ack=True
    assert upload(remote,'synthetic-bucket',path,receipt)['state']=='verified'
    assert upload(remote,'synthetic-bucket',path,receipt)['uploaded'] is False
    assert remote.writes==1 and original.read_bytes()==before


def test_corrupt_readback_or_reached_cap_never_claims_success(sealed):
    path,receipt,_=sealed;remote=S3();remote.files['daily/'+path.name]=b'wrong bytes'
    with pytest.raises(ValueError,match='mismatch'):upload(remote,'synthetic-bucket',path,receipt)
    assert remote.writes==0
    remote=S3();remote.used=1000
    with pytest.raises(ValueError,match='cap'):upload(remote,'synthetic-bucket',path,receipt,cap=1000)
    assert remote.writes==0


def test_plaintext_and_changed_local_bytes_cannot_be_uploaded(sealed):
    path,receipt,_=sealed;path.write_bytes(b'private plaintext');remote=S3()
    with pytest.raises(ValueError,match='receipt'):upload(remote,'synthetic-bucket',path,receipt)
    receipt.update(encrypted_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),encrypted_bytes=path.stat().st_size)
    with pytest.raises(subprocess.CalledProcessError):upload(remote,'synthetic-bucket',path,receipt)
    assert remote.writes==0


def test_uploader_policy_has_explicit_no_delete_and_no_other_bucket():
    from scripts.provision_backup_storage import policy,BUCKET
    rows=policy()['Statement']
    assert rows[2]['Effect']=='Deny' and 's3:DeleteObjectVersion' in rows[2]['Action']
    assert rows[1]['Resource']=='arn:aws:s3:::'+BUCKET+'/daily/*'
    assert all(not action.startswith(('iam:','ec2:')) for row in rows for action in row['Action'])
