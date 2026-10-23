"""Setup guard tests use mocks only; they are never claimed as live smokes."""
import json
import shutil
from pathlib import Path
import httpx
import pytest
from dotenv import dotenv_values
from lastcopy.config import ROOT
from scripts import setup_odk_test, seed_odk_test, configure_nightshift


def test_odk_setup_pins_release_and_preserves_existing_config(tmp_path, monkeypatch):
    checkout = tmp_path / "private/central"
    checkout.mkdir(parents=True)
    monkeypatch.setattr(setup_odk_test, "ROOT", tmp_path)
    monkeypatch.setattr(setup_odk_test.subprocess, "check_output", lambda *a, **k: setup_odk_test.CENTRAL_COMMIT)
    setup_odk_test.prepare()
    override = (checkout / "lastcopy.local.yml").read_text()
    assert "127.0.0.1:8384:80" in override
    assert "internal: true" in override
    assert "0.0.0.0" not in override
    (checkout / ".env").write_text("existing user configuration")
    with pytest.raises(SystemExit, match="Refusing to overwrite"):
        setup_odk_test.prepare()
    assert (checkout / ".env").read_text() == "existing user configuration"


def test_seed_refuses_remote_connection_before_any_network_or_admin_write(tmp_path, monkeypatch):
    fixture = tmp_path / "fixtures/representative"
    shutil.copytree(ROOT / "fixtures/representative", fixture)
    (tmp_path / ".env").write_text("ODK_BASE_URL=https://production.example.invalid\n")
    monkeypatch.setattr(seed_odk_test, "ROOT", tmp_path)
    monkeypatch.setattr(seed_odk_test.subprocess, "check_output", lambda *a, **k: setup_odk_test.CENTRAL_COMMIT)
    def forbidden(*args, **kwargs):
        raise AssertionError("Network/admin action on refused target")
    monkeypatch.setattr(seed_odk_test, "docker_admin", forbidden)
    monkeypatch.setattr(seed_odk_test.httpx, "Client", forbidden)
    with pytest.raises(RuntimeError, match="not this local test stack"):
        seed_odk_test.seed()


@pytest.mark.parametrize("resources_present", [False, True])
def test_database_build_marker_only_for_empty_stack(tmp_path, monkeypatch, resources_present):
    directory = tmp_path / "private/central/files"
    directory.mkdir(parents=True)
    monkeypatch.setattr(setup_odk_test, "ROOT", tmp_path)
    monkeypatch.setattr(setup_odk_test.subprocess, "check_output", lambda *a, **k: "existing-volume" if resources_present else "")
    marker = directory / "allow-postgres14-upgrade"
    if resources_present:
        with pytest.raises(SystemExit, match="manual upgrade review"):
            setup_odk_test.initialize_fresh_database()
        assert not marker.exists()
    else:
        setup_odk_test.initialize_fresh_database()
        assert marker.is_file()


def test_runtime_configuration_uses_real_token_without_printing_it(tmp_path, monkeypatch, capsys):
    token = "unit-test-only-private-runtime-token"
    state = tmp_path / "appdata/ai.meterless.runtime"
    state.mkdir(parents=True)
    (state / "proxy-token").write_text(token)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "appdata"))
    monkeypatch.setattr(configure_nightshift, "ROOT", tmp_path)
    original_client = httpx.Client
    calls = []
    def handler(request):
        calls.append(request)
        if request.headers.get("authorization") == "Bearer " + token:
            return httpx.Response(200, json={"data": [{"id": "meterless/auto"}, {"id": "meterless/new-route"}]})
        return httpx.Response(401)
    monkeypatch.setattr(configure_nightshift.httpx, "Client", lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs))
    configure_nightshift.configure()
    output = capsys.readouterr().out
    assert token not in output
    assert len(calls) == 2
    assert all(request.headers["meterless-app"] == "lastcopy" for request in calls)
    saved = dotenv_values(tmp_path / ".env")
    assert saved["NIGHTSHIFT_TOKEN"] == token
    assert saved["SAMPLE_MODE"] == "true"
    assert "meterless/new-route" in json.loads(output)["routes"]
