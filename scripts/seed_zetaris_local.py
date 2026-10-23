"""Register only the two bundled synthetic CSVs in our verified local Zetaris.

Uses request shapes and dffs paths from the actual shipped UI client. This is
connected integration setup, not Sample mode, investigation or recovery logic.
"""
import json
import argparse
import time
from datetime import datetime, timezone
from pathlib import PurePosixPath
from dotenv import set_key
import httpx
from lastcopy.config import ROOT
from lastcopy.inventory import digest
from .verify_zetaris_local import BASE, connect

DATABASE = "lastcopy_stage1"
DIRECTORY = "file-store/lastcopy-stage1-smoke"
SOURCE = "dffs://lastcopy-stage1-smoke/"


def seed(verify_existing=False):
    files = {name: (ROOT / "fixtures/zetaris" / name).read_bytes() for name in ("device.csv", "server.csv")}
    hashes = {name: digest(data) for name, data in files.items()}
    output = ROOT / "private/smoke/zetaris-registration.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(output.read_text()) if output.exists() else None
    if existing and (existing.get("source_hashes") != hashes or existing.get("base_url") != BASE):
        raise RuntimeError("Existing synthetic registration receipt differs; refusing changes")
    statements = []
    with httpx.Client(timeout=180, follow_redirects=False, trust_env=False) as client:
        headers = connect(client)
        def call(method, path, **kwargs):
            response = client.request(method, BASE + "/api/proxy" + path, headers=headers, **kwargs)
            if not 200 <= response.status_code < 300:
                raise RuntimeError(f"Local synthetic setup {method} returned HTTP {response.status_code}; body suppressed")
            return response
        def sql(statement):
            response = call("POST", "/sql-editor/sqls/run-query", json={"sql": statement, "limit": 5})
            result = response.json()
            if isinstance(result, dict) and any(result.get(key) for key in ("error", "errorMessage")):
                raise RuntimeError("Synthetic registration SQL failed; no result claimed")
            statements.append({"sql": statement, "response_sha256": digest(response.content)})
        if not existing and not verify_existing:
            listing = call("GET", "/ndp-files/list", params={"path": "file-store"}).json()
            databases = call("GET", "/lightning-database/databases").json()
            if not isinstance(listing, list) or not isinstance(databases, list):
                raise RuntimeError("Local source-list response differs from the shipped client contract")
            if any(PurePosixPath(str(item.get("fileName", ""))).name == DIRECTORY.rsplit("/", 1)[1] for item in listing):
                raise RuntimeError("Synthetic folder already exists without our receipt; refusing overwrite")
            if DATABASE.lower() in json.dumps(databases).lower():
                raise RuntimeError("Synthetic database already exists without our receipt; refusing overwrite")
            call("POST", "/ndp-files/createdir", json={"path": DIRECTORY})
            upload = call("POST", "/ndp-files/save", data={"path": DIRECTORY}, files=[("files", (name, data, "text/csv")) for name, data in files.items()]).json()
            results = upload.get("results", [])
            successes = {PurePosixPath(str(item["SaveSuccess"]["fileName"])).name for item in results if isinstance(item, dict) and "SaveSuccess" in item}
            if successes != set(files) or any("SaveFailure" in item for item in results):
                # Retain controlled synthetic upload response privately for diagnosis.
                (ROOT / "private/smoke/zetaris-upload-response.json").write_text(json.dumps(upload), encoding="utf-8")
                raise RuntimeError("Both synthetic CSV uploads were not attested; not registering tables")
            sql(f'CREATE LIGHTNING DATABASE {DATABASE} DESCRIBE BY "LastCopy synthetic Stage 1 smoke"')
            for table, name in (("device_evidence", "device.csv"), ("server_evidence", "server.csv")):
                sql(f'CREATE LIGHTNING FILESTORE TABLE {table} FROM {DATABASE} FORMAT CSV OPTIONS (path "{SOURCE}{name}", header "true", inferSchema "false")')
        versions = call("GET", "/utility/version").json()
        # This is an actual engine-side join; expected rows live in scripts.smoke.
        query = f"SELECT d.submission_id, d.xml_sha256 AS device_hash, s.xml_sha256 AS server_hash FROM {DATABASE}.device_evidence d JOIN {DATABASE}.server_evidence s ON d.submission_id = s.submission_id WHERE d.run_id = 'lastcopy-smoke-001' AND s.run_id = 'lastcopy-smoke-001' LIMIT 3"
        joined = call("POST", "/query/sql/start", json={"select": query, "pageLimit": 3})
        rows = joined.json().get("records")
        expected = [{"submission_id": "synthetic-001", "device_hash": "a" * 64, "server_hash": "a" * 64}, {"submission_id": "synthetic-002", "device_hash": "b" * 64, "server_hash": "c" * 64}]
        if not isinstance(rows, list) or sorted(rows, key=lambda r: r["submission_id"]) != expected:
            raise RuntimeError("Real joined rows differ from independently authored expectations")
    for name, expected_hash in hashes.items():
        if digest((ROOT / "fixtures/zetaris" / name).read_bytes()) != expected_hash:
            raise RuntimeError("Original synthetic CSV changed")
    version_names = {key: value.get("version") for key, value in versions.items() if key in ("apiVersion", "driverVersion") and isinstance(value, dict)}
    if not version_names or not all(version_names.values()):
        raise RuntimeError("Serving version was not established")
    config = {"ZETARIS_SQL_ENDPOINT": BASE + "/api/proxy/query/sql/start", "ZETARIS_HEADERS_JSON": json.dumps(headers), "ZETARIS_QUERY_FIELD": "select", "ZETARIS_ROWS_POINTER": "/records", "ZETARIS_DEVICE_TABLE": DATABASE + ".device_evidence", "ZETARIS_SERVER_TABLE": DATABASE + ".server_evidence", "ZETARIS_SOURCE_PREFIX": SOURCE, "ZETARIS_DEPLOYMENT_VERSION": json.dumps(version_names, sort_keys=True)}
    receipt = {"observed_at": datetime.now(timezone.utc).isoformat(), "base_url": BASE,
               "storage": "local Zetaris NDP file store; not S3", "source_prefix": SOURCE,
               "source_hashes": hashes, "original_csv_unchanged": True,
               "registration_statements": existing["registration_statements"] if existing else statements,
               "verification_only": verify_existing,
               "serving_versions": version_names, "joined_rows": rows,
               "query": query, "query_response_sha256": digest(joined.content),
               "aws_write": False, "credentials": "ignored local .env only"}
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    config["ZETARIS_QUERY_OPTIONS_JSON"] = json.dumps({"pageLimit": 3})
    for name, value in config.items():
        # Windows sync/indexing can briefly lock a file against atomic rename.
        # Retry the same local write; never replay source uploads or SQL writes.
        for attempt in range(10):
            try:
                set_key(str(ROOT / ".env"), name, value)
                break
            except PermissionError:
                if attempt == 9:
                    raise RuntimeError("Private connection config is locked; source receipt is saved, rerun with --verify-existing") from None
                time.sleep(0.5)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-existing", action="store_true", help="Read-only verification of already registered synthetic sources; no uploads or SQL DDL")
    seed(parser.parse_args().verify_existing)
