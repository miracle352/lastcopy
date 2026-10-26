import json
from datetime import datetime,timezone,timedelta
from types import SimpleNamespace
from lastcopy.operations import status
from scripts.backup_health import record


def test_backup_health_retains_last_success_and_flags_failure_staleness_and_disk(tmp_path,monkeypatch):
    store=SimpleNamespace(directory=tmp_path)
    path=tmp_path/'operations'/'backup.json'
    assert status(store)['attention']
    receipt=tmp_path/'receipt.json'
    now=datetime.now(timezone.utc).isoformat()
    receipt.write_text(json.dumps({'created_at':now,'central_database':True,'application_databases':3}))
    record(path,'success',receipt)
    value=status(store)
    assert value['last_success']==now and not value['attention']
    assert not value['off_host_automatic'] and not value['full_machine_restore_verified']
    record(path,'failed')
    assert status(store)['last_success']==now
    assert any('failed' in text for text in status(store)['attention'])
    path.write_text(json.dumps({'state':'success','last_success':(datetime.now(timezone.utc)-timedelta(hours=37)).isoformat(),'password':'never-return-this'}))
    monkeypatch.setattr('lastcopy.operations.shutil.disk_usage',lambda _:SimpleNamespace(free=1024))
    value=status(store)
    assert value['last_success'] is None and len(value['attention'])==2
    assert 'never-return-this' not in json.dumps(value)


def test_operations_are_owner_only(cloud,monkeypatch):
    from tests.test_accounts import provider,account_login,H
    from tests.test_cloud_access import login
    client,_,password=cloud
    assert client.get('/ui/operations',headers=H).status_code==401
    provider(monkeypatch);account_login(client,'a@example.test')
    assert client.get('/ui/operations',headers=H).status_code==403
    login(client,password)
    assert client.get('/ui/operations',headers=H).status_code==409  # fixture is Sample; no cloud claim


from tests.test_cloud_access import cloud
