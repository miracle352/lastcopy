"""Automatic comparison is read-only, bounded, scoped and durable."""
import json
import hashlib
import pytest
from fastapi.testclient import TestClient
from lastcopy.config import Settings
from lastcopy.store import RunStore
from scripts.build_stage2_fixtures import example


def setup(tmp_path,monkeypatch,**changes):
    inbox=tmp_path/'inbox';inbox.mkdir()
    values={'SAMPLE_MODE':'false','ODK_TEST_PROJECT':'true','ODK_PROJECT_ID':'7','ODK_FORM_ID':'inspection',
        'ODK_CONNECTION_ID':'synthetic-offline-only','ODK_MAPPING_REFERENCE':'authored-synthetic-stage2',
        'LASTCOPY_WATCH_INBOX':str(inbox),'LASTCOPY_WATCH_DEVICE_IDS':'["device-41"]',
        'LASTCOPY_WATCH_INTERVAL_SECONDS':'60','LASTCOPY_WATCH_MAX_CHECKS':'3',**changes}
    class Remote:
        calls=0
        def __init__(self,*a,**k):self.client=self
        def close(self):pass
        def capture(self,run):
            type(self).calls+=1;d=example('media');return json.dumps(d['snapshot']).encode(),d['server']
    monkeypatch.setattr('lastcopy.odk_recovery.CentralRecovery',Remote)
    monkeypatch.setattr('scripts.recover.CentralRecovery',Remote)
    store=RunStore(tmp_path/'store',Settings(values))
    return store,inbox,Remote


def put(inbox,data=None,name='device.zip',seal=True):
    data=data or example('media')['device'];p=inbox/name;p.write_bytes(data)
    if seal:(inbox/(name+'.ready.json')).write_text(json.dumps({'schema_version':1,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}))
    return p


def test_monitor_status_exists_and_sample_cannot_enable(tmp_path):
    from lastcopy.api import app,get_store
    app.dependency_overrides[get_store]=lambda:RunStore(tmp_path,Settings({'SAMPLE_MODE':'true'}))
    try:
        with TestClient(app,base_url='http://127.0.0.1:8000') as c:
            r=c.get('/ui/watch');assert r.status_code==200 and not r.json()['configured']
            assert c.post('/ui/watch/control',json={'action':'start'}).status_code==409
    finally:app.dependency_overrides.clear()


def test_complete_export_runs_real_comparator_once_and_keeps_source(tmp_path,monkeypatch):
    from lastcopy.monitor import Monitor
    store,inbox,remote=setup(tmp_path,monkeypatch);p=put(inbox);before=p.read_bytes()
    m=Monitor(store);m.control('start');m.tick(now=1000)
    state=m.status();assert state['last_run_id'] and state['checks_completed']==1 and remote.calls==1
    from lastcopy.ui import Workspace
    view=Workspace(store).view(state['last_run_id'])
    assert view['automatic_check'] and view['current_report']['findings'][0]['verdict']=='MISSING_ATTACHMENT'
    assert view['current_report']['provider_calls']==0 and not view['plans']
    Monitor(store).tick(now=1001)
    assert m.status()['checks_completed']==1 and remote.calls==1 and p.read_bytes()==before


def test_unfinished_or_bad_seal_never_contacts_server(tmp_path,monkeypatch):
    from lastcopy.monitor import Monitor
    store,inbox,remote=setup(tmp_path,monkeypatch);p=put(inbox,seal=False)
    m=Monitor(store);m.control('start');m.tick(now=1000)
    assert remote.calls==0 and not m.status()['last_run_id']
    (inbox/'device.zip.ready.json').write_text(json.dumps({'schema_version':1,'sha256':'0'*64,'bytes':p.stat().st_size}))
    m.tick(now=1001);assert remote.calls==0 and m.status()['input_errors']


def test_missing_device_coverage_and_hard_budget_survive_restart(tmp_path,monkeypatch):
    from lastcopy.monitor import Monitor
    store,inbox,remote=setup(tmp_path,monkeypatch,LASTCOPY_WATCH_DEVICE_IDS='["device-41","absent-device"]',LASTCOPY_WATCH_MAX_CHECKS='1')
    put(inbox);m=Monitor(store);m.control('start');m.tick(now=1000)
    from lastcopy.ui import Workspace
    report=Workspace(store).view(m.status()['last_run_id'])['current_report']
    assert not report['coverage']['complete'] and report['coverage']['missing_devices']==['absent-device']
    Monitor(store).tick(now=1061);assert remote.calls==1 and m.status()['state']=='budget_reached'


def test_pause_and_failed_authentication_never_claim_absence(tmp_path,monkeypatch):
    from lastcopy.monitor import Monitor
    store,inbox,remote=setup(tmp_path,monkeypatch);put(inbox);m=Monitor(store)
    m.control('pause');m.tick(now=1000);assert remote.calls==0
    def unavailable(*a):raise ValueError('Authentication rejected')
    monkeypatch.setattr(remote,'capture',unavailable);m.control('start');m.tick(now=1001)
    assert m.status()['state']=='error' and not m.status()['last_run_id']
    with store.connect() as c:assert c.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0]==0
    m.tick(now=1002);assert m.status()['checks_completed']==1  # bounded retry cadence


def test_crash_after_queued_job_reuses_persisted_run_id(tmp_path,monkeypatch):
    from lastcopy.monitor import Monitor
    store,inbox,remote=setup(tmp_path,monkeypatch);put(inbox);m=Monitor(store);m.control('start')
    drain=store.drain
    monkeypatch.setattr(store,'drain',lambda:(_ for _ in ()).throw(KeyboardInterrupt('lost process before acknowledgement')))
    with pytest.raises(KeyboardInterrupt):m.tick(now=1000)
    with store.connect() as c:rid=c.execute('SELECT run_id FROM jobs').fetchone()[0]
    monkeypatch.setattr(store,'drain',drain);Monitor(store).tick(now=1001)
    assert m.status()['last_run_id']==rid and remote.calls==1
    with store.connect() as c:assert c.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]==1


def test_collection_target_cannot_write_or_publish_to_sponsors(tmp_path,monkeypatch):
    from lastcopy.odk_recovery import CentralRecovery,configured_read_target
    values={'SAMPLE_MODE':'false','ODK_BASE_URL':'http://localhost:8384','ODK_READ_PROJECT_ID':'3',
        'ODK_READ_FORM_ID':'water','ODK_READ_PROJECT_NAME':'Water Point Condition Check'}
    settings=Settings(values);remote=CentralRecovery(settings,read_only=True)
    try:
        assert configured_read_target(settings)['environment']=='read_only_collection'
        with pytest.raises(ValueError,match='cannot write'):remote.write({'target':remote.target},{})
    finally:remote.client.close()
    from lastcopy.models import RunManifest
    from lastcopy.ui import Workspace
    from lastcopy.ui_investigation import UIInvestigation
    from scripts.run import bundle_snapshot
    d=example('media');store=RunStore(tmp_path/'private',Settings(values));ws=Workspace(store)
    run=RunManifest.model_validate(dict(d['run'],mode='connected',destination={**d['run']['destination'],'environment':'read_only_collection'}))
    device=store.register('device',d['device']);server=store.register('server',bundle_snapshot(json.dumps(d['snapshot']).encode(),d['server']))
    ws.draft(run,[device.input_id],server.input_id,provenance='Authenticated configured Central capture')
    with pytest.raises(ValueError,match='publication is disabled'):UIInvestigation(store).start(run.run_id)


def test_unexpected_device_and_hostile_xml_never_start_capture(tmp_path,monkeypatch):
    from lastcopy.monitor import Monitor
    from scripts.build_stage2_fixtures import pack
    store,inbox,remote=setup(tmp_path,monkeypatch,LASTCOPY_WATCH_DEVICE_IDS='["another-device"]');put(inbox)
    m=Monitor(store);m.control('start');m.tick(now=1000);assert remote.calls==0 and m.status()['input_errors']
    from lastcopy.inventory import read_archive
    parts=read_archive(example('media')['device'],store.settings)
    path=json.loads(parts['device-manifest.json'])['instances'][0]['xml_path']
    parts[path]=b'<!DOCTYPE data [<!ENTITY x SYSTEM "file:///secret">]><data>&x;</data>'
    put(inbox,pack(parts),name='bad.zip')
    m.tick(now=1001);assert remote.calls==0


def test_ui_sources_use_registered_ids_and_persist_reviewed_roster(tmp_path,monkeypatch):
    from lastcopy.monitor import Monitor
    from lastcopy.models import WatchSources
    store,inbox,remote=setup(tmp_path,monkeypatch)
    source=store.register('device',example('media')['device'])
    m=Monitor(store);body=WatchSources(device_input_ids=[source.input_id],expected_device_ids=['device-41','missing'])
    assert m.accept_sources(body)['expected_devices']==['device-41','missing']
    Monitor(store).tick(now=1000)
    assert m.status()['last_run_id'] and remote.calls==1
    assert m.status()['expected_devices']==['device-41','missing']
    with pytest.raises(ValueError):m.accept_sources(WatchSources(device_input_ids=[source.input_id],expected_device_ids=['other']))


def test_browser_cannot_change_monitor_path_or_target(tmp_path,monkeypatch):
    from lastcopy.api import app,get_store
    store,_,_=setup(tmp_path,monkeypatch);app.dependency_overrides[get_store]=lambda:store
    try:
        with TestClient(app,base_url='http://127.0.0.1:8000') as c:
            r=c.post('/ui/watch/sources',json={'device_input_ids':['a'*64],'expected_device_ids':['d'],'inbox':'C:/private','project_id':3})
            assert r.status_code==422
    finally:app.dependency_overrides.clear()


def test_pause_during_readback_stays_paused_after_that_read_finishes(tmp_path,monkeypatch):
    from lastcopy.monitor import Monitor
    store,inbox,remote=setup(tmp_path,monkeypatch);put(inbox);m=Monitor(store)
    capture=remote.capture
    def paused_capture(self,run):
        m.control('pause');return capture(self,run)
    monkeypatch.setattr(remote,'capture',paused_capture)
    m.control('start');m.tick(now=1000)
    assert not m.status()['enabled'] and m.status()['state']=='paused'
    assert 'paused' in m.status()['message'].lower()


def test_collection_connection_does_not_change_recovery_capture_target():
    from lastcopy.odk_recovery import CentralRecovery
    settings=Settings({'SAMPLE_MODE':'false','ODK_TEST_PROJECT':'true','ODK_BASE_URL':'http://localhost:8384',
        'ODK_PROJECT_ID':'1','ODK_FORM_ID':'inspection','ODK_RECOVERY_PROJECT_ID':'2','ODK_RECOVERY_FORM_ID':'inspection',
        'ODK_READ_PROJECT_ID':'3','ODK_READ_FORM_ID':'water','ODK_READ_PROJECT_NAME':'Water Point Condition Check'})
    recovery=CentralRecovery(settings);collection=CentralRecovery(settings,read_only=True)
    try:
        assert recovery.target['project_id']==2 and not recovery.read_only
        assert collection.target['project_id']==3 and collection.read_only
    finally:recovery.client.close();collection.client.close()
