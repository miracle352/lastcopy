"""Validate immutable supplied raw captures. Receipts attest captured bytes, not publisher truth."""
import json
from .inventory import read_archive, digest, parse_xml, ImportRejected
from .models import SourceSnapshot


def load_snapshot(envelope, payload, settings):
    if len(envelope) > 2097152:
        raise ImportRejected('Snapshot envelope exceeds 2 MiB')
    try:
        snapshot = SourceSnapshot.model_validate_json(envelope)
    except Exception:
        raise ImportRejected('Invalid raw snapshot envelope') from None
    if snapshot.kind != 'central_raw' or digest(payload) != snapshot.archive_sha256:
        raise ImportRejected('Raw snapshot kind or payload hash mismatch')
    files = read_archive(payload, settings)
    evidence = {r.evidence_id: r for r in snapshot.receipts}
    if len(evidence) != len(snapshot.receipts) or set(snapshot.receipt_ids) != set(evidence):
        raise ImportRejected('Snapshot receipt IDs must resolve uniquely')
    if len(snapshot.versions) > 1000 or len(evidence) > 10000:
        raise ImportRejected('Snapshot exceeds version/receipt limits')
    seen = set()
    for receipt in snapshot.receipts:
        if receipt.source_snapshot_id != snapshot.snapshot_id or receipt.archive_sha256 not in (None, snapshot.archive_sha256):
            raise ImportRejected('Receipt outside snapshot scope')
        if receipt.source_file and receipt.response_sha256:
            if receipt.source_file not in files or digest(files[receipt.source_file]) != receipt.response_sha256:
                raise ImportRejected('Receipt file/hash mismatch')
    for v in snapshot.versions:
        key = (v.form_id, v.version_id)
        if key in seen or v.snapshot_id != snapshot.snapshot_id or v.form_id not in snapshot.form_ids:
            raise ImportRejected('Duplicate or out-of-scope server version')
        seen.add(key)
        xml = files.get(v.xml_path)
        if xml is None or digest(xml) != v.xml_sha256:
            raise ImportRejected('Snapshot XML missing or hash mismatch')
        root = parse_xml(xml, settings)
        ids = [n.text for n in root.findall('./{*}meta/{*}instanceID')]
        deprecated = [n.text for n in root.findall('./{*}meta/{*}deprecatedID')]
        if (root.get('id') != v.form_id or root.get('version') != v.form_version or ids != [v.version_id]
                or deprecated != ([v.deprecated_id] if v.deprecated_id else [])):
            raise ImportRejected('Snapshot XML identity mismatch')
        slots = set()
        for m in v.media:
            if m.version_id != v.version_id:
                raise ImportRejected('Attachment outside version scope')
            if m.filename in slots:
                raise ImportRejected('Duplicate server attachment slot')
            slots.add(m.filename)
            if m.sha256 and (m.archive_path not in files or digest(files[m.archive_path]) != m.sha256):
                raise ImportRejected('Snapshot attachment byte/hash mismatch')
    return snapshot, files, evidence


def positive(receipt, snapshot, *, file=None, version=None, form=None):
    if receipt is None or receipt.captured_at == 'unknown':
        return False
    if receipt.source_snapshot_id != snapshot.snapshot_id:
        return False
    if version is not None and receipt.version_id != version:
        return False
    if form is not None and receipt.form_id != form:
        return False
    if file is not None and (receipt.source_file != file or receipt.response_sha256 is None):
        return False
    if snapshot.synthetic:
        return receipt.request_method == 'LOCAL' and receipt.outcome == 'synthetic' and receipt.http_status is None
    if receipt.request_method == 'LOCAL' and receipt.outcome == 'success' and receipt.query_receipt_id:
        # Honest normalized indexes are linked to actual captured authenticated
        # native GETs. They do not pretend their derived JSON was an HTTP response.
        parents = [r for r in snapshot.receipts if r.evidence_id == receipt.query_receipt_id]
        return (receipt.request_scope == 'normalized authenticated Central capture; see native receipt'
                and len(parents) == 1 and parents[0].request_method == 'GET'
                and parents[0].outcome == 'success' and parents[0].http_status == 200
                and parents[0].source_snapshot_id == snapshot.snapshot_id
                and parents[0].source_file is not None and parents[0].response_sha256 is not None
                and (version is None or parents[0].version_id == version))
    return receipt.request_method == 'GET' and receipt.outcome == 'success' and receipt.http_status is not None and 200 <= receipt.http_status < 300


def scope_listing(snapshot, files, evidence):
    receipt = evidence.get(snapshot.listing_receipt_id)
    if not positive(receipt, snapshot) or not receipt.source_file or not receipt.response_sha256:
        return None
    try:
        doc = json.loads(files[receipt.source_file])
        fields = ['form_id', 'form_version', 'logical_submission_id', 'version_id', 'deprecated_id', 'current']
        expected = [{k: getattr(v, k) for k in fields} for v in snapshot.versions]
        if (doc['connection_id'] != snapshot.connection_id or doc['project_id'] != snapshot.project_id or doc['form_ids'] != snapshot.form_ids
                or doc['history_complete'] != snapshot.history_complete or doc['versions'] != expected):
            return None
        return doc
    except (KeyError, ValueError, TypeError):
        return None
