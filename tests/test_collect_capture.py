"""Controls from the actual synthetic Collect 2026.3.5 emulator capture."""
import io
import json
import sqlite3
import zipfile

from lastcopy.config import ROOT, Settings
from lastcopy.inventory import digest, inventory, parse_xml


def test_actual_collect_capture_retains_identity_repeats_media_and_completion(tmp_path):
    directory = ROOT / "fixtures/collect-v2026.3.5"
    data = (directory / "device.zip").read_bytes()
    expected = json.loads((directory / "expected-inventory.json").read_text())
    result = inventory(data, Settings({"SAMPLE_MODE": "true"}))
    assert result.archive_sha256 == expected["archive_sha256"]
    assert result.manifest.collector_version == "v2026.3.5"
    assert not result.limitations
    version, = result.versions
    assert version.version_id == expected["instance_id"]
    assert version.form_id == expected["form_id"]
    assert version.form_version == expected["form_version"]
    assert version.completion_status == "complete"
    media, = version.media
    assert media.filename == expected["attachment_name"]
    assert media.sha256 == expected["attachment_sha256"]
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        xml = parse_xml(archive.read(version.xml_path), Settings({"SAMPLE_MODE": "true"}))
        assert xml.findtext("site_code") == "0017"
        assert [node.text for node in xml.findall("reading/value")] == ["03", "05"]
        assert digest(archive.read(media.archive_path)) == media.sha256
        db_name, = [name for name in archive.namelist() if name.endswith("/metadata/instances.db")]
        db = tmp_path / "instances.db"
        db.write_bytes(archive.read(db_name))
    with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as connection:
        row, = connection.execute("SELECT status, finalizationDate FROM instances WHERE jrFormId = ?", (version.form_id,)).fetchall()
    assert row[0] == "complete" and row[1] > 0
    assert not result.preservation_checked
    assert digest(data) == digest((directory / "device.zip").read_bytes())


def test_namespace_mismatch_does_not_silently_establish_media():
    data = (ROOT / "fixtures/collect-v2026.3.5/device.zip").read_bytes()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    manifest = json.loads(files["device-manifest.json"])
    form_path = manifest["form_definitions"][0]["xml_path"]
    # Reproduce the authored test form mistake found by the real capture:
    # XForms namespace inherited by data template, absent in Collect's instance.
    files[form_path] = files[form_path].replace(b'<data xmlns=""', b'<data')
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, value in files.items():
            archive.writestr(name, value)
    result = inventory(output.getvalue(), Settings({"SAMPLE_MODE": "true"}))
    assert result.versions[0].media == []
    assert any("Missing matching original XForm" in issue for issue in result.limitations)
    assert not result.preservation_checked
