"""Account-scoped read connection: never inherit credentials or enable recovery."""
import json
import httpx
from tests.test_accounts import provider, account_login, H
from tests.test_cloud_access import cloud


def test_connection_is_verified_private_persistent_and_read_only(cloud, monkeypatch):
    client, root, _ = cloud
    root.settings.values['ODK_BASE_URL'] = 'https://central.example.test'
    provider(monkeypatch)
    requests = []
    project_name=chr(0x2000B)*512
    private_password=chr(0x2000C)*512
    def send(request):
        requests.append((request.method, str(request.url)))
        if request.url.path == '/v1/sessions':
            return httpx.Response(200, json={'token': 'private-session'})
        if request.url.path == '/v1/projects/7':
            return httpx.Response(200, json={'id': 7, 'name': project_name})
        return httpx.Response(200, json={'xmlFormId': 'water_points', 'name': 'Water points'})
    original = httpx.Client
    monkeypatch.setattr('lastcopy.odk_recovery.httpx.Client', lambda **kw: original(transport=httpx.MockTransport(send), **kw))
    account_login(client, 'a@example.test')
    body = {'project_id': 7, 'form_id': 'water_points', 'email': 'viewer@example.test', 'password': private_password}
    r = client.post('/ui/connection/setup', headers=H, json=body)
    assert r.status_code == 200, r.text
    assert r.json()['state'] == 'connected'
    assert all(secret not in r.text for secret in (private_password, 'private-session', 'viewer@example.test'))
    settings = client.get('/ui/settings', headers=H).json()
    assert settings['connected_ready'] and settings['target']['environment'] == 'read_only_collection'
    assert settings['target']['project_id'] == 7
    assert client.get('/ui/connection', headers=H).json()['state'] == 'connected'
    # A new session reloads the private connection from disk, not browser state.
    account_login(client, 'b@example.test')
    assert not client.get('/ui/settings', headers=H).json()['connected_ready']
    account_login(client, 'a@example.test')
    assert client.get('/ui/settings', headers=H).json()['connected_ready']
    files = list((root.directory/'accounts').glob('*/central-connection.json'))
    assert len(files) == 1
    assert json.loads(files[0].read_bytes())['ODK_READ_PROJECT_ID'] == '7'
    from lastcopy.accounts import Accounts
    from lastcopy.odk_recovery import configured_target
    import pytest
    account = Accounts(root).store_for(client.cookies.get('lastcopy_session'))
    with pytest.raises(ValueError, match='Dedicated ODK test project'):
        configured_target(account.settings)
    assert all(method == 'GET' or url.endswith('/v1/sessions') for method, url in requests)


def test_connection_rejects_url_injection_failed_auth_and_wrong_scope(cloud, monkeypatch):
    client, root, _ = cloud
    root.settings.values['ODK_BASE_URL'] = 'https://central.example.test'
    provider(monkeypatch)
    account_login(client, 'a@example.test')
    body = {'project_id': 7, 'form_id': 'water_points', 'email': 'viewer@example.test', 'password': 'private-odk-password'}
    assert client.post('/ui/connection/setup', headers=H, json={**body, 'server_url': 'http://169.254.169.254'}).status_code == 422
    assert client.post('/ui/connection/setup', headers=H, json={**body, 'form_id': '../other'}).status_code == 422
    assert client.post('/ui/connection/setup', headers=H, json={**body, 'form_id': '..'}).status_code == 422
    original = httpx.Client
    monkeypatch.setattr('lastcopy.odk_recovery.httpx.Client', lambda **kw: original(transport=httpx.MockTransport(lambda r: httpx.Response(401, text='private upstream body')), **kw))
    r = client.post('/ui/connection/setup', headers=H, json=body)
    assert r.status_code == 409 and 'private upstream body' not in r.text
    assert not list((root.directory/'accounts').glob('*/central-connection.json'))
    assert not client.get('/ui/settings', headers=H).json()['connected_ready']


def test_corrupt_saved_connection_fails_closed_without_hiding_reports(cloud,monkeypatch):
    client,root,_=cloud
    provider(monkeypatch);account_login(client,'a@example.test')
    from lastcopy.accounts import Accounts
    store=Accounts(root).store_for(client.cookies.get('lastcopy_session'))
    (store.directory/'central-connection.json').write_text('{"ODK_PASSWORD":"private-test"}')
    assert client.get('/ui/runs',headers=H).status_code==200
    assert client.get('/ui/connection',headers=H).json()['state']=='unavailable'
    assert not client.get('/ui/settings',headers=H).json()['connected_ready']


def test_wrong_remote_scope_and_credential_throttle_never_save(cloud,monkeypatch):
    client,root,_=cloud
    root.settings.values['ODK_BASE_URL']='https://central.example.test'
    provider(monkeypatch);account_login(client,'a@example.test')
    original=httpx.Client
    def send(request):
        if request.url.path=='/v1/sessions':return httpx.Response(200,json={'token':'private-session'})
        return httpx.Response(200,json={'id':99,'name':'Wrong project'})
    monkeypatch.setattr('lastcopy.odk_recovery.httpx.Client',lambda **kw:original(transport=httpx.MockTransport(send),**kw))
    body={'project_id':7,'form_id':'water_points','email':'viewer@example.test','password':'private-test'}
    for _ in range(5):assert client.post('/ui/connection/setup',headers=H,json=body).status_code==409
    assert client.post('/ui/connection/setup',headers=H,json=body).status_code==429
    assert not list((root.directory/'accounts').glob('*/central-connection.json'))


def test_only_one_upstream_connection_test_can_run_across_accounts(cloud,monkeypatch):
    client,root,_=cloud
    root.settings.values['ODK_BASE_URL']='https://central.example.test'
    provider(monkeypatch);account_login(client,'a@example.test')
    from lastcopy.store import RunStore
    with RunStore(root.directory/'account-connection-admission',root.settings).lease() as held:
        assert held
        result=client.post('/ui/connection/setup',headers=H,json={'project_id':7,'form_id':'water_points','email':'viewer@example.test','password':'private-test'})
    assert result.status_code==409
    assert not list((root.directory/'accounts').glob('*/central-connection.json'))
