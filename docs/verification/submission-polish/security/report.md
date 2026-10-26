# Security Review: security-source-20261026

## Scope

Authorized sanitized 397-file snapshot, archive SHA-256 2b559ec05d25a3f496e3dd2afeabb06b8cce0e5aaa563c26cc7840f0923a4321. Git revision is its parent metadata; this snapshot includes uncommitted changes.

- Scan mode: repository
- Target kind: git_revision
- Target ID: target_sha256_0ad1e857a916070b3a8f10fa239b16d987778ecd6bc882f4e616705789263790
- Revision: 94ce7d122acaeb0407aac94f55b16f070ded0aa0
- Inventory strategy: repository
- Included paths: .
- Excluded paths: none
- Artifacts reviewed: artifacts/baseline.json, artifacts/web-review.json, artifacts/data-review.json, artifacts/structural-review.json
- Scan context: Generated source-backed threat model from an independent architecture reviewer. Independent baseline and focused browser/data reviews; no deployment or penetration-test claim.

Limitations and exclusions:
- Font binaries were checked for provenance/hash/local serving, not reverse-engineered. Third-party dependencies were reviewed as source/lock entries; this is not a complete transitive dependency implementation audit.
- Live OS/IAM/Cognito/Central settings, physical devices, native browser zoom and signed-in organizer template are not established by source review.
- Validation imports created ignored __pycache__ files under snapshot; original source file bytes remain unchanged.
- Excluded web/public/fonts/\*.woff2: Local licensed font provenance/hash/size checked; font binary reverse engineering excluded.
- Excluded private/\*\*, live configuration and external services: Private credentials/evidence/build trees excluded from sanitized target; no live deployment or external penetration-test scope.

### Scan Summary

| Field | Value |
| --- | --- |
| Scan outcome | completed |
| Reportable findings | 2 |
| Severity mix | medium: 2 |
| Confidence mix | high: 2 |
| Coverage | complete |
| Validation mode | Offline static audit plus bounded parent regression validation outside immutable source snapshot |

Canonical artifacts: `scan-manifest.json`, `findings.json`, and `coverage.json`. This report is a deterministic projection of those files.

## Threat Model

LastCopy compares original ODK Collect ZIP/XML/media with captured Central evidence, persists content-addressed originals and deterministic reports in SQLite, and offers explicitly reviewed recovery only for synthetic sources and a configured synthetic Central project. FastAPI owns evidence access, session validation, parsing, comparison, device delivery and recovery. Next.js provides the browser interface and a restricted server-side API proxy. Supported execution paths materially differ: Windows loopback processes; a local sample Docker container; AWS Next.js/FastAPI sharing one unprivileged container behind Caddy; and Vercel either acting as an earlier HTTPS API proxy or a later landing/workspace gateway. The inspected source is a sanitized snapshot, not proof of current deployment configuration. Sources: lastcopy/api.py:28, lastcopy/api.py:33, lastcopy/api.py:144, lastcopy/store.py:29, lastcopy/recovery.py:71, scripts/start_realtime.ps1:50, scripts/container_start.py:22, deploy/aws/compose.api.yaml:7, deploy/aws/prepare-https.sh:12, web/lib/backend.ts:3.

### Assets

- Original device/server archives, manifest identities and hashes; reports, receipts, recovery plans/results and sealed investigation evidence. RunStore stores original bytes and verifies their kind-bound content identity on retrieval; artifact downloads verify stored hashes. Sources: lastcopy/store.py:51, lastcopy/store.py:80, lastcopy/store.py:148.
- Account identity and isolation: Cognito verifies credentials/email; the server derives account directory names from SHA-256 of the verified immutable Cognito sub. Root account/session tables and each account's evidence database must remain private. Sources: lastcopy/accounts.py:114, lastcopy/accounts.py:128, lastcopy/accounts.py:164.
- Owner passphrase hash, transport/session/device keys, account Central credentials, direct NVIDIA key, SSH private key, backup uploader credentials and backup recipient private key. Configuration files have different recipients and protection mechanisms; they are not interchangeable capabilities. Sources: lastcopy/cloud_access.py:20, lastcopy/account_connection.py:104, lastcopy/cloud_ai.py:66, scripts/setup_cloud_project.py:14, scripts/backup_offsite.py:82, docs/RISK_AUDIT.md:72.
- Central collection records and their XML/media are read assets; the separately configured synthetic project grants conditional recovery write authority. Setup assigns the automation actor Viewer on collection and Manager on recovery; actual Central role state remains external to this snapshot. Sources: scripts/setup_cloud_project.py:67, lastcopy/odk_recovery.py:18, lastcopy/odk_recovery.py:171.
- Encrypted database backups and the ability to decrypt them. Backups include every nested application lastcopy.sqlite3, allowlisted sealed investigation evidence and a Central PostgreSQL dump; adjacent configuration files are excluded. Sources: scripts/backup_databases.py:12, scripts/backup_databases.py:36, scripts/backup_databases.py:75.
- Shared storage, worker capacity, authentication/email budget, provider credits and operator hosting budget. Accounts are limited to 100 MiB registered input, 25 saved jobs and four active account checks across accounts; new account creation is bounded to 100. Sources: lastcopy/accounts.py:25, lastcopy/accounts.py:37, lastcopy/accounts.py:96, lastcopy/accounts.py:114.

### Trust Boundaries

- Browser to Next.js proxy: Host/origin validation, explicit route allowlists, fixed server-configured upstream destination, request-size limits, redirect rejection and no-store responses constrain the proxy. The proxy adds the server transport key and forwards only the shaped session cookie. Browser-supplied headers do not select an upstream URL. Sources: web/lib/backend.ts:15, web/lib/backend.ts:24, web/lib/backend.ts:35, web/app/api/service/\[...path\]/route.ts:5, web/app/api/service/\[...path\]/route.ts:16.
- Next.js or device relay to hosted FastAPI: normal hosted traffic first needs the transport key. Owner-session validation grants operator access; otherwise an account session selects a restricted account store. A distinct device key is accepted only for POST /device-transfer and GET /device-transfer/status. Fixed public-demo and account-authentication operations are explicit session exceptions, still behind hosted transport. FastAPI validates local Host and Origin separately. Sources: lastcopy/api.py:29, lastcopy/api.py:33, lastcopy/api.py:122.
- Cognito to local account/session authority: server performs InitiateAuth followed by GetUser, requires email_verified=true and derives the local account from the returned sub. Cognito access tokens are consumed server-side. Browser sessions are random, HMAC-digested in SQLite, eight-hour and revocable; login cookies are Secure, HttpOnly and SameSite=Strict. Sources: lastcopy/accounts.py:114, lastcopy/accounts.py:128, lastcopy/accounts.py:164, lastcopy/cloud_access.py:36.
- Account session to evidence resources: account files resolve beneath root/accounts/\<sha256-sub\>/, with lastcopy.sqlite3 and optional central-connection.json. Account Settings inherit only configured limit keys, account mode and the operator-approved Central origin before loading the account's own connection. This is application-level isolation within the same process/container UID, not separate OS tenants. Sources: lastcopy/accounts.py:128, lastcopy/account_connection.py:39, lastcopy/store.py:29, deploy/aws/Dockerfile.api:17.
- Untrusted archives/XML/media to deterministic evidence processing: ZIP inputs remain in memory rather than being extracted; safe relative paths, duplicate normalization, symlink/encryption rejection, archive count/size bounds, defused XML and depth/node/text bounds apply. Content completion and source identity come from validated manifests/evidence rather than XML presence alone. Sources: lastcopy/inventory.py:22, lastcopy/inventory.py:60, lastcopy/inventory.py:97, lastcopy/models.py:8.
- Account connection setup to Central: users provide project/form identity and credentials but cannot choose the destination origin. The origin is copied from the operator's ODK_BASE_URL and must be HTTPS without userinfo/path/query/fragment. Setup authenticates and verifies project/form identity before atomically storing the connection mode 0600. Central responses have call/time/per-response/aggregate limits, and requests disable redirects/environment proxies. Sources: lastcopy/accounts.py:133, lastcopy/account_connection.py:30, lastcopy/account_connection.py:62, lastcopy/odk_recovery.py:39, lastcopy/odk_recovery.py:59.
- Reviewed plan to recovery writes: source archives must explicitly be synthetic; completion, coverage, original XML/media and edit-chain checks precede staging. Apply binds persisted plan hashes, target and environment to current configuration, requires explicit review, uses an OS-backed lease, captures fresh evidence and performs immediate Central preconditions. CentralRecovery rejects read-only connections and non-synthetic destinations. Central has no atomic attachment compare-and-swap, so an isolated project without concurrent external writers is an explicit prerequisite. Sources: lastcopy/recovery.py:71, lastcopy/recovery.py:243, lastcopy/api.py:215, lastcopy/odk_recovery.py:171.
- Paired Windows emulator to AWS inbox: operator-controlled adb reads forms/instances/metadata from one configured native project using an argv subprocess and bounded stdout/time. Link configuration selects one HTTPS origin and device key. Cloud delivery verifies roster/form scope, stores received-\<sha256\>.zip and its readiness seal in /app/private/inbox, and returns a hash/length/kind-bound acknowledgement. Desktop receipt validation precedes marking delivery complete. Sources: lastcopy/device_transfer.py:87, lastcopy/device_transfer.py:138, scripts/prepare_cloud_device.py:64, lastcopy/cloud_relay.py:40, lastcopy/cloud_inbox.py:45.
- Private evidence to public demonstration: fixed cases use root/public-examples/lastcopy.sqlite3 with independently constructed sample-only Settings, not owner/account stores. Browser demo proxy strips the session cookie, allows only fixed cases/actions and sends no uploaded file body. Sources: lastcopy/public_demo.py:20, web/app/api/demo/\[...path\]/route.ts:4, web/app/api/demo/\[...path\]/route.ts:12.
- Owner to cloud AI and synthetic sponsor investigation: cloud setup independently requires an owner session and connected mode. NVIDIA credentials are stored in application/cloud-ai.json; fixed NVIDIA endpoints consume them. The test sends synthetic fixture material, retains deterministic verifier authority and has persisted setup/test budgets. Connected sponsor investigation requires a completed authenticated synthetic capture and synthetic source manifests; it launches a worker process with operator process environment plus store settings. Sources: lastcopy/cloud_ai.py:48, lastcopy/cloud_ai.py:59, lastcopy/cloud_ai.py:117, lastcopy/cloud_ai.py:146, lastcopy/nvidia_cloud.py:25, lastcopy/ui_investigation.py:23.
- Account to export/erasure workflow: only AccountStore instances receive privacy controls. Export reads only that account's inputs/artifacts, rechecks hashes/identities, uses bounded count/bytes/time and excludes session, provider and connection files. Erasure creates an awaiting_operator_review row; it performs no deletion or immediate account closure. Sources: lastcopy/account_privacy.py:16, lastcopy/account_privacy.py:44, lastcopy/account_privacy.py:53.
- Privileged host/deployment/backup operators to production resources: AWS compose loads /srv/lastcopy/private/api.env and maps application/inbox host directories. Caddy independently terminates public HTTPS; the API/upstream Host is rewritten to localhost. The root-run backup service can invoke Docker pg_dump and write backups/operation receipts. Offsite upload uses a separate mode-0600 credential file and fixed S3 destination. These capabilities are operator authority, not public-account authority. Sources: deploy/aws/compose.api.yaml:7, deploy/aws/prepare-https.sh:12, deploy/aws/lastcopy-backup.service:6, deploy/aws/backup-databases.sh:10, scripts/backup_offsite.py:77.

### Attacker Capabilities

- Unauthenticated internet users can reach public Next.js pages, account-authentication forms and fixed public-demo routes in hosted mode; they do not start with transport, owner, device, Central or SSH credentials. Hosted FastAPI separately enforces transport and session exceptions. Sources: lastcopy/api.py:33, web/app/api/account/\[action\]/route.ts:3, web/app/api/demo/\[...path\]/route.ts:4.
- A verified beta account can upload its own ZIP/manifest/server inputs, run supported account checks, configure its own Central project/form credentials at the approved origin and request its own export/erasure review. It cannot select another account directory through a request, inherits no owner/provider/device/session keys and is restricted to the API account route set. Sources: lastcopy/accounts.py:128, lastcopy/api.py:50, lastcopy/account_connection.py:17, lastcopy/account_privacy.py:16.
- An adversary may control archive contents, XML/media names and bytes, supplied manifests, supported request bodies, identifiers and browser headers, plus the content of Central/provider responses when those external services or the user's account content are untrusted. Parser, response-size and identity boundaries therefore matter independently of a hosted deployment. Sources: lastcopy/inventory.py:22, lastcopy/inventory.py:60, lastcopy/api.py:260, lastcopy/odk_recovery.py:59.
- Possession of the device key grants scoped delivery and polling only; possession of the server transport key alone does not grant private owner/account reports. Owner-session and account-session digests are looked up in the root durable ledger. Sources: lastcopy/api.py:40, lastcopy/cloud_access.py:39, lastcopy/accounts.py:128.
- Local Windows user, AWS host administrator, Docker operator, production deployment account and backup IAM administrator are trusted privileged actors. This review does not assume their credentials or filesystem are attacker-controlled. The supported local mode relies on OS user/loopback trust and does not create account isolation when cloud access is disabled. Sources: scripts/start_realtime.ps1:50, lastcopy/api.py:38, scripts/setup_cloud_project.py:14.
- A boundary failure could add access to another account's source bytes, operator credentials, unintended remote destinations, production Central writes, provider spending or host execution. These are protected capability categories, not findings established by this architecture pass.

### Security Objectives

- User-provided objective: preserve strict account separation, server-only credentials, bounded upload/parsing/network/jobs, synthetic-only recovery, scoped exports and reviewed erasure requests, and encrypted offhost backups.
- Preserve immutable original bytes and report provenance; validate identifiers, hashes and scope on reads and downloads. Sources: lastcopy/store.py:70, lastcopy/store.py:80, lastcopy/store.py:148.
- Require the appropriate combination of transport key, owner/account session or separately scoped device key at each hosted entry point; retain independent browser Host/origin controls. Sources: lastcopy/api.py:33, lastcopy/api.py:122, web/lib/backend.ts:15.
- Use verified server-side identity to select an account's store and never inherit operator credentials into the account Settings object. Sources: lastcopy/accounts.py:128, lastcopy/accounts.py:164.
- Keep ZIP/XML requests and HTTP responses within finite count, memory, decompression and execution budgets; preserve finite shared beta quotas and free-space reserve. Sources: lastcopy/config.py:15, lastcopy/inventory.py:22, lastcopy/inventory.py:60, lastcopy/accounts.py:25, lastcopy/odk_recovery.py:59.
- Keep account-requested Central destinations fixed to the operator-approved HTTPS origin and sensitive network calls free of redirects/environment proxy influence. Sources: lastcopy/account_connection.py:30, lastcopy/account_connection.py:68, lastcopy/odk_recovery.py:49.
- Never write collection records through recovery. Require sealed plan/target/environment review, original synthetic evidence, fresh preflight/readback, and safe handling of lost acknowledgements. Sources: lastcopy/recovery.py:71, lastcopy/recovery.py:243, lastcopy/odk_recovery.py:171.
- Public examples and provider smoke tests must use isolated synthetic material and never expose private source archives or imply model authority over deterministic preservation verdicts. Sources: lastcopy/public_demo.py:20, lastcopy/cloud_ai.py:146, lastcopy/nvidia_cloud.py:37.
- Export only the authenticated account's verified originals/reports. Treat erasure as a reviewed operational request and do not promise current automatic deletion or expiry of retained backups. Sources: lastcopy/account_privacy.py:25, lastcopy/account_privacy.py:44, lastcopy/account_privacy.py:53.
- Encrypt before offhost transmission, exclude environment/provider configuration files, verify ciphertext receipt/readback, retain older copies and stop at finite local/offsite storage bounds. The uploader's IAM policy must remain narrower than host/database authority. Sources: scripts/backup_databases.py:59, scripts/backup_databases.py:70, scripts/backup_offsite.py:36, scripts/provision_backup_storage.py:16.

### Assumptions

- Scope is the complete sanitized source snapshot. No application code, tests, network calls, credentials, live configuration, git history or exploitation inputs were executed/read. Architecture coverage is not a completed vulnerability audit.
- The security-policy helper returned exit 0 with no output, and source inventory showed no SECURITY.md. Repository AGENTS.md/docs are source context, not authority overriding the caller's read-only/offline instructions.
- AWS host paths, URLs and configured project IDs are supported by setup source; current env_file contents, Caddy state, mounted ownership/modes, SSH/firewall settings, Central assignments, Cognito policies and IAM deployment were not independently observed. Sanitized verification artifacts are absent.
- Vercel has two supported configurations: configure_vercel_cloud.py sets an earlier HTTPS API proxy with transport key, while web/lib/backend.ts and service routes implement a WORKSPACE_ORIGIN gateway. CLOUD_PILOT.md describes the later landing/workspace arrangement. Exact production environment cannot be inferred from the earlier script. Sources: scripts/configure_vercel_cloud.py:15, web/lib/backend.ts:3, web/app/api/service/\[...path\]/route.ts:8, docs/CLOUD_PILOT.md:57.
- Backups are not whole-machine recovery: Central/Enketo configuration and link keys, environment/provider credentials and future external attachment storage require separate procedures. The recipient private key's Windows location and restricted ACLs are documented, not reproduced in an inspected provisioning script. Sources: scripts/backup_databases.py:1, scripts/backup_databases.py:82, docs/RISK_AUDIT.md:72.
- Offsite support exists in source but activation is unresolved. backup-databases.sh invokes upload only if backup-uploader.json exists; FINAL_GAP_CLOSURE.md says AWS authentication/activation remain pending, while older RISK_AUDIT.md says unattended offhost replication is not configured. Neither a code path nor a proposed S3/IAM configuration proves deployed replication. Sources: deploy/aws/backup-databases.sh:16, docs/FINAL_GAP_CLOSURE.md:19, docs/RISK_AUDIT.md:91.
- The proposed retention description mentions immediate closure revocation, but implemented privacy control only records an erasure-review request. Current interface explicitly reports no automatic deletion and inactive expiry. Treat closure revocation/erasure operations as unimplemented operational policy, not existing product behavior. Sources: docs/FINAL_GAP_CLOSURE.md:26, lastcopy/account_privacy.py:25, lastcopy/account_privacy.py:44.
- The read-only Central wrapper prevents its write method, but the remote account's Viewer role is an operator responsibility verified externally. Account setup authenticates and checks project/form identity; it does not itself inspect Central role assignments. Sources: lastcopy/account_connection.py:86, lastcopy/odk_recovery.py:171.
- Central attachment writes lack atomic compare-and-swap. Synthetic target isolation from concurrent external writers remains a prerequisite even with immediate XML/version/slot checks and readback. Sources: lastcopy/odk_recovery.py:175, lastcopy/recovery.py:243.
- All application account/demo/owner stores share one container UID and application mount. Directory separation and request-selected Settings are application controls; no separate per-account OS/container boundary is established. Sources: lastcopy/accounts.py:138, lastcopy/public_demo.py:23, deploy/aws/Dockerfile.api:17.
- Windows file creation mode 0600 in cross-platform Python is not evidence of a specific Windows ACL. Local account security and private-file protections require host controls; source shows an explicit Windows locking branch but no general ACL provisioning for generated local cloud configuration. Sources: scripts/prepare_cloud_access.py:19, scripts/prepare_cloud_device.py:70, lastcopy/store.py:173.
- Cloud sponsor runtime readiness is not established by source. The actual Zetaris consumer imports a hardcoded local verifier using http://localhost:3130 and an ignored local bundle, rather than consuming ZETARIS_SQL_ENDPOINT for that path. A deployed synthetic investigation worker inherits the parent process environment and requires the local dependency/runtime assumptions to hold. Sources: lastcopy/connected.py:14, scripts/verify_zetaris_local.py:16, scripts/verify_zetaris_local.py:27, scripts/setup_zetaris_local.py:10, lastcopy/ui_investigation.py:44.

## Findings

| Finding | Severity | Confidence | Detailed write-up |
| --- | --- | --- | --- |
| [Native Collect metadata query materializes unbounded rows before its limit](#finding-1) | medium | high | inline below |
| [Bounded XML inputs amplify into gigabytes of retained ancestor paths](#finding-2) | medium | high | inline below |

### Confidence Scale

| Label | Meaning |
| --- | --- |
| high | Direct evidence supports the finding with no material unresolved blocker. |
| medium | Evidence supports a plausible issue, but material runtime or reachability proof remains. |
| low | Evidence is incomplete and the item is retained only for explicit follow-up. |

<a id="finding-1"></a>

### [1] Native Collect metadata query materializes unbounded rows before its limit

| Field | Value |
| --- | --- |
| Severity | medium |
| Confidence | high |
| Confidence rationale | Independent source audit and parent verification traced real callers and controls. Bounded regression demonstrates missing rejection on old code, acceptance after fix; no multi-gigabyte exploit executed. |
| Category | Unbounded derived work |
| CWE | CWE-400 |
| Affected lines | lastcopy/device_transfer.py:26-52, lastcopy/device_transfer.py:204-228, scripts/package_collect_project.py:31-38 |

#### Summary

Compact SQLite instances view with recursive/expansive query or computed large values can occupy native transfer indefinitely or exhaust shared API memory.

#### Root Cause

Read-only SQLite permits expensive views and values; SELECT \* materializes rows before enforcing its limit.

#### Validation

Parent inspected every cited source range and actual registration/device-transfer callers. Old-code negative controls failed as expected; current targeted parser/native-transfer suite passed 20 tests. Full core suite passed 256 with one Windows skip.

Validation method: Offline source validation plus bounded local regression tests; no memory-exhaustion attack run

#### Dataflow

DeviceTransfer.tick → unpack bounded native tar → write temporary project → scripts.package_collect_project.package → read-only SQLite SELECT \* FROM instances WHERE jrFormId=? → list materialization → only then len(rows)\>100 rejection

#### Reachability

Malicious/compromised explicitly paired device, or malicious copied Collect project selected by operator; ordinary hosted ZIP upload does not reach this parser

#### Severity

**Medium** — High process-availability impact requires a malicious explicitly paired device or operator-selected metadata.

Additional runtime or deployment evidence could raise or lower this severity.

Impact assessment:
- **Level:** high
- **Rationale:** Compact SQLite instances view with recursive/expansive query or computed large values can occupy native transfer indefinitely or exhaust shared API memory.

Likelihood assessment:
- **Level:** low
- **Rationale:** Explicit paired-device or operator selection prerequisite; not a public ZIP endpoint.

#### Remediation

Require expected ordinary-table schema, select needed columns, fetch at most101 rows, enforce connection value limits and deadline-aware SQLite progress handler.

Tests:
- Reject native views before querying; bound selected values and rows; retain normal packaging/device-transfer controls.

<a id="finding-2"></a>

### [2] Bounded XML inputs amplify into gigabytes of retained ancestor paths

| Field | Value |
| --- | --- |
| Severity | medium |
| Confidence | high |
| Confidence rationale | Independent source audit and parent verification traced real callers and controls. Bounded regression demonstrates missing rejection on old code, acceptance after fix; no multi-gigabyte exploit executed. |
| Category | Unbounded derived work |
| CWE | CWE-400 |
| Affected lines | lastcopy/inventory.py:22-47, lastcopy/inventory.py:50-57, lastcopy/inventory.py:141-154, lastcopy/xml_compare.py:18-30, lastcopy/models.py:146-153, lastcopy/api.py:269-272, deploy/aws/compose.api.yaml:14 |

#### Summary

Shared API process CPU/memory exhaustion; hosted API/web container has 1280m memory limit.

#### Root Cause

XML source-size/node limits omit expanded names and the aggregate ancestor paths subsequently retained.

#### Validation

Parent inspected every cited source range and actual registration/device-transfer callers. Old-code negative controls failed as expected; current targeted parser/native-transfer suite passed 20 tests. Full core suite passed 256 with one Windows skip.

Validation method: Offline source validation plus bounded local regression tests; no memory-exhaustion attack run

#### Dataflow

POST /ui/devices or /inputs/device → AccountStore.register → RunStore.register → inventory → walk → retained MediaReference.xml_path; comparator also retains full paths in xml_facts

#### Reachability

Verified public-beta account uploading a crafted device archive

#### Severity

**Medium** — High shared-service availability impact, but authenticated beta upload and existing admission bounds constrain likelihood.

Additional runtime or deployment evidence could raise or lower this severity.

Impact assessment:
- **Level:** high
- **Rationale:** Shared API process CPU/memory exhaustion; hosted API/web container has 1280m memory limit.

Likelihood assessment:
- **Level:** medium
- **Rationale:** Requires a verified account and malicious compact XML.

#### Remediation

Bound expanded names, individual paths and aggregate derived-path/fact bytes before constructing/retaining them in shared inventory and xml_facts; add regression.

Tests:
- Reject long expanded names/namespaces, deep derived paths and aggregate path work; retain ordered namespace/repeat identity.

## Reviewed Surfaces

| Surface | Risk Area | Outcome | Notes |
| --- | --- | --- | --- |
| Architecture and effective resources | not recorded | No issue found | Independent canonical architecture retained all16 consumer/deployment/resource rows and assumptions. Citation paths/lines checked; source map is not runtime proof. |
| XML archive import and deterministic comparison | not recorded | Reported | baseline-xml-path-amplification source validated and reported; pre-fix snapshot. Working shared parser now bounds namespaces/names/path work; negative control+normal ordered-repeat controls passed. |
| Paired native Collect metadata packaging | not recorded | Reported | baseline-native-sqlite-work-amplification source validated; requires malicious paired device/operator-selected DB, not arbitrary public ZIP. Ordinary-table/selected-column/value/deadline/101-row limits tested in working fix. |
| Hosted authentication, tenant isolation, browser proxy and safe rendering | not recorded | No issue found | Independent baseline/focused web reviewers fully traced owner/account/device authority, fixed upstream, Host/Origin, cookie and data paths. Their source-backed control rejections retained in supplemental review; no confirmed auth/SSRF/XSS bypass. |
| Recovery, provider actions, World Model and operator workflows | not recorded | No issue found | All lastcopy modules/scripts/deploy source fully reviewed. Review/hash/target/readback checks restrict synthetic recovery. Models are phase-enumerated and cannot change verifier outputs; graph bridge uses fixed memory namespaces. Vendored optional local filesystem namespace is unreachable from product callers, so traversal candidate rejected. |
| Tests, fixtures, contracts, generated declarations and dependency manifests | not recorded | No issue found | 391 full-file review union. Parent fully read web/AGENTS.md. Generated declarations structurally verified as type-only; OpenAPI parsed all66paths/157internal refs with no external refs; all156vendored lock entries checked for registry+integrity. Existing install-script entries noted, not executed. Synthetic fixtures/tests/docs source scanned; no confirmed embedded operational credential. |
| Encrypted backups, account exports and erasure-review workflow | not recorded | No issue found | Prefix-only no-delete S3 policy, CMS ciphertext validation/readback and scoped account exports are source-backed. Erasure endpoint records pending review only; proposed30day expiry inactive. No automatic/full-machine restore claim. |

## Open Questions And Follow Up

- Current source fixes must pass packaged-image and hosted regression checks before release; this scan reports defects in its immutable pre-fix snapshot.
- Full-machine/Enketo-key restoration, physical-phone backup, supported always-on Nightshift runtime and human penetration testing remain separate operational acceptance gaps.
