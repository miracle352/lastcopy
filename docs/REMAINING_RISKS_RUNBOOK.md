# Remaining risks: practical closure plan

27 October: the separate stack assessment and approved remediation are recorded
in [STACK_SECURITY_REVIEW.md](STACK_SECURITY_REVIEW.md). This supersedes the old
host/Docker/container patch state below, with remaining upstream dependency risks
retained explicitly. Physical-phone, clean-host and human acceptance stay open.

Latest implementation supersedes the old application-image and model-route state
below: [AUTONOMOUS_SERVICE.md](AUTONOMOUS_SERVICE.md). The hosted application now
uses Alpine; a live, advertised NVIDIA Lightning route passed. Physical-phone,
clean-host and independent human acceptance remain open. Performance measurements
for different hostnames are kept separate.

26 October 2026. Current delivered branch: `codex/product-redesign`.
Read this with `BACKUP_ACTIVATION.md`; it does not replace the retained receipts.
This plan distinguishes actual completion from prerequisites and future work.

## For tomorrow morning

The hosted core, accounts, Central, deterministic checks, permitted synthetic
recovery and encrypted daily backup already work without this PC. Actual S3
component restoration and native Chromium 200% zoom passed. The submission form
fields are now supplied by the owner; use `submission/SUBMIT_TOMORROW.md`.

The following work is **not** a prerequisite invented by the submission form.
It is product acceptance/security work. Do not delay a truthful bounded-beta
submission while claiming any unperformed test complete.

| Item | What closes it | Current dependency |
| --- | --- | --- |
| Physical-phone collection/export | Actual phone completes offline test, retains originals, sends with PC off, exports original form/XML/media/completion metadata and passes LastCopy | Borrowed Android phone and its owner's consent |
| Phone background backup with PC off | Supported phone-side export agent and authenticated transport, then Android permission/background/restart acceptance | New collector integration; current desktop relay is emulator-only |
| Clean-host rebuild | Fresh isolated machine restores configured services, identities, data and existing link behavior | Separate machine/VM, protected configuration-recovery decisions and controlled access |
| Human review | Named independent reviewer performs scoped tests and records findings; material findings fixed/retested | Actual web-security reviewer |
| Home performance | Same mobile-profile production measurements meet the goal after measured code reduction | Focused implementation/build/browser/measurement pass; current median 82 |
| Debian advisories | Relevant fixes available and tested, or documented exposure treatment and continued update ownership | Upstream stable fixes and advisory triage; no stable upgrade offered in last check |
| Always-on sponsor runtime | Supported Nightshift host plus Zetaris, private transport, actual inventory/inference/graph/query/revision acceptance with PC off | Suitable always-on supported hardware/runtime; no extra host is authorized |

## 1. Borrow one Android phone: test first, automate second

Do not root, unlock the bootloader, replace its Collect installation, or use the
emulator launcher's root/settings tricks on somebody's phone. Do not use a real
respondent's records. Do not put synthetic acceptance data into collection project
1, which remains separate from recovery testing.

1. Record phone model, Android version and installed Collect version. Use an
   isolated Collect project for the existing dedicated synthetic Central test
   scope, not somebody's existing campaign. An operator creates a narrowly scoped
   App User in Central and shares its QR privately; the public ODK website is not
   the LastCopy Central login. New LastCopy accounts do not inherit owner access.
2. In Collect's project settings, enable the chosen Wi-Fi/mobile **Auto send**
   behavior and disable **Delete after send**. Download the test form while online.
3. Turn the PC off. On the phone, disconnect networking, fill one synthetic form
   with a harmless photo and any required repeated answers, then finalize it.
   Check that it remains queued. Restore networking and confirm native delivery
   to the hosted Central. This tests Collect-to-Central, not independent backup.
4. Leave all originals on the phone. With Collect idle, enable USB debugging only
   for the authorized computer. Use ordinary ADB file access to copy the selected
   project, including **forms, instances and metadata**. Original XForms and
   completion metadata are required; just a photo or CSV is insufficient.
5. Check the actual serial and project directory, rather than using an emulator
   UUID. Never paste the App User URL/key into a public terminal log or chat.
   If Android refuses access, record that result; do not bypass it with rooting.
6. Package the stopped-app copied project using the existing operator CLI, with
   the actual form ID/version and an explicitly supplied device label. Import
   through LastCopy with the expected-device roster and exact destination. Keep
   the copied original and its hashes. Inspect XML/repeats and retrieved photo
   bytes, not only the submission count.
7. Repeat with no phone attached: absence must be shown as incomplete coverage,
   not a verified all-device result. Revoke USB authorization/disable debugging
   when finished. Retain only permitted synthetic evidence.

Inspect the current CLI before using it:

```powershell
Set-Location -LiteralPath 'C:\Users\IYANUOLUWA\OneDrive\Documents\ChatGPT\My experiments\lastcopy'
.\private\android\sdk\platform-tools\adb.exe devices -l
.\.venv\Scripts\python.exe -m scripts.package_collect_project --help
```

`scripts/start_cloud_link.ps1` and `scripts/prepare_cloud_device.py` are explicitly
for the paired AOSP emulator. They are not phone installers. A phone that sends
to Central by itself has not automatically created an independent LastCopy source
backup. For ongoing backup without a PC, a supported Android-side export/transfer
integration must be designed and tested; a web page cannot read Collect's private
storage just because the user signs in.

Sources: [Collect settings](https://docs.getodk.org/collect-settings/),
[ODK ADB guidance](https://docs.getodk.org/collect-adb/).

## 2. Clean-host disaster recovery

The completed component drill proved SQLite, Central PostgreSQL, Redis and key
bytes from encrypted S3 readback. It did not rebuild the operating system, routing,
TLS, account-provider configuration or provider runtime on a new machine.

Use a local VM on suitable spare hardware to avoid a new AWS bill, or explicitly
approve a temporary AWS test instance and maximum spend. Do not destroy or
repurpose the working host. Do not detach its static IP, change production DNS or
restore a dump over its live databases as a drill.

1. Inventory the exact source commit, application/Central image digests and
   pinned dependencies. The current source commit is visible with `git rev-parse
   HEAD`. Create the fresh machine with enough disk/RAM for the recorded stack.
2. Separately recover operator access and configuration from an owner-controlled
   secure store. The application/Central environment, Cognito identifiers,
   routing/TLS settings, provider setup and backup recipient key are intentionally
   not all inside the database backup. Decide their encrypted custody before
   calling the system disaster-recoverable. Do not send them in chat or Git.
3. Clone the finished source branch. The deployment helpers are setup aids, not a
   turnkey restore: `prepare-central.sh` initializes an empty Central and
   `prepare-https.sh` contains production hostnames. A qualified operator must
   adapt these for the isolated target. Never blindly run the production Caddy
   configuration on a staging machine.
4. Disable collection polling, recovery, SMTP/email delivery and provider calls
   on the restore target. Do not connect restored sessions/credentials to public
   accounts. Use loopback/private networking first and no production routing.
5. Fetch one exact ciphertext object from the approved S3 prefix; verify size,
   SHA-256 and authenticated decryption. Restore into new isolated SQLite paths,
   PostgreSQL database/volume, Redis volume and generated-key volume. Retain the
   trusted manifest and verify every restored file hash.
6. Verify source inputs, saved reports, account isolation and pending operation
   states. An uncertain recovery must re-read before retry; no completed write
   should run again. Use the existing recovery/fault controls only in the
   dedicated synthetic test scope.
7. Test the actual restored application and a retained synthetic Web Form link
   through controlled test routing. Existing hostname-dependent links and
   Cognito callbacks need deliberate mapping; a database fingerprint alone does
   not test them. Check original XML, each media slot and bytes independently.
8. Record recovery time, backup age, restored image/source identities, exact
   successes/failures and confirmation the live server was unchanged. Remove only
   explicitly identified test resources after acceptance; delete no backups.

Pass only after these checks run on a genuinely fresh machine. Full-machine
snapshots can complement this plan but introduce storage cost and do not replace
an actual restore test.

Source: [ODK Central backup requirements](https://docs.getodk.org/central-backup/).

## 3. Get a real person to review security

Ask a web-application security engineer or experienced security mentor for a
time-boxed review. A second AI agent, Lighthouse, npm audit or an automated
scanner is not that person. A short independent review is also not a comprehensive
penetration test; record its actual scope honestly.

Copyable request (send it yourself; no organizer/reviewer message is sent here):

> Can you independently review LastCopy's authentication, per-account isolation,
> untrusted ZIP/XML/native metadata boundaries and bounded recovery? Please use
> two disposable accounts and synthetic records only. Start with read-only source
> review and bounded manual checks. No stress flooding, credential extraction,
> production deletion, conflict overwrite or writes outside the dedicated
> synthetic recovery project. Record the reviewed commit, steps, severity and
> evidence for each issue; mark untested areas. I will fix and retest material
> findings before claiming the review complete.

Provide the repository/commit and the existing automated report under
`docs/verification/submission-polish/security/`, plus a separate private briefing
for any authorized test credentials. Use the six priority cases in
`RISK_CLOSURE_FOLLOWUP.md`. Invite a specific reviewer to the private repository,
or make it public when the owner chooses. Never share owner/NVIDIA/AWS keys.

Use [OWASP WSTG](https://owasp.org/www-project-web-security-testing-guide/) to
organize the review. Have the reviewer retest fixes and state exclusions. If a
reviewer is unavailable before submission, state "automated review completed;
independent human review pending" and keep sensitive field use out of the beta.

## 4. Home-page performance

The actual AWS reference home scores are 73, 82, 85 (median 82); median LCP 2.561s,
CLS 0. `/demo` scored 91 with LCP 2.071s. Windows scores remain lower and retained.
The largest reference cost is React/framework startup/hydration. The home route
also downloads a shared 114 KB decoded stylesheet (about 28 KB transferred),
with much of it unused above the fold. These are actionable leads, not proof of
a new fix. The hero paints without an opacity gate; motion/examples already
load after interaction/near visibility. Do not add a fake delay or hide controls.

Next implementation pass:

1. Split demonstrably route-specific CSS from the root cascade while retaining
   shared tokens and tested visual order. Avoid deleting selectors by a single
   screenshot: responsive, dialog and error states also need them.
2. Keep static navigation/footer/illustration markup on the server where possible;
   isolate mobile-menu and session behavior into small client components. Compare
   actual bundle/network output before assuming a rewrite reduces hydration.
3. Verify landing, login, app, evidence, recovery and native zoom at all five
   widths, reduced motion, keyboard focus and back/reload. Keep the requested
   scroll motion functional and text readable.
4. Build and measure production three times with the same mobile profile and a
   cold browser; retain all reports. Accept only a real median improvement, with
   LCP ≤2.5s, CLS ≤0.1 and working input. A preview can be checked before an
   authorized production deployment. Do not change CPU/network settings to pass.

The recorded repeatable Lighthouse command is in `RISK_CLOSURE_FOLLOWUP.md`.
Nothing in this runbook claims the 90 target is already met by the home page.

## 5. Debian advisories

The exact deployed image has 72 retained Debian-database matches; a fresh stable
package-index simulation offered zero upgrades. "Unimportant" and "not yet
assigned" are Debian labels, not proof of no risk. Do not mix unstable libraries
into the working image or run `npm audit fix --force` to clear a counter.

Maintain an exposure register by CVE/package, affected feature, reachable caller,
mitigation and upstream fixed version. The SQLite Session Extension API, zlib
combine functions and glibc attacker-controlled file modes are discussed with
vendor links in `RISK_CLOSURE_FOLLOWUP.md`; other matches remain unresolved.
The deployed app already uses a non-root read-only container, dropped capabilities,
no-new-privileges, memory/PID limits, validated inputs and scoped private mounts.
Those reduce impact but do not patch a library.

When stable fixes arrive: build a candidate from approved sources, run core,
offline, real synthetic recovery/retry and browser checks, scan its exact digest,
then deploy with a retained rollback image. Check the host, Central/Redis/Caddy
images and bundled Node/CPython/application dependencies separately; the Debian
package report is not a whole-system security certificate. Do not claim that all
72 are exploitable, or that all are harmless.

## 6. Remove the operator-PC dependency from sponsor inference

Nightshift's documented hotspot editions are Windows, Mac and DGX. The current
Windows product documents Windows 10/11 with NVIDIA/CUDA. That is not evidence
that a cheap generic Windows Server VM or the existing Linux host is supported.
No compatible always-on sponsor host is presently provisioned.

Supported route to validate:

1. Obtain vendor confirmation of a compatible always-on host/runtime. Use suitable
   existing spare hardware or separately approve hosting cost; do not buy another
   server on the assumption it works. Zetaris also needs its actual persistent
   runtime and source registration; moving only Nightshift does not move the
   combined path.
2. Install the official runtime on that host, configure its cloud provider
   privately if supported, and verify authenticated model inventory and inference.
   Route aliases are not serving-model names; retain actual response identity.
3. Connect LastCopy through authenticated private transport. Keep the hotspot
   protected rather than opening its raw port to the internet. Keep secrets on
   their host and validate the configured origin; use no arbitrary model URLs.
4. Run both connected controls through actual Zetaris evidence, World Model reads
   and Nightshift investigator/reviewer. Turn the operator PC off and repeat.
   Restart the supported runtime, test token rejection and provider outage, and
   confirm no Sample fallback or invented success.

Direct NVIDIA cloud is already a separately labelled option for hosted AI. It can
avoid the operator PC for that option, but it does not satisfy the claim
"Nemotron through Nightshift" and must not be relabelled. For tomorrow's entry,
show the existing genuine sponsor evidence as Replay and disclose local runtime
dependence instead of promising an untested always-on deployment.

Sources: [Nightshift hotspot](https://github.com/Meterless/Meterless/blob/main/docs/products/nightshift/hotspot.md),
[Windows product requirements](https://www.meterless.ai/windows.html).
