# Product redesign and release-limit follow-up

Requested after the Stage 7 audit. The deterministic comparator, finding
semantics, integration dispatch and recovery engine remain authoritative.
This is a presentation redesign plus targeted local-image remediation.

## Direction and research

Viewed Stripr's real landing page and `/app` in the connected Chromium browser
at desktop size, including its hierarchy, panels and navigation. The public web
reader could not retrieve it; browser inspection succeeded. The reference was
used for visual discipline, not its assets, brand, copy or financial subject.

Read the primary project pages for
[Codrops ConnectedGrid](https://github.com/codrops/ConnectedGrid),
[OnScrollColumnsRows](https://github.com/codrops/OnScrollColumnsRows),
[Motion](https://github.com/motiondivision/motion) and
[Anime](https://github.com/juliangarnier/anime). These informed the research;
their implementations, images and dependencies were not copied or installed.
This was a targeted survey, not a claim to inspect every animation repository.

The original LastCopy concept is **the record journey**: a field notebook,
retained originals and a comparison receipt. Warm paper makes the original
concrete; ink-green surfaces hold the investigation; amber keeps an unresolved
attachment visible. The interactive illustration is explicitly labelled and
cannot produce a real verdict or upload.

## Changed presentation

- Simplified, route-aware navigation with a keyboard-operable mobile menu and
  a compact footer. Technical architecture is secondary.
- Larger editorial hero, layered HTML/CSS notebook and receipt, user-selected
  Original/Comparison/Readback states and a coordinated paper entrance.
- Native-scroll chapter reveals and story progress; desktop scan/document
  travel pauses offscreen and when the document is hidden. No scroll hijacking.
- Sample/export entry panels, explicit scope and validation, larger upload
  targets, saved checks, API-derived result counts and structured finding actions.
- Matching evidence and recovery surfaces, readable mobile drawers, report
  downloads and preserved exact-target review gates.
- Reduced motion removes loops, parallax and choreography while retaining
  controls and understandable states. No new animation dependency, external
  assets or imagery. Existing self-hosted OFL fonts remain in use.

## Verification and known failures

Final measured results are in `verification/redesign/` and the current HANDOFF.
The first visual pass found decorative overflow; its ring layer was contained.
A result coverage grid initially separated term/value pairs; each pair is now
grouped. A CSS download arrow entered the accessible name; it was replaced with
an `aria-hidden` SVG. The first mobile Lighthouse pass found one paper-heading
contrast failure; its text was darkened before the final checks. The 200%
layout-zoom pass exposed a desktop hero reflow failure; container-based
responsive composition fixed it. Final browser checks cover all five widths,
zoom, reduced motion, a static first frame and real sample/review/download flows.

The initial restricted regression run stalled at local fixture/bridge work and
was interrupted. The rerun with local subprocess access passed **169 tests in
52.77 seconds**, with the existing nonfailing Starlette deprecation warning.
This does not turn prior intermittent live-provider failures into successes.

## Second-annotation blockers

Docker Scout previously failed automatic approval because its operation could
export private image/package metadata. It remains unused. The safer local
matcher downloads a public advisory database, then runs matching with scanner
networking disabled; no image inventory is sent to the advisory service.
The same retained database permits an honest before/after comparison.

The first targeted rebuild upgraded installed binaries from 13 selected Debian
source families, without a broad automatic distribution upgrade. It removed all
85 `resolved` candidates from the original 201-entry scan. Its 116 remaining
entries were 115 `open` and one `undetermined`; they are not dismissed as safe.
The final image also pins the verified same-series official security releases
[Node 24.22.1](https://nodejs.org/en/blog/release/v24.22.1) and
[Python 3.13.17](https://www.python.org/downloads/release/python-31317/).
Host runtimes were not replaced. Final scan/runtime receipts identify the immutable image that actually ran.
The final container passed sample comparison, bundled font requests, report and
bundle hash checks across a real restart with external networking disabled and
non-root UID 10001. The security-runtime image passed all 169 core tests in
33.96 seconds; a subsequent CSS-only zoom fix was checked in the browser and
incorporated into the final runtime image. Debian matching does not cover every application or bundled runtime
vulnerability and is not a security certification.

The supplied submission URL was opened with URL-aware browser tooling. It
redirected to sign-in. The user attempted Google sign-in and Google rejected the
automated browser as insecure. We did not bypass that restriction. The current
authenticated submission template remains unverified until the user supplies a
redacted form screenshot/field list from a normal browser. No guessed metadata
or submission is produced.

## Running and release boundaries

Use [the two-PowerShell-tab guide](RUN_LOCALLY.md). The repository is a folder,
not a terminal. Nothing in this follow-up publishes, submits, changes visibility
or triggers Vercel deployment. Prior live receipts remain historical evidence;
fresh presentation tests are explicitly labelled Sample.


## Final measured presentation checks

The production browser run passed six grouped acceptance checks and retained
34 sealed screenshots at 360, 390, 768, 1280 and 1440px, plus 200% CSS layout
zoom and reduced motion. It used actual local fixture contents and reports,
with external browser requests blocked and no mocked successful responses.
A separate keyboard-only sample/evidence/review/bundle/readback/report flow
passed, including Escape focus return, refresh and back navigation.
Screenshots were visually reviewed across all five widths. Browser checks are
Chromium-specific; CSS layout zoom is not a claim of native browser-zoom testing.

Pinned mobile Lighthouse 13.5.0, production build, simulated Moto G Power,
412×823/DPR 1.75, 150ms RTT, 1638.4kbps throughput and 4× CPU slowdown on the
shared Windows host:

| Route/run | Performance | Accessibility | Best practices | SEO | LCP | CLS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Landing, build-contended | 56 | 100 | 100 | 60 | 3.885s | 0 |
| Landing, image export active | 94 | 100 | 100 | 60 | 2.541s | 0 |
| Landing, no build/workflow run active | 97 | 100 | 100 | 60 | 2.442s | 0 |
| Actual workspace | 88 | 100 | 100 | 60 | 2.873s | 0 |

All three final landing measurements are retained: median performance **94**,
median LCP **2.541s**. The 2.5s median LCP target is still unmet; one better run
is not a guarantee. Workspace performance remains below 90. SEO 60 reflects
intentional `noindex` for the private preview. Scores are lab observations, not
field INP/Core Web Vitals or an isolated hardware benchmark. Raw reports remain
private; sanitized configuration/results are in `performance.json`.
