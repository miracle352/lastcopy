# Risk closure follow-up — 26 October 2026

This follows `SUBMISSION_FINISH.md`; it does not turn incomplete checks into
acceptance claims. Original sources, field project 1 and prior backups remain
unchanged. Repository visibility and submission remain the owner's decisions.

| Item | Actual result / next dependency |
| --- | --- |
| Performance | Windows fresh score **56**. Three AWS reference home scores **73, 82, 85** (median **82**); median LCP **2.561s**, CLS **0**, other categories **100**. Targets remain unmet. |
| Debian | Fresh stable package index, simulated upgrade of the exact deployed image: **zero available upgrades**. 72 retained advisories are still open, not silently dismissed. |
| Enketo recovery | Opt-in Redis/three-key capture and isolated restore verification are implemented. **16 Linux synthetic tests pass**, including the kernel output-size bound. Live capture/activation requires the pending explicit scope approval. |
| Physical phone | Still unavailable. Emulator evidence does not establish physical-phone transfer or backup while the PC is off. |
| Native zoom | User check requested in a normal browser at 200%; no result recorded yet. Earlier CSS scaling remains separately labelled. |
| Submission fields | Connected browser redirects to sign-in; requested current field labels from the owner's normal authenticated browser. No fields guessed or submission sent. |
| Always-on sponsor runtime | Current official Nightshift hotspot docs list Windows/Mac/DGX editions; no supported deployment on this Linux host was found. Hosted core, accounts, Central and deterministic recovery continue independently. |
| Independent human security review | Automated source review and remediation evidence exist; an actual external reviewer is still required. Scope below is ready to hand to that reviewer. |

## Performance evidence

`verification/risk-closure/lighthouse-home.json` is an actual production run,
using Lighthouse 13.5.0, its unchanged default simulated mobile profile (412×823,
DPR 1.75, CPU 4×, RTT 150ms) and Chrome 153. The benchmark index was 341.5.
Two completed temporary LastCopy Next test servers were closed after verifying
their command lines; no user apps, provider services or unrelated Node processes
were killed. Prior poor scores are retained. No faster desktop profile, simulated
success, measurement delay or field Core Web Vitals claim replaces this result.

The slow task was attributed to framework startup; the headline already paints
without opacity/clip animation. Motion/sample enhancements are already deferred.
A quiet reference measurement was subsequently completed, as recorded below;
representative physical-device testing is still absent. A site rewrite was not
substituted for this measurement. Working input and readable motion remain
higher priority than a cosmetic score change.

A bounded reference run was also started on the existing idle Singapore AWS
host: a disposable Node 24.22.1 / Debian Chromium container, Lighthouse 13.5.0,
1.5 CPU quota, 768 MiB memory and at least 1.5 GiB host headroom before every
measurement. No private mounts, keys, provider calls or application writes.
Initial browser startup failed because its profile could not use the read-only
home; profile/cache paths were moved to temporary storage and no failed startup
was assigned a score. Home scores were **73, 82, 85**, median **82**; LCP was
**3.112s, 2.561s, 2.187s**, median **2.561s**; TBT **801, 567, 529.5ms**.
CLS was **0**, with accessibility/best practices/SEO **100** throughout.
Benchmark indices were **1448.5, 1551.5, 1468.5**. All repetitions are retained
under `verification/risk-closure/`. The performance ≥90 and median LCP ≤2.5s
targets remain unmet; these results do not replace the Windows failures.
The `/demo` reference run scored **91 performance**, LCP **2.071s**, TBT **350ms**,
CLS **0**, and **100** in each other category. This single demo measurement
meets the stated lab goals; it is not a home-page pass or field-data guarantee.

To repeat locally on a quiet machine with Chromium installed:

```powershell
$env:CHROME_PATH='C:\path\to\chrome.exe'
npx --yes lighthouse@13.5.0 https://lastcopy-five.vercel.app/ --chrome-flags="--headless --no-sandbox --disable-dev-shm-usage" --only-categories=performance,accessibility,best-practices,seo --output=json --output-path=home-mobile.json
```

Use a fresh output filename for each of three runs; repeat for `/demo`. Retain
the default mobile throttling and record host/browser versions. No desktop
profile or warmed-browser result should replace a cold mobile measurement.

## Debian treatment

The actual image is
`sha256:2ee904ea5edc695e5cfea68e0cccdf405b877ddb71d651faf13c1e876b15abe6`.
The disposable stable-index simulation made no installed-package changes;
`verification/risk-closure/stable-updates.json` records its result.

The two SQLite 2026 advisories concern the Session Extension's changeset APIs;
LastCopy's Python SQL calls do not call those APIs or enable extension loading.
This is a reachability observation, not a claim that SQLite has no vulnerabilities.
Native SQLite import is a paired/operator CLI, read-only, with an ordinary-table
requirement, selected columns, row/value limits and a query deadline.
See [CVE-2026-50812](https://security-tracker.debian.org/tracker/CVE-2026-50812)
and [CVE-2026-50813](https://security-tracker.debian.org/tracker/CVE-2026-50813).

The zlib combine-function issue does not describe the Python ZIP decompression
API used here; archive entry/aggregate/XML limits remain necessary and tested.
See [CVE-2026-27171](https://security-tracker.debian.org/tracker/CVE-2026-27171).
For the glibc `fopen` issue, file modes in project code are fixed by code rather
than supplied by an uploaded archive. See
[CVE-2026-18374](https://security-tracker.debian.org/tracker/CVE-2026-18374).
Other native-library advisories retain unresolved reachability; Debian's
"unimportant" and "not yet assigned" labels are not invented severity scores.

Do not mix Debian unstable packages into this server or run destructive automatic
upgrades to obtain a zero count. The API remains an unprivileged, read-only-root
container with dropped capabilities, no-new-privileges, memory/PID limits and
scoped private mounts. These mitigate impact; they do not patch a library.

## Enketo and host recovery

[ODK's backup instructions](https://docs.getodk.org/central-backup/) require
Redis state and generated Enketo keys to preserve existing Web Form links.
The new explicit `--include-enketo` option adds only `main.rdb`, `enketo-secret`,
`enketo-less-secret` and `enketo-api-key` to the existing authenticated encrypted
archive. It excludes application/provider environment files. Missing, changing,
oversized or invalid source files abort the copy; generated key bytes are never
printed. The default daily job has not been broadened without approval.

The regression control deliberately disabled live/restored content comparison
in memory: the mismatch test failed with `DID NOT RAISE`. Unmodified code passed
the same control in the Linux suite. The first Windows sandbox run could not
load OpenSSL's DLLs; the unsandboxed synthetic crypto suite passed, and final
Linux tests avoid treating that environment failure as a product result.

`scripts/verify_enketo_restore.py --stage <private-extracted-backup>` validates
manifest hashes, loads a scratch RDB using the installed Redis image digest,
publishes no port, has Docker networking disabled and compares bounded content
fingerprints. It checks unchanged generated-key bytes; it does not start a new
public service or claim browser-level Web Form link acceptance. A disagreement
is a failed drill. Only its own uniquely named scratch container is removed.

A complete host rebuild still needs operator-controlled configuration recovery:
the Central/application environment, Cognito identifiers, DNS/static-IP routing,
TLS setup, operator access and provider reconfiguration. The recipient private
key remains on the owner's PC; maintain a second secure offline copy. Those keys
are deliberately not copied into Git or the new Enketo scope. Restoring a scratch
Redis/database is not proof of a full-machine disaster recovery.

Current official runtime guidance: [Nightshift hotspot](https://github.com/Meterless/Meterless/blob/main/docs/products/nightshift/hotspot.md).
Another paid host, unsupported Wine setup, publicly exposed desktop hotspot or
direct-NVIDIA relabelling was not used to claim an always-on sponsor path.

## Independent reviewer handoff

Review commit `57dd9a7` plus the narrowly scoped backup follow-up diff. Give a
reviewer repository read access when the owner chooses to publish or invite them;
do not share environment files, real account exports, provider keys or originals.
Use separate disposable beta accounts and synthetic inputs, with permission for
bounded manual testing only. No destructive production test or stress flood.

Priority checks:

1. Account A cannot list, download, export or recover account B's inputs/runs.
2. Expired/revoked sessions, cross-origin writes and imported redirect/target URLs
   fail closed; errors do not expose credentials or private filesystem paths.
3. ZIP/XML limits and native SQLite limits remain effective on malformed inputs.
4. Provider failures cannot create synthetic connected success or modify verdicts.
5. Recovery remains restricted to synthetic project 2, with exact preconditions,
   fresh readback and no conflict overwrite or duplicate retry.
6. Backup destinations/keys are private and prefix-scoped; corrupt readback, cap
   exhaustion and interrupted jobs cannot produce verified backup health.

The existing automated report retains its two pre-fix findings and separate fix
tests. No external human audit has been commissioned or claimed by this file.
