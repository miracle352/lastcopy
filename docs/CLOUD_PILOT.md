# Hosted water-point pilot

Verified 25 October 2026. Public introduction: https://lastcopy-five.vercel.app/ .
Its record-check links open the private HTTPS workspace at
https://app-18-141-113-136.sslip.io/app . Central is
https://central-18-141-113-136.sslip.io/ . These are temporary pilot hostnames;
the user has not supplied an owned domain. No domain was purchased.

## Use it on this PC

The repository root is the **folder**, not a terminal:
`C:\Users\IYANUOLUWA\OneDrive\Documents\ChatGPT\My experiments\lastcopy`.
Use PowerShell in that folder. The cloud website does not need local Node,
FastAPI, Docker Desktop or a second terminal to remain open.

1. Open the workspace. Use the owner passphrase in the ignored local
   `private/cloud/OWNER_ACCESS.txt`; keep it private. Eight-hour Secure,
   HttpOnly, SameSite=Strict sessions are checked against the durable server
   ledger. Returning from Vercel restores an existing valid sign-in through a
   same-origin check; an expired/revoked session requires the passphrase again.
2. Open the paired emulator with:

   ```powershell
   Set-Location 'C:\Users\IYANUOLUWA\OneDrive\Documents\ChatGPT\My experiments\lastcopy'
   .\scripts\open_collect.ps1
   ```

3. In **Water Point Condition Check**, choose **Fill Blank Form** and complete
   an inspection. Mark it finished. Wi-Fi auto-send is configured; deletion
   after send is disabled. The emulator needs this PC and internet to remain
   available. This is a real empty collection, not a seeded campaign.
4. Leave the desktop link running. It makes two stable native observations,
   publishes an immutable scoped export, and sends its sealed bytes over HTTPS.
   The cloud monitor reads Central again and runs the deterministic comparator.
   The workspace updates from real saved state. No fabricated progress or
   model calls are used. Check the explicit source roster and evidence.

For the link alone: `./scripts/start_cloud_link.ps1`. Its state is in ignored
`private/cloud/device-link-status.json`. Cloud **Pause automatic checks** prevents
new device capture/delivery on the next control poll. A capture already in flight
may finish. Closing the mirror does not stop the emulator/link. A PC restart needs
the launcher again; no Windows startup task or crash supervisor was installed.

The original local setup and its source archives remain available, but its monitor
was paused to avoid presenting a stale local-server target after cloud pairing.
Use [RUN_LOCALLY.md](RUN_LOCALLY.md) for historical local operation.

## Actual deployment and boundaries

- One Lightsail `lastcopy-core`, Ubuntu 24.04 LTS, Singapore, 4 GB/2 vCPU/80 GB,
  **$24/month base**. Static IPv4 `18.141.113.136` is attached. AWS says an attached
  Lightsail static IP has no extra charge; an unattached one is charged. No paid
  snapshots/load balancer/storage service, new Zetaris cluster or IAM change.
- Viewed credit applicability explicitly includes Lightsail. No zero-bill or
  account-wide hard-cap claim; taxes, overages and other resources are separate.
  The instance remains billable until deleted. Evidence must be backed up before
  any future deletion; no destructive cleanup was performed.
- Caddy 2.11.7 manages actual public certificates and renewals. Only 80/443 and
  key-authenticated SSH are public. API 8000, workspace 3000, Central 8384 and all
  databases remain internal/loopback. SSH host key was checked against the
  authenticated AWS browser terminal before private-key use. Password SSH is off.
- Public landing stays on Vercel. Private files, downloads, monitor and recovery
  live on AWS. Actual valid 5,246,287-byte synthetic ZIP got HTTP 413 through
  Vercel; identical bytes got HTTP 201 with matching hash through the workspace.
  Vercel private-data routes now direct users to the workspace, rather than
  claiming the platform accepts LastCopy's 10 MiB uploads.
- Owner access requires a server transport key **and** a valid owner session.
  A distinct device key can only deliver bounded exports and read its narrowly
  scoped run control. It cannot read reports or Apply recovery. No credential is
  placed in browser URLs/localStorage; only the owner session is an HttpOnly cookie.
- Collection project **1**, `Water Point Condition Check`, has zero field
  submissions at verification. Automation is **Viewer** there. Project **2**,
  `LastCopy cloud recovery (synthetic)`, is the only recovery target; automation
  has Manager there. The paired App User is assigned only the collection form.
- Private SQLite/evidence directories and Central Docker volumes survive process
  and host restart. This is one host, not high availability or an off-host backup.
  Paid snapshots are off. No disaster-restore acceptance or unattended 24/7 claim.

## Actual verification

All receipts below are in `docs/verification/cloud/`.

| Check | Actual result |
| --- | --- |
| Core Python suite | 214 passed, 63.17 s; one existing nonfailing Starlette deprecation |
| Hosted proxy/session/routing | 6 passed; unauthorized paths, forwarded hosts, CSRF, external redirects and outages covered |
| Pinned World Model conformance | 8/8 passed |
| Production builds | Local Next build, AWS image build and Vercel build passed |
| Native export → HTTPS → automatic cloud comparison | Actual version-2 native synthetic cohort; unchanged XML/form/media; PRESERVED; deduplicated; zero uploads to Central/model calls |
| Native synthetic recovery | Actual missing record in project 2; UI review/read-before-Apply; original identifiers; fresh XML/history/media readback PRESERVED; separate independent recheck passed |
| Lost acknowledgement + restart | Worker exit 73 after actual accepted upload; changed host boot ID; resume/repeat Apply performed zero further uploads; exactly one target record; fresh readback PRESERVED |
| Production browser | Actual Vercel/AWS, Chromium 153.0.8010.12; 360/390/768/1280/1440 widths, 200% CSS layout zoom, reduced motion, keyboard evidence/focus, reload, downloads, login/logout |
| Large upload | Same synthetic binary-media ZIP: Vercel 413; AWS workspace 201; matching original SHA-256 |
| Production npm dependencies | Audit reports zero known vulnerabilities; no automatic upgrades |

Tests were observed failing before fixes: missing access gate, scoped delivery,
public-example isolation, safe return routing, persisted control, and cross-project
delivery counters. A meaningful mutation removing delivery-receipt validation was
caught, then the original implementation was restored byte-for-byte. Browser runs
caught a broken isolated-example link and Strict-cookie return navigation; both
were corrected. Intermediate failed checks are retained rather than relabelled.
The last accepted browser run is identified in `verification/cloud/browser/`.

## Limits that remain

- Bounded polling, not push/instant synchronization: desktop polls every 30 s;
  server checks at 60 s when enabled. Changing files wait for stable observation.
  Budgets remain explicit: 40 exports, 120 comparisons per configured monitor
  session, 1,000 ledger runs, 512 MiB registered inputs, 10 MiB each upload,
  30 server submissions per capture and 300 s bounded investigation. Operator
  retention/capacity work is required beyond these pilot bounds. A restart does
  not reset quotas or manufacture coverage.
- This PC's dedicated AOSP emulator is verified. A physical-phone/remote-device
  collector, arbitrary Collect versions and phone-side background agent are not
  implemented. A new first inspection's native cloud auto-send has not been
  authored on the user's behalf; its configured behavior is distinct from the
  actual native-export/delivery and synthetic recovery acceptances above.
- Cloud Nightshift/Zetaris are **not configured**. Automatic copy checks explicitly
  make zero provider calls. Assisted investigation reports the missing actual
  integrations and never falls back to Sample. Local sponsor acceptance from
  earlier stages remains historical evidence; no cloud sponsor/Nemotron success
  is claimed. The pinned World Model is included and conformance-tested.
- Existing upstream container/OS advisory limitations from Stage 7 remain; a fresh
  exhaustive cloud-image CVE scan was not completed. npm audit is not an image
  audit. No Docker Scout metadata was exported. No fresh mobile Lighthouse score
  is claimed for this hosting change; earlier unmet performance goals remain in
  the handoff. Browser responsiveness checks are not field Core Web Vitals.
- Organizer authenticated submission template remains unverified. No submission,
  public repository visibility change or invented award eligibility.
- Server SSH still uses key-only access; source firewall and account-level
  operational hardening, off-host backups, owned-domain migration, credential
  rotation UI and monitoring need a separate operations pass before a sensitive
  real-world deployment. This is a bounded single-owner pilot.

Automatic review rejected a later environment-file transfer because it contained
credentials. The safer accepted route uploaded only a source archive scanned for
private files/known credentials and changed three non-secret settings in place on
AWS. No rejected transfer was bypassed. Environment files remain private.

## Primary deployment references

- [Lightsail pricing](https://aws.amazon.com/lightsail/pricing/)
- [Attached static IP costs](https://docs.aws.amazon.com/lightsail/latest/userguide/understanding-static-ip-addresses-in-amazon-lightsail.html)
- [Vercel payload limits](https://vercel.com/docs/functions/limitations)
- [Caddy automatic HTTPS](https://caddyserver.com/docs/automatic-https)
- [ODK installation](https://docs.getodk.org/central-install-digital-ocean/)
- [ODK scoped assignments](https://docs.getodk.org/central-api-project-management/)
- [Official scrcpy runtime](https://github.com/Genymobile/scrcpy/releases/tag/v5.0.1)

scrcpy is an ignored local Apache-2.0 runtime, not website media. Its official
Windows archive SHA-256 was verified; software rendering is used on this PC and
clipboard auto-sync is disabled. No AI imagery or community audio was used.
