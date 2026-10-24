# Stage 5: working local application

The application uses the existing registered-input store, deterministic comparator,
supervised connected investigation and reviewed recovery engine. Results are API
responses, not client-authored success states. No imagery, generated media or model
calls are used to build fixtures or perform deterministic verification/recovery.

## Start locally

From the repository root, in one PowerShell terminal:

```powershell
$env:SAMPLE_MODE='false'
$env:LASTCOPY_DATA_DIR='private/stage5/ui'
.\.venv\Scripts\python.exe -m uvicorn lastcopy.api:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
npm run build
npm run start
```

Open http://127.0.0.1:3000 . Use `npm run dev` during development. The existing
server-only `.env` supplies the configured synthetic Central target and connected
providers. Do not enter API keys in the browser. For an entirely offline Sample
workspace, set SAMPLE_MODE=true before starting the API; no provider is needed.
Samples remain offline even when the local API also has a configured connection.

## User flow

- `/` introduces the actual capability and its limits. Both start links work.
- `/app` opens five authored sample cases or accepts up to eight device ZIPs.
  Device IDs, source hashes, explicit completion and original XForms are validated.
  The user reviews the expected-device roster; absent devices are not inferred away.
- Imported checks use either a scoped versioned server bundle (Replay, with an
  explicit captured-run/capture reference) or the configured Central synthetic test
  project (Connected). No arbitrary target URL or filesystem path is accepted.
  Preparing a connection performs a read-only native capture; it is visibly labelled.
- Save inputs for later persists only registered IDs, roster and source selections
  on the server. Its opaque reference is in the URL. No secrets or export content
  are stored in localStorage/sessionStorage. Review confirmation resets on reload.
- Run check starts the real comparator. `/runs/[id]` restores the saved check,
  actual events, coverage, findings, plans and recovery attempts. Queued/running
  comparisons can be cancelled. Startup marks abandoned comparisons interrupted.
- Every finding opens a native modal evidence drawer. Escape closes it and focus
  returns to the triggering button. Expanded XML paths and occurrence indices,
  original/server/current-edit values, file slots, hashes, receipts and untouched
  file downloads are available. Values are rendered as text; imported XML/HTML is
  never inserted as executable browser content. Large value displays truncate at
  500 rows with an explicit message; the verifier still compares full bounded inputs.
- Downloads include a plain-language report, findings JSON, complete receipt report,
  allowlisted redacted trace and an untouched recovery bundle. Connected technical
  downloads resolve actual query rows/source objects and append-only graph history.

The UI keeps investigation completion, source coverage and recovery status separate.
The original report is immutable; a newer recovery/read-only readback can supply a
new displayed report. Intentional retained history is shown without an overwrite
action. EXPORT_VIEW_ONLY recommends a suitable export and never schedules upload.
Unknown/conflicting results wait for information/manual review. Missing bytes are
not reconstructed. No global device-erasure approval is displayed.

## Recovery review and restart

Stage 4 is reused. Plans display exact project/form/connection/origin, original
submission/version, expected current version, untouched required files/hashes,
preconditions and limitations. The user confirms the sealed plan and downloads its
bundle. Apply is available only in Connected mode after an explicit fresh read-only
server check says the original plan is still eligible. This readiness is held only
in component memory and resets on reload. The engine independently rechecks every
write regardless of what the UI showed. Unknown acknowledgements require readback;
neither a timeout nor POST success is preservation proof.

Sample plans have an explicitly offline environment and no Apply action. After
review, Compare offline readback example runs the same comparator on a **separate
authored synthetic capture**, with source bytes copied unchanged. It says no upload
occurred and links back to the original gaps/plan. Replay plans cannot Apply.

## Connected investigation

The normal Connected start also dispatches the existing Stage 3 supervised worker,
using the bounded native synthetic test capture. A native capture is accepted for
publication only with explicit synthetic device manifests, configured test target,
complete scoped native evidence and the guarded UI capture provenance. All raw
objects remain private. Small normalized CSV evidence is materialized to the actual
local Zetaris deployment; this is not heterogeneous in-place federation.

The UI shows provider/query/graph diagnostics in secondary technical details and
exposes cancellation. One active connected investigation is allowed per store;
limits remain 12 steps, two critique rounds and 300 seconds. Provider failure never
substitutes Sample evidence or changes verifier outputs. A detached supervisor
survives an API restart; an OS lease identifies an abandoned running supervisor as
interrupted. Provider operations are not automatically replayed. Investigation
evidence is scoped to the original capture, separately labelled when fresh recovery
readback has changed the current displayed verdict.

## Verification performed

`scripts/verify_stage5_browser.mjs` uses pinned playwright-core 1.63.0 and the installed
Chromium. It drives real production UI controls and API responses. The only injected
transport failure discards the browser acknowledgement **after** a real Apply request
finishes; no successful result is mocked. The saved verified state then restores and
contains exactly one write intent. New live fixtures require a fresh synthetic tag;
the setup script refuses to overwrite/delete a record to recreate a gap.

```powershell
$env:SAMPLE_MODE='false'
$env:LASTCOPY_DATA_DIR='private/stage5/ui'
.\.venv\Scripts\python.exe -m scripts.seed_stage5_browser --tag A_NEW_SYNTHETIC_TAG
node scripts/verify_stage5_browser.mjs
```

The browser blocks external web origins; local backend Connected services remain
explicitly authorized. Production-browser checks covered sample comparison,
evidence keyboard/focus behavior, downloads, plan review/reload/back navigation,
offline readback, all five fixture controls, queued cancellation, invalid ZIP,
saved imports, native Central capture, reviewed recovery, lost acknowledgement,
actual Zetaris/World Model/Nightshift behavior and empty browser storage. The final
connected-status test was resumed against the same saved run after its final commit;
no upload was repeated. See `verification/stage5-browser.json` and
`verification/stage5-connected.json` for actual results and run IDs.

390/768/1280px layouts, narrow reflow and reduced motion were checked in Chromium.
200% was separately checked with CSS zoom 2 at 1280px (not a claim of browser-menu
zoom or every assistive technology): page and evidence dialog did not overflow.
The Replay browser check also covered an absent expected device, retained capture
reference, mobile reload, evidence and unavailable automatic recovery. Receipts are
`stage5-zoom.json` and `stage5-replay.json`; screenshots stay under ignored private/.

## Remaining boundaries

This is a single-user local application. The Vercel public UI cannot proxy to a
private loopback evidence API and returns an actionable unavailable state. No backend
hosting, authentication system, real-field publication or public repository change
was added. Preserve the loopback binding. The UI accepts the documented manifested
device/export format; it does not infer completion for arbitrary unmanifested ZIPs.
Native capture bounds and isolated synthetic recovery restrictions from STAGE4.md
remain. Cross-browser/screen-reader testing and performance targets are not claimed;
Stage 6 visual/motion polish and Stage 7 broader audits remain separate requests.
