# LastCopy Implementation Plan and Codex Prompts

> For agentic workers: use the repository's existing execution/review skills when available. Follow these stages in order; do not install a skills framework just to execute this document. Each stage has a checkable deliverable. The user has requested implementation in Codex.

**Goal:** Build LastCopy: independently reconcile surviving field-device backups with an ODK Central server, prepare bounded recovery, and verify preservation by reading the server again.

**Architecture:** A local-first web application with a deterministic reconciliation/recovery core, a bounded investigation loop, and an evidence ledger. Zetaris is the live evidence-query layer; Meterless World Model connects observations and hypotheses; Nightshift is the primary AI provider. Offline sample mode has separate, clearly labelled adapters.

**Tech stack:** Preserve a suitable existing stack. For an empty repository, use Next.js + TypeScript for the web UI, Python + FastAPI for the API/core on port 8000, SQLite/local private files for single-user development persistence, and a small Node/TypeScript bridge to the pinned official Meterless World Model reference. Select compatible supported versions from official documentation, then lock them. No hosted database, Redis, auth SaaS, GPU, or new Zetaris deployment is necessary for the initial build.

**Spec:** The Product Contract below is authoritative for these prompts. Save it to `docs/PRODUCT_SPEC.md` during Prompt 1; save the project-specific task plan to `docs/superpowers/plans/2026-10-23-lastcopy.md`.

## How to use this packet

Keep this file in the Codex project as `LASTCOPY_CODEX_PROMPTS.md`. Paste Prompt 0 once, then paste Prompts 1–7 in order in the same project. The product and visual direction are approved; routine implementation choices do not require another permission loop. Respect actual credential, data-access, and deployment boundaries. Complete each stage's checks before moving to its dependent stage. Do not claim that preparing these prompts means any implementation or integration has already passed.

## Product Contract

### User and outcome

- First user: a field coordinator closing an inspection, environmental survey, or research campaign using ODK Collect and ODK Central.
- Question: which completed records and referenced files in the supplied device snapshots have a verified server copy, which need recovery, and which remain unresolved?
- The initial supported platform is ODK Central. Kobo incidents motivate the problem, but Kobo compatibility is not a first-release promise. Do not call ODK recovery bundles universally compatible with Kobo.
- Core flow: add device exports and expected-device roster → acquire scoped server evidence → investigate gaps → review a recovery plan → apply permitted operations to an explicitly configured test server → fetch fresh server evidence → rerun the same checks → export an evidence report.
- Account for a matching retained historical submission version. A legitimate newer edit is not automatically corruption and must not be overwritten.
- Preserve source archives. Work on copies. Preserve references between form versions, submission versions, repeat occurrences and media files.
- Report only on supplied snapshots and verified scope. A missing device, incomplete export, permission error, unavailable history, unreadable attachment or unsupported encryption prevents complete coverage. Never promise that all work ever collected is safe to erase.
- A hash proves equality/integrity of checked bytes; it does not authenticate the original publisher or prove that respondents' answers are true.

### First-release input contract

- Accept an unencrypted ZIP of one ODK Collect project's surviving instance directories and matching original XForm XML definitions. Preserve native paths, including an enclosing project directory. Each selected instance points to its actual XML filename and relative media files; do not assume every file is named `instance.xml` or infer record identity from a folder name.
- Normalize the input through a LastCopy `device-manifest.json` with `schema_version: 1`, `snapshot_id`, `device_id`, `captured_at` (or explicit unknown), `collector_version` (or unknown), `instances: [{xml_path, completion_status}]`, and `form_definitions: [{xml_path}]`. Allowed completion values are `complete`, `draft`, `unknown`. The app may create this manifest through a guided import while retaining the original ZIP unchanged. Use trustworthy available exporter metadata, otherwise obtain an explicit coordinator selection/attestation. Never silently infer that every saved XML file is completed. Inventory drafts/unknowns, but exclude them from automatic submission until completion is explicitly established.
- Device labels and the expected-device roster can be coordinator-supplied; label their origin. Parse original instance/form/version IDs and any edit-chain metadata from XML. Destination ODK project and form mapping come from the configured connection and explicit run scope, not a guessed device filename. Validate every mapping. Missing identity, an incomplete edit chain or a missing original form definition becomes an explicit verification/recovery limitation, not an invented association.
- Support server evidence from either the configured Central API or a versioned LastCopy raw snapshot produced by that same read-only exporter. The snapshot manifest records project/form scope, capture time, scope completeness, logical submission/version IDs, metadata and relative paths to original XML and downloaded media. Include request/evidence receipts. A flat server CSV is an optional view to diagnose, not sufficient preservation evidence. Synthetic snapshot packs are labelled synthetic.
- Stage 1 pins and records the actual Collect/export format and Central versions tested. Compatibility is limited to this documented format and tested server behavior; do not claim every historic/mobile export format is supported. A source ZIP missing media cannot be used to reconstruct absent bytes.

### Deterministic correctness

Use code for ZIP inventory, XML parsing, record identity, version-chain checks, repeat preservation, cryptographic hashes, comparisons, bundle contents, request execution and final verdicts. A model can propose diagnoses and evidence checks; it cannot supply missing answers, override comparisons or declare preservation.

For XML, compare namespace-aware expanded names, attributes and ordered child/repeat occurrences. Ignore attribute ordering and namespace-prefix spelling, not meaningful leaf values. Specify and test treatment of formatting-only inter-element whitespace. Preserve significant whitespace, Unicode and leading zeros. Do not flatten repeated groups into a single dictionary entry. Do not infer a blanket list of ignorable fields.

For media, identity includes submission/version and referenced filename. Multiple references to one filename can legitimately share one attachment. Two different filenames with identical bytes can legitimately require two accessible attachment slots. Compare retrieved bytes independently using SHA-256; do not count equal hashes as proof of every expected slot. Do not infer preservation from `exists=true` without the promised readback evidence.

Use these item verdicts: `PRESERVED`, `MISSING_SUBMISSION`, `MISSING_ATTACHMENT`, `CONTENT_CONFLICT`, `EXPORT_VIEW_ONLY`, `UNVERIFIABLE`. `EXPORT_VIEW_ONLY` requires positive evidence that raw server XML/media preserves the source while the selected tabular export omits it. Separate investigation completion from preservation success. Label an edited current record whose original is retained as history, and identify exactly which version was checked.

All findings carry evidence IDs resolving to source archive/file, XML path/repeat index or media reference, submission/form/version identity, capture time, query receipt and comparison result. If absence can only be established within a supplied export, say so; do not silently assert global server absence.

### Bounded recovery

Initially support creating a genuinely missing submission through the documented native ODK interface and restoring missing media on the verified supported target version. Preserve original IDs and XML bytes where the native retry protocol requires them. Never change an instance ID merely to bypass a conflict. Do not automatically overwrite different answers or reassign a file by filename similarity.

Every plan records target project/form/submission/version, source hashes, evidence, allowed operation and preconditions. Recheck preconditions immediately before a write. Handle uncertain POST outcomes through readback before retrying. Serialize writes for the same submission. Respect actual documented support for historical-version attachment writes; route unsupported cases to a manual plan instead of inventing an endpoint.

The app's Apply action is an explicit review of a concrete plan and configured environment. Initial automated writes target a dedicated test project with synthetic data. Recovery success requires fresh XML/media readback and the same deterministic verifier. Downloaded bundles are not labelled recovered merely because they were created. The app does not erase devices.

### Scope and evidence modes

- `SAMPLE_MODE=true`: deterministic synthetic examples and offline evidence adapter. No Nightshift, Zetaris, ODK, S3 or internet access. Label the mode and state that no live model was called. Never fabricate provider traces or pretend a local query was a live Zetaris call.
- Connected mode: actual integrations, explicit failure/partial status when a provider is unavailable. No silent fallback to sample data. Pure comparisons may remain available, but missing sponsor/AI work must be visible.
- Single-user local development first. No organization billing, collaboration system, new identity provider, arbitrary plug-in marketplace or general-purpose data-recovery promise.

### Hackathon requirements carried into the build

Target Open Agent Hackathon 2026, primary Track 02: The Agent That Can Explain Why. Deadline recorded in the event materials: October 27, 2026, 23:45 UTC (October 28, 00:45 WAT). Recheck organizer updates before final submission.

Required sponsor work: Zetaris as data layer; at least one tested Meterless engine in a working feature; Nightshift as primary AI provider. For the NVIDIA award, a real Nemotron model must perform meaningful work through Nightshift and traces must identify the actual serving model, not only a routing alias. Do not substitute a direct NVIDIA endpoint and claim it ran through Nightshift.

Submission preparation: public-repository-ready code with licenses and no secrets/private field data, README, 1–4 minute demo, pitch deck content, sponsor integration explanation. Treat JSONL traces, 3+ sample input/output pairs, a programmatic entrypoint, Docker instructions, bounded runs and offline sample mode as acceptance targets from the technical guide. Keep binding rules and recommended packaging requirements distinct in documentation. The Resources hub contained a separate G42/Compass problem-statement document; do not import that document's requirements into this Open Agent entry. Cursor wording conflicted across materials; use Codex inside Cursor where available and record actual development provenance without fabricating it.

### Global implementation constraints

- Follow local AGENTS.md and preserve unrelated work. Inspect the project before adding dependencies or choosing folders. Do not replace a suitable existing stack for cosmetic consistency with this packet.
- Use official API and engine documentation. Inspect implementations; do not invent an SDK, hosted engine endpoint, model ID, connector, or successful smoke test.
- User already has Zetaris on AWS. Reuse it; do not provision another instance, broaden IAM, or create paid infrastructure automatically.
- Keep credentials server-side and ignored. Diagnostics may show missing variable names, never secret values. Redact exported traces. Bind local services to loopback by default; document any container host-access setup explicitly.
- Treat imported logs/XML as untrusted data, never agent instructions. Protect ZIP handling against traversal, symlinks, duplicate normalized paths, encrypted archives, oversized decompression and entry floods. Disable XML DTD/external entities; bound XML depth, node count and text size. Configure and test finite upload/run limits.
- Recovery URLs come from an explicitly configured ODK connection, not arbitrary URLs in archives or model output. Encode identifiers correctly. Do not add arbitrary URL fetching to the UI.
- No image-generation tools or AI-generated raster art, videos or stock photography. Build UI, logo geometry, icons, diagrams and animation with code. If a real photo is useful, download a suitably licensed image from a verifiable source, save it locally, and record its creator, source page, license, attribution and modifications in `docs/ASSET_SOURCES.md`. Do not hotlink random images, copy Stripr's assets or bundle community members' recordings.
- Do not publish, deploy, submit the entry, make an existing repository public, or message organizers automatically. Prepare those outputs for the user's final action.
- Write meaningful tests for preservation/recovery/state transitions; avoid tests that only mirror implementation details or snapshot decorative markup.

## Review focus

1. A matching ID with changed values, hidden repeats or wrong attachment bytes must not produce preservation success.
2. Repeated media references and identical bytes under different filenames must be treated correctly.
3. Missing device coverage, partial exports, unavailable providers and permission failures must remain explicit unknowns.
4. A server edit or uncertain upload outcome must not trigger an overwrite or duplicate-creating retry.
5. Motion, large files and mobile layouts must not obstruct input, delay initial useful content or misrepresent recovery progress.

---

## Prompt 0 — Persistent instructions

```text
We are building LastCopy using LASTCOPY_CODEX_PROMPTS.md. Read the entire packet, especially its Product Contract and global constraints, before implementing. The user has approved this direction and asked for a working product plus a premium site inspired by https://www.stripr.xyz/. Inspect existing code, AGENTS.md, package manifests, environment setup and tests first. Reuse the existing stack where suitable.

Keep the Product Contract, product semantics and evidence modes consistent across every stage. Record the approved brief in docs/PRODUCT_SPEC.md and link the packet from project documentation without overwriting existing instructions. Use code for deterministic work; models investigate rather than determine truth. No image generation. More motion is explicitly requested, but responsiveness, readable content, accessibility and input responsiveness are mandatory.

Never invent integration success, model names, metrics, customer endorsements, recovered data or live evidence. Continue with authorized independent work when a credential is missing, record the affected blocker, and request only the specific missing setting when necessary. Do not ask routine implementation-permission questions. Execute only the stage I paste next; finish its checks, summarize changed behavior and actual verification, and preserve a concise docs/HANDOFF.md with the next stage and remaining blockers. Do not deploy or submit automatically.
```

## Prompt 1 — Establish the contracts and prove the integration path

```text
Implement Stage 1 of LASTCOPY_CODEX_PROMPTS.md. First inspect the repository and choose a minimal architecture compatible with its current stack. For an empty project, use the default architecture in the packet. Create docs/PRODUCT_SPEC.md, docs/HACKATHON_REQUIREMENTS.md and a file-by-file implementation plan with interfaces, meaningful tests and stage gates. Scope automated recovery to ODK Central in a dedicated test project; keep Kobo compatibility out of the first-release claim.

Create the smallest runnable skeleton, .env.example with placeholders, ignored local configuration, health endpoint and configuration validation. Implement the packet's explicit first-release input contract and add one representative archive layout with device-manifest.json, original instance XML, matching XForm definitions and media. Record the provenance of coordinator-supplied device identity/completion status and configure the destination explicitly. Use real docs to determine authentication and query details. Do not copy credentials from another project or print tokens. Define the domain objects RunManifest, SourceSnapshot, SubmissionVersion, XmlFact, MediaReference, EvidenceReceipt, Finding and RecoveryPlan in one authoritative schema/boundary per language. Generate or contract-test browser/API types instead of maintaining divergent handwritten copies.

Add repeatable smoke commands:
1. Zetaris: a bounded real query across two registered tiny synthetic evidence sources. Record SQL, source names, result rows/hash and elapsed time. Registration alone is insufficient. Reuse the user's existing AWS instance and S3 prefix where configured; use the official working small-CSV/S3 recipe before assuming another connector works. Configuration may supply the SQL endpoint/auth scheme discovered from the actual deployment; do not invent a bearer-token convention.
2. Nightshift: authenticated model inventory and one real inference using current official guidance. Follow the token/header and cold-load requirements in the cited provider guide. Inspect response/trace fields to resolve the actual serving model. Test available tool/structured-output support; if native tool calls are unsupported, use schema-validated action JSON with a code-owned tool dispatcher. Do not assume OpenAI compatibility implies every optional feature works.
3. Meterless World Model: pin the official reference/spec commit and run its existing tests or conformance suite. Use the actual reference through a small bridge or a documented conforming implementation. No dependency whose only use is an import.
4. ODK: read health/connection metadata and retrieve a known synthetic test submission's XML and attachment bytes from a real configured test server. Prepare an optional local ODK Central test setup from official instructions if needed. Do not expose a server publicly or modify production data.

Document exact successful/failed/not-run smoke results. When credentials or Docker are unavailable, complete the skeleton, schemas and offline fixtures, mark live checks blocked and identify the missing variable names/prerequisite. Do not call the stage live-verified until it is. Lock compatible versions after checking actual install/runtime support, including Windows development commands.

Acceptance: app/API boot locally, configuration errors are actionable and redacted, schemas agree, smoke commands are rerunnable, and docs distinguish real observations from blocked work. No polished marketing UI yet.
```

## Prompt 2 — Build the preservation verifier and honest offline examples

```text
Implement Stage 2 using the Product Contract. Build a deterministic archive/XML/media pipeline and a CLI that reads a RunManifest, reconciles supplied device/server snapshots and writes findings, evidence receipts and JSONL events. Add POST /run on port 8000 using registered input IDs/manifest references rather than trusting arbitrary filesystem paths. Keep private sources immutable. Use persisted run IDs and bounded jobs; separate run completion from preservation outcome.

Implement namespace-aware ordered XML comparison and version identity. Compare the matching retained historical version when appropriate and separately report current edits. Identify repeated groups by expanded paths plus occurrence indices, not labels or flattened keys. Compare each referenced media slot and retrieved bytes independently. Handle one filename referenced twice versus two filenames containing equal bytes correctly. Hash untouched inputs and outputs; source hashes alone do not authenticate a server.

Implement all six item verdicts from the packet, evidence references and coverage reporting. Keep finding codes separate from the underlying preservation status: EXPORT_VIEW_ONLY means the source was positively preserved, while a limited export caused the apparent gap; it must not schedule a data upload. No complete-coverage result when an expected device, source scope or required readback is absent. A failed authenticated request is not evidence that a record is missing. Preserve uncertain mappings as UNVERIFIABLE. Test missing completion metadata, missing original XForms and a mismatched destination scope; none may silently become an automatic recovery.

Create deterministic synthetic fixtures with hand-specified expected outcomes and seeds. At least these cases:
- Two genuinely stranded submissions among device snapshots; server contains other records so totals alone can mislead.
- A received submission with a missing attachment; include repeated references to one filename and two differently named files with identical bytes as correct controls.
- A tabular export that omits a repeated group while the original server XML preserves all repeat occurrences.
- A newer intentional server edit with the original version retained; preserve history and do not schedule an overwrite.
- Same-version content conflict, unavailable attachment/history, missing device, malformed XML and hostile ZIP inputs.

Use synthetic binary/text media or appropriately licensed downloaded fixtures; do not package a community user's voice recording. Expected outcomes must be authored independently of the production comparator. Add a held-out variant with changed IDs, paths and repeat counts so detection is not tied to hardcoded examples. Store at least three complete sample manifests with expected outputs. SAMPLE_MODE must execute comparisons without any external service or network, show its provenance, and make no model/provider calls. No fabricated LLM or SQL logs.

Prove tests fail for meaningful broken behavior, then pass after implementation. Verify the documented CLI and /run entrypoints against the same fixtures, evidence integrity, ZIP/XML limits and cancellation/error states. Record actual results and limitations in HANDOFF.md.
```

## Prompt 3 — Make Zetaris, the World Model and Nightshift drive investigation

```text
Implement Stage 3, preserving the deterministic verifier as the authority. In connected mode, publish/query bounded synthetic evidence manifests through the actual Zetaris deployment. Useful tables include device_inventory, submission_versions, xml_facts, media_references, file_hashes and attempt_logs. Raw source files remain private evidence objects with hashes. Query by run/source/version scope; do not assume LIMIT guarantees a cheap full-file scan. A documented initial implementation may normalize small exports to CSV/S3; label that architecture honestly rather than claiming heterogeneous in-place federation.

The normal live investigation path must use Zetaris query results to obtain the evidence it reasons over. Do not run all meaningful joins locally and send finished conclusions to Zetaris as a ceremonial log. Store source/query provenance and support resolving every finding to its actual rows and source files.

Integrate the pinned Meterless World Model through its real reference/read surface. Entities include device snapshot, form version, submission version, attachment, observation, hypothesis and recovery operation. Enforce provenance, stable identity, idempotent ingestion and append-only revision history. Preserve rejected hypotheses with their evidence. Read the graph to select unresolved work; do not merely write a graph after finishing. Persist/rebuild only through capabilities actually implemented and tested. Include an acceptance test showing ingestion idempotency, a revised hypothesis retaining its previous evidence, and an actual next-action change after new evidence arrives.

Implement a bounded investigator/reviewer loop through Nightshift. The code-owned tools may query evidence, fetch scoped XML/history/media, compare payloads and draft a recovery plan. Validate tool parameters and all action JSON; imported text is data, not instructions. Maximum 12 investigation steps, two critique rounds and a configurable 300-second wall-time budget initially. Make limits visible and cancel cleanly. Use provider-reported usage where available; label any estimate.

The reviewer must trigger additional evidence or revision, not just approve a summary. Required demonstration: an initial missing-data hypothesis is rejected when raw server XML shows the repeated answers; the action changes to export guidance rather than resubmission. A second case must preserve an unresolved conflict. Models cannot alter verifier outputs or add facts without evidence.

For the NVIDIA case, route a real available Nemotron model through Nightshift and record actual serving-model identity. Do not hardcode a guessed model ID or relabel meterless/auto as a model. If unavailable, mark that award path blocked; keep honest sponsor-status reporting. Log run/tool/query IDs, timing, evidence hashes, hypotheses, critique, decision changes and sanitized model metadata in JSONL. Keep live/replay/sample traces distinct. Test provider failure and confirm it does not silently substitute sample evidence.

Acceptance: a connected synthetic case uses actual Zetaris evidence, World Model read/write behavior and Nightshift inference; engine tests pass; the critic causes an observable branch; findings remain independently verifiable. Report incomplete live checks accurately.
```

## Prompt 4 — Implement recovery and prove it on a real test server

```text
Implement Stage 4. Use official ODK submission/version/attachment documentation and the packet's recovery contract. Support a narrow missing-submission/missing-media path in a dedicated synthetic test project. Stage and download a recovery bundle containing untouched required files, an operation manifest, target identities, source hashes, evidence and instructions. Keep conflicts and unsupported historical writes out of automatic application.

Add explicit plan review and an Apply action bound to the configured target environment. Re-read target preconditions before each write, verify the expected version, preserve original identifiers, serialize per-submission work and handle uncertainty through readback before retry. Never respond to 409 by manufacturing an instance ID. No clearing attachments, deleting submissions or overwriting conflicting answers as a convenience.

Persist attempt state so a server/process restart can resume safely. Treat POST success as an attempt result, not preservation proof. After applying, fetch fresh original XML, version metadata and attachment bytes, and run the same comparator again. Record which deficits disappeared, which remain and which new conflicts appeared. Repeated Apply must not create another submission or repeat completed work unnecessarily.

Acceptance tests must cover a crash/timeout after a successful upload but before local acknowledgement, a version change between plan and apply, an existing conflicting record, a missing media file, and an already-completed operation. Run at least one genuine synthetic recovery against real ODK Central and retain a redacted receipt of before state, documented requests, after readback and comparison. A fixture server or second synthetic export can exercise offline behavior but cannot substitute for this live acceptance claim.

Use these historical upstream regressions as semantic controls, not claims about current unfixed defects: two references to one filename require one accessible slot; two different filenames with identical bytes require both accessible slots. Construct synthetic equivalents and cite the upstream fixes. Do not import unlicensed community audio.

Keep original sources unchanged and verify their hashes after all operations. If a real test server cannot run, finish local work and document the precise remaining blocker; do not say recovery is end-to-end verified.
```

## Prompt 5 — Build the usable application around the working flow

```text
Implement Stage 5 as real UI connected to the existing API; no screenshot-as-interface or hardcoded successful run. Use semantic HTML and plain language. Build / as the product introduction, /app as import/check flow, /runs/[id] as the saved investigation, and an evidence/report view within the run. Adapt route conventions to the existing framework.

The four-step flow is Add exports → Check copies → Review gaps → Verify recovery. Support device-file upload and expected-device roster, scoped server snapshot/test connection, visible validation limits, a clear run action and cancellable progress from actual events. Show Sample or Connected mode prominently. Replays must say Replay and identify the captured run. Do not put secrets, tokens or credentials in browser state/URLs/localStorage.

Results should lead with a sentence a nontechnical coordinator can understand, then affected records and the useful action. Use labels such as 'Photo missing on server', 'Original retained in history', 'Answers present; export omitted them', and 'Could not verify'. Separate investigation completion, source coverage and recovery status. Avoid an unqualified 'safe to wipe' badge. Counts must come from actual run results.

Each finding opens its source files, meaningful XML path/repeat index, before/after values, attachment reference and evidence receipt. Keep SQL/model/provider diagnostics in a secondary Evidence/Technical details view. Show hashes in a readable abbreviated form with copy/full-detail access. Allow downloading findings JSON, a plain-language report, traces with redaction and the staged recovery bundle.

Recovery review displays the exact configured project, operations, unchanged source files, conflicts/unknowns and preconditions. Apply is available only for supported reviewed plans in the configured test environment. After a timeout/reload, restore saved state and read the server before offering a retry. No progress percentages unless measured; no fixed delay used to simulate reasoning.

Provide useful empty, validating, queued, running, waiting-for-information, cancelled, failed, complete-with-gaps and verified states. Make forms, drawers, menus and dialogs keyboard-operable with focus management. Use text plus icons for states, never color alone. Mobile results use readable stacked summaries and an evidence drawer; preserve table detail through labelled scrolling or an accessible alternate layout. Verify persistence and refresh/back-navigation behavior through a full browser run.

Acceptance: a user can open a sample, run the actual offline comparator, inspect a finding, prepare the permitted recovery and verify its result in the appropriate mode without a developer editing JSON. Connected behavior must use the existing integration and recovery code.
```

## Prompt 6 — Give it the Stripr-level finish, with substantially more motion

```text
Implement Stage 6 without changing preservation, recovery or integration semantics. First inspect https://www.stripr.xyz/ in a browser if available, including its landing page and /app, and inspect our current UI at desktop and mobile sizes. If browsing is unavailable, use the recorded observations below and do not pretend you viewed it. Build an original LastCopy composition using the reference's visual discipline, not its brand, copy, code or finance imagery.

Recorded reference observations from October 23, 2026: near-black green-tinted background; subtle grid and teal atmosphere; Fraunces serif display headings paired with Figtree body text; small uppercase mint labels; white headings with restrained blue-to-mint emphasis; large two-column hero; glass-like dark panels with fine borders; bright mint primary button and quieter secondary button; code-built connected diagram; generous spacing; explanatory product sections, calculator, technical evidence, FAQ and consistent footer. The measured desktop h1 used Fraunces at 56px with 58.8px line height; body used Figtree. Treat those as observations, not dimensions to copy blindly.

LastCopy design direction: dark ink/green base, warm off-white typography, sea-glass mint for verified states, cool blue for evidence and amber for unresolved/missing work. Suggested starting tokens are #060C0C, #0D1818, #EAF5F0, #42DBB3, #73BDF4 and #F2B66D; verify real contrast, especially small muted text. Use Fraunces for short display headings and a legible wide Figtree or compatible existing sans for body/UI. Self-host downloaded open-license fonts with their licenses, subset sensibly and use font-display:swap. Reuse existing typography if changing it would damage an established design system.

Create an original code-built document/checkmark identity and favicon using simple SVG geometry. Use a consistent icon set such as existing Lucide components. No emoji UI, AI image generation, stock AI art, generic glowing orb, giant background video or mockup image standing in for real controls. A photo is optional: only download a verifiably licensed real image when it helps explain fieldwork, optimize and store it locally, and record attribution in docs/ASSET_SOURCES.md. Do not scrape Stripr's images or hotlink external assets.

Landing composition:
- A compact clear navigation and an immediately understandable hero. Suggested headline: 'Bring every record home.' Supporting copy: 'Check that your field forms, answers and photos reached the server. Recover what is missing. Verify the result.' Main CTA 'Check a sample'; secondary 'Check my exports'. Both must work.
- A substantial original HTML/CSS/SVG scene showing field-device exports, an investigation checkpoint and checked server copies. An amber document remains unresolved until an illustrative recovery step. Label illustrative data; do not imply this animation is a live recovery. An actual sample run can separately drive a result panel from real API events.
- A short concrete problem story, three-step product explanation, an interactive actual sample, an evidence/recovery walkthrough and a concise limitations/FAQ section. Avoid a long wall of technical instructions or repeated generic feature-card grids. Keep detailed sponsor architecture behind a secondary technical link.
- A composed footer with working links. No fabricated customer logos, testimonials, adoption statistics, uptime, '100% recovery' claims or sponsor endorsements.

More motion is a requirement. Use CSS, native observers and at most one React motion library already present or justified. Implement a coordinated hero entrance, a restrained moving document path, scroll-linked storytelling, section reveals, hover/press/focus states, animated sample-case transitions, evidence drawer transitions and real recovery-state transitions. Suggested motion scale: 160–220ms controls; 450–650ms entrances; 12–20px reveal travel; 50–70ms item stagger with short groups. Fine-pointer parallax can move layers by at most about 8px. Keep text stable enough to read. Do not add constant spinning icons or fake activity.

Preserve native scrolling. No scroll hijacking, cursor replacement, excessive pinning, flashing effects or animation that delays the primary action. Prefer transform/opacity; avoid animating layout and large blur filters. Ambient loops pause when offscreen or the tab is hidden. On narrow/touch screens replace complex choreography with a clear stacked scene and restrained transitions. prefers-reduced-motion disables parallax, looping travel and scroll choreography while keeping every state understandable. Loading and verification changes must reflect real events, never ornamental success.

Apply the same finish to the actual app: deliberate hierarchy, generous readable spacing, restrained glass, beautiful buttons with hover/active/loading/disabled/focus states, clear upload targets, readable run results and polished mobile drawers. Glass is a surface treatment, not low contrast across every panel. Avoid a landing-page-only redesign.

Acceptance: inspect and correct screenshots at 360, 390, 768, 1280 and 1440px; check 200% zoom and reduced motion. No clipped navigation, broken dropdowns, duplicate headers, horizontal page overflow, obscured controls or invisible focus. Keep visual regression evidence and record what was actually checked. Preserve a useful static first frame and responsive inputs while animations run.
```

## Prompt 7 — Verify the complete product and prepare the submission

```text
Implement Stage 7. Audit the actual product against PRODUCT_SPEC.md and the packet. Fix material failures before adding scope. Run the appropriate core tests, engine conformance, API contracts, browser flows, production build and dependency/security checks. Triage issues instead of running destructive automatic dependency upgrades.

Verify these complete paths:
1. Offline: external providers stopped and external network disabled, with local app services running. All bundled sample cases compare real fixture contents, display honest modes, retain evidence and produce downloadable reports/bundles. Self-hosted assets/fonts must work.
2. Connected investigation: real Zetaris evidence query, a World Model read that affects the next action, real Nightshift inference and an investigator/reviewer revision. Keep actual model identity and sanitized source/query receipts. Confirm that sponsor outage never produces a fake connected success.
3. Real test-server recovery: capture missing data before, review/apply a bounded plan, fetch fresh XML/media after and independently verify preservation. Repeat after a simulated lost acknowledgement/restart and confirm no duplicate creation or conflict overwrite.
4. Correct controls: legitimate historical edit, shared media reference, different filenames with equal bytes, complete raw XML but incomplete export, and missing evidence coverage. Confirm neither false recovery nor false assurance.
5. Browser usability: first-run empty state → sample/import → run → evidence → recovery review → verification → saved report; reload/back navigation, error/cancel handling, keyboard-only use, 200% zoom, reduced motion and the stated responsive widths.

Measure the production build, not the dev server. Target mobile Lighthouse performance at least 90 and accessibility/best-practices/SEO at least 95 where applicable on public routes, CLS <=0.1 and lab LCP <=2.5s under a documented repeatable mobile profile. These are goals, not fabricated guarantees. Fix unnecessary JS, oversized images/fonts, layout shifts and animation jank; lazy-load noncritical motion and evidence viewers. Lighthouse alone does not establish field INP/Core Web Vitals. Report device/throttling/mode, actual scores and any unmet targets honestly. Interaction responsiveness and working workflows take priority over inflating a score.

Prepare README setup for Windows and the actual runtime, API/CLI examples, .env.example, Docker instructions, sample IO, architecture/sponsor explanation, licensing/attribution, a limitations document, redacted traces, a 1–4 minute demo script and a concise pitch-deck outline. Include metadata only against the correct current Open Agent template. Explain existing upstream code and distinguish new work. Preserve no real field records, private credentials or community-user recordings in the public-repository-ready output.

The demo should show a real gap, an evidence-led hypothesis revision, a permitted recovery, fresh readback and a correct control. Separate Sample, Replay and Connected on screen. Do not call a saved capture live or a planned test completed. No predicted win percentage or invented benchmark superiority.

Recheck official organizer updates and report any material rule conflict. End with a short readiness report listing what works, actual checks/results, unresolved limitations, files for the user to review and exact launch commands. Prepare deployment instructions but do not publish, change repository visibility or submit automatically.
```

## Primary references for Codex

- Event and tracks: https://hackathon.genai.works/event/open-agent-hackathon-2026
- Authenticated resource hub: https://hackathon.genai.works/resources
- Zetaris getting started and recipes: https://github.com/zetaris/getting-started
- Zetaris SQL companion: https://github.com/zetaris/getting-started/blob/main/docs/guides/zetaris-lightning-sql-companion.md
- Zetaris working small-file recipe: https://github.com/zetaris/getting-started/blob/main/open_data/parquet_csv/HOWTO.md
- Meterless World Model specification/reference: https://github.com/Meterless/Meterless/tree/main/engines/world-model
- Nightshift provider guide: https://github.com/Meterless/Meterless/blob/main/docs/agent-ready/add-meterless-provider.md
- Nightshift hotspot: https://github.com/Meterless/Meterless/blob/main/docs/products/nightshift/hotspot.md
- ODK submission/version/media API: https://docs.getodk.org/central-api-submission-management/
- ODK native submission protocol: https://docs.getodk.org/central-api-openrosa-endpoints/
- ODK test deployment instructions: https://docs.getodk.org/central-install/
- Historical repeated-reference fix/test: https://github.com/getodk/central-backend/commit/1ef57ebc98ac12d1921bcd71840ee435ebcc4354
- Historical identical-bytes attachment issue: https://github.com/getodk/central-backend/issues/299
- July 2026 queued-report incident: https://community.kobotoolbox.org/t/database-error-and-error-401-at-data-entry/76518
- Historical repeated-group/export incident: https://forum.getodk.org/t/data-from-question-groups-lost-when-submitting-finalized-forms/36768
- Native missing-media handling: https://docs.surveycto.com/03-collecting-data/01-mobile-data-collection/03a.incomplete-submissions.html
- Visual reference inspected: https://www.stripr.xyz/ and https://www.stripr.xyz/app

These links establish documentation, historical problems and visual reference. They are not evidence that LastCopy is implemented, benchmarked, uniquely original, production-ready or guaranteed to win. Inspect pinned source licenses and current provider interfaces before copying code or executing integrations.
