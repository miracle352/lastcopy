# LastCopy handoff

Current stage: **3 verified, including real connected acceptance (2026-10-24)**.
Prompt 0 persists in AGENTS.md; PRODUCT_SPEC.md is authoritative. Stage 4 requires
a new request. No recovery execution or backend deployment was added.

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
