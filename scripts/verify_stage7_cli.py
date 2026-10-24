"""Documented CLI, literal fixture expectations, evidence seals, immutable input."""
import json
import os
from pathlib import Path
import subprocess
import sys
from lastcopy.config import ROOT
from lastcopy.inventory import digest


def main():
    checks = []
    for fixture in sorted((ROOT/'fixtures/stage2').iterdir()) + sorted((ROOT/'fixtures/stage3').iterdir()):
        expected = json.loads((fixture/'expected.json').read_bytes())
        before = {p.name: digest(p.read_bytes()) for p in fixture.iterdir() if p.is_file()}
        out = ROOT/'private/stage7/cli'/fixture.parent.name/fixture.name
        result = subprocess.run([sys.executable, '-m', 'scripts.run', '--data-dir', str(out/'ledger'), 'run',
            '--manifest', str(fixture/'run-manifest.json'), '--device', str(fixture/'device.zip'),
            '--server-manifest', str(fixture/'server-snapshot.json'), '--server-payload', str(fixture/'server-payload.zip'),
            '--output', str(out/'report')], cwd=ROOT, env={**os.environ, 'SAMPLE_MODE': 'true'}, capture_output=True, timeout=60)
        assert result.returncode == 0, result.stdout.decode(errors='replace')
        report = json.loads((out/'report/report.json').read_bytes())
        if 'verdicts' in expected:
            assert {f['version_id']: f['verdict'] for f in report['findings']} == expected['verdicts']
        else:
            assert all(f['verdict'] == expected['verdict'] for f in report['findings'])
        assert report['provider_calls'] == 0 and report['mode'] == 'sample'
        assert before == {p.name: digest(p.read_bytes()) for p in fixture.iterdir() if p.is_file()}
        checks.append({'fixture': fixture.relative_to(ROOT).as_posix(), 'status': 'passed',
            'verdicts': [f['verdict'] for f in report['findings']], 'provider_calls': 0,
            'sources_unchanged': True, 'report_sha256': digest((out/'report/report.json').read_bytes())})
    target = ROOT/'docs/verification/stage7/cli.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(checks, indent=2)+'\n', encoding='utf8')
    print(f'{len(checks)} fixture CLI comparisons passed; no provider calls')


if __name__ == '__main__':
    main()
