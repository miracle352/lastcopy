# Stage 1 verification — 2026-10-23

Status: **Stage 1 skeleton and connected integration/Collect format gate verified**.
No preservation, investigation or recovery feature is claimed complete.

## Actual local observations

| Check | Observed result |
| --- | --- |
| Node / Python | Node 24.12.0; Python 3.13.7, Windows |
| Isolated Python dependency install | Successful; exact versions in requirements.lock |
| Python tests | 41 passed; one Starlette deprecation warning for its httpx-based test client |
| Python dependency consistency | `pip check`: no broken requirements |
| Archive inventory CLI | Four files; original inspection-final.xml; explicit completion provenance; two ordered media references sharing one slot |
| Raw server snapshot validator | One synthetic version; two synthetic receipts; payload/identity/hash checks passed |
| OpenAPI generation | Pydantic schemas exported; pytest verifies artifact equals authoritative models |
| Browser/API type generation | openapi-typescript generated browser types; TypeScript check passed |
| Production web build | Next.js 16.4.3 build passed: /, /_not-found, /api/health, /api/inventory |
| Actual Meterless reference bridge | PASS: one observation processed, replay processed zero, snapshot entity read from graph |
| Unmodified upstream tests | 10 passed using root's patched Vitest 5.0.5 |
| Unmodified upstream conformance | 8/8 checks passed, including provenance, stable IDs, merge bands, append audit and idempotency mutation control |
| npm audit | Zero known advisories in active workspace lock after replacing vulnerable initial test runner |
| Local API boot | Uvicorn running on 127.0.0.1:8000; real HTTP sample flow used it |
| Production web boot | Next start ready on 127.0.0.1:3000 |
| Browser | Actual sample button→API inventory→four files/one version/two references; preservation_checked=false |
| Responsive review | Desktop screenshot reviewed; 390px mobile screenshot reviewed and saved; mobile scrollWidth=innerWidth=390, no page overflow |
| Keyboard | Skip link visibly focused with Tab; sample action activated with keyboard; status result rendered |
| Private GitHub repository | miracle352/lastcopy, API reports private=true |
| Docker | Engine 29.9.1 accessible outside sandbox; no Central stack started |

One test-client deprecation warning remains: current Starlette recommends httpx2
for TestClient. API requests and all tests pass; production integration code uses
httpx 0.28.1. This is not a failed live check. No unsupported automatic dependency
upgrade was used. Root toolchain versions are locked; the upstream reference's
original package/lock are retained for provenance and are not installed/executed
as a separate development environment.

The deterministic representative ZIP hash is
`57a4865ba7bf63542dbef16baf2d11c25570a38a15c5d15a755588249e90878d`.
The sample network-isolation test populates all provider settings, prohibits the
probe dispatcher/socket connection and verifies each provider is still blocked.
A connected provider failure remains a failure; no sample fallback occurs.
Archive tests cover traversal, symlinks, encrypted flags, duplicate normalized
paths, file-parent collisions, entry floods/decompression/upload limits, XML
DTD/entities/depth/nodes/text/bytes and malformed XML. Scope/provenance tests cover
unknown/draft completion, missing original form/media and mismatched destination.

Desktop screenshot saving through the browser connector was denied by that
connector's workspace-root configuration. The screenshot was still returned and
visually reviewed. The mobile screenshot was returned normally and saved through
the authorized workspace file tool at `verification/mobile-390.png`. This is a
browser screenshot, not AI-generated imagery. Stage 6's full visual audit, zoom
matrix, reduced-motion interaction review and performance targets are not claimed.

## Real integration checks — not run successfully

Rerun commands are in README and INTEGRATIONS.md. The connected-mode smoke
commands were executed and reported **BLOCKED before any request**. Individual
machine-readable receipts are in `verification/{zetaris,nightshift,odk}.json`.

- Zetaris: local 2.4.3.1 installed; actual auth/query contract configured privately.
  Vendor verifier 9/9 PASS; constant SQL and independent two-source synthetic
  evidence query PASS. Sources are registered local NDP CSVs, not S3. Connected
  evidence receipt: `verification/zetaris-live-2026-10-23.json`. No AWS cluster,
  AWS source upload or IAM change occurred; AWS/S3 compatibility remains untested.
- Nightshift: resolved. Version 1.2.3 serves a verified 1B GGUF on CPU through
  `meterless/auto`; real authenticated inference PASS at 19:39:31Z, 9040.73 ms.
  Actual identity `local-runtime/llama-3.2-1b-instruct`. Structured JSON observed
  supported, native tools not demonstrated. Receipt:
  `verification/nightshift-live-2026-10-23.json`. No Nemotron claim.
- ODK: official Central v2026.3.1 is now running locally with the dedicated
  synthetic project. Connected read-only smoke PASS on 2026-10-23T18:02:54Z:
  authentication, project metadata, version XML and attachment byte retrieval.
  Sanitized receipt: `verification/odk-live-2026-10-23.json`. Actual Collect export verification is recorded separately below. Historical
  replacement behavior and recovery writes remain untested.

These observations now resolve the Stage 1 configuration/format blockers. No
secrets were copied from unrelated projects. Tested compatibility remains limited
to the documented synthetic captures and explicit server behavior.

## Requested deployment

Vercel project `lastcopy` has been created and linked to the new private repo.
Production deployment **READY**:
[lastcopy-five.vercel.app](https://lastcopy-five.vercel.app/).

- Deployment ID: `dpl_ifKUPUttNy7KipoVdQFw3XUxkghc`.
- Tested application commit: `dfbc15b2ac21dae389306c706a509ba5750179df`.
- Framework: Next.js 16.4.3, Node 24.x; remote build duration about 23 seconds.
- Vercel deployed the Git push through the configured private GitHub connection.
- Direct isolated-browser check: page rendered the actual Stage 1 skeleton.
- Direct hosted `/api/health`: HTTP 200, `service=lastcopy-web`,
  `evidence_backend=not_deployed`, `live_verified=false`.
- Direct hosted `/api/inventory`: HTTP 503, private API unavailable.
- Actual hosted button: explicit unavailable-backend explanation and enabled
  retry control, no substituted fixture result or fabricated preservation.
- Later documentation/test-only commit adds this record and the partial-snapshot
  control. Web application source remains unchanged from the tested commit.

Vercel's fetch-helper connector returned a scope-related 403; direct browser
requests to the public deployment passed the HTTP checks above. This connector
limitation does not block deployment. No authorization settings were broadened.
Post-deploy observability: health/error behavior checked directly; runtime-log
scan and external monitoring/drains are not configured or claimed. No Lighthouse
or production evidence-processing benchmark was run at Stage 1.

Partial snapshot control: missing media with a failed receipt and incomplete
scope validates as partial. Changing it to complete scope is rejected. The final
41-test run passed after adding this control. The private evidence API stays local.

Unblocking follow-up: all **46 Python tests passed** after adding guarded local
setup helpers. The only warning remains the existing Starlette test-client
deprecation. No application/web/contracts source changed during this follow-up.
Installation provenance, exact readback hashes and remaining blockers are recorded
in LOCAL_SETUP.md. At that earlier checkpoint, Stage 1 live verification was
incomplete; the later blocker-resolution checks below supersede that status.

Local Zetaris follow-up: final **54 Python tests passed** after the actual local
installation, body-option compatibility fix, S3 source-scope alias controls,
credential boundary checks, file-lock retry control and isolation of an older
test from the now-configured ignored `.env`. The existing Starlette warning is
unchanged. The first smoke HTTP 400 exposed the required `pageLimit` field; after
configuring it, the independent smoke passed in 8802.67 ms. Configuration remains
Sample by default. No web application source or domain schema changed in this
follow-up. Nightshift inference and the actual Collect native-path export are now verified.

## Blocker resolution: actual Collect export

Actual Collect v2026.3.5 ran in the dedicated AOSP API 30 emulator. The new
synthetic form was filled and finalized through the app; native XML, original
XForm, attachment and metadata were copied after force-stop. The selected native
database row has `status=complete` and `finalizationDate`; the UI showed Ready to
send count 2 including the earlier negative control. No record was sent.

LastCopy inventory passed identity/version, two ordered readings (`03`, `05`),
site code `0017`, original bytes and attachment hash. ZIP SHA256:
`7777ac13eba61e0a463925cb0973f14453b18b27b2f0809d196d1b796c074c79`.
Receipt: `verification/collect-export-2026-10-23.json`.
A bad authored XForm namespace was detected first and retained privately; the
supported record uses a new corrected form identity. Regression coverage requires
mismatched namespace to remain a limitation. No comparison rule was weakened.

No known Stage 1 external blocker remains. Nemotron, physical-device coverage,
AWS/S3 connectors and recovery execution are unverified future scope.

Final blocker-resolution regression run: **56 Python tests passed**, including
actual Collect capture bytes/identity/repeats/media/completion and the namespace
mismatch negative control. One existing non-failing Starlette/httpx deprecation
warning remains. `node --check scripts/setup_nightshift_text.mjs` passed. No web
or API schema contract changed in this follow-up, so prior build/type checks remain
applicable. Local service restoration was checked after emulator shutdown.
