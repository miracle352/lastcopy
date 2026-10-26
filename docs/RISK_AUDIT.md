# Product polish and risk audit — 26 October 2026

Latest follow-up: [SUBMISSION_FINISH.md](SUBMISSION_FINISH.md) records the newer security fixes, automated off-host backup, narrated film and actual remaining checks. Earlier results below retain their original scope.

## Later release recheck

Final production mobile measurements supersede historical scores below: landing
96/91/88, median 91 and median LCP 2.47s; demo 98 and 2.13s; CLS 0 and other
categories 100 throughout. One landing run still missed the goals (88/2.504s).
These are lab runs, not field Core Web Vitals. Native browser zoom remains
unverified; 200% CSS layout zoom passed. Final image retains 116 unresolved
Debian database matches (71 unassigned, 44 unimportant, one low), using the
existing public advisory database locally; no package metadata was exported.

[RELEASE_READINESS.md](RELEASE_READINESS.md) supersedes the historical checklist
below where noted. Both fresh local sponsor cases are verified with actual
Zetaris queries, World Model reads and Nightshift/Nemotron inference. The stopped
driver was restarted and preflight now rejects an unavailable driver before
login. This is still a PC-dependent local integration, not a hosted Nightshift
claim. Account-owned read-connection setup now works on the configured HTTPS
Central origin, without inherited owner keys or recovery capability. Central
project/App User provisioning is still an operator action.

Password-reset delivery and sign-in were confirmed by the owner. The morning
scheduled backup succeeded and its explicitly approved encrypted off-host copy
matched the ciphertext hash. The health page exposes backup failure/staleness
and the disk reserve. Completed sealed investigation objects/queries/graph
journals are included in backups; unfinished runs, private configuration and
Enketo link keys remain outside this backup. No old copy was deleted.

Fresh actual Central readback and repeated Apply preserved the prior synthetic
recovery without another upload. Only the owner-approved summary of its counts,
timestamp and hashes is public. Automatic review rejected publication of the
full production receipts; they were kept on AWS.

The final full suite passed 243 tests with one Windows symlink skip; the later
focused guards and 16 JavaScript checks passed. npm full/production checks and
25 public PyPI version advisory checks reported zero known advisories. These
checks are not independent certification. Read the newest `release-final`
Lighthouse and Debian receipts for final measurements; earlier measurements
below are historical. Native browser zoom and physical-phone acceptance remain
explicitly unverified.


## What changed

The landing story follows scroll position: original → gap → readback. Sections
reveal once as they enter, with a readable static first frame and reduced-motion
fallback. Timed example cycling and its pause/play controls were removed. The
first example still runs the real offline comparator automatically. Changing a
case remains a user choice; no animation completes a real investigation.

The walkthrough now has labelled native radio choices instead of an unstyled
dropdown. Arrow keys work while requests change; stale requests are cancelled.
Sign-out belongs to the header on desktop and the navigation menu on smaller
screens. The sign-in form has one password field and an **Open records** action.
An operator leaves email blank and enters the existing passphrase there. That
uses the existing server-checked, persisted, throttled owner endpoint. Nothing
compares credentials in browser code and no authentication bypass was added.
Regular accounts still require verified Cognito identity and separate stores.

Heading order, paper-text contrast and the mobile link's accessible name were
corrected from actual Lighthouse failures. Only the public homepage and public
synthetic walkthrough can be indexed; account/private routes retain no-index.

## Backups and restoration actually checked

The operator approved daily encrypted backups **without any deletion**. The
installed `lastcopy-backup.timer` runs around 03:20–03:30 Africa/Lagos each day.
It passed an actual service invocation. A 5 GiB free-space gate refuses another
backup when capacity is low; this does not delete or limit existing evidence.
Storage therefore grows and needs disk, service-failure and billing/credit monitoring.

Each application SQLite database uses its online backup API and an integrity
check. Central uses a consistent custom-format PostgreSQL dump. AES-256-GCM CMS
encryption uses a public certificate on AWS. The recipient private key is at
`%USERPROFILE%\.lastcopy\backup\recipient.key`, outside the OneDrive project,
with restricted Windows ACLs. It was not uploaded to AWS. Environment files and
provider-key configuration files are excluded. Central database contents include
private account/authentication data, so decrypted dumps remain private too.

One actual encrypted copy was downloaded and decrypted privately on this PC.
All **10 SQLite databases**, **33 input hashes** and **40 output hashes** passed.
The downloaded Central dump restored into a new scratch database. Full rows of
`submissions`, `submission_defs` (including XML) and `blobs` had the same hashes
as the current live database, beyond matching totals. The scratch database was
removed; the live database was not overwritten. Restore tools refuse a dump
whose hash differs from the trusted backup manifest.

**Limits:** per-database snapshots are not an atomic whole-machine snapshot.
Enketo link keys/configuration, environment reconstruction, provider credentials
and any future external attachment store require separate recovery procedures.
Daily backups are on the same AWS host; one off-host copy is verified, while
unattended off-host replication is not configured. Losing the private recipient
key makes its backups unreadable: the owner must keep an additional secure key
copy. No field source or older backup was deleted.

These limits follow [ODK's backup guidance](https://docs.getodk.org/central-backup/),
which distinguishes database backups from Web Form links and external storage.

## Security checks and residual risk

- **233 Python tests passed**, one Windows symlink test skipped, one existing
  deprecation warning. The same three backup controls passed on Linux, including
  symlink rejection and ciphertext tamper rejection.
- **15 JavaScript gateway/key/scroll checks passed**; World Model conformance
  **8/8**. Production builds and actual browser flows were checked.
- Both full and production-only npm audits report zero vulnerabilities; `pip check` passed.
  The focused working-tree/history audit found no configured secret or explicit
  private-key pattern in public files/history. This is not an exhaustive audit.
- The final deployed image was compared to the complete public Debian advisory
  database locally, in a read-only, network-disabled scanner. No image metadata
  was exported to a scanner service. There were **116 unresolved entries**:
  71 unassigned urgency, 44 Debian-labelled unimportant and one low
  (`coreutils`, CVE-2016-2781). No fixed bookworm version was listed for these
  entries. Unassigned does not mean safe; these findings remain open.
- Container hardening removes Linux capabilities and privilege elevation,
  makes the root filesystem read-only and bounds processes. Only the intended
  data/inbox mounts and a bounded temporary filesystem remain writable. These
  mitigations do not erase advisories or replace independent security review.

## Actual production measurements

Lighthouse 13.5.0, headless Chrome 153 on this Windows desktop, **Next production
build**, mobile simulation: 412×823, DPR 1.75, 4× CPU slowdown, 150 ms RTT and
1,638.4 Kbps throughput. Other applications were not stopped, so host contention
is part of these observations. No development-server score is substituted.

| Route | Performance | Accessibility | Best practices | SEO | Lab LCP | CLS |
|---|---:|---:|---:|---:|---:|---:|
| Homepage, final three runs | 82 / 78 / 62 | 100 each | 100 each | 100 each | 2.68 / 2.86 / 3.08 s | 0 each |
| Walkthrough, one run | 81 | 100 | 100 | 100 | 3.32 s | 0 |

Homepage performance median **78**, median LCP **2.86 s**. The performance ≥90
and LCP ≤2.5 s goals remain unmet. The earlier run (65/94/100/60) was retained;
contrast, heading/name errors and public indexing were corrected. Headline
visibility no longer waits for an entrance animation, scroll code is deferred
until interaction, and geometry reads are batched before writes. Remaining
framework/hydration work and host variability need a controlled performance pass.
Lighthouse does not establish field INP or Core Web Vitals.

## What is still missing

1. **Unattended off-host backup, restore playbook and alerts.** Database recovery
   is verified; full host/Web Form-link recovery and automatic off-host transfer
   are not. Backup failure/disk alerts are not an email monitoring service yet.
2. **Supported hosted sponsor runtime.** Direct NVIDIA inference worked and its
   saved test is Replay. It is not Nightshift. No complete hosted
   Zetaris/World Model/Nightshift investigation was invented. The existing
   4 GiB host has no tested supported Nightshift deployment or Zetaris compute
   within the approved budget. The official [Nightshift CLI guide](https://meterless.ai/cli.html)
   documents its supported runtime editions; no generic deployment was assumed.
3. **A physical collection device and per-account project onboarding.** The
   emulator/relay needs this PC. Hosting the website does not make a powered-off
   emulator collect files. New public accounts can import their private exports
   and scoped snapshots; they do not inherit the owner's Central connection or
   automatically receive their own connected ODK project.
4. **Account/data deletion and a retention decision.** Current evidence remains
   until explicitly removed by the operator. No automatic deletion was added.
   Human password-reset delivery still needs an end-user check, separately from
   the verified real signup email.
5. **Owned domain, email capacity, support/legal details and independent review.**
   Cognito's free built-in email works within its shared quota; Resend needs an
   owned verified sending domain. No domain or paid service was purchased.
6. **The remaining performance goals and authenticated event template.** The
   browser/runtime checks and current scores are retained, not labelled perfect.

## Launch and operations

Use [LastCopy](https://lastcopy-five.vercel.app/) or the
[record server](https://app-18-141-113-136.sslip.io/app); neither requires this PC
for hosting or direct NVIDIA cloud. The no-account judge route is `/demo` and
explicitly uses synthetic files.

For the existing emulator link, open PowerShell:

```powershell
Set-Location "C:\Users\IYANUOLUWA\OneDrive\Documents\ChatGPT\My experiments\lastcopy"
./scripts/open_collect.ps1
./scripts/start_cloud_link.ps1
```

On the existing AWS server, inspect or request a manual backup:

```bash
sudo systemctl list-timers lastcopy-backup.timer
sudo systemctl start lastcopy-backup.service
sudo systemctl show lastcopy-backup.service -p Result -p ExecMainStatus
sudo journalctl -u lastcopy-backup.service -n 10 --no-pager
```

No repository visibility change, event submission, paid extra, IAM broadening or
field recovery upload was performed. Receipts are in
`verification/polish-risk/`; earlier sealed evidence was preserved.
