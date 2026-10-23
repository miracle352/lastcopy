"""Connect to the newly installed local runtime without displaying its token."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import httpx
from dotenv import set_key
from lastcopy.config import ROOT


def configure():
    state = Path(os.environ["LOCALAPPDATA"]) / "ai.meterless.runtime"
    token_path = state / "proxy-token"
    if not token_path.is_file():
        raise SystemExit("Nightshift has not created its runtime token yet; start the official app first")
    token = token_path.read_text(encoding="utf-8").strip()
    if not token or token == "rt-local":
        raise SystemExit("Nightshift runtime token is not usable")
    base = "http://127.0.0.1:8088/v1"
    headers = {"Authorization": "Bearer " + token, "meterless-app": "lastcopy"}
    with httpx.Client(timeout=10, trust_env=False, follow_redirects=False) as client:
        wrong = client.get(base + "/models", headers={**headers, "Authorization": "Bearer lastcopy-deliberately-invalid-smoke-token"})
        if wrong.status_code not in (401, 403):
            raise SystemExit("Runtime did not reject a wrong token; not configuring this endpoint")
        response = client.get(base + "/models", headers=headers)
        if response.status_code != 200:
            raise SystemExit(f"Authenticated Nightshift inventory failed with HTTP {response.status_code}")
        routes = [entry["id"] for entry in response.json().get("data", []) if isinstance(entry.get("id"), str)]
        if "meterless/auto" not in routes:
            raise SystemExit("Documented auto route not in actual inventory; explicit route selection needed")
    env_path = ROOT / ".env"
    if not env_path.exists():
        env_path.write_text("# LastCopy private local settings. Never commit.\nSAMPLE_MODE=true\n", encoding="utf-8")
    for name, value in {"NIGHTSHIFT_BASE_URL": base, "NIGHTSHIFT_TOKEN": token, "NIGHTSHIFT_ROUTE": "meterless/auto"}.items():
        set_key(str(env_path), name, value)
    receipt = {"observed_at": datetime.now(timezone.utc).isoformat(), "base_url": base, "wrong_token_http_status": wrong.status_code, "authenticated_inventory_http_status": response.status_code, "routes": routes, "selected_route": "meterless/auto", "inference_verified": False, "token": "redacted; saved only in ignored local .env"}
    directory = ROOT / "private/smoke"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "nightshift-inventory.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    configure()
