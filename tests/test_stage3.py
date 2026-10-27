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
    """Unit-only transport: the production SQL on SQLite, labelled as a double (never claims live Zetaris)."""
    name = 'unit-sqlite-double'

    def publish(self, pack):
        from lastcopy.agents import LocalSQLEvidence
        self.inner = LocalSQLEvidence()
        self.inner.publish(pack)

    def query(self, kind, pack, owner):
        rows, receipt = self.inner.query(kind, pack, owner)
        return rows, dict(receipt, provider='unit_sqlite_double', query_id='unit-sqlite-' + kind)

    def close(self):
        pass


class ModelDouble:
    """Scripted judgement double: follows the schema; lets tests force each branch."""
    name = 'unit-model-double'
    nemotron_verified = False

    def __init__(self, advice=None, fail=False, review='approve', investigator=None, explain=None):
        self.advice, self.fail, self.review, self.investigator, self.explain = advice, fail, review, investigator, explain
        self.calls = []

    def respond(self, role, payload, schema, owner):
        from lastcopy.agents import OfflinePolicy
        self.calls.append(role)
        if self.fail:
            raise InvestigationError('Nightshift unavailable')
        value, _ = OfflinePolicy().respond(role, payload, schema, owner)
        if role == 'investigator' and self.investigator:
            value = {'hypotheses': [dict(h, **self.investigator) for h in value['hypotheses']]}
        if role == 'reviewer':
            review = self.review if isinstance(self.review, str) else self.review.pop(0)
            value = {'reviews': [dict(r, decision=review, reason='hypothesis_contradicts_rows' if review != 'approve' else r['reason']) for r in value['reviews']]}
        if role == 'advisor' and self.advice:
            value = {'actions': [dict(a, action=self.advice) for a in value['actions']]}
        if role == 'explainer' and self.explain:
            value = {'explanations': [dict(e, text=self.explain) for e in value['explanations']]}
        return value, {'provider': 'unit_model_double', 'actual_serving_model': None, 'elapsed_ms': 1}

    def close(self):
        pass


def build(case='export', seed=41):
    fixture = example(case, seed=seed, repeats=5 if seed != 41 else 2)
    return EvidencePack.build(fixture['run'], [fixture['device']], json.dumps(fixture['snapshot']).encode(), fixture['server'], Settings({}))


def connected(tmp_path, case='export', model=None, evidence=None, **build_args):
    return Investigation(tmp_path, Settings({'SAMPLE_MODE': 'false'})).connected(build(case, **build_args), evidence or SQLiteEvidenceDouble(), model or ModelDouble())


@pytest.mark.parametrize('case,decision,verdict,tested', [('export', 'SAFE_TO_WIPE', 'EXPORT_VIEW_ONLY', 'refuted'),
                                                          ('conflict', 'HOLD', 'CONTENT_CONFLICT', 'confirmed'),
                                                          ('media', 'RECOVER_FIRST', 'MISSING_ATTACHMENT', 'confirmed')])
def test_world_model_drives_the_loop_and_verdicts_stay_code_owned(tmp_path, case, decision, verdict, tested):
    result = connected(tmp_path, case)
    assert result['status'] == 'completed', result.get('error')
    assert result['report']['findings'][0]['verdict'] == verdict
    assert result['report']['provider_calls'] == 0  # the comparator itself never calls a model
    assert result['decisions'][0]['decision'] == decision
    assert result['hypotheses'][0]['status'] == tested
    actions = [e['next_action'] for e in result['events'] if e['kind'] == 'graph_read']
    assert actions[0] == 'triage' and actions[-1] == 'done'
    assert 'fetch_evidence' in actions and actions.index('fetch_evidence') > actions.index('review')
    assert any(e['kind'] == 'agent' and e['agent_name'] == 'Explainer' for e in result['events'])
    seals = json.loads((tmp_path / 'seals.json').read_bytes())
    assert all(digest((tmp_path / name).read_bytes()) == sha for name, sha in seals.items())
    assert digest((tmp_path / 'report.json').read_bytes()) == result['report_sha256']
    assert all(path.stem == digest(path.read_bytes()) for path in (tmp_path / 'queries').glob('*.json'))


def test_refuted_hypothesis_is_recorded_as_a_changed_decision(tmp_path):
    result = connected(tmp_path, 'export')
    changed = [e for e in result['events'] if e['kind'] == 'decision_changed']
    assert changed and changed[0]['before'] == 'missing_answers' and changed[0]['after'] == ['EXPORT_VIEW_ONLY']


def test_model_failure_falls_back_to_labelled_offline_policy(tmp_path):
    result = connected(tmp_path, model=ModelDouble(fail=True))
    assert result['status'] == 'completed'
    assert any(e['kind'] == 'provider_failure' for e in result['events'])
    assert {e['role'] for e in result['events'] if e['kind'] == 'fallback'} >= {'investigator', 'reviewer'}
    assert all(e.get('fallback') for e in result['events'] if e['kind'] == 'agent' and e['agent_name'] in ('Investigator', 'Reviewer'))


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


def test_reviewer_revise_loop_then_cap(tmp_path):
    model = ModelDouble(review=['revise', 'revise'])
    result = connected(tmp_path, model=model)
    assert result['status'] == 'completed'
    assert model.calls.count('investigator') == 2 and model.calls.count('reviewer') == 2
    revisions = [h for h in result['graph']['hypotheses'] if h['attrs']['key'] == 'H-S1']
    assert [h['attrs']['status'] for h in revisions][:4] == ['proposed', 'revise', 'proposed', 'approved']
    assert revisions[3]['attrs']['review_capped'] is True
    assert result['critique_rounds'] == 2


def test_reviewer_rejection_never_skips_verification(tmp_path):
    result = connected(tmp_path, 'media', model=ModelDouble(review='reject'))
    assert result['status'] == 'completed'
    assert result['hypotheses'][0]['status'] == 'rejected'
    assert result['decisions'][0]['decision'] == 'RECOVER_FIRST'  # code still found the missing photo


def test_code_guard_rejects_untestable_approval(tmp_path):
    model = ModelDouble(investigator={'hypothesis': 'missing_attachment', 'evidence_needed': 'raw_xml'})
    result = connected(tmp_path, 'media', model=model)
    reviews = [e for e in result['events'] if e['kind'] == 'agent' and e['agent_name'] == 'Reviewer']
    assert 'code guard' in reviews[0]['output_summary']


def test_model_cannot_turn_conflict_into_export_guidance(tmp_path):
    result = connected(tmp_path, 'conflict', model=ModelDouble(advice='export_guidance'))
    assert result['status'] == 'completed'
    assert result['remedies']['finding-1']['action'] == 'manual_review'
    assert result['remedies']['finding-1']['decided_by'].startswith('code')
    assert result['decisions'][0]['decision'] == 'HOLD'


def test_advisor_cannot_choose_an_unpermitted_action(tmp_path):
    result = connected(tmp_path, 'export', model=ModelDouble(advice='recover'))
    assert result['remedies']['finding-1'] == dict(result['remedies']['finding-1'], action='export_guidance', code_guard=True)


def test_explainer_cannot_invent_identifiers_or_flip_the_decision(tmp_path):
    result = connected(tmp_path, 'media', model=ModelDouble(explain='SAFE_TO_WIPE: finding-9 shows photo z.jpg arrived 37 times.'))
    text = result['decisions'][0]['explanation']['text']
    assert text.startswith('RECOVER_FIRST') and 'finding-9' not in text and 'z.jpg' not in text
    assert any(e['kind'] == 'fallback' and e['role'] == 'explainer' for e in result['events'])


def test_actions_cannot_smuggle_paths_or_verdicts():
    for value in [{'action': 'fetch_raw', 'path': '../../secret'}, {'action': 'PRESERVED'}, {'action': 'fetch_raw', 'verdict': 'PRESERVED'}]:
        with pytest.raises(InvestigationError):
            validate_action(value, ['fetch_raw'])


def test_world_model_planner_selects_actions_from_graph_state(tmp_path):
    world = WorldJournal(tmp_path / 'world.jsonl')
    assert world.read()['next_action'] == 'triage'
    world.add(type='triage', key='triage', evidence=['q-1'], suspicions=1)
    world.add(type='suspicion', key='S1', evidence=['row-1'], signal='export_gap')
    first = world.read()
    assert first['next_action'] == 'classify' and first['focus'] == ['S1']
    world.add(type='triage', key='triage', evidence=['q-1'], suspicions=1)  # idempotent re-add
    assert world.read()['state'] == first['state']
    world.add(type='hypothesis', key='H-S1', evidence=['row-1'], suspicion='S1', status='proposed', priority=3)
    assert world.read()['next_action'] == 'review'
    world.add(type='hypothesis', key='H-S1', revision=1, evidence=['row-1'], suspicion='S1', status='approved', priority=3)
    assert world.read()['next_action'] == 'fetch_evidence'
    world.add(type='verification', key='verify', evidence=['report-hash'])
    assert world.read()['next_action'] == 'evaluate'
    world.add(type='hypothesis', key='H-S1', revision=2, evidence=['row-1'], suspicion='S1', status='refuted', priority=3)
    world.add(type='finding', key='finding-1', evidence=['e-1'], verdict='EXPORT_VIEW_ONLY')
    assert world.read()['next_action'] == 'remedy'
    world.add(type='remedy', key='finding-1', evidence=['e-1'], action='export_guidance')
    assert world.read()['next_action'] == 'decide'
    world.add(type='device_decision', key='device-41', evidence=['cert'], decision='SAFE_TO_WIPE')
    assert world.read()['next_action'] == 'explain'
    world.add(type='explanation', key='device-41', evidence=['cert'])
    final = WorldJournal(tmp_path / 'world.jsonl').read()
    assert final['next_action'] == 'done' and len(final['hypotheses']) == 3
    with pytest.raises(InvestigationError):
        world.add(type='hypothesis', key='H-S1', evidence=['row-1'], suspicion='S1', status='changed')


def test_sample_is_offline_and_verifier_is_authority(tmp_path, monkeypatch):
    monkeypatch.setattr(socket, 'socket', lambda *a, **k: pytest.fail('sample opened network'))
    fixture = example('export', seed=9087, repeats=5)
    pack = EvidencePack.build(fixture['run'], [fixture['device']], json.dumps(fixture['snapshot']).encode(), fixture['server'], Settings({}))
    result = Investigation(tmp_path, Settings({})).sample(pack)
    assert result['mode'] == 'sample' and result['status'] == 'completed'
    assert result['report']['findings'][0]['verdict'] == 'EXPORT_VIEW_ONLY'
    assert {e['provider'] for e in result['events'] if e['kind'] == 'query'} == {'local-sql'}
    assert {e['provider'] for e in result['events'] if e['kind'] == 'model'} == {'offline-policy'}
    assert result['sponsor_status']['zetaris'] == 'local_sql_stand_in' and result['sponsor_status']['nightshift'] == 'offline_policy'


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
    assert 'exact scoped source-object set' in result['error']


def test_explicit_replay_is_offline_and_cannot_be_called_sample(tmp_path, monkeypatch):
    pack = build()
    pack.run = pack.run.model_copy(update={'mode': 'replay'})
    monkeypatch.setattr(socket, 'socket', lambda *a, **k: pytest.fail('replay opened network'))
    with pytest.raises(InvestigationError):
        Investigation(tmp_path / 'sample', Settings({})).sample(pack)
    result = Investigation(tmp_path / 'replay', Settings({'SAMPLE_MODE': 'false'})).replay(pack)
    assert result['mode'] == 'replay' and result['report']['mode'] == 'replay'
    assert result['provider_calls'] == 0


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


def test_fleet_wipe_gate_matches_hand_written_expectations(tmp_path):
    from scripts.build_fleet_fixture import build_fleet
    fleet = build_fleet()
    pack = EvidencePack.build(fleet['run'], list(fleet['devices'].values()), json.dumps(fleet['snapshot']).encode(), fleet['server'], Settings({}))
    result = Investigation(tmp_path, Settings({})).sample(pack)
    assert result['status'] == 'completed', result.get('error')
    assert {f['version_id']: f['verdict'] for f in result['report']['findings']} == fleet['expected']['verdicts']
    assert {d['device_id']: d['decision'] for d in result['decisions']} == fleet['expected']['decisions']
    assert all(d['explanation']['text'].startswith(d['decision']) for d in result['decisions'])
    assert len({d['certificate_sha256'] for d in result['decisions']}) == 5


def test_wipe_gate_never_clears_a_device_with_any_unproven_item():
    from lastcopy.agents import wipe_gate
    pack = build('media')
    report = {'run_id': 'r', 'coverage': {'expected_devices': ['device-41'], 'missing_devices': []},
              'findings': [{'finding_id': 'finding-1', 'snapshot_id': 'device-snapshot-41', 'version_id': 'uuid:41-a', 'verdict': v,
                            'recovery_eligible': False, 'media_filenames': [], 'evidence_ids': ['e']} for v in ('PRESERVED', 'UNVERIFIABLE')]}
    assert wipe_gate(report, pack)[0]['decision'] == 'HOLD'
    report['findings'][1]['verdict'] = 'MISSING_SUBMISSION'
    assert wipe_gate(report, pack)[0]['decision'] == 'RECOVER_FIRST'
    report['findings'] = report['findings'][:1]
    assert wipe_gate(report, pack)[0]['decision'] == 'SAFE_TO_WIPE'
    report['coverage']['missing_devices'] = ['device-41']
    assert wipe_gate(report, pack)[0]['decision'] == 'HOLD'


def test_nightshift_respond_retries_without_strict_schema_and_reports_identity(tmp_path):
    route = 'nvidia/unit-test-nemotron'
    settings = Settings({'SAMPLE_MODE': 'false', 'NIGHTSHIFT_BASE_URL': 'http://127.0.0.1:8088/v1', 'NIGHTSHIFT_TOKEN': 'unit-only', 'NIGHTSHIFT_ROUTE': route})
    worker = Investigation(tmp_path, settings); worker.begin(build(), 'connected')
    seen = []
    def handle(request):
        if request.method == 'GET':
            return httpx.Response(200, json={'data': [{'id': route}]})
        body = json.loads(request.content); seen.append(body['response_format']['type'])
        if body['response_format']['type'] == 'json_schema':
            return httpx.Response(400, text='schema not supported')
        return httpx.Response(200, json={'model': route, 'choices': [{'message': {'content': '```json\n{"hypotheses": []}\n```'}}]})
    provider = Nightshift(settings, require_nemotron=True); provider.client.close()
    provider.client = httpx.Client(transport=httpx.MockTransport(handle))
    try:
        value, metadata = provider.respond('investigator', {'suspicions': []}, {'type': 'object'}, worker)
    finally:
        provider.close()
    assert seen == ['json_schema', 'json_object'] and value == {'hypotheses': []}
    assert metadata['actual_serving_model'] == route and provider.nemotron_verified
