"""Configure only the inspected official bundle; no image pull, start or AWS call."""
import json
import secrets
import string
import subprocess
from pathlib import Path
from dotenv import dotenv_values, set_key
from lastcopy.config import ROOT

PROJECT = "lastcopy-zetaris"
BUNDLE = ROOT / "private/zetaris-install/zetaris-platform"


def prepare():
    marker = BUNDLE / "lastcopy-prepared.json"
    if marker.exists():
        print(marker.read_text())
        return
    # A different installation must never inherit newly generated credentials.
    for resource in ("volume", "container"):
        args = ["docker", resource, "ls"]
        if resource == "container":
            args.append("--all")
        args += ["--filter", f"label=com.docker.compose.project={PROJECT}", "--quiet"]
        if subprocess.check_output(args, text=True).strip():
            raise SystemExit("Existing local Zetaris resources require review; not changing credentials")
    env = BUNDLE / ".env"
    values = dotenv_values(env)
    images = {key: values.get(key, "") for key in ("DRIVER_IMAGE", "API_IMAGE", "UI_IMAGE")}
    if not all(value.startswith("zetarishackathon.azurecr.io/") for value in images.values()):
        raise SystemExit("Unexpected distribution image registry")
    backup = BUNDLE / ".env.vendor-original"
    if backup.exists():
        raise SystemExit("Preparation was interrupted; review private configuration before retrying")
    backup.write_bytes(env.read_bytes())
    def password():
        return "Aa9@" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(36))
    settings = {
        "COMPOSE_PROJECT_NAME": PROJECT,
        "COMPOSE_PROFILES": "",
        "ZETARIS_ADMIN_EMAIL": "lastcopy-admin@example.invalid",
        "ZETARIS_ADMIN_ORG": "lastcopy",
        "ZETARIS_ADMIN_PASSWORD": password(),
        "POSTGRES_PASSWORD": password(),
        "ZSPARK_DRIVER_MEM": "2g",
        "ZSPARK_DRIVER_CORES": "2",
        "ZSPARK_MASTER_URL": "local[2]",
        "ZETARIS_API_MAX_HEAP": "1g",
        "UI_PORT": "127.0.0.1:3130",
        "GUI_URL": "http://localhost:3130",
        "ALLOWED_ORIGINS": "http://localhost:3130",
        "API_PORT": "18888",
        "API_INTERNAL_PORT": "18889",
        "DRIVER_PORT": "11000",
        "SPARK_UI_PORT": "14040",
        "TELEMETRY_ENABLED": "false",
    }
    # Password alphabet deliberately excludes shell interpolation/quoting characters;
    # the vendor verifier reads literal unquoted .env values with sed.
    for key, value in settings.items():
        set_key(str(env), key, value, quote_mode="never")
    override = """# Private local evaluation only. No AWS services are created.
services:
  postgres:
    ports: !reset []
    restart: "no"
  driver:
    ports: !override
      - "127.0.0.1:11000:10000"
      - "127.0.0.1:14040:4040"
    restart: "no"
  api:
    ports: !override
      - "127.0.0.1:18888:8888"
    restart: "no"
  ui:
    restart: "no"
"""
    (BUNDLE / "compose.override.yaml").write_text(override, encoding="utf-8", newline="\n")
    # Never emit resolved Compose config: it contains passwords and the vendor key.
    subprocess.run(["docker", "compose", "config", "--quiet"], cwd=BUNDLE, check=True)
    result = subprocess.run(["docker", "compose", "config", "--format", "json"], cwd=BUNDLE, check=True, capture_output=True, text=True)
    services = json.loads(result.stdout)["services"]
    ports = []
    for name, service in services.items():
        if service.get("profiles"):
            continue
        for port in service.get("ports", []):
            if port.get("host_ip") != "127.0.0.1":
                raise SystemExit("Non-loopback published port; not prepared")
            ports.append({"service": name, "host": port["host_ip"], "port": port["published"]})
    receipt = {"project": PROJECT, "base_url": "http://localhost:3130", "images": images,
               "published_ports": ports, "config_valid": True, "started": False,
               "credentials": "ignored bundle .env only", "aws_launch": False}
    marker.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(marker.read_text())


if __name__ == "__main__":
    prepare()
