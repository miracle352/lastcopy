"""Server-local test-scope switch. No environment file is exported.

Only used by the explicit synthetic delivery acceptance, never the normal app.
"""
import argparse,hashlib,os
from pathlib import Path


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['test','restore']);action=p.parse_args().action
    if os.name!='posix':raise ValueError('Authorized Ubuntu host only')
    root=Path('/srv/lastcopy/private');path=root/'api.env';backup=root/'api-before-scoped-test.env'
    if action=='restore':
        original=backup.read_bytes();path.write_bytes(original);path.chmod(0o600)
        print(hashlib.sha256(path.read_bytes()).hexdigest());return
    raw=path.read_bytes();lines=raw.decode('utf-8').splitlines()
    assert 'ODK_READ_PROJECT_ID=1' in lines and 'LASTCOPY_CLOUD_ACCESS=true' in lines
    # Keep a host-local private backup; never print secret lines.
    if backup.exists() and backup.read_bytes()!=raw:raise ValueError('Existing backup differs; operator review required')
    if not backup.exists():
        with backup.open('xb') as f:f.write(raw)
        backup.chmod(0o600)
    changes={'ODK_READ_PROJECT_ID':'2','ODK_READ_PROJECT_NAME':'LastCopy cloud recovery (synthetic)',
        'ODK_READ_CONNECTION_ID':'aws-central-automatic-acceptance','LASTCOPY_WATCH_INBOX':'/app/private/application/automatic-acceptance-inbox',
        'LASTCOPY_WATCH_DEVICE_IDS':'["water-emulator-01"]','LASTCOPY_WATCH_MAX_CHECKS':'1','LASTCOPY_WATCH_INTERVAL_SECONDS':'30'}
    kept=[line for line in lines if line.partition('=')[0] not in changes]
    path.write_text('\n'.join(kept+[k+'='+v for k,v in changes.items()])+'\n',encoding='utf-8');path.chmod(0o600)
    print(hashlib.sha256(raw).hexdigest())


if __name__=='__main__':main()
