"""Breaks caught: arbitrary paths, duplicate run overwrite, lost state/cancel/evidence."""
import importlib.util
import json
import subprocess
import sys
import pytest
from fastapi.testclient import TestClient
from lastcopy.config import Settings, ROOT
from scripts.build_stage2_fixtures import example, pack


def setup_store(tmp_path, case='stranded'):
    assert importlib.util.find_spec('lastcopy.store'), 'Persistent registered-input run store is not implemented'
    from lastcopy.store import RunStore
    from lastcopy.models import RunRequest
    store = RunStore(tmp_path, Settings({'SAMPLE_MODE': 'true'}))
    data = example(case)
    m = store.register('manifest', json.dumps(data['run']).encode())
    d = store.register('device', data['device'])
    s = store.register('server', pack({'server-snapshot.json': json.dumps(data['snapshot']), 'server-payload.zip': data['server']}))
    request = RunRequest(manifest_id=m.input_id, device_input_ids=[d.input_id], server_input_id=s.input_id)
    return store, data, request


def test_persisted_idempotent_run_and_artifact_integrity(tmp_path):
    store, data, req = setup_store(tmp_path)
    assert store.enqueue(req).state == 'queued'
    store.drain()
    assert store.get(data['run']['run_id']).state == 'completed'
    report = json.loads(store.artifact(data['run']['run_id'], 'report.json'))
    assert sorted(f['verdict'] for f in report['findings']) == ['MISSING_SUBMISSION', 'MISSING_SUBMISSION', 'PRESERVED']
    assert not report['coverage']['complete']
    hashes = store.get(data['run']['run_id']).output_hashes
    import hashlib
    for name, value in hashes.items():
        assert hashlib.sha256(store.artifact(data['run']['run_id'], name)).hexdigest() == value
    from lastcopy.store import RunStore
    again = RunStore(tmp_path, Settings({'SAMPLE_MODE': 'true'}))
    assert again.enqueue(req).state == 'completed'
    assert again.artifact(data['run']['run_id'], 'report.json') == store.artifact(data['run']['run_id'], 'report.json')
    assert b'provider_call' not in again.artifact(data['run']['run_id'], 'events.jsonl')


def test_cancel_queued_run_is_terminal_without_a_report(tmp_path):
    store, data, req = setup_store(tmp_path)
    store.enqueue(req)
    assert store.cancel(data['run']['run_id']).state == 'cancelled'
    store.drain()
    assert store.get(data['run']['run_id']).state == 'cancelled'
    with pytest.raises(KeyError): store.artifact(data['run']['run_id'], 'report.json')


def test_run_id_cannot_overwrite_another_request(tmp_path):
    store, data, req = setup_store(tmp_path)
    store.enqueue(req)
    data['run']['expected_device_ids'].append('other-device')
    other = store.register('manifest', json.dumps(data['run']).encode())
    with pytest.raises(ValueError, match='already'):
        store.enqueue(req.model_copy(update={'manifest_id': other.input_id}))


def test_api_rejects_filesystem_paths_and_runs_registered_inputs(tmp_path, monkeypatch):
    store, data, req = setup_store(tmp_path, 'export')
    from lastcopy.api import app, get_store
    app.dependency_overrides[get_store] = lambda: store
    try:
        with TestClient(app) as client:
            assert client.post('/run', json={'manifest_path': 'C:/private/.env'}).status_code == 422
            assert client.post('/run', json={**req.model_dump(), 'server_input_id': 'f' * 64}).status_code == 404
            response = client.post('/run', json=req.model_dump())
            assert response.status_code == 202
            rid = data['run']['run_id']
            assert client.get('/runs/' + rid).json()['state'] == 'completed'
            report = client.get('/runs/' + rid + '/artifacts/report.json').json()
            assert report['findings'][0]['verdict'] == 'EXPORT_VIEW_ONLY'
            assert not report['findings'][0]['recovery_eligible']
            assert client.get('/runs/' + rid + '/artifacts/not-registered').status_code == 404
            assert client.post('/run', content=b' ' * 65537, headers={'Content-Type': 'application/json'}).status_code == 413
    finally:
        app.dependency_overrides.clear()


def test_running_cancellation_is_persisted_and_does_not_publish(tmp_path, monkeypatch):
    store, data, req = setup_store(tmp_path)
    import lastcopy.store as module
    actual = module.reconcile
    def cancel_during_comparison(*args, **kwargs):
        event = kwargs['event']
        def progress(kind, details):
            event(kind, details)
            store.cancel(data['run']['run_id'])
        return actual(*args, **{**kwargs, 'event': progress})
    monkeypatch.setattr(module, 'reconcile', cancel_during_comparison)
    store.enqueue(req)
    store.drain()
    assert store.get(data['run']['run_id']).state == 'cancelled'
    with pytest.raises(KeyError): store.artifact(data['run']['run_id'], 'report.json')


def test_restart_marks_unfinished_running_job_interrupted(tmp_path):
    store, data, req = setup_store(tmp_path)
    store.enqueue(req)
    with store.connect() as c:
        c.execute("UPDATE jobs SET state='running'")  # Simulated previous process death, no runner lease held.
    from lastcopy.store import RunStore
    resumed = RunStore(tmp_path, Settings({'SAMPLE_MODE': 'true'}))
    resumed.drain()
    assert resumed.get(data['run']['run_id']).state == 'interrupted'
    with pytest.raises(KeyError): resumed.artifact(data['run']['run_id'], 'report.json')


def test_source_tampering_fails_without_rewriting_original_or_publishing(tmp_path):
    store, data, req = setup_store(tmp_path)
    store.enqueue(req)
    with store.connect() as c:
        c.execute('UPDATE inputs SET data=? WHERE id=?', (b'changed', req.device_input_ids[0]))
    store.drain()
    status = store.get(data['run']['run_id'])
    assert status.state == 'failed' and 'integrity' in status.error
    with pytest.raises(KeyError): store.artifact(data['run']['run_id'], 'report.json')


def test_queue_limit_and_lease_prevent_unbounded_parallel_jobs(tmp_path):
    store, data, req = setup_store(tmp_path)
    for i in range(4):
        data['run']['run_id'] = 'queued-' + str(i)
        mid = store.register('manifest', json.dumps(data['run']).encode()).input_id
        store.enqueue(req.model_copy(update={'manifest_id': mid}))
    data['run']['run_id'] = 'overflow'
    mid = store.register('manifest', json.dumps(data['run']).encode()).input_id
    with pytest.raises(ValueError, match='queue'):
        store.enqueue(req.model_copy(update={'manifest_id': mid}))
    with store.lease() as held:
        assert held
        store.drain()
        assert store.get('queued-0').state == 'queued'


def test_cli_uses_same_report_and_keeps_input_bytes_unchanged(tmp_path):
    from scripts.build_stage2_fixtures import build
    build()
    fixture = ROOT / 'fixtures/stage2/history'
    before = {p.name: p.read_bytes() for p in fixture.iterdir()}
    output = tmp_path / 'out'
    command = [sys.executable, '-m', 'scripts.run', '--data-dir', str(tmp_path / 'db'), 'run',
        '--manifest', str(fixture / 'run-manifest.json'), '--device', str(fixture / 'device.zip'),
        '--server-manifest', str(fixture / 'server-snapshot.json'), '--server-payload', str(fixture / 'server-payload.zip'), '--output', str(output)]
    done = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stdout + done.stderr
    report = json.loads((output / 'report.json').read_bytes())
    assert report['findings'][0]['original_retained_in_history']
    assert report['findings'][0]['verdict'] == 'PRESERVED'
    assert {p.name: p.read_bytes() for p in fixture.iterdir()} == before


def test_api_exposes_cancelled_and_failed_states_without_success_artifacts(tmp_path):
    store, data, req = setup_store(tmp_path)
    from lastcopy.api import app, get_store
    app.dependency_overrides[get_store] = lambda: store
    try:
        store.enqueue(req)
        with TestClient(app) as client:
            rid = data['run']['run_id']
            assert client.post('/runs/' + rid + '/cancel').json()['state'] == 'cancelled'
            assert client.get('/runs/' + rid + '/artifacts/report.json').status_code == 404
            assert client.post('/runs/not-found/cancel').status_code == 404
            assert b'cancelled' in client.get('/runs/' + rid + '/events').content
        data['run']['run_id'] = 'failed-integrity'
        mid = store.register('manifest', json.dumps(data['run']).encode()).input_id
        store.enqueue(req.model_copy(update={'manifest_id': mid}))
        with store.connect() as c:
            c.execute('UPDATE inputs SET data=? WHERE id=?', (b'tampered', req.device_input_ids[0]))
        store.drain()
        with TestClient(app) as client:
            assert client.get('/runs/failed-integrity').json()['state'] == 'failed'
            assert client.get('/runs/failed-integrity/artifacts/report.json').status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_output_tampering_is_rejected(tmp_path):
    store, data, req = setup_store(tmp_path)
    store.enqueue(req)
    store.drain()
    with store.connect() as c:
        c.execute("UPDATE artifacts SET data=? WHERE name='report.json'", (b'false success',))
    from lastcopy.inventory import ImportRejected
    with pytest.raises(ImportRejected, match='integrity'):
        store.artifact(data['run']['run_id'], 'report.json')


def test_registration_api_rejects_hostile_and_oversized_uploads(tmp_path):
    store, data, req = setup_store(tmp_path)
    from lastcopy.api import app, get_store
    from scripts.build_stage2_fixtures import pack
    app.dependency_overrides[get_store] = lambda: store
    try:
        with TestClient(app) as client:
            assert client.post('/inputs/device', content=pack({'../escape': b'bad'})).status_code == 422
            assert client.post('/inputs/server', content=pack({'server-payload.zip': data['server']})).status_code == 422
            store.settings = Settings({'SAMPLE_MODE': 'true', 'MAX_UPLOAD_BYTES': '32'})
            assert client.post('/inputs/device', content=b'x' * 33).status_code == 413
    finally:
        app.dependency_overrides.clear()


def test_first_request_uses_loaded_server_store_configuration(tmp_path, monkeypatch):
    from lastcopy.api import get_store
    monkeypatch.delenv('LASTCOPY_DATA_DIR', raising=False)
    monkeypatch.setattr(Settings, 'load', classmethod(lambda cls: cls({'SAMPLE_MODE': 'true', 'LASTCOPY_DATA_DIR': str(tmp_path)})))
    # Reading the directory before loading .env would split initial uploads and
    # later jobs into different stores, making newly registered IDs disappear.
    store = get_store()
    assert store.directory == tmp_path.resolve()
