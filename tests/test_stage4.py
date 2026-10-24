"""Independent stateful recovery controls; fake transport is never live evidence."""
import copy
import json
import pytest
from lastcopy.config import Settings
from lastcopy.inventory import read_archive, digest
from lastcopy.models import RunRequest
from lastcopy.store import RunStore
from scripts.build_stage2_fixtures import example, pack


class Target:
    def __init__(self, case='stranded'):
        self.case = case
        self.created = False
        self.restored = False
        self.posts = []
        self.crash = False
        self.changed = False

    def capture(self, run):
        data = example('conflict' if self.changed else ('complete' if self.created or self.restored else self.case))
        # Retain all device submissions for the stranded control.
        if self.created and self.case == 'stranded':
            original = example('stranded')
            data = original
            data = filled(data)
        return json.dumps(data['snapshot']).encode(), data['server']

    def write(self, plan, files, filename=None):
        self.posts.append(filename or 'submission')
        self.created = filename is None
        self.restored = filename is not None
        if self.crash:
            self.crash = False
            raise KeyboardInterrupt('process lost after server accepted')
        return {'method': 'POST', 'status': 201 if filename is None else 200}


def filled(data):
    # Authored target state after recovering b; do not derive expected outcomes from comparator.
    d = copy.deepcopy(data)
    sf = read_archive(d['server'], Settings({}))
    a = d['snapshot']['versions'][0]
    b = copy.deepcopy(a)
    b['version_id'] = b['logical_submission_id'] = 'uuid:41-b'
    b['xml_path'] = 'raw/b/original.xml'
    sf[b['xml_path']] = sf[a['xml_path']].replace(b'uuid:41-a', b'uuid:41-b')
    b['xml_sha256'] = digest(sf[b['xml_path']])
    for m in b['media']:
        m['version_id'] = 'uuid:41-b'
    for r in list(d['snapshot']['receipts']):
        if r['version_id'] == 'uuid:41-a':
            r = copy.deepcopy(r)
            r['version_id'] = 'uuid:41-b'
            r['evidence_id'] += '-b'
            if r['source_file'] == a['xml_path']:
                r['source_file'] = b['xml_path']
                r['response_sha256'] = b['xml_sha256']
            elif r['source_file'].endswith('attachments.json'):
                r['source_file'] = 'raw/b/attachments.json'
                sf[r['source_file']] = sf['raw/a/attachments.json'].replace(b'uuid:41-a', b'uuid:41-b')
                r['response_sha256'] = digest(sf[r['source_file']])
            d['snapshot']['receipts'].append(r)
    for m in b['media']:
        m['readback_receipt_id'] += '-b'
    d['snapshot']['versions'].append(b)
    d['snapshot']['attachment_listing_receipt_ids']['uuid:41-b'] = d['snapshot']['attachment_listing_receipt_ids']['uuid:41-a'] + '-b'
    scope = json.loads(sf['scope.json'])
    scope['versions'].append({k:b[k] for k in scope['versions'][0]})
    sf['scope.json'] = json.dumps(scope).encode()
    for r in d['snapshot']['receipts']:
        if r['source_file'] == 'scope.json': r['response_sha256'] = digest(sf['scope.json'])
    d['snapshot']['receipt_ids'] = [r['evidence_id'] for r in d['snapshot']['receipts']]
    d['server'] = pack(sf)
    d['snapshot']['archive_sha256'] = digest(d['server'])
    return d


def setup(tmp_path, case='stranded'):
    from lastcopy.recovery import RecoveryEngine
    data = example(case)
    store = RunStore(tmp_path, Settings({'SAMPLE_MODE':'false'}))
    ids = {k: store.register(k, v).input_id for k,v in {
        'device':data['device'], 'manifest':json.dumps(data['run']).encode(),
        'server':pack({'server-snapshot.json':json.dumps(data['snapshot']), 'server-payload.zip':data['server']})}.items()}
    req = RunRequest(manifest_id=ids['manifest'], device_input_ids=[ids['device']], server_input_id=ids['server'])
    store.enqueue(req); store.drain()
    remote = Target(case)
    engine = RecoveryEngine(store, data['run']['destination'], remote, allow_fixture=True)
    report = json.loads(store.artifact(data['run']['run_id'], 'report.json'))
    candidate = next((f for f in report['findings'] if f['recovery_eligible']), report['findings'][0])
    return engine, remote, data, candidate


def reviewed(engine, data, finding):
    plan = engine.stage(data['run']['run_id'], finding['finding_id'])
    engine.review(plan['plan_id'], plan['plan_sha256'], plan['target'])
    return plan


def test_lost_ack_restart_reads_before_retry(tmp_path):
    engine, remote, data, finding = setup(tmp_path)
    plan = reviewed(engine, data, finding)
    remote.crash = True
    with pytest.raises(KeyboardInterrupt): engine.apply(plan['plan_id'])
    from lastcopy.recovery import RecoveryEngine
    restarted = RecoveryEngine(engine.store, engine.target, remote, allow_fixture=True)
    result = restarted.apply(plan['plan_id'])
    assert result['state'] == 'verified'
    assert remote.posts == ['submission']
    assert result['disappeared'] == ['MISSING_SUBMISSION']
    assert result['after']['findings'][1]['verdict'] == 'PRESERVED'
    assert restarted.apply(plan['plan_id']) == result
    assert remote.posts == ['submission']


@pytest.mark.parametrize('change', ['version', 'conflict'])
def test_change_between_review_and_apply_blocks(tmp_path, change):
    engine, remote, data, finding = setup(tmp_path, 'media')
    plan = reviewed(engine, data, finding)
    remote.changed = True
    if change == 'version':
        original = remote.capture
        def capture(run):
            d = example('history'); return json.dumps(d['snapshot']).encode(), d['server']
        remote.capture = capture
    result = engine.apply(plan['plan_id'])
    assert result['state'] == 'blocked'
    assert not remote.posts


def test_missing_slot_equal_bytes_and_shared_name(tmp_path):
    engine, remote, data, finding = setup(tmp_path, 'media')
    plan = reviewed(engine, data, finding)
    assert plan['media_filenames'] == ['b.bin']
    bundle = read_archive(engine.bundle(plan['plan_id']), Settings({}))
    assert bundle['files/projects/field-a/instances/a-native/b.bin'] == read_archive(data['device'], Settings({}))['projects/field-a/instances/a-native/b.bin']
    result = engine.apply(plan['plan_id'])
    assert remote.posts == ['b.bin']
    assert result['state'] == 'verified'
    assert result['remaining'] == []
    assert result['source_hashes_verified']


def test_review_target_and_sample_guard(tmp_path):
    engine, remote, data, finding = setup(tmp_path)
    plan = engine.stage(data['run']['run_id'], finding['finding_id'])
    with pytest.raises(ValueError): engine.apply(plan['plan_id'])
    with pytest.raises(ValueError): engine.review(plan['plan_id'], '0'*64, plan['target'])
    wrong = dict(plan['target'], project_id=99)
    with pytest.raises(ValueError): engine.review(plan['plan_id'], plan['plan_sha256'], wrong)
    engine.store.settings = Settings({'SAMPLE_MODE':'true'})
    with pytest.raises(ValueError): engine.apply(plan['plan_id'])
    assert not remote.posts


@pytest.mark.parametrize('case', ['history', 'export', 'conflict'])
def test_no_plan_for_preserved_export_history_conflict(tmp_path, case):
    engine, remote, data, finding = setup(tmp_path, case)
    with pytest.raises(ValueError): engine.stage(data['run']['run_id'], finding['finding_id'])
    assert not remote.posts


def test_timeout_after_success_readback_on_resume(tmp_path):
    engine, remote, data, finding = setup(tmp_path,'media')
    plan = reviewed(engine,data,finding)
    native = remote.write
    def timeout(*args,**kwargs):
        native(*args,**kwargs)
        raise TimeoutError('acknowledgement unavailable')
    remote.write = timeout
    result = engine.apply(plan['plan_id'])
    assert result['state']=='blocked'
    assert len(remote.posts)==1
    remote.write = native
    assert engine.apply(plan['plan_id'])['state']=='verified'
    assert len(remote.posts)==1


@pytest.mark.parametrize('broken',['media','completion','xform','scope'])
def test_uncertain_sources_never_become_automatic_recovery(tmp_path,broken):
    from lastcopy.recovery import RecoveryEngine
    data = example('media')
    files = read_archive(data['device'],Settings({}))
    m = json.loads(files['device-manifest.json'])
    if broken=='media': del files['projects/field-a/instances/a-native/b.bin']
    elif broken=='completion': m['instances'][0]['completion_status']='unknown'
    elif broken=='xform':
        files['projects/field-a/forms/original.xml'] = files['projects/field-a/forms/original.xml'].replace(b'version="1"',b'version="2"')
    elif broken=='scope': data['run']['destination']['project_id']=99
    files['device-manifest.json']=json.dumps(m).encode()
    store=RunStore(tmp_path,Settings({'SAMPLE_MODE':'false'}))
    req=RunRequest(manifest_id=store.register('manifest',json.dumps(data['run']).encode()).input_id,
        device_input_ids=[store.register('device',pack(files)).input_id],
        server_input_id=store.register('server',pack({'server-snapshot.json':json.dumps(data['snapshot']),'server-payload.zip':data['server']})).input_id)
    store.enqueue(req); store.drain()
    report=json.loads(store.artifact(data['run']['run_id'],'report.json'))
    engine=RecoveryEngine(store,data['run']['destination'],Target('media'),allow_fixture=True)
    with pytest.raises(ValueError): engine.stage(data['run']['run_id'],report['findings'][0]['finding_id'])


def test_bundle_result_evidence_integrity_and_serialization(tmp_path):
    engine,remote,data,finding=setup(tmp_path,'media')
    plan=reviewed(engine,data,finding)
    lock=RunStore(engine.store.directory/'recovery-lock',engine.store.settings)
    with lock.lease() as held:
        assert held
        with pytest.raises(ValueError,match='active'): engine.apply(plan['plan_id'])
    assert not remote.posts
    result=engine.apply(plan['plan_id'])
    for pair in result['capture_hashes']:
        for sha in pair: assert digest(engine.evidence(plan['plan_id'],sha))==sha
    with engine.store.connect() as c:
        c.execute('UPDATE recovery_plans SET bundle=? WHERE id=?',(b'broken',plan['plan_id']))
    with pytest.raises(ValueError,match='integrity'): engine.bundle(plan['plan_id'])


def test_api_and_cli_bundle_review_apply_same_plan(tmp_path,monkeypatch,capsys):
    from fastapi.testclient import TestClient
    from lastcopy.api import app,get_store,get_recovery
    from scripts import recover
    engine,remote,data,finding=setup(tmp_path,'media')
    app.dependency_overrides[get_store]=lambda:engine.store
    app.dependency_overrides[get_recovery]=lambda:engine
    from types import SimpleNamespace
    remote.client=SimpleNamespace(close=lambda:None)
    monkeypatch.setattr('lastcopy.api.CentralRecovery',lambda _:remote)
    try:
        with TestClient(app) as client:
            response=client.post('/recovery/plans',json={'run_id':data['run']['run_id'],'finding_id':finding['finding_id']})
            assert response.status_code==201
            plan=response.json(); base='/recovery/plans/'+plan['plan_id']
            bundle=client.get(base+'/bundle')
            assert bundle.status_code==200
            assert bundle.content==engine.bundle(plan['plan_id'])
            assert client.post('/recovery/plans',json={'path':'C:/secret'}).status_code==422
            body={'plan_sha256':plan['plan_sha256'],'target':plan['target']}
            assert client.post(base+'/review',json=body).json()['state']=='reviewed'
            assert client.post(base+'/apply',json=body,headers={'Origin':'https://hostile.invalid'}).status_code==403
            assert client.get(base+'/result').json()['state']=='not_applied'
            applied=client.post(base+'/apply',json=body)
            assert applied.status_code==200 and applied.json()['state']=='verified'
            assert remote.posts==['b.bin']
            assert client.post(base+'/apply',json=body).json()==applied.json()
            assert remote.posts==['b.bin']
        monkeypatch.setattr(recover.Settings,'load',lambda:engine.store.settings)
        monkeypatch.setattr(recover,'configured_target',lambda _:engine.target)
        target=tmp_path/'bundle.zip'
        assert recover.main(['--data-dir',str(tmp_path),'bundle',plan['plan_id'],'--output',str(target)])==0
        assert target.read_bytes()==bundle.content
    finally: app.dependency_overrides.clear()


def test_authenticated_failure_never_means_absence(tmp_path):
    engine,remote,data,finding=setup(tmp_path,'media')
    plan=reviewed(engine,data,finding)
    def unauthorized(run): raise ValueError('Central GET failed HTTP 401; absence not established')
    remote.capture=unauthorized
    result=engine.apply(plan['plan_id'])
    assert result['state']=='blocked' and result['after'] is None
    assert not remote.posts


@pytest.mark.parametrize('race',['version','slot','conflict','unauthorized','existing-create'])
def test_native_immediate_preflight_never_overwrites(race):
    import httpx
    from lastcopy.odk_recovery import CentralRecovery
    cfg={'SAMPLE_MODE':'false','ODK_TEST_PROJECT':'true','ODK_PROJECT_ID':'7','ODK_FORM_ID':'inspection',
        'ODK_BASE_URL':'http://localhost:8384'}
    seen=[]
    xml=b'<data id="inspection"><meta><instanceID>uuid:test</instanceID></meta></data>'
    def handle(req):
        seen.append(req.method)
        if req.url.path.endswith('/versions'):
            return httpx.Response(200,json=[{'instanceId':'new' if race=='version' else 'uuid:test','current':True}])
        if req.url.path.endswith('.xml'):
            return httpx.Response(200,content=xml.replace(b'uuid:test',b'conflict') if race=='conflict' else xml)
        if req.url.path.endswith('/attachments'):
            return httpx.Response(200,json=[{'name':'missing.bin','exists':True}])
        return httpx.Response(401 if race=='unauthorized' else 200,json={})
    remote=CentralRecovery(Settings(cfg),client=httpx.Client(transport=httpx.MockTransport(handle)))
    remote.begin()
    plan={'target':remote.target,'logical_submission_id':'uuid:test','version_id':'uuid:test','xml_path':'original.xml',
        'media_paths':{'missing.bin':'missing.bin'},'media_filenames':['missing.bin']}
    with pytest.raises(ValueError):
        remote.write(plan,{'original.xml':xml,'missing.bin':b'synthetic'},None if race=='existing-create' else 'missing.bin')
    assert 'POST' not in seen


def test_changed_origin_requires_new_plan(tmp_path):
    engine,remote,data,finding=setup(tmp_path,'media')
    plan=reviewed(engine,data,finding)
    engine.store.settings=Settings({'SAMPLE_MODE':'false','ODK_BASE_URL':'https://another.example.invalid'})
    with pytest.raises(ValueError,match='origin'): engine.apply(plan['plan_id'])
    assert not remote.posts
