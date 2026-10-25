"""Recompare retained synthetic pilot captures through the documented CLI offline.

These are captured inputs, not another live check. Socket connections are denied.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from lastcopy.config import ROOT, Settings
from lastcopy.inventory import read_archive
from scripts.run import main as run_cli


def main():
    base = ROOT / 'docs/verification/water-point'
    results = []
    # Retain the ledger/results privately. Windows may hold SQLite handles until
    # collection; deleting a just-used ledger here is unnecessary and fragile.
    work = Path(tempfile.mkdtemp(prefix='water-point-recompare-', dir=ROOT / 'private'))
    with patch('socket.socket.connect', side_effect=AssertionError('Network denied during captured-input comparison')):
        for phase, expected in (('before', 'MISSING_SUBMISSION'), ('after', 'PRESERVED')):
            inputs = base / 'captured'
            server = read_archive((inputs / (phase + '-server.zip')).read_bytes(), Settings({}))
            scope = work / phase
            scope.mkdir()
            for name, data in server.items():
                assert name in ('server-snapshot.json', 'server-payload.zip')
                (scope / name).write_bytes(data)
            args = ['--data-dir', str(scope / 'ledger'), 'run', '--manifest', str(inputs / (phase + '-manifest.json')),
                    '--device', str(inputs / (phase + '-device-0.zip')), '--server-manifest', str(scope / 'server-snapshot.json'),
                    '--server-payload', str(scope / 'server-payload.zip'), '--output', str(scope / 'result')]
            assert run_cli(args) == 0
            report = json.loads((scope / 'result/report.json').read_text(encoding='utf-8'))
            assert len(report['findings']) == 1 and report['findings'][0]['verdict'] == expected
            assert report['provider_calls'] == 0 and not report['recovery_executed']
            results.append({'capture': phase, 'run_id': report['run_id'], 'expected': expected, 'actual': report['findings'][0]['verdict'], 'provider_calls': 0})
    (base / 'captured-cli.json').write_text(json.dumps({'status': 'passed', 'mode': 'offline recomparison of captured synthetic evidence; not live',
                                                      'network': 'socket.socket.connect denied', 'results': results}, indent=2) + '\n', encoding='utf-8')
    print('PASS captured before/after inputs through documented CLI with network connections denied')


if __name__ == '__main__':
    main()
