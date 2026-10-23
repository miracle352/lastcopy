import io
import json
import socket
import stat
import zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from lastcopy.api import app
from lastcopy.config import Settings, ROOT, REQUIRED
from lastcopy.inventory import inventory, parse_xml, ImportRejected, digest
from lastcopy.models import DeviceManifest, RunManifest, Finding, SourceSnapshot
from scripts.smoke import run, nightshift_base
from lastcopy.scope import validate_run_import
from scripts.validate_snapshot import validate as validate_snapshot
from scripts.export_contracts import build_openapi

FIXTURE = ROOT / "fixtures/representative"
SAMPLE = Settings({"SAMPLE_MODE": "true"})


def archive(entries):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as target:
        for name, value in entries:
            target.writestr(name, value)
    return out.getvalue()


def files():
    with zipfile.ZipFile(FIXTURE / "device.zip") as source:
        return {name: source.read(name) for name in source.namelist()}


def test_representative_identity_repeats_and_immutable_bytes():
    source = (FIXTURE / "device.zip").read_bytes()
    expected = json.loads((FIXTURE / "expected-inventory.json").read_text())
    result = inventory(source, SAMPLE)
    version = result.versions[0]
    assert version.form_id == expected["form_id"]
    assert version.form_version == expected["form_version"]
    assert version.version_id == expected["version_id"]
    assert len(version.media) == 2
    assert version.media[0].archive_path == version.media[1].archive_path
    assert version.media[0].occurrence_indices == [1, 1, 1]
    assert version.media[1].occurrence_indices == [1, 2, 1]
    assert version.media[0].sha256 == version.media[1].sha256
    assert not result.preservation_checked
    assert digest(source) == digest((FIXTURE / "device.zip").read_bytes())


@pytest.mark.parametrize("status", ["draft", "unknown"])
def test_completion_must_be_explicit_and_never_upgraded(status):
    entries = files()
    manifest = json.loads(entries["device-manifest.json"])
    manifest["instances"][0]["completion_status"] = status
    entries["device-manifest.json"] = json.dumps(manifest).encode()
    result = inventory(archive(entries.items()), SAMPLE)
    assert result.versions[0].completion_status == status
    assert any("excluded" in issue for issue in result.limitations)
    del manifest["instances"][0]["completion_status"]
    with pytest.raises(ValidationError):
        DeviceManifest.model_validate(manifest)


def test_provenance_and_unrecognized_fields_required():
    manifest = json.loads(files()["device-manifest.json"])
    del manifest["device_provenance"]
    with pytest.raises(ValidationError):
        DeviceManifest.model_validate(manifest)


@pytest.mark.parametrize("path", ["../outside", "/absolute", "C:/drive", "a\\b", "a/./b", "a//b", "a/../b"])
def test_hostile_zip_paths(path):
    with pytest.raises(ImportRejected):
        inventory(archive([(path, b"data")]), SAMPLE)


def test_duplicate_casefold_and_file_parent_paths_rejected():
    for entries in ([('a', b'x'), ('A', b'y')], [('a', b'x'), ('a/b', b'y')]):
        with pytest.raises(ImportRejected):
            inventory(archive(entries), SAMPLE)


def test_symlink_rejected():
    link = zipfile.ZipInfo("link")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    with pytest.raises(ImportRejected, match="symlink"):
        inventory(archive([(link, b"/etc/passwd")]), SAMPLE)


def test_encrypted_flag_rejected():
    data = bytearray(archive([("secret", b"x")]))
    local = data.index(b"PK\x03\x04")
    central = data.index(b"PK\x01\x02")
    data[local + 6] |= 1
    data[central + 8] |= 1
    with pytest.raises(ImportRejected, match="Encrypted"):
        inventory(bytes(data), SAMPLE)


@pytest.mark.parametrize("limits", [{"MAX_UPLOAD_BYTES": "10"}, {"MAX_UNCOMPRESSED_BYTES": "20"}, {"MAX_ZIP_ENTRIES": "1"}])
def test_zip_limits(limits):
    with pytest.raises(ImportRejected):
        inventory((FIXTURE / "device.zip").read_bytes(), Settings(limits))


@pytest.mark.parametrize("data,limits", [
    (b'<!DOCTYPE a [<!ENTITY secret SYSTEM "file:///etc/passwd">]><a>&secret;</a>', {}),
    (b'<a><b><c/></b></a>', {"MAX_XML_DEPTH": "2"}),
    (b'<a><b/><c/></a>', {"MAX_XML_NODES": "2"}),
    (b'<a>long text</a>', {"MAX_XML_TEXT": "2"}),
    (b'<a/>', {"MAX_XML_BYTES": "2"}),
    (b'<unclosed>', {}),
])
def test_xml_hardening(data, limits):
    with pytest.raises(ImportRejected):
        parse_xml(data, Settings(limits))


def test_missing_media_and_form_identity_are_limitations():
    entries = files()
    media_path = next(path for path in entries if path.endswith("sample.txt"))
    del entries[media_path]
    result = inventory(archive(entries.items()), SAMPLE)
    assert result.versions[0].media[0].sha256 is None
    assert any("absent" in issue for issue in result.limitations)
    xml_path = result.versions[0].xml_path
    entries[xml_path] = entries[xml_path].replace(b'version="20261023"', b'version="unknown"')
    assert any("matching original XForm" in issue for issue in inventory(archive(entries.items()), SAMPLE).limitations)


def test_contract_disallows_false_preservation():
    with pytest.raises(ValidationError):
        Finding(finding_id="f", verdict="CONTENT_CONFLICT", preservation="preserved", summary="bad", snapshot_id="s", form_id="f", logical_submission_id="i", version_id="v", evidence_ids=["e"], absence_scope=None)


def test_exported_contracts_match_authoritative_models():
    assert json.loads((ROOT / "contracts/openapi.json").read_text()) == build_openapi()


def test_pinned_upstream_source_integrity():
    upstream = ROOT / "third_party/world-model"
    pin = json.loads((upstream / "UPSTREAM.json").read_text())
    assert pin["commit"] == "1742dec56a66e58eef9dda2d2b865823758ca8cd"
    assert all(digest((upstream / path).read_bytes()) == expected for path, expected in pin["files_sha256"].items())


def test_provider_probes_are_independent():
    config = Settings({"SAMPLE_MODE": "false", "NIGHTSHIFT_BASE_URL": "http://127.0.0.1:8088/v1", "NIGHTSHIFT_TOKEN": "test-only", "NIGHTSHIFT_ROUTE": "meterless/auto"})
    assert config.status("nightshift").ready
    assert not config.status().ready


def test_run_manifest_uses_explicit_synthetic_destination():
    run_manifest = RunManifest.model_validate_json((FIXTURE / "run-manifest.json").read_bytes())
    assert run_manifest.destination.project_id == 7
    assert run_manifest.destination.mapping_provenance.origin == "coordinator_attestation"
    assert run_manifest.max_steps == 12
    imported = inventory((FIXTURE / "device.zip").read_bytes(), SAMPLE)
    assert validate_run_import(run_manifest, imported) == []
    run_manifest.destination.form_id = "wrong-form"
    assert "destination mapping" in validate_run_import(run_manifest, imported)[0]


def test_raw_snapshot_contract_and_payload():
    result = validate_snapshot(FIXTURE / "server-snapshot.json", FIXTURE / "server-payload.zip")
    assert result["synthetic"] is True
    assert result["versions"] == 1
    assert result["preservation_checked"] is False


def test_partial_snapshot_missing_media_remains_explicit(tmp_path):
    snapshot = json.loads((FIXTURE / "server-snapshot.json").read_text())
    with zipfile.ZipFile(FIXTURE / "server-payload.zip") as source:
        payload = archive([("xml/original.xml", source.read("xml/original.xml"))])
    snapshot["archive_sha256"] = digest(payload)
    snapshot["scope_complete"] = False
    snapshot["limitations"] = ["Synthetic permission failure prevents attachment readback"]
    failed = snapshot["receipts"][1]
    failed.update(source_file=None, response_sha256=None, outcome="failed", http_status=403)
    for media in snapshot["versions"][0]["media"]:
        media["sha256"] = None
    manifest_path, payload_path = tmp_path / "manifest.json", tmp_path / "payload.zip"
    manifest_path.write_text(json.dumps(snapshot))
    payload_path.write_bytes(payload)
    result = validate_snapshot(manifest_path, payload_path)
    assert result["scope_complete"] is False and result["preservation_checked"] is False
    snapshot["scope_complete"] = True
    manifest_path.write_text(json.dumps(snapshot))
    with pytest.raises(ImportRejected, match="incomplete scope"):
        validate_snapshot(manifest_path, payload_path)


def test_config_redaction_and_bad_values():
    config = Settings({"SAMPLE_MODE": "false", "ODK_PASSWORD": "secret-for-test", "ODK_BASE_URL": "https://user:secret-for-test@localhost", "MAX_RUN_SECONDS": "999", "ODK_PROJECT_ID": "bad"}).status()
    assert not config.ready
    assert config.errors
    assert "secret-for-test" not in config.model_dump_json()
    assert "ODK_EMAIL" in config.missing["odk"]


def test_sample_blocks_all_external_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network called in sample mode")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr("scripts.smoke.bounded_probe", forbidden)
    configured = {name: "synthetic-test-setting" for names in REQUIRED.values() for name in names}
    configured["SAMPLE_MODE"] = "true"
    sample = Settings(configured)
    for provider in ("zetaris", "nightshift", "odk"):
        assert run(provider, sample)["status"] == "BLOCKED"
    assert inventory((FIXTURE / "device.zip").read_bytes(), SAMPLE).mode == "sample"


def test_connected_provider_failure_remains_failure(monkeypatch):
    settings = Settings({"SAMPLE_MODE": "false", "NIGHTSHIFT_BASE_URL": "http://127.0.0.1:8088/v1", "NIGHTSHIFT_TOKEN": "test-token", "NIGHTSHIFT_ROUTE": "meterless/auto"})
    monkeypatch.setattr("scripts.smoke.bounded_probe", lambda *args: {"status": "FAIL", "reason": "HTTP 401 unauthorized"})
    result = run("nightshift", settings)
    assert result["status"] == "FAIL" and result["mode"] == "connected"
    assert "details" not in result


@pytest.mark.parametrize("suffix", ["", "/v1", "/v1/models", "/v1/chat/completions", "/healthz"])
def test_nightshift_base_normalization(suffix):
    assert nightshift_base("http://127.0.0.1:8088" + suffix) == "http://127.0.0.1:8088/v1"


def test_api_health_and_real_fixture_contract(monkeypatch):
    monkeypatch.setenv("SAMPLE_MODE", "true")
    with TestClient(app) as client:
        assert client.get("/health").json()["live_verified"] is False
        assert client.get("/configuration").json()["ready"] is True
        expected = inventory((FIXTURE / "device.zip").read_bytes(), SAMPLE).model_dump(mode="json")
        assert client.get("/sample/inventory").json() == expected
        assert client.post("/imports/validate", content=(FIXTURE / "device.zip").read_bytes()).json() == expected
        assert client.post("/imports/validate", content=b"invalid").status_code == 422
        monkeypatch.setenv("MAX_UPLOAD_BYTES", "10")
        assert client.post("/imports/validate", content=b"a" * 11).status_code == 413


def test_connected_never_falls_back_to_sample(monkeypatch):
    monkeypatch.setenv("SAMPLE_MODE", "false")
    with TestClient(app) as client:
        assert client.get("/sample/inventory").status_code == 409
        assert client.get("/health").json()["mode"] == "connected"
        assert client.get("/configuration").json()["ready"] is False
