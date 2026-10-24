# LastCopy

Independently check which field records and referenced files in surviving device
snapshots have a verified ODK Central copy. Recover only permitted gaps, then read
the server again. **Stages 2-5 are implemented: deterministic verification,
connected investigation and reviewed synthetic recovery with real Central
readback.** No Kobo compatibility promise. See [Stage 4](docs/STAGE4.md) for
the bounded recovery CLI/API, actual acceptance receipts and limitations.
[Stage 5](docs/STAGE5.md) documents the working local UI, uploads, saved results,
evidence and reviewed recovery flow.

The repository is private by user request. Deployment serves the diagnostic web
skeleton only. The single-user evidence API and private files stay local; the
Vercel page reports the backend as unavailable rather than fabricating a result.

[Vercel skeleton](https://lastcopy-five.vercel.app/) Â·
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

The dedicated local Central test server is now verified. Its guarded setup,
Nightshift/Collect verification evidence and rerun steps are documented in
[local integration setup](docs/LOCAL_SETUP.md).

## Architecture and boundaries

- Next.js/TypeScript: simple web skeleton and local same-origin API proxy.
- Python/FastAPI, port 8000: bounded ZIP/XML/media comparisons and registered jobs.
- Private immutable registered input bytes and SQLite run/receipt persistence.
- Node/TypeScript bridge: the actual vendored Meterless World Model reference,
  pinned and independently conformance-tested. Not an invented hosted endpoint.
- Connected data layer: local Zetaris 2.4.3.1 is installed and its bounded
  two-CSV join is verified. AWS Quickstart is verified but no compute cluster
  exists. Nightshift CPU text inference is verified separately. Stage 2 does not
  call these providers; connected agent orchestration is Stage 3.

No hosted database, auth SaaS, GPU provisioning, S3/IAM changes or cloud infrastructure
creation. No AI-generated imagery. Fixture media is original synthetic binary/text data. Source XML and archive bytes remain unchanged.

Read the [full prompt packet](LASTCOPY_CODEX_PROMPTS.md),
[Product Contract](docs/PRODUCT_SPEC.md), [file-by-file plan](docs/superpowers/plans/2026-10-23-lastcopy.md),
[compatibility boundary](docs/COMPATIBILITY.md), [actual verification](docs/VERIFICATION.md),
and [handoff and blockers](docs/HANDOFF.md). Stages 3–7 require separate instructions. [Licensing and upstream provenance](docs/ASSET_SOURCES.md).

Stage 1 blocker resolution: Nightshift CPU text inference and an actual synthetic
Collect v2026.3.5 emulator export now pass. See [compatibility](docs/COMPATIBILITY.md)
and [verification](docs/VERIFICATION.md) for scope, exact receipts and remaining
future compatibility limits. The original unknown-version sample is unchanged.

## Stage 2: run the deterministic offline verifier

The CLI and local API run the same comparator on immutable registered inputs.
Sample mode makes no external service, SQL or model calls. A completed run can
still have gaps or unknowns; coverage and preservation are separate result fields.

```powershell
$env:SAMPLE_MODE='true'
.\.venv\Scripts\python.exe -m scripts.run --data-dir private/stage2 run --manifest fixtures/stage2/stranded/run-manifest.json --device fixtures/stage2/stranded/device.zip --server-manifest fixtures/stage2/stranded/server-snapshot.json --server-payload fixtures/stage2/stranded/server-payload.zip --output private/reports/stranded
.\.venv\Scripts\python.exe -m scripts.run --data-dir private/stage2 status sample-stranded-41
```

Replace `stranded` with `media`, `export` or `history` for the other complete
samples. Each includes independently authored `expected.json`. Output contains
`report.json`, `findings.json`, `receipts.json` and actual local `events.jsonl`.
Matching run IDs are idempotent; different inputs require a new run ID.
`completed` means the job finished, not that every record was preserved.

Start the API on port 8000 as above, then verify all four samples through real HTTP:

```powershell
.\.venv\Scripts\python.exe -m scripts.verify_stage2_http
```

Register raw device ZIPs at `POST /inputs/device`, RunManifest JSON at
`POST /inputs/manifest`, and the two-file server transport ZIP at
`POST /inputs/server`. `POST /run` accepts **only registered input IDs**.
See [Stage 2 contracts, HTTP examples and limits](docs/STAGE2.md) and
[the handoff](docs/HANDOFF.md). The existing web page still inventories samples;
the run-results interface is Stage 5. Private evidence processing is not deployed
on Vercel. No recovery writes occur in Stage 2.


## Stage 3 investigation

The bounded scripts.investigate CLI adds scoped Zetaris evidence queries, pinned World Model graph revisions and schema-validated Nightshift investigator/reviewer actions. The deterministic verifier owns verdicts. Three synthetic capture packs have independent expectations and a held-out variant. Sample/replay make no provider calls.

See [architecture, commands and limits](docs/STAGE3.md) and [actual acceptance/blockers](docs/HANDOFF.md). Inventory advertising alone does not verify the NVIDIA award path.
