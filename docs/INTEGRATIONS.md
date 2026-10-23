# Integration path and rerunnable smoke checks

Checked official documentation on 2026-10-23. This is configuration guidance, not
evidence of successful live calls. No credentials were taken from another project.
All probes reject redirects, cap response bytes, use finite timeouts, and print
controlled diagnostics rather than exception bodies, tokens or full URLs.
Configure `.env` locally; it is ignored. Sample mode makes no network calls.

## Zetaris: reuse the existing AWS deployment

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
- `ZETARIS_S3_PREFIX`, `ZETARIS_DEPLOYMENT_VERSION`: actual source scope and installed version.

The adapter presently supports a single JSON POST SQL request and a bounded JSON
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

## Optional local Central setup (prepared, not started)

Docker Engine is installed and reachable outside the Codex sandbox on this host.
An ODK server has not been configured. Follow the official Docker Compose
installation rather than inventing a reduced Central service:

```powershell
git clone -c core.autocrlf=false https://github.com/getodk/central private/central
git -C private/central submodule update --init --recursive
```

Select and record an actual release/commit before starting. Follow its `.env`
and Compose instructions. For local testing use a Linux VM/WSL2 as recommended,
and override every published Compose port to `127.0.0.1` with unused host ports.
Inspect `docker compose config` for exposed ports before `up`; do not expose a
public server or change firewall/IAM. Configure the local TLS/trust arrangement
from upstream guidance rather than disabling TLS verification in LastCopy.
Create a dedicated synthetic project/form/submission using the bundled fixture,
record the real Central and Collect versions, then run the read-only smoke.
Container-to-host access, if later required, must be explicitly configured and
documented; defaults here use loopback with native host processes.
