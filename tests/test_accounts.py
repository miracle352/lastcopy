"""Real HTTP + persistent isolation; only the remote identity boundary is replaced.

Removing account selection leaks owner runs. Trusting an email from the request
instead of GetUser permits impersonation. A provider outage must not sign in.
"""
import pytest
from tests.test_cloud_access import cloud,login

H={'authorization':'Bearer '+'t'*48}

def provider(monkeypatch,verified=True):
    try:from lastcopy.accounts import Cognito
    except ImportError:pytest.fail('Verified public accounts are not implemented')
    def call(self,action,body):
        if action=='InitiateAuth':
            if body['AuthParameters']['PASSWORD']!='Valid-password12':raise ValueError('Bad credentials')
            return {'AuthenticationResult':{'AccessToken':body['AuthParameters']['USERNAME']}}
        if action=='GetUser':return {'UserAttributes':[{'Name':'sub','Value':{'a@example.test':'11111111-1111-4111-8111-111111111111','b@example.test':'22222222-2222-4222-8222-222222222222'}[body['AccessToken']]},{'Name':'email_verified','Value':'true' if verified else 'false'}]}
        return {}
    monkeypatch.setattr(Cognito,'call',call)

def account_login(client,email):return client.post('/account/login',headers=H,json={'email':email,'password':'Valid-password12'})

def test_accounts_are_verified_isolated_and_survive_restart_without_owner_secrets(cloud,monkeypatch):
    client,store,password=cloud;provider(monkeypatch)
    assert login(client,password).status_code==200
    own=client.post('/ui/samples/media',headers=H).json()['run_id']
    assert account_login(client,'a@example.test').status_code==200
    assert client.get('/ui/runs',headers=H).json()==[]
    assert client.get('/ui/runs/'+own,headers=H).status_code==404
    a=client.post('/ui/samples/history',headers=H).json()['run_id']
    settings=client.get('/ui/settings',headers=H).json()
    assert settings['target'] is None and not settings['connected_ready']
    assert client.get('/ui/connection',headers=H).json()['state']=='not_configured'
    assert account_login(client,'b@example.test').status_code==200
    assert client.get('/ui/runs/'+a,headers=H).status_code==404
    from lastcopy.api import app,get_store
    from lastcopy.store import RunStore
    app.dependency_overrides[get_store]=lambda:RunStore(store.directory,store.settings)
    assert account_login(client,'a@example.test').status_code==200
    assert client.get('/ui/runs/'+a,headers=H).status_code==200
    assert client.post('/session/logout',headers=H).status_code==200
    assert client.get('/ui/runs',headers=H).status_code==401
    assert login(client,password).status_code==200
    assert client.get('/ui/runs/'+a,headers=H).status_code==404

def test_unverified_identity_and_provider_outage_never_create_a_session(cloud,monkeypatch):
    client,store,_=cloud;provider(monkeypatch,False)
    assert account_login(client,'a@example.test').status_code==403
    assert client.get('/ui/runs',headers=H).status_code==401
    from lastcopy.accounts import Cognito
    def down(*a,**k):raise ValueError('Private upstream body')
    monkeypatch.setattr(Cognito,'call',down)
    r=account_login(client,'a@example.test');assert r.status_code==503
    assert 'Private upstream body' not in r.text and not r.cookies

def test_public_auth_is_bounded_and_rejects_imported_fields(cloud,monkeypatch):
    client,_,_=cloud;provider(monkeypatch)
    assert client.post('/account/login',json={'email':'a@example.test','password':'Valid-password12'}).status_code==401
    assert client.post('/account/login',headers=H,json={'email':'a@example.test','password':'Valid-password12','sub':'owner'}).status_code==422
    for _ in range(10):client.post('/account/signup',headers=H,json={'email':'a@example.test','password':'Valid-password12'})
    assert client.post('/account/signup',headers=H,json={'email':'b@example.test','password':'Valid-password12'}).status_code==429

def test_beta_queue_is_bounded_across_accounts_and_capacity_returns_after_completion(cloud):
    from lastcopy.accounts import Accounts
    from lastcopy.ui import Workspace
    from lastcopy.models import RunRequest
    from lastcopy.inventory import ImportRejected
    _,root,_=cloud;accounts=Accounts(root);jobs=[]
    for i in range(5):
        token=accounts.create_session(f'{i:08x}-1111-4111-8111-111111111111',f'user{i}@example.test')
        store=accounts.store_for(token);draft=Workspace(store).sample('media');jobs.append((store,RunRequest.model_validate(draft['request'])))
    for store,request in jobs[:4]:store.enqueue(request)
    with pytest.raises(ImportRejected,match='beta job'):jobs[4][0].enqueue(jobs[4][1])
    jobs[0][0].drain()
    assert jobs[4][0].enqueue(jobs[4][1]).state=='queued'

def test_account_cannot_configure_owner_ai_or_read_device_scope(cloud,monkeypatch):
    client,_,_=cloud;provider(monkeypatch)
    assert account_login(client,'a@example.test').status_code==200
    assert client.get('/ui/cloud-ai',headers=H).status_code==403
    assert client.get('/device-transfer/status',headers=H).status_code==403
