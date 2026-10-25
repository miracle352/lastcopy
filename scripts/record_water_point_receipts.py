"""Collect already-produced acceptance receipts and verify the final local scope.

This reads only the exact local projects, starts the configured read-only monitor,
and makes no Central writes. Private app-user settings/QR files are never copied.
"""
import hashlib
import json
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import dotenv_values

from lastcopy.config import ROOT
from lastcopy.store import RunStore


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cfg = dotenv_values(ROOT / '.env')
    assert cfg['ODK_BASE_URL'] == 'http://localhost:8384'
    assert cfg['ODK_READ_PROJECT_ID'] == '3'
    assert Path(cfg['LASTCOPY_WATCH_INBOX']).resolve() == (ROOT / 'private/water-point/live-inbox').resolve()
    assert not list(Path(cfg['LASTCOPY_WATCH_INBOX']).iterdir())
    assert json.loads(cfg['LASTCOPY_WATCH_DEVICE_IDS']) == ['water-field-01']
    out = ROOT / 'docs/verification/water-point'
    out.mkdir(parents=True, exist_ok=True)

    def save(name, value):
        (out / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

    with httpx.Client(timeout=90, trust_env=False, follow_redirects=False) as client:
        login = client.post(cfg['ODK_BASE_URL'] + '/v1/sessions', json={'email': cfg['ODK_EMAIL'], 'password': cfg['ODK_PASSWORD']})
        login.raise_for_status()
        headers = {'Authorization': 'Bearer ' + login.json()['token']}
        projects = []
        for pid, name, count in ((3, 'Water Point Condition Check', 0), (4, 'LastCopy water-point pilot (synthetic)', 1)):
            project = client.get(cfg['ODK_BASE_URL'] + f'/v1/projects/{pid}', headers=headers)
            project.raise_for_status()
            assert project.json()['name'] == name
            records = client.get(cfg['ODK_BASE_URL'] + f'/v1/projects/{pid}/forms/lastcopy_water_point_v1/submissions', headers=headers)
            records.raise_for_status()
            assert len(records.json()) == count
            projects.append({'id': pid, 'name': name, 'submission_count': count, 'response_sha256': hashlib.sha256(records.content).hexdigest()})
        connection = client.get('http://127.0.0.1:8000/ui/connection')
        connection.raise_for_status()
        connection = connection.json()
        assert connection['state'] == 'connected' and connection['project_id'] == 3 and not connection['dedicated_test_project']
        monitor = client.post('http://127.0.0.1:8000/ui/watch/control', json={'action': 'start'})
        monitor.raise_for_status()
        monitor = monitor.json()
        deadline = time.monotonic() + 15
        while monitor['state'] == 'waiting_for_worker' and time.monotonic() < deadline:
            time.sleep(0.25)
            response = client.get('http://127.0.0.1:8000/ui/watch')
            response.raise_for_status()
            monitor = response.json()
        assert monitor['enabled'] and monitor['state'] == 'waiting_for_exports'
        assert monitor['received_devices'] == [] and monitor['last_run_id'] is None
        assert monitor['recovery_writes'] == 0
        save('final-state.json', {'checked_at': datetime.now(timezone.utc).isoformat(), 'projects': projects, 'connection': connection, 'monitor': monitor,
                                  'scope': 'Actual local collection is empty; expected device is a planned label, not a connected phone', 'central_writes': 0})

    private = ROOT / 'private/water-point'
    for name in ('setup.json', 'form-revision.json', 'collect-setup-receipt.json', 'live-acceptance.json', 'restart-receipt.json'):
        value = json.loads((private / name).read_text(encoding='utf-8'))
        if name == 'setup.json':
            value.pop('credentials', None)
        save(name, value)
    store = RunStore(ROOT / 'private/application')
    captured = out / 'captured'
    captured.mkdir(exist_ok=True)
    for phase in ('before', 'after'):
        view = json.loads((private / (phase + '-view.json')).read_text(encoding='utf-8'))
        save(phase + '-report.json', view['current_report'])
        request = view['request']
        inputs = [('manifest', request['manifest_id'], 'manifest.json'), ('server', request['server_input_id'], 'server.zip')]
        inputs += [('device', iid, f'device-{index}.zip') for index, iid in enumerate(request['device_input_ids'])]
        hashes = {}
        for kind, iid, suffix in inputs:
            data = store.input(iid, kind)
            name = phase + '-' + suffix
            target = captured / name
            if target.exists():
                assert target.read_bytes() == data
            else:
                target.write_bytes(data)
            hashes[name] = hashlib.sha256(data).hexdigest()
        save(phase + '-captured-inputs.json', {'scope': 'Actual immutable synthetic pilot inputs captured for this run; replay is not a new live check', 'run_id': view['status']['run_id'], 'files': hashes})
    # Sanitized request log contains only method/scope/status/time/response hash.
    rows = [json.loads(line) for line in (private / 'delivery-attempts.jsonl').read_text(encoding='utf-8').splitlines()]
    assert all(set(row) <= {'method', 'scope', 'status', 'response_sha256', 'at'} for row in rows)
    (out / 'native-delivery.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')

    verified = {}
    for folder, expected_count in (('stage7', 77), ('redesign', 43), ('product', 35)):
        base = ROOT / 'docs/verification' / folder
        sealed = json.loads((base / 'SHA256.json').read_text(encoding='utf-8'))
        assert len(sealed) == expected_count
        assert all(sha(base / name) == digest for name, digest in sealed.items())
        verified[folder] = len(sealed)
    original = json.loads((ROOT / 'docs/verification/water-point-form-20261025.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT / name) == digest for name, digest in original['files'].items())
    original_export = private / 'inbox-v2/water-emulator-v2.zip'
    fixture = ROOT / 'fixtures/water-point-collect-v2026.3.5/device.zip'
    assert sha(original_export) == sha(fixture) == 'ad38566bd7d61aca8ad15bec668d9588205da4a65f732dc1a532ce354ae1b3db'
    files = ['forms/water-point-condition/water-point-condition-v2.xml', 'outputs/01a169aa-cee9-7832-9577-4d6d6d6607ba/water-point-condition-v2.xlsx']
    save('integrity.json', {'prior_evidence_seals_verified': verified, 'original_v1_form_files_unchanged': True,
                            'original_v2_collect_export_sha256': sha(original_export), 'synthetic_fixture_identical_to_original_export': True,
                            'active_form_files': {name: sha(ROOT / name) for name in files}})
    # Check the two newly created app-user credentials without printing their bytes.
    tokens = []
    for directory in ('collection-collect', 'pilot-collect'):
        settings = json.loads((private / directory / 'settings.json').read_text(encoding='utf-8'))
        tokens.append(settings['general']['server_url'].split('/key/', 1)[1].split('/', 1)[0].encode())
    paths = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    findings = []
    count = 0
    for name in paths:
        p = ROOT / name
        if name and p.is_file():
            count += 1
            if any(token in p.read_bytes() for token in tokens):
                findings.append(name)
    save('app-user-credential-audit.json', {'working_files_checked': count, 'new_private_tokens_checked': len(tokens), 'findings': findings,
                                          'scope': 'Exact new app-user token bytes against public-repository-ready working files; no QR/settings file copied'})
    assert not findings
    print('PASS final empty collection scope, monitor waiting for exports, native pilot receipts and prior evidence integrity')


if __name__ == '__main__':
    main()
