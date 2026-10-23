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

Verified: 54 Python tests, TypeScript, Next production build, 10 upstream tests,
8 conformance checks, actual reference bridge, raw fixture/receipt validation,
API/web boot, real browser sample flow, mobile/desktop review and npm audit zero.
See VERIFICATION.md for actual observations and the non-failing test-client warning.

## Integration verification and remaining Stage 1 blockers

Configure only this repository's ignored `.env`, without sharing tokens in chat:

1. Zetaris connection blocker resolved: official local 2.4.3.1 runs at
   http://localhost:3130. Vendor verification **9/9 PASS**; independent bounded
   two-source query **PASS** at 2026-10-23T19:13:04Z, with two expected rows and
   matching/mismatching synthetic hash values. Sources are actual registered CSVs
   in the local NDP file store (`dffs://lastcopy-stage1-smoke/`), not S3. Request
   contract/auth/version were observed from the shipped client and real API.
   Credentials stay in ignored config. Refresh an expired local session using
   `scripts.seed_zetaris_local --verify-existing`; no source writes in that mode.
   AWS remains unlaunched; AWS/S3 connector compatibility remains untested.
2. Nightshift 1.2.3 is installed from the official Windows installer, whose SHA256
   matched the vendor build information. The running loopback API rejected a wrong
   token (401) and accepted its real token for inventory (200). Config is saved in
   ignored `.env`. Actual text inference failed HTTP 400, `no_provider_configured`:
   no local serving model or cloud provider is configured. Inventory is a catalog,
   not proof of installed models. Model setup and real inference/capabilities remain
   blocked; concrete serving identity and Nemotron execution remain unverified.
3. ODK connection blocker resolved: official Central v2026.3.1 runs in the isolated
   `lastcopy-odk` Docker project at http://localhost:8384. Dedicated synthetic project
   1 contains the original fixture form/XML/media. Real read-only smoke **PASS** at
   2026-10-23T18:02:54Z, including authentication, version XML and attachment bytes.
   Setup was a synthetic test seed; no recovery feature was implemented. Credentials
   stay in ignored `.env`; sample mode remains the default. See LOCAL_SETUP.md.
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
