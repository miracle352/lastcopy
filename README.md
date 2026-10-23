# LastCopy

Independently check which field records and referenced files in surviving device
snapshots have a verified ODK Central copy. Recover only permitted gaps, then read
the server again. **Stage 1 development skeleton; preservation/recovery is not
implemented or live-verified yet.** No Kobo compatibility promise.

The repository is private by user request. Deployment serves the diagnostic web
skeleton only. The single-user evidence API and private files stay local; the
Vercel page reports the backend as unavailable rather than fabricating a result.

[Vercel skeleton](https://lastcopy-five.vercel.app/) ·
[Private repository](https://github.com/miracle352/lastcopy)

## Setup (Windows PowerShell)

Tested with Node 24.12.0 and Python 3.13.7. Use Node 24 LTS and Python 3.13.
All commands below run from this repository root.

```powershell
npm ci
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
Copy-Item .env.example .env
```

Terminal 1:

```powershell
.\.venv\Scripts\python.exe -m uvicorn lastcopy.api:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
npm run dev
```

Open [the local skeleton](http://127.0.0.1:3000). Click **Validate sample archive**
to inventory the real bundled ZIP. It makes no external/provider/model calls.
API process health is [on port 8000](http://127.0.0.1:8000/health);
`GET /configuration` returns missing variable names and redacted validation errors.
Health means the process is up, not that integrations or preservation passed.

For macOS/Linux replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.
Do not use a publicly accessible bind address for the private API.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.build_fixture
.\.venv\Scripts\python.exe -m scripts.inventory fixtures/representative/device.zip
.\.venv\Scripts\python.exe -m scripts.validate_snapshot fixtures/representative/server-snapshot.json fixtures/representative/server-payload.zip
.\.venv\Scripts\python.exe -m scripts.export_contracts
npm run contracts
npm run typecheck
npm run smoke:world-model
npm run test:world-model
npm run conformance:world-model
npm run build
```

`lastcopy/models.py` is the authoritative domain/API schema. Pydantic exports
`contracts/openapi.json`; openapi-typescript generates `web/lib/api.generated.ts`.
The browser imports generated types. Regeneration must produce no tracked diff.

Read-only external smokes (blocked without explicit configuration):

```powershell
.\.venv\Scripts\python.exe -m scripts.smoke zetaris
.\.venv\Scripts\python.exe -m scripts.smoke nightshift
.\.venv\Scripts\python.exe -m scripts.smoke odk
```

Exit 0 means the probe passed; exit 2 means blocked or failed. Receipts go to
ignored `private/smoke/`. Sample mode blocks all external smokes before networking.
To run connected probes, configure `.env` using [integration instructions](docs/INTEGRATIONS.md)
and set `SAMPLE_MODE=false`. Never paste secrets into chat or commit `.env`.
Run each probe separately when budgeting cold-load time.

## Architecture and boundaries

- Next.js/TypeScript: simple web skeleton and local same-origin API proxy.
- Python/FastAPI, port 8000: bounded ZIP/XML inventory and domain schemas.
- Private immutable files and, from Stage 2, SQLite run/receipt persistence.
- Node/TypeScript bridge: the actual vendored Meterless World Model reference,
  pinned and independently conformance-tested. Not an invented hosted endpoint.
- Connected data layer: existing Zetaris AWS deployment; Nightshift is the
  planned primary AI provider. Neither is labelled integrated until live checks pass.

No hosted database, auth SaaS, GPU provisioning, S3/IAM changes or infrastructure
creation. No AI-generated imagery. The only fixture media is original synthetic
text. Source XML and archive bytes remain unchanged.

Read the [full prompt packet](LASTCOPY_CODEX_PROMPTS.md),
[Product Contract](docs/PRODUCT_SPEC.md), [file-by-file plan](docs/superpowers/plans/2026-10-23-lastcopy.md),
[compatibility boundary](docs/COMPATIBILITY.md), [actual verification](docs/VERIFICATION.md),
and [handoff and blockers](docs/HANDOFF.md). Later stages are not implemented by
this initial skeleton. [Licensing and upstream provenance](docs/ASSET_SOURCES.md).
