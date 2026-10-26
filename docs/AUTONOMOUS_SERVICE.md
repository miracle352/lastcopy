# Hosted runtime and fresh acceptance

26 October 2026. This is an implementation/retest pass, not a claim that every
release limit is closed. Evidence is in `verification/autonomous-pass/`.

## What changed

The AWS LastCopy application image moved from Debian to Alpine 3.23, retaining
CPython **3.13.17** and Node **24.22.1**. A multi-stage build keeps the global npm
installation out of the final runtime. OpenSSL is included for the existing
backup tooling. The exact active image is
`sha256:de28d66aec981542f5e8a8eab332141c1d906729cf4364fe7656b9185be9ba06`
(287,328,147 bytes). The previous tested Debian image remains available as
`lastcopy-api:rollback-autonomous-20261026`.

No application environment bytes or private source volumes were changed/deleted.
The application remains non-root, with a read-only root, dropped capabilities,
no-new-privileges and the existing resource limits. Startup recreates the real
API/UI services and durable monitor workers; the operator PC does not host them.

The landing/header/footer use native anchors where client navigation was
unnecessary. Auth, illustration and demo-only CSS now load through their owning
components/routes. A server Suspense boundary separates the below-hero journey.
The extraction asserted declaration preservation; browser checks exercised the
resulting cascade. Comparator, integration and recovery semantics are unchanged.

## Advisory scope

`scripts/audit_alpine_image.py` downloads the complete official Alpine 3.23 main
and community security-fix feeds. Installed apk source identities are compared
using apk's version comparator in network-disabled containers. Package metadata
is not sent to a scanning service. Database hashes and the exact image digest
are retained in `alpine-advisories.json`. No installed version was older than a
listed security fix.

This removes Debian packages from the LastCopy application container. It does
**not** patch or certify Central, Redis, Caddy, the Ubuntu host, bundled Node or
CPython. Alpine's fix feed is not a register of every unresolved issue, so its
zero result is not directly comparable to the prior 72 Debian open-status
matches. The old Debian result remains retained against its original digest.
No forced dependency upgrade, unstable Debian mixture or production-data
migration was used. The alternative distroless Python image was rejected because
its Python 3.13.5 would downgrade the pinned runtime.

Public references: [Alpine main feed](https://secdb.alpinelinux.org/v3.23/main.json),
[community feed](https://secdb.alpinelinux.org/v3.23/community.json),
[official Node Alpine image notes](https://github.com/nodejs/docker-node#nodealpine).

## Actual checks

- Windows: **265 passed, 3 skipped**, existing Starlette deprecation warning.
- Alpine image: **268 passed**, existing Starlette warning. Tests use a disposable
  writable filesystem; no production evidence mounts. The first attempts failed
  on absent OpenSSL, read-only fixture generation and deliberately small tmpfs
  free space. Those failures are retained. The production guard was not weakened.
- World Model: **10/10** tests on Windows and Linux; **8/8** conformance checks on
  both. Linux test-runner cache needs a disposable writable test environment;
  this is distinct from application runtime permissions.
- JavaScript proxy/policy/story/key-entry controls: **16/16** passed.
- Actual offline API: five fixture cases, networking disabled, non-root/read-only
  runtime, **51 original source hashes unchanged**, zero provider calls. Reports,
  evidence downloads, bundle and explicitly offline readback passed.
- Production build and TypeScript passed. Local and AWS browser walkthroughs
  passed actual comparison, evidence, bundle, readback and account empty states.
- Home/demo/login/signup reviewed at **360, 390, 768, 1000, 1280 and 1440 px**.
  Scroll phases, keyboard controls, reduced motion and static no-JS first frame
  passed. Native Chromium **200% zoom** passed the evidence drawer, Escape focus
  restoration and reachable recovery bundle without page overflow.
- Fresh hosted HTTPS requests verified real scoped Central reads, private-session
  protection, logout revocation and successful recent local/S3 backup status.
- The existing synthetic recovery was rechecked with fresh XML/version/media
  capture on the new runtime: **PRESERVED**. Repeated completed Apply made no
  upload. Native source SHA remained
  `25dadf67ef5c4f58e9d13ce85d5ed0e930abff1d2b5e311815694e5aa69382f3`.
- npm audit: **0 reported vulnerabilities** across all installed dependency
  categories. `pip check` passed. These do not replace an independent review.

The deployment guard initially requested protected endpoints without their
server transport credential, received 401 and rolled back. It was corrected to
exercise the existing transport boundary inside the container; final activation
passed. No authentication rule was disabled.

## AI that runs on AWS

The previous configured Bolt staging route returned an actual 404 despite its
presence in inventory. That failed attempt is retained, without a fallback.
The operator selected **nvidia/nemotron-3.5-lightning-30b-a3b from fresh inventory**
and the actual AWS investigator/reviewer test passed. The provider reported the
same serving model for both calls, 132 and 545 total tokens, and approximately
459/489 ms serving request durations. The action changed from `fetch_raw_xml` to
`export_guidance` after verifier evidence. The report hash and request/response
hashes are in `nvidia-live-retest.json`; credentials remain on AWS.

This is **live direct NVIDIA inference over a synthetic verifier case**. It does
not claim that Zetaris/Nightshift were used, or that this smoke test is a full
connected investigation. The PC-dependent combined sponsor runtime remains
separate. Current official [Nightshift hotspot documentation](https://github.com/Meterless/Meterless/blob/main/docs/products/nightshift/hotspot.md)
lists Windows, Mac and DGX editions; a supported always-on replacement has not
been verified within the existing $24 host budget. No guessed Linux install,
relabelling or unapproved GPU/second-server purchase was made.

## Production performance

Same Lighthouse 13.5 default simulated-mobile settings: 412x823, DPR 1.75,
4x CPU slowdown, RTT 150 ms, throughput 1,638.4 Kbps. Actual profile fields and
browser benchmark indices are retained. Each run uses a fresh browser on the
existing AWS host, an isolated 1.5 CPU/768 MiB browser container, and requires
1.5 GiB host memory headroom. Browser tooling was removed after measurement.

On the updated **AWS application hostname**, home scores were **88, 84, 79**:
median **84**, median LCP **2,479.932 ms**, CLS **0**. Accessibility,
best-practices and SEO were **100**. `/demo` scored **94**, LCP **2,362 ms**,
CLS **0**, other categories **100**. The home target of 90 remains unmet.
These are not a direct improvement claim against the older Vercel-hostname
median 82. A separate local Windows measurement was 52, LCP 3,935.74 ms,
CLS 0; retained rather than discarded. No field INP/CWV claim follows.

After the owner renewed Vercel team access, the working-tree deployment
`dpl_6MTmMWPdnQtz5kdHHcPjuDBQ9Z8E` reached READY and was aliased to
`https://lastcopy-five.vercel.app`. Both the full public walkthrough and scroll
browser checks passed again on that actual production URL. This was a CLI upload
of the tested working tree; its automatic Git metadata still names the previous
HEAD, rather than certifying the dirty working tree as that commit.

Three new **Vercel home** measurements were **93, 86, 84**: median **86**
(the earlier recorded median was 82), median LCP **2,533.3935 ms**, CLS **0**.
Other categories were **100**. The new Vercel `/demo` measurement was **84**,
LCP **2,506.344 ms**, CLS **0**, other categories **100**. Its earlier single
measurement was 91; this pass does not hide that regression/variation. Home and
demo remain below the 90 goal on this hostname, and median home LCP narrowly
misses 2.5 seconds. All raw runs, including the lower scores, are retained.
Actual interaction and recovery flows passed; the score goals are not a claim
of universal performance or field Web Vitals.

## Still required

1. **Physical Android phone:** the owner chose to do this later. Emulator/desktop
   checks are not physical-phone background/export acceptance.
2. **Clean-host restoration:** encrypted S3 component restoration passed earlier;
   it is not a from-zero independent machine rebuild. Provider/bootstrap config
   remains deliberately outside exported backups. A disposable isolated host,
   approved secret re-provisioning and a full restored browser/collection test
   are still required. No additional paid host was created.
3. **Independent human security review:** no reviewer is available. Automated
   testing and AI review are complete only within their recorded scopes; neither
   is a substitute for a human reviewer.
4. **Combined sponsor migration** and **home performance 90** remain open as
   described above. Keep sponsor captures labelled Replay when their PC runtime
   is off. Core verification and the direct-cloud AI option run on AWS.

Do not claim "everything fixed", universal automatic phone backup, full-machine
disaster recovery or a completed human audit. Keep real sources and existing
backups. Repository visibility, default branch and submission are unchanged.
