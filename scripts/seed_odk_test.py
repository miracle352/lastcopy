"""Seed only our pinned loopback Central stack; never accepts a remote target.

This is synthetic test setup, not an application recovery implementation.
Secrets are generated locally, passed on stdin, and stored only in ignored .env.
"""
import json
import secrets
import subprocess
from pathlib import Path
from urllib.parse import quote
import httpx
from dotenv import dotenv_values, set_key
from lastcopy.config import ROOT
from lastcopy.inventory import digest
from .setup_odk_test import CENTRAL_COMMIT, CENTRAL_RELEASE

CHECKOUT = ROOT / "private/central"
BASE = "http://localhost:8384"
PROJECT_NAME = "LastCopy synthetic Stage 1"
EMAIL = "lastcopy-test@example.invalid"
COMPOSE = ["docker", "compose", "-p", "lastcopy-odk", "-f", "docker-compose.yml", "-f", "lastcopy.local.yml"]


def docker_admin(command, password=None):
    result = subprocess.run(COMPOSE + ["exec", "-T", "service", "odk-cmd", "--email", EMAIL, command], cwd=CHECKOUT, input=(password + "\n") if password else None, text=True, capture_output=True, timeout=60)
    # Do not print captured stdout/stderr: command prompts and service diagnostics
    # are not a safe secret boundary.
    if result.returncode:
        raise RuntimeError(f"Local ODK admin command failed: {command}; exit {result.returncode}")


def checked(client, method, path, **kwargs):
    response = client.request(method, BASE + path, **kwargs)
    if response.status_code >= 300:
        raise RuntimeError(f"Synthetic ODK setup {method} failed with HTTP {response.status_code}; response SHA256 {digest(response.content)}")
    return response


def seed():
    if subprocess.check_output(["git", "-C", str(CHECKOUT), "rev-parse", "HEAD"], text=True).strip() != CENTRAL_COMMIT:
        raise RuntimeError("Local Central checkout pin changed")
    fixture = ROOT / "fixtures/representative"
    source_zip_hash = digest((fixture / "device.zip").read_bytes())
    manifest = json.loads((fixture / "device/device-manifest.json").read_text())
    if manifest.get("synthetic") is not True:
        raise RuntimeError("Refusing non-synthetic fixture")
    env_path = ROOT / ".env"
    config = dotenv_values(env_path) if env_path.exists() else {}
    if config.get("ODK_BASE_URL") not in (None, "", BASE):
        raise RuntimeError("Existing ODK connection is not this local test stack; not modifying it")
    if config.get("ODK_EMAIL") not in (None, "", EMAIL):
        raise RuntimeError("Existing local ODK account is not our synthetic account; not modifying it")
    with httpx.Client(timeout=30, follow_redirects=False, trust_env=False) as client:
        # Read the actual version served by this exact checkout before seeding.
        version_text = checked(client, "GET", "/version.txt").text
        if CENTRAL_COMMIT not in version_text:
            raise RuntimeError("Central served version does not match the reviewed checkout")
        password = config.get("ODK_PASSWORD")
        if not password:
            password = secrets.token_urlsafe(32)
            if not env_path.exists():
                env_path.write_text("# LastCopy local configuration. Never commit.\nSAMPLE_MODE=true\n", encoding="utf-8")
            set_key(str(env_path), "ODK_PASSWORD", password)
        existing_login = client.post(BASE + "/v1/sessions", json={"email": EMAIL, "password": password})
        if existing_login.status_code == 401:
            docker_admin("user-create", password)
        elif existing_login.status_code != 200:
            raise RuntimeError(f"Local ODK login preflight returned HTTP {existing_login.status_code}")
        docker_admin("user-promote")
        token = checked(client, "POST", "/v1/sessions", json={"email": EMAIL, "password": password}).json()["token"]
        client.headers["Authorization"] = "Bearer " + token
        projects = checked(client, "GET", "/v1/projects").json()
        matches = [project for project in projects if project.get("name") == PROJECT_NAME]
        if len(matches) > 1:
            raise RuntimeError("Ambiguous synthetic test project")
        project = matches[0] if matches else checked(client, "POST", "/v1/projects", json={"name": PROJECT_NAME}).json()
        project_id = project["id"]
        form_bytes = (fixture / "device" / manifest["form_definitions"][0]["xml_path"]).read_bytes()
        form_id = "inspection"
        forms_path = f"/v1/projects/{project_id}/forms"
        forms = checked(client, "GET", forms_path).json()
        if not any(form.get("xmlFormId") == form_id for form in forms):
            checked(client, "POST", forms_path + "?publish=true", content=form_bytes, headers={"Content-Type": "application/xml"})
        elif checked(client, "GET", forms_path + "/inspection.xml").content != form_bytes:
            raise RuntimeError("Existing synthetic form bytes differ; refusing overwrite")
        instance = (fixture / "device" / manifest["instances"][0]["xml_path"]).read_bytes()
        from lastcopy.inventory import parse_xml
        from lastcopy.config import Settings
        instance_id = parse_xml(instance, Settings({})).findtext("./{*}meta/{*}instanceID")
        scope = forms_path + "/inspection/submissions/" + quote(instance_id, safe="")
        existing = client.get(BASE + scope + ".xml")
        media_path = fixture / "device/projects/field-a/instances/inspection_001/sample.txt"
        if existing.status_code == 404:
            # Native documented OpenRosa upload, preserving original identity and bytes.
            checked(client, "POST", f"/v1/projects/{project_id}/submission", files={"xml_submission_file": ("inspection-final.xml", instance, "application/xml"), "sample.txt": ("sample.txt", media_path.read_bytes(), "text/plain")}, headers={"X-OpenRosa-Version": "1.0"})
        elif existing.status_code != 200 or existing.content != instance:
            raise RuntimeError("Existing synthetic submission differs or is unreadable; refusing overwrite/retry")
        current = checked(client, "GET", scope + ".xml").content
        media = checked(client, "GET", scope + "/attachments/sample.txt").content
        if current != instance or media != media_path.read_bytes():
            raise RuntimeError("Synthetic seed readback mismatch")
    settings = {"ODK_BASE_URL": BASE, "ODK_EMAIL": EMAIL, "ODK_PROJECT_ID": str(project_id), "ODK_FORM_ID": form_id, "ODK_SUBMISSION_ID": instance_id, "ODK_VERSION_ID": instance_id, "ODK_ATTACHMENT_NAME": "sample.txt", "ODK_CENTRAL_VERSION": CENTRAL_RELEASE, "ODK_TEST_PROJECT": "true"}
    for key, value in settings.items():
        set_key(str(env_path), key, value)
    if digest((fixture / "device.zip").read_bytes()) != source_zip_hash:
        raise RuntimeError("Original source archive changed")
    receipt = {"operation": "local_synthetic_test_setup", "central_release": CENTRAL_RELEASE, "central_commit": CENTRAL_COMMIT, "version_evidence_sha256": digest(version_text.encode()), "target": BASE, "project_id": project_id, "form_id": form_id, "instance_id": instance_id, "xml_sha256": digest(current), "attachment_sha256": digest(media), "source_archive_unchanged": True, "credentials": "ignored local .env only", "recovery_feature_implemented": False}
    output = ROOT / "private/smoke/odk-setup.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    seed()
