"""Read-only final-state/integrity receipts; private configuration stays private."""
import hashlib
import json
import subprocess
import tempfile
import sqlite3
from contextlib import closing
from pathlib import Path
from dotenv import dotenv_values
import httpx
from defusedxml import ElementTree as ET
from lastcopy.config import ROOT, Settings
from lastcopy.device_transfer import DeviceTransfer, unpack
from lastcopy.store import RunStore


def main():
    cfg = dict(dotenv_values(ROOT / '.env'))
    assert cfg['ODK_BASE_URL'] == 'http://localhost:8384' and cfg['ODK_READ_PROJECT_ID'] == '3'
    out = ROOT / 'docs/verification/realtime'
    out.mkdir(exist_ok=True)
    store = RunStore(ROOT / 'private/application', Settings(cfg))
    transfer = DeviceTransfer(store)
    files = unpack(transfer.adb_pull())
    form = (ROOT / 'forms/water-point-condition/water-point-condition-v2.xml').read_bytes()
    assert any(data == form for name, data in files.items() if name.startswith('forms/') and name.endswith('.xml'))
    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory) / 'instances.db'
        db.write_bytes(files['metadata/instances.db'])
        with closing(sqlite3.connect(db.as_uri() + '?mode=ro', uri=True)) as c:
            native_count = c.execute('SELECT COUNT(*) FROM instances WHERE jrFormId=?', ('lastcopy_water_point_v1',)).fetchone()[0]
    assert native_count == 0
    project = cfg['LASTCOPY_COLLECT_PROJECT_ID']
    adb = cfg['LASTCOPY_ADB_PATH']
    raw = subprocess.check_output([adb, '-s', 'emulator-5558', 'exec-out', 'cat', '/data/data/org.odk.collect.android/shared_prefs/general_prefs' + project + '.xml'])
    prefs = {n.get('name'): n.text if n.tag == 'string' else n.get('value') for n in ET.fromstring(raw)}
    assert prefs['autosend'] == 'wifi_only' and prefs.get('delete_send', 'false') == 'false'
    with httpx.Client(timeout=45, trust_env=False) as c:
        r = c.get('http://127.0.0.1:8000/ui/watch');r.raise_for_status();watch = r.json()
        assert watch['enabled'] and watch['device_transfer']['state'] == 'waiting_for_records' and watch['last_run_id'] is None
        login = c.post(cfg['ODK_BASE_URL'] + '/v1/sessions', json={'email': cfg['ODK_EMAIL'], 'password': cfg['ODK_PASSWORD']});login.raise_for_status()
        counts = {}
        for pid, expected in ((3, 0), (4, 1)):
            response = c.get(cfg['ODK_BASE_URL'] + f'/v1/projects/{pid}/forms/lastcopy_water_point_v1/submissions', headers={'Authorization': 'Bearer ' + login.json()['token']})
            response.raise_for_status();counts[str(pid)] = len(response.json());assert counts[str(pid)] == expected
    verified = {}
    for folder in ('stage7', 'redesign', 'product', 'water-point'):
        base = ROOT / 'docs/verification' / folder
        seals = json.loads((base / 'SHA256.json').read_text(encoding='utf-8'))
        assert all(hashlib.sha256((base / p).read_bytes()).hexdigest() == value for p, value in seals.items())
        verified[folder] = len(seals)
    original = ROOT / 'private/water-point/inbox-v2/water-emulator-v2.zip'
    assert hashlib.sha256(original.read_bytes()).hexdigest() == 'ad38566bd7d61aca8ad15bec668d9588205da4a65f732dc1a532ce354ae1b3db'
    result = {'status': 'passed', 'native_collection_project': project, 'published_form_downloaded_into_collect': True,
              'original_form_sha256': hashlib.sha256(form).hexdigest(), 'native_saved_records': native_count,
              'collect_auto_send': 'wifi_only', 'collect_delete_after_send': False, 'central_submission_counts': counts,
              'watch': watch, 'prior_seals_verified': verified, 'original_pilot_export_unchanged': True,
              'scope': 'Actual local empty collection with automatic device export and native Wi-Fi send configured; no new synthetic record seeded in collection project',
              'not_claimed': ['Physical-phone export compatibility', 'Public HTTPS/cloud deployment', 'New native auto-send submission acceptance', 'Uninterrupted coverage or perfect reliability']}
    (out / 'final-state.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    # Exact app-user bytes only; never print their values or copy settings/QR files.
    tokens = [prefs['server_url'].split('/key/')[1].split('/')[0].encode()]
    pilot = json.loads((ROOT / 'private/water-point/pilot-collect/settings.json').read_text(encoding='utf-8'))
    tokens.append(pilot['general']['server_url'].split('/key/')[1].split('/')[0].encode())
    paths = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    findings = [name for name in paths if name and (ROOT / name).is_file() and any(token in (ROOT / name).read_bytes() for token in tokens)]
    assert not findings
    (out / 'app-user-credential-audit.json').write_text(json.dumps({'new_private_tokens_checked': 2, 'findings': findings, 'scope': 'Exact app-user bytes against non-ignored working files'}, indent=2) + '\n', encoding='utf-8')
    print('PASS actual collection setup, source retention, automatic producer state, prior evidence integrity and private credential exclusion')


if __name__ == '__main__':
    main()
