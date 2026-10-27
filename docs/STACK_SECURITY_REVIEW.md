# Host and Central stack security review

For the later deployed dependency patch, current audit counts and major-version
compatibility failure, see [CENTRAL_DEPENDENCY_CHANGE_PLAN.md](CENTRAL_DEPENDENCY_CHANGE_PLAN.md).
The counts in this document describe the earlier assessment.

Completed deployment/retest pass: **27 October 2026, Africa/Lagos**. Machine
receipts retain their explicit UTC timestamps. Latest saved runtime evidence is
in `verification/stack-review/`; earlier evidence remains tied to its original
images and dates. No repository visibility, default branch or submission change.

## Changes actually deployed

The owner separately approved the host plan, Docker maintenance and container
rollout. The three prepared plans retain their original pre-approval wording:
`STACK_HOST_CHANGE_PLAN.md`, `STACK_DOCKER_CHANGE_PLAN.md` and
`STACK_CONTAINER_CHANGE_PLAN.md`. Their corresponding operations are now done.

| Component | Before | Now |
| --- | --- | --- |
| Ubuntu kernel | 7.0.0-1012-aws, reboot pending | **7.0.0-1014-aws**, new boot ID, no reboot pending |
| Host Brotli | 1.1.0-2build2 | **1.1.0-2ubuntu0.1**, USN-8956-1 fix |
| Docker Engine | Ubuntu 29.1.3 | Official **29.9.2**, following the separately approved 29.8.2 vendor migration and two-package patch |
| Central application | Same v2026.3.1 source, Node 24.20.0 | Same source, **Node 24.22.1**, stable OS updates, four reviewed parser lock entries |
| Enketo | Same 7.6.4 source, Node 22.12.0 | Same source, **Node 22.23.4**, stable OS updates |
| PostgreSQL | 14.24 | **14.24**, stable OS updates; no major migration |
| Redis | 8.10.1 | **8.10.1**, stable OS updates |
| pyxform | 4.5.0, Python 3.12.13 | **4.5.0**, Python **3.12.15**, OpenSSL **3.5.9**, stable Alpine 3.24 updates and one file-buffer flush |
| nginx/private mail | Original upstream images | Same applications, stable Debian package updates |

Caddy remains **2.11.7**, the current stable release checked during this pass.
The LastCopy API/UI image remains its tested Alpine digest from
`AUTONOMOUS_SERVICE.md`; no preservation, recovery or integration algorithm changed.

Central's production lock patch changes only proxy-addr **2.0.8**, body-parser
**1.20.9**, its nested qs **6.16.1**, and multer **2.5.0**. The build rejects an
unknown upstream lock hash and verifies the exact patched output hash. Dependency
sources/integrities are retained in `deploy/aws/central-dependencies.json`.
There was no `npm audit fix --force` or untested major Knex/database upgrade.

The final repository refresh found 29.9.2 after the initial approved plan had
pinned 29.8.2. The owner explicitly approved `STACK_DOCKER_PATCH_FOLLOWUP.md`.
This second patch updates only Engine/CLI, retains the 29.8.2 packages and keeps
containerd 2.4.2, Compose 5.6.1 and Buildx 0.38.1. Its separate receipt records
the exact final version and identity/configuration checks. No hidden automatic
version jump was used.
The final fresh apt simulation reports **zero available upgrades**. This is a
repository/package-state observation, not proof that no future or undisclosed
vulnerabilities exist.

## Access and isolation

- Key-only SSH remains on port 22; direct root login and X11 forwarding are off,
  authentication attempts are capped at three, and the existing Ubuntu key and
  TCP forwarding still work. A fresh SSH connection was checked before cancelling
  the five-minute rollback timer.
- UFW is enabled with inbound TCP 22/80/443 allowed. LastCopy API/UI and Central
  proxy stay bound to loopback. UFW is not treated as protection for arbitrary
  Docker-published ports: actual private bindings and external TCP refusals were
  checked separately.
- PostgreSQL and Redis now use separate internal Docker networks. Central has
  the PostgreSQL network; Enketo has the Redis network. nginx, Enketo and Central
  were tested against both permitted and forbidden service connections.
- Eight Central-stack services have no-new-privileges, a 256 PID cap and local
  logs capped at three 10 MB files. Existing application/database limits remain;
  nginx, Redis, mail and pyxform now also have explicit container memory limits.
- The upstream stack still requires its existing startup/root-capability model
  and writable roots. This pass does **not** claim that those eight services
  became non-root/read-only, nor that every service capability was eliminated.
  LastCopy's separate application container remains non-root/read-only.

The deployment replaced only the non-secret cloud override. The merged Compose
config is validated without exporting its environment values. The persistent
override disables inherited upstream image builds for patched services, so a
routine `compose up --build` cannot silently replace them with older runtimes.
Original configuration and rollback images remain private on AWS.

## What verification actually established

- Fresh encrypted database/Enketo backup completed before maintenance and again
  after rollout; recent S3 readback remains verified. No older backup was deleted.
- One host reboot changed its boot ID, activated the installed kernel and returned
  SSH in **30.5 seconds**. Docker, Caddy, the backup timer and all services restarted.
- Docker vendor maintenance retained **all nine original running containers**,
  their image identities and volume names. A root-only cold rollback copy of
  Docker/containerd state, including private configuration, remains on AWS only.
  It is deliberately outside the narrower exported S3 backup scope. Disk reserve
  remains above 5 GiB; no private plaintext was transferred to this PC.
- The later eight-container patch rollout took about **27 seconds** between its
  maintenance gate and completion timestamps. Before reopening access it matched
  project/form/submission/version/attachment/blob source-row hashes, three
  generated Enketo key hashes, original native ZIP SHA and volume identities.
  API environment bytes remained unchanged; no source record was written/deleted.
- Fresh XML, version and attachment readback from **synthetic project 2** compares
  as **PRESERVED**. Repeated completed Apply made **zero additional uploads**.
  Collection project 1 remained read-only. No physical-phone claim follows.
- Actual isolated PostgreSQL dump/restore and Redis RDB readback controls passed.
  Central's patched bcrypt/Node and Enketo's Express/Node loading passed.
- The malformed proxy-prefix regression fails on the original Central image and
  passes on the patched image. Actual JSON/multipart HTTP controls accepted valid
  data and rejected malformed/oversized inputs inside `--network none` containers.
- The small synthetic XLSX failed on the original pyxform HTTP wrapper because
  it reopened an unflushed write buffer. One `flush()` fixed this. Actual XLSForm
  conversion, Java validation and malformed-input rejection then passed on the
  candidate, and the live Central-to-pyxform service request also passed. No
  Central form was created by the conversion control.
- Fresh public browser acceptance passed real sample comparison, evidence drawer,
  recovery bundle, explicitly offline readback, account empty states and responsive
  layouts. Actual scoped Central reads, login/logout protection and direct NVIDIA
  Lightning inference passed after the kernel, Docker and container changes.
  Direct NVIDIA remains explicitly distinct from Nightshift/Zetaris.
- Final core suite: **274 passed, 3 skipped**, one existing Starlette deprecation
  warning. New scanner/config controls: **12 passed**. No UI changes in this pass;
  no new Lighthouse score, native zoom or physical-device claim is made.
- After the final 29.9.2 patch, public browser acceptance and fresh recovery
  readback/repeated Apply passed again. All nine containers were running with
  zero observed restart counts/OOM flags and their existing health checks passed.
  Focused working-tree/history credential scans found no matches in their stated
  scopes. They do not establish that every possible secret format is detected.

The initial guarded SSH check hit a shell `pipefail`/early-exit issue and restored
the original policy. The corrected check passed before activation was accepted.
An SSH caller timed out during container deployment, but the host-managed job
finished. Its receipt/journal was read instead of repeating the rollout.

## Advisory results and their limits

The official Debian database was downloaded once, hashed and compared locally
against each exact old/new image. Containers doing inventory had no network and
no private source mounts. **Only installed source packages count**. The scanner
was corrected to exclude residual `config-files` records; before/after controls
and a real nginx Perl false positive are retained. The authoritative comparison
is `debian-installed-comparison.json`; the provisional report is explicitly labelled.

| Image component | Before matches | After matches | After matches behind a listed fixed version |
| --- | ---: | ---: | ---: |
| nginx | 228 | 140 | 0 |
| Central | 138 | 124 | 0 |
| Enketo | 3,916 | 2,159 | 0 |
| Redis cache | 87 | 72 | 0 |
| Redis main | 87 | 72 | 0 |
| PostgreSQL | 118 | 118 | 0 |
| Private mail | 190 | 98 | 0 |

These are **database source-package matches**, not independently exploitable
vulnerabilities. In Enketo, **1,889** remaining matches are attributed to the
`linux` source installed as development headers, not a running container kernel.
Open/undetermined Debian findings remain; an unassigned urgency is not harmlessness.
Bundled Node/Python and application dependencies require their separate checks.
The updated pyxform Alpine main/community fix-feed check found **0 installed
versions behind listed fixes across 40 installed source-package identities**;
that feed does not enumerate all open vulnerabilities.

The Central **production npm report** moved from **32 package entries**
(1 critical, 15 high, 16 moderate) to **29** (0 critical, 13 high, 16 moderate).
Transitive entries can refer to the same underlying issue. The public lock and
manifest were verified against the pinned upstream GitHub commit before any
metadata went to npm. Only verified public dependency data was submitted;
credentials, fields and environment were not.

`remaining-central-dependencies.json` retains every remaining package entry,
advisory reference, fix information, exposure classification and next action.
The main review groups are:

- **Migration/maintenance graph:** Knex/liftoff/findup-sync/braces/micromatch.
  Inspected upstream code uses Knex with PostgreSQL for operator-owned migrations.
  This does not prove exploitability or universal unreachability; major-version
  compatibility and a caller-specific injection review are still required.
- **Mail:** retained Nodemailer recipient/parser/SMTP advisories need dedicated
  adversarial tests and an upstream-compatible mailer upgrade. This is a real
  application subsystem, not dismissed as a development-only dependency.
- **Process/proxy/config graph:** pm2, js-yaml, FTP/PAC/proxy dependencies. Keep
  configuration operator-owned; do not parse imported field evidence as process
  configuration. Per-advisory reachability remains incomplete.
- **HTTP, exports and object-store graph:** remaining Express/router/query/logger
  and exporter/MinIO transitive advisories need targeted patches and endpoint
  tests. PostgreSQL blob storage and bounds reduce particular exposure, but do
  not patch the libraries or establish that all related paths are unreachable.

Enketo's full application-library dependency graph has **not** received a separate
complete audit in this pass; its Node runtime, OS packages and live connectivity
were checked. Caddy/Docker vendor advisory review and current package state are
not a whole-host penetration test. PostgreSQL 14 support ends **12 November 2026**;
plan an upstream-supported Central database upgrade before then, with an isolated
restore/migration drill. No unreviewed PostgreSQL major migration was attempted.

The Redis isolated control also reported the host's `vm.overcommit_memory=0`
warning. Changing that setting was outside the approved host plan and was not
silently bundled into the runtime patches. Redis RDB/dump controls passed and no
live container OOM/restarts were observed, but memory-pressure/fork behavior has
not been load-tested. Review Redis memory/fork settings before larger workloads.

## Recreate, rollback and inspect

Existing-host recreate (the approved private override is already installed):

```sh
cd /srv/lastcopy/central
sudo docker compose -p lastcopy-cloud-odk -f docker-compose.yml -f lastcopy.cloud.yml up -d --no-build --pull never
```

Do not replace `lastcopy.cloud.yml` with the older bootstrap override or blindly
rebuild/pull all images. Patched build recipes and dependency patch data are in
`deploy/aws/Dockerfile.stack-*` and `central-dependencies.json`; exact deployed
digests are in the activation receipt. Stable apt repositories and build tags
can evolve: a new build needs a fresh scan and acceptance, not the old receipt.

Container rollback uses retained `lastcopy-stack:rollback-<service>-20261027`
images and `/srv/lastcopy/stack-review/original-cloud-override.yml`; it does not
restore database bytes automatically. Docker package rollback and cold data are
under the separate root-only `docker-cold-rollback-20261027` directory. Keep those
private: they may contain authentication/configuration state. Any rollback needs
an operator review, maintenance gate and fresh readback before reopening access.

Useful read-only checks: `docker ps`, `docker version`,
`systemctl status caddy docker lastcopy-backup.timer`, `ufw status verbose` and
`python -m pytest tests/test_stack_config.py tests/test_image_advisory_scope.py tests/test_alpine_advisories.py`.

## Scope still open

This closes the requested **separate assessment and deployed compatible fixes**,
not all risks. Remaining upstream dependency patches, full per-advisory caller
review, physical-phone acceptance, clean-host restoration and independent human
security review remain open. Performance and combined always-on Nightshift/Zetaris
limits in `AUTONOMOUS_SERVICE.md` are unchanged. Do not describe this as certified,
zero-vulnerability or universal production readiness.

References checked: [ODK release](https://github.com/getodk/central/releases/tag/v2026.3.1),
[Node security release](https://nodejs.org/en/blog/vulnerability/october-2026-security-releases),
[Docker advisory](https://github.com/moby/moby/security/advisories/GHSA-7cfq-22r6-qp73),
[Docker Ubuntu procedure](https://docs.docker.com/engine/install/ubuntu/),
[Docker 29 security release notes](https://docs.docker.com/engine/release-notes/29/),
[Ubuntu Brotli notice](https://ubuntu.com/security/notices/USN-8956-1),
[PostgreSQL security](https://www.postgresql.org/support/security/14/),
[PostgreSQL support policy](https://www.postgresql.org/support/versioning/),
[Redis fixes](https://redis.io/docs/latest/operate/oss_and_stack/stack-with-enterprise/release-notes/redisce/redisos-8.10-release-notes/),
[Caddy releases](https://github.com/caddyserver/caddy/releases).
