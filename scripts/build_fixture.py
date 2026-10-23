"""Authored synthetic fixture, fixed paths/IDs/times. No model or network."""
import json
import zipfile
from pathlib import Path
from lastcopy.inventory import digest

ROOT = Path(__file__).resolve().parents[1] / "fixtures/representative"
AT = "2026-10-23T09:00:00Z"
ID = "uuid:11111111-2222-4333-8444-555555555555"
attestation = {"origin": "coordinator_attestation", "reference": "synthetic-coordinator-selection-001"}
manifest = {
    "schema_version": 1, "snapshot_id": "synthetic-device-a-001", "device_id": "device-a",
    "captured_at": AT, "collector_version": "unknown", "device_provenance": attestation,
    "synthetic": True,
    "instances": [{"xml_path": "projects/field-a/instances/inspection_001/inspection-final.xml", "completion_status": "complete", "completion_provenance": attestation}],
    "form_definitions": [{"xml_path": "projects/field-a/forms/inspection.xml"}],
}
xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<data xmlns="urn:lastcopy:inspection" id="inspection" version="20261023">
  <site_code>0017</site_code><notes>  Café — synthetic observation  </notes>
  <reading><value>03</value><attachment>sample.txt</attachment></reading>
  <reading><value>05</value><attachment>sample.txt</attachment></reading>
  <meta><instanceID>{ID}</instanceID></meta>
</data>
'''
form = '''<?xml version="1.0" encoding="UTF-8"?>
<h:html xmlns:h="http://www.w3.org/1999/xhtml" xmlns="http://www.w3.org/2002/xforms" xmlns:jr="http://openrosa.org/javarosa">
<h:head><h:title>Synthetic inspection</h:title><model>
<instance><data xmlns="urn:lastcopy:inspection" id="inspection" version="20261023"><site_code/><notes/><reading jr:template=""><value/><attachment/></reading><meta><instanceID/></meta></data></instance>
<bind nodeset="/data/site_code" type="string"/><bind nodeset="/data/notes" type="string"/>
<bind nodeset="/data/reading/value" type="string"/><bind nodeset="/data/reading/attachment" type="binary"/>
<bind nodeset="/data/meta/instanceID" type="string" readonly="true()"/>
</model></h:head><h:body><input ref="/data/site_code"><label>Site code</label></input><input ref="/data/notes"><label>Notes</label></input><group ref="/data/reading"><label>Readings</label><repeat nodeset="/data/reading"><input ref="value"><label>Value</label></input><upload ref="attachment" mediatype="text/*"><label>Supporting file</label></upload></repeat></group></h:body></h:html>
'''
files = {
    "device-manifest.json": (json.dumps(manifest, indent=2) + "\n").encode(),
    manifest["instances"][0]["xml_path"]: xml.encode(),
    manifest["form_definitions"][0]["xml_path"]: form.encode(),
    "projects/field-a/instances/inspection_001/sample.txt": b"Synthetic field attachment. No personal or community data.\n",
}
ROOT.mkdir(parents=True, exist_ok=True)
for path, data in files.items():
    target = ROOT / "device" / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
with zipfile.ZipFile(ROOT / "device.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path, data in sorted(files.items()):
        entry = zipfile.ZipInfo(path, date_time=(2026, 10, 23, 9, 0, 0))
        entry.external_attr = 0o100644 << 16
        entry.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(entry, data)
run = {"schema_version": 1, "run_id": "synthetic-stage1", "mode": "sample", "source_snapshot_ids": [manifest["snapshot_id"], "synthetic-server-001"], "expected_device_ids": ["device-a"], "roster_provenance": attestation, "destination": {"connection_id": "synthetic-offline-only", "project_id": 7, "form_id": "inspection", "environment": "dedicated_synthetic_test", "mapping_provenance": attestation}}
(ROOT / "run-manifest.json").write_text(json.dumps(run, indent=2) + "\n")
(ROOT / "expected-inventory.json").write_text(json.dumps({"form_id": "inspection", "form_version": "20261023", "version_id": ID, "site_code": "0017", "repeat_count": 2, "media_references": 2, "unique_attachment_slots": 1, "completion_status": "complete", "preservation_checked": False}, indent=2) + "\n")
print("Built deterministic representative archive", digest((ROOT / "device.zip").read_bytes()))

# Same envelope a future read-only exporter will emit; this pack is SYNTHETIC,
# not an exporter observation. Envelope stays outside the hashed payload ZIP.
from lastcopy.inventory import inventory
from lastcopy.config import Settings
from lastcopy.models import SourceSnapshot, EvidenceReceipt
device = inventory((ROOT / "device.zip").read_bytes(), Settings({"SAMPLE_MODE": "true"}))
version = device.versions[0].model_copy(deep=True)
version.snapshot_id = "synthetic-server-001"
version.xml_path = "xml/original.xml"
version.current = True
server_files = {version.xml_path: xml.encode(), "media/sample.txt": files["projects/field-a/instances/inspection_001/sample.txt"]}
with zipfile.ZipFile(ROOT / "server-payload.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path, data in sorted(server_files.items()):
        entry = zipfile.ZipInfo(path, date_time=(2026, 10, 23, 9, 0, 0))
        entry.external_attr = 0o100644 << 16
        entry.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(entry, data)
receipts = []
for index, (path, data) in enumerate(server_files.items()):
    receipts.append(EvidenceReceipt(evidence_id=f"synthetic-receipt-{index}", source_snapshot_id=version.snapshot_id, source_file=path, archive_sha256=None, captured_at=AT, query_receipt_id=None, request_method="LOCAL", outcome="synthetic", request_scope="synthetic-pack-generator; not an HTTP request", response_sha256=digest(data), comparison=None, form_id=version.form_id, version_id=version.version_id, xml_path=None))
for media in version.media:
    media.archive_path = "media/sample.txt"
    media.readback_receipt_id = "synthetic-receipt-1"
snapshot = SourceSnapshot(schema_version=1, snapshot_id=version.snapshot_id, kind="central_raw", archive_sha256=digest((ROOT / "server-payload.zip").read_bytes()), captured_at=AT, synthetic=True, scope_complete=True, project_id=7, form_ids=[version.form_id], versions=[version], receipt_ids=[r.evidence_id for r in receipts], receipts=receipts, limitations=["Synthetic scoped snapshot, not a live Central exporter capture"])
(ROOT / "server-snapshot.json").write_text(snapshot.model_dump_json(indent=2) + "\n", encoding="utf-8")
