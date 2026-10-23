"""Prepare the official pinned Central checkout for a loopback-only synthetic test.

Does not start Docker or touch AWS. Run the documented Compose command afterward.
"""
from pathlib import Path
import json
import subprocess
from lastcopy.config import ROOT

CENTRAL_COMMIT = "7d6de621955c5bb6a68e098ca10c9cbb92285cdf"
CENTRAL_RELEASE = "v2026.3.1"


def prepare():
    checkout = ROOT / "private/central"
    actual = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
    if actual != CENTRAL_COMMIT:
        raise SystemExit("Central checkout differs from the reviewed release pin")
    config = """DOMAIN=localhost
SYSADMIN_EMAIL=lastcopy@example.invalid
SSL_TYPE=upstream
HTTP_PORT=8384
HTTPS_PORT=8444
SENTRY_TRACE_RATE=0
"""
    override = """# Local synthetic testing only. Never use this override for a public server.
services:
  nginx:
    # Docker Desktop does not publish ports from an internal-only network.
    # Only nginx joins the host-facing bridge; application/data services do not.
    networks: [default, loopback]
    # Upstream nginx resolves its default CSP-report sink at startup. Keep
    # that sink inside the container while the test network has no egress.
    extra_hosts:
      - "o130137.ingest.sentry.io:127.0.0.1"
    ports: !override
      - 127.0.0.1:8384:80
    restart: "no"
  service:
    restart: "no"
  postgres14:
    restart: "no"
  mail:
    restart: "no"
  pyxform:
    restart: "no"
  enketo:
    restart: "no"
  enketo_redis_main:
    restart: "no"
  enketo_redis_cache:
    restart: "no"
networks:
  default:
    internal: true
  loopback: {}
"""
    for name, content in ((".env", config), ("lastcopy.local.yml", override)):
        path = checkout / name
        if path.exists() and path.read_text() != content:
            raise SystemExit(f"Refusing to overwrite existing differing {name}")
        path.write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps({"release": CENTRAL_RELEASE, "commit": actual, "project": "lastcopy-odk", "base_url": "http://localhost:8384", "public_access": False, "runtime_network": "internal services; nginx-only host bridge", "started": False}, indent=2))


def initialize_fresh_database():
    marker = ROOT / "private/central/files/allow-postgres14-upgrade"
    if marker.exists():
        return
    # Upstream test/test-images.sh creates this required build marker. Only do
    # that automatically for our isolated stack with no prior containers/volumes.
    for resource in ("volume", "container"):
        command = ["docker", resource, "ls"]
        if resource == "container":
            command.append("--all")
        command.extend(["--filter", "label=com.docker.compose.project=lastcopy-odk", "--quiet"])
        existing = subprocess.check_output(command, text=True).strip()
        if existing:
            raise SystemExit("Existing LastCopy test database resources need manual upgrade review; marker not created")
    marker.write_text("Fresh isolated LastCopy synthetic test stack; no legacy database.\n", encoding="utf-8", newline="\n")
    print("Created upstream PostgreSQL build marker for verified empty test stack")


if __name__ == "__main__":
    prepare()
    initialize_fresh_database()
