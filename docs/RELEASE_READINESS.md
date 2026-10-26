# Submission review — 26 October 2026

Latest follow-up: [SUBMISSION_FINISH.md](SUBMISSION_FINISH.md) records the newer security fixes, automated off-host backup, narrated film and actual remaining checks. Earlier results below retain their original scope.

Public product: https://lastcopy-five.vercel.app/ . Judges can use `/demo`
without an account and inspect `/technical` for explicitly labelled Replay
receipts. The private workspace and Central run on the approved $24 AWS host;
the PC is not needed to host them. Repository visibility is unchanged.

## Verified in this release

- Full Python suite: **243 passed, one Windows symlink skip**, one existing
  Starlette/httpx deprecation warning. The earlier three failures were outdated
  driver-identity test fixtures; the wrong-container security assertion remains.
- JavaScript gateway/key/scroll/browser-policy checks: **16 passed**.
  Pinned World Model conformance: **8/8**.
- A real production container with `--network none` compared all five sample
  cases over actual Uvicorn HTTP, downloaded findings/reports/bundle, compared
  the separate readback fixture and retained every fixture-file hash.
  Check `verification/release-final/offline-container.json` for the actual count;
  this is not a claim that a saved capture is live.
- Both fresh local sponsor investigations completed. Each made four actual
  Zetaris queries and three Nightshift calls, with two critique rounds and graph
  reads selecting work. The serving identity reported by Nightshift was
  `nvidia/nemotron-3.5-lightning-30b-a3b`. Export guidance replaced the missing-data
  hypothesis; the second case retained an unresolved conflict. Independent
  recomputation and source/query/graph seals passed.
- A stopped Zetaris driver caused the first fresh attempt to fail. Its UI/API
  had remained healthy. Restarting the existing driver fixed the path. Preflight
  now checks driver identity/readiness before login and bounds Docker probes.
  The failed attempt was retained; no sample fallback was substituted.
- Actual Central XML/version/media readback of the previous synthetic recovery
  still showed preservation. Repeated Apply was tested with writes prohibited:
  one matching instance, zero uploads and unchanged original archive hashes.
- Account connections were tested against actual Central GETs in temporary
  isolated stores on AWS. Existing Viewer credentials stayed on that host; this
  was not a new Cognito signup or automatic Central provisioning claim.
- The owner confirmed real password-reset email delivery, reset and sign-in.
  Real verification-email/signup delivery had already been confirmed.
- Morning scheduled encrypted backup succeeded. The explicitly approved
  encrypted off-host copy matched its ciphertext hash. Older copies were not
  deleted. The owner-only health view reports recent success, failure and disk
  reserve. Completed sealed investigations are now included alongside SQLite
  ledgers and Central's dump; keys and adjacent configuration remain excluded.
- npm full/production audits report zero advisories. PyPI reported no advisories
  for the 25 pinned Python versions checked. This does not replace independent
  review. Debian image findings remain open; read their actual receipt.
- Final deployed public and authenticated owner browser flows passed. Scroll
  stages, section reveals, enhancement-failure fallback, keyboard choices,
  drawers, downloads, reload and sign-out passed. Widths: 360, 390, 768, 1000,
  1280 and 1440px. Landing scroll-flow CLS was 0.007. The four Linux backup tests
  passed, including the symlink check skipped on Windows; final-image World
  Model conformance was 8/8. All eight previous evidence seals are unchanged.
- Production mobile Lighthouse 13.5.0 / Chromium 153: landing performance
  **96 / 91 / 88**, median **91**, median LCP **2.47s**, CLS **0**. Demo:
  **98**, LCP **2.13s**, CLS **0**. Accessibility, best practices and SEO were
  **100** in all four runs. Simulated 4× CPU, 150ms RTT, 1638kbps throughput,
  412×823 CSS pixels / DPR 1.75. One landing run missed the goals (88, 2.504s);
  median success is not a guarantee. See `verification/release-final/lighthouse-summary.json`.

## Changes users can see

The scroll story and section reveals use actual scroll position. Decorative
pause/play controls are absent; genuine automatic-check Pause/Cancel controls
remain. Reduced motion and the static first frame remain readable. The example
interface loads near its section, then runs the real comparator automatically;
an unavailable enhancement has a visible fallback rather than invented results.

Sign-out is in navigation. Public case choices use keyboard-operable native
radios. Sign-in uses the existing server-verified owner endpoint when email is
blank; it has no credential bypass. Private account connection setup verifies
the configured HTTPS Central origin, exact project and form before saving a
read-only scope. Secrets stay server-side in mode-0600 files. Account setup has
a persisted attempt limit and one shared upstream-test slot; it cannot enable
recovery or choose arbitrary URLs. The production browser policy restricts
resources/forms/frames; Next's inline bootstrap is still allowed, so this is not
a strict nonce-based CSP claim.

## What still needs a decision or external acceptance

1. **Physical-device backup:** Collect can submit to hosted Central independently
   of this PC. Automatic independent exports from a physical phone are not
   verified. The tested emulator/relay requires the PC. Do not erase originals.
2. **Project onboarding:** signup creates a private LastCopy account, not an ODK
   project/App User. An operator must grant Central Viewer access and privately
   pair a collector. Imported manifests and scoped snapshots remain supported.
3. **Always-on sponsor runtime:** the fresh integrated sponsor path is verified
   locally. Its saved public receipts are Replay. Direct NVIDIA on AWS is a
   separate working provider; it is not Nightshift. No unsupported Linux port,
   extra server, Zetaris cluster or expanded IAM role was provisioned.
4. **Disaster recovery:** daily copies are on the same host; one approved
   off-host copy is verified. Unattended independent replication and alerts,
   Enketo-link/configuration restoration and full-machine recovery are incomplete.
   Running/unsealed investigations and private provider/connection configuration
   are excluded. Re-enter those credentials after restore. Backups refuse an
   aggregate above 2 GiB or less than 5 GiB free; retention has no deletion.
   Keep another secure copy of the recipient key outside OneDrive.
5. **Privacy/security:** agree retention/deletion/support procedures before
   sensitive field use. Self-service erasure and independent security review are
   incomplete. Shared free Cognito email capacity and the 100-account beta cap
   apply. Resend still needs an owned verified domain; none was purchased.
6. **Performance/accessibility:** use the final measured mobile receipt, not a
   predicted score. Native browser zoom, physical touch devices and field INP
   are not established by CSS layout zoom or Lighthouse.

## Submission assets and owner actions

The review deck is in `submission/LastCopy-submission-deck.pptx`; its editable
text, package geometry, fonts and first-party import are validated. All eight
slides were rendered and visually inspected; native PowerPoint was not used.
The actual UI recording is `submission/LastCopy-demo.mp4` (2m43s), with authored captions
below the interface and a separate `LastCopy-demo.srt`. The recording distinguishes
Sample and Replay and does not stage another live upload on camera. Review both
assets before manual submission. Final duration and hashes are in the release
submission-assets receipt.

The expanded official rules were checked on 26 October:
https://hackathon.genai.works/event/open-agent-hackathon-2026#rules . **Every
entry must integrate Zetaris and Meterless.** Required deliverables include a
1–4 minute video, slide deck, GitHub source/README and sponsor explanation.
Deadline: **27 October 23:45 UTC / 28 October 00:45 Africa/Lagos**.

The authenticated submission-form fields remain unverified. Use the owner's
normal signed-in browser at https://hackathon.genai.works/submissions . Review
the video/deck, choose judge access to the private repository (use branch
`codex/product-redesign`), and submit manually. No public visibility change,
merge to main, asset upload to another service or event submission is automatic.

## Exact launch commands

Hosted use needs no terminal: open the Vercel site or its private workspace.
For the local emulator link, open **PowerShell** in the repository folder:

```powershell
Set-Location "C:\Users\IYANUOLUWA\OneDrive\Documents\ChatGPT\My experiments\lastcopy"
./scripts/open_collect.ps1
./scripts/start_cloud_link.ps1
```

The repository root is that folder; PowerShell is the terminal. For standalone
offline setup, API/CLI examples and the production web command, see
`RUN_LOCALLY.md`, the root README and `.env.example`. Keep keys out of chat.
