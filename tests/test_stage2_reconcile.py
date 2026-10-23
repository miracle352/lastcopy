"""Breaks caught: count-only matching, hash deduplication, fake absence/history/view success."""
import importlib.util
import json
import socket
import pytest
from scripts.build_stage2_fixtures import example, pack, hash_bytes
from lastcopy.config import Settings
from lastcopy.inventory import read_archive, ImportRejected


def reconcile(data, cancel=lambda: False, settings=None):
    assert importlib.util.find_spec('lastcopy.reconcile'), 'Supplied-snapshot reconciliation is not implemented'
    from lastcopy.reconcile import reconcile as run
    from lastcopy.models import RunManifest
    return run(RunManifest.model_validate(data['run']), [data['device']],
               data['snapshot'], data['server'], settings or Settings({'SAMPLE_MODE': 'true'}), cancel=cancel)


@pytest.mark.parametrize('case', ['stranded', 'media', 'export', 'history', 'conflict'])
def test_authored_outcomes_are_independent_of_comparator(case, monkeypatch):
    monkeypatch.setattr(socket.socket, 'connect', lambda *a, **k: pytest.fail('Sample attempted network'))
    data = example(case)
    result = reconcile(data)
    assert {f.version_id: f.verdict for f in result.findings} == data['expected']['verdicts']
    assert sum(f.recovery_eligible for f in result.findings) == data['expected']['eligible_count']
    assert result.coverage.complete == (case in ['export', 'history', 'conflict'])
    assert all(f.original_retained_in_history for f in result.findings) == data['expected']['history']
    assert all(set(f.evidence_ids) <= {r.evidence_id for r in result.receipts} for f in result.findings)
    assert result.provenance == 'synthetic supplied snapshots; no external services or model calls'


def test_held_out_variant_changes_identity_paths_and_repeat_counts():
    result = reconcile(example('stranded', seed=9087, repeats=5))
    assert sorted(f.verdict for f in result.findings) == ['MISSING_SUBMISSION', 'MISSING_SUBMISSION', 'PRESERVED']


def test_same_bytes_under_different_names_require_each_slot():
    result = reconcile(example('media'))
    finding, = result.findings
    assert finding.verdict == 'MISSING_ATTACHMENT'
    assert finding.media_filenames == ['b.bin']
    # same.bin appears twice, a.bin has identical bytes; neither fills b.bin's slot.


@pytest.mark.parametrize('change', ['scope', 'connection', 'auth', 'history', 'device', 'missing_readback'])
def test_unavailable_evidence_cannot_become_missing_or_complete(change):
    data = example('history' if change == 'history' else 'control')
    s = data['snapshot']
    if change == 'scope': s['project_id'] = 8
    if change == 'connection': s['connection_id'] = 'another-central'
    if change == 'auth':
        receipt = next(r for r in s['receipts'] if r['evidence_id'] == s['listing_receipt_id'])
        receipt.update(outcome='failed', http_status=401)
    if change == 'history':
        s['versions'] = [v for v in s['versions'] if v['current']]
        s['history_complete'] = False
    if change == 'device': data['run']['expected_device_ids'].append('absent-device')
    if change == 'missing_readback': s['versions'][0]['media'][0]['readback_receipt_id'] = None
    result = reconcile(data)
    assert not result.coverage.complete
    assert not any(f.recovery_eligible for f in result.findings)
    if change != 'device': assert all(f.verdict == 'UNVERIFIABLE' for f in result.findings)


def test_cancellation_stops_comparison():
    from lastcopy.reconcile import RunCancelled
    with pytest.raises(RunCancelled): reconcile(example('stranded'), cancel=lambda: True)


def test_deadline_stops_before_a_false_completed_result():
    from lastcopy.reconcile import reconcile as run, RunDeadline
    from lastcopy.models import RunManifest
    data = example('control')
    ticks = iter([0, 301])
    with pytest.raises(RunDeadline):
        run(RunManifest.model_validate(data['run']), [data['device']], data['snapshot'], data['server'],
            Settings({'SAMPLE_MODE': 'true'}), clock=lambda: next(ticks))


def test_unrelated_broken_history_blocks_missing_record_candidate():
    data = example('stranded')
    # Keep the root listing consistent with the deliberately broken chain metadata.
    files = read_archive(data['server'], Settings({'SAMPLE_MODE': 'true'}))
    listing = json.loads(files['scope.json'])
    data['snapshot']['versions'][0]['logical_submission_id'] = 'invented-root'
    listing['versions'][0]['logical_submission_id'] = 'invented-root'
    files['scope.json'] = json.dumps(listing).encode()
    data['server'] = pack(files)
    data['snapshot']['archive_sha256'] = hash_bytes(data['server'])
    for r in data['snapshot']['receipts']:
        if r['source_file'] == 'scope.json': r['response_sha256'] = hash_bytes(files['scope.json'])
    result = reconcile(data)
    assert not any(f.recovery_eligible for f in result.findings)
    assert all(f.verdict == 'UNVERIFIABLE' for f in result.findings)


@pytest.mark.parametrize('change', ['completion_missing', 'form_missing', 'malformed', 'traversal'])
def test_untrusted_inputs_never_become_recovery(change):
    data = example('stranded')
    files = read_archive(data['device'], Settings({'SAMPLE_MODE': 'true'}))
    manifest = json.loads(files['device-manifest.json'])
    if change == 'completion_missing': del manifest['instances'][0]['completion_status']
    if change == 'form_missing': del files[manifest['form_definitions'][0]['xml_path']]
    if change == 'malformed': files[manifest['instances'][0]['xml_path']] = b'<broken>'
    if change == 'traversal': files['../outside'] = b'hostile'
    files['device-manifest.json'] = json.dumps(manifest)
    data['device'] = pack(files)
    with pytest.raises(ImportRejected): reconcile(data)


def test_unavailable_attachment_is_unknown_not_missing():
    data = example('control')
    r = next(r for r in data['snapshot']['receipts'] if r['evidence_id'] == data['snapshot']['versions'][0]['media'][0]['readback_receipt_id'])
    r.update(outcome='failed', http_status=403)
    result = reconcile(data)
    assert result.findings[0].verdict == 'UNVERIFIABLE'
    assert not result.coverage.complete and not result.findings[0].recovery_eligible


def test_changed_attachment_bytes_are_conflict_even_with_matching_declared_hashes():
    data = example('control')
    files = read_archive(data['server'], Settings({'SAMPLE_MODE': 'true'}))
    slot = data['snapshot']['versions'][0]['media'][0]
    files[slot['archive_path']] = b'different actual captured bytes'
    slot['sha256'] = hash_bytes(files[slot['archive_path']])
    for r in data['snapshot']['receipts']:
        if r['evidence_id'] == slot['readback_receipt_id']: r['response_sha256'] = slot['sha256']
    data['server'] = pack(files)
    data['snapshot']['archive_sha256'] = hash_bytes(data['server'])
    result = reconcile(data)
    assert result.findings[0].verdict == 'CONTENT_CONFLICT'
    assert not result.findings[0].recovery_eligible


def test_missing_device_scope_attestation_prevents_complete_coverage():
    data = example('control')
    files = read_archive(data['device'], Settings({'SAMPLE_MODE': 'true'}))
    manifest = json.loads(files['device-manifest.json'])
    manifest.pop('scope_complete', None)
    manifest.pop('scope_provenance', None)
    files['device-manifest.json'] = json.dumps(manifest)
    data['device'] = pack(files)
    result = reconcile(data)
    assert not result.coverage.complete
    assert not any(f.recovery_eligible for f in result.findings)


def test_tabular_omission_cannot_hide_raw_content_conflict():
    data = example('export')
    files = read_archive(data['server'], Settings({'SAMPLE_MODE': 'true'}))
    version = data['snapshot']['versions'][0]
    files[version['xml_path']] = files[version['xml_path']].replace(b'0017', b'9999')
    version['xml_sha256'] = hash_bytes(files[version['xml_path']])
    for r in data['snapshot']['receipts']:
        if r['source_file'] == version['xml_path']: r['response_sha256'] = version['xml_sha256']
    data['server'] = pack(files)
    data['snapshot']['archive_sha256'] = hash_bytes(data['server'])
    assert reconcile(data).findings[0].verdict == 'CONTENT_CONFLICT'


@pytest.mark.parametrize('setting,limit', [('MAX_RUN_UNCOMPRESSED_BYTES', '200'), ('MAX_RUN_RECEIPTS', '20')])
def test_aggregate_run_limits_stop_before_publishing_oversized_evidence(setting, limit):
    with pytest.raises(ImportRejected):
        reconcile(example('export', repeats=30), settings=Settings({'SAMPLE_MODE': 'true', setting: limit}))


def test_two_names_cannot_reuse_one_attachment_readback_receipt():
    data = example('control')
    slots = data['snapshot']['versions'][0]['media']
    slots[2]['archive_path'] = slots[1]['archive_path']
    slots[2]['readback_receipt_id'] = slots[1]['readback_receipt_id']
    result = reconcile(data)
    assert result.findings[0].verdict == 'UNVERIFIABLE'
    assert not result.coverage.complete


def test_failed_http_status_never_becomes_positive_synthetic_listing():
    data = example('stranded')
    next(r for r in data['snapshot']['receipts'] if r['evidence_id'] == data['snapshot']['listing_receipt_id'])['http_status'] = 401
    result = reconcile(data)
    assert all(f.verdict == 'UNVERIFIABLE' for f in result.findings)
    assert not any(f.recovery_eligible for f in result.findings)


def test_comparison_evidence_resolves_original_bytes_and_expanded_root():
    data = example('control')
    result = reconcile(data)
    sources = {data['run']['source_snapshot_ids'][0]: read_archive(data['device'], Settings({'SAMPLE_MODE': 'true'})),
               data['snapshot']['snapshot_id']: read_archive(data['server'], Settings({'SAMPLE_MODE': 'true'}))}
    for receipt in result.receipts:
        if receipt.source_file and receipt.response_sha256:
            assert hash_bytes(sources[receipt.source_snapshot_id][receipt.source_file]) == receipt.response_sha256
        if receipt.comparison and json.loads(receipt.comparison).get('checked'):
            assert receipt.xml_path == '/{urn:lastcopy:test}data[1]'
            assert receipt.repeat_indices == [1]


def test_two_stranded_submissions_across_distinct_device_snapshots():
    from lastcopy.models import RunManifest
    from lastcopy.reconcile import reconcile as run
    data = example('stranded')
    files = read_archive(data['device'], Settings({'SAMPLE_MODE': 'true'}))
    manifest = json.loads(files['device-manifest.json'])
    second = json.loads(json.dumps(manifest))
    second.update(snapshot_id='second-device-snapshot', device_id='second-device')
    second['instances'] = [manifest['instances'][2]]
    manifest['instances'] = manifest['instances'][:2]
    # Scope each ZIP to its explicitly selected records, retaining original bytes.
    def device(selected):
        prefixes = [entry['xml_path'].rsplit('/', 1)[0] + '/' for entry in selected['instances']]
        contents = {name: value for name, value in files.items()
                    if '/forms/' in name or any(name.startswith(prefix) for prefix in prefixes)}
        contents['device-manifest.json'] = json.dumps(selected)
        return pack(contents)
    data['run']['source_snapshot_ids'].append('second-device-snapshot')
    data['run']['expected_device_ids'].append('second-device')
    result = run(RunManifest.model_validate(data['run']), [device(manifest), device(second)],
                 data['snapshot'], data['server'], Settings({'SAMPLE_MODE': 'true'}))
    assert {f.version_id: f.verdict for f in result.findings} == {
        'uuid:41-a': 'PRESERVED', 'uuid:41-b': 'MISSING_SUBMISSION', 'uuid:41-c': 'MISSING_SUBMISSION'}
    assert sorted(result.coverage.supplied_devices) == ['device-41', 'second-device']
    assert sum(f.recovery_eligible for f in result.findings) == 2


def test_snapshot_label_cannot_replace_metadata_hash():
    data = example('control')
    files = read_archive(data['device'], Settings({'SAMPLE_MODE': 'true'}))
    manifest = json.loads(files['device-manifest.json'])
    manifest['snapshot_id'] = 'server-envelope'
    files['device-manifest.json'] = json.dumps(manifest)
    data['device'] = pack(files)
    data['run']['source_snapshot_ids'][0] = 'server-envelope'
    result = reconcile(data)
    assert len(result.input_hashes) == 3
    assert result.input_hashes['snapshot:server-envelope'] == hash_bytes(data['device'])
