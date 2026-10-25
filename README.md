# LastCopy

For this PC: [which folder, which terminal, and exact launch commands](docs/RUN_LOCALLY.md).
The current redesign and verification follow-up is documented in [REDESIGN.md](docs/REDESIGN.md).
The latest connected entry flow and automatic examples are documented in
[PRODUCT_FLOW.md](docs/PRODUCT_FLOW.md).

Bring every record home. LastCopy compares surviving ODK Collect project exports
with scoped ODK Central evidence, explains gaps, stages a reviewed recovery, and
reads the server again before calling the checked copy preserved.

Deterministic Python code owns identities, ordered XML/repeat comparison, media
slots, hashes and final verdicts. The investigator can request evidence and revise
hypotheses; it cannot change a verifier result. This is a single-user local tool,
not a promise that every historic export or Kobo installation is supported.

## Windows setup and production launch

Windows runtime tested: **Python 3.13.7, Node 24.12.0, Next 16.4.3**.
The updated local image uses **Python 3.13.17 and Node 24.22.1** security releases. Docker Desktop is
optional for samples; real local Central/Zetaris use their separate existing
stacks. Run all commands from this repository root in PowerShell.

```powershell
npm ci
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
Copy-Item .env.example .env  # first setup only; never overwrite existing secrets
npm run build
```

Terminal 1 (this PC's existing configured local connection):

```powershell
$env:SAMPLE_MODE='false'
$env:LASTCOPY_DATA_DIR='private/application'
.\.venv\Scripts\python.exe -m uvicorn lastcopy.api:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
npm run start
```

Open [LastCopy](http://127.0.0.1:3000) or [the check flow](http://127.0.0.1:3000/app).
The normal entry opens **My records** and reads the configured Central project
and form. Connected mode requires the existing local Central/Zetaris services
and Nightshift plus private server-side settings; a fresh clone has no credentials.
The configured Central project is a synthetic test environment. Your own campaign
has not been checked without its exports. See [the local guide](docs/RUN_LOCALLY.md).

For a completely offline installation, change the first terminal's SAMPLE_MODE
to 'true' and LASTCOPY_DATA_DIR to 'private/offline-examples'. Choose **Try example
records**, inspect evidence, prepare a permitted bundle and compare the explicitly
offline readback example. Sample comparisons make no provider calls or uploads.
Local assets/fonts require no internet. Installation and the optional font rebuild
do require downloads. For macOS/Linux use
`.venv/bin/python` instead of `.venv\Scripts\python.exe`.

For development only, replace `npm run start` with `npm run dev`. Production
performance measurements use `npm run build` followed by `npm run start`.

## CLI and API

The same comparator is available without the browser:

```powershell
$env:SAMPLE_MODE='true'
.\.venv\Scripts\python.exe -m scripts.run --data-dir private/cli run --manifest fixtures/stage2/media/run-manifest.json --device fixtures/stage2/media/device.zip --server-manifest fixtures/stage2/media/server-snapshot.json --server-payload fixtures/stage2/media/server-payload.zip --output private/cli-report
```

Outputs: `report.json`, `findings.json`, `receipts.json`, `events.jsonl`; source
ZIP/XML/media remain unchanged. Repeated identical exports are idempotent;
conflicting export contents are not overwritten. See [sample IO](docs/SAMPLE_IO.md).

The API accepts registered IDs, never arbitrary filesystem paths:

```powershell
$api='http://127.0.0.1:8000'
$draft=Invoke-RestMethod -Method Post "$api/ui/samples/media"
Invoke-RestMethod -Method Post "$api/ui/runs/$($draft.run_id)/start"
for ($attempt=0; $attempt -lt 150; $attempt++) {
  $check=Invoke-RestMethod "$api/ui/runs/$($draft.run_id)"
  if ($check.status.state -notin @('queued','running')) { break }
  Start-Sleep -Milliseconds 200
}
if ($check.status.state -ne 'completed') { throw 'Check did not complete; inspect its saved state' }
Invoke-WebRequest "$api/ui/runs/$($draft.run_id)/downloads/report.txt" -OutFile report.txt
```

For custom clients: POST raw bytes to `/inputs/device`, `/inputs/manifest` and
`/inputs/server`; the last is a ZIP containing `server-snapshot.json` plus
`server-payload.zip`. POST `/run` with `manifest_id`, `device_input_ids` and
`server_input_id`. GET `/runs/{id}`, `/runs/{id}/events` and
`/runs/{id}/artifacts/report.json`. See the generated
[OpenAPI contract](contracts/openapi.json). `/health` proves process health only.

## Connected mode and recovery

Configure server-side `.env` using [integration setup](docs/INTEGRATIONS.md) and
[local setup](docs/LOCAL_SETUP.md), set `SAMPLE_MODE=false`, and restart the API.
Keep keys out of browser storage and Git. The supplied `.env.example` contains
placeholders only. Reuse existing Zetaris; no AWS provisioning is required.

The UI accepts device ZIPs, an explicit expected-device roster and a scoped
snapshot or the configured Central read connection. Connected investigation uses
actual scoped Zetaris rows, the pinned Meterless World Model reference and real
Nightshift inference. Normalized small CSV evidence manifests are the current
architecture, not heterogeneous in-place federation. See
[architecture and sponsor use](docs/ARCHITECTURE.md).

Apply requires review of the configured dedicated synthetic test target, fresh
precondition readback and a supported missing-submission/media operation. XML
conflicts and unsupported history writes remain manual. POST success alone is
not preservation. [Recovery commands and constraints](docs/STAGE4.md).

## Docker

```powershell
docker compose build
docker compose up -d
# Open http://127.0.0.1:3000
# Stop without deleting evidence:
docker compose stop
```

Stop host services using ports 3000/8000 first. One non-root container runs the
same API and production UI with a shared loopback connection; Docker publishes
only to host loopback. Evidence persists in the named volume. Do not run
`down -v` unless you intentionally want to destroy that volume. Container binds
are internal `0.0.0.0` so Docker can forward its loopback host ports. The default
is Sample only; no credentials or private evidence enter the image build context.
Compose does not disable host internet. The audit's explicit process fences are
documented in [Stage 7](docs/STAGE7.md). Connected container networking needs a
separately reviewed setup; do not replace private provider URLs with guessed
public endpoints. Docker build/runtime check status is recorded in the handoff.

## Verification and submission preparation

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.export_contracts
npm run contracts
npm run typecheck
npm run test:world-model
npm run conformance:world-model
npm run build
npm audit
```

Regenerating contracts must produce no domain/client drift. Pinned audit and
browser commands, production performance results, failures and limitations are
in [Stage 7](docs/STAGE7.md) and [HANDOFF](docs/HANDOFF.md).

[Product Contract](docs/PRODUCT_SPEC.md) · [compatibility](docs/COMPATIBILITY.md) ·
[limitations](docs/LIMITATIONS.md) · [demo script](docs/DEMO_SCRIPT.md) ·
[pitch outline](docs/PITCH_DECK.md) · [deployment instructions](docs/DEPLOYMENT.md).
No automatic publishing, visibility change or event submission is authorized.
The existing Vercel preview has no private API; local workflows are the working
product. The repository remains private until its owner chooses otherwise.

## Licensing and new work

LastCopy first-party code is MIT licensed. Meterless World Model is vendored
Apache-2.0 at the recorded upstream commit, unchanged except the documented
AGENTS-to-SPEC filename. Fonts retain their OFL licenses. Runtime dependencies
retain their licenses. [Asset and upstream attribution](docs/ASSET_SOURCES.md).
LastCopy adds the verifier, bounded evidence adapters/investigator, graph bridge,
recovery state machine, persistence, CLI/API/UI, fixtures and regression tests.
Development used Codex desktop on Windows, not Cursor. All bundled field/media
examples are synthetic, including the actual Collect emulator capture. No
community-user recordings or AI-generated imagery are included.
