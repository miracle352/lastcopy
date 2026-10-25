# Automatic collection link — retained local acceptance

The later hosted pilot is now implemented and verified: see
[CLOUD_PILOT.md](CLOUD_PILOT.md). Its desktop link uses HTTPS; the original local
monitor was paused when the verified empty collection moved to cloud Central.
The remainder below records the earlier local milestone and its original limits.

25 October 2026. Actual local flow: paired Collect emulator → two matching native
observations → immutable archive and integrity seal → persistent comparison queue
→ fresh authenticated Central XML/history/media readback → saved result and UI.
This is bounded polling, not a promise of perfect or uninterrupted coverage.

## Start and use

From the repository root in PowerShell:

```powershell
.\scripts\start_realtime.ps1 -ShowEmulator
```

The explicit switch requests an interactive emulator window when starting it.
An already-running emulator keeps its existing window mode; an open form is never
terminated just to change the window. Omitting the switch starts it headlessly.
Docker Desktop and the documented Python/Node runtimes must be installed. The
launcher starts the existing Central services, restores the paired emulator's
local forward and starts missing local API/production UI processes. It does not
build/pull new images, replace a database, launch AWS resources or create a Windows
startup task. It does not supervise future crashes. Logs stay in ignored
`private/runtime-logs/`.

Open http://127.0.0.1:3000/app. The actual collection project is Central project 3,
**Water Point Condition Check**. Its native Collect project has the same readable
name, published form version `2026102502`, native **Wifi only** sending, and **Delete
after send disabled**. Both the device and server collection scopes are empty.
No synthetic inspection was inserted there. The pilot remains separate in project 4.

The device is observed every 15 seconds while automatic checking is enabled.
New exports trigger the existing comparator; scheduled server recaptures remain
60 seconds initially. The UI polls saved state every five seconds. Pause stops
future polling; an already-started bounded read can finish. The device-link panel
shows actual observation times and disconnected/changing/empty/error/budget states.
An empty device produces **waiting for records**, never a completed success report.

## Actual fixes

- Native access by `10.0.2.2` received Central HTTP 421 because its hostname did not
  match the local server. A paired `adb reverse tcp:8384 tcp:8384` supports the
  actual localhost address; no LAN/internet port was exposed.
- The old local test stack advertised `https://localhost:8444` even though it only
  published HTTP port 8384. `python -m scripts.setup_collect_loopback` applies an
  explicit loopback-only node-config override to the exact pinned existing stack.
  Its advertised form URL now downloads original bytes successfully. Database
  mounts were checked unchanged. **Never use that override on a public server.**
- Native UI replacement of the long private URL was unreliable. Only the dedicated
  AOSP emulator's stopped-app project preference was corrected and byte-verified;
  its old configuration remains privately retained. No form XML, instance database
  or media was edited. A partially exposed setup diagnostic led to revocation of
  the old scoped account session and replacement; the old session returns 403,
  the new single-form account verifies. Raw credentials/QR files are not public.
  QR import itself remains unverified; native manual setup plus the scoped debug
  configuration correction is the tested path.

## Producer boundaries

The producer only reads the explicitly configured serial, native project and form.
It does not discover devices, root/stop Collect, submit records or apply recovery.
The separate launcher restores root access only after verifying the dedicated
AOSP emulator; it refuses to root a physical phone. Physical-phone export access
has not been accepted and must not be inferred from this debug-emulator test.

Two bounded TAR observations must contain identical files. Linked/traversing,
duplicate/aliasing, Windows-special, oversized or changing exports are rejected.
Completion comes from actual native SQLite metadata. Private native captures are
retained separately; unrelated form rows are excluded from the supplied ZIP.
Only synthetic cohorts can filter a form version. Original field versions may not
be filtered away to manufacture a green result.

Intent and registered bytes are persisted before publishing the ZIP and seal.
A restart after ZIP publication resumes the pending seal using those exact bytes
without recapturing or making a duplicate export. Sources are not overwritten or
deleted. Sample mode never starts a device pull or external request.

Limits: 45-second device commands; 500 entries, 32 MiB expanded/native files,
10 MiB per file/registered ZIP; 40 new exports per configured transfer session;
256 MiB retained native TAR budget. Existing 120 comparison attempts/session,
100-file inbox, 1000-job/512 MiB ledger quotas and 300-second run limits remain.
These finite sessions need operator review/archive planning for long-running use;
this work does not claim unattended indefinite retention or 24/7 availability.

## Evidence and remaining cloud work

`verification/realtime/` records 201 passing core tests, a production build,
actual ADB-to-Central comparison (PRESERVED), unchanged-observation deduplication,
fresh production browser state at five widths, CSS 200% zoom, reduced motion,
keyboard pause/resume and reload persistence. No mocks supplied the live evidence.
The native collection download succeeded and its empty state was verified.
Native auto-send was configured but a new collection submission was not seeded
just to claim its end-to-end acceptance. Existing pilot delivery remains documented.

The user has authorized a $24/month planning budget and use of available AWS
credit. The signed-in console showed no EC2 instances in Singapore and the
Lightsail first-instance screen. Global View completed with an error, so its
account-wide totals are not treated as authoritative. The viewed credit's service
list includes Amazon Lightsail. Private credit balances/IDs are not packaged here.
No paid server, domain, public backend, Vercel update or AWS IAM change has been
created by this milestone. Public deployment still needs a persistent authenticated
backend, private durable storage, reachable HTTPS Central and a tested export
transport. Vercel's frontend alone does not supply those parts.

Official references: [Collect ADB](https://docs.getodk.org/collect-adb/),
[Central native endpoints](https://docs.getodk.org/central-api-openrosa-endpoints/),
[node-config overrides](https://github.com/node-config/node-config/wiki/Environment-Variables#node_config),
[Vercel runtime storage](https://vercel.com/docs/functions/runtimes),
[Lightsail prices](https://aws.amazon.com/lightsail/pricing/).
