"""Bounded Stage 3 CLI. Explicit operator paths only; no model-supplied paths/SQL."""
import argparse
import json
import multiprocessing
import time
from pathlib import Path
from lastcopy.config import ROOT, Settings
from lastcopy.investigation import EvidencePack, Investigation, InvestigationError
from lastcopy.connected import ZetarisEvidence, Nightshift
from scripts.run import bounded_file
from lastcopy.store import RunStore
from lastcopy.investigation import encoded, seal_outputs


def execute(pack, output, settings, connected, nemotron=False, replay=False):
    worker = Investigation(output, settings)
    if not connected:
        worker.replay(pack) if replay else worker.sample(pack)
        return
    evidence, provider = ZetarisEvidence(output, worker), None
    try:
        from lastcopy.cloud_ai import configuration
        config=configuration(settings)
        if config.get('AI_PROVIDER')=='nvidia_direct':
            if nemotron:raise InvestigationError('NVIDIA award requires Nemotron through Nightshift; direct cloud is not that path')
            from lastcopy.nvidia_cloud import NvidiaCloud
            provider=NvidiaCloud(Settings(dict(settings.values,**config)))
        else:provider = Nightshift(settings, require_nemotron=nemotron)
        worker.connected(pack, evidence, provider)
    except InvestigationError as error:
        if not (output / 'events.jsonl').exists():
            worker.begin(pack, 'connected')
        worker.finish('failed', error=str(error))
    finally:
        evidence.close()
        if provider:
            provider.close()


def supervise(target, arguments, output, run):
    """Hard deadline/cancel even while an integration socket or engine is blocked.

    One CLI worker owns one attempt. Never resumes/repeats provider operations.
    A killed publication may leave bounded synthetic tables; no raw/recovery writes.
    """
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise InvestigationError('Use a fresh empty attempt directory; existing evidence is immutable')
    process = multiprocessing.get_context('spawn').Process(target=target, args=arguments)
    started = time.monotonic()
    process.start()
    reason = None
    try:
        while process.is_alive():
            if (output / 'cancel').exists():
                reason = ('cancelled', 'Investigation cancelled; no recovery executed')
                break
            if time.monotonic() - started >= run.max_seconds:
                reason = ('failed', 'Investigation hard wall-time budget exhausted')
                break
            process.join(.1)
    except KeyboardInterrupt:
        reason = ('cancelled', 'Investigation cancelled by operator')
    if reason:
        process.terminate()
        process.join(5)
        if process.is_alive():
            process.kill()
            process.join()
    result_path = output / 'investigation.json'
    if result_path.exists():
        return json.loads(result_path.read_bytes())
    output.mkdir(parents=True, exist_ok=True)
    event_path = output / 'events.jsonl'
    events = [json.loads(line) for line in event_path.read_bytes().splitlines()] if event_path.exists() else []
    status, error = reason or ('interrupted', 'Worker exited without a terminal result; no automatic replay')
    event = dict(run_id=run.run_id, mode=run.mode, seq=len(events) + 1, kind=status,
                 elapsed_ms=round((time.monotonic() - started) * 1000, 2), error=error)
    with event_path.open('ab') as file:
        file.write(encoded(event) + b'\n')
    result = dict(run_id=run.run_id, mode=run.mode, status=status, error=error,
        provider_calls=sum(e['kind'] == 'model' for e in events), provider_attempts='see tool events; terminated request usage unavailable',
        steps=sum(e['kind'] == 'tool' for e in events), critique_rounds=sum(e.get('role') == 'reviewer' for e in events), events=events + [event])
    result_path.write_bytes(encoded(result) + b'\n')
    seal_outputs(output)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--device', type=Path, action='append', required=True)
    parser.add_argument('--server-manifest', type=Path, required=True)
    parser.add_argument('--server-payload', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--connected', action='store_true')
    modes.add_argument('--replay', action='store_true', help='Offline supplied-capture comparison labelled replay; no replayed model calls')
    parser.add_argument('--nemotron', action='store_true', help='Connected award check: discover a Nemotron route and require its actual reported serving identity')
    args = parser.parse_args()
    if args.nemotron and not args.connected:
        parser.error('--nemotron requires --connected')
    settings = Settings.load()
    manifest = json.loads(bounded_file(args.manifest, 65536))
    if args.connected:
        manifest['mode'] = 'connected'
    elif args.replay:
        manifest['mode'] = 'replay'
    elif manifest['mode'] != 'sample':
        parser.error('Non-sample manifest requires --connected or --replay; no implicit mode fallback')
    pack = EvidencePack.build(manifest, [bounded_file(p, 10485760) for p in args.device],
        bounded_file(args.server_manifest, 2097152), bounded_file(args.server_payload, 10485760), settings)
    # One investigation process across CLI invocations. Existing Stage 2 workers
    # keep their separate four-job queue; no unbounded background AI job pool.
    with RunStore(ROOT / 'private/stage3-jobs', settings).lease() as acquired:
        if not acquired:
            raise InvestigationError('Another Stage 3 job owns the runner; retry after it finishes')
        result = supervise(execute, (pack, args.output, settings, args.connected, args.nemotron, args.replay), args.output, pack.run)
    print(json.dumps({key: result[key] for key in ('run_id', 'mode', 'status', 'provider_calls', 'steps', 'critique_rounds')}, indent=2))
    for decision in result.get('decisions', []):
        print(f"{decision['device_id']:>12}  {decision['decision']:<14} {(decision.get('explanation') or {}).get('text', '')}")
    if 'error' in result:
        print(result['error'])
    return 0 if result['status'] == 'completed' else 2


if __name__ == '__main__':
    raise SystemExit(main())
