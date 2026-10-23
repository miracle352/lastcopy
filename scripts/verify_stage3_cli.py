"""Run documented offline/replay entrypoints and verify literal expectations/seals."""
import json
import os
import subprocess
import sys
import time
from lastcopy.config import ROOT
from lastcopy.inventory import digest


def main():
    base = ROOT / 'private/verification' / ('stage3-cli-' + str(time.time_ns()))
    receipts = []
    for name, replay in [('export-review', False), ('unresolved-conflict', False), ('held-out', False), ('held-out', True)]:
        fixture = ROOT / 'fixtures/stage3' / name
        expected = json.loads((fixture / 'expected.json').read_bytes())
        hashes = {p.name: digest(p.read_bytes()) for p in fixture.iterdir() if p.is_file()}
        output = base / (name + ('-replay' if replay else ''))
        command = [sys.executable, '-m', 'scripts.investigate', '--manifest', str(fixture / 'run-manifest.json'),
            '--device', str(fixture / 'device.zip'), '--server-manifest', str(fixture / 'server-snapshot.json'),
            '--server-payload', str(fixture / 'server-payload.zip'), '--output', str(output)]
        if replay:
            command.append('--replay')
        result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=60,
            env={**os.environ, 'SAMPLE_MODE': 'false' if replay else 'true'})
        assert result.returncode == 0, result.stdout.decode(errors='replace') + result.stderr.decode(errors='replace')
        report = json.loads((output / 'investigation.json').read_bytes())
        assert report['status'] == 'completed' and report['provider_calls'] == 0
        assert report['mode'] == ('replay' if replay else 'sample')
        assert all(f['verdict'] == expected['verdict'] and not f['recovery_eligible'] for f in report['report']['findings'])
        assert not any(e['kind'] in ('query', 'model') for e in report['events'])
        seals = json.loads((output / 'seals.json').read_bytes())
        assert all(digest((output / path).read_bytes()) == sha for path, sha in seals.items())
        assert hashes == {p.name: digest(p.read_bytes()) for p in fixture.iterdir() if p.is_file()}
        receipts.append({'fixture': name, 'mode': report['mode'], 'status': 'PASS', 'verdict': expected['verdict'],
            'provider_calls': 0, 'source_files_unchanged': True, 'output_seals_verified': True,
            'report_sha256': report['report_sha256']})
    (ROOT / 'docs/verification/stage3-cli.json').write_text(json.dumps(receipts, indent=2) + '\n')
    print(json.dumps(receipts, indent=2))


if __name__ == '__main__':
    main()
