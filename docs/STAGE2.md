# Stage 2 deterministic supplied-snapshot verifier

The CLI and FastAPI service share `reconcile.py`. They perform no external calls,
SQL, model inference or recovery writes in any evidence mode. Sample requires
explicitly synthetic sources. Connected/replay compare supplied captured evidence
and say that it is not fresh live evidence; they do not silently use samples.
`SAMPLE_MODE=true` rejects a non-sample manifest. Existing provider smoke commands
remain separate and are not called by this pipeline.

## Inputs and explicit scope

Device ZIPs use the existing native-path contract and immutable original files.
Completion/provenance is mandatory: missing metadata is rejected; `draft` and
`unknown` produce UNVERIFIABLE and no recovery candidate. Missing declared XForm
files reject input; unmatched form identity or unsupported XPath remains a
limitation. No identity or destination comes from folder naming.

Optional v1 additions `scope_complete` (defaults false) and `scope_provenance`
are required before device coverage can be complete. They attest only the scope
of the supplied snapshot, not every record ever collected. Unknown capture times
remain limited. Old Stage 1 fixtures continue to validate but acquire no new
completeness claim merely by being imported into Stage 2.

The raw server envelope is `SourceSnapshot` schema 1 with payload ZIP SHA256,
connection ID, project/form scope, versions and typed receipts. Stage 2 adds:

- `connection_id` must equal the RunManifest's configured connection ID.
- `listing_receipt_id` resolves to a successful captured scope listing file.
  Its versioned normalized JSON contains connection_id, project_id, form_ids,
  history_complete and ordered `versions` entries with form_id, form_version,
  logical_submission_id, version_id, deprecated_id and current. These must agree
  with the envelope. Missing/failed/inconsistent listing evidence cannot establish
  absence. Historical chains must terminate, resolve and have one current version.
- `attachment_listing_receipt_ids` maps version IDs to captured JSON documents
  containing that version_id and its complete `filenames` list. A missing slot is
  asserted only inside this successful captured listing; 401/403/404 read failures
  alone do not establish it.
- Every positive XML readback receipt binds form/version, original file and hash.
  Every positive media readback also names `attachment_filename`; two names require
  independently identified receipts, even if their bytes/hash are equal. Repeated
  source references to one filename may share its one server slot.
- `tabular_views` maps a captured wide CSV file to one version and explicit
  expanded, indexed XML paths for its columns. CSV needs `version_id`, unique
  headers and exactly one row for the selected version. This is a narrow diagnostic
  mapping, not a general OData/CSV importer or a reconstruction source.

Synthetic receipts use LOCAL/synthetic and no HTTP status. Non-synthetic positive
readbacks require GET/success/2xx. A typed failed status cannot be promoted by
setting a success label. Hash/identity consistency is checked independently from
whether evidence is sufficient for a verdict. Supplied receipts are capture
provenance, not cryptographic proof of a publisher, respondent truth or a current
server state. Only the synthetic normalized capture format has been exercised in
Stage 2; an automatic native Central capture/export adapter is not implemented.

## Comparison and verdicts

XML compares expanded element/attribute names and ordered child occurrences.
Prefix spelling and attribute order do not matter. No field is globally ignored.
Whitespace between element-only children is formatting unless xml:space=preserve
applies. In mixed content, all direct text and tails are significant. Leaf text,
Unicode, leading zeros and attribute values are exact; the XML parser's standard
line-ending/entity normalization applies. Comments/PIs are outside this data-tree
comparison. Difference details retain expanded paths and occurrence indices, with
at most 64 detailed differences plus the full difference count.

| Verdict | Preservation | Action in Stage 2 |
| --- | --- | --- |
| PRESERVED | preserved | None; identify checked version/current edit |
| MISSING_SUBMISSION | not_preserved | Review candidate only, bounded to captured scope |
| MISSING_ATTACHMENT | not_preserved | Review candidate only, specific filename slots |
| CONTENT_CONFLICT | not_preserved | Manual; never overwrite |
| EXPORT_VIEW_ONLY | preserved | Export guidance; never an upload candidate |
| UNVERIFIABLE | unknown | Manual; acquire missing evidence |

Finding `code` is separate from preservation. An original retained in history is
checked against that version's XML/media, identifies the current version, and
does not schedule an overwrite. Missing original/history readback stays unknown.
Malformed XML or hostile archives fail validation instead of inventing an item
identity. Conflicting duplicate source versions require explicit selection.

Coverage cannot be complete if an expected device, scope attestation or required
readback is absent. Known gaps may finish with `preservation_outcome=with_gaps`;
unresolved evidence gives `unresolved`. Coverage means only the stated supplied
scope; it is not a device-erasure authorization. `recovery_eligible` indicates a
future review candidate, not an executable or applied recovery plan. Stage 4 must
recheck fresh target preconditions and obtain explicit plan review.

## Registered API on port 8000

Keep the server on 127.0.0.1. It is single-user local development, without network
authentication or multi-tenant isolation. Configure `LASTCOPY_DATA_DIR` in the
server environment, never in request JSON. Default: ignored `private/stage2`.

```powershell
$env:SAMPLE_MODE='true'
.\.venv\Scripts\python.exe -m uvicorn lastcopy.api:app --host 127.0.0.1 --port 8000
```

`POST /inputs/manifest` accepts RunManifest JSON bytes; `/inputs/device` accepts
device ZIP bytes. `/inputs/server` accepts a bounded transport ZIP with exactly
`server-snapshot.json` and `server-payload.zip`; the original inner payload and
envelope bytes are retained. `scripts.run.bundle_snapshot` constructs this wrapper.
Each registration returns input_id, kind and original-data sha256.

```json
{
  "manifest_id": "<registered 64-character ID>",
  "device_input_ids": ["<registered device ID>"],
  "server_input_id": "<registered server ID>"
}
```

Submit that body to `POST /run`: HTTP 202 with persisted run ID/state. No arbitrary
path or URL field is accepted. Inspect `GET /runs/{run_id}`, actual JSONL at
`GET /runs/{run_id}/events`, and sealed outputs at
`GET /runs/{run_id}/artifacts/{name}`. Names are allowlisted: report.json,
findings.json, receipts.json, events.jsonl. `POST /runs/{run_id}/cancel` requests
cooperative cancellation. Unknown IDs are 404; conflicting run IDs/full queues are
409; invalid captures are 422; oversize bodies are 413. State completion and
preservation outcome are distinct fields.

## Persistence, bounds and restart

Hash keys use separate snapshot/capture/registration namespaces so supplied
labels cannot replace metadata integrity hashes.

SQLite stores original immutable registered BLOBs, request identity, states,
receipts/reports and actual event records. Originals are checked on read and again
before report publication; output SHA256 values are checked on download. Final
artifacts/state/events commit atomically. The ledger detects accidental tampering;
hashes are not signatures protecting against an attacker who can rewrite the DB
and every hash. Keep private DB files private and back them up offline.

Same run ID + same registered request returns its saved state/output without
re-execution. A different request for that ID is rejected. Use a new run ID for
new evidence or a new verifier revision. An OS runner lease prevents concurrent
workers for the same store. A later runner marks abandoned running jobs
`interrupted`; it never publishes or silently replays a partial result.

```powershell
.\.venv\Scripts\python.exe -m scripts.run --data-dir private/stage2 resume-queue
.\.venv\Scripts\python.exe -m scripts.run --data-dir private/stage2 cancel sample-stranded-41
.\.venv\Scripts\python.exe -m scripts.run --data-dir private/stage2 export sample-stranded-41 --output private/reports/stranded-copy
```

`resume-queue` processes queued jobs and marks abandoned running jobs interrupted.
After a process restart, use this explicit operation for remaining queued work.
Cancellation is observed between bounded operations and just before the atomic
publish; a single bounded ZIP/XML operation is not preempted halfway through.
Failed/cancelled/interrupted jobs have events/status but no success report.

Limits: four active queued/running jobs, one runner per store, 1000 stored runs,
512 MiB registered input storage; at most eight device archives + one server
capture, 64 MiB combined device/server-payload archive bytes (plus bounded metadata)
and 64 MiB aggregate expanded bytes,
1000 device versions, 20,000 receipts, 2000 events and 32 MiB outputs per job.
Run deadline is at most 300 seconds, checked cooperatively. Request JSON is
64 KiB; individual uploads are at most 10 MiB. Existing ZIP limits (500 entries,
32 MiB expanded/archive) and XML limits (1 MiB, depth 64, 10,000 nodes,
524,288 text characters) apply. New MAX_RUN_UNCOMPRESSED_BYTES and MAX_RUN_RECEIPTS
settings can lower their hard bounds. No untrusted paths are extracted to disk.

CLI exit 0 means a completed comparison (even with gaps), or a successful status/
cancel/queue operation. Exit 2 means invalid input, a failed/cancelled/interrupted
run or export failure. Never use exit 0 alone as preservation evidence.

## Reproducible samples and verification

`fixtures/stage2/{stranded,media,export,history}` each contains a full RunManifest,
device ZIP, server envelope/payload and hand-authored expected.json. Fixed seed 41
produces binary bytes, not imagery/recordings. Expected verdicts are literal,
independent of production comparison code. A test-only held-out seed 9087 changes
identities, paths and repeat count from two to five. The fixture builder never
invokes the comparator or providers to author expected results.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.build_stage2_fixtures
.\.venv\Scripts\python.exe -m scripts.verify_stage2_http
```

The HTTP verifier requires the real sample API running. It registers/uploads,
submits, polls and downloads all four reports, checks authored outcomes and all
output hashes, and rejects arbitrary paths/malformed ZIPs. Tests additionally
exercise offline network denial, input/output immutability, deadlines, queue
limits, cancellation, interrupted runners, hostile archives and scope failures.
