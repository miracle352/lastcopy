"""UI adapters must preserve scope, real comparisons, persisted review and privacy."""
import json
import socket
import pytest
from fastapi.testclient import TestClient
from lastcopy.config import Settings
from lastcopy.store import RunStore


@pytest.fixture
def ui(tmp_path):
    from lastcopy.api import app,get_store
    store=RunStore(tmp_path,Settings({'SAMPLE_MODE':'true'}))
    app.dependency_overrides[get_store]=lambda:store
    with TestClient(app, base_url='http://127.0.0.1:8000') as client: yield client,store
    app.dependency_overrides.clear()


def test_sample_real_comparator_persisted_evidence_and_bundle(ui,monkeypatch):
    client,store=ui
    from lastcopy.ui import Workspace
    # Any external service construction is a bug in the offline sample path.
    monkeypatch.setattr('lastcopy.odk_recovery.CentralRecovery.__init__',lambda *a,**k:pytest.fail('Sample contacted Central'))
    draft=client.post('/ui/samples/media').json()
    assert 'request' in draft
    started=client.post('/ui/runs/'+draft['run_id']+'/start',json={})
    assert started.status_code==202
    rid=started.json()['run_id']
    view=client.get('/ui/runs/'+rid).json()
    assert view['report']['findings'][0]['verdict']=='MISSING_ATTACHMENT'
    assert view['manifest']['mode']=='sample' and view['report']['provider_calls']==0
    fid=view['report']['findings'][0]['finding_id']
    evidence=client.get('/ui/runs/'+rid+'/findings/'+fid).json()
    assert evidence['source_files'] and evidence['receipts']
    assert any(r['xml_path'] and r['repeat_indices'] for r in evidence['receipts'])
    assert client.get('/ui/runs/'+rid+'/downloads/report.txt').status_code==200
    plan=client.post('/ui/runs/'+rid+'/plans',json={'finding_id':fid}).json()
    assert 'plan_id' in plan
    assert client.get('/recovery/plans/'+plan['plan_id']+'/bundle').status_code==200
    assert client.get('/ui/runs/'+rid).json()['plans'][0]['plan']['plan_id']==plan['plan_id']
    checked=client.post('/ui/runs/'+rid+'/sample-readback').json()
    after=client.post('/run',json=checked['request']).json()['run_id']
    assert client.get('/ui/runs/'+after).json()['report']['findings'][0]['verdict']=='PRESERVED'
    assert client.get('/ui/runs/'+after).json()['parent_run_id']==rid
    # A new service instance reads the same ledger after browser/server reload.
    assert Workspace(store).view(rid)['sample_readback_run_id']==after
    assert client.post('/recovery/plans/'+plan['plan_id']+'/apply',json={'plan_sha256':plan['plan_sha256'],'target':plan['target']}).status_code==409


def test_import_roster_scope_and_path_rejection(ui):
    client,store=ui
    from scripts.build_stage2_fixtures import example,pack
    data=example('stranded')
    device=client.post('/ui/devices',content=data['device'],headers={'Content-Type':'application/zip'}).json()
    assert device['inventory']['manifest']['device_id']=='device-41'
    server=client.post('/inputs/server',content=pack({'server-snapshot.json':json.dumps(data['snapshot']),'server-payload.zip':data['server']})).json()
    body={'device_input_ids':[device['input_id']],'expected_device_ids':['device-41','missing-device'],
        'server_input_id':server['input_id'],'source':'snapshot','captured_run_reference':'authored-test-capture','confirm_scope':True}
    draft=client.post('/ui/prepare',json=body)
    # Imported captures are Replay and cannot silently become a sample or live connection.
    assert draft.status_code==409  # server is in explicit SAMPLE_MODE
    assert client.post('/ui/prepare',json={'path':'C:/private'}).status_code==422
    assert client.post('/ui/devices',content=b'not zip').status_code==422
    assert client.get('/ui/runs/not-found/findings/x').status_code==404


def test_replay_retains_capture_reference_and_missing_coverage(tmp_path):
    from lastcopy.ui import Workspace
    from scripts.build_stage2_fixtures import example,pack
    from lastcopy.models import UIPrepareRequest
    store=RunStore(tmp_path,Settings({'SAMPLE_MODE':'false'})); workspace=Workspace(store)
    data=example('stranded')
    d=workspace.device(data['device'])
    s=store.register('server',pack({'server-snapshot.json':json.dumps(data['snapshot']),'server-payload.zip':data['server']}))
    draft=workspace.prepare(UIPrepareRequest(device_input_ids=[d['input_id']],expected_device_ids=['device-41','missing-device'],
        server_input_id=s.input_id,source='snapshot',confirm_scope=True,captured_run_reference='captured-run-7'))
    from lastcopy.models import RunRequest
    store.enqueue(RunRequest.model_validate(draft['request'])); store.drain()
    view=Workspace(store).view(draft['run_id'])
    assert view['manifest']['mode']=='replay' and view['captured_run_reference']=='captured-run-7'
    assert view['report']['coverage']['missing_devices']==['missing-device']
    assert not view['report']['coverage']['complete']
    assert not any(f['recovery_eligible'] for f in view['report']['findings'])


def test_trace_download_redacts_imported_values(ui):
    client,store=ui
    draft=client.post('/ui/samples/media').json(); rid=client.post('/run',json=draft['request']).json()['run_id']
    text=client.get('/ui/runs/'+rid+'/downloads/trace.jsonl').text
    assert not any(json.loads(line).get('event') in ('model','sql') for line in text.splitlines())
    assert 'redaction' in text
    assert 'Bearer ' not in text


def test_export_selections_persist_without_credentials_or_restoring_confirmation(ui):
    client,store=ui
    from scripts.build_stage2_fixtures import example
    d=client.post('/ui/devices',content=example('media')['device']).json()
    body={'device_input_ids':[d['input_id']],'roster':'device-41\nmissing-device','source':'snapshot','captured_run_reference':'capture-7'}
    saved=client.post('/ui/imports',json=body)
    assert saved.status_code==201
    sid=saved.json()['session_id']
    restored=client.get('/ui/imports/'+sid).json()
    assert restored['roster']==body['roster'] and restored['devices'][0]['input_id']==d['input_id']
    assert 'confirm_scope' not in restored and 'token' not in restored
    assert client.post('/ui/imports',json=dict(body,password='never accepted')).status_code==422
    assert client.get('/ui/imports/C:/private').status_code==404


def test_readback_checkpoint_does_not_write_and_resolves_new_capture_files(tmp_path):
    from tests.test_stage4 import setup,reviewed
    from lastcopy.ui import Workspace
    engine,remote,data,finding=setup(tmp_path,'media')
    plan=reviewed(engine,data,finding)
    check=engine.recheck(plan['plan_id'])
    assert check['state']=='ready' and not remote.posts
    for sha in check['capture_hashes']: assert engine.evidence(plan['plan_id'],sha)
    remote.restored=True
    check=engine.recheck(plan['plan_id'])
    assert check['state']=='preserved' and not remote.posts
    view=Workspace(engine.store).view(data['run']['run_id'])
    assert view['current_report']['findings'][0]['verdict']=='PRESERVED'
    assert Workspace(engine.store).finding(data['run']['run_id'],finding['finding_id'])['source_files']


def test_server_restart_marks_only_unleased_running_comparisons_interrupted(ui):
    client,store=ui
    draft=client.post('/ui/samples/media').json()
    from lastcopy.models import RunRequest
    store.enqueue(RunRequest.model_validate(draft['request']))
    with store.connect() as c: c.execute("UPDATE jobs SET state='running' WHERE run_id=?",(draft['run_id'],))
    with store.lease() as held:
        assert held
        store.recover_interrupted()
        assert store.get(draft['run_id']).state=='running'
    store.recover_interrupted()
    assert store.get(draft['run_id']).state=='interrupted'
    assert client.get('/ui/runs/'+draft['run_id']).json()['current_report'] is None


def test_connected_dispatch_failure_is_separate_and_never_sample_substitution(tmp_path,monkeypatch):
    from lastcopy.ui import Workspace
    from lastcopy.ui_investigation import UIInvestigation
    from scripts.build_stage2_fixtures import example,pack
    from lastcopy.models import RunManifest,RunRequest
    from unittest.mock import Mock
    store=RunStore(tmp_path,Settings({'SAMPLE_MODE':'false'}));ws=Workspace(store)
    data=example('media');run=RunManifest.model_validate(dict(data['run'],mode='connected'))
    d=store.register('device',data['device']);s=store.register('server',pack({'server-snapshot.json':json.dumps(data['snapshot']),'server-payload.zip':data['server']}))
    draft=ws.draft(run,[d.input_id],s.input_id,sample_case=None,parent_run_id=None,captured_run_reference=None,provenance='Authenticated configured Central capture')
    store.enqueue(RunRequest.model_validate(draft['request']));store.drain()
    monkeypatch.setattr('lastcopy.ui_investigation.subprocess.Popen',Mock(side_effect=OSError('launch failed')))
    state=UIInvestigation(store).start(run.run_id)
    assert state['state']=='failed' and not state['events'] and state['result'] is None
    assert ws.view(run.run_id)['current_report']['findings'][0]['verdict']=='MISSING_ATTACHMENT'
    assert UIInvestigation(store).start(run.run_id)['attempt_id']==state['attempt_id']


def test_sample_cannot_dispatch_connected_worker(ui,monkeypatch):
    client,store=ui
    from lastcopy.ui_investigation import UIInvestigation
    monkeypatch.setattr('lastcopy.ui_investigation.subprocess.Popen',lambda *a,**k:pytest.fail('Sample spawned provider worker'))
    d=client.post('/ui/samples/media').json()
    assert client.post('/ui/runs/'+d['run_id']+'/start',json={}).status_code==202
    assert client.get('/ui/runs/'+d['run_id']).json()['investigation'] is None
    with pytest.raises(ValueError): UIInvestigation(store).start(d['run_id'])


def test_values_are_read_from_actual_ordered_xml_and_current_edit(ui):
    client,_=ui
    d=client.post('/ui/samples/history').json();rid=client.post('/run',json=d['request']).json()['run_id']
    evidence=client.get('/ui/runs/'+rid+'/findings/finding-1').json()
    assert evidence['server_xml_available'] and evidence['current_edit_available']
    site=next(v for v in evidence['compared_values'] if v['path'].endswith('site[1]'))
    assert site['source_value']==site['server_value']=='0017'
    assert site['current_edit_value']=='intentional edit'
    repeated=[v for v in evidence['compared_values'] if '/{urn:lastcopy:test}reading[' in v['path'] and v['path'].endswith('value[1]')]
    assert len(repeated)==2 and repeated[0]['occurrence_indices']!=repeated[1]['occurrence_indices']


def test_dead_connected_supervisor_is_interrupted_not_replayed(tmp_path):
    from lastcopy.ui_investigation import UIInvestigation
    store=RunStore(tmp_path,Settings({'SAMPLE_MODE':'false'}));job=UIInvestigation(store)
    with store.connect() as c:c.execute("INSERT INTO ui_investigations VALUES('run-a','attempt-a','running',NULL)")
    lock=RunStore(job.directory('run-a','attempt-a').parent/'worker-lock-attempt-a',store.settings)
    with lock.lease() as held:
        assert held and job.status('run-a')['state']=='running'
    assert job.status('run-a')['state']=='interrupted'
    assert 'not automatically replayed' in job.status('run-a')['error']
