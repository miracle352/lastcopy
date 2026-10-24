import json
import socket
import pytest
from lastcopy.config import Settings
from scripts.build_stage2_fixtures import example
from lastcopy.investigation import EvidencePack, Investigation, WorldJournal, validate_action, InvestigationError
from lastcopy.connected import ZetarisEvidence
from lastcopy.connected import Nightshift
from lastcopy.inventory import digest
import sqlite3
import csv
import io
import time
import threading
import httpx
from pathlib import Path
from scripts.investigate import supervise


class SQLiteEvidenceDouble:
    """Unit-only transport: execute the production SQL, never claim live Zetaris."""
    def publish(self, pack):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        for name, rows in pack.tables.items():
            columns = pack.columns(name)
            self.db.execute('CREATE TABLE ' + name + '(' + ','.join('"' + c + '" TEXT' for c in columns) + ')')
            self.db.executemany('INSERT INTO ' + name + ' VALUES(' + ','.join('?' for _ in columns) + ')', [[r[c] for c in columns] for r in rows])

    def query(self, kind, pack, owner):
        adapter = object.__new__(ZetarisEvidence)
        adapter.database = 'lc3_' + 'a' * 20
        sql = adapter.sql(kind, pack).replace(adapter.database + '.', '')
        rows = [dict(row) for row in self.db.execute(sql)]
        return rows, {'query_id': 'unit-sqlite-' + kind, 'sql': sql, 'provider': 'unit_sqlite_double', 'elapsed_ms': 1}


class ModelDouble:
    nemotron_verified = False
    def __init__(self, final='export_guidance', fail=False, initial_review='request_raw'):
        self.actions = iter(['investigate_gap', initial_review, final])
        self.fail = fail

    def action(self, role, prompt, allowed, owner):
        if self.fail:
            raise InvestigationError('Nightshift unavailable')
        return {'action': next(self.actions)}, {'provider': 'unit_model_double', 'actual_serving_model': None, 'elapsed_ms': 1}


def build(case='export', seed=41):
    fixture = example(case, seed=seed, repeats=5 if seed != 41 else 2)
    return EvidencePack.build(fixture['run'], [fixture['device']], json.dumps(fixture['snapshot']).encode(), fixture['server'], Settings({}))


@pytest.mark.parametrize('case,action,verdict,status', [('export', 'export_guidance', 'EXPORT_VIEW_ONLY', 'rejected'), ('conflict', 'manual_review', 'CONTENT_CONFLICT', 'unresolved_conflict')])
def test_critic_changes_actual_branch_and_verdict_remains_code_owned(tmp_path, case, action, verdict, status):
    result = Investigation(tmp_path, Settings({'SAMPLE_MODE': 'false'})).connected(build(case), SQLiteEvidenceDouble(), ModelDouble(action))
    assert result['status'] == 'completed', result.get('error')
    assert result['next_action'] == action
    assert result['report']['findings'][0]['verdict'] == verdict
    assert result['report']['provider_calls'] == 0  # Comparator itself has no providers.
    assert result['critique_rounds'] == 2 and result['steps'] <= 12
    assert result['graph']['hypotheses'][-1]['attrs']['status'] == status
    assert result['graph']['hypotheses'][0]['attrs']['evidence']
    assert any(e['kind'] == 'decision_changed' for e in result['events'])
    assert not result['report']['findings'][0]['recovery_eligible']
    seals = json.loads((tmp_path / 'seals.json').read_bytes())
    assert all(digest((tmp_path / name).read_bytes()) == sha for name, sha in seals.items())
    assert digest((tmp_path / 'report.json').read_bytes()) == result['report_sha256']
    assert all(path.stem == digest(path.read_bytes()) for path in (tmp_path / 'queries').glob('*.json'))


def test_model_failure_after_real_query_dispatch_never_supplies_report(tmp_path):
    result = Investigation(tmp_path, Settings({'SAMPLE_MODE': 'false'})).connected(build(), SQLiteEvidenceDouble(), ModelDouble(fail=True))
    assert result['status'] == 'failed' and 'report' not in result
    assert result['provider_calls'] == 1
    assert any(e['kind'] == 'query' for e in result['events'])


@pytest.mark.parametrize('change,error', [({'max_steps': 1}, 'step budget'), ({'max_critique_rounds': 0}, 'Critique budget')])
def test_visible_budgets_fail_closed(tmp_path, change, error):
    pack = build()
    pack.run = pack.run.model_copy(update=change)
    result = Investigation(tmp_path, Settings({'SAMPLE_MODE': 'false'})).connected(pack, SQLiteEvidenceDouble(), ModelDouble())
    assert result['status'] == 'failed' and error in result['error']


def test_cancel_does_not_publish(tmp_path):
    class Forbidden:
        def publish(self, pack):
            pytest.fail('cancelled run published evidence')
    result = Investigation(tmp_path, Settings({'SAMPLE_MODE': 'false'}), cancel=lambda: True).connected(build(), Forbidden(), None)
    assert result['status'] == 'cancelled' and result['provider_calls'] == 0


def test_critic_can_keep_insufficient_evidence_unresolved(tmp_path):
    result = Investigation(tmp_path, Settings({'SAMPLE_MODE': 'false'})).connected(build(seed=9087), SQLiteEvidenceDouble(), ModelDouble(initial_review='keep_unresolved'))
    assert result['status'] == 'incomplete' and 'report' not in result
    assert not any(e.get('tool') == 'compare_payloads' for e in result['events'])


def test_actions_cannot_smuggle_paths_or_verdicts():
    for value in [{'action': 'fetch_raw', 'path': '../../secret'}, {'action': 'PRESERVED'}, {'action': 'fetch_raw', 'verdict': 'PRESERVED'}]:
        with pytest.raises(InvestigationError):
            validate_action(value, ['fetch_raw'])


def test_graph_rebuild_idempotency_revision_and_next_action(tmp_path):
    world = WorldJournal(tmp_path / 'world.jsonl')
    first = dict(type='hypothesis', key='record-a', revision=0, status='possible_missing_data', next_action='review', evidence=['export-row-1'])
    world.add(**first)
    before = world.read()
    world.add(**first)
    assert world.read() == before
    world.add(type='hypothesis', key='record-a', revision=1, status='rejected', next_action='export_guidance', evidence=['raw-row-2', 'export-row-1'])
    after = WorldJournal(tmp_path / 'world.jsonl').read()
    assert before['next_action'] == 'review' and after['next_action'] == 'export_guidance'
    assert len(after['hypotheses']) == 2
    assert after['hypotheses'][0]['attrs']['evidence'] == ['export-row-1']
    assert after['hypotheses'][1]['attrs']['status'] == 'rejected'
    with pytest.raises(InvestigationError):
        world.add(**{**first, 'status': 'changed'})


def test_sample_is_offline_and_verifier_is_authority(tmp_path, monkeypatch):
    monkeypatch.setattr(socket, 'socket', lambda *a, **k: pytest.fail('sample opened network'))
    fixture = example('export', seed=9087, repeats=5)
    pack = EvidencePack.build(fixture['run'], [fixture['device']], json.dumps(fixture['snapshot']).encode(), fixture['server'], Settings({}))
    result = Investigation(tmp_path, Settings({})).sample(pack)
    assert result['mode'] == 'sample' and result['provider_calls'] == 0
    assert result['report']['findings'][0]['verdict'] == 'EXPORT_VIEW_ONLY'
    assert not any(e['kind'] in ('model', 'query') for e in result['events'])


def test_connected_provider_failure_has_no_sample_fallback(tmp_path):
    fixture = example('export')
    pack = EvidencePack.build(fixture['run'], [fixture['device']], json.dumps(fixture['snapshot']).encode(), fixture['server'], Settings({}))
    class Unavailable:
        def publish(self, pack):
            raise InvestigationError('Zetaris unavailable')
    result = Investigation(tmp_path, Settings({'SAMPLE_MODE': 'false'})).connected(pack, Unavailable(), None)
    assert result['status'] == 'failed' and result.get('report') is None
    assert result['mode'] == 'connected' and 'Zetaris unavailable' in result['error']


def test_pack_scope_bounds_and_immutable_source_hashes():
    fixture = example('export')
    pack = EvidencePack.build(fixture['run'], [fixture['device']], json.dumps(fixture['snapshot']).encode(), fixture['server'], Settings({}))
    assert pack.tables['xml_facts'] and pack.tables['media_references']
    assert all(row['run_id'] == pack.run.run_id for rows in pack.tables.values() for row in rows)
    assert all(len(data) <= 1048576 for data in pack.csv_files().values())
    fixture['snapshot']['synthetic'] = False
    with pytest.raises(InvestigationError, match='synthetic'):
        EvidencePack.build(fixture['run'], [fixture['device']], json.dumps(fixture['snapshot']).encode(), fixture['server'], Settings({}))


def test_csv_json_survives_actual_spark_dialect():
    pack = build()
    for name, data in pack.csv_files().items():
        rows = list(csv.DictReader(io.StringIO(data.decode()), doublequote=False, escapechar='\\'))
        assert rows == pack.tables[name]
    facts = pack.tables['xml_facts']
    assert any(json.loads(r['fact_json']).get('text') == '0017' for r in facts)


def stalled_worker(directory, cancel=False):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if cancel:
        (directory / 'cancel').touch()
    time.sleep(20)


@pytest.mark.parametrize('cancel,status', [(False, 'failed'), (True, 'cancelled')])
def test_supervisor_stops_blocked_worker(tmp_path, cancel, status):
    output = tmp_path / 'attempt'
    run = build().run.model_copy(update={'max_seconds': 5 if cancel else 2})
    def signal_cancel():
        output.mkdir(parents=True, exist_ok=True)
        (output / 'cancel').touch()
    timer = threading.Timer(.3, signal_cancel) if cancel else None
    if timer:
        timer.start()
    try:
        result = supervise(stalled_worker, (output, False), output, run)
    finally:
        if timer:
            timer.join()
    assert result['status'] == status
    assert 'report' not in result
    assert (output / 'seals.json').exists()
    with pytest.raises(InvestigationError):
        supervise(stalled_worker, (output, cancel), output, run)


def test_query_object_tampering_and_omission_fail_closed(tmp_path):
    class Tampered(SQLiteEvidenceDouble):
        def query(self, kind, pack, owner):
            rows, receipt = super().query(kind, pack, owner)
            if kind == 'objects':
                rows[0]['sha256'] = '0' * 64
            return rows, receipt
    result = Investigation(tmp_path, Settings({'SAMPLE_MODE': 'false'})).connected(build(), Tampered(), ModelDouble())
    assert result['status'] == 'failed' and 'report' not in result


def test_explicit_replay_is_offline_and_cannot_be_called_sample(tmp_path, monkeypatch):
    pack = build()
    pack.run = pack.run.model_copy(update={'mode': 'replay'})
    monkeypatch.setattr(socket, 'socket', lambda *a, **k: pytest.fail('replay opened network'))
    with pytest.raises(InvestigationError):
        Investigation(tmp_path / 'sample', Settings({})).sample(pack)
    result = Investigation(tmp_path / 'replay', Settings({'SAMPLE_MODE': 'false'})).replay(pack)
    assert result['mode'] == 'replay' and result['report']['mode'] == 'replay'
    assert result['provider_calls'] == 0


def test_model_cannot_turn_conflict_into_export_guidance(tmp_path):
    result = Investigation(tmp_path, Settings({'SAMPLE_MODE': 'false'})).connected(build('conflict'), SQLiteEvidenceDouble(), ModelDouble('export_guidance'))
    assert result['status'] == 'failed' and 'report' not in result
    assert not (tmp_path / 'report.json').exists()
    assert 'Invalid' in result['error']


def test_optional_tables_can_be_empty_without_inventing_evidence():
    pack = build()
    pack.tables['media_references'] = []
    pack.tables['attempt_logs'] = []
    csvs = pack.csv_files()
    for name in ('media_references', 'attempt_logs'):
        reader = csv.DictReader(io.StringIO(csvs[name].decode()), doublequote=False, escapechar='\\')
        assert reader.fieldnames == pack.columns(name)
        assert list(reader) == []


def test_failed_authenticated_query_keeps_query_id_and_hides_body(tmp_path):
    worker = Investigation(tmp_path, Settings({'SAMPLE_MODE': 'false'}))
    pack = build()
    worker.begin(pack, 'connected')
    adapter = object.__new__(ZetarisEvidence)
    adapter.database = 'lc3_' + 'a' * 20
    adapter.owner = worker
    adapter.headers = {'Authorization': 'test-only'}
    adapter.client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(403, text='private-body-for-test')))
    try:
        with pytest.raises(InvestigationError, match='HTTP 403'):
            adapter.query('versions', pack, worker)
    finally:
        adapter.close()
    assert worker.events[-1]['kind'] == 'query_failure'
    assert worker.events[-1]['query_id'].startswith('query-')
    assert 'private-body-for-test' not in json.dumps(worker.events)


def test_nvidia_bounded_action_disables_thinking_and_records_reported_identity(tmp_path):
    route='nvidia/unit-test-nemotron'
    settings=Settings({'SAMPLE_MODE':'false','NIGHTSHIFT_BASE_URL':'http://127.0.0.1:8088/v1',
                       'NIGHTSHIFT_TOKEN':'unit-only','NIGHTSHIFT_ROUTE':route})
    worker=Investigation(tmp_path,settings);worker.begin(build(),'connected')
    def handle(request):
        if request.method=='GET':
            return httpx.Response(200,json={'data':[{'id':route}]})
        body=json.loads(request.content)
        assert body['reasoning_effort']=='none'
        assert body['max_tokens']==80
        assert body['response_format']['json_schema']['strict'] is True
        return httpx.Response(200,json={'model':route,'choices':[{'message':{'content':'{"action":"request_raw"}'}}],
            'usage':{'prompt_tokens':4,'completion_tokens':5,'total_tokens':9}})
    provider=Nightshift(settings,require_nemotron=True);provider.client.close()
    provider.client=httpx.Client(transport=httpx.MockTransport(handle))
    try:
        action,metadata=provider.action('reviewer',{'evidence':'unit synthetic'},['request_raw'],worker)
    finally:provider.close()
    assert action=={'action':'request_raw'}
    assert metadata['actual_serving_model']==route and metadata['usage_source']=='provider_reported'
    assert provider.nemotron_verified is True
