"""Operator CLI over the same registered-ID recovery flow as the local API."""
import argparse
import json
from pathlib import Path
from lastcopy.config import Settings, ROOT
from lastcopy.inventory import digest, inventory
from lastcopy.models import RunManifest
from lastcopy.store import RunStore, encoded
from lastcopy.recovery import RecoveryEngine
from lastcopy.odk_recovery import CentralRecovery, configured_target
from scripts.run import bundle_snapshot


def capture_registered(store, manifest_id, device_input_ids, *, read_only=False):
    if store.settings.sample: raise ValueError('SAMPLE_MODE prohibits live captures')
    run = RunManifest.model_validate_json(store.input(manifest_id,'manifest'))
    if run.mode != 'connected': raise ValueError('Live capture requires a connected manifest')
    if not 1 <= len(device_input_ids) <= 8 or len(set(device_input_ids)) != len(device_input_ids):
        raise ValueError('One to eight unique registered device IDs required')
    source_ids = [inventory(store.input(i,'device'),store.settings).manifest.snapshot_id for i in device_input_ids]
    remote = CentralRecovery(store.settings,read_only=read_only)
    try: envelope,payload = remote.capture(run)
    finally: remote.client.close()
    snap = json.loads(envelope)
    # Produce a new immutable manifest; never mutate the registered original.
    source_ids += [snap['snapshot_id']]
    updated = run.model_copy(update={'source_snapshot_ids':source_ids})
    m = store.register('manifest',updated.model_dump_json().encode())
    s = store.register('server',bundle_snapshot(envelope,payload))
    return {'manifest_id':m.input_id,'server_input_id':s.input_id,'snapshot_id':snap['snapshot_id'],
            'envelope_sha256':digest(envelope),'payload_sha256':digest(payload),'mode':'connected'}


def save_new(path, data):
    if path.exists():
        if path.is_symlink() or path.read_bytes()!=data: raise ValueError('Refusing to overwrite a different output')
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as f: f.write(data)


def main(argv=None):
    p = argparse.ArgumentParser(description='Reviewed synthetic ODK recovery; IDs only, explicit target confirmation')
    p.add_argument('--data-dir',type=Path,default=ROOT/'private/stage2')
    sub = p.add_subparsers(dest='command',required=True)
    stage = sub.add_parser('stage'); stage.add_argument('run_id'); stage.add_argument('finding_id')
    capture = sub.add_parser('capture'); capture.add_argument('manifest_id'); capture.add_argument('--device-input-id',action='append',required=True);capture.add_argument('--read-only',action='store_true',help='Use the separately configured collection read scope')
    for command in ('get','review','apply','bundle','events','result'):
        parser = sub.add_parser(command); parser.add_argument('plan_id')
        if command in ('review','apply'):
            parser.add_argument('--plan-sha256',required=True)
            parser.add_argument('--target-sha256',required=True,help='SHA256 of canonical target JSON, printed by get/stage')
        if command in ('bundle','events','result'): parser.add_argument('--output',type=Path,required=True)
    args = p.parse_args(argv)
    settings = Settings.load(); store = RunStore(args.data_dir,settings)
    try:
        if args.command == 'capture': result = capture_registered(store,args.manifest_id,args.device_input_id,read_only=args.read_only)
        else:
            engine = RecoveryEngine(store,None if settings.sample else configured_target(settings))
            if args.command == 'stage': result = engine.stage(args.run_id,args.finding_id)
            elif args.command == 'get': result = engine.get(args.plan_id)
            elif args.command in ('review','apply'):
                plan = engine.get(args.plan_id)
                if args.target_sha256 != digest(encoded(plan['target'])) or args.plan_sha256 != plan['plan_sha256']:
                    raise ValueError('Explicit target/plan hash confirmation differs')
                if args.command == 'review': result = engine.review(args.plan_id,args.plan_sha256,plan['target'])
                else:
                    if settings.sample: raise ValueError('SAMPLE_MODE prohibits Apply')
                    engine.remote = CentralRecovery(settings)
                    try: result = engine.apply(args.plan_id)
                    finally: engine.remote.client.close()
            else:
                data = engine.bundle(args.plan_id) if args.command=='bundle' else engine.events(args.plan_id) if args.command=='events' else encoded(engine.result(args.plan_id))
                save_new(args.output,data)
                result = {'plan_id':args.plan_id,'output_sha256':digest(data),'bytes':len(data)}
        if 'target' in result: result = dict(result,target_sha256=digest(encoded(result['target'])))
        print(json.dumps(result,indent=2))
        return 2 if result.get('state') in ('blocked','with_gaps') else 0
    except (ValueError,KeyError) as e:
        print(json.dumps({'error':str(e)})); return 2


if __name__ == '__main__': raise SystemExit(main())
