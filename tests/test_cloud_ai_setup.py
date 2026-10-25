import json
from tests.test_cloud_access import cloud,login
from lastcopy.api import app,get_store
from lastcopy.config import Settings
from lastcopy.store import RunStore
from lastcopy.investigation import InvestigationError

H={'authorization':'Bearer '+'t'*48}

def test_owner_cloud_key_is_server_only_and_failed_replacement_preserves_it(cloud,monkeypatch):
    client,root,password=cloud
    settings=Settings(dict(root.settings.values,SAMPLE_MODE='false',LASTCOPY_DATA_DIR=str(root.directory)))
    app.dependency_overrides[get_store]=lambda:RunStore(root.directory,settings)
    from lastcopy.nvidia_cloud import NvidiaCloud
    monkeypatch.setattr(NvidiaCloud,'models',lambda self:['nvidia/catalog-model'])
    assert client.post('/ui/cloud-ai/connect',headers=H,json={'api_key':'private-key-1234567890123'}).status_code==401
    assert login(client,password).status_code==200
    result=client.post('/ui/cloud-ai/connect',headers=H,json={'api_key':'private-key-1234567890123'})
    assert result.status_code==200 and result.json()['models']==['nvidia/catalog-model']
    assert result.json()['inference_verified'] is False
    status=client.get('/ui/cloud-ai',headers=H)
    assert status.status_code==200 and status.json()['configured']
    assert 'private-key-1234567890123' not in result.text+status.text
    before=(root.directory/'cloud-ai.json').read_bytes()
    def down(*a):raise InvestigationError('suppressed provider error')
    monkeypatch.setattr(NvidiaCloud,'models',down)
    bad=client.post('/ui/cloud-ai/connect',headers=H,json={'api_key':'new-private-key-123456789'})
    assert bad.status_code==503
    assert (root.directory/'cloud-ai.json').read_bytes()==before
    assert 'new-private-key' not in bad.text and 'suppressed provider error' not in bad.text

def test_inventory_budget_survives_service_reconstruction(cloud,monkeypatch):
    client,root,password=cloud
    settings=Settings(dict(root.settings.values,SAMPLE_MODE='false',LASTCOPY_DATA_DIR=str(root.directory)))
    app.dependency_overrides[get_store]=lambda:RunStore(root.directory,settings)
    from lastcopy.nvidia_cloud import NvidiaCloud
    monkeypatch.setattr(NvidiaCloud,'models',lambda self:['nvidia/catalog-model'])
    assert login(client,password).status_code==200
    for _ in range(30):assert client.post('/ui/cloud-ai/connect',headers=H,json={'api_key':'private-key-1234567890123'}).status_code==200
    assert client.post('/ui/cloud-ai/connect',headers=H,json={'api_key':'private-key-1234567890123'}).status_code==429

def test_exhausted_inference_allowance_is_visible_before_clicking_test(cloud):
    import time
    client,root,password=cloud
    settings=Settings(dict(root.settings.values,SAMPLE_MODE='false',LASTCOPY_DATA_DIR=str(root.directory)))
    app.dependency_overrides[get_store]=lambda:RunStore(root.directory,settings)
    with root.connect() as c:
        c.execute('CREATE TABLE cloud_ai_budget(at REAL NOT NULL)')
        c.executemany('INSERT INTO cloud_ai_budget VALUES(?)',[(time.time(),)]*10)
    assert login(client,password).status_code==200
    value=client.get('/ui/cloud-ai',headers=H).json()
    assert value['test_remaining']==0 and value['test_resets_at']
