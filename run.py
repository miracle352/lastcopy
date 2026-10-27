"""LastCopy entry point for judges and operators.

  python run.py                                   investigate the five-tablet example (no credentials, no network)
  python run.py input_examples/example_2.json     investigate any bundled example
  python run.py --all                             run every example and refresh output_examples/ and logs/
  python run.py --serve                           start the HTTP API on 0.0.0.0:$PORT (POST /investigate)

Sample mode runs the full agent loop: World Model planning, the Scout's SQL on a
local engine, the offline policy in the model roles, the deterministic verifier,
the wipe gate and the explanation check. Connected mode (Zetaris + Nightshift +
Nemotron) runs with `python -m scripts.investigate --connected --nemotron ...`.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXAMPLES = sorted((ROOT / 'input_examples').glob('example_*.json'))
COLOURS = {'SAFE_TO_WIPE': '\033[32m', 'RECOVER_FIRST': '\033[33m', 'HOLD': '\033[31m'}


def load_example(path: Path) -> dict:
    spec = json.loads(Path(path).read_text(encoding='utf-8'))
    for key in ('manifest', 'server_manifest', 'server_payload', *[f'devices[{i}]' for i in range(len(spec['devices']))]):
        value = spec['devices'][int(key[8:-1])] if key.startswith('devices[') else spec[key]
        resolved = (ROOT / value).resolve()
        if not resolved.is_relative_to(ROOT / 'fixtures') or not resolved.is_file():
            raise SystemExit(f'{path}: {value} must be a bundled file under fixtures/')
    return spec


def guideline_trace(result: dict, started: datetime) -> list[dict]:
    """The Technical Execution Guide's recommended JSONL shape, one line per agent action."""
    lines = []
    for e in result['events']:
        if e['kind'] not in ('agent', 'model', 'query', 'fallback', 'decision_changed', 'provider_failure', 'completed', 'failed', 'started'):
            continue
        at = started.timestamp() + e.get('elapsed_ms', 0) / 1000
        base = {'timestamp': datetime.fromtimestamp(at, timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-4] + 'Z', 'run_id': result['run_id'],
                'trace_id': 'trace-' + result['run_id'], 'mode': result['mode']}
        if e['kind'] == 'agent':
            lines.append(base | {k: e.get(k) for k in ('agent_name', 'action', 'input_summary', 'output_summary', 'target_agent', 'model',
                                                         'confidence', 'retry_count', 'status')} | ({'fallback': True} if e.get('fallback') else {}))
        elif e['kind'] == 'model':
            lines.append(base | {'agent_name': e.get('role', '').title(), 'action': 'model_request', 'model': e.get('actual_serving_model') or e.get('provider'),
                                 'provider': e.get('provider'), 'routing_id': e.get('routing_id'), 'status': 'success' if e.get('valid') else 'invalid_output',
                                 'retry_count': e.get('attempt', 1) - 1, 'output_summary': '; '.join(e.get('errors', [])) or 'schema-valid JSON'})
        elif e['kind'] == 'query':
            lines.append(base | {'agent_name': 'Scout' if e.get('query_kind') in ('export_gaps', 'missing_versions', 'missing_media', 'xml_mismatch') else 'Evidence fetcher',
                                 'action': 'sql_query', 'input_summary': e.get('query_kind'), 'output_summary': f"{e.get('row_count')} rows",
                                 'model': e.get('provider'), 'query_id': e.get('query_id'), 'status': 'success', 'retry_count': 0})
        else:
            lines.append(base | {'agent_name': 'Orchestrator', 'action': e['kind'], 'output_summary': e.get('note') or e.get('reason') or e.get('error'),
                                 'status': e['kind']} | ({'before': e['before'], 'after': e['after']} if e['kind'] == 'decision_changed' else {}))
    return lines


def investigate(path: Path, quiet: bool = False) -> dict:
    os.environ.setdefault('SAMPLE_MODE', 'true')
    from lastcopy.config import Settings
    from lastcopy.investigation import EvidencePack, Investigation
    from scripts.export_investigation import export
    spec = load_example(path)
    read = lambda p: (ROOT / p).read_bytes()
    manifest = json.loads(read(spec['manifest']))
    settings = Settings({'SAMPLE_MODE': 'true'})
    pack = EvidencePack.build(manifest, [read(d) for d in spec['devices']], read(spec['server_manifest']), read(spec['server_payload']), settings)
    out = ROOT / 'private' / 'runs' / f"{manifest['run_id']}-{int(time.time() * 1000)}"
    started = datetime.now(timezone.utc)
    if not quiet:
        print(f"\n[INFO] run_id={manifest['run_id']} mode=sample question={spec['question']!r}")
    result = Investigation(out, settings).sample(pack)
    trace = guideline_trace(result, started)
    logs = ROOT / 'logs'
    logs.mkdir(exist_ok=True)
    log_file = logs / f"trace-{manifest['run_id']}.jsonl"
    log_file.write_text(''.join(json.dumps(line, ensure_ascii=False) + '\n' for line in trace), encoding='utf-8', newline='\n')
    if not quiet:
        for line in trace:
            if line.get('action') in ('model_request', 'sql_query'):
                continue
            print(f"[INFO] {line.get('agent_name', ''):<22} {line.get('action', ''):<26} -> {line.get('target_agent') or '':<20} "
                  f"{(line.get('output_summary') or '')[:90]}  ({line.get('model') or ''})")
    if result['status'] != 'completed':
        print(json.dumps({'run_id': result['run_id'], 'status': result['status'], 'error': result.get('error')}, indent=2))
        raise SystemExit(2)
    doc = export(out, label=spec['question'])
    doc['question'] = spec['question']
    doc['log_file'] = str(log_file.relative_to(ROOT)).replace('\\', '/')
    doc['execution_time_seconds'] = round((datetime.now(timezone.utc) - started).total_seconds(), 2)
    if not quiet:
        print(f"\n  {'DEVICE':<12} {'DECISION':<14} WHY")
        for d in doc['decisions']:
            colour = COLOURS.get(d['decision'], '') if sys.stdout.isatty() else ''
            print(f"  {d['device_id']:<12} {colour}{d['decision']:<14}\033[0m {d['explanation']['text']}" if colour else
                  f"  {d['device_id']:<12} {d['decision']:<14} {d['explanation']['text']}")
        print(f"\n[INFO] Completed in {doc['execution_time_seconds']} s; trace: {doc['log_file']}; "
              f"engines: evidence={','.join(doc['engines']['evidence'])} models={','.join(doc['engines']['models'])}")
    return doc


def serve():
    import uvicorn
    os.environ.setdefault('SAMPLE_MODE', 'true')
    uvicorn.run('lastcopy.api:app', host='0.0.0.0', port=int(os.environ.get('PORT', '8000')))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('example', nargs='?', type=Path, default=ROOT / 'input_examples' / 'example_1.json')
    parser.add_argument('--all', action='store_true', help='run every bundled example and refresh output_examples/')
    parser.add_argument('--serve', action='store_true', help='start the HTTP API')
    args = parser.parse_args()
    if args.serve:
        return serve()
    targets = EXAMPLES if args.all else [args.example]
    for path in targets:
        doc = investigate(path)
        if args.all:
            out = ROOT / 'output_examples' / (path.stem + '_output.json')
            out.parent.mkdir(exist_ok=True)
            out.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
            print(f'[INFO] wrote {out.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
