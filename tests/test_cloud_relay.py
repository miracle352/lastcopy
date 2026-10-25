"""A lost delivery acknowledgement must retry the same immutable bytes.

The external wire is simulated; receiver, authentication, SQLite and files are
real. Removing acknowledgement validation/deduplication must fail these tests.
"""
import hashlib,json
import httpx
import pytest
from tests.test_cloud_access import cloud
from lastcopy.api import app,get_store
from lastcopy.config import Settings
from lastcopy.store import RunStore
from scripts.build_stage2_fixtures import example


def sender(tmp_path):
    inbox=tmp_path/'sender';inbox.mkdir()
    data=example('stranded')['device'];sha=hashlib.sha256(data).hexdigest()
    (inbox/'capture.zip').write_bytes(data)
    (inbox/'capture.zip.ready.json').write_text(json.dumps({'schema_version':1,'sha256':sha,'bytes':len(data)}))
    settings=Settings({'SAMPLE_MODE':'false','LASTCOPY_WATCH_INBOX':str(inbox),'LASTCOPY_CLOUD_ORIGIN':'https://cloud.example','LASTCOPY_TRANSFER_KEY':'d'*48})
    return RunStore(tmp_path/'sender-ledger',settings),data


def test_lost_ack_retries_same_bytes_and_receiver_deduplicates(cloud,tmp_path):
    from lastcopy.cloud_relay import Relay
    receiver,store,_=cloud
    inbox=tmp_path/'receiver';inbox.mkdir()
    values=dict(store.settings.values,SAMPLE_MODE='false',LASTCOPY_TRANSFER_KEY='d'*48,LASTCOPY_WATCH_INBOX=str(inbox),
        LASTCOPY_WATCH_DEVICE_IDS='["device-41"]',ODK_BASE_URL='https://central.example',ODK_READ_PROJECT_ID='1',
        ODK_READ_FORM_ID='inspection',ODK_READ_PROJECT_NAME='Test collection')
    app.dependency_overrides[get_store]=lambda:RunStore(store.directory,Settings(values))
    source,data=sender(tmp_path);calls=[]
    def wire(request):
        assert str(request.url)=='https://cloud.example/device-transfer'
        assert request.headers['authorization']=='Bearer '+'d'*48
        assert request.content==data
        calls.append(request.content)
        response=receiver.post('/device-transfer',content=request.content,headers=dict(request.headers,host='localhost'))
        assert response.status_code==201
        if len(calls)==1:raise httpx.ReadTimeout('Acknowledgement lost after receiver accepted bytes')
        return httpx.Response(response.status_code,json=response.json())
    with httpx.Client(transport=httpx.MockTransport(wire)) as client:
        relay=Relay(source,client=client)
        with pytest.raises(httpx.ReadTimeout):relay.flush()
        assert relay.flush()==1
        assert Relay(source,client=client).flush()==0
    assert len(calls)==2 and len(list(inbox.glob('*.zip')))==1
    assert list(inbox.glob('*.zip'))[0].read_bytes()==data
    assert (tmp_path/'sender/capture.zip').read_bytes()==data


def test_wrong_delivery_receipt_never_marks_source_sent(tmp_path):
    from lastcopy.cloud_relay import Relay
    store,data=sender(tmp_path)
    with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(201,json={'sha256':'0'*64,'input_id':'1'*64,'bytes':len(data),'preservation_proof':False}))) as client:
        with pytest.raises(ValueError):Relay(store,client=client).flush()
    with store.connect() as c:assert c.execute('SELECT COUNT(*) FROM relay_sent').fetchone()[0]==0


def test_sample_mode_refuses_relay_before_network(tmp_path):
    from lastcopy.cloud_relay import Relay
    store,_=sender(tmp_path)
    isolated=RunStore(store.directory,Settings(dict(store.settings.values,SAMPLE_MODE='true')))
    with pytest.raises(ValueError):Relay(isolated)


def test_cloud_pause_prevents_native_capture(tmp_path):
    from lastcopy.cloud_relay import Relay
    from lastcopy.device_transfer import DeviceTransfer
    from scripts.cloud_device_link import cycle
    from tests.test_device_transfer import setup
    _,inbox,store=setup(tmp_path)
    store.settings=Settings(dict(store.settings.values,LASTCOPY_CLOUD_ORIGIN='https://cloud.example',LASTCOPY_TRANSFER_KEY='d'*48))
    transfer=DeviceTransfer(store,pull=lambda:pytest.fail('Paused link read the device'))
    def control(request):
        assert request.method=='GET' and request.url.path=='/device-transfer/status'
        return httpx.Response(200,json={'enabled':False,'interval_seconds':30,'source_device_ids':['device-one']})
    with httpx.Client(transport=httpx.MockTransport(control)) as client:
        assert cycle(transfer,Relay(store,client=client))['state']=='paused'
    assert not list(inbox.glob('*.zip'))
