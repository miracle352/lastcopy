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

## Live acceptance status

See HANDOFF.md and `verification/stage3-*`. Actual Zetaris registration and all
four queries passed, including 11 export-gap rows, one version match, three raw
source handles and seven media-reference rows. Pinned reference tests/conformance
passed. Unit tests exercise both reviewer branches with clearly named SQLite/model
doubles; those are not live sponsor acceptance.

The connected investigator reached Nightshift and failed honestly: HTTP 400
`no_provider_configured`. The installed 1B Llama text lane is stopped; start
attempts returned HTTP 409 admission refusal for critical memory pressure, also
after the user freed memory. No cloud provider key is configured. Inventory lists
Nemotron routes but no Nemotron inference/serving identity was observed. Therefore
the combined live investigation/reviewer acceptance and NVIDIA award path remain
blocked. A separately pinned smaller text model also failed admission, including
after an idle-runtime restart; see MODEL_SOURCES.md. The runtime sometimes denied
startup even when reported free RAM exceeded the printed requirement. No guard
was bypassed. Paused LastCopy services were restored and their health rechecked.
Do not claim Stage 3 end-to-end live verification or use Stage 1's old
inference receipt as a substitute. No recovery writes or backend deployment occurred.
