import io,json,zipfile
from tests.test_cloud_access import cloud,login
from tests.test_accounts import provider,account_login,H
from lastcopy.inventory import digest
from scripts.privacy_requests import pending


def test_private_export_and_erasure_request_are_account_scoped_and_idempotent(cloud,monkeypatch):
    client,root,password=cloud;provider(monkeypatch)
    assert client.get('/ui/account',headers=H).status_code==401
    login(client,password)
    assert client.get('/ui/account',headers=H).status_code==403
    account_login(client,'a@example.test')
    draft=client.post('/ui/samples/history',headers=H).json();rid=draft['run_id']
    before=client.get('/ui/runs/'+rid,headers=H).json()
    assert client.post('/ui/account/request',headers=H,json={'confirm_reviewed_request':False}).status_code==422
    request=client.post('/ui/account/request',headers=H,json={'confirm_reviewed_request':True}).json()
    assert request['request_state']=='awaiting_operator_review' and not request['automatic_deletion']
    assert client.post('/ui/account/request',headers=H,json={'confirm_reviewed_request':True}).json()==request
    result=client.get('/ui/account/export',headers=H);assert result.status_code==200
    assert result.headers['cache-control']=='no-store'
    assert digest(result.content)==result.headers['x-content-sha256']
    with zipfile.ZipFile(io.BytesIO(result.content)) as bundle:
        manifest=json.loads(bundle.read('manifest.json'))
        assert manifest['files'] and all(digest(bundle.read(path))==sha for path,sha in manifest['files'].items())
        assert all(path.startswith(('originals/','reports/')) for path in manifest['files'])
    assert client.get('/ui/runs/'+rid,headers=H).json()==before
    account_login(client,'b@example.test')
    assert client.get('/ui/account',headers=H).json()['request_state']=='not_requested'
    with zipfile.ZipFile(io.BytesIO(client.get('/ui/account/export',headers=H).content)) as bundle:
        assert json.loads(bundle.read('manifest.json'))['files']=={}
    account_login(client,'a@example.test')
    assert client.get('/ui/account',headers=H).json()==request
    queue=pending(root.directory)
    assert len(queue)==1 and queue[0]['state']=='awaiting_operator_review'
