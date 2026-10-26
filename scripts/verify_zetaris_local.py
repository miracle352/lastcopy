"""Real local login/query check using the official bundle verifier's HTTP contract.

No source registration or AWS access. Secrets never enter receipts or stdout.
"""
import json
import subprocess
import time
import uuid
from datetime import datetime, timezone
from dotenv import dotenv_values
import httpx
from lastcopy.config import ROOT
from lastcopy.inventory import digest
from .setup_zetaris_local import BUNDLE, PROJECT

BASE = "http://localhost:3130"
SQL = "select 7 as seven"


def checked(client, method, path, **kwargs):
    response = client.request(method, BASE + path, **kwargs)
    if response.status_code != 200:
        raise RuntimeError(f"Local Zetaris {method} returned HTTP {response.status_code}; body suppressed")
    return response


def connect(client):
    prepared = json.loads((BUNDLE / "lastcopy-prepared.json").read_text())
    config = dotenv_values(BUNDLE / ".env")
    if prepared.get("project") != PROJECT or config.get("GUI_URL") != BASE:
        raise RuntimeError("Local bundle identity changed; not sending credentials")
    # Confirm this is our actual running image/project before sending credentials.
    for service, image_key in (('ui','UI_IMAGE'),('driver','DRIVER_IMAGE')):
        raw = subprocess.check_output(["docker", "compose", "ps", "--format", "json", service], cwd=BUNDLE, text=True,timeout=15)
        running = json.loads(raw or '{}')
        if isinstance(running, list):running = running[0] if len(running)==1 else {}
        if (running.get('Project') != PROJECT or running.get('State') != 'running'
                or running.get('Image') != prepared['images'][image_key]
                or running.get('Health') in ('unhealthy','starting')):
            raise RuntimeError(f'The expected isolated local Zetaris {service} is not ready; no credentials sent')
    login = checked(client, "POST", "/api/auth/login", json={"username": config["ZETARIS_ADMIN_EMAIL"], "password": config["ZETARIS_ADMIN_PASSWORD"]}).json()
    token = login.get("idToken") or login.get("token") or login.get("accessToken")
    org_id = login.get("orgId")
    if not isinstance(token, str) or not token or not str(org_id).isdecimal():
        raise RuntimeError("Actual local login response does not match the official verifier contract")
    return {"Authorization": "Bearer " + token, "X-Org-ID": str(org_id), "X-Request-ID": str(uuid.uuid4())}


def verify():
    start = time.monotonic()
    with httpx.Client(timeout=90, follow_redirects=False, trust_env=False) as client:
        headers = connect(client)
        response = checked(client, "POST", "/api/proxy/query/sql/start", headers=headers, json={"select": SQL, "pageLimit": 5})
    result = response.json()
    # The official verifier checks for the named 'seven' cell, not mere reachability.
    def cells(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "seven" and child in ("7", 7):
                    yield {"seven": child}
                else:
                    yield from cells(child)
        elif isinstance(value, list):
            for child in value:
                yield from cells(child)
    rows = list(cells(result))
    directory = ROOT / "private/smoke"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "zetaris-local-query-response.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if rows != [{"seven": "7"}] and rows != [{"seven": 7}]:
        raise RuntimeError("Real query did not return the expected single named cell; private response retained")
    receipt = {"provider": "zetaris", "check": "local_installation_login_and_constant_query",
               "observed_at": datetime.now(timezone.utc).isoformat(), "status": "PASS",
               "base_url": BASE, "sql": SQL, "rows": rows,
               "response_sha256": digest(response.content),
               "elapsed_ms": round((time.monotonic() - start) * 1000, 2),
               "two_source_evidence_smoke_passed": False, "aws_launch": False}
    (directory / "zetaris-local-installation.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    verify()
