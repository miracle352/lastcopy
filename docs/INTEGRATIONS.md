# Integration path and rerunnable smoke checks

Checked official documentation on 2026-10-23. This is configuration guidance, not
evidence of successful live calls. No credentials were taken from another project.
All probes reject redirects, cap response bytes, use finite timeouts, and print
controlled diagnostics rather than exception bodies, tokens or full URLs.
Configure `.env` locally; it is ignored. Sample mode makes no network calls.

## Zetaris: local installation selected; AWS launch deferred

User screenshots confirmed a verified AWS Quickstart connection but no compute
clusters. The earlier assumption of an existing running AWS Zetaris instance was
incorrect. On 2026-10-23 the user selected local installation and deferred AWS
launch. See LOCAL_SETUP.md for distribution access and current prerequisites.
Do not launch a paid cluster or treat the Quickstart stack as a query endpoint.

The local 2.4.3.1 installation is now running at http://localhost:3130. The vendor
verifier passed all nine checks; LastCopy's independent real query across the two
registered local CSVs passed. Actual storage is NDP (`dffs://`), not S3; this does
not establish AWS/S3 connector behavior. The official S3 recipe below remains the
starting point for a future authorized S3 setup. The local NDP route was verified
against the actual shipped client and API, rather than assumed from a local cache.
See [local setup and exact receipts](LOCAL_SETUP.md).

References: [official small-file/S3 recipe](https://github.com/zetaris/getting-started/blob/main/open_data/parquet_csv/HOWTO.md),
[SQL companion](https://github.com/zetaris/getting-started/blob/main/docs/guides/zetaris-lightning-sql-companion.md).
Start with `fixtures/zetaris/device.csv` and `server.csv`: two and three rows,
synthetic identifiers and known hashes. They deliberately include a mismatch and
an unmatched row. Upload only these tiny files to an approved prefix on the
existing configured S3 bucket; no upload, IAM change or registration is automated.

The documented starting point is a logical database followed by CSV filestore
table registration. `fixtures/zetaris/register.sql.template` records the form.
Replace path/region/database placeholders with actual approved settings. Private
bucket access must use the deployment's supported credential configuration; do
not mark private objects public. A LIMIT is not a scan bound: these inputs must
remain the tiny fixtures, never a broad production prefix or wildcard.

The recipe establishes SQL syntax, not an HTTP authentication convention. Discover
the actual installed deployment's query request and response contract. Configure:

- `ZETARIS_SQL_ENDPOINT`: actual documented SQL-over-HTTP endpoint.
- `ZETARIS_HEADERS_JSON`: actual required headers/authentication; no guessed Bearer scheme.
- `ZETARIS_QUERY_FIELD`: actual JSON field containing SQL.
- `ZETARIS_ROWS_POINTER`: JSON pointer to rows; `/` means response is the array.
- `ZETARIS_DEVICE_TABLE`, `ZETARIS_SERVER_TABLE`: two distinct registered tiny tables.
- `ZETARIS_QUERY_OPTIONS_JSON`: optional additional body fields required by the
  actual endpoint. This local endpoint requires `{"pageLimit":3}`. Options cannot
  override the configured SQL field.
- `ZETARIS_SOURCE_PREFIX`, `ZETARIS_DEPLOYMENT_VERSION`: actual source scope and
  installed version. `ZETARIS_S3_PREFIX` remains a compatible legacy alias; local
  NDP storage must not be labelled as S3.

The adapter supports a single JSON POST SQL request with configured body options and a bounded JSON
row response. If the deployed interface uses JDBC, asynchronous jobs or a different
request shape, that adapter must be adjusted from its real documentation; this is
an explicit compatibility limitation. It is not evidence of a working connector.
The smoke performs an actual joined query, checks independently authored expected
rows, and records SQL, source names, rows, result hash and elapsed time. Registration
alone cannot pass it. It makes no registration requests and provisions nothing.

## Nightshift / Meterless Runtime

Reference: [official provider guide](https://github.com/Meterless/Meterless/blob/1742dec56a66e58eef9dda2d2b865823758ca8cd/docs/agent-ready/add-meterless-provider.md),
[hotspot](https://github.com/Meterless/Meterless/blob/1742dec56a66e58eef9dda2d2b865823758ca8cd/docs/products/nightshift/hotspot.md).
Set `NIGHTSHIFT_BASE_URL` (usual local URL `http://127.0.0.1:8088/v1`),
`NIGHTSHIFT_TOKEN` (real runtime token, not `rt-local`) and `NIGHTSHIFT_ROUTE` from
the actual authenticated inventory. Tokens stay in ignored server config.

Requests use Bearer authentication, `meterless-app: lastcopy`, and chat scope
`meterless-scope: user`. URL normalization handles `/v1`, `/v1/models`,
`/v1/chat/completions` and `/healthz`. The inventory decides authentication state;
health alone is insufficient. Cold inference timeout is 180 seconds, within a
300-second per-provider wall-time budget. HTTP 401/403 is explicitly unauthorized.

The smoke calls authenticated model inventory, a real text inference, then probes
function calls and strict structured output. Capability support requires observed
valid output, not merely HTTP 200. No function call from the model is executed.
Stage 3 must implement schema-validated action JSON and code-owned dispatch if
native tools are unavailable. A routing mode is not a serving-model identity.
Only a concrete model reported in the response can be recorded; missing concrete
identity stays unresolved. NVIDIA/Nemotron qualification is never inferred from
`meterless/auto`; its meaningful feature and serving trace remain Stage 3 work.

Live verification on 2026-10-23: authenticated inventory plus text inference
**PASS**, with concrete model `local-runtime/llama-3.2-1b-instruct` served by
Nightshift's single CPU lane. Strict JSON output passed; native tools were not
demonstrated. The 1B starter GGUF and setup procedure are pinned in LOCAL_SETUP.md.
Receipt: `verification/nightshift-live-2026-10-23.json`.

## Meterless World Model reference

Pinned upstream commit `1742dec56a66e58eef9dda2d2b865823758ca8cd`.
Vendored source, original tests, conformance runner, reference lock and Apache-2.0
license live under `third_party/world-model`. Files are unmodified upstream;
`SPEC.md` is the upstream `AGENTS.md`, renamed to distinguish upstream specification
from LastCopy's agent instructions. No upstream raster images are bundled.

`npm run smoke:world-model` actually ingests a synthetic snapshot observation,
re-ingests it to prove idempotency, and reads the graph for that snapshot.
`npm run test:world-model` and `npm run conformance:world-model` execute the
existing upstream controls. Stage 3 must make graph reads affect next actions;
the Stage 1 smoke does not claim that product integration is already implemented.
The reference uses memory/JSON storage, not a hosted engine. Its event/schema
behavior and limitations should be respected before production use.

## ODK Central read-only synthetic test scope

References: [authentication](https://docs.getodk.org/central-api-authentication/),
[submission/version/media APIs](https://docs.getodk.org/central-api-submission-management/),
[native OpenRosa submission](https://docs.getodk.org/central-api-openrosa-endpoints/),
[installation](https://docs.getodk.org/central-install/).

Configure `ODK_BASE_URL`, `ODK_EMAIL`, `ODK_PASSWORD`, `ODK_PROJECT_ID`,
`ODK_FORM_ID`, `ODK_SUBMISSION_ID`, `ODK_VERSION_ID`, `ODK_ATTACHMENT_NAME`,
`ODK_CENTRAL_VERSION` and `ODK_TEST_PROJECT=true`. Use a dedicated synthetic test
project with a known submission and attachment; never production credentials.
SSO-only Central does not support this email/password session flow.

The smoke logs in with POST `/v1/sessions` and keeps the returned token in memory.
It then uses documented Bearer session auth for project metadata, submission
version history, exact version XML, expected attachment slots and actual version
attachment bytes. Each path segment is URL-encoded. It validates the XML form and
version identity and records SHA-256 for retrieved bytes; `exists=true` alone is
never treated as proof. It makes no submission/media writes. Metadata reachability
is the connection check; no undocumented health/version endpoint is invented.
Central version is labelled operator-reported until tested against that installation.

Historical attachment writes are not promised. Native missing-submission retry
and supported missing-media writes must be tested in Stage 4; a 409 never permits
manufacturing another instance ID. Uncertain outcomes require readback first.

## Dedicated local Central setup (running and readback verified)

The official full Docker Compose stack is running on this host, pinned to
v2026.3.1 / `7d6de621955c5bb6a68e098ca10c9cbb92285cdf`. Connected read-only
smoke passed against the bundled synthetic XML/media. See [LOCAL_SETUP.md](LOCAL_SETUP.md)
for observed results, safety boundaries, exact commands and shutdown instructions.
To reproduce from a fresh ignored directory:

```powershell
git clone -c core.autocrlf=false https://github.com/getodk/central private/central
git -C private/central checkout v2026.3.1
git -C private/central submodule update --init --recursive
.\.venv\Scripts\python.exe -m scripts.setup_odk_test
Push-Location private/central
docker compose -p lastcopy-odk -f docker-compose.yml -f lastcopy.local.yml config
docker compose -p lastcopy-odk -f docker-compose.yml -f lastcopy.local.yml up -d --build
Pop-Location
.\.venv\Scripts\python.exe -m scripts.seed_odk_test
```

Wait for server startup before seeding. Setup refuses conflicting configuration
and only creates the upstream PostgreSQL marker on an empty test stack. Seeding
refuses a different connection/account/commit or conflicting existing fixture.
Only nginx publishes a port, bound to `127.0.0.1:8384`; application/data services
stay on an internal Docker network. Loopback HTTP uses upstream's SSL termination
mode for this private test only; no TLS verification is disabled. No public server,
cloud resources or IAM changes are involved. A real Collect export is still needed.
