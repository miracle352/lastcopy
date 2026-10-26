"""Match installed Alpine source packages locally against official secfixes.

This feed lists fixes, not every open vulnerability; zero matches is not a
whole-system security claim. Bundled CPython/Node are outside apk coverage.
"""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen


def inventory(raw):
    packages = set()
    for record in raw.strip().split('\n\n'):
        fields = dict(line.split(':', 1) for line in record.splitlines() if ':' in line)
        if fields.get('P') and fields.get('V'):
            packages.add((fields.get('o', fields['P']), fields['V']))
    if not packages:
        raise ValueError('No installed Alpine package inventory')
    return sorted(packages)


def findings(packages, databases, less_than):
    rows = []
    for db in databases:
        if db.get('distroversion') != 'v3.23':
            raise ValueError('Advisory release does not match Alpine 3.23')
        fixes = {row['pkg']['name']: row['pkg'].get('secfixes', {}) for row in db['packages']}
        for name, installed in packages:
            for fixed, identifiers in fixes.get(name, {}).items():
                if less_than(installed, fixed):
                    rows.extend({'package': name, 'installed': installed, 'fixed_version': fixed,
                                 'cve': cve, 'repository': db['reponame']} for cve in identifiers)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    image = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', args.image], text=True).strip()
    base = ['docker', 'run', '--rm', '--pull=never', '--network', 'none', '--read-only',
            '--memory', '128m', '--pids-limit', '32', '--cap-drop', 'ALL', '--entrypoint']
    def run(entry, *command):
        return subprocess.check_output(base + [entry, image, *command], text=True, timeout=30).strip()
    if not run('cat', '/etc/alpine-release').startswith('3.23.'):
        raise ValueError('Image is not Alpine 3.23')
    packages = inventory(run('cat', '/lib/apk/db/installed'))
    databases, receipts = [], []
    for repo in ('main', 'community'):
        url = 'https://secdb.alpinelinux.org/v3.23/' + repo + '.json'
        with urlopen(url, timeout=45) as response:
            data = response.read(16 * 1024 * 1024 + 1)
        if len(data) > 16 * 1024 * 1024:
            raise ValueError('Public advisory database exceeds 16 MiB bound')
        databases.append(json.loads(data))
        receipts.append({'url': url, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    rows = findings(packages, databases, lambda installed, fixed: run('apk', 'version', '-t', installed, fixed) == '<')
    report = {'observed_at': datetime.now(timezone.utc).isoformat(), 'image_id': image,
              'image': args.image, 'installed_source_packages': packages, 'databases': receipts,
              'findings': rows, 'metadata_exported': False, 'scanner_network': 'none',
              'scope': __doc__}
    Path(args.output).write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'image_id': image, 'packages': len(packages), 'findings': len(rows)}))


if __name__ == '__main__':
    main()
