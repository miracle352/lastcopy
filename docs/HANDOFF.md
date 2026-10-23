# LastCopy handoff

Current stage: **3 implemented; combined live acceptance blocked**. Prompt 0
persists in AGENTS.md. PRODUCT_SPEC.md remains authoritative. Stage 4 requires
another request; no recovery execution was added.

## Working behavior

- Stage 2 verifier remains the only preservation authority; API /run is unchanged.
- Bounded synthetic evidence normalization into six real Zetaris CSV tables.
  Actual anti-join/version/object/media queries supply investigation evidence.
  Raw source objects stay private, unchanged and hash-addressed. This is local
  NDP CSV materialization, not in-place federation or fresh Central acquisition.
- Real pinned World Model bridge: idempotent ingestion, stable external identity,
  append-only hypothesis revisions with retained evidence, revision links and
  graph reads that select the next action. Rebuild uses implemented reference APIs.
- Nightshift action JSON is schema/phase validated. The reviewer requests raw
  evidence and revises the hypothesis. Code compares bytes and seals its report;
  a model cannot turn a conflict into preservation or schedule an overwrite.
- One supervised CLI worker, at most 12 steps/two critique rounds/300 seconds,
  hard cancellation/deadline including blocked sockets, persisted attempt traces,
  output seals, observed sponsor statuses and no automatic provider replay.
- Three complete synthetic packs with independent expectations and a held-out
  variant. Sample and explicit replay compare real inputs offline, with no SQL,
  model/provider calls or fabricated agent logs.

## Actual checks

The full Python suite passed **128 tests** before the final hardening additions;
then the final Stage 3 suite passed **19 tests**, plus a separately passing authenticated-query failure
control (20 Stage 3 controls total). Existing Starlette/httpx deprecation warning remains non-failing.
TypeScript typecheck passed. Pinned World Model: **10 tests and 8 conformance
checks passed**. Three meaningful broken-behavior mutations were each caught by
failing assertions. All three offline CLI packs and one explicit replay passed
literal expectations, source immutability and output-seal verification.

Actual Zetaris: six tables registered; four real scoped queries passed, returning
11 export-gap rows, one device/server version match, three private source-object
references and seven media-reference rows. The connected investigation itself
reached Nightshift, then failed explicitly without substituting sample results.
The observable reviewer/export-guidance and unresolved-conflict branches passed
with named SQLite/model doubles; **they have not passed through live inference**.

See STAGE3.md and verification/stage3-* for commands, actual rows, query IDs/hashes,
limits and receipts. Earlier Stage 2 and Stage 1 results remain in VERIFICATION.md
and LOCAL_SETUP.md; their old inference checks do not substitute for this gate.

## Genuine remaining blocker

Nightshift 1.2.3 returns HTTP 400 `no_provider_configured`: no running text lane or
cloud provider. The existing Llama 1B lane repeatedly failed HTTP 409 memory
admission, including after the user freed memory twice. A separately pinned,
hash-verified Apache-2.0 SmolLM2 360M text model was installed as a smaller optional
lane; it also failed admission. An idle-runtime restart did not clear the refusal
(example: need 1452 MB, reported MemAvailable 2385 MB). Safeguards were preserved.
See MODEL_SOURCES.md for model provenance; no model weights enter Git.

Authenticated inventory advertises three Nemotron routes, but no Nemotron model
was available for a verified inference. **Combined live investigator/reviewer
acceptance and NVIDIA award verification remain blocked.** Neither a routing
alias nor the smaller non-Nemotron model is claimed as Nemotron. Retry the helper
and connected command after Nightshift admits a lane, or configure a real provider
inside Nightshift; do not send keys in chat. A fresh empty attempt directory is
required. Provider outages never silently switch modes.

## Runtime and next action

The temporarily paused ODK containers, local API and web preview were restored.
Health checks returned HTTP 200 for API (Sample mode), web and Central. API uses
its existing private/stage2-complete ledger on port 8000. Nightshift's two text
lanes remain installed but stopped. Source archives, credentials and volumes
were preserved. No imagery, AWS provisioning, field-data upload or recovery write.

See STAGE3.md for exact commands and sponsor architecture. CLI sample example:

```powershell
$env:SAMPLE_MODE='true'
.\.venv\Scripts\python.exe -m scripts.investigate --manifest fixtures/stage3/export-review/run-manifest.json --device fixtures/stage3/export-review/device.zip --server-manifest fixtures/stage3/export-review/server-snapshot.json --server-payload fixtures/stage3/export-review/server-payload.zip --output private/stage3/sample-new
```

For live mode use SAMPLE_MODE=false, a fresh output directory, and --connected.
Add --nemotron only for the explicitly checked award path. Recovery is Stage 4.
The Stage 3 CLI is local; port-8000 health still accurately reports Stage 2.
Private repository: https://github.com/miracle352/lastcopy . Existing Vercel
skeleton: https://lastcopy-five.vercel.app/ . Private backend is not deployed.
Never make the repository public without user instruction.
