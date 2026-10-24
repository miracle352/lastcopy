# LastCopy handoff

Current stage: **5 implemented; real production-browser flow verified (2026-10-24)**.
Prompt 0 persists in AGENTS.md; PRODUCT_SPEC.md is authoritative. Stage 6 requires
a new request. The private/local backend is not deployed to Vercel.

## Stage 5 outcome

Implemented `/` introduction, `/app` upload/sample/roster/capture flow and
`/runs/[id]` persisted investigation/evidence/report/recovery. The frontend uses a
bounded allowlisted local API proxy and generated Python/OpenAPI TypeScript
contracts. No screenshot UI, hardcoded successful verdict, browser credential or
AI-generated imagery. Existing light-tool styling is retained; Stage 6 polish is
not included. API health reports stage 5.

The four steps work: Add exports -> Check copies -> Review gaps -> Verify recovery.
Saved input selections and plan attempts survive reload. Actual comparator events
drive progress/cancellation. Modal evidence includes original files, meaningful XML
paths/occurrences and device/server/separate-current-edit values. Download reports,
findings, redacted traces and untouched recovery bundles. Modes are explicit;
Replay identifies the captured reference. Missing devices prohibit complete coverage
and automatic recovery. Sample readback compares a separately authored offline
export and expressly performs no upload.

Connected imports use the configured native Central test capture and existing
Stage 3 query/world/model worker. Its status/provenance remains distinct from the
deterministic verdict and newer recovery readback. Supported Apply reuses Stage 4,
requires exact target review plus a new read-only server check, and resets readiness
after reload. Lost acknowledgements restore saved state without another upload.

Actual production Chromium flow passed on the local built UI. Saved connected run
`check-967bc239-7d5e-4a2b-b4d5-ce9a4ee1f4b3` used four real Zetaris queries, three
World Model reads and three Nightshift calls: 9 steps, 2 critique rounds. Nightshift
reported actual Nemotron serving identity in retained model events. The original
diagnosis remains MISSING_ATTACHMENT; fresh post-recovery evidence is PRESERVED.
Exactly one write intent exists. The browser acknowledgement was deliberately
discarded after the real Apply request; reload recovered verified state without a
duplicate write. Immutable registered source SHA-256 still matches the setup ZIP.

Receipts: `verification/stage5-browser.json`, `stage5-connected.json`,
`stage5-replay.json`, `stage5-zoom.json`. The browser trace includes actual API
request paths. Initial test-locator/origin-wait failures were corrected; connected
completion was rechecked on the same saved run after its final state commit rather
than repeating recovery. Sample/history/export/conflict/stranded controls, downloads,
focus return/Escape, back/reload, real queued cancellation, invalid archive, saved
imports and empty browser storage were exercised. Mobile Replay with missing-device
coverage passed with no recovery/provider action. No page/dialog overflow at checked
390/768/1280px; reduced-motion and CSS zoom 2 were checked. This does not claim
cross-browser or screen-reader certification.

Final verification: **165 Python tests passed** in 105.96 seconds, including 11
Stage 5 tests; existing non-failing Starlette/httpx deprecation only. Production
Next build and generated TypeScript passed. The added supervisor-lease control
confirms dead connected work becomes interrupted without repeating provider calls.
New Stage 5 tests initially failed before UI adapter code;
tests also caught saved connected evidence being inaccessible without connection
configuration, which is fixed without weakening Apply guards.
All four new receipt files were checked against actual private configured secret
values and common token signatures: no matches. No session/auth bodies were exported.

No blocker remains for the narrow local acceptance path. Limits remain manifested
export compatibility, local-only private backend, isolated synthetic recovery and
bounded captures/provider jobs. Browser-menu zoom, other browsers, full assistive
technology audit and Stage 6/7 quality/performance targets are not claimed. Native
Nightshift Setup UI issue remains unrelated; its headless real inference worked.
Exact operation and verification commands: STAGE5.md.

## Historical Stage 4 handoff

## Stage 4 outcome

The existing deterministic reconciler remains authoritative. Added typed sealed
plans, explicit target/origin/version-bound review and Apply, deterministic ZIP
bundles/downloads, a SQLite attempt/capture/result ledger, OS serialization,
fresh scoped preconditions and original-XML/version/attachment-byte readback.
Sources are reread from the immutable registered store and checked after Apply.
Completed work is reused. Unknown writes require readback before another write.
Run completion, individual recovery and whole-source preservation stay separate;
the result retains full findings/coverage and operation/run-wide deficit deltas.

Supported writes are original-ID missing-submission creation and filling a
verified missing current-version attachment slot in a configured synthetic test
project. No historical repair, conflicting answer/media overwrite, deleting,
clearing, invented instance IDs or fabricated bytes. EXPORT_VIEW_ONLY has no plan.
Sample bundles remain offline and cannot Apply or instantiate network clients.

Actual live checks used the existing real local ODK Central v2026.3.1 at
localhost:8384, pinned commit 7d6de621955c5bb6a68e098ca10c9cbb92285cdf. Created only
the dedicated project **2**, `LastCopy synthetic Stage 4 recovery`, form inspection.
The earlier Stage 1 project and source archives remain unchanged. No AWS work.

- `stage4-20261024-01-create`: MISSING_SUBMISSION -> PRESERVED after native
  multipart POST and fresh XML/history/all-slot readback; repeat Apply did not write.
- `stage4-20261024-01-media`: MISSING_ATTACHMENT -> PRESERVED; only b.bin uploaded.
- `stage4-20261024-01-lost-ack`: real POST accepted; worker exited 73 before local
  acknowledgement. A new CLI process read back and verified without another POST.
- `stage4-20261024-api-media`: actual HTTP port-8000 stage/download/review/Apply
  and repeated Apply passed against another real missing attachment.
- `stage4-20261024-02-media`: repeated the HTTP acceptance after adding origin
  binding, native immediate version/XML/slot preflights and untouched device manifest.
- `stage4-20261024-02-lost-ack`: final original-ID creation/preflight and new-process
  CLI restart passed; exactly one write intent, no duplicate upload.

These directories under `docs/verification/` retain redacted actual request scopes,
status/hash receipts, untouched synthetic source/bundle bytes, before/after native
captures, findings and events. `stage4-integrity.json` records independent offline
checks of all six receipts: output/source seals, bundle byte equality and rerunning
the same reconciler before/after. Hashes alone do not authenticate a remote server.
All fixtures use authored binary/text bytes: sample.txt is referenced twice;
a.bin and b.bin contain equal bytes but both slots are independently required.
No community audio or AI-generated imagery was used. Upstream fixes and official
protocol references are cited in STAGE4.md.

Verification: the initial 8 recovery tests failed with the absent module, then
passed. Two deliberate in-memory mutations independently failed their acceptance
tests: ignoring XML conflicts falsely verified a conflict; ignoring version drift
falsely verified a changed version. The real code passed those controls. The final
complete Python suite passed **154 tests** in 80.60 seconds, including **22 Stage 4
tests**. OpenAPI/TypeScript regeneration and `npm run typecheck` passed. One
existing non-failing Starlette/httpx
deprecation remains. A sandbox-only TestClient socket-pair stall was diagnosed via
stack traces and resolved by running those tests with loopback permission.
The synthetic evidence packages were scanned recursively (587 objects including
nested ZIPs) for common credential/token signatures; none were found. This check
supplements exclusion of all session responses and private configuration from
capture/bundle code; it is not a general security certification.
`stage4-capture-entrypoints.json` additionally records successful real CLI capture
and HTTP `/recovery/capture` -> registered `/run` -> PRESERVED, with zero writes.
The captured server envelopes link explicitly labelled local normalization to
actual native authenticated GET receipts; normalized JSON is not called a native
Central response. Original source IDs are read from registered device manifests.

## Stage 4 limits and operation

See STAGE4.md for exact CLI/API commands, limits and evidence endpoints. API health
now reports stage 4. The live backend stays bound to loopback; no authentication
system or production deployment was added. UI review/Apply controls are Stage 5;
the Stage 4 explicit actions are the working CLI and typed HTTP endpoints.

No external blocker remains for the narrow synthetic acceptance path. Genuine
limits: Central lacks atomic compare-and-swap for attachment POST, so the dedicated
project must exclude concurrent external writers; a local OS lease cannot lock
other clients/stores. Preflight and post-write comparison detect drift but do not
provide a multi-writer transaction. Historical media writes remain unsupported.
Capture is bounded to 30 submissions, 10 versions each, 50 slots/version, 200
requests/capture, 1 MiB/response, 8 MiB total and 120 seconds; Apply has 300 seconds.
This is verified local Central recovery, not production/cloud recovery, Kobo
support or permission to erase a device. Stage 3 sponsor checks were not rerun in
Stage 4; their earlier actual receipts remain below. Nightshift's native Setup UI
issue is unrelated and remains documented.

## Historical Stage 3 handoff (claims below describe that stage)

## Actual connected acceptance

Both synthetic cases used the actual existing local Zetaris deployment, the
pinned Meterless World Model reference and NVIDIA cloud inference through
Nightshift 1.2.3. The reported concrete model was
`nvidia/nemotron-3.5-lightning-30b-a3b`, discovered from authenticated Nightshift
inventory and verified by real responses, not relabelled from meterless/auto.

- Export case: 102.168 seconds, 9 steps, 2 critiques, 3 model calls. The reviewer
  requested raw evidence, the verifier returned EXPORT_VIEW_ONLY, the initial
  hypothesis was rejected and the action became export_guidance. No upload.
- Conflict case: 63.318 seconds, 9 steps, 2 critiques, 3 model calls. The verifier
  returned CONTENT_CONFLICT and the reviewer kept unresolved_conflict with
  manual_review. No overwrite or executable recovery was scheduled.
- Each case made four real scoped Zetaris evidence queries. Source bytes stayed
  unchanged; reports were independently re-compared using the same authoritative
  verifier, output seals checked, and actual reference graph rebuilds matched.
- Graph actions changed review -> fetch_raw -> export_guidance/manual_review.
  Earlier hypothesis revisions and their evidence remained available. The model
  could not alter verifier findings. Limits remained 12 steps/2 critiques/300s.

Receipts, actual JSONL, query rows and reports are in
`verification/stage3-live-{export,conflict}*`. The model/usage fields are what
Nightshift reported; no local token estimates or upstream identity beyond its
response are invented. NVIDIA integration work is demonstrated; this is not an
organizer award decision or a guarantee of eligibility/winning.

## Tests and entrypoints

**132 Python tests passed** (one existing non-failing Starlette/httpx warning).
**6 private-key-helper Node tests passed**. The NVIDIA action-contract test was
observed failing, then passed after the fix. Three earlier mutation controls
caught broken behavior. Typecheck previously passed; web code was not changed.
The pinned World Model's 10 tests and 8 conformance checks passed on Oct 23;
today's live runs and independent rebuilds additionally exercised that reference.
The three offline CLI cases and explicit replay remain verified, without model or
SQL calls. Historical failed receipts are retained as history, not overwritten.

Stage 3 CLI: `scripts.investigate`; see STAGE3.md for full commands. Set
SAMPLE_MODE=false and use --connected --nemotron for live mode with a fresh
output directory. The ignored configuration now selects the actual tested NVIDIA
cloud route. Source objects are private; only bounded normalized synthetic CSV
manifests go to Zetaris NDP. This is materialization, not heterogeneous in-place
federation, S3 integration, or fresh Central acquisition.

Independent offline artifact verification example:

```powershell
.\.venv\Scripts\python.exe -m scripts.verify_stage3_live --attempt private/stage3/cloud-export-20261024-02 --fixture fixtures/stage3/export-review --receipt private/verification/live-export-recheck.json
```

The port-8000 /run endpoint remains the Stage 2 verifier using registered IDs.
Its health correctly reports Stage 2; Stage 3 is the supervised local CLI.
Completed investigation and preservation outcome remain separate. Recovery is
Stage 4; no Apply, uploads, destructive writes, erasure approval or blanket
safe-to-wipe claim exists.

## Unblock details and limitations

The native Nightshift Add Key wizard did not navigate; dismissing it left blank
content. Its exact frontend exception is not diagnosed. The key was entered by
the human through a tested hidden-input prompt using Nightshift's observed native
key API. It was never printed, put in chat, retrieved for inspection or committed.
A possible doubled original paste was reported, but that original value was not
inspected. Fresh entry rejects a second nvapi- prefix and authentication/inference
then passed. See NIGHTSHIFT_KEY_ENTRY.md. Native Setup UI remains a known issue;
headless key entry and the provider/investigation paths work.

Nemotron short structured actions required reasoning_effort=none on the tested
route. This installed Nightshift adapter supports that control; a real strict
JSON probe passed and the code sends it for NVIDIA action requests. Actions are
still validated with a closed schema and phase allowlist. Models never supply
missing answers or determine preservation. Temporary observation-only network
diagnostics were removed; no vendor engine/source or TLS safeguards were changed.

Docker was restarted and the four existing Zetaris containers started, with
login/query readiness verified. No new AWS infrastructure, IAM or model download
was needed for the live cloud cases. The installed optional local text lanes remain
stopped. Old memory/admission blocker records are historical. ODK recovery was
not exercised in this stage; its containers were not required for supplied captures.
Private evidence processing remains local; the Vercel skeleton is unchanged.

Private repo: https://github.com/miracle352/lastcopy . Never make public without
user instruction. Existing skeleton: https://lastcopy-five.vercel.app/ . No Stage 4
work, imagery generation, production field-data publication or backend deployment.
