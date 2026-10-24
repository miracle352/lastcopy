# Evidence-driven investigation

Stage 2 remains the preservation authority. Stage 3 adds a local CLI investigator,
not recovery execution. The existing port-8000 `/run` endpoint still runs the
deterministic verifier using registered input IDs. Its health stage remains 2;
the Stage 3 supervisor is a separate entrypoint, not a deployed web worker.

## Actual architecture

`EvidencePack` normalizes explicitly synthetic supplied device/server captures.
It does not compare them or generate conclusions before querying. Private
content-addressed objects retain original ZIP, envelope, XML, XForms and media
bytes. Only small normalized CSV manifests go to the existing local Zetaris
NDP file store. This is CSV materialization, **not heterogeneous in-place
federation**, S3 integration, or fresh Central acquisition. Supplied synthetic
server captures remain labelled synthetic even when Zetaris queries are live.

Each attempt creates an isolated database and source directory. Six tables hold
device_inventory, submission_versions, xml_facts, media_references, file_hashes
and attempt_logs. Rows have run/source/version scope, stable content IDs and
original object references. XML paths retain namespaces and occurrence indices;
JSON facts use the actual Spark backslash-escaped CSV dialect. A missing value in
an attachment readback remains unavailable; equal hashes never merge filenames.

The normal connected path performs an actual Zetaris anti-join between device
XML paths and selected export paths. Those returned rows cause a provisional
missing-data hypothesis. The model reviewer can request raw evidence or keep it
unresolved. Only a request changes the graph's next action to fetch raw evidence.
Zetaris then joins device/server version identities and returns registered source
object handles; those results select the private bytes passed to the verifier.
Media-reference rows are queried separately. Raw comparison still happens in code.
No completed preservation findings are uploaded as ceremonial query inputs.

The second reviewer receives the deterministic result. Export-only gaps can
become export guidance; conflicts remain manual review. A model cannot edit
findings, eligibility, coverage, hashes or the comparator report. Guidance is
non-executable. No upload, overwrite, missing-byte reconstruction or Apply exists
in this stage. No provider failure substitutes sample evidence.

## World Model and provenance

`bridge/investigation-world.ts` imports the actual pinned reference at commit
`1742dec56a66e58eef9dda2d2b865823758ca8cd`. LastCopy persists an append-only,
content-identified JSONL observation/revision journal. Reads rebuild it through
real `ingest`, external-key `upsertEntity`, `relate`, and `view("graph").query`.
There is no invented hosted SDK, search view, distributed store or spec-only API.

Entities include snapshots, form versions, submission versions, attachments,
observations, hypotheses and recovery operations. Hypothesis revisions are distinct
entities linked with `revises`; rejected hypotheses and earlier evidence survive.
Graph reads occur before review, before raw acquisition and after revision, and
their next action controls dispatch. This initial planner manages one batch gap
hypothesis per attempt. It is not a general multi-incident scheduling service.

Successful runs save `query-evidence.json`, exact per-query receipts/rows,
`published-rows.json`, publication hashes, private objects, the world journal,
the independently verifiable `report.json`, and `investigation.json` with a finding
resolution map. Findings resolve through actual query IDs/row IDs to private
source objects and the verifier's file/path/media receipts. Failure traces retain
queries completed before failure. `seals.json` hashes output files, including raw
source objects and event logs. A seal detects byte changes; it authenticates
neither a server nor the original respondent.

## Bounds and cancellation

The existing RunManifest owns at most 12 steps, two critique rounds and 300
seconds (lower configurable limits are respected). One code-owned tool dispatch
can issue the fixed scoped version/object queries, never arbitrary model SQL.
Nightshift uses strict action JSON, validated again by Pydantic with extra fields
forbidden and phase-specific action allowlists. Imported content is data; model
tools accept neither paths nor URLs. Provider-reported serving identity and token
usage are recorded; unavailable usage is labelled, never fabricated.

One OS lease bounds the CLI to one Stage 3 job. A spawned worker is supervised
against the **whole attempt deadline**, including blocked sockets/engine calls.
Create an empty `cancel` file in its attempt directory, or press Ctrl+C. The
supervisor terminates blocked work and persists a cancelled/failed result.
Unexpected worker exits become interrupted. Attempts are never automatically
replayed; use a new empty output directory. Stage 2 retains its separate four-job
queue. A hard kill can leave bounded synthetic Zetaris registration artifacts;
no automatic table deletion or source overwrite occurs. The directory/database
names in publication receipts allow later deliberate cleanup.

Publication caps: 8 devices, 16 MiB compressed inputs, 64 MiB private objects,
64 total submission versions, 256 media references, 5,000 rows/1 MiB per CSV,
4 MiB CSV total, 512 world observations and 2 MiB per query response. Existing
ZIP/XML protections apply. CSV scans can read whole files despite WHERE/LIMIT;
the small physical files and isolated sources establish scan bounds. This is not
a production-scale evidence warehouse.

## Commands (PowerShell, repository root)

```powershell
$env:SAMPLE_MODE='true'
.\.venv\Scripts\python.exe -m scripts.investigate --manifest fixtures/stage3/export-review/run-manifest.json --device fixtures/stage3/export-review/device.zip --server-manifest fixtures/stage3/export-review/server-snapshot.json --server-payload fixtures/stage3/export-review/server-payload.zip --output private/stage3/sample-01

$env:SAMPLE_MODE='false'
.\.venv\Scripts\python.exe -m scripts.investigate --manifest fixtures/stage3/export-review/run-manifest.json --device fixtures/stage3/export-review/device.zip --server-manifest fixtures/stage3/export-review/server-snapshot.json --server-payload fixtures/stage3/export-review/server-payload.zip --output private/stage3/connected-01 --connected
```

Use `unresolved-conflict` for the conflict case, `held-out` for changed identities,
paths and five repeats. Expected verdicts/actions in each pack are hand-authored.
Sample runs only the actual comparator; no graph/model/SQL calls or fabricated
agent traces. `--replay` with SAMPLE_MODE=false performs an explicitly labelled
offline supplied-capture comparison; it does not replay model responses as live
inference. A non-sample manifest cannot silently become sample.

Append `--nemotron` to a connected command to discover advertised Nemotron IDs
from authenticated Nightshift inventory and require an actual returned Nemotron
serving identity. An advertised route is not proof that its model is available.
No guessed model ID or direct NVIDIA endpoint is used. Ordinary successful
Nightshift inference on another model leaves the NVIDIA award path blocked.

```powershell
.\.venv\Scripts\python.exe -m scripts.verify_stage3_cli
.\.venv\Scripts\python.exe -m scripts.verify_stage3_mutations
.\.venv\Scripts\python.exe -m pytest -q
npm run test:world-model
npm run conformance:world-model
```

`scripts.verify_stage3_zetaris PUBLICATION_JSON --output NEW_DIRECTORY` rechecks
the exact previously published fixture hashes and actual scoped queries without
claiming an investigator/model run. It is a separate read-only integration check.

## Live acceptance status - verified 2026-10-24

Both real connected synthetic runs passed: EXPORT_VIEW_ONLY -> export_guidance
(102.168 s) and CONTENT_CONFLICT -> unresolved conflict/manual_review (63.318 s).
Each used four actual Zetaris queries, real reference graph reads/revisions and
three Nemotron calls through Nightshift, within 9 steps/two critiques/300 seconds.
The reported model was `nvidia/nemotron-3.5-lightning-30b-a3b`, from authenticated
inventory and actual responses. The NVIDIA integration demonstration is verified;
award eligibility or an organizer decision is not asserted.

`verification/stage3-live-{export,conflict}*` includes actual receipts, JSONL,
reports and query rows. Independent verification re-compared the original private
objects selected by query rows, rebuilt the reference graph and checked every
output seal. No recovery was executed. Historical failed records remain intact.

The native Add Key UI was unresponsive and main content blank after skipping its
wizard. A tested private hidden-input helper uses the observed native key API;
see NIGHTSHIFT_KEY_ENTRY.md. The human re-entered their key once, with a duplicate
paste guard. No stored key was retrieved or included in chat/Git. Real inference
then succeeded. The original bad entry's exact problem is not proven.

The tested NVIDIA route needs reasoning_effort=none for these short bounded
strict-JSON actions; this is supported by the installed adapter, passed a real
probe and has a regression control. No reasoning text is requested or logged.
Token usage is taken from Nightshift's response, with no local estimate added.
The native UI remains a known issue, but does not block the working CLI path.
Local text lanes stay stopped; the cloud path avoids the previous RAM admission
problem. Neither the vendor runtime nor TLS safeguards were modified.

```powershell
.\.venv\Scripts\python.exe -m scripts.verify_stage3_live --attempt private/stage3/cloud-export-20261024-02 --fixture fixtures/stage3/export-review --receipt private/verification/live-export-recheck.json
```

This verification command is offline artifact checking, never relabelled as a new
live model run. Supplied source captures are synthetic; actual Zetaris querying
and provider calls do not turn them into newly fetched real Central records.
