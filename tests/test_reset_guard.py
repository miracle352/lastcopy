import copy
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.reset_guard import ALLOW, BLOCK, USAGE, canonical_sha256, guard

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / 'output_examples' / 'live_connected_fleet.json'
FLEET = ROOT / 'fixtures' / 'fleet'


def doc():
    return json.loads(LIVE.read_text(encoding='utf-8'))


def export(name):
    return (FLEET / f'{name}.zip').read_bytes()


def test_safe_tablet_with_unchanged_export_is_allowed():
    r = guard(doc(), 'tablet-01', export('tablet-01'))
    assert r['verdict'] == 'ALLOW'
    assert all(c['pass'] for c in r['checks'])


@pytest.mark.parametrize('device', ['tablet-02', 'tablet-03', 'tablet-04'])
def test_tablets_not_cleared_are_blocked(device):
    r = guard(doc(), device, export(device))
    assert r['verdict'] == 'BLOCK'
    assert any('SAFE_TO_WIPE' in reason for reason in r['reasons'])


def test_tablet_that_never_exported_is_blocked():
    r = guard(doc(), 'tablet-05', None)
    assert r['verdict'] == 'BLOCK'


def test_new_data_collected_after_the_check_blocks_the_reset():
    # tablet-01 was cleared, but the bytes on the device now differ from the certified export
    r = guard(doc(), 'tablet-01', export('tablet-01') + b'new survey collected after the check')
    assert r['verdict'] == 'BLOCK'
    assert any('changed since the check' in reason for reason in r['reasons'])


def test_missing_fresh_export_blocks():
    assert guard(doc(), 'tablet-01', None)['verdict'] == 'BLOCK'


def test_edited_certificate_is_blocked():
    d = doc()
    d['decisions'][1]['certificate']['decision'] = 'SAFE_TO_WIPE'  # tablet-02 forged to look safe
    d['decisions'][1]['decision'] = 'SAFE_TO_WIPE'
    r = guard(d, 'tablet-02', export('tablet-02'))
    assert r['verdict'] == 'BLOCK'
    assert any(reason.startswith('certificate hash') for reason in r['reasons'])


def test_forged_certificate_with_recomputed_hash_still_fails_the_rule():
    d = doc()
    dec = d['decisions'][1]
    dec['certificate']['decision'] = dec['decision'] = 'SAFE_TO_WIPE'
    dec['certificate_sha256'] = canonical_sha256(dec['certificate'])
    r = guard(d, 'tablet-02', export('tablet-02'))
    assert r['verdict'] == 'BLOCK'
    assert any(reason.startswith('decision follows rule') for reason in r['reasons'])


def test_open_adversary_objection_blocks():
    d = doc()
    dec = d['decisions'][0]
    dec['certificate'] = copy.deepcopy(dec['certificate'])
    dec['certificate']['challenge'] = {'objection': 'archive_altered'}
    dec['certificate']['decision'] = dec['decision'] = 'HOLD'
    dec['certificate_sha256'] = canonical_sha256(dec['certificate'])
    assert guard(d, 'tablet-01', export('tablet-01'))['verdict'] == 'BLOCK'


def test_stale_check_is_blocked_when_a_limit_is_set():
    d = doc()
    captured = datetime.fromisoformat(d['captured_at'].replace('Z', '+00:00'))
    assert guard(d, 'tablet-01', export('tablet-01'), 24, now=captured + timedelta(hours=2))['verdict'] == 'ALLOW'
    assert guard(d, 'tablet-01', export('tablet-01'), 24, now=captured + timedelta(hours=30))['verdict'] == 'BLOCK'


def test_unknown_device_raises():
    with pytest.raises(KeyError):
        guard(doc(), 'tablet-99', None)


def test_cli_exit_codes():
    def run(*args):
        return subprocess.run([sys.executable, '-m', 'scripts.reset_guard', str(LIVE), *args],
                              cwd=ROOT, capture_output=True, text=True).returncode
    assert run('--device', 'tablet-01', '--export', str(FLEET / 'tablet-01.zip')) == ALLOW
    assert run('--device', 'tablet-02', '--export', str(FLEET / 'tablet-02.zip')) == BLOCK
    assert run('--device', 'tablet-99') == USAGE


def test_cli_json_output():
    out = subprocess.run([sys.executable, '-m', 'scripts.reset_guard', str(LIVE), '--device', 'tablet-01',
                          '--export', str(FLEET / 'tablet-01.zip'), '--json'],
                         cwd=ROOT, capture_output=True, text=True).stdout
    assert json.loads(out)['verdict'] == 'ALLOW'
