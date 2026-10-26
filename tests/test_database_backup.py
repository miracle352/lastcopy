import sqlite3,hashlib,subprocess,shutil
from pathlib import Path
import pytest

def test_database_snapshot_preserves_sources_and_does_not_copy_provider_keys(tmp_path):
    from scripts.backup_databases import snapshot_databases
    root=tmp_path/'source';root.mkdir();stage=tmp_path/'backup';stage.mkdir()
    db=root/'lastcopy.sqlite3'
    with sqlite3.connect(db) as c:c.execute('CREATE TABLE evidence(bytes BLOB)');c.execute('INSERT INTO evidence VALUES(?)',(b'untouched original',))
    before=hashlib.sha256(db.read_bytes()).hexdigest()
    (root/'cloud-ai.json').write_text('PRIVATE_KEY_DO_NOT_EXPORT')
    files=snapshot_databases(root,stage)
    assert files==['application/lastcopy.sqlite3']
    with sqlite3.connect(stage/files[0]) as c:assert c.execute('SELECT bytes FROM evidence').fetchone()[0]==b'untouched original'
    assert hashlib.sha256(db.read_bytes()).hexdigest()==before
    assert not list(stage.rglob('cloud-ai.json'))

def test_database_backup_rejects_links(tmp_path):
    from scripts.backup_databases import snapshot_databases
    root=tmp_path/'source';root.mkdir();stage=tmp_path/'stage';stage.mkdir()
    target=tmp_path/'outside';target.mkdir()
    try:(root/'linked').symlink_to(target,target_is_directory=True)
    except OSError:pytest.skip('Creating a Windows symlink requires developer mode')
    with pytest.raises(ValueError,match='links'):snapshot_databases(root,stage)

def test_backup_encryption_authenticates_ciphertext(tmp_path):
    from scripts.backup_databases import encrypt
    openssl=shutil.which('openssl') or 'C:/Program Files/Git/usr/bin/openssl.exe'
    key=tmp_path/'key.pem';cert=tmp_path/'public.pem';source=tmp_path/'source';source.write_bytes(b'synthetic evidence only')
    subprocess.run([openssl,'req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-subj','/CN=Backup test','-days','1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    sealed=tmp_path/'sealed.cms';encrypt(source,sealed,cert,openssl)
    command=[openssl,'cms','-decrypt','-binary','-inform','DER','-in',str(sealed),'-recip',str(cert),'-inkey',str(key)]
    assert subprocess.check_output(command)==source.read_bytes()
    raw=bytearray(sealed.read_bytes());raw[-1]^=1;sealed.write_bytes(raw)
    assert subprocess.run(command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0
