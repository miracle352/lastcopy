"""Deterministic supplied-evidence reconciliation. No network, models or writes."""
import csv
import io
import json
import time
from .inventory import digest, inventory, read_archive, ImportRejected
from .models import RunManifest, EvidenceReceipt, Finding, Coverage, ReconciliationReport
from .scope import validate_run_import
from .snapshots import load_snapshot, positive, scope_listing
from .xml_compare import compare_xml, xml_facts


class RunCancelled(Exception):
    pass


class RunDeadline(Exception):
    pass


def reconcile(run: RunManifest, devices, envelope, payload, settings, *, cancel=lambda: False,
              event=lambda kind, details: None, clock=time.monotonic):
    start = clock()

    def checkpoint():
        if cancel():
            raise RunCancelled('Run cancelled')
        if clock() - start >= min(run.max_seconds, settings.limit('MAX_RUN_SECONDS')):
            raise RunDeadline('Run exceeded wall-time limit')

    checkpoint()
    if not 1 <= len(devices) <= 8 or sum(map(len, devices)) + len(payload) > 67108864:
        raise ImportRejected('Run exceeds input count/64 MiB limit')
    if settings.sample and run.mode != 'sample':
        raise ImportRejected('SAMPLE_MODE requires a sample manifest; no implicit mode fallback')
    envelope = envelope if isinstance(envelope, bytes) else json.dumps(envelope, sort_keys=True).encode()
    server, server_files, evidence = load_snapshot(envelope, payload, settings)
    sources = []
    uncompressed = sum(map(len, server_files.values()))
    for data in devices:
        checkpoint()
        files = read_archive(data, settings)
        uncompressed += sum(map(len, files.values()))
        if uncompressed > settings.limit('MAX_RUN_UNCOMPRESSED_BYTES'):
            raise ImportRejected('Run exceeds aggregate uncompressed byte limit')
        source = inventory(data, settings)
        sources.append((source, files))
    if run.mode == 'sample' and (not server.synthetic or any(not s.manifest.synthetic for s, _ in sources)):
        raise ImportRejected('Sample accepts only explicitly synthetic supplied snapshots')
    snapshots = [s.manifest.snapshot_id for s, _ in sources] + [server.snapshot_id]
    if len(set(snapshots)) != len(snapshots):
        raise ImportRejected('Duplicate input snapshot identity')
    supplied = [s.manifest.device_id for s, _ in sources]
    if len(set(supplied)) != len(supplied):
        raise ImportRejected('More than one snapshot for the same device is ambiguous')
    missing_devices = sorted(set(run.expected_device_ids) - set(supplied))
    limitations = []
    mapping = []
    if set(snapshots) != set(run.source_snapshot_ids):
        mapping.append('Supplied snapshots do not match explicit run scope')
    for source, _ in sources:
        mapping.extend(validate_run_import(run, source))
        if not source.manifest.scope_complete or source.manifest.scope_provenance is None or source.manifest.captured_at == 'unknown':
            limitations.append('Device source scope/capture completeness is not established')
    if server.connection_id != run.destination.connection_id or server.project_id != run.destination.project_id or server.form_ids != [run.destination.form_id]:
        mapping.append('Server destination project/form scope mismatch')
    listing = scope_listing(server, server_files, evidence)
    if listing is None:
        mapping.append('Successful scoped version listing unavailable or inconsistent')
    limitations.extend(mapping)
    if missing_devices:
        limitations.append('Expected device snapshots absent: ' + ', '.join(missing_devices))
    if not server.scope_complete or not server.history_complete or server.limitations:
        limitations.append('Server scope/history capture is incomplete or limited')
    limitations.extend(server.limitations)
    if server.captured_at == 'unknown':
        mapping.append('Server capture time unknown')
        limitations.append('Server capture time unknown')
    receipts = list(server.receipts)
    if len(receipts) > settings.limit('MAX_RUN_RECEIPTS'):
        raise ImportRejected('Run receipt limit exceeded')
    findings = []
    versions = {v.version_id: v for v in server.versions if v.form_id == run.destination.form_id}
    source_ids = {}
    for source, _ in sources:
        for v in source.versions:
            source_ids.setdefault((v.form_id, v.version_id), []).append(v.xml_sha256)

    def chain(v):
        seen = set()
        while v.deprecated_id:
            if v.version_id in seen or v.deprecated_id not in versions:
                return None
            seen.add(v.version_id)
            previous = versions[v.deprecated_id]
            if previous.form_id != v.form_id:
                return None
            v = previous
        return v.version_id

    # A complete listing is useful for absence only if its claimed histories are
    # internally consistent, including records unrelated to the source under test.
    for candidate in versions.values():
        root_id = chain(candidate)
        currents = [item for item in versions.values() if item.logical_submission_id == root_id and item.current is True]
        if root_id is None or candidate.logical_submission_id != root_id or candidate.current is None or len(currents) != 1:
            mapping.append('Captured version histories are ambiguous or incomplete')
            break
    limitations.extend(mapping)

    def add_receipt(source, v, path, comparison, indices=None, source_file=None, response_hash=None):
        if len(receipts) >= settings.limit('MAX_RUN_RECEIPTS'):
            raise ImportRejected('Run receipt limit exceeded')
        record = EvidenceReceipt(evidence_id=f'comparison-{len(receipts) + 1}',
            source_snapshot_id=source.manifest.snapshot_id, source_file=source_file or v.xml_path,
            archive_sha256=source.archive_sha256, captured_at=source.manifest.captured_at,
            query_receipt_id=None, request_method='LOCAL', outcome='synthetic' if source.manifest.synthetic else 'success',
            request_scope='deterministic supplied-snapshot comparison; not a network query',
            response_sha256=v.xml_sha256 if source_file is None else response_hash, comparison=json.dumps(comparison, ensure_ascii=False, sort_keys=True),
            form_id=v.form_id, version_id=v.version_id, xml_path=path, repeat_indices=indices or [])
        receipts.append(record)
        return record.evidence_id

    for source, files in sources:
        for v in source.versions:
            checkpoint()
            if len(findings) >= 1000:
                raise ImportRejected('Run exceeds 1000 source-version limit')
            source_facts = xml_facts(files[v.xml_path], settings)
            ids = [add_receipt(source, v, source_facts[0]['path'], {'source_xml_sha256': v.xml_sha256, 'checked': True}, [1])]
            selected = versions.get(v.version_id)
            current = None
            retained = False
            media_missing, media_conflict, unknown = [], [], []
            action, verdict, code = 'manual', 'UNVERIFIABLE', 'EVIDENCE_UNAVAILABLE'
            summary = 'Could not verify the supplied record.'
            scope = None
            eligible = False
            problems = list(mapping) + list(v.limitations)
            if len(source_ids[(v.form_id, v.version_id)]) > 1:
                problems.append('Duplicate source version across supplied snapshots requires explicit selection')
            if v.completion_status != 'complete':
                problems.append('Completion not explicitly established')
            if v.deprecated_id:
                # No guessed logical root when the device export lacks its full edit chain.
                problems.append('Device edit chain not resolved in this first-release importer')
            if not problems and selected is None:
                if listing and server.scope_complete and server.history_complete and not server.limitations:
                    verdict, code, action = 'MISSING_SUBMISSION', 'VERSION_ABSENT_IN_CAPTURE', 'review_create'
                    summary = 'Version absent within the complete supplied project/form/history capture.'
                    scope = f'snapshot:{server.snapshot_id};project:{server.project_id};form:{v.form_id};captured:{server.captured_at}'
                    # A different known edit of the same logical record is never a create candidate.
                    related = any(s.logical_submission_id == v.version_id or s.deprecated_id == v.version_id for s in versions.values())
                    if related:
                        verdict, code, action = 'UNVERIFIABLE', 'HISTORY_UNAVAILABLE', 'manual'
                        summary = 'Related server edit exists but the required original readback is absent.'
                    ids.append(server.listing_receipt_id)
                else:
                    problems.append('Absence cannot be established from incomplete listing/history')
            elif not problems:
                xml_receipts = [r for r in server.receipts if positive(r, server, file=selected.xml_path, version=selected.version_id, form=selected.form_id)
                                and r.response_sha256 == selected.xml_sha256]
                logical = chain(selected)
                currents = [s for s in versions.values() if s.logical_submission_id == logical and s.current]
                if not xml_receipts or logical is None or selected.logical_submission_id != logical or len(currents) != 1:
                    problems.append('Scoped XML readback or unambiguous version history unavailable')
                else:
                    ids.append(xml_receipts[0].evidence_id)
                    current = currents[0].version_id
                    if chain(currents[0]) != logical:
                        problems.append('Current edit chain is incomplete or inconsistent')
                    retained = selected.current is False and current != selected.version_id
                    if not selected.current and not retained:
                        problems.append('Server current-version metadata unavailable')
                if not problems:
                    comparison = compare_xml(files[v.xml_path], server_files[selected.xml_path], settings)
                    ids.append(add_receipt(source, v, None, {k: value for k, value in comparison.items() if k != 'differences'}))
                    for difference in comparison['differences']:
                        ids.append(add_receipt(source, v, difference['path'], difference, difference['indices']))
                    verdict, code, action = 'PRESERVED', 'RAW_VERSION_PRESERVED', 'none'
                    summary = 'Original version XML and every referenced attachment slot match supplied readback bytes.'
                    if not comparison['equal']:
                        verdict, code, action = 'CONTENT_CONFLICT', 'XML_CONTENT_DIFFERS', 'manual'
                        summary = 'Same-version XML content differs; no overwrite is permitted.'
                    attachment_receipt = evidence.get(server.attachment_listing_receipt_ids.get(selected.version_id))
                    attachment_names = None
                    if positive(attachment_receipt, server, version=selected.version_id, form=selected.form_id) and attachment_receipt.source_file and attachment_receipt.response_sha256:
                        try:
                            doc = json.loads(server_files[attachment_receipt.source_file])
                            if doc['version_id'] == selected.version_id and isinstance(doc['filenames'], list) and all(isinstance(n, str) for n in doc['filenames']):
                                attachment_names = doc['filenames']
                                ids.append(attachment_receipt.evidence_id)
                        except (KeyError, ValueError, TypeError):
                            pass
                    slots = {m.filename: m for m in selected.media}
                    for m in v.media:
                        checkpoint()
                        slot = slots.get(m.filename)
                        r = evidence.get(slot.readback_receipt_id) if slot else None
                        detail = {'filename': m.filename, 'source_sha256': m.sha256, 'server_sha256': None,
                                  'readback_receipt_id': r.evidence_id if r else None}
                        if m.sha256 is None:
                            unknown.append(m.filename)
                        elif slot and slot.sha256 and positive(r, server, file=slot.archive_path, version=selected.version_id, form=selected.form_id) and r.response_sha256 == slot.sha256 and r.attachment_filename == m.filename:
                            # Do not trust declared hashes alone: independently digest the untouched readback bytes.
                            actual = digest(server_files[slot.archive_path])
                            detail['server_sha256'] = actual
                            ids.append(r.evidence_id)
                            if actual != digest(files[m.archive_path]):
                                media_conflict.append(m.filename)
                        elif attachment_names is not None and m.filename not in attachment_names and slot is None:
                            media_missing.append(m.filename)
                        else:
                            unknown.append(m.filename)
                        ids.append(add_receipt(source, v, m.xml_path, detail, m.occurrence_indices, m.archive_path, m.sha256))
                    if unknown:
                        limitations.append('Required attachment readback unavailable')
                    if comparison['equal']:
                        if media_conflict:
                            verdict, code, action = 'CONTENT_CONFLICT', 'ATTACHMENT_BYTES_DIFFER', 'manual'
                            summary = 'Referenced attachment bytes differ; no overwrite is permitted.'
                        elif unknown:
                            verdict, code, action = 'UNVERIFIABLE', 'ATTACHMENT_READBACK_UNAVAILABLE', 'manual'
                            summary = 'Required attachment slot readback is unavailable; existence flags are insufficient.'
                        elif media_missing:
                            verdict, code, action = 'MISSING_ATTACHMENT', 'ATTACHMENT_ABSENT_IN_CAPTURE', 'review_media'
                            summary = 'Successful scoped attachment listing omits the referenced filename slot.'
                            scope = f'snapshot:{server.snapshot_id};version:{selected.version_id};attachment-list'
                    if verdict == 'PRESERVED':
                        for view in server.tabular_views:
                            if view.version_id != v.version_id:
                                continue
                            vr = evidence.get(view.receipt_id)
                            if not positive(vr, server, file=view.archive_path, version=v.version_id, form=v.form_id):
                                limitations.append('Selected tabular view readback unavailable')
                                continue
                            try:
                                table = csv.DictReader(io.StringIO(server_files[view.archive_path].decode('utf-8')))
                                if len(table.fieldnames or []) != len(set(table.fieldnames or [])):
                                    raise ValueError()
                                rows = [row for row in table if row.get('version_id') == v.version_id]
                                if len(rows) != 1 or any(c not in rows[0] for c in view.columns):
                                    raise ValueError()
                                facts = source_facts
                                represented = set(view.columns.values())
                                omitted = [f for f in facts if f['text'] is not None and f['path'] not in represented]
                                if omitted:
                                    verdict, code, action = 'EXPORT_VIEW_ONLY', 'TABULAR_FIELDS_OMITTED', 'export_guidance'
                                    summary = 'Raw XML and attachment slots preserve the source; the selected tabular view omits fields/repeats.'
                                    ids.append(vr.evidence_id)
                                    for fact in omitted[:64]:
                                        ids.append(add_receipt(source, v, fact['path'], {'tabular_omitted': True, 'raw_preserved': True}, fact['indices']))
                            except ImportRejected:
                                raise
                            except (KeyError, UnicodeError, ValueError, csv.Error):
                                limitations.append('Tabular view cannot be interpreted by the supported wide-CSV mapping')
            if problems:
                verdict, code, action, retained = 'UNVERIFIABLE', 'SCOPE_OR_SOURCE_UNCERTAIN', 'manual', False
                summary = '; '.join(sorted(set(problems)))
                limitations.extend(problems)
            eligible = (verdict in ('MISSING_SUBMISSION', 'MISSING_ATTACHMENT') and not retained and not missing_devices and not mapping
                        and source.manifest.scope_complete and source.manifest.scope_provenance is not None
                        and source.manifest.captured_at != 'unknown' and server.scope_complete and server.history_complete
                        and not server.limitations)
            if verdict in ('MISSING_SUBMISSION', 'MISSING_ATTACHMENT'):
                limitations.append('Required record or attachment readback absent')
            if not eligible and action in ('review_create', 'review_media'):
                action = 'manual'
            findings.append(Finding(finding_id=f'finding-{len(findings) + 1}', verdict=verdict,
                preservation='preserved' if verdict in ('PRESERVED', 'EXPORT_VIEW_ONLY') else 'unknown' if verdict == 'UNVERIFIABLE' else 'not_preserved',
                code=code, summary=summary, snapshot_id=source.manifest.snapshot_id, form_id=v.form_id,
                logical_submission_id=v.logical_submission_id, version_id=v.version_id, evidence_ids=sorted(set(ids)),
                absence_scope=scope, original_retained_in_history=retained, current_version_id=current,
                media_filenames=sorted(set(media_missing + media_conflict + unknown)), recovery_eligible=eligible, next_action=action))
            event('version_compared', {'finding_id': findings[-1].finding_id, 'verdict': verdict})
    checkpoint()
    # Receipt IDs are immutable identities across source/capture namespaces.
    if len({r.evidence_id for r in receipts}) != len(receipts) or len(receipts) > 20000:
        raise ImportRejected('Receipt identity collision or run receipt limit exceeded')
    complete = not limitations and not missing_devices and all(f.verdict != 'UNVERIFIABLE' for f in findings)
    unresolved_scope = any(issue != 'Required record or attachment readback absent' for issue in limitations)
    outcome = ('unresolved' if unresolved_scope or any(f.preservation == 'unknown' for f in findings)
               else 'with_gaps' if any(f.preservation == 'not_preserved' for f in findings) else 'verified')
    hashes = {'snapshot:' + s.manifest.snapshot_id: s.archive_sha256 for s, _ in sources}
    hashes['snapshot:' + server.snapshot_id] = server.archive_sha256
    hashes['capture:server-envelope'] = digest(envelope)
    return ReconciliationReport(run_id=run.run_id, mode=run.mode,
        provenance='synthetic supplied snapshots; no external services or model calls' if run.mode == 'sample' else 'supplied captured snapshots; not fresh live evidence; no model calls',
        preservation_outcome=outcome,
        coverage=Coverage(complete=complete, expected_devices=run.expected_device_ids, supplied_devices=sorted(supplied),
                          missing_devices=missing_devices, limitations=sorted(set(limitations)), checked_versions=len(findings)),
        findings=findings, receipts=receipts, input_hashes=hashes)
