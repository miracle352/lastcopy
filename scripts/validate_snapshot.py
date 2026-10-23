"""Validate a v1 raw snapshot envelope and immutable payload, not preservation."""
import argparse
import json
import zipfile
from pathlib import Path
from lastcopy.config import ROOT, Settings
from lastcopy.inventory import digest, parse_xml, ImportRejected, read_archive
from lastcopy.models import SourceSnapshot, safe_path


def validate(manifest_path, archive_path):
    snapshot = SourceSnapshot.model_validate_json(manifest_path.read_bytes())
    if snapshot.kind != "central_raw":
        raise ImportRejected("Expected central_raw snapshot")
    payload = archive_path.read_bytes()
    settings = Settings.load()
    if len(payload) > settings.limit("MAX_UPLOAD_BYTES") or digest(payload) != snapshot.archive_sha256:
        raise ImportRejected("Snapshot archive limit or SHA-256 mismatch")
    files = read_archive(payload, settings)
    evidence = {receipt.evidence_id: receipt for receipt in snapshot.receipts}
    if len(evidence) != len(snapshot.receipts) or set(snapshot.receipt_ids) != set(evidence):
        raise ImportRejected("Snapshot receipt IDs must resolve uniquely")
    for receipt in snapshot.receipts:
        if receipt.source_snapshot_id != snapshot.snapshot_id:
            raise ImportRejected("Receipt outside snapshot scope")
        if receipt.source_file and receipt.response_sha256:
            if receipt.source_file not in files or digest(files[receipt.source_file]) != receipt.response_sha256:
                raise ImportRejected("Receipt file/hash mismatch")
    for version in snapshot.versions:
        if version.snapshot_id != snapshot.snapshot_id or version.form_id not in snapshot.form_ids:
            raise ImportRejected("Version outside snapshot scope")
        xml = files.get(version.xml_path)
        if xml is None or digest(xml) != version.xml_sha256:
            raise ImportRejected("Snapshot XML missing or hash mismatch")
        root = parse_xml(xml, settings)
        if root.attrib.get("id") != version.form_id or root.attrib.get("version") != version.form_version or root.findtext("./{*}meta/{*}instanceID") != version.version_id:
            raise ImportRejected("Snapshot XML identity mismatch")
        for media in version.media:
            if media.version_id != version.version_id or media.readback_receipt_id not in evidence:
                raise ImportRejected("Attachment identity/receipt mismatch")
            data = files.get(media.archive_path)
            if media.sha256 is None:
                receipt = evidence[media.readback_receipt_id]
                if data is not None or receipt.outcome not in ("failed", "partial") or snapshot.scope_complete or not snapshot.limitations:
                    raise ImportRejected("Missing media requires failed/partial receipt and explicit incomplete scope")
                continue
            if data is None or digest(data) != media.sha256 or evidence[media.readback_receipt_id].response_sha256 != media.sha256:
                raise ImportRejected("Snapshot attachment bytes/receipt mismatch")
    return {"snapshot_id": snapshot.snapshot_id, "synthetic": snapshot.synthetic, "scope_complete": snapshot.scope_complete, "versions": len(snapshot.versions), "receipts": len(evidence), "preservation_checked": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.manifest, args.archive), indent=2))
