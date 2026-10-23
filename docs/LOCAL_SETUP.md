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

## Nightshift: local CPU text inference PASS

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

Resolved at 2026-10-23T19:39:31Z: authenticated text inference **PASS**
through `meterless/auto`, concrete reported identity
`local-runtime/llama-3.2-1b-instruct`, elapsed 9040.73 ms including capability probes.
Strict structured JSON was observed supported; native tool calls were not
shown. Stage 3 must validate action JSON and use a code-owned dispatcher.
No Nemotron model or NVIDIA award qualification is claimed.

Installed only the vendor WIN manifest's `starter-brain` text model:
`Llama-3.2-1B-Instruct-Q4_K_M.gguf`, 807694464 bytes, SHA256
`6f85a640a97cf2bf5b8e764087b1e83da0fdb51d7c9fab7d0fece9385611df83`.
Source: vendor manifest's bartowski Hugging Face mirror, repository revision
`067b946cf014b7c697f3654f621d577a3e3afd1c`; source header hash matched.
The runtime hardware assessment selected CPU and excluded the older integrated
Intel UHD GPU. Its installed shell exposed `/admin/lanes` and lane start controls
on the per-user named pipe; these were confirmed against the live daemon.
The setup uses one `lastcopy-text` lane, context 2048, parallel 1, no autostart.
No media engine, cloud key or larger model fleet was configured.

Rerun from the repository with the official app running:

```powershell
node scripts/setup_nightshift_text.mjs private/installers/Llama-3.2-1B-Instruct-Q4_K_M.gguf
$env:SAMPLE_MODE='false'
.venv\Scripts\python -m scripts.smoke nightshift
Remove-Item Env:SAMPLE_MODE
```

The setup checks runtime ownership/version and the GGUF hash before installation,
refuses to replace a different model/lane, and saves a sanitized installation
receipt. Setup alone is not inference proof; the separate smoke is required.
Receipts: `verification/nightshift-live-2026-10-23.json` and
`verification/nightshift-text-installation-2026-10-23.json`.

## Zetaris: local installation and two-source smoke PASS

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
recommend a user WSL2 environment with Docker integration. On this host the supplied
scripts ran unchanged with Git for Windows Bash and `MSYS_NO_PATHCONV=1` against
Docker Desktop's Linux engine. Docker VM disk capacity was checked separately.
No user Linux distribution was installed. The actual vendor preflight passed all
required checks, with one warning: it truncates Docker memory to 7 GiB against an
8 GiB recommendation (actual allocation approximately 7.65 GiB).

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
was inspected in memory without printing secrets. All four persistent services
are now healthy; init and bootstrap finished with exit 0. The existing ODK test
stack remained running throughout.

The first registry check returned authentication required. The user then completed
the issued registry login privately. All exact matching images were downloaded;
immutable digests are recorded in
[image provenance](verification/zetaris-images-2026-10-23.json). Platform image
files, registry credentials, admin passwords, session tokens and query cursors
remain outside version control.

Observed verification:

- Real local login plus `select 7 as seven`: PASS, one named cell `seven=7`.
  First cold check took 57499.84 ms. Sanitized
  [installation receipt](verification/zetaris-local-installation-2026-10-23.json).
- Official `verify.sh`: **9/9 PASS** after the sample bootstrap completed.
  [Original output](verification/zetaris-vendor-verify-2026-10-23.txt).
  Its final line hardcodes the default port 3000; the actual configured and
  browser-verified URL is **http://localhost:3130/login**.
- Actual `/api/proxy/utility/version` reported API and driver **2.4.3.1**.
- Only the two bundled synthetic CSVs were uploaded to the local NDP file store,
  then registered as `lastcopy_stage1.device_evidence` and
  `lastcopy_stage1.server_evidence`. Original CSV byte hashes remained unchanged.
  [Source verification](verification/zetaris-local-sources-2026-10-23.json).
- Independent `scripts.smoke zetaris`: **PASS** at 2026-10-23T19:13:04Z,
  elapsed **8802.67 ms**. The actual engine-side join returned the two expected
  rows, including the synthetic mismatch; an unmatched source row was excluded.
  SQL, source names, rows, row hash and elapsed time are in the
  [connected receipt](verification/zetaris-live-2026-10-23.json).

This storage is `dffs://lastcopy-stage1-smoke/`, not AWS/S3. The public official
S3 recipe was reviewed first; the local NDP request contract and path construction
were established from the actual shipped client and verified by real requests.
Upload uses multipart `path` and repeated `files` at `/api/proxy/ndp-files/save`;
registration uses `/api/proxy/sql-editor/sqls/run-query` with `sql`. The final
read-only query uses `/api/proxy/query/sql/start` with `select` and `pageLimit:3`,
Bearer session auth and the actual login's `X-Org-ID`; rows are at `/records`.
The generic smoke now supports configured body options. A missing `pageLimit`
caused the first independent smoke to return 400; its corrected rerun passed.

A temporary Windows rename-access failure occurred while saving root `.env`
after initial registration and a successful join. No source writes were replayed.
`--verify-existing` rechecked the existing sources and saved a durable receipt
before retrying local config writes. Initial DDL response hashes were not retained;
the source receipt honestly has an empty registration-statement receipt list.
Dotenv temporary files are ignored. No credentials or query cursor are committed.

Local admin email is `lastcopy-admin@example.invalid`; its generated password is
the `ZETARIS_ADMIN_PASSWORD` value in the ignored bundle `.env` at
`private/zetaris-install/zetaris-platform/.env`. This is separate from portal and
registry credentials. Do not paste it into chat. Root `.env` holds only the local
connection settings needed by LastCopy; its default remains `SAMPLE_MODE=true`.

Rerun the read-only connected probe from the repository root:

```powershell
$env:SAMPLE_MODE='false'
.\.venv\Scripts\python.exe -m scripts.smoke zetaris
Remove-Item Env:SAMPLE_MODE
```

When the local session expires, refresh it without source uploads or DDL:

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_zetaris_local --verify-existing
```

To stop or start this installation while retaining its data, from the bundle
directory use `docker compose stop` or `docker compose start`. Never use
`down -v` for routine shutdown. Future AWS launch still requires cost review;
no AWS cluster, source upload, IAM change or S3 connector verification occurred.

## Actual Collect emulator capture

User requested an Android emulator because no phone was available. Official Google
repository metadata pinned platform-tools 37.0.1, Emulator 37.2.12 and the AOSP
API 30 x86_64 image revision 11. Downloaded archive SHA1 checksums matched Google's
metadata before extraction. ODK Collect v2026.3.5 APK matched the release SHA256
`82f3fa0d5b95a650f591c0f74a9b920fef448e45c02523a3aaf9505848c91a24`.
All SDK, image, AVD and raw export files are ignored under `private/android`.
The existing WHPX hypervisor was usable; no Windows feature change was required.
No Java/Android Studio installation or Google account was needed.

Only AVD `LastCopyCollect` / `emulator-5558` was used. Collect's launch activity
was resolved from the installed package. Its local project points at the emulator
host alias `http://10.0.2.2:8384`, with no credentials and no server submission.
The synthetic XForm was transferred into its own project with `adb push`.
AOSP debug `adb root` was used for scoped-storage access; the imported file's UID
and SELinux category were matched to Collect-created files. No enforcement was
disabled. This emulator procedure is not advice to root a field phone.

Entered `0017`, repeat values `03` and `05`, and selected the 67-byte synthetic
text file through Android's document picker. Collect renamed the copied attachment
and generated its own instance UUID. Finalize succeeded. After force-stopping the
app, `adb pull` copied the dedicated project. The native database selected row 2
has status complete and a finalization timestamp. The first record is a retained
namespace-mismatch control; only the second record is in the supported manifest.

`scripts.capture_collect_fixture` is a narrow one-time capture packager, not a
universal exporter. It reads the already-copied database read-only, refuses an
existing output directory, checks actual identities/answers/media, retains bytes
and paths, and runs LastCopy inventory. The reusable verification is:

```powershell
.venv\Scripts\python -m scripts.inventory fixtures/collect-v2026.3.5/device.zip
.venv\Scripts\python -m pytest -q tests/test_collect_capture.py
```

References: [Collect release](https://github.com/getodk/collect/releases/tag/v2026.3.5),
[official adb workflow and project paths](https://docs.getodk.org/collect-adb/),
[emulator command line](https://developer.android.com/studio/run/emulator-commandline),
[Google package downloads](https://developer.android.com/studio#command-tools).

The emulator was stopped after capture. ODK/Zetaris test containers had been
paused to free memory and were restored afterward. Nightshift's test text lane
was stopped to release memory; its verified model and configuration remain.
