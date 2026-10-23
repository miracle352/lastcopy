# Stage 1 verification — 2026-10-23

Status: **local Stage 1 skeleton verified; live integration gate remains blocked**.
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

- Zetaris: no configured SQL endpoint, auth/request/response contract, registered
  two-source fixture scope, approved S3 prefix or deployed version. No real query
  has run; no rows/hash from Zetaris are claimed. Two tiny input CSVs and a
  registration template are prepared. Existing AWS deployment is to be reused.
- Nightshift: installed 1.2.3, real token configured locally, wrong-token rejection
  401 and authenticated inventory 200 observed. Inference attempted and failed
  HTTP 400 with `no_provider_configured`; a serving model must be configured.
  Inference/capability and concrete model identity checks remain incomplete.
- ODK: official Central v2026.3.1 is now running locally with the dedicated
  synthetic project. Connected read-only smoke PASS on 2026-10-23T18:02:54Z:
  authentication, project metadata, version XML and attachment byte retrieval.
  Sanitized receipt: `verification/odk-live-2026-10-23.json`. No real Collect
  export version, historical replacement behavior or recovery write is tested.

These are genuine configuration/data-access blockers. No secrets were copied
from unrelated projects. The only source format pin is the synthetic native-path
ZIP/manifest v1, not a claimed real Collect/Central compatibility matrix.

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
in LOCAL_SETUP.md. Full Stage 1 live verification remains incomplete.
