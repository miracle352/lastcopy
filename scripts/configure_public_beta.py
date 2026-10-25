"""Add two non-secret identity IDs on the authorized AWS host, no env export."""
from pathlib import Path
import os

def main():
    if os.name!='posix':raise ValueError('Run on the configured Ubuntu host only')
    path=Path('/srv/lastcopy/private/api.env');lines=path.read_text().splitlines()
    assert 'ODK_READ_PROJECT_ID=1' in lines and 'LASTCOPY_CLOUD_ACCESS=true' in lines
    changes={'COGNITO_POOL_ID':'ap-southeast-1_wBMnjFEA2','COGNITO_CLIENT_ID':'5jsf74uhepkghk249gp98t75n'}
    kept=[line for line in lines if line.partition('=')[0] not in changes]
    path.write_text('\n'.join(kept+[k+'='+v for k,v in changes.items()])+'\n');path.chmod(0o600)
    print('Added only Cognito pool/client IDs. Existing credentials retained on this host without export.')

if __name__=='__main__':main()
