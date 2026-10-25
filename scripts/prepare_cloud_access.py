"""Create owner/transport credentials privately; never print their values.

Run locally once, then upload api.env only over the verified SSH connection.
The owner passphrase is a private handoff artifact, never a repository asset.
"""
import hashlib,json,secrets,os
from pathlib import Path
from lastcopy.config import ROOT


def main():
    folder=ROOT/'private/cloud';folder.mkdir(parents=True,exist_ok=True)
    path=folder/'access.json'
    if not path.exists():
        salt=secrets.token_hex(16);password=secrets.token_urlsafe(24)
        value={'owner_passphrase':password,'password_hash':salt+':'+hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex(),
            'transport_key':secrets.token_urlsafe(48),'session_key':secrets.token_urlsafe(48),'transfer_key':secrets.token_urlsafe(48),
            'central_email':'coordinator@example.invalid','central_password':secrets.token_urlsafe(32)}
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(value,f,indent=2)
    value=json.loads(path.read_text(encoding='utf-8'))
    config={'SAMPLE_MODE':'true','LASTCOPY_CLOUD_ACCESS':'true','LASTCOPY_TRANSPORT_KEY':value['transport_key'],
        'LASTCOPY_SESSION_KEY':value['session_key'],'LASTCOPY_OWNER_PASSWORD_HASH':value['password_hash'],
        'LASTCOPY_TRANSFER_KEY':value['transfer_key'],'LASTCOPY_DATA_DIR':'/app/private/application',
        'LASTCOPY_DEVICE_TRANSFER_ENABLED':'false'}
    target=folder/'api.env'
    if not target.exists():target.write_text(''.join(k+'='+v+'\n' for k,v in config.items()),encoding='utf-8',newline='\n')
    print('Owner credentials prepared in ignored private/cloud/access.json; API configuration contains only the password hash. No credential values printed.')


if __name__=='__main__':main()
