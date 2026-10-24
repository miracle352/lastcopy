# Stage 7 audit and readiness — 2026-10-24

The deterministic verifier remains the authority. This stage audits the actual
product and prepares an owner-reviewable local release; it does not publish,
deploy, change visibility or submit an entry. No Git push was performed because
the existing linked branch can trigger a Vercel deployment.

## Material fixes

- API Host validation rejects DNS rebinding; browser Origin validation covers
  all routes rather than only Apply. The Next evidence proxy/inventory route
  rejects non-local Host headers. New negative tests failed before the fix
  (untrusted Host returned 200), then passed. Existing tests now use the actual
  loopback base URL. This is still a single-user local boundary, not hosted auth.
- Evidence drawer code loads on demand. Noncritical motion loads during idle;
  reduced motion skips it. Fonts preload locally, Fraunces retains only the
  actually used 450 weight, combined WOFF2 shrinks from 63,244 to 43,300 bytes.
  Noncritical landing navigation does not prefetch unused routes. The largest
  heading is visible at first paint while supporting layers animate.
- `/app` loading fallback reserves a viewport so the footer cannot jump when
  the actual form appears. Measured CLS fell from 0.520 to 0.002. Pending import
  mode says “Reading configured mode” instead of briefly claiming Sample.
- README is rewritten for the real application, production commands, CLI/API,
  inputs, evidence and recovery; local Docker packaging is implemented/tested.
  Browser/seed tools accept separate receipt directories so earlier attempts
  stay intact. A new seed refuses nonempty output directories.
- Git attributes preserve captured receipt bytes. A staged-byte seal check
  caught Windows newline normalization changing 15 JSON artifacts; disabling
  text normalization for the new hashed receipts fixed the staged hashes.
  `SHA256.json` seals all retained Stage 7 evidence files.

## Acceptance evidence

| Area | Actual result | Receipt |
| --- | --- | --- |
| Core | 169 tests passed in 112.98s; existing Starlette/httpx deprecation only | Full suite rerun after security fix |
| World Model | 10 reference tests, 8/8 conformance checks passed | Existing pinned upstream suite; real reference bridge also used live |
| Contracts/types/build | Regenerated OpenAPI/TypeScript produced no schema drift; typecheck and production Next build pass | Generated files unchanged; no API/domain schema divergence |
| Private key helper | 6 Node tests pass, including doubled paste guard | `tests/nightshift-key-entry.test.mjs` |
| Offline | All five UI samples, original evidence, JSON/text/JSONL reports and eligible bundles pass with providers stopped | `verification/stage7/offline-browser.json` |
| Offline environment | All existing sponsor/test containers exited; Nightshift/Zetaris/Central ports unreachable; local API works | `offline-environment.json` |
| CLI | Seven complete Stage 2/3 fixture packs match hand-authored expectations; source hashes unchanged, zero provider calls | `cli.json` |
| Fresh connected export | Four real Zetaris queries, 3 Nightshift calls, 9 steps, 2 critiques, 125.148s; graph action review → fetch_raw → export_guidance | `connected-export/independent.json` and actual query/model/graph files |
| Fresh connected conflict | Same bounded integrations, 50.052s; conflict retained, manual_review, no recovery | `connected-conflict/independent.json` |
| Serving model | Responses reported `nvidia/nemotron-3.5-lightning-30b-a3b` through Nightshift; response-reported usage only | Actual model events in the two traces; no guessed alias |
| Outage | Stopped-provider connected attempt fails with zero model calls; no sample fallback | `provider-outage-investigation.json` |
| Real Central recovery | Missing submission, missing media and lost-ack process restart all become PRESERVED after fresh same-verifier readback; one intent, repeated Apply no write | `../verification/stage4-20261024-stage7-{create,media,lost-ack}/receipt.json`, `recovery-independent.json` |
| Real conflict | Existing conflicting Central XML rejects an automatic plan and remains unchanged; zero recovery writes | `real-conflict.json` |
| Browser | First sample, actual evidence, review/bundle/offline readback, controls, validation, queued cancellation, reload/back; no successful-response mocks | `browser-initial-attempt.json`, keyboard and responsive receipts |
| Keyboard only | Tab/Enter/Space/Escape through actual sample, modal trap/return, review, bundle, readback, report and back | `keyboard.json` |
| Replay | Actual synthetic capture upload, explicit capture identity, missing-device coverage, refresh/evidence; no recovery/model | `replay-browser.json` |
| Responsive | 360, 390, 768, 1280, 1440px; landing/import/run/drawer, reduced motion, no-JS, 200% CSS zoom | `responsive-complete/browser.json` plus PNG baselines |
| Docker | Actual build, non-root UID 10001, Python 3.13.7/Node 24.12.0; real sample report/bundle survive restart, `.env` absent | `docker.json` |

The offline fence is process-scoped: Python rejects non-loopback DNS/TCP, Node
rejects non-loopback TCP/fetch and the browser blocks external origins. This
does not disable the host network or change firewall settings. Providers were
then restored, retaining all volumes/configuration. Installation, image builds
and advisory downloads occurred separately and required internet.

Correct controls include matching original history plus separate intentional
current edit, shared filename references, separately named equal-byte files,
positive raw XML with incomplete export, missing device/XForm/completion/scope,
unavailable history/attachment, hostile ZIP/XML and authenticated failure. Tests
prohibit both false recovery and false assurance. Fixture outcomes are authored
independently; the held-out variant changes identities, paths and repeat count.

### Live UI limitations retained honestly

The full production browser checks performed real import/capture, explicit
review, precondition reread, Apply, deliberately lost browser acknowledgement,
fresh XML/media verification and reload without another upload. Both later
connected investigations failed separately: the first during publication after
provider restart; the next with Nightshift reviewer HTTP 504 after real queries.
The browser harness also saw a GET connection reset; only read GET retries were
added, never automatic Apply or inference retries. Failed attempts are retained.
`browser-recovery.json` and `browser-02-recovery.json` distinguish independently
verified recovery from failed sponsor diagnosis. Earlier fresh CLI connected
checks above are real Stage 7 successes, not relabelled browser successes.

The restored Zetaris constant SQL query and a separate publication diagnostic
passed after readiness checks. No completed upload was retried. A new read-only
post-recovery investigation **completed** with four actual queries, three model
calls and two critique rounds. The production browser then opened its saved
Connected result, downloaded actual investigation/query/graph/redacted receipts,
and reloaded with zero POST requests. See `connected-browser.json`,
`post-recovery-summary.json` and `post-recovery-connected/`. This is a distinct
fresh API-created check of the recovered record; it never replaces or rewrites
the earlier failed runs. The required rejected missing-answer hypothesis remains
demonstrated by the separate fresh connected export case. Provider availability
remains an external operational dependency, not a preservation failure.

## Production mobile measurement

Lighthouse **13.5.0**, Headless Chromium **153**, Windows/Intel Core i7-10810U
(12 logical processors). Simulated Moto G Power: **412×823**, DPR **1.75**,
150ms RTT, 1638.4kb/s throughput, 4× simulated CPU slowdown; fresh navigation/
storage reset, production `next build`/`next start`, local loopback. Profile and
timestamps are retained verbatim in `verification/stage7/performance.json`.
The baseline ran amid other audit work; later production repetitions were
serialized, with providers stopped. This is not a controlled cross-device
benchmark or a claim that every score change is caused only by the code edits.

| Route/run | Performance | Accessibility | Best practices | SEO | LCP | CLS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Landing baseline | 31 | 100 | 100 | 60 | 7.2s | .002 |
| Landing final 1 | 93 | 100 | 100 | 60 | 2.583s | 0 |
| Landing final 2 | 81 | 100 | 100 | 60 | 2.691s | 0 |
| Landing final 3 | 86 | 100 | 100 | 60 | 2.557s | 0 |
| Technical | 88 | 100 | 100 | 60 | 2.537s | 0 |
| App before layout fix | 66 | 100 | 100 | 60 | 2.822s | .520 |
| App after layout fix | 76 | 100 | 100 | 60 | 3.1s | .002 |

Landing median performance **86**, not ≥90; LCP still exceeds 2.5s. These goals
are **unmet**. Accessibility/best-practice goals pass in these lab checks. SEO
60 reflects deliberate private-preview `noindex`; it was not removed to inflate
scores. No public canonical URL was invented. CLS goal passes after the material
app fix. Working interactions take precedence over stripping the functional UI.
Lighthouse does not measure field INP or establish real-user Core Web Vitals.
CSS 200% zoom is a reflow test, not a claim of browser-menu zoom equivalence.

## Security/dependency triage

`npm audit`: zero reported advisories. Pinned `pip-audit 2.10.1` on the locked
Python requirements: zero reported vulnerabilities; `pip check` passes. No
destructive `npm audit fix`, broad dependency upgrade or lock replacement ran.
The existing Starlette test-client deprecation is non-failing compatibility debt.
No project linter or coverage tool was configured; compile/type checks and
meaningful regression tests were run. No coverage percentage is invented.

Working files and all 436 historical Git blobs were checked against currently
configured secret bytes and explicit key/private-key patterns. No matches;
`.env`/private directories are ignored. This is a focused scan, not a universal
entropy/secret guarantee. No stored NVIDIA key was read. Public-ready fixtures
and receipts are authored synthetic data, not private field records or community
audio. Original source archives remain immutable.

Docker Scout was not executed: automatic approval rejected possible image/package
metadata transmission to Docker. The replacement downloads Debian's complete
public advisory JSON, then matches source-package versions locally in a
network-disabled read-only container. No inventory is sent externally.
`debian-image.json` reports **201 candidates** across 69 source packages: 115
open, 85 resolved upstream but older installed versions, 1 undetermined. Debian
urgencies: 156 not-yet-assigned, 44 unimportant, 1 low. These labels are not CVSS.

Thirteen source packages have fixed-version candidates: dpkg, glibc, gnupg2,
gnutls28, libcap2, libgcrypt20, openssl, pam, pcre2, perl, sed, systemd, xz-utils.
Triage: **do not publish this image** before targeted base-package refresh and
repeat Docker/host compatibility checks. Do not dismiss unassigned urgency as
safe. Open/unimportant distribution issues require individual applicability
review; no blanket exploitability claim is made. Bundled Node/CPython binary
advisories are outside this Debian source-package scan. The image is a verified
local Sample runtime, not a security-cleared hosted release. No image was pushed.

## Reproduction and owner review

Use the README's exact production Windows launch or `docker compose build` then
`docker compose up -d` (stop host 3000/8000 first). Keep the evidence volume.
For repeat checks:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm run test:world-model
npm run conformance:world-model
.\.venv\Scripts\python.exe -m scripts.export_contracts
npm run contracts
npm run typecheck
npm run build
npm run start
# Separate terminal, with the local API also running:
node scripts/verify_stage7_keyboard.mjs
$env:LASTCOPY_BROWSER_OUTPUT='private/stage7/new-visual-check'
$env:LASTCOPY_BROWSER_EVIDENCE='private/stage7/new-visual-check/screens'
node scripts/verify_stage6_browser.mjs
```

`verify_stage7_offline.mjs` requires a fresh empty Sample workspace and stopped
providers. Use `SAMPLE_MODE=true`, a fresh `LASTCOPY_DATA_DIR`,
`PYTHONPATH=scripts/offline_guard` for Python, and
`node --require ./scripts/offline_node_guard.cjs node_modules/next/dist/bin/next start web --hostname 127.0.0.1`.
The fences are audit utilities, not normal production configuration.

Pinned Lighthouse command: `npx --yes lighthouse@13.5.0 http://127.0.0.1:3000/ --chrome-flags='--headless=new' --only-categories=performance,accessibility,best-practices,seo --output=json --output-path=private/new-mobile.json --quiet`.
Set `CHROME_PATH` to the installed Playwright Chromium executable first; preserve
all repeat scores. `scripts.audit_debian_image` performs the local-only image
advisory check; `scripts.audit_release` performs the focused Git/current scan.

Review `README.md`, `LIMITATIONS.md`, `ARCHITECTURE.md`, `SAMPLE_IO.md`,
`DEMO_SCRIPT.md`, `PITCH_DECK.md`, `SUBMISSION_REVIEW.md`, `DEPLOYMENT.md` and the
receipts above. The actual demo video/deck files are not recorded/assembled by
this stage. The current authenticated Open Agent template remains unverified;
no guessed template metadata is emitted. Public rules now explicitly make Cursor
optional; Codex development provenance is accurately declared. No publication,
visibility change, final deployment or submission has occurred.
