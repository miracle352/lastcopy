"""Change only non-secret web settings on the existing server, with no export.

Run with the host's Python over verified SSH. Credential lines remain on that
host and are neither printed nor transferred. No third-party modules required.
"""
from pathlib import Path
import os


def main():
    if os.name!='posix':raise ValueError('Run only on the authorized Ubuntu host')
    path=Path('/srv/lastcopy/private/api.env');lines=path.read_text(encoding='utf-8').splitlines()
    assert 'ODK_READ_PROJECT_ID=1' in lines and 'LASTCOPY_CLOUD_ACCESS=true' in lines
    changes={'PUBLIC_APP_ORIGIN':'https://app-18-141-113-136.sslip.io','API_ORIGIN':'http://127.0.0.1:8000','NEXT_TELEMETRY_DISABLED':'1'}
    remove=set(changes)|{'WORKSPACE_ORIGIN','VERCEL'}
    kept=[line for line in lines if line.partition('=')[0] not in remove]
    path.write_text('\n'.join(kept+[k+'='+v for k,v in changes.items()])+'\n',encoding='utf-8')
    path.chmod(0o600)
    print('Changed only workspace origin, loopback API and telemetry settings on this host. Credential lines retained without export.')


if __name__=='__main__':main()
