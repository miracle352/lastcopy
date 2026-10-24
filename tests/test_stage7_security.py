"""Browser-facing local boundaries must reject rebinding and cross-site writes."""
import pytest
from fastapi.testclient import TestClient
from lastcopy.api import app, get_store
from lastcopy.config import Settings
from lastcopy.store import RunStore


@pytest.fixture
def local(tmp_path):
    store = RunStore(tmp_path, Settings({'SAMPLE_MODE': 'true'}))
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app, base_url='http://127.0.0.1:8000') as client:
        yield client, store
    app.dependency_overrides.clear()


def test_rebinding_host_cannot_read_local_evidence(local):
    client, _ = local
    assert client.get('/health', headers={'host': 'rebound.example:8000'}).status_code == 400
    assert client.get('/health').status_code == 200


@pytest.mark.parametrize('origin', ['https://untrusted.example', 'null'])
def test_cross_site_simple_post_cannot_create_sample_jobs(local, origin):
    client, _ = local
    before = client.get('/ui/runs').json()
    response = client.post('/ui/samples/media', headers={'origin': origin})
    assert response.status_code == 403
    assert client.get('/ui/runs').json() == before


def test_documented_local_ui_still_works(local):
    client, _ = local
    assert client.post('/ui/samples/media', headers={'origin': 'http://127.0.0.1:3000'}).status_code == 201
