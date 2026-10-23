# Local integration setup — observed 2026-10-23

## ODK Central: connected smoke PASS

Official full Central release v2026.3.1, commit
`7d6de621955c5bb6a68e098ca10c9cbb92285cdf`; backend submodule
`de0d2a07fd7c9ff698cbc312e550dd40ff058340`. Checkout and runtime data are ignored
under `private/central`. Docker Compose project: `lastcopy-odk`.

Only nginx publishes `127.0.0.1:8384:80`. Application/database/Enketo services
remain on an internal Docker network; nginx additionally joins a host bridge
because Docker Desktop does not publish ports from an internal-only network.
Its upstream default Sentry CSP report hostname resolves to container loopback.
No public binding, firewall change, AWS provisioning or IAM change was made.
The official SSL-upstream mode supplies private loopback HTTP; this configuration
is unsuitable for a public deployment. Restart policies are disabled.

`scripts.setup_odk_test` checks the release pin and refuses differing config.
Its PostgreSQL build marker is created only for a verified empty dedicated stack,
following upstream's test image recipe. It never authorizes a database upgrade.
`scripts.seed_odk_test` checks the served version before writes, generates a local
test password and creates only its dedicated synthetic account/project/form and
native OpenRosa submission. It refuses remote or conflicting existing targets.
Credentials are saved only in ignored `.env`; no password is printed or committed.

Project 1: `LastCopy synthetic Stage 1`; form `inspection`; instance
`uuid:11111111-2222-4333-8444-555555555555`. Native upload preserved the original
fixture XML and attachment. The source archive hash remained unchanged.

The independent read-only smoke passed at `2026-10-23T18:02:54.153194+00:00`
in 5128.13 ms. It authenticated and fetched project metadata, submission versions,
exact version XML, attachment metadata and actual 59-byte attachment:

- XML SHA256: `714d1ae663fc4ce9235f9203deb2223c0e28c7de491c4a9d2b4921c8d129285b`
- Attachment SHA256: `e2a8e5636dac0d6601662dfc2df30c76337ab4d027e92b94e5c7e42b137458a4`
- Sanitized receipt: [odk-live-2026-10-23.json](verification/odk-live-2026-10-23.json).

Run the smoke from the repository root:

```powershell
$env:SAMPLE_MODE='false'
.\.venv\Scripts\python.exe -m scripts.smoke odk
Remove-Item Env:SAMPLE_MODE
```

The persisted default remains `SAMPLE_MODE=true`. To stop the local test stack
without deleting its data, from `private/central` run:

```powershell
docker compose -p lastcopy-odk -f docker-compose.yml -f lastcopy.local.yml stop
```

This is integration setup, not recovery implementation. Actual Collect export
format/version, edited historical versions and recovery writes remain unverified.

## Nightshift: installed and authenticated; inference blocked

Installed the official Windows 1.2.3 distribution at
`C:\Users\IYANUOLUWA\AppData\Local\Nightshift`. Installer exited 0; product
version is 1.2.3. Download and build-information sources:
[official download directory](https://meterless.ai/Nightshift/WIN/),
[vendor build information](https://meterless.ai/Nightshift/WIN/APP_BUILD_INFO.txt).

Installer SHA256 matched the vendor's published value:
`0679114b9096c6a2c787cad893802ed8be75cee867fabb07ea42ceab6b78b008`.
The vendor distribution is unsigned; no SmartScreen or other security warning
was bypassed. Installer and provenance files are ignored in `private/installers`.

The official app started its API at `http://127.0.0.1:8088/v1`.
`scripts.configure_nightshift` read only its own runtime proxy token, checked
wrong-token rejection (401), checked real authenticated model inventory (200),
and saved the three Nightshift variables only in ignored `.env`. No token is
in this document. The inventory includes `meterless/auto`, but listing a route
does not prove a local model is installed or loaded.

Real text smoke at `2026-10-23T17:51:48.854725+00:00` failed HTTP 400.
The bounded synthetic reproduction returned `no_provider_configured`:
"No provider is configured. Add a cloud key in Setup or install/start a local model."
Official CLI route preview also returned no candidates. No image/video generation
was requested. No cloud key, paid provider or large model fleet was added.

Remaining step: configure a text serving model in the installed app's Setup,
then rerun `scripts.smoke nightshift` with sample mode disabled. Native desktop
automation is unavailable in this session; no model-start API was invented.
Successful inference, tool/structured output capabilities and concrete serving
model identity remain unverified. The alias alone cannot establish Nemotron use.

## Zetaris: local bundle prepared; registry login pending

User supplied the Quickstart stack ARN in account `350353785155`, Singapore
(`ap-southeast-1`), stack `zetaris-miracle352-39fec9a1`. Screenshots then confirmed
six outputs containing network/role/bucket details but no endpoint; Zetaris shows
the AWS credential `miracle352` as Verified and no compute clusters. A Quickstart
stack is not proof of a running Zetaris service. The earlier deployment assumption
has been corrected. No authenticated AWS resources were accessed through tools.

After reviewing the displayed AWS cost estimate, the user chose **run locally
then launch later**. No AWS cluster is authorized now. The official getting-started
guides were downloaded to ignored `vendor/zetaris`, commit
`6a2fbaa47c32c9ac33f6584c64b43b146c621bed`.

Host preflight observed Docker Engine 29.9.1, Linux x86_64, 12 CPUs and
8,211,181,568 bytes of Docker RAM; host drive free space 167,677,751,296 bytes.
The existing ODK test stack is running and shares Docker resources. Only Docker
Desktop's internal WSL distribution is installed; the vendor's shell instructions
specify a user WSL2 environment with Docker integration. No configuration or image
pull has been attempted without the actual matching vendor bundle.

The [official local guide](https://github.com/zetaris/getting-started/blob/main/docs/install/updated_zetaris_installation_guide.md)
requires the platform ZIP, matching `.env`, issued registry access and evaluation
or licence entitlement. These are separate from the Apache-licensed recipe repo.
The user downloaded `zetaris-platform.zip` from the signed-in Run locally page.
Observed ZIP SHA256:
`14c6a811a140378bec1749ceffd7fa123bafb2f178545b26354e8f9433b413d3`;
27,996,894 bytes compressed, 31,245,009 expanded. This is an observed hash, not
a separately verified vendor signature. Paths and expansion bounds were checked
before extraction into ignored `private/zetaris-install/zetaris-platform`.

The actual bundle has three pinned Zetaris images (driver, API and UI) plus
PostgreSQL and one-shot init/bootstrap jobs; it does not include the AI service
listed in the general guide. Its original `.env` is preserved privately. The
guarded `scripts.setup_zetaris_local` generated new local admin/database passwords,
selected project `lastcopy-zetaris` to isolate its volumes, disabled automatic
restart and configured only loopback ports: UI 3130, API 18888, JDBC 11000 and
Spark UI 14040. PostgreSQL, the internal API and optional catalog HTTP port have
no host publication. Compose configuration validation passed, and resolved config
was inspected in memory without printing secrets. The application is not started.

The exact driver image manifest check returned `UNAUTHORIZED` / authentication
required. User action pending: follow the registry login instructions on
[Run locally](https://cloud.enterprise.zetaris.com/dashboard/download), usually
`docker login zetarishackathon.azurecr.io`, entering issued registry credentials
privately at the prompts. Portal/AWS login is not registry login. No registry
password or token is to be pasted into chat or committed. Image downloads,
startup, vendor verification and actual query remain pending this access.

After registry login: run the supplied preflight, verify image access, start
the official services and run the supplied
verifier plus `SELECT 1 AS one`. Check port 3000 for a LastCopy conflict. Only then
configure LastCopy's actual discovered query/auth contract and two-source smoke.

No S3 writes or live Zetaris query have occurred. Source registration, query/auth
contract and serving version remain genuine blockers. No running Zetaris or live
query verification success is claimed. A cloud launch later needs separate cost review.
