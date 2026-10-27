"""Authored synthetic five-tablet survey team for the wipe-gate demo.

Expected outcomes are hand-written literals (expected.json), never comparator output.

tablet-01  two records; the server spreadsheet omits repeated answers, raw XML has them  -> SAFE_TO_WIPE
tablet-02  one record; its photo b.bin never reached the server                          -> RECOVER_FIRST
tablet-03  two records; one never reached the server at all                              -> RECOVER_FIRST
tablet-04  one record; the server copy has a different answer                            -> HOLD
tablet-05  on the roster, no export received                                             -> HOLD
"""
import json
import random
from pathlib import Path
from scripts.build_stage2_fixtures import AT, PROVENANCE, hash_bytes, pack

FORM = 'household_survey'
SID = 'server-snapshot-fleet'


def build_fleet(seed=2026, repeats=3):
    rng = random.Random(seed)
    readings = ''.join(f'<member><age>{n:02}</age></member>' for n in range(21, 21 + repeats))

    def xml(iid, site='0017'):
        return (f'<data xmlns="urn:lastcopy:test" id="{FORM}" version="3"><village>{site}</village>' + readings +
                '<photo>same.bin</photo><photo>same.bin</photo><twin>a.bin</twin><twin>b.bin</twin>'
                f'<meta><instanceID>{iid}</instanceID></meta></data>').encode()

    xform = (f'<h:html xmlns:h="http://www.w3.org/1999/xhtml" xmlns="http://www.w3.org/2002/xforms">'
             f'<h:head><model><instance><data xmlns="urn:lastcopy:test" id="{FORM}" version="3"/></instance>'
             '<bind nodeset="/data/photo" type="binary"/><bind nodeset="/data/twin" type="binary"/>'
             '</model></h:head></h:html>').encode()
    plan = {  # device -> list of (instance id, server behaviour)
        'tablet-01': [('uuid:fleet-01-a', 'ok'), ('uuid:fleet-01-b', 'ok')],
        'tablet-02': [('uuid:fleet-02-a', 'no_photo')],
        'tablet-03': [('uuid:fleet-03-a', 'ok'), ('uuid:fleet-03-b', 'never_arrived')],
        'tablet-04': [('uuid:fleet-04-a', 'edited')],
    }
    roster = ['tablet-01', 'tablet-02', 'tablet-03', 'tablet-04', 'tablet-05']
    devices, media_bytes = {}, {}
    for device, records in plan.items():
        binary = bytes(rng.randrange(256) for _ in range(173))
        root = f'odk/projects/survey/{device}'
        files = {root + '/forms/household_survey.xml': xform}
        entries = []
        for iid, _ in records:
            folder = f'{root}/instances/{iid.split(":")[1]}'
            path = folder + '/submission.xml'
            files[path] = xml(iid)
            entries.append({'xml_path': path, 'completion_status': 'complete', 'completion_provenance': PROVENANCE})
            for name in ('same.bin', 'a.bin', 'b.bin'):
                files[folder + '/' + name] = binary
            media_bytes[iid] = binary
        manifest = {'schema_version': 1, 'snapshot_id': f'device-snapshot-{device}', 'device_id': device, 'captured_at': AT,
                    'collector_version': 'synthetic-format-v1', 'device_provenance': PROVENANCE, 'synthetic': True,
                    'scope_complete': True, 'scope_provenance': PROVENANCE, 'instances': entries,
                    'form_definitions': [{'xml_path': root + '/forms/household_survey.xml'}]}
        files['device-manifest.json'] = json.dumps(manifest, sort_keys=True)
        devices[device] = pack(files)

    sf, versions, receipts, lists = {}, [], [], {}

    def receipt(name, file, version=None, attachment=None):
        rid = f'{SID}-{name}'
        receipts.append({'evidence_id': rid, 'source_snapshot_id': SID, 'source_file': file, 'archive_sha256': None, 'captured_at': AT,
                         'query_receipt_id': None, 'request_method': 'LOCAL', 'outcome': 'synthetic',
                         'request_scope': 'authored synthetic captured scope; not HTTP/SQL', 'response_sha256': hash_bytes(sf[file]),
                         'comparison': None, 'form_id': FORM, 'version_id': version, 'xml_path': None, 'attachment_filename': attachment})
        return rid

    expected = {}
    for device, records in plan.items():
        for iid, behaviour in records:
            key = iid.split(':')[1]
            if behaviour == 'never_arrived':
                expected[iid] = 'MISSING_SUBMISSION'
                continue
            path = f'raw/{key}/submission.xml'
            sf[path] = xml(iid, site='9999' if behaviour == 'edited' else '0017')
            receipt(key + '-xml', path, iid)
            missing = ('b.bin',) if behaviour == 'no_photo' else ()
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
            expected[iid] = {'no_photo': 'MISSING_ATTACHMENT', 'edited': 'CONTENT_CONFLICT'}.get(behaviour, 'PRESERVED')
    # The coordinator's spreadsheet export: one column per household, no repeat group columns.
    rows = ''.join(f'{iid},0017\n' for iid, _ in plan['tablet-01'])
    sf['household_survey.csv'] = ('version_id,village\n' + rows).encode()
    views = []
    for iid, _ in plan['tablet-01']:
        expected[iid] = 'EXPORT_VIEW_ONLY'
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
    run = {'schema_version': 1, 'run_id': 'sample-fleet-2026', 'mode': 'sample',
           'source_snapshot_ids': [f'device-snapshot-{d}' for d in plan] + [SID], 'expected_device_ids': roster,
           'roster_provenance': PROVENANCE, 'destination': {'connection_id': 'synthetic-offline-only', 'project_id': 7, 'form_id': FORM,
           'environment': 'dedicated_synthetic_test', 'mapping_provenance': PROVENANCE}}
    decisions = {'tablet-01': 'SAFE_TO_WIPE', 'tablet-02': 'RECOVER_FIRST', 'tablet-03': 'RECOVER_FIRST', 'tablet-04': 'HOLD', 'tablet-05': 'HOLD'}
    return {'run': run, 'devices': devices, 'server': server, 'snapshot': snapshot, 'expected': {'verdicts': expected, 'decisions': decisions}}


def write(root=None):
    root = Path(root or Path(__file__).resolve().parents[1] / 'fixtures/fleet')
    data = build_fleet()
    root.mkdir(parents=True, exist_ok=True)
    for name, key in [('run-manifest.json', 'run'), ('server-snapshot.json', 'snapshot'), ('expected.json', 'expected')]:
        (root / name).write_text(json.dumps(data[key], indent=2) + '\n', encoding='utf-8', newline='\n')
    for device, archive in data['devices'].items():
        (root / f'{device}.zip').write_bytes(archive)
    (root / 'server-payload.zip').write_bytes(data['server'])
    return root


if __name__ == '__main__':
    print('Wrote', write())
