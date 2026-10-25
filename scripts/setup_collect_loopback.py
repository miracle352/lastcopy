"""Correct the exact existing local Central's advertised native download URLs.

Loopback-only development override; never use it on a public Central deployment.
No volume is removed, image upgraded, form changed or submission written.
"""
import json
import subprocess
import time
from urllib.parse import urlsplit
import httpx
from dotenv import dotenv_values
from lastcopy.config import ROOT
from scripts.setup_odk_test import CENTRAL_COMMIT


def main():
    cfg = dotenv_values(ROOT / '.env')
    if cfg.get('ODK_BASE_URL') != 'http://localhost:8384':
        raise ValueError('Only the existing localhost Central may be configured')
    checkout = ROOT / 'private/central'
    def execute(args, **kwargs):
        return subprocess.check_output(args, cwd=checkout, **kwargs)
    assert execute(['git', 'rev-parse', 'HEAD']).decode().strip() == CENTRAL_COMMIT
    mounts_before = execute(['docker', 'inspect', 'lastcopy-odk-postgres14-1', '--format', '{{json .Mounts}}'])
    before = execute(['docker', 'exec', 'lastcopy-odk-service-1', 'node', '-p', "require('config').get('default.env.domain')"]).decode().strip()
    if before not in ('https://localhost:8444', 'http://localhost:8384'):
        raise ValueError('Central advertises an unexpected scope; no configuration changed')
    override = json.dumps({'default': {'env': {'domain': 'http://localhost:8384'}}})
    probe = execute(['docker', 'exec', '-e', 'NODE_CONFIG=' + override, 'lastcopy-odk-service-1', 'node', '-p', "require('config').get('default.env.domain')"]).decode().strip()
    assert probe == 'http://localhost:8384'
    text = '# Local paired-emulator development only. Never deploy publicly.\nservices:\n  service:\n    environment:\n      NODE_CONFIG: ' + json.dumps(override) + '\n'
    path = checkout / 'lastcopy.native.yml'
    if path.exists() and path.read_text(encoding='utf-8') != text:
        raise ValueError('Refusing to replace an existing different native override')
    path.write_text(text, encoding='utf-8')
    subprocess.run(['docker', 'compose', '-p', 'lastcopy-odk', '-f', 'docker-compose.yml', '-f', 'lastcopy.local.yml', '-f', 'lastcopy.native.yml',
                    'up', '-d', '--no-deps', '--no-build', '--pull', 'never', 'service'], cwd=checkout, check=True)
    actual = execute(['docker', 'exec', 'lastcopy-odk-service-1', 'node', '-p', "require('config').get('default.env.domain')"]).decode().strip()
    assert actual == 'http://localhost:8384'
    assert mounts_before == execute(['docker', 'inspect', 'lastcopy-odk-postgres14-1', '--format', '{{json .Mounts}}'])
    settings = json.loads((ROOT / 'private/water-point/collection-collect/settings.json').read_text(encoding='utf-8'))
    url = settings['general']['server_url']
    assert urlsplit(url).hostname == 'localhost' and urlsplit(url).port == 8384
    from defusedxml import ElementTree as ET
    deadline = time.monotonic() + 60
    with httpx.Client(timeout=10, trust_env=False) as client:
        while True:
            try:
                response = client.get(url + '/formList', headers={'X-OpenRosa-Version': '1.0'})
                if response.status_code == 200:
                    break
            except httpx.RequestError:
                pass
            if time.monotonic() > deadline:
                raise ValueError('Central did not become ready; no native-download success claimed')
            time.sleep(1)
        node = next(n for n in ET.fromstring(response.content).iter() if n.tag.endswith('downloadUrl'))
        target = urlsplit(node.text)
        assert (target.scheme, target.hostname, target.port) == ('http', 'localhost', 8384)
        downloaded = client.get(node.text, headers={'X-OpenRosa-Version': '1.0'})
        assert downloaded.status_code == 200
        original = (ROOT / 'forms/water-point-condition/water-point-condition-v2.xml').read_bytes()
        assert downloaded.content == original
    receipt = {'operation': 'Corrected advertised URL on existing local Central', 'before': before, 'after': actual,
               'form_download_status': downloaded.status_code, 'downloaded_original_form_matches': True, 'database_mounts_unchanged': True,
               'central_record_writes': 0, 'scope': 'Loopback-only local development, ADB paired-device forward; not public HTTPS'}
    (ROOT / 'docs/verification/realtime/central-native-url.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('PASS local Central advertises reachable native form URL; downloaded original bytes match; database mounts unchanged')


if __name__ == '__main__':
    main()
