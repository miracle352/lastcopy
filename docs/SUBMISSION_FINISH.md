# Submission finish — 26 October 2026

Newest acceptance: [BACKUP_ACTIVATION.md](BACKUP_ACTIVATION.md) closes Enketo
activation, isolated S3 component restore, native Chromium zoom and the
owner-transcribed submission fields; see the linked morning submission checklist.

This supersedes earlier readiness counts where it explicitly gives newer results.
Further risk work is recorded in [RISK_CLOSURE_FOLLOWUP.md](RISK_CLOSURE_FOLLOWUP.md),
including the newer performance result and prepared Enketo restore scope.
The repository remains private. The owner will make it public after review;
no event submission has been made.

## Product and evidence

- Public entry: <https://lastcopy-five.vercel.app/>. Judges can use `/demo`
  without an account. `/technical` clearly identifies captured sponsor work as
  Replay and now exposes its actual SQL, rows, model actions and hypothesis
  revisions in keyboard-operable disclosure controls.
- The existing AWS workspace and ODK Central keep working while the PC is off.
  Public signup, email verification and password reset use the existing hosted
  account system. The owner previously confirmed email/reset/sign-in delivery.
- New genuine recovery: `narrated-demo-20261026`, dedicated synthetic project 2.
  An authored fixture derived from the retained emulator export was seeded with
  XML but without its referenced attachment. This is not new physical collection.
  The actual UI staged/reviewed the exact plan, re-read the target, restored the
  missing file, fetched fresh XML/version/media and verified preservation.
  Reload retained the result; repeated Apply returned verified without another
  upload. The real collection project 1 was not written to.
- Original emulator export SHA-256 remains
  `25dadf67ef5c4f58e9d13ce85d5ed0e930abff1d2b5e311815694e5aa69382f3`.
  The authored demo source is separately identified and remains immutable.

## Checks

- Working core suite: **257 passed, one Windows symlink skip**. Existing
  Starlette/httpx deprecation warning remains. In the production candidate,
  **258 passed** as UID 10001 with networking disabled, using a writable scratch
  source copy because three existing tests intentionally regenerate fixtures.
  A first run against root-owned image source correctly refused those writes;
  the production filesystem was not made writable to satisfy tests.
- Targeted parser/native-transfer security suite: **20 passed**. Small controls
  fail against the old implementation and pass against the fixes. XML now bounds
  expanded names/namespaces and aggregate derived paths before retaining facts.
  Native SQLite metadata must be an ordinary table; value/query/row bounds apply
  before materialization. Preservation comparison rules are unchanged.
- Account export/erasure-review test passes with tenant isolation, source hashes,
  persisted idempotency and a read-only operator request queue. No automatic
  erasure or backup expiry has been activated.
- Pinned World Model: **10 tests passed; 8/8 conformance checks**. Type checking
  and production builds passed. JavaScript/TypeScript checks: **16 passed**.
  The final deployed image also passed actual HTTP offline acceptance for all
  five bundled cases with Docker networking disabled, zero provider calls and
  all 51 source-file hashes unchanged. Hosted/browser receipts record actual sample,
  evidence, bundle, readback, refresh and responsive checks at 360, 390, 768,
  1280 and 1440 pixels, reduced motion and 200% CSS layout scaling.
- [Independent automated source review](verification/submission-polish/security/report.md)
  retained two resource-exhaustion findings in its pre-fix source snapshot.
  Their working fixes are tested separately, including a namespace guard that runs before tree expansion; do not describe the old snapshot
  as a zero-finding scan. It is not an external human penetration test.
- The newer Debian base reduced advisory-database matches from 116 to **72**:
  43 unassigned and 29 unimportant under Debian's labels. This is not a clean
  image claim. The final image is
  `sha256:2ee904ea5edc695e5cfea68e0cccdf405b877ddb71d651faf13c1e876b15abe6`.
  The scan used the retained public Debian database locally and sent no
  image/package inventory to an external scanning service. Node/CPython binary and application
  vulnerabilities are outside that Debian database's scope.

### Latest mobile performance: target not met

Production home-page Lighthouse checks on 26 October returned performance
**61, 62 and 59** (median **61**); the latter two followed completion of media
encoding/core tests. A third idle repetition timed out after 180 seconds, so no
three-run idle median or new demo score is claimed. Completed runs had
accessibility, best practices and SEO **100**, CLS **0**, and LCP **2.51, 2.93
and 3.13 seconds**. These do not meet the performance ≥90 / LCP ≤2.5s goals.

Profile: Chrome 153, Lighthouse default simulated mobile, 412×823, DPR 1.75,
4× CPU slowdown and 150 ms simulated RTT. The host benchmark index was 316–388
versus 1348.5 in the earlier sealed release measurements; the new reports show
substantial script/layout time on this heavily constrained PC. That observation
does not invalidate the new low scores or prove other devices fast. No homepage
JavaScript or animation was added for this finish. Detailed evidence viewers
remain server-rendered, and motion/sample enhancement remains lazy-loaded.
Repeat on a quiet reference machine before claiming the target. These are lab
measurements, not field INP or Core Web Vitals. See `lighthouse-summary.json`.

## Backup and privacy operations

Daily encrypted S3 replication is active on the existing host. A real systemd
run uploaded new ciphertext, fetched it back and verified its hash. The timer is
enabled. The private Singapore bucket blocks public access, uses versioning/SSE
and HTTPS-only transport. The uploader is prefix-scoped and cannot delete.
The 512 MiB software guard stops new uploads rather than expiring old copies;
it is not an AWS-enforced billing cap after credential compromise.

Only encrypted database/evidence backups leave the host. The temporary plaintext
uploader credential on CloudShell was removed after the approved encrypted
transfer; the actual host credential remains private. Recipient decryption-key
custody remains the owner's responsibility. Keep a second secure offline copy.

Existing database restore drills remain valid for their recorded backups. The
new isolated S3 restoration also covers Enketo Redis and generated-key bytes.
Daily replication does not itself establish automatic restoration. Full host
configuration recovery is incomplete; adjacent environment/provider credentials
remain excluded. Do not promise full-machine or public Web Form-link browser recovery.

Verified users can download their registered originals and deterministic reports
under **Your data**, and submit an authenticated erasure-review request. Requests
remain pending until an operator handles them. The read-only queue command and
the prepared, inactive policy are in [RETENTION_POLICY_DRAFT.md](RETENTION_POLICY_DRAFT.md).
No original, older backup or field record was deleted.

## Demo and review

[Narrated demo](../submission/LastCopy-demo-narrated.mp4) and
[captions](../submission/LastCopy-demo-narrated.srt): under three minutes.
It uses actual product footage, a code-built problem opener and expressly
requested local speech synthesis. No AI-generated imagery or community audio.
Sample, Connected synthetic recovery and captured Replay are labelled separately.
The original caption-only film and editable deck remain available unchanged.
[Delivery notes](../submission/README.md) identify the recommended film, modes,
chapter timing and actual encoding/audio checks. Earlier deck performance
figures are historical and must not replace the latest measurements above.

## Remaining acceptance and launch

Early attempts failed while Docker or the local Nightshift endpoint was unavailable, and retained failure traces without sample fallback. Restarting the installed runtime restored its authenticated inventory (76 models). Fresh export and conflict investigations then both completed: four actual Zetaris queries, three Nightshift calls and two critique rounds each, with reported serving identity `nvidia/nemotron-3.5-lightning-30b-a3b`. Independent recomparison, query/source/output seals and World Model rebuild passed. The export hypothesis changed to guidance; the conflict stayed unresolved. See `connected-export-verified.json` and `connected-conflict-verified.json` under the new verification folder.

The film's sponsor chapter still says Replay: it shows a saved successful capture, not a live inference while watching. A vendor-supported always-on Nightshift runtime is not available on the small Linux host, so that combined sponsor path remains local and must not be advertised as always on. The hosted verifier, accounts, Central and bounded recovery are independent of this PC.

Physical-phone backup, a complete machine restore and human penetration testing
remain unverified. Native 200% Chromium zoom is now tested; current organizer
field labels were supplied by the owner from the authenticated form.
Public Central project/App User provisioning is still an operator action. Emulator
and automated source-audit results do not substitute for physical-device/human checks.
A verified email-sending domain is still absent; shared account
email limits remain. Read [RUN_LOCALLY.md](RUN_LOCALLY.md) for exact PowerShell
commands; hosted judges can simply open the public demo link above.
