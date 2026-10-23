"""Guard controls for local verification; these do not count as live checks."""
import json
import httpx
import pytest
from scripts import verify_zetaris_local as verifier
from lastcopy.config import Settings
from scripts import smoke, seed_zetaris_local


def prepare(tmp_path, monkeypatch, *, foreign_ui=False):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "lastcopy-prepared.json").write_text(json.dumps({"project": "lastcopy-zetaris", "images": {"UI_IMAGE": "vendor/ui:pinned"}}))
    (bundle / ".env").write_text("GUI_URL=http://localhost:3130\nZETARIS_ADMIN_EMAIL=test@example.invalid\nZETARIS_ADMIN_PASSWORD=private-test-password\n")
    monkeypatch.setattr(verifier, "BUNDLE", bundle)
    monkeypatch.setattr(verifier, "ROOT", tmp_path)
    ui = {"Project": "unrelated" if foreign_ui else "lastcopy-zetaris", "State": "running", "Image": "vendor/ui:pinned"}
    monkeypatch.setattr(verifier.subprocess, "check_output", lambda *a, **k: json.dumps(ui))


def test_wrong_container_identity_prevents_password_transmission(tmp_path, monkeypatch):
    prepare(tmp_path, monkeypatch, foreign_ui=True)
    def forbidden(request):
        raise AssertionError("No HTTP request is allowed for the wrong local container")
    with httpx.Client(transport=httpx.MockTransport(forbidden)) as client:
        with pytest.raises(RuntimeError, match="expected isolated local UI"):
            verifier.connect(client)


@pytest.mark.parametrize("result,passed", [({"data": [{"seven": "7"}]}, True), ({"data": [{"seven": "8"}]}, False)])
def test_reachability_alone_cannot_pass_query_check(tmp_path, monkeypatch, capsys, result, passed):
    prepare(tmp_path, monkeypatch)
    def handler(request):
        if request.url.path == "/api/auth/login":
            return httpx.Response(200, json={"token": "private-unit-test-token", "orgId": 42})
        assert request.url.path == "/api/proxy/query/sql/start"
        assert request.headers["X-Org-ID"] == "42"
        return httpx.Response(200, json=result)
    original_client = httpx.Client
    monkeypatch.setattr(verifier.httpx, "Client", lambda **kw: original_client(transport=httpx.MockTransport(handler), **kw))
    receipt = tmp_path / "private/smoke/zetaris-local-installation.json"
    if passed:
        verifier.verify()
        assert json.loads(receipt.read_text())["two_source_evidence_smoke_passed"] is False
    else:
        with pytest.raises(RuntimeError, match="expected single named cell"):
            verifier.verify()
        assert not receipt.exists()
    output = capsys.readouterr().out
    assert "private-unit-test-token" not in output
    assert "private-test-password" not in output


@pytest.mark.parametrize("values,expected", [
    ({"ZETARIS_S3_PREFIX": "s3a://existing-bucket/tiny/"}, "s3a://existing-bucket/tiny/"),
    ({"ZETARIS_SOURCE_PREFIX": "dffs://lastcopy-stage1-smoke/"}, "dffs://lastcopy-stage1-smoke/"),
    ({"ZETARIS_SOURCE_PREFIX": "dffs://local/", "ZETARIS_S3_PREFIX": "s3a://legacy/"}, "dffs://local/"),
])
def test_source_scope_supports_local_ndp_and_preserves_existing_s3(values, expected):
    settings = Settings(values)
    assert settings.source_prefix == expected
    assert "ZETARIS_SOURCE_PREFIX" not in settings.status("zetaris").missing["zetaris"]


def test_zetaris_probe_uses_required_body_options_without_replacing_sql(monkeypatch):
    rows = [{"submission_id": "synthetic-001", "device_hash": "a" * 64, "server_hash": "a" * 64}, {"submission_id": "synthetic-002", "device_hash": "b" * 64, "server_hash": "c" * 64}]
    values = {"ZETARIS_DEVICE_TABLE": "tiny.device", "ZETARIS_SERVER_TABLE": "tiny.server", "ZETARIS_HEADERS_JSON": "{}", "ZETARIS_QUERY_OPTIONS_JSON": '{"pageLimit":3}', "ZETARIS_QUERY_FIELD": "select", "ZETARIS_SQL_ENDPOINT": "http://localhost:3130/query", "ZETARIS_ROWS_POINTER": "/records", "ZETARIS_DEPLOYMENT_VERSION": "test"}
    def handler(request):
        body = json.loads(request.content)
        assert body["pageLimit"] == 3
        assert "JOIN tiny.server" in body["select"]
        return httpx.Response(200, json={"records": rows})
    original_client = httpx.Client
    monkeypatch.setattr(smoke.httpx, "Client", lambda **kw: original_client(transport=httpx.MockTransport(handler), **kw))
    assert smoke.probe_zetaris(values)["rows"] == rows
    values["ZETARIS_QUERY_OPTIONS_JSON"] = '{"select":"wrong query"}'
    with pytest.raises(smoke.ProbeFailure, match="must not override"):
        smoke.probe_zetaris(values)


def test_config_lock_retry_does_not_replay_source_writes_and_receipt_is_saved_first(tmp_path, monkeypatch, capsys):
    source = verifier.ROOT / "fixtures/zetaris"
    fixture = tmp_path / "fixtures/zetaris"
    fixture.mkdir(parents=True)
    for name in ("device.csv", "server.csv"):
        (fixture / name).write_bytes((source / name).read_bytes())
    monkeypatch.setattr(seed_zetaris_local, "ROOT", tmp_path)
    monkeypatch.setattr(seed_zetaris_local, "connect", lambda client: {"Authorization": "Bearer private-test-token"})
    rows = [{"submission_id": "synthetic-001", "device_hash": "a" * 64, "server_hash": "a" * 64}, {"submission_id": "synthetic-002", "device_hash": "b" * 64, "server_hash": "c" * 64}]
    def handler(request):
        if request.method == "GET" and request.url.path.endswith("/utility/version"):
            return httpx.Response(200, json={"apiVersion": {"version": "2.4.3.1"}})
        assert request.method == "POST" and request.url.path.endswith("/query/sql/start")
        assert json.loads(request.content)["select"].startswith("SELECT ")
        return httpx.Response(200, json={"records": rows})
    original_client = httpx.Client
    monkeypatch.setattr(seed_zetaris_local.httpx, "Client", lambda **kw: original_client(transport=httpx.MockTransport(handler), **kw))
    written = {}
    locked_once = []
    def save(path, name, value):
        assert (tmp_path / "private/smoke/zetaris-registration.json").is_file()
        if not locked_once:
            locked_once.append(True)
            raise PermissionError("test-only transient file lock")
        written[name] = value
    monkeypatch.setattr(seed_zetaris_local, "set_key", save)
    monkeypatch.setattr(seed_zetaris_local.time, "sleep", lambda seconds: None)
    seed_zetaris_local.seed(verify_existing=True)
    assert json.loads(written["ZETARIS_QUERY_OPTIONS_JSON"]) == {"pageLimit": 3}
    assert "private-test-token" not in capsys.readouterr().out
