# Water-point collection and automatic copy checks

Updated automatic device link and actual native-connection fixes:
[REALTIME.md](REALTIME.md). The approved dedicated emulator now supplies stable
exports automatically; manual physical-phone transport remains outside acceptance.

Implemented locally on 25 October 2026. No Vercel deployment, repository push,
visibility change or public submission occurred.

## What is running

- Central project **3: Water Point Condition Check** is the collection project.
  It contains no field records or seeded test submissions. The form ID stays
  `lastcopy_water_point_v1`; the current form version is `2026102502`.
- Project **4: LastCopy water-point pilot (synthetic)** holds one actual
  emulator-created test submission. It is separate from the collection project.
- LastCopy reads project 3 through a separately configured **read-only collection
  connection**. The existing recovery target remains project 2. Collection scope
  cannot write through the recovery transport or publish evidence to sponsors.
- The automatic monitor runs inside the local API. It starts no separate cloud
  service and makes no model, Zetaris or World Model calls. Automatic reports
  explicitly identify deterministic comparison and fresh authenticated Central
  evidence. Existing explicit sponsor investigations remain separate test paths.

## Use the app

Open http://127.0.0.1:3000/app with the production UI, API and existing Central
containers running. Exact launch commands remain in [RUN_LOCALLY.md](RUN_LOCALLY.md).

1. Add a supported device ZIP. Confirm its device identity and include every
   expected device in the roster. Device files stay immutable in the private
   registry.
2. Select **Read the connected ODK Central server** and review the displayed
   project/form scope.
3. Confirm the roster, then choose **Use these exports for automatic checks**.
   This uses registered IDs and persists the reviewed roster; no JSON editing
   or browser filesystem path is required.
4. **Keep checking as exports arrive** shows actual state, received/missing
   devices, last comparison time, report link and attempt budget. Start, pause
   or request a fresh check with its controls. Saved reports survive reload.

The initial planned device label is `water-field-01`. It is not evidence that a
device is connected. Replace the roster through the reviewed upload flow when
the first actual device export arrives. No complete-coverage result exists while
its evidence is absent.

## Supplying continuous device evidence

The checker watches a private configured inbox and accepts reviewed uploads
through the UI. It cannot see unsynced records on an inaccessible phone. Android
does not automatically send its private Collect directories to this PC.

For a USB/copied-project workflow, first obtain a consistent stopped-app copy
using the documented ODK export/ADB procedure. Never root a field phone for this
feature. The AOSP emulator used in acceptance is a dedicated debug device.
Package its native files with the operator CLI:

```powershell
.\.venv\Scripts\python.exe -m scripts.package_collect_project --source 'PATH_TO_COPIED_PROJECT' --form-id lastcopy_water_point_v1 --device-id 'YOUR_DEVICE_ID' --collector-version v2026.3.5 --output 'private/water-point/live-inbox/device-export.zip'
.\.venv\Scripts\python.exe -m scripts.seal_export 'private/water-point/live-inbox/device-export.zip'
```

Use a new output name for each export. The packager refuses overwriting. For test
entries add `--synthetic`; omit it only for actual collected observations. It
selects all copied native rows for the declared form unless an operator explicitly
supplies `--form-version`. Do not exclude old field versions merely to obtain a
green result. The acceptance test's version-2 cohort is separate from the retained
version-1 prototype control.

A transport producer may instead copy an already-packaged archive as `.partial`,
rename it to `.zip` after transfer, then publish `name.zip.ready.json` last:

```json
{"schema_version":1,"sha256":"SHA256_OF_UNTOUCHED_ZIP","bytes":12345}
```

The size/hash must match. Incomplete, linked, hostile, out-of-roster, wrong-form,
unknown-time or ambiguous older exports are not silently adopted. Unknown
completion remains unknown. The native metadata packager keeps the full database
private and includes only selected completion rows and its original database hash.

## Collect setup

The current form was installed and finalized in the existing `LastCopyCollect`
Android emulator. There were two separately entered problem occurrences and one
synthetic image chosen through Android's picker. Original XML and media were
retained. The emulator is stopped after acceptance to release RAM.

Form-scoped **app-user** accounts were created for projects 3 and 4. Their actual
form lists were checked. Private native-app settings and QR PNG/SVG files are in
`private/water-point/collection-collect/` and `private/water-point/pilot-collect/`.
They contain access credentials and are intentionally excluded from Git and the
LastCopy browser API. QR import into Collect has not been acceptance-tested.
Do not put these private files in public reports.

These settings use emulator host alias `10.0.2.2`. They are for the local emulator;
real phones need an explicitly configured reachable HTTPS Central deployment.
This work did not expose the local server to a LAN or the internet. A Vercel UI
cannot reach this PC's loopback API.

## Behavior and limits

The inbox is inspected every five seconds while the API runs. A newly adopted
export triggers a fresh check; enabled sessions also reread Central at the
configured interval (60 seconds initially). This is scheduled near-real-time
comparison, not an uninterrupted phone stream or a completion-time guarantee.
The UI polls actual saved state every five seconds.

There is one monitor lease per evidence store and a persistent attempt budget
(120 initially, hard maximum 1000). Restart does not reset it. Each capture and
comparison retains the existing bounds: 1–8 device inputs, 10 MiB ZIP upload,
32 MiB expanded archive, 30 Central submissions, 10 versions per submission,
50 attachment slots, 1 MiB per response, 8 MiB aggregate capture, and existing
request/run deadlines. The ledger's existing 1000-job/512 MiB input quotas still
apply. These are initial small-project limits; larger scopes fail explicitly.
There are at most 100 files in an inbox and 5000 monitor events. Sources are never
silently deleted for retention. Archive old inbox files yourself when needed.

Pausing prevents future captures. An in-flight read can finish and remains
recorded. It cannot upload a recovery. Resume/restart reuses a persisted pending
run, rather than making a second run for that interrupted job. Authentication or
capture failures leave an error and never become missing-record evidence or a
Sample fallback. The latest successful report is historical until a new capture
completes; capture times remain in its receipts.

## What was actually verified

The final full Python-suite result and production browser receipts are in
`verification/water-point/`. Production build and generated TypeScript pass.
All 189 tests passed, with one nonfailing Starlette deprecation warning. Retained
before/after pilot captures also passed the documented CLI with socket connections
denied; this recomparison is saved evidence, not another live check.
Three initial route/monitor tests failed before implementation. The tests exercise
sealed inputs, actual fixture comparison, missing devices, failure, pause during
capture, restart/idempotency, persistent budgets, private completion metadata and
read/recovery scope isolation. Collection writes and sponsor publication are
rejected. The original archive hashes remain unchanged.

The live version-2 pilot produced **MISSING_SUBMISSION** before native delivery
and **PRESERVED** after fresh XML, history, attachment listing and byte readback.
Two repeat values and one attachment slot matched. Central retained one logical
submission while repeated automatic checks and an actual API restart retained
state. No recovery Apply was exercised in this follow-up; ordinary synthetic
delivery used the documented native OpenRosa endpoint.

Actual fixes/limitations: version 1's implicit namespace did not match Collect's
saved root and stayed **UNVERIFIABLE**. Version 2 adds XLSForm `attribute::xmlns`;
both original form versions and the first export remain retained. The comparator
was not relaxed. One initial delivery attempt returned 400 because the helper
omitted the required `X-OpenRosa-Version: 1.0` header. After a fresh absence check,
the corrected documented request returned 201. A browser keyboard test caught
focus loss during monitor actions; focus restoration was fixed and the test
passed. The keyboard drawer test now waits for asynchronous closing before
asserting focus return; the assertion remains.

Browser coverage: actual uploaded-source enrollment, pause/reload, saved evidence,
both repeat values, report download, keyboard use, 360/390/768/1280/1440 widths,
200% CSS layout zoom and reduced motion. Chromium only. Native browser zoom,
unattended physical-phone exports, QR import, field deployment, new Lighthouse
measurements and a new Docker rebuild were not verified. Existing image/security
and organizer-template limitations remain historical release work.

The final active monitor uses the empty `private/water-point/live-inbox` and planned
device `water-field-01`. It is enabled and waiting for exports. The synthetic pilot
and collection-scope acceptance sources remain in separate persisted monitor
histories; they are not enrolled as current field evidence.

Official references: [Collect ADB exports](https://docs.getodk.org/collect-adb/),
[XLSForm extensibility](https://xlsform.org/en/#advanced-use-and-extensibility),
[Central form revisions](https://docs.getodk.org/central-api-form-management/),
[OpenRosa requests](https://docs.getodk.org/central-api-openrosa-endpoints/),
[Collect settings QR codes](https://docs.getodk.org/collect-import-export/).
