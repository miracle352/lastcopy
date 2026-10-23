"""Explicit local-file CLI; API and worker use only immutable registered IDs."""
import argparse
import io
import json
import sys
import zipfile
from pathlib import Path
from lastcopy.config import ROOT, Settings
from lastcopy.inventory import ImportRejected, digest
from lastcopy.models import RunRequest
from lastcopy.store import RunStore, ARTIFACTS


def bundle_snapshot(envelope, payload):
    result = io.BytesIO()
    with zipfile.ZipFile(result, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in [('server-snapshot.json', envelope), ('server-payload.zip', payload)]:
            info = zipfile.ZipInfo(name, (2026, 10, 23, 10, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    return result.getvalue()


def bounded_file(path, limit):
    with path.open('rb') as file:
        data = file.read(limit + 1)
    if len(data) > limit:
        raise ImportRejected('CLI input exceeds bounded file limit')
    return data


def export(store, run_id, directory):
    directory.mkdir(parents=True, exist_ok=True)
    for name in ARTIFACTS:
        data = store.artifact(run_id, name)
        path = directory / name
        if path.exists():
            if path.is_symlink() or digest(path.read_bytes()) != digest(data):
                raise ValueError('Refusing to overwrite a different export artifact')
        else:
            with path.open('xb') as file:
                file.write(data)


def main(argv=None):
    parser = argparse.ArgumentParser(description='LastCopy deterministic supplied-snapshot runner; no providers or recovery writes')
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'private/stage2')
    subs = parser.add_subparsers(dest='command', required=True)
    run = subs.add_parser('run')
    run.add_argument('--manifest', type=Path, required=True)
    run.add_argument('--device', type=Path, action='append', required=True)
    run.add_argument('--server-manifest', type=Path, required=True)
    run.add_argument('--server-payload', type=Path, required=True)
    run.add_argument('--output', type=Path)
    for name in ['status', 'cancel', 'export']:
        sub = subs.add_parser(name)
        sub.add_argument('run_id')
        if name == 'export':
            sub.add_argument('--output', type=Path, required=True)
    subs.add_parser('resume-queue')
    args = parser.parse_args(argv)
    try:
        settings = Settings.load()
        store = RunStore(args.data_dir, settings)
        if args.command == 'run':
            limit = settings.limit('MAX_UPLOAD_BYTES')
            if len(args.device) > 8:
                raise ImportRejected('At most eight device snapshots per run')
            manifest = store.register('manifest', bounded_file(args.manifest, 65536))
            devices = [store.register('device', bounded_file(p, limit)) for p in args.device]
            server = store.register('server', bundle_snapshot(bounded_file(args.server_manifest, 2097152), bounded_file(args.server_payload, limit)))
            status = store.enqueue(RunRequest(manifest_id=manifest.input_id, device_input_ids=[d.input_id for d in devices], server_input_id=server.input_id))
            store.drain()
            status = store.get(status.run_id)
            if status.state == 'completed':
                directory = args.output or ROOT / 'private/reports' / digest(status.run_id.encode())
                export(store, status.run_id, directory)
        elif args.command == 'cancel':
            status = store.cancel(args.run_id)
        elif args.command == 'resume-queue':
            store.drain()
            print(json.dumps({'queue_processed': True, 'interrupted_jobs_are_not_replayed': True}))
            return 0
        else:
            status = store.get(args.run_id)
            if args.command == 'export':
                export(store, args.run_id, args.output)
        print(status.model_dump_json(indent=2))
        return 0 if status.state == 'completed' or args.command in ('status', 'cancel') else 2
    except (ValueError, KeyError, OSError):
        # File paths, imported record text and settings values are private.
        print(json.dumps({'status': 'rejected', 'reason': 'Invalid, unavailable, conflicting or oversized local input/output; no preservation result claimed'}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
