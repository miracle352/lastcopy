import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import run

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('name', ['example_1.json', 'example_2.json', 'example_3.json', 'example_4.json'])
def test_every_input_example_runs_offline_and_matches_hand_written_expectations(name, monkeypatch, tmp_path):
    monkeypatch.setenv('SAMPLE_MODE', 'true')
    spec = json.loads((ROOT / 'input_examples' / name).read_text())
    doc = run.investigate(ROOT / 'input_examples' / name, quiet=True)
    expected = json.loads((ROOT / spec['expected']).read_text())
    assert {f['version_id']: f['verdict'] for f in doc['findings']} == expected['verdicts']
    if 'decisions' in expected:
        assert {d['device_id']: d['decision'] for d in doc['decisions']} == expected['decisions']
    assert doc['engines']['evidence'] == ['local-sql'] and doc['engines']['models'] == ['offline-policy']
    lines = [json.loads(l) for l in (ROOT / doc['log_file']).read_text().splitlines()]
    assert {'agent_name', 'action', 'target_agent', 'model', 'retry_count', 'status'} <= set(lines[1])
    assert any(l.get('agent_name') == 'World Model planner' for l in lines)


def test_example_paths_must_stay_inside_fixtures(tmp_path):
    bad = tmp_path / 'bad.json'
    bad.write_text(json.dumps({'question': 'x', 'manifest': '../etc/passwd', 'devices': [], 'server_manifest': 'x', 'server_payload': 'x'}))
    with pytest.raises(SystemExit):
        run.load_example(bad)


def test_investigate_endpoint_is_json_in_json_out_and_named_examples_only(monkeypatch):
    monkeypatch.setenv('SAMPLE_MODE', 'true')
    from lastcopy.api import app
    client = TestClient(app, base_url='http://127.0.0.1:8000')
    response = client.post('/investigate', json={'example': 'photo'})
    assert response.status_code == 200 and response.json()['decisions'][0]['decision'] == 'RECOVER_FIRST'
    assert client.post('/investigate', json={'example': '../../etc/passwd'}).status_code == 422
    assert client.post('/investigate', json={'example': 'fleet', 'path': '/etc'}).status_code == 422
