"""Offline independent checking of an actual connected synthetic run's artifacts.

Does not call a model/network or turn a replay into a live trace. Hashes prove
artifact integrity, not server authentication. Actual calls remain in JSONL.
"""
import argparse
import json
from pathlib import Path
from lastcopy.config import ROOT, Settings
from lastcopy.inventory import digest
from lastcopy.investigation import WorldJournal, encoded
from lastcopy.models import RunManifest
from lastcopy.reconcile import reconcile


def verify(directory, fixture):
    directory, fixture = Path(directory), Path(fixture)
    result = json.loads((directory / 'investigation.json').read_bytes())
    expected = json.loads((fixture / 'expected.json').read_bytes())
    manifest = RunManifest.model_validate_json((directory / 'run-manifest.json').read_bytes())
    assert result['status'] == 'completed' and result['mode'] == 'connected'
    assert result['next_action'] == expected['next_action']
    assert result['steps'] <= manifest.max_steps and result['critique_rounds'] == 2
    assert result['events'][-1]['elapsed_ms'] <= manifest.max_seconds * 1000
    assert result['sponsor_status'] == {'zetaris':'queried','world_model':'read_write_reference',
        'nightshift':'inference_observed','nvidia':'verified'}
    seals = json.loads((directory / 'seals.json').read_bytes())
    assert all(digest((directory / name).read_bytes()) == sha for name, sha in seals.items())
    assert digest((directory / 'report.json').read_bytes()) == result['report_sha256']
    evidence = json.loads((directory / 'query-evidence.json').read_bytes())
    for event in result['events']:
        if event['kind'] != 'query':
            continue
        data = (directory / 'queries' / (event['evidence_object'] + '.json')).read_bytes()
        assert digest(data) == event['evidence_object']
        captured = json.loads(data)
        assert captured['receipt']['query_id'] == event['query_id']
        assert digest(encoded(captured['rows'])) == event['rows_sha256']
        assert event['row_count'] == len(captured['rows']) and event['provider'] == 'zetaris'
    devices, envelope, payload = [], None, None
    for row in evidence['objects']:
        data = (directory / 'objects' / row['object_id']).read_bytes()
        assert digest(data) == row['sha256'] == row['object_id']
        if row['role'] == 'device':
            assert data == (fixture / 'device.zip').read_bytes()
            devices.append(data)
        elif row['role'] == 'envelope':
            assert data == (fixture / 'server-snapshot.json').read_bytes()
            envelope = data
        elif row['role'] == 'payload':
            assert data == (fixture / 'server-payload.zip').read_bytes()
            payload = data
    report = reconcile(manifest, devices, envelope, payload, Settings({'SAMPLE_MODE':'false'})).model_dump(mode='json')
    assert report == result['report']
    assert all(f['verdict'] == expected['verdict'] and not f['recovery_eligible'] for f in report['findings'])
    assert report['provider_calls'] == 0 and report['recovery_executed'] is False
    models = [e for e in result['events'] if e['kind'] == 'model']
    assert len(models) == result['provider_calls'] == 3
    assert all(e['provider'] == 'nightshift' and e['serving_model_resolved'] and
               'nemotron' in e['actual_serving_model'].lower() and
               not e['actual_serving_model'].startswith('meterless/') for e in models)
    reviewers = [e for e in models if e['role'] == 'reviewer']
    assert reviewers[0]['action'] == 'request_raw'
    assert reviewers[-1]['action'] == expected['next_action']
    raw_query = next(e for e in result['events'] if e['kind'] == 'query' and e['query_kind'] == 'versions')
    assert reviewers[0]['seq'] < raw_query['seq']
    actions = [e['next_action'] for e in result['events'] if e['kind'] == 'graph_read']
    assert actions == ['review','fetch_raw',expected['next_action']]
    graph = WorldJournal(directory / 'world.jsonl', manifest.run_id).read()
    assert graph == result['graph']
    assert {'device_snapshot','form_version','submission_version','attachment','observation','hypothesis','recovery_operation'} <= {e['type'] for e in graph['entities']}
    revisions = [h['attrs'] for h in graph['hypotheses']]
    assert len(revisions) == 3 and revisions[-1]['status'] == expected['final_hypothesis']
    assert set(revisions[0]['evidence']) <= set(revisions[-1]['evidence'])
    assert all(f['finding_id'] in result['finding_resolution'] for f in report['findings'])
    return {'status':'PASS','run_id':manifest.run_id,'mode':'connected',
        'verdict':expected['verdict'],'next_action':result['next_action'],
        'hypothesis_history':[r['status'] for r in revisions], 'graph_next_actions':actions,
        'models':sorted({e['actual_serving_model'] for e in models}),
        'usage_source':'Nightshift response-reported; no local estimates added',
        'reported_usage':[e['usage'] for e in models],
        'provider_calls':3,'steps':result['steps'],'critique_rounds':2,
        'elapsed_ms':result['events'][-1]['elapsed_ms'],
        'query_ids':[q['query_id'] for q in evidence['queries']],
        'report_sha256':result['report_sha256'],'independent_recomparison':'PASS',
        'reference_rebuild':'PASS','source_bytes_unchanged':'PASS','output_seals':'PASS',
        'recovery_executed':False,'source_kind':'authored synthetic supplied captures queried through real Zetaris'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    receipt = verify(args.attempt, args.fixture)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
