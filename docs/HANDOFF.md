# LastCopy handoff

Current stage: **1 — contracts and runnable skeleton implemented, local checks
passed; live integration path not yet verified**. Prompt 0 persists in AGENTS.md.
The complete source packet is LASTCOPY_CODEX_PROMPTS.md. No later stage was run.

Implemented: Next.js/TypeScript diagnostic skeleton; local FastAPI health/config
and immutable bounded ZIP/XML inventory; explicit device, completion and run
mapping provenance; domain schemas with generated browser types; synthetic native
archive and raw snapshot envelopes; read-only repeatable provider smokes; actual
pinned Meterless bridge/tests/conformance; Product Contract, requirements register,
file-by-file stage plan, integration/compatibility/deployment guidance and locks.
No AI-generated imagery. No production/field data or recovery writes.

Verified: 41 Python tests, TypeScript, Next production build, 10 upstream tests,
8 conformance checks, actual reference bridge, raw fixture/receipt validation,
API/web boot, real browser sample flow, mobile/desktop review and npm audit zero.
See VERIFICATION.md for actual observations and the non-failing test-client warning.

## Genuine remaining Stage 1 blockers

Configure only this repository's ignored `.env`, without sharing tokens in chat:

1. Zetaris: `ZETARIS_SQL_ENDPOINT`, `ZETARIS_HEADERS_JSON`,
   `ZETARIS_QUERY_FIELD`, `ZETARIS_ROWS_POINTER`, `ZETARIS_DEVICE_TABLE`,
   `ZETARIS_SERVER_TABLE`, `ZETARIS_S3_PREFIX`, `ZETARIS_DEPLOYMENT_VERSION`.
   Register the tiny synthetic sources on the existing authorized AWS/S3 scope;
   verify the actual deployment's auth/query shape before configuring the adapter.
2. Nightshift: `NIGHTSHIFT_BASE_URL`, `NIGHTSHIFT_TOKEN`, `NIGHTSHIFT_ROUTE`.
   Real authenticated inventory/inference/capabilities and concrete serving-model
   identity remain untested. A routing alias cannot establish Nemotron execution.
3. ODK: `ODK_BASE_URL`, `ODK_EMAIL`, `ODK_PASSWORD`, `ODK_PROJECT_ID`,
   `ODK_FORM_ID`, `ODK_SUBMISSION_ID`, `ODK_VERSION_ID`, `ODK_ATTACHMENT_NAME`,
   `ODK_CENTRAL_VERSION`, `ODK_TEST_PROJECT=true`. Need dedicated synthetic
   server scope and known XML/media. Docker works; no Central instance was started.
4. Compatibility: obtain and record an actual Collect export/version and Central
   installation behavior. Current fixture explicitly uses unknown Collect version
   and is synthetic, not a live export. See COMPATIBILITY.md.

Then set `SAMPLE_MODE=false` and run each provider smoke separately. Do not label
Stage 1 live-verified until the real checks pass. Continue no dependent connected
feature on invented interfaces. No infrastructure, IAM or public ODK server should
be provisioned automatically.

## Next stage

Prompt 2, only when requested: deterministic namespace-aware ordered comparator,
historical-version/media-slot checks, SQLite run ledger, registered imports,
CLI and /run, three independently expected offline sample IO pairs plus held-out
controls. The current inventory endpoint does not reconcile or recover anything.

Private repository: https://github.com/miracle352/lastcopy . User will decide when
to make it public. Vercel deployment is explicitly authorized for this skeleton;
production is **READY** at https://lastcopy-five.vercel.app/ . Verified actual
hosted page, health HTTP 200 and inventory HTTP 503 with the explicit private-API
unavailable UI. Hosted skeleton must continue to say its private evidence backend
is unavailable. No provider credentials were deployed. The full runnable sample
inventory is local; hosting the private evidence API requires a later trust and
persistence design. See VERIFICATION.md for the exact application commit/receipt.

Launch commands and exact verification entrypoints: ../README.md.
