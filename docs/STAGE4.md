# Stage 4: reviewed synthetic recovery

The deterministic verifier remains the authority. Recovery uses its existing
`reconcile()` implementation before every write and after fresh readback. A
completed investigation, a successful POST, a downloaded ZIP and verified
preservation are different states. No model/provider is involved in Apply.

Supported operations are creating an absent **original** submission with its
untouched original instance ID/XML/media, and filling a missing attachment slot
on the verified current original version. Historical writes, unknown completion,
missing original XForms/bytes, ambiguous mapping, conflicts and incomplete scope
are excluded. EXPORT_VIEW_ONLY never becomes an upload plan.

## Native protocol and semantic controls

The implementation follows official [OpenRosa submission documentation](https://docs.getodk.org/central-api-openrosa-endpoints/)
and [submission/version/attachment documentation](https://docs.getodk.org/central-api-submission-management/):

- Create: multipart `POST /v1/projects/{projectId}/submission`, original
  `xml_submission_file`, one file part per filename, X-OpenRosa-Version 1.0.
- Media: raw binary `POST /v1/projects/{projectId}/forms/{formId}/submissions/{originalId}/attachments/{filename}`.
- Readback: scoped submissions, versions, original version XML, expected
  attachment listings and the retrieved bytes for each accessible slot.
- There is no implemented historical attachment upload endpoint. No DELETE,
  attachment clearing, submission editing, new replacement ID or overwrite
  workaround is used. A 409 stops the attempt and requires fresh readback.

Historical controls cite the upstream [duplicate-reference fix and tests](https://github.com/getodk/central-backend/commit/1ef57ebc98ac12d1921bcd71840ee435ebcc4354)
and [identical-content attachment fix](https://github.com/getodk/central-backend/commit/236bb30e725e56bc62f5ec1ab490a9a233ea824a)
linked from [issue 299](https://github.com/getodk/central-backend/issues/299).
These are resolved historical regressions, not assertions of current defects.
Our synthetic fixture uses `sample.txt` twice and `a.bin`/`b.bin` with identical
authored binary/text bytes. Both distinct slots must be accessible. No community
recording, generated imagery or downloaded audio is packaged.

## Configuration and bounds

The existing ignored `.env` supplies ODK_BASE_URL, ODK_EMAIL, ODK_PASSWORD,
ODK_TEST_PROJECT=true and ODK_CENTRAL_VERSION. ODK_RECOVERY_PROJECT_ID and
ODK_RECOVERY_FORM_ID select the dedicated Stage 4 project separately from Stage 1.
ODK_CONNECTION_ID defaults to local-central-test; ODK_MAPPING_REFERENCE defaults
to configured-synthetic-test-project. ODK_RECOVERY_PROJECT_NAME defaults to
`LastCopy synthetic Stage 4 recovery` and is checked against native project
metadata. The concrete origin, deployment-version setting, target, original
version, source bytes and operation are sealed into the plan hash. Changes require
a new plan/review. Credentials are never included in bundles or receipts.

SAMPLE_MODE=true may stage/download/review eligible synthetic fixture bundles;
it cannot capture or Apply and never creates a Central client. Replay plans
cannot Apply. There is no implicit sample fallback on network failure.

Capture bounds: 30 submissions per form, 10 versions per submission, 50 slots per
version, 200 requests per capture, 1 MiB per response, 8 MiB aggregate bytes and
120 seconds. Apply has a 300-second deadline; response streaming checks it and
individual HTTP calls time out after 15 seconds. Existing ZIP/XML limits apply
to all captured/bundled data. The local ledger allows 1,000 plans, 500 events per
plan, 128 MiB bundles and 512 MiB recovery captures. Larger cases fail explicitly.

## CLI and HTTP

Start the single-user loopback API with connected settings only when needed:

```powershell
$env:SAMPLE_MODE='false'
$env:LASTCOPY_DATA_DIR='private/stage4/operator'
.\.venv\Scripts\python.exe -m uvicorn lastcopy.api:app --host 127.0.0.1 --port 8000
```

Register device ZIPs and an explicitly scoped connected RunManifest through the
existing `/inputs/device` and `/inputs/manifest` endpoints. Capture accepts only
registered IDs; it returns **new** immutable manifest/server IDs. Source snapshot
identities are parsed from the registered device manifests, never guessed from
their names/order. Use these IDs and the original device input IDs with `/run`.
Read the completed findings before staging a recovery operation.

| Action | Request |
|---|---|
| Capture | POST /recovery/capture `{manifest_id, device_input_ids}` |
| Stage | POST /recovery/plans `{run_id, finding_id}` |
| Inspect | GET /recovery/plans/{plan_id} |
| Download | GET /recovery/plans/{plan_id}/bundle |
| Review | POST /recovery/plans/{plan_id}/review `{plan_sha256, target}` |
| Apply | POST /recovery/plans/{plan_id}/apply `{plan_sha256, target}` |
| Status/readback | GET /recovery/plans/{plan_id}/result |
| Attempts | GET /recovery/plans/{plan_id}/events |
| Evidence object | GET /recovery/plans/{plan_id}/evidence/{sha256} |

`target` is the complete target object returned by the plan. Inspect its project,
form, identifiers, environment/origin, files, evidence, unsupported cases and
preconditions before confirming. Requests never accept filesystem paths or
arbitrary target URLs. JSON requests are capped at 64 KiB. Run/API and recovery
ledgers share immutable inputs but use separate OS leases.

The CLI uses exactly the same registered IDs, plan hashes and engine:

```powershell
.\.venv\Scripts\python.exe -m scripts.recover --data-dir private/stage4/operator capture MANIFEST_ID --device-input-id DEVICE_INPUT_ID
.\.venv\Scripts\python.exe -m scripts.recover --data-dir private/stage4/operator stage RUN_ID FINDING_ID
.\.venv\Scripts\python.exe -m scripts.recover --data-dir private/stage4/operator get PLAN_ID
.\.venv\Scripts\python.exe -m scripts.recover --data-dir private/stage4/operator bundle PLAN_ID --output private/recovery.zip
.\.venv\Scripts\python.exe -m scripts.recover --data-dir private/stage4/operator review PLAN_ID --plan-sha256 PLAN_SHA --target-sha256 TARGET_SHA
.\.venv\Scripts\python.exe -m scripts.recover --data-dir private/stage4/operator apply PLAN_ID --plan-sha256 PLAN_SHA --target-sha256 TARGET_SHA
.\.venv\Scripts\python.exe -m scripts.recover --data-dir private/stage4/operator result PLAN_ID --output private/recovery-result.json
```

Get/stage print TARGET_SHA from canonical target JSON. The plan hash also binds
the origin/version setting and source/evidence hashes. CLI output files are never
silently replaced. Bundles contain untouched instance XML, original XForms,
device manifest and required media, operation.json, before evidence and
instructions. Bundle creation is not recovery.

## Durable attempts and limits of assurance

SQLite commits write intent before calling the native transport. Attempt events
and capture objects have independent hashes. Results retain append-only revisions.
An OS lock serializes all recovery in this store, stronger than serialization per
submission. A crashed process releases that lock. A subsequent Apply reads fresh
state first. Unknown POST outcomes are never retried blindly. If everything is
already preserved, no POST occurs; a completed result is returned without repeating
work. A partial create that leaves missing media requires a newly reviewed media
plan. It does not re-upload XML as a shortcut.

Full capture is followed immediately by a scoped native preflight: absence for
create; current version, original XML and missing slot for media. Fresh original
XML, metadata and actual attachment bytes are fetched afterward and checked by
the same reconciler. Results include the operation's disappeared/remaining/new
conflicts and a run-wide delta, while retaining the full before/after findings and
coverage. Failed authenticated reads stop recovery; they do not prove absence.

Central offers no atomic compare-and-swap for attachment POST. This initial path
therefore requires an isolated dedicated synthetic test project without concurrent
external writers; the local lease cannot serialize other clients/stores. A
concurrent edit after the last preflight cannot be prevented transactionally by
these endpoints. Version drift/conflicting readback blocks verification. This is
not production multi-writer safety, historical repair or device-erasure approval.
The local unauthenticated API must remain bound to loopback. Browser UX is Stage 5.

## Reproduce live acceptance

Use the existing pinned local Central stack described in LOCAL_SETUP.md. Each tag
has deterministic fresh IDs. Reusing a completed tag is rejected; never delete
server data to recreate a missing-state demonstration.

```powershell
.\.venv\Scripts\python.exe -m scripts.verify_stage4_live --case media --tag NEW_TAG --api
.\.venv\Scripts\python.exe -m scripts.verify_stage4_live --case lost-ack --tag NEW_TAG
```

The first exercises actual HTTP port-8000 endpoints. The second exits its worker
with code 73 immediately after a real successful POST, before local acknowledgement,
then resumes through the documented CLI in a new process. Receipts retain actual
before/after capture bytes, request paths/statuses/hashes, comparator findings,
events, source hashes and output seals. Session/auth responses are excluded.
See HANDOFF.md for actual results and precise verification scope.
