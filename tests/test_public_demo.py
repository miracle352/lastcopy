"""Judges can inspect actual offline comparisons without owner credentials.

Mutation controls: using the owner store leaks a private run; forwarding an
arbitrary path makes a recovery write reachable; calling Central fails offline.
"""
import json
import pytest
from fastapi.testclient import TestClient
from tests.test_cloud_access import cloud
from lastcopy.api import app,get_store
from lastcopy.config import Settings
from lastcopy.store import RunStore


def demo_headers():return {'authorization':'Bearer '+'t'*48}


def test_public_demo_comparison_evidence_bundle_and_readback_are_real_and_offline(cloud,monkeypatch):
    client,store,_=cloud
    monkeypatch.setattr('lastcopy.odk_recovery.CentralRecovery.__init__',lambda *a,**k:pytest.fail('Public demo contacted Central'))
    response=client.get('/public/demo/media',headers=demo_headers())
    assert response.status_code==200
    view=response.json();assert view['manifest']['mode']=='sample'
    assert view['report']['findings'][0]['verdict']=='MISSING_ATTACHMENT'
    assert view['report']['provider_calls']==0
    rid=view['manifest']['run_id'];fid=view['report']['findings'][0]['finding_id']
    evidence=client.get(f'/public/demo/media/evidence/{fid}',headers=demo_headers())
    assert evidence.status_code==200 and evidence.json()['source_files'] and evidence.json()['receipts']
    first_file=evidence.json()['source_files'][0]
    from hashlib import sha256
    original=client.get('/public/demo/media/objects/'+first_file['object_id'],headers=demo_headers())
    assert original.status_code==200 and sha256(original.content).hexdigest()==first_file['sha256']
    plan=client.get('/public/demo/media/plan',headers=demo_headers())
    assert plan.status_code==200 and plan.json()['mode']=='sample' and plan.json()['source_hashes']
    bundle=client.get('/public/demo/media/bundle',headers=demo_headers())
    assert bundle.status_code==200 and bundle.content.startswith(b'PK')
    assert client.get('/public/demo/media/downloads/report.txt',headers=demo_headers()).status_code==200
    checked=client.post('/public/demo/media/readback',headers=demo_headers())
    assert checked.status_code==200
    assert checked.json()['current_report']['findings'][0]['verdict']=='PRESERVED'
    assert checked.json()['manifest']['mode']=='sample'
    assert 'no upload' in checked.json()['provenance'].lower()
    after_id=checked.json()['current_report']['findings'][0]['finding_id']
    assert client.get(f'/public/demo/media/readback/evidence/{after_id}',headers=demo_headers()).status_code==200
    after_report=client.get('/public/demo/media/readback/downloads/report.json',headers=demo_headers())
    assert after_report.status_code==200 and after_report.json()['run_id']==checked.json()['current_report']['run_id']
    assert client.post('/public/demo/media/readback',headers=demo_headers()).json()['manifest']['run_id']==checked.json()['manifest']['run_id']
    with store.connect() as c:assert c.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]==0


def test_public_demo_never_routes_owner_records_or_arbitrary_writes(cloud):
    client,_,password=cloud
    assert client.post('/session/login',json={'password':password},headers=demo_headers()).status_code==200
    private=client.post('/ui/samples/media',headers=demo_headers()).json()
    client.post('/session/logout',headers=demo_headers())
    assert client.get('/public/demo/'+private['run_id'],headers=demo_headers()).status_code in (401,404,422)
    assert client.get('/public/demo/media/evidence/not-a-finding',headers=demo_headers()).status_code==404
    assert client.get('/public/demo/media/objects/'+'0'*64,headers=demo_headers()).status_code==404
    for path in ('apply','review','devices','server','watch','connection'):
        assert client.post('/public/demo/media/'+path,headers=demo_headers()).status_code in (401,404,405)
    assert client.get('/public/demo/media').status_code==401
