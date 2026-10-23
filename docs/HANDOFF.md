# LastCopy handoff

Current stage: **2 — deterministic supplied-snapshot verifier implemented and
verified**. Prompt 0 persists in AGENTS.md; PRODUCT_SPEC.md remains authoritative.
Next: Prompt 3 only when explicitly requested. No Stage 3+ work was performed.

## Implemented

- Ordered namespace-aware XML comparison, exact meaningful text/attributes,
  explicit formatting whitespace policy, bounded indexed differences.
- Raw snapshot/receipt/connection/scope/history checks; independent filename
  attachment readbacks; all six verdicts with separate preservation and codes.
- Complete captured raw evidence is required for EXPORT_VIEW_ONLY; it never
  becomes an upload candidate. Retained originals identify current edits and
  never schedule an overwrite. Failed requests cannot establish absence.
- Coverage records expected/supplied/missing devices and evidence limitations.
  Missing completion/forms/mappings never become automatic recovery.
- Immutable registered input BLOBs, SQLite run IDs/state/events, output hashes,
  bounded queue/runner, cancellation/deadlines and interrupted-run handling.
- CLI `scripts.run` and POST /run on local port 8000, registered IDs only.
  Findings, receipts, reports and actual JSONL events persist and export.
- Four complete synthetic sample packs plus independent expectations and held-out
  identity/path/repeat controls. No network/providers/models in sample comparison.
- Generated OpenAPI/browser contracts, plan, runtime/format/limits documentation.

## Actual verification

**111 Python tests passed** (one existing non-failing Starlette/httpx warning).
TypeScript typecheck and production build passed. Four meaningful in-memory
mutations each failed the intended test; real source was never left mutated.
All four samples passed both documented CLI and real HTTP entrypoints; report
bytes matched exactly across them. All exported/downloaded hashes and source
immutability checks passed. Queue, cancel/error, interruption, hostile inputs,
limits, evidence integrity and first-request store selection have controls.

See VERIFICATION.md and `verification/stage2-{summary,http,cli,mutations}.json`.
Core source hashes are recorded in the summary receipt. Samples are in
`fixtures/stage2/{stranded,media,export,history}`. See STAGE2.md for exact semantics,
server capture format, API/CLI commands and hard limits.

## Runtime and boundaries

The local API is running at http://127.0.0.1:8000 in Sample mode, with ignored
ledger `private/stage2-complete`. Example saved run: `sample-stranded-41`.
Usual launches from repo root:

```powershell
$env:SAMPLE_MODE='true'
.\.venv\Scripts\python.exe -m uvicorn lastcopy.api:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe -m scripts.run --data-dir private/stage2 run --manifest fixtures/stage2/stranded/run-manifest.json --device fixtures/stage2/stranded/device.zip --server-manifest fixtures/stage2/stranded/server-snapshot.json --server-payload fixtures/stage2/stranded/server-payload.zip --output private/reports/stranded
```

Job completion does not mean preservation success. `with_gaps` and `unresolved`
are distinct from `verified`; coverage is only for supplied scope. Candidate
flags request future review, never execute recovery. Use a new run ID for new
inputs or a new verifier revision; existing run outputs are immutable/idempotent.
After a crash use CLI `resume-queue`; abandoned running jobs become interrupted.

No known Stage 2 blocker remains. Intentional limitations: normalized supplied
capture format only; no automatic native Central exporter, fresh live agent
investigation, recovery writes, advanced media XPath or run-results UI. These
belong to dependent stages or documented unsupported inputs. Cancellation is
cooperative between bounded operations. Supplied hashes do not authenticate
publishers. No erasure authorization or universal Collect/Kobo claim exists.

Stage 1 provider/Collect checks previously passed; see LOCAL_SETUP.md and the
historical receipts. Stage 2 did not rerun or fake those external integrations.
ODK/Zetaris/Nightshift setup is preserved. No imagery, field records, provider
secrets, AWS provisioning or recovery writes were added.

Private repo: https://github.com/miracle352/lastcopy . Never make it public without
user instruction. Existing Vercel URL: https://lastcopy-five.vercel.app/ . It hosts
the diagnostic skeleton; the private evidence backend/run processing is local and
not deployed. Run-results UI is Stage 5; no marketing redesign was performed.
