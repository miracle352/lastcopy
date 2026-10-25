"""Real-user entry and automatic examples must retain evidence/connection semantics."""
import json
import pytest
from fastapi.testclient import TestClient
from lastcopy.config import Settings
from lastcopy.store import RunStore


def client_for(tmp_path,settings):
    from lastcopy.api import app,get_store
    store=RunStore(tmp_path,Settings(settings));app.dependency_overrides[get_store]=lambda:store
    return TestClient(app,base_url='http://127.0.0.1:8000'),store


@pytest.mark.parametrize('mode',['true','false'])
def test_automatic_example_reuses_actual_comparison_and_has_no_provider_calls(tmp_path,monkeypatch,mode):
    client,store=client_for(tmp_path,{'SAMPLE_MODE':mode})
    monkeypatch.setattr('lastcopy.odk_recovery.CentralRecovery.__init__',lambda *a,**k:(_ for _ in ()).throw(AssertionError('Example contacted Central')))
    try:
        with client:
            first=client.post('/ui/examples/media',json={});assert first.status_code==200
            second=client.post('/ui/examples/media',json={});assert second.status_code==200
            assert first.json()['run_id']==second.json()['run_id']
            view=client.get('/ui/runs/'+first.json()['run_id']).json()
            assert view['report']['findings'][0]['verdict']=='MISSING_ATTACHMENT'
            assert view['report']['provider_calls']==0 and view['investigation'] is None
            with store.connect() as c:assert c.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]==1
    finally:
        from lastcopy.api import app
        app.dependency_overrides.clear()


def test_previous_reports_have_human_metadata_and_true_counts(tmp_path):
    client,_=client_for(tmp_path,{'SAMPLE_MODE':'true'})
    try:
        with client:
            d=client.post('/ui/samples/stranded').json();client.post('/ui/runs/'+d['run_id']+'/start',json={})
            report=client.get('/ui/runs/'+d['run_id']).json()['report']
            recent=client.get('/ui/runs').json()[0]
            assert recent['title'] and d['run_id'] not in recent['title']
            assert recent['record_count']==len(report['findings'])==3
            assert recent['attention_count']==sum(f['preservation']!='preserved' for f in report['findings'])==2
            assert recent['checked_at'] and recent['sample_case']=='stranded'
    finally:
        from lastcopy.api import app
        app.dependency_overrides.clear()


def test_connection_verifies_project_and_form_without_record_writes(tmp_path,monkeypatch):
    calls=[]
    class Remote:
        base='http://localhost:8384'
        target={'project_id':2,'form_id':'inspection'}
        def __init__(self,*a):pass
        def begin(self):pass
        def login(self):calls.append('authenticate')
        def scope(self):return '/v1/projects/2/forms/inspection'
        def request(self,method,path):
            calls.append((method,path))
            return 200,json.dumps({'name':'LastCopy synthetic Stage 4 recovery'} if path=='/v1/projects/2' else {'name':'Inspection','xmlFormId':'inspection'}).encode()
        def close(self):pass
        @property
        def client(self):return self
    monkeypatch.setattr('lastcopy.odk_recovery.CentralRecovery',Remote)
    client,_=client_for(tmp_path,{'SAMPLE_MODE':'false','ODK_RECOVERY_PROJECT_NAME':'LastCopy synthetic Stage 4 recovery'})
    try:
        with client:
            response=client.get('/ui/connection');assert response.status_code==200
            body=response.json();assert body['state']=='connected' and body['record_writes']==0
            assert body['project_name']=='LastCopy synthetic Stage 4 recovery'
            assert len(body['receipts'])==2 and all(r['method']=='GET' and len(r['sha256'])==64 for r in body['receipts'])
            assert all(c=='authenticate' or c[0]=='GET' for c in calls)
    finally:
        from lastcopy.api import app
        app.dependency_overrides.clear()


def test_sample_connection_cannot_contact_a_server(tmp_path,monkeypatch):
    monkeypatch.setattr('lastcopy.odk_recovery.CentralRecovery.__init__',lambda *a,**k:pytest.fail('Sample opened an external connection'))
    client,_=client_for(tmp_path,{'SAMPLE_MODE':'true'})
    try:
        with client:
            body=client.get('/ui/connection').json()
            assert body['state']=='not_configured' and body['record_writes']==0 and body['receipts']==[]
    finally:
        from lastcopy.api import app
        app.dependency_overrides.clear()


def test_connection_failure_never_becomes_missing_records(tmp_path,monkeypatch):
    def rejected(*a,**k):raise ValueError('Central authentication failed HTTP 403')
    monkeypatch.setattr('lastcopy.odk_recovery.CentralRecovery.__init__',rejected)
    client,_=client_for(tmp_path,{'SAMPLE_MODE':'false'})
    try:
        with client:
            body=client.get('/ui/connection').json()
            assert body['state']=='unavailable' and body['record_writes']==0
            assert body['receipts']==[] and body['project_name'] is None
            assert 'missing' not in body['message'].lower()
    finally:
        from lastcopy.api import app
        app.dependency_overrides.clear()
