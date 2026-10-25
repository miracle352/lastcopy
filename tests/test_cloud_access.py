"""Hosted evidence must require both a server transport key and owner session.

Removing either check exposes private runs; these tests exercise real HTTP/DB.
"""
import hashlib
import pytest
from fastapi.testclient import TestClient
from lastcopy.api import app, get_store
from lastcopy.config import Settings
from lastcopy.store import RunStore


@pytest.fixture
def cloud(tmp_path):
    salt = '01' * 16
    password = 'test-only-owner-passphrase'
    hashed = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    store = RunStore(tmp_path, Settings({'SAMPLE_MODE':'true', 'LASTCOPY_CLOUD_ACCESS':'true',
        'LASTCOPY_TRANSPORT_KEY':'t'*48, 'LASTCOPY_SESSION_KEY':'s'*48,
        'LASTCOPY_OWNER_PASSWORD_HASH':salt+':'+hashed}))
    app.dependency_overrides[get_store] = lambda:store
    with TestClient(app, base_url='https://localhost') as client:yield client,store,password
    app.dependency_overrides.clear()


def login(client,password):
    return client.post('/session/login',json={'password':password},headers={'authorization':'Bearer '+'t'*48})


def test_private_evidence_requires_transport_and_owner(cloud):
    client,store,password=cloud
    assert client.get('/ui/runs').status_code == 401
    client.headers['authorization']='Bearer '+'t'*48
    assert client.get('/ui/runs').status_code == 401
    response=login(client,password)
    assert response.status_code==200
    cookie=response.headers['set-cookie']
    assert all(flag in cookie.lower() for flag in ('httponly','secure','samesite=strict'))
    assert password not in response.text
    assert client.get('/ui/runs').status_code==200
    client.headers.pop('authorization')
    assert client.get('/ui/runs').status_code==401


def test_persistent_login_throttle_and_tamper_rejection(cloud):
    client,store,password=cloud
    for _ in range(5):assert login(client,'wrong').status_code==401
    # Rebuilding the store/service must not reset a brute-force budget.
    app.dependency_overrides[get_store]=lambda:RunStore(store.directory,store.settings)
    assert login(client,password).status_code==429
    client.cookies.set('lastcopy_session','forged',domain='localhost.local',path='/')
    assert client.get('/ui/runs',headers={'authorization':'Bearer '+'t'*48}).status_code==401


def test_logout_revokes_session_and_partial_config_fails_closed(cloud):
    client,store,password=cloud
    client.headers['authorization']='Bearer '+'t'*48
    assert login(client,password).status_code==200
    old=client.cookies.get('lastcopy_session')
    assert client.post('/session/logout').status_code==200
    client.cookies.set('lastcopy_session',old,domain='localhost.local',path='/')
    assert client.get('/ui/runs').status_code==401
    broken=Settings(dict(store.settings.values,LASTCOPY_SESSION_KEY=''))
    app.dependency_overrides[get_store]=lambda:RunStore(store.directory,broken)
    assert login(client,password).status_code==503


def test_cloud_cross_site_write_remains_blocked(cloud):
    client,_,password=cloud
    assert login(client,password).status_code==200
    assert client.post('/ui/samples/media',headers={'authorization':'Bearer '+'t'*48,
        'origin':'https://untrusted.example'}).status_code==403


def test_device_key_is_scoped_to_inbox_and_restart_is_idempotent(cloud,tmp_path):
    from scripts.build_stage2_fixtures import example
    from lastcopy.inventory import digest
    client,store,_=cloud
    inbox=tmp_path/'inbox';inbox.mkdir()
    values=dict(store.settings.values,SAMPLE_MODE='false',LASTCOPY_TRANSFER_KEY='d'*48,
        LASTCOPY_WATCH_INBOX=str(inbox),LASTCOPY_WATCH_DEVICE_IDS='["device-41"]',
        ODK_BASE_URL='https://central.example',ODK_READ_PROJECT_ID='1',ODK_READ_FORM_ID='inspection',ODK_READ_PROJECT_NAME='Test collection')
    app.dependency_overrides[get_store]=lambda:RunStore(store.directory,Settings(values))
    data=example('stranded')['device']
    headers={'authorization':'Bearer '+'d'*48,'content-type':'application/zip'}
    assert client.get('/ui/runs',headers=headers).status_code==401
    assert client.post('/device-transfer',content=data).status_code==401
    first=client.post('/device-transfer',content=data,headers=headers)
    assert first.status_code==201
    assert first.json()['sha256']==digest(data) and first.json()['preservation_proof'] is False
    assert client.post('/device-transfer',content=data,headers=headers).json()==first.json()
    assert len(list(inbox.glob('*.zip')))==1
    assert list(inbox.glob('*.zip'))[0].read_bytes()==data
    assert len(list(inbox.glob('*.ready.json')))==1
    values['LASTCOPY_WATCH_DEVICE_IDS']='["other-device"]'
    assert client.post('/device-transfer',content=data,headers=headers).status_code==409


def test_sample_mode_cannot_accept_remote_device_upload(cloud,tmp_path):
    client,store,_=cloud
    values=dict(store.settings.values,LASTCOPY_TRANSFER_KEY='d'*48)
    app.dependency_overrides[get_store]=lambda:RunStore(store.directory,Settings(values))
    assert client.post('/device-transfer',content=b'not-a-zip',headers={'authorization':'Bearer '+'d'*48}).status_code==409


def test_public_examples_use_separate_offline_store_and_cannot_read_owner_runs(cloud,monkeypatch):
    client,store,_=cloud
    monkeypatch.setattr('lastcopy.odk_recovery.CentralRecovery.__init__',lambda *a,**k:pytest.fail('Example contacted Central'))
    headers={'authorization':'Bearer '+'t'*48}
    response=client.get('/public/examples/media',headers=headers)
    assert response.status_code==200
    view=response.json()
    assert view['manifest']['mode']=='sample' and view['report']['provider_calls']==0
    assert view['report']['findings'][0]['verdict']=='MISSING_ATTACHMENT'
    assert client.get('/ui/runs/'+view['manifest']['run_id'],headers=headers).status_code==401
    with store.connect() as c:assert c.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]==0
    assert client.get('/public/examples/not-a-case',headers=headers).status_code==401


def test_device_link_can_read_only_its_run_control_and_report_bounded_state(cloud,tmp_path):
    client,store,_=cloud
    inbox=tmp_path/'inbox';inbox.mkdir()
    values=dict(store.settings.values,SAMPLE_MODE='false',LASTCOPY_TRANSFER_KEY='d'*48,
        LASTCOPY_WATCH_INBOX=str(inbox),LASTCOPY_WATCH_DEVICE_IDS='["device-41"]',
        ODK_BASE_URL='https://central.example',ODK_READ_PROJECT_ID='1',ODK_READ_FORM_ID='inspection',ODK_READ_PROJECT_NAME='Test collection')
    app.dependency_overrides[get_store]=lambda:RunStore(store.directory,Settings(values))
    response=client.get('/device-transfer/status',headers={'authorization':'Bearer '+'d'*48,'x-lastcopy-device-state':'waiting_for_records'})
    assert response.status_code==200
    assert response.json()=={'enabled':False,'interval_seconds':30,'source_device_ids':['device-41']}
    assert client.get('/ui/watch',headers={'authorization':'Bearer '+'d'*48}).status_code==401
    assert client.get('/device-transfer/status',headers={'authorization':'Bearer '+'d'*48,'x-lastcopy-device-state':'verified'}).status_code==422


def test_device_receipts_do_not_cross_inbox_or_destination_scope(cloud,tmp_path):
    from scripts.build_stage2_fixtures import example
    from lastcopy.cloud_inbox import status
    client,store,_=cloud
    inbox=tmp_path/'inbox-one';inbox.mkdir()
    values=dict(store.settings.values,SAMPLE_MODE='false',LASTCOPY_TRANSFER_KEY='d'*48,LASTCOPY_WATCH_INBOX=str(inbox),
        LASTCOPY_WATCH_DEVICE_IDS='["device-41"]',ODK_BASE_URL='https://central.example',ODK_READ_PROJECT_ID='1',
        ODK_READ_FORM_ID='inspection',ODK_READ_PROJECT_NAME='First project')
    app.dependency_overrides[get_store]=lambda:RunStore(store.directory,Settings(values))
    assert client.post('/device-transfer',content=example('stranded')['device'],headers={'authorization':'Bearer '+'d'*48}).status_code==201
    assert status(RunStore(store.directory,Settings(values)))['exports_completed']==1
    empty=tmp_path/'inbox-two';empty.mkdir()
    changed=Settings(dict(values,LASTCOPY_WATCH_INBOX=str(empty),ODK_READ_PROJECT_ID='2',ODK_READ_PROJECT_NAME='Second project'))
    other=status(RunStore(store.directory,changed))
    assert other['exports_completed']==0 and other['last_export_at'] is None
