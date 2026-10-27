"""Turn one sealed investigation directory into a web-safe JSON document.

Usage: python -m scripts.export_investigation <investigation-dir> <output.json> [--label TEXT]

Checks every sealed file hash first, then keeps only what a reader needs:
agent trace lines, graph decisions, SQL text and row counts, model identities,
verdicts, per-device decisions and certificates. No raw field bytes, no tokens,
no hostnames. The document says which engines answered (Zetaris or local SQL,
Nemotron via Nightshift or the offline policy).
"""
import argparse
import json
import re
from pathlib import Path
from lastcopy.inventory import digest

SAFE_EVENT = ('seq', 'kind', 'elapsed_ms', 'agent_name', 'action', 'target_agent', 'input_summary', 'output_summary', 'model', 'status',
              'retry_count', 'fallback', 'next_action', 'focus', 'why', 'counts', 'provider', 'role', 'attempt', 'valid', 'errors',
              'routing_id', 'actual_serving_model', 'usage', 'operation_elapsed_ms', 'query_kind', 'row_count', 'engine', 'query_id',
              'hypothesis', 'before', 'after', 'note', 'tool', 'reason', 'error')
HOST = re.compile(r'https?://\S+|\b\d{1,3}(?:\.\d{1,3}){3}\b')


def clean(value):
    if isinstance(value, str):
        return HOST.sub('[redacted]', value)
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    return value


def export(directory, label=None):
    directory = Path(directory)
    seals = json.loads((directory / 'seals.json').read_bytes())
    for name, sha in seals.items():
        if digest((directory / name).read_bytes()) != sha:
            raise SystemExit(f'Seal mismatch for {name}; refusing to export')
    result = json.loads((directory / 'investigation.json').read_bytes())
    queries = []
    for path in sorted((directory / 'queries').glob('*.json')) if (directory / 'queries').exists() else []:
        q = json.loads(path.read_bytes())
        r = q['receipt']
        queries.append({'query_id': r['query_id'], 'kind': r.get('query_kind'), 'provider': r.get('provider'), 'engine': r.get('engine'),
                        'rows': r.get('row_count'), 'elapsed_ms': r.get('elapsed_ms'),
                        'sql': re.sub(r"'[0-9a-f]{64}'", "'<sha256>'", r.get('sql', ''))})
    events = [{k: e[k] for k in SAFE_EVENT if k in e} for e in result['events']]
    models = sorted({e['actual_serving_model'] for e in result['events'] if e.get('kind') == 'model' and e.get('actual_serving_model')})
    report = result.get('report') or {}
    findings = [{k: f[k] for k in ('finding_id', 'verdict', 'version_id', 'snapshot_id', 'summary', 'media_filenames', 'recovery_eligible', 'evidence_ids')}
                for f in report.get('findings', [])]
    world = [json.loads(line) for line in (directory / 'world.jsonl').read_text().splitlines()] if (directory / 'world.jsonl').exists() else []
    doc = {
        'label': label or f"{result['mode']} run {result['run_id']}",
        'run_id': result['run_id'], 'mode': result['mode'], 'status': result['status'], 'error': result.get('error'),
        'engines': {'evidence': sorted({q['provider'] for q in queries}), 'models': models or ['offline-policy' if result['mode'] == 'sample' else 'none'],
                    'planner': 'Meterless World Model (pinned reference)', 'verdicts': 'deterministic code'},
        'sponsor_status': result.get('sponsor_status'), 'provider_calls': result['provider_calls'], 'steps': result['steps'],
        'critique_rounds': result['critique_rounds'],
        'decisions': [{k: d[k] for k in ('device_id', 'decision', 'reasons', 'counts', 'records', 'certificate', 'certificate_sha256', 'actions', 'explanation')}
                      for d in result.get('decisions', [])],
        'findings': findings, 'coverage': report.get('coverage'), 'remedies': result.get('remedies'),
        'hypotheses': result.get('hypotheses'), 'queries': queries, 'events': events,
        'world_revisions': [{k: r[k] for k in r if k not in ('evidence',)} | {'evidence_count': len(r.get('evidence', []))} for r in world],
        'seals_sha256': digest(json.dumps(seals, sort_keys=True).encode()),
        'report_sha256': result.get('report_sha256'),
    }
    return clean(doc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--label')
    args = parser.parse_args()
    doc = export(args.directory, args.label)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(f"Exported {args.output} ({doc['mode']}, {doc['status']}, models: {', '.join(doc['engines']['models'])})")


if __name__ == '__main__':
    main()
