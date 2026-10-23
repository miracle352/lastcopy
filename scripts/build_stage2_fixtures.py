"""Authored synthetic examples. Expected verdicts are literals, never comparator output."""
import csv
import io
import json
import random
import hashlib
import zipfile
from pathlib import Path

AT = '2026-10-23T10:00:00Z'
PROVENANCE = {'origin': 'coordinator_attestation', 'reference': 'authored-synthetic-stage2'}


def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def pack(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 23, 10, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data.encode() if isinstance(data, str) else data)
    return buffer.getvalue()


def example(case, seed=41, repeats=2):
    """Returns input bytes plus hand-authored outcomes. Tests may change capture evidence."""
    form = 'inspection' if seed == 41 else f'survey_{seed}'
    root = 'projects/field-a' if seed == 41 else f'outer/project-{seed}/native'
    rng = random.Random(seed)
    binary = bytes(rng.randrange(256) for _ in range(127))
    ids = {key: f'uuid:{seed}-{key}' for key in ['a', 'b', 'c', 'other', 'new']}
    readings = ''.join(f'<reading><value>{n:02}</value></reading>' for n in range(3, 3 + repeats))

    def xml(key, value='0017', deprecated=None):
        return (f'<data xmlns="urn:lastcopy:test" id="{form}" version="1"><site>{value}</site>'
                + readings + '<photo>same.bin</photo><photo>same.bin</photo><twin>a.bin</twin><twin>b.bin</twin>'
                + f'<meta><instanceID>{ids[key]}</instanceID>'
                + (f'<deprecatedID>{ids[deprecated]}</deprecatedID>' if deprecated else '') + '</meta></data>').encode()

    xform = (f'<h:html xmlns:h="http://www.w3.org/1999/xhtml" xmlns="http://www.w3.org/2002/xforms">'
             f'<h:head><model><instance><data xmlns="urn:lastcopy:test" id="{form}" version="1"/></instance>'
             '<bind nodeset="/data/photo" type="binary"/><bind nodeset="/data/twin" type="binary"/>'
             '</model></h:head></h:html>').encode()
    source_keys = ['a', 'b', 'c'] if case == 'stranded' else ['a']
    device_files = {root + '/forms/original.xml': xform}
    entries = []
    for key in source_keys:
        folder = root + f'/instances/{key}-native'
        path = folder + f'/answers-{key}.xml'
        entries.append({'xml_path': path, 'completion_status': 'complete', 'completion_provenance': PROVENANCE})
        device_files[path] = xml(key)
        for name in ['same.bin', 'a.bin', 'b.bin']:
            device_files[folder + '/' + name] = binary
    device_id = f'device-{seed}'
    device_manifest = {'schema_version': 1, 'snapshot_id': f'device-snapshot-{seed}', 'device_id': device_id,
        'captured_at': AT, 'collector_version': 'synthetic-format-v1', 'device_provenance': PROVENANCE,
        'synthetic': True, 'scope_complete': True, 'scope_provenance': PROVENANCE,
        'instances': entries, 'form_definitions': [{'xml_path': root + '/forms/original.xml'}]}
    device_files['device-manifest.json'] = json.dumps(device_manifest, sort_keys=True)
    sf, versions, receipts = {}, [], []
    sid = f'server-snapshot-{seed}'

    def receipt(name, file, version=None, attachment=None):
        rid = f'{sid}-{name}'
        receipts.append({'evidence_id': rid, 'source_snapshot_id': sid, 'source_file': file,
            'archive_sha256': None, 'captured_at': AT, 'query_receipt_id': None, 'request_method': 'LOCAL',
            'outcome': 'synthetic', 'request_scope': 'authored synthetic captured scope; not HTTP/SQL',
            'response_sha256': hash_bytes(sf[file]), 'comparison': None, 'form_id': form,
            'version_id': version, 'xml_path': None, 'attachment_filename': attachment})
        return rid

    def server(key, *, value='0017', deprecated=None, current=True, missing=()):
        version_id = ids[key]
        path = f'raw/{key}/original.xml'
        sf[path] = xml(key, value, deprecated)
        receipt(key + '-xml', path, version_id)
        media = []
        names = ['same.bin', 'a.bin', 'b.bin']
        listing = f'raw/{key}/attachments.json'
        sf[listing] = json.dumps({'version_id': version_id, 'filenames': [n for n in names if n not in missing]}).encode()
        lr = receipt(key + '-attachments', listing, version_id)
        for name in names:
            if name in missing:
                continue
            mp = f'raw/{key}/media/{name}'
            sf[mp] = binary
            mr = receipt(key + '-' + name, mp, version_id, name)
            media.append({'version_id': version_id, 'filename': name, 'xml_path': '/media', 'occurrence_indices': [],
                          'archive_path': mp, 'sha256': hash_bytes(binary), 'readback_receipt_id': mr})
        versions.append({'snapshot_id': sid, 'form_id': form, 'form_version': '1', 'logical_submission_id': ids['a'] if deprecated else version_id,
                         'version_id': version_id, 'deprecated_id': ids[deprecated] if deprecated else None,
                         'xml_path': path, 'xml_sha256': hash_bytes(sf[path]), 'completion_status': 'complete',
                         'current': current, 'media': media, 'limitations': []})
        return lr

    attachment_lists = {}
    views = []
    if case == 'stranded':
        attachment_lists[ids['a']] = server('a')
        attachment_lists[ids['other']] = server('other')
        expected = {ids['a']: 'PRESERVED', ids['b']: 'MISSING_SUBMISSION', ids['c']: 'MISSING_SUBMISSION'}
    elif case == 'media':
        attachment_lists[ids['a']] = server('a', missing=('b.bin',))
        expected = {ids['a']: 'MISSING_ATTACHMENT'}
    elif case == 'export':
        attachment_lists[ids['a']] = server('a')
        sf['view.csv'] = f'version_id,site\n{ids["a"]},0017\n'.encode()
        vr = receipt('tabular', 'view.csv', ids['a'])
        views = [{'version_id': ids['a'], 'archive_path': 'view.csv', 'receipt_id': vr,
                  'columns': {'site': '/{urn:lastcopy:test}data[1]/{urn:lastcopy:test}site[1]'}}]
        expected = {ids['a']: 'EXPORT_VIEW_ONLY'}
    elif case == 'history':
        attachment_lists[ids['a']] = server('a', current=False)
        attachment_lists[ids['new']] = server('new', value='intentional edit', deprecated='a')
        expected = {ids['a']: 'PRESERVED'}
    elif case == 'conflict':
        attachment_lists[ids['a']] = server('a', value='9999')
        expected = {ids['a']: 'CONTENT_CONFLICT'}
    else:
        attachment_lists[ids['a']] = server('a')
        expected = {ids['a']: 'PRESERVED'}
    sf['scope.json'] = json.dumps({'connection_id': 'synthetic-offline-only', 'project_id': 7, 'form_ids': [form], 'history_complete': True,
        'versions': [{k: v[k] for k in ['form_id', 'form_version', 'logical_submission_id', 'version_id', 'deprecated_id', 'current']} for v in versions]}, sort_keys=True).encode()
    listing_id = receipt('scope', 'scope.json')
    server_bytes = pack(sf)
    snapshot = {'schema_version': 1, 'snapshot_id': sid, 'kind': 'central_raw', 'archive_sha256': hash_bytes(server_bytes),
        'captured_at': AT, 'synthetic': True, 'scope_complete': True, 'connection_id': 'synthetic-offline-only', 'project_id': 7, 'form_ids': [form],
        'limitations': [], 'receipt_ids': [r['evidence_id'] for r in receipts], 'receipts': receipts,
        'versions': versions, 'listing_receipt_id': listing_id, 'history_complete': True,
        'attachment_listing_receipt_ids': attachment_lists, 'tabular_views': views}
    run = {'schema_version': 1, 'run_id': f'sample-{case}-{seed}', 'mode': 'sample',
        'source_snapshot_ids': [device_manifest['snapshot_id'], sid], 'expected_device_ids': [device_id],
        'roster_provenance': PROVENANCE, 'destination': {'connection_id': 'synthetic-offline-only',
        'project_id': 7, 'form_id': form, 'environment': 'dedicated_synthetic_test', 'mapping_provenance': PROVENANCE}}
    return {'run': run, 'device': pack(device_files), 'server': server_bytes, 'snapshot': snapshot,
            'expected': {'verdicts': expected, 'history': case == 'history', 'missing_submission_count': 2 if case == 'stranded' else 0,
                         'eligible_count': 2 if case == 'stranded' else 1 if case == 'media' else 0},
            'seed': seed, 'repeats': repeats}


def build():
    root = Path(__file__).resolve().parents[1] / 'fixtures/stage2'
    for name in ['stranded', 'media', 'export', 'history']:
        data = example(name)
        folder = root / name
        folder.mkdir(parents=True, exist_ok=True)
        for key, filename in [('run', 'run-manifest.json'), ('snapshot', 'server-snapshot.json'), ('expected', 'expected.json')]:
            (folder / filename).write_text(json.dumps(data[key], indent=2) + '\n')
        (folder / 'device.zip').write_bytes(data['device'])
        (folder / 'server-payload.zip').write_bytes(data['server'])
    print('Built four deterministic synthetic Stage 2 sample packs; seed 41; literal expected verdicts')


if __name__ == '__main__':
    build()
