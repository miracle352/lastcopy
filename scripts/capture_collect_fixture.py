"""Package the dedicated synthetic Collect capture without changing its bytes.

This deliberately narrow Stage 1 fixture builder is not a general device exporter.
Input is the already copied, stopped-app project from the documented emulator run.
Completion comes from Collect's read-only database, never from XML presence.
"""
import hashlib
import json
import sqlite3
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from lastcopy.config import ROOT, Settings
from lastcopy.inventory import inventory, parse_xml


def sha(data):
    return hashlib.sha256(data).hexdigest()


def capture():
    source = ROOT / "private/android/collect-export-v2"
    target = ROOT / "fixtures/collect-v2026.3.5"
    if target.exists():
        raise SystemExit("Refusing to overwrite an existing captured fixture")
    db = source / "metadata/instances.db"
    with sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = [dict(row) for row in connection.execute("SELECT * FROM instances WHERE jrFormId = 'lastcopy_collect_smoke_v2'")]
    if len(rows) != 1 or rows[0]["status"] != "complete":
        raise SystemExit("Expected the single genuinely finalized synthetic record")
    row = rows[0]
    relative = Path(row["instanceFilePath"])
    if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".xml":
        raise SystemExit("Unsafe native instance path")
    native_xml = source / "instances" / relative
    xml_bytes = native_xml.read_bytes()
    xml = parse_xml(xml_bytes, Settings({"SAMPLE_MODE": "true"}))
    assert xml.get("id") == row["jrFormId"] == "lastcopy_collect_smoke_v2"
    assert xml.get("version") == row["jrVersion"] == "20261023"
    assert xml.findtext("site_code") == "0017"
    assert [node.text for node in xml.findall("reading/value")] == ["03", "05"]
    media_name = xml.findtext("supporting_file")
    assert media_name and Path(media_name).name == media_name
    media = (native_xml.parent / media_name).read_bytes()
    assert media == b"LastCopy synthetic emulator attachment. No field or personal data.\n"
    assert (source / "forms/collect-verified.xml").read_bytes() == (ROOT / "private/android/collect-verified.xml").read_bytes()
    at = datetime.now(timezone.utc).isoformat()
    prefix = "projects/c7ee4de9-247c-42ac-8d78-d5bb9e7d8d4d/"
    reference = "docs/verification/collect-export-2026-10-23.json"
    provenance = {"origin": "exporter_metadata", "reference": reference + "#instances-row-2"}
    manifest = {
        "schema_version": 1, "snapshot_id": "collect-emulator-2026-10-23",
        "device_id": "lastcopy-collect-emulator", "captured_at": at,
        "collector_version": "v2026.3.5", "synthetic": True,
        "device_provenance": {"origin": "coordinator_attestation", "reference": reference + "#dedicated-synthetic-avd"},
        "instances": [{"xml_path": prefix + "instances/" + relative.as_posix(),
                       "completion_status": "complete", "completion_provenance": provenance}],
        "form_definitions": [{"xml_path": prefix + "forms/collect-verified.xml"}],
    }
    files = {"device-manifest.json": (json.dumps(manifest, indent=2) + "\n").encode()}
    for directory in ["forms", "instances"]:
        for item in sorted((source / directory).rglob("*")):
            if item.is_file() and (item == source / "forms/collect-verified.xml" or item.parent == native_xml.parent or item.parent == source / "forms/collect-verified-media"):
                files[prefix + item.relative_to(source).as_posix()] = item.read_bytes()
    for name in ["forms.db", "instances.db"]:
        files[prefix + "metadata/" + name] = (source / "metadata" / name).read_bytes()
    target.mkdir()
    archive = target / "device.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 23, 20, 5, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, data)
    observed = inventory(archive.read_bytes(), Settings({"SAMPLE_MODE": "true"}))
    assert len(observed.versions) == 1
    version = observed.versions[0]
    assert version.form_id == "lastcopy_collect_smoke_v2" and version.completion_status == "complete"
    assert len(version.media) == 1 and version.media[0].sha256 == sha(media)
    receipt = {
        "observed_at": at, "status": "PASS", "data": "synthetic answers, actual Collect-generated native instance/export",
        "collector_version": "v2026.3.5", "collector_version_code": 5551,
        "apk_sha256": "82f3fa0d5b95a650f591c0f74a9b920fef448e45c02523a3aaf9505848c91a24",
        "android": "AOSP API 30 x86_64 revision 11", "avd": "LastCopyCollect",
        "emulator": "37.2.12", "platform_tools": "37.0.1", "hypervisor": "WHPX",
        "export_method": "adb pull of dedicated project after am force-stop; original paths and bytes retained",
        "storage_access": "AOSP debug emulator adb-root; imported form assigned app UID and matching project SELinux label; enforcement not disabled",
        "completion_evidence": {"database_sha256": sha(db.read_bytes()), "table": "instances", "row_id": row["_id"],
                                "status": row["status"], "finalization_date_epoch_ms": row["finalizationDate"],
                                "ui": "Collect Finalize action; Ready to send count 2 (one earlier negative control plus this record); not sent"},
        "instance_id": xml.findtext("meta/instanceID"), "form_id": row["jrFormId"], "form_version": row["jrVersion"],
        "xml_path": manifest["instances"][0]["xml_path"], "xml_sha256": sha(xml_bytes),
        "repeat_values": ["03", "05"], "site_code": "0017", "attachment_name": media_name,
        "attachment_bytes": len(media), "attachment_sha256": sha(media),
        "archive_sha256": sha(archive.read_bytes()),
        "files": [{"path": name, "bytes": len(data), "sha256": sha(data)} for name, data in sorted(files.items())],
        "scope": "one unencrypted synthetic Collect project; original capture including cache retained privately",
        "limitations": ["Not a physical-phone compatibility claim", "Not a Central submission or recovery test",
                        "No historic/encrypted export compatibility claim", "ZIP and LastCopy manifest created by code; instance XML and media copied unchanged from Collect"],
    }
    (target / "expected-inventory.json").write_text(json.dumps({"archive_sha256": receipt["archive_sha256"],
        "instance_id": receipt["instance_id"], "form_id": row["jrFormId"], "form_version": row["jrVersion"],
        "completion_status": "complete", "site_code": "0017", "repeat_values": ["03", "05"],
        "attachment_name": media_name, "attachment_sha256": sha(media)}, indent=2) + "\n")
    (ROOT / reference).write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "archive_sha256": receipt["archive_sha256"], "instance_id": receipt["instance_id"],
                      "completion_status": row["status"], "original_file_count": len(files) - 1}, indent=2))


if __name__ == "__main__":
    capture()
