"""Read-only real-provider probes. Sample mode never opens a connection."""
import argparse
import json
import re
import time
import multiprocessing
from contextvars import ContextVar
from datetime import datetime, timezone
from urllib.parse import quote, urlsplit, urlunsplit
import httpx
from lastcopy.config import Settings, ROOT, REQUIRED
from lastcopy.inventory import digest, parse_xml


class ProbeFailure(Exception):
    pass


DEADLINE = ContextVar("smoke_deadline", default=float("inf"))


def request(client, method, url, *, max_bytes=2097152, **kwargs):
    remaining = DEADLINE.get() - time.monotonic()
    if remaining <= 0:
        raise ProbeFailure("Smoke wall-time budget exhausted")
    timeout = httpx.Timeout(min(remaining, 180), connect=min(remaining, 10))
    with client.stream(method, url, timeout=timeout, **kwargs) as response:
        if response.status_code >= 300:
            # Never include provider body, request URL or headers in diagnostics.
            raise ProbeFailure(f"HTTP {response.status_code}" + (" unauthorized" if response.status_code in (401, 403) else ""))
        data = bytearray()
        for part in response.iter_bytes():
            if time.monotonic() >= DEADLINE.get():
                raise ProbeFailure("Smoke wall-time budget exhausted")
            if len(data) + len(part) > max_bytes:
                raise ProbeFailure("Response exceeds bounded smoke limit")
            data.extend(part)
        return bytes(data)


def nightshift_base(value):
    url = urlsplit(value)
    path = url.path.rstrip("/")
    for suffix in ("/v1/chat/completions", "/v1/models", "/healthz", "/v1"):
        if path.endswith(suffix):
            path = path[:-len(suffix)]
            break
    return urlunsplit((url.scheme, url.netloc, path + "/v1", "", ""))


def probe_nightshift(values):
    base = nightshift_base(values["NIGHTSHIFT_BASE_URL"])
    headers = {"Authorization": "Bearer " + values["NIGHTSHIFT_TOKEN"], "meterless-app": "lastcopy", "meterless-scope": "user"}
    with httpx.Client(timeout=httpx.Timeout(180, connect=10), follow_redirects=False) as client:
        inventory = json.loads(request(client, "GET", base + "/models", headers=headers))
        ids = [item["id"] for item in inventory.get("data", [])]
        route = values["NIGHTSHIFT_ROUTE"]
        if route not in ids or not any(i.startswith("meterless/") for i in ids):
            raise ProbeFailure("NIGHTSHIFT_ROUTE not in authenticated Meterless inventory")
        body = {"model": route, "messages": [{"role": "user", "content": 'Synthetic smoke: respond with the text LASTCOPY_OK.'}], "max_tokens": 64}
        inference_raw = request(client, "POST", base + "/chat/completions", headers=headers, json=body)
        inference = json.loads(inference_raw)
        content = inference.get("choices", [{}])[0].get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise ProbeFailure("Inference did not return a text string")
        # Serving model must be a reported concrete identity, not a routing alias.
        actual = inference.get("model")
        actual = actual if isinstance(actual, str) and not actual.startswith("meterless/") else None
        capabilities = {}
        tool = {"type": "function", "function": {"name": "inspect_evidence", "description": "Read synthetic evidence", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}}
        probes = {
            "native_tools": {"tools": [tool], "tool_choice": {"type": "function", "function": {"name": "inspect_evidence"}}},
            "structured_output": {"response_format": {"type": "json_schema", "json_schema": {"name": "action", "strict": True, "schema": {"type": "object", "properties": {"action": {"type": "string", "enum": ["inspect_evidence"]}}, "required": ["action"], "additionalProperties": False}}}},
        }
        for name, options in probes.items():
            try:
                reply = json.loads(request(client, "POST", base + "/chat/completions", headers=headers, json={**body, **options}))
                msg = reply.get("choices", [{}])[0].get("message", {})
                if name == "native_tools":
                    calls = msg.get("tool_calls", [])
                    supported = bool(calls) and all(c.get("function", {}).get("name") == "inspect_evidence" and json.loads(c["function"]["arguments"]) == {} for c in calls)
                else:
                    supported = json.loads(msg.get("content", "null")) == {"action": "inspect_evidence"}
                capabilities[name] = "observed_supported" if supported else "not_demonstrated"
            except (ProbeFailure, ValueError, KeyError, TypeError):
                capabilities[name] = "not_demonstrated"
        return {"inventory_count": len(ids), "routing_id": route, "actual_serving_model": actual, "serving_model_resolved": actual is not None, "response_sha256": digest(inference_raw), "capabilities": capabilities, "nvidia_award_verified": False, "next": "Stage 3 must validate action JSON and dispatch code-owned tools; no tool execution in Stage 1"}


def pointer(value, path):
    if path == "/":
        return value
    for key in path.lstrip("/").split("/"):
        value = value[key.replace("~1", "/").replace("~0", "~")]
    return value


def probe_zetaris(values):
    tables = [values["ZETARIS_DEVICE_TABLE"], values["ZETARIS_SERVER_TABLE"]]
    if any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?", table) for table in tables) or tables[0] == tables[1]:
        raise ProbeFailure("Configure two distinct simple registered synthetic table names")
    sql = f"SELECT d.submission_id, d.xml_sha256 AS device_hash, s.xml_sha256 AS server_hash FROM {tables[0]} d JOIN {tables[1]} s ON d.submission_id = s.submission_id WHERE d.run_id = 'lastcopy-smoke-001' AND s.run_id = 'lastcopy-smoke-001' LIMIT 3"
    headers = json.loads(values["ZETARIS_HEADERS_JSON"])
    if not isinstance(headers, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in headers.items()):
        raise ProbeFailure("ZETARIS_HEADERS_JSON must be a header object matching the actual deployment")
    try:
        options = json.loads(values.get("ZETARIS_QUERY_OPTIONS_JSON", "{}"))
    except ValueError:
        raise ProbeFailure("ZETARIS_QUERY_OPTIONS_JSON must be a JSON object") from None
    if not isinstance(options, dict) or values["ZETARIS_QUERY_FIELD"] in options:
        raise ProbeFailure("ZETARIS_QUERY_OPTIONS_JSON must be an object and must not override the SQL field")
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        response = request(client, "POST", values["ZETARIS_SQL_ENDPOINT"], headers=headers, json={**options, values["ZETARIS_QUERY_FIELD"]: sql})
    rows = pointer(json.loads(response), values["ZETARIS_ROWS_POINTER"])
    expected = [{"submission_id": "synthetic-001", "device_hash": "a" * 64, "server_hash": "a" * 64}, {"submission_id": "synthetic-002", "device_hash": "b" * 64, "server_hash": "c" * 64}]
    if not isinstance(rows, list) or sorted(rows, key=lambda row: row["submission_id"]) != expected:
        raise ProbeFailure("Query rows do not match the two tiny synthetic sources")
    return {"sql": sql, "sources": tables, "source_prefix": values.get("ZETARIS_SOURCE_PREFIX") or values.get("ZETARIS_S3_PREFIX"), "rows": rows, "rows_sha256": digest(json.dumps(rows, sort_keys=True).encode()), "deployment_version": values["ZETARIS_DEPLOYMENT_VERSION"], "registration_only": False}


def probe_odk(values):
    if values.get("ODK_TEST_PROJECT") != "true":
        raise ProbeFailure("ODK_TEST_PROJECT must attest a dedicated synthetic test project")
    base = values["ODK_BASE_URL"].rstrip("/")
    project, form, submission, version, filename = [quote(values[name], safe="") for name in ("ODK_PROJECT_ID", "ODK_FORM_ID", "ODK_SUBMISSION_ID", "ODK_VERSION_ID", "ODK_ATTACHMENT_NAME")]
    scope = f"/v1/projects/{project}/forms/{form}/submissions/{submission}"
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        login = json.loads(request(client, "POST", base + "/v1/sessions", json={"email": values["ODK_EMAIL"], "password": values["ODK_PASSWORD"]}))
        headers = {"Authorization": "Bearer " + login["token"]}
        metadata = request(client, "GET", base + f"/v1/projects/{project}", headers=headers)
        versions = json.loads(request(client, "GET", base + scope + "/versions", headers=headers))
        if not any(item.get("instanceId") == values["ODK_VERSION_ID"] for item in versions):
            raise ProbeFailure("ODK_VERSION_ID not in retrieved submission history")
        xml = request(client, "GET", base + scope + f"/versions/{version}.xml", headers=headers)
        root = parse_xml(xml, Settings(values))
        if root.attrib.get("id") != values["ODK_FORM_ID"] or root.findtext("./{*}meta/{*}instanceID") != values["ODK_VERSION_ID"]:
            raise ProbeFailure("XML identity does not match configured scope")
        slots = json.loads(request(client, "GET", base + scope + f"/versions/{version}/attachments", headers=headers))
        if not any(item.get("name") == values["ODK_ATTACHMENT_NAME"] and item.get("exists") is True for item in slots):
            raise ProbeFailure("Known synthetic attachment slot is absent")
        media = request(client, "GET", base + scope + f"/versions/{version}/attachments/{filename}", headers=headers)
    return {"scope": scope, "version_id": values["ODK_VERSION_ID"], "operator_reported_central_version": values["ODK_CENTRAL_VERSION"], "metadata_sha256": digest(metadata), "xml_sha256": digest(xml), "attachment_sha256": digest(media), "attachment_bytes": len(media), "write_performed": False, "preservation_checked": False}


def _probe_worker(connection, provider, values, seconds):
    DEADLINE.set(time.monotonic() + seconds)
    try:
        connection.send({"status": "PASS", "details": globals()["probe_" + provider](values)})
    except ProbeFailure as e:
        connection.send({"status": "FAIL", "reason": str(e)})
    except Exception as e:
        connection.send({"status": "FAIL", "reason": type(e).__name__ + ": check configured endpoint/schema; secret-bearing diagnostics suppressed"})
    finally:
        connection.close()


def bounded_probe(provider, values, seconds):
    # A process boundary enforces the total wall budget on Windows too, including
    # slow-trickling HTTP bodies that per-read timeouts alone cannot bound.
    context = multiprocessing.get_context("spawn")
    reader, writer = context.Pipe(duplex=False)
    process = context.Process(target=_probe_worker, args=(writer, provider, values, seconds))
    process.start()
    writer.close()
    try:
        if reader.poll(seconds):
            return reader.recv()
        return {"status": "FAIL", "reason": "Smoke wall-time budget exhausted"}
    finally:
        if process.is_alive():
            process.terminate()
        process.join(timeout=5)
        reader.close()


def run(provider, settings):
    started = time.monotonic()
    DEADLINE.set(started + settings.limit("MAX_RUN_SECONDS"))
    result = {"provider": provider, "observed_at": datetime.now(timezone.utc).isoformat(), "mode": "sample" if settings.sample else "connected"}
    status = settings.status(provider)
    missing = status.missing[provider]
    if settings.sample or missing or status.errors:
        result.update(status="BLOCKED", reason="SAMPLE_MODE disables external access" if settings.sample else "Missing or invalid configuration", missing=missing, configuration_errors=status.errors)
    else:
        try:
            result.update(bounded_probe(provider, settings.values, settings.limit("MAX_RUN_SECONDS")))
        except ProbeFailure as e:
            result.update(status="FAIL", reason=str(e))
        except Exception as e:
            result.update(status="FAIL", reason=type(e).__name__ + ": check configured endpoint/schema; secret-bearing diagnostics suppressed")
    result["elapsed_ms"] = round((time.monotonic() - started) * 1000, 2)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("provider", choices=["zetaris", "nightshift", "odk", "all"])
    args = parser.parse_args()
    settings = Settings.load()
    results = [run(p, settings) for p in REQUIRED if args.provider in (p, "all")]
    # Only generated, deliberately redacted receipts. No raw responses/tokens.
    directory = ROOT / "private/smoke"
    directory.mkdir(parents=True, exist_ok=True)
    for result in results:
        (directory / (result["provider"] + ".json")).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(results, indent=2))
    raise SystemExit(0 if all(r["status"] == "PASS" for r in results) else 2)
