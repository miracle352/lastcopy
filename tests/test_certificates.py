import copy
import json
from pathlib import Path

from scripts.clearance_sheet import sheet
from scripts.verify_certificate import check, expected_decision, sha256

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / 'output_examples' / 'live_connected_fleet.json'
FLEET = ROOT / 'fixtures' / 'fleet'


def load(p):
    return json.loads(p.read_text(encoding='utf-8'))


def test_every_bundled_certificate_verifies():
    for p in [LIVE, *sorted((ROOT / 'output_examples').glob('example_*_output.json'))]:
        assert all(ok for *_, ok, _ in check(load(p), {})), p.name


def test_live_certificates_bind_the_original_archives():
    archives = {sha256(p.read_bytes()): p.name for p in [*FLEET.glob('tablet-*.zip'), FLEET / 'server-payload.zip']}
    rows = check(load(LIVE), archives)
    assert all(ok for *_, ok, _ in rows)
    assert sum(what == 'device export bytes' for _, what, *_ in rows) == 4


def test_edited_decision_or_certificate_is_caught():
    doc = load(LIVE)
    forged = copy.deepcopy(doc)
    forged['decisions'][1]['decision'] = 'SAFE_TO_WIPE'
    assert not all(ok for *_, ok, _ in check(forged, {}))
    forged = copy.deepcopy(doc)
    forged['decisions'][1]['certificate']['decision'] = 'SAFE_TO_WIPE'
    assert not all(ok for *_, ok, _ in check(forged, {}))


def test_foreign_archive_is_reported():
    rows = check(load(LIVE), {sha256(b'not an export'): 'other.zip'})
    assert any(not ok and 'other.zip' in detail for *_, ok, detail in rows)


def test_rule_never_clears_missing_or_unexported_devices():
    base = {'device_export_sha256': 'x', 'records': []}
    assert expected_decision(base | {'device_export_sha256': None}) == 'HOLD'
    assert expected_decision(base | {'records': [{'verdict': 'PRESERVED'}, {'verdict': 'MISSING_ATTACHMENT'}]}) == 'RECOVER_FIRST'
    assert expected_decision(base | {'records': [{'verdict': 'CONTENT_CONFLICT'}]}) == 'HOLD'
    assert expected_decision(base) == 'HOLD'
    assert expected_decision(base | {'records': [{'verdict': 'EXPORT_VIEW_ONLY'}]}) == 'SAFE_TO_WIPE'


def test_clearance_sheet_lists_only_safe_tablets_for_signoff():
    md = sheet(load(LIVE))
    assert 'b.bin' in md and 'uuid:fleet-03-b' in md
    signoff = md.split('## Sign-off')[1]
    assert '`tablet-01`' in signoff and 'tablet-02' not in signoff


def test_blind_scenarios_are_decided_correctly_and_never_wrongly_cleared():
    from scripts.blind_eval import run_seed, scenario, truth
    assert truth(['ok', 'view_only'], True) == 'SAFE_TO_WIPE' and truth(['ok', 'no_photo', 'edited'], True) == 'RECOVER_FIRST'
    assert truth(['edited'], True) == 'HOLD' and truth([], False) == 'HOLD'
    assert scenario(7) == scenario(7) and scenario(7) != scenario(8)
    for seed in (3, 11):
        r = run_seed(seed)
        assert r['status'] == 'completed' and r['fleet_correct'], r
        assert not any(t['wrongly_cleared'] for t in r['tablets'])
