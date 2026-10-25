"""Direct NVIDIA is explicit, never renamed Nightshift and never a sample fallback."""
import json
import httpx
import pytest
from lastcopy.config import Settings
from lastcopy.investigation import InvestigationError

def adapter(monkeypatch,reply):
    try:from lastcopy.nvidia_cloud import NvidiaCloud
    except ImportError:pytest.fail('Explicit direct NVIDIA adapter not implemented')
    requests=[]
    def handler(request):
        requests.append(request)
        if request.url.path.endswith('/models'):return httpx.Response(200,json={'data':[{'id':'nvidia/actual-nemotron-test'}]})
        return httpx.Response(200,json=reply)
    p=NvidiaCloud(Settings({'SAMPLE_MODE':'false','NVIDIA_API_KEY':'private-test-key','NVIDIA_MODEL_ID':'nvidia/actual-nemotron-test'}))
    p.client.close();p.client=httpx.Client(transport=httpx.MockTransport(handler))
    return p,requests

def test_direct_cloud_action_requires_actual_inventory_and_validated_json(monkeypatch):
    reply={'model':'nvidia/actual-nemotron-test','choices':[{'message':{'content':'{"action":"fetch_raw_xml"}'}}],'usage':{'total_tokens':24},'secret':'must-not-log'}
    p,requests=adapter(monkeypatch,reply)
    try:
        action,receipt=p.choose('investigator',{'evidence':'untrusted input'},['fetch_raw_xml'],None)
        assert action=={'action':'fetch_raw_xml'}
        assert receipt['provider']=='nvidia_direct' and receipt['nightshift_used'] is False
        assert receipt['actual_serving_model']=='nvidia/actual-nemotron-test'
        assert receipt['usage']=={'total_tokens':24}
        assert 'private-test-key' not in json.dumps(receipt) and 'must-not-log' not in json.dumps(receipt)
        assert [r.url.path for r in requests]==['/v1/models','/v1/chat/completions']
    finally:p.close()

@pytest.mark.parametrize('content',['{"action":"upload"}','{"action":"fetch_raw_xml","facts":"invented"}','not-json'])
def test_cloud_cannot_add_facts_or_execute_unlisted_actions(monkeypatch,content):
    p,_=adapter(monkeypatch,{'model':'nvidia/actual-nemotron-test','choices':[{'message':{'content':content}}]})
    try:
        with pytest.raises(InvestigationError):p.choose('reviewer',{},['fetch_raw_xml'],None)
    finally:p.close()

def test_cloud_sample_guard_and_outage_have_no_provider_fallback(monkeypatch):
    p,_=adapter(monkeypatch,{'error':'provider failed'})
    try:
        with pytest.raises(InvestigationError):p.choose('reviewer',{},['manual_review'],None)
    finally:p.close()
    from lastcopy.nvidia_cloud import NvidiaCloud
    with pytest.raises(InvestigationError):NvidiaCloud(Settings({'SAMPLE_MODE':'true','NVIDIA_API_KEY':'private-test-key'}))

def test_nemotron_reasoning_is_explicitly_disabled_for_bounded_action_json(monkeypatch):
    p,requests=adapter(monkeypatch,{'model':'nvidia/nemotron-3-test','choices':[{'message':{'content':'{"action":"manual_review"}'}}]})
    p.values['NVIDIA_MODEL_ID']='nvidia/nemotron-3-test';p.inventory=['nvidia/nemotron-3-test']
    try:
        p.choose('reviewer',{},['manual_review'],None)
        body=json.loads(requests[-1].content)
        assert body['chat_template_kwargs']['enable_thinking'] is False
    finally:p.close()

def test_documented_bolt_route_is_distinct_from_inventory_and_serving_identity(monkeypatch):
    canonical='nvidia/nemotron-3.5-bolt-e4b'
    p,requests=adapter(monkeypatch,{'model':canonical,'choices':[{'message':{'content':'{"action":"manual_review"}'}}]})
    p.values['NVIDIA_MODEL_ID']=canonical;p.inventory=[canonical]
    try:
        _,receipt=p.choose('reviewer',{},['manual_review'],None)
        body=json.loads(requests[-1].content)
        assert body['model']=='stg/'+canonical
        assert body['response_format']['type']=='json_schema'
        assert body['response_format']['json_schema']['schema']['additionalProperties'] is False
        assert receipt['routing_id']=='stg/'+canonical
        assert receipt['catalog_model']==receipt['actual_serving_model']==canonical
    finally:p.close()
