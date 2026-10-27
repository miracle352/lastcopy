"""Blind benchmark: hidden, randomly planted conditions on every tablet, decided by the full agent loop.

  python -m scripts.blind_eval                      # seeds 1-200, prints a summary table
  python -m scripts.blind_eval --seeds 401-650 --json eval/blind-holdout.json

For each seed a generator (this file) builds a fresh fleet of 2-6 tablets. Each tablet gets
hidden conditions drawn at random: records that matched, a photo that never uploaded, a record
that never arrived, an answer edited on the server, records hidden only by the spreadsheet view,
or an export that was never collected. (An export with no completed records is
rejected at import, so the whole check fails closed; it is not generated here.) The investigation sees only the archives
and the server capture. It never sees the plan. The truth for each tablet is written down here,
from the planted conditions, before the run, and compared only after the decision.

The number that matters is `wrongly_cleared`: tablets the agent called SAFE_TO_WIPE while they
still held the only copy of something, or held data in conflict. It must be 0.
"""
import argparse
import json
import random
import tempfile
import time
from collections import Counter
from pathlib import Path

from scripts.build_stage2_fixtures import AT, PROVENANCE, hash_bytes, pack

FORM = 'household_survey'
SID = 'server-snapshot-blind'
CONDITIONS = ('ok', 'ok', 'view_only', 'no_photo', 'never_arrived', 'edited')
# Truth, from the planted conditions only. Order matters: anything still only on the tablet first.
TRUTH_TEXT = {'RECOVER_FIRST': 'holds the only copy of a record or file',
              'HOLD': 'conflict, empty export or no export: a person must look',
              'SAFE_TO_WIPE': 'everything is already on the server'}


def truth(conditions, exported):
    if not exported:
        return 'HOLD'
    if any(c in ('no_photo', 'never_arrived') for c in conditions):
        return 'RECOVER_FIRST'
    if any(c == 'edited' for c in conditions):
        return 'HOLD'
    if not conditions:
        return 'HOLD'
    return 'SAFE_TO_WIPE'


def scenario(seed):
    """Plan only: which tablets exist, which exported, and what is planted on each record."""
    rng = random.Random(seed)
    n = rng.randint(2, 6)
    plan, roster = {}, [f'tablet-{i:02}' for i in range(1, n + 1)]
    for device in roster:
        r = rng.random()
        if r < 0.12:
            plan[device] = None            # never exported
        else:
            plan[device] = [rng.choice(CONDITIONS) for _ in range(rng.randint(1, 3))]
    if all(v is None for v in plan.values()):  # the pack needs at least one export
        plan[roster[0]] = ['ok']
    return {'seed': seed, 'run_id': f'blind-{seed}', 'roster': roster, 'plan': plan,
            'truth': {d: truth(c or [], c is not None) for d, c in plan.items()}}


def build(spec, repeats=3):
    rng = random.Random(spec['seed'] * 7919)
    readings = ''.join(f'<member><age>{n:02}</age></member>' for n in range(21, 21 + repeats))

    def xml(iid, site='0017'):
        return (f'<data xmlns="urn:lastcopy:test" id="{FORM}" version="3"><village>{site}</village>' + readings +
                '<photo>same.bin</photo><photo>same.bin</photo><twin>a.bin</twin><twin>b.bin</twin>'
                f'<meta><instanceID>{iid}</instanceID></meta></data>').encode()

    xform = (f'<h:html xmlns:h="http://www.w3.org/1999/xhtml" xmlns="http://www.w3.org/2002/xforms">'
             f'<h:head><model><instance><data xmlns="urn:lastcopy:test" id="{FORM}" version="3"/></instance>'
             '<bind nodeset="/data/photo" type="binary"/><bind nodeset="/data/twin" type="binary"/>'
             '</model></h:head></h:html>').encode()
    devices, media_bytes, records = {}, {}, []
    for device, conds in spec['plan'].items():
        if conds is None:
            continue
        root = f'odk/projects/survey/{device}'
        files = {root + '/forms/household_survey.xml': xform}
        entries = []
        for k, cond in enumerate(conds):
            iid = f"uuid:{spec['run_id']}-{device}-{k}"
            binary = bytes(rng.randrange(256) for _ in range(97 + k))
            folder = f'{root}/instances/{iid.split(":")[1]}'
            files[folder + '/submission.xml'] = xml(iid)
            entries.append({'xml_path': folder + '/submission.xml', 'completion_status': 'complete', 'completion_provenance': PROVENANCE})
            for name in ('same.bin', 'a.bin', 'b.bin'):
                files[folder + '/' + name] = binary
            media_bytes[iid] = binary
            records.append((iid, cond))
        manifest = {'schema_version': 1, 'snapshot_id': f'device-snapshot-{device}', 'device_id': device, 'captured_at': AT,
                    'collector_version': 'synthetic-format-v1', 'device_provenance': PROVENANCE, 'synthetic': True,
                    'scope_complete': True, 'scope_provenance': PROVENANCE, 'instances': entries,
                    'form_definitions': [{'xml_path': root + '/forms/household_survey.xml'}]}
        files['device-manifest.json'] = json.dumps(manifest, sort_keys=True)
        devices[device] = pack(files)

    sf, versions, receipts, lists, views = {}, [], [], {}, []

    def receipt(name, file, version=None, attachment=None):
        rid = f'{SID}-{name}'
        receipts.append({'evidence_id': rid, 'source_snapshot_id': SID, 'source_file': file, 'archive_sha256': None, 'captured_at': AT,
                         'query_receipt_id': None, 'request_method': 'LOCAL', 'outcome': 'synthetic',
                         'request_scope': 'blind benchmark synthetic captured scope; not HTTP/SQL', 'response_sha256': hash_bytes(sf[file]),
                         'comparison': None, 'form_id': FORM, 'version_id': version, 'xml_path': None, 'attachment_filename': attachment})
        return rid

    csv_rows = []
    for iid, cond in records:
        key = iid.split(':')[1]
        if cond == 'never_arrived':
            continue
        path = f'raw/{key}/submission.xml'
        sf[path] = xml(iid, site='9999' if cond == 'edited' else '0017')
        receipt(key + '-xml', path, iid)
        missing = ('b.bin',) if cond == 'no_photo' else ()
        listing = f'raw/{key}/attachments.json'
        sf[listing] = json.dumps({'version_id': iid, 'filenames': [n for n in ('same.bin', 'a.bin', 'b.bin') if n not in missing]}).encode()
        lists[iid] = receipt(key + '-attachments', listing, iid)
        media = []
        for name in ('same.bin', 'a.bin', 'b.bin'):
            if name in missing:
                continue
            mp = f'raw/{key}/media/{name}'
            sf[mp] = media_bytes[iid]
            mr = receipt(key + '-' + name, mp, iid, name)
            media.append({'version_id': iid, 'filename': name, 'xml_path': '/media', 'occurrence_indices': [], 'archive_path': mp,
                          'sha256': hash_bytes(media_bytes[iid]), 'readback_receipt_id': mr})
        versions.append({'snapshot_id': SID, 'form_id': FORM, 'form_version': '3', 'logical_submission_id': iid, 'version_id': iid,
                         'deprecated_id': None, 'xml_path': path, 'xml_sha256': hash_bytes(sf[path]), 'completion_status': 'complete',
                         'current': True, 'media': media, 'limitations': []})
        if cond == 'view_only':
            csv_rows.append(iid)
    if csv_rows:
        sf['household_survey.csv'] = ('version_id,village\n' + ''.join(f'{i},0017\n' for i in csv_rows)).encode()
        for iid in csv_rows:
            vr = receipt('tabular-' + iid.split(':')[1], 'household_survey.csv', iid)
            views.append({'version_id': iid, 'archive_path': 'household_survey.csv', 'receipt_id': vr,
                          'columns': {'village': '/{urn:lastcopy:test}data[1]/{urn:lastcopy:test}village[1]'}})
    sf['scope.json'] = json.dumps({'connection_id': 'synthetic-offline-only', 'project_id': 7, 'form_ids': [FORM], 'history_complete': True,
        'versions': [{k: v[k] for k in ['form_id', 'form_version', 'logical_submission_id', 'version_id', 'deprecated_id', 'current']} for v in versions]},
        sort_keys=True).encode()
    listing_id = receipt('scope', 'scope.json')
    server = pack(sf)
    snapshot = {'schema_version': 1, 'snapshot_id': SID, 'kind': 'central_raw', 'archive_sha256': hash_bytes(server), 'captured_at': AT,
                'synthetic': True, 'scope_complete': True, 'connection_id': 'synthetic-offline-only', 'project_id': 7, 'form_ids': [FORM],
                'limitations': [], 'receipt_ids': [r['evidence_id'] for r in receipts], 'receipts': receipts, 'versions': versions,
                'listing_receipt_id': listing_id, 'history_complete': True, 'attachment_listing_receipt_ids': lists, 'tabular_views': views}
    run = {'schema_version': 1, 'run_id': spec['run_id'], 'mode': 'sample',
           'source_snapshot_ids': [f'device-snapshot-{d}' for d in devices] + [SID], 'expected_device_ids': spec['roster'],
           'roster_provenance': PROVENANCE, 'destination': {'connection_id': 'synthetic-offline-only', 'project_id': 7, 'form_id': FORM,
           'environment': 'dedicated_synthetic_test', 'mapping_provenance': PROVENANCE}}
    return run, list(devices.values()), json.dumps(snapshot).encode(), server


def run_seed(seed):
    from lastcopy.config import Settings
    from lastcopy.investigation import EvidencePack, Investigation
    spec = scenario(seed)
    run, devices, envelope, payload = build(spec)
    settings = Settings({'SAMPLE_MODE': 'true'})
    started = time.monotonic()
    with tempfile.TemporaryDirectory() as tmp:
        try:
            result = Investigation(Path(tmp) / 'run', settings).sample(EvidencePack.build(run, devices, envelope, payload, settings))
        except Exception as error:  # a crash is a failed scenario, never a skipped one
            result = {'status': 'failed', 'error': f'{type(error).__name__}: {error}', 'decisions': []}
    got = {d['device_id']: d['decision'] for d in result.get('decisions', [])}
    rows = []
    for device in spec['roster']:
        want, have = spec['truth'][device], got.get(device, 'NO_DECISION')
        rows.append({'device': device, 'planted': spec['plan'][device], 'truth': want, 'decision': have, 'correct': want == have,
                     'wrongly_cleared': have == 'SAFE_TO_WIPE' and want != 'SAFE_TO_WIPE'})
    return {'seed': seed, 'status': result.get('status'), 'error': result.get('error'), 'seconds': round(time.monotonic() - started, 2),
            'steps': result.get('steps'), 'tablets': rows, 'fleet_correct': result.get('status') == 'completed' and all(r['correct'] for r in rows)}


def parse_seeds(text):
    out = []
    for part in text.split(','):
        a, _, b = part.partition('-')
        out += list(range(int(a), int(b or a) + 1))
    return out


def summarise(results):
    tablets = [t for r in results for t in r['tablets']]
    by_truth = Counter((t['truth'], t['correct']) for t in tablets)
    by_cond = Counter()
    for t in tablets:
        tags = ['no export'] if t['planted'] is None else (['empty export'] if not t['planted'] else sorted(set(t['planted'])))
        for tag in tags:
            by_cond[(tag, t['correct'])] += 1
    return {'fleets': len(results), 'fleets_correct': sum(r['fleet_correct'] for r in results),
            'runs_completed': sum(r['status'] == 'completed' for r in results),
            'tablets': len(tablets), 'tablets_correct': sum(t['correct'] for t in tablets),
            'wrongly_cleared': sum(t['wrongly_cleared'] for t in tablets),
            'by_truth': {k: f"{by_truth[(k, True)]}/{by_truth[(k, True)] + by_truth[(k, False)]}" for k in ('SAFE_TO_WIPE', 'RECOVER_FIRST', 'HOLD')},
            'by_planted_condition': {c: f"{by_cond[(c, True)]}/{by_cond[(c, True)] + by_cond[(c, False)]}"
                                     for c in sorted({c for c, _ in by_cond})},
            'mean_seconds_per_fleet': round(sum(r['seconds'] for r in results) / max(1, len(results)), 2)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--seeds', default='1-200')
    parser.add_argument('--json', type=Path)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    seeds = parse_seeds(args.seeds)
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(args.workers) as pool:
        results = list(pool.map(run_seed, seeds))
    s = summarise(results)
    print(f"Blind benchmark, seeds {args.seeds}: {s['fleets_correct']}/{s['fleets']} fleets and "
          f"{s['tablets_correct']}/{s['tablets']} tablets decided correctly; wrongly cleared: {s['wrongly_cleared']}")
    for k, v in s['by_truth'].items():
        print(f'  truth {k:<14} {v}')
    for k, v in s['by_planted_condition'].items():
        print(f'  planted {k:<14} {v}')
    for r in results:
        if not r['fleet_correct']:
            print('  MISS seed', r['seed'], r['status'], r['error'], [(t['device'], t['planted'], t['truth'], t['decision']) for t in r['tablets'] if not t['correct']])
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({'seeds': args.seeds, 'summary': s, 'runs': results}, indent=1) + '\n', encoding='utf-8', newline='\n')
    raise SystemExit(0 if s['wrongly_cleared'] == 0 and s['fleets_correct'] == s['fleets'] else 1)


if __name__ == '__main__':
    main()
