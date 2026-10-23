"""Probe only official loopback Nightshift candidates; never reads a token."""
import json
import httpx


if __name__ == "__main__":
    results = []
    with httpx.Client(timeout=1, follow_redirects=False, trust_env=False) as client:
        for port in (8088, 8090, 8787, 11434):
            base = f"http://127.0.0.1:{port}"
            try:
                response = client.get(base + "/v1/models", headers={"meterless-app": "lastcopy"})
                results.append({"base_url": base + "/v1", "http_status": response.status_code, "authenticated": False})
            except httpx.RequestError:
                results.append({"base_url": base + "/v1", "reachable": False})
    print(json.dumps(results, indent=2))
