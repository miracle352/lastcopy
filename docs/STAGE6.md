# Stage 6 presentation

The visual metaphor is a chain of evidence: original device documents pass an
XML/version/bytes checkpoint before a checked readback. An amber attachment
remains unresolved until a clearly labelled illustrative step is requested.
The illustration makes no network request and is independent of the actual
sample workbench. That workbench starts the existing sample API job and displays
only saved comparator results and real events.

## System

Dark ink `#060C0C`, surface `#0D1818`, off-white `#EAF5F0`, verified mint
`#42DBB3`, evidence blue `#73BDF4`, unresolved amber `#F2B66D`. Muted text is
`#A8BDB6` or `#849C94`; opaque semantic pairs have executable WCAG calculations.
Fraunces is restricted to display headings, Figtree to body/controls. Local WOFF2
files total 63,244 bytes and use `font-display:swap`; missing glyphs fall back to
system fonts. Exact pinned font sources, transformations and licenses live with
the assets and in `ASSET_SOURCES.md`.

The header, footer and navigation are shared. App controls keep their native
semantics; keyboard focus has a visible outline. Narrow layouts stack status
summaries and recovery review; evidence remains a native modal with labelled
scrolling, Escape and focus return. No new runtime motion dependency was added.

Controls transition around 180ms, entrances around 560ms with 60ms short-group
stagger. Transform/opacity do the animated work. Fine-pointer scene parallax is
bounded to 4px per axis; touch/narrow layouts disable it. IntersectionObserver
pauses document loops outside the viewport; visibilitychange pauses them while
the tab is hidden. Native scrolling drives a small story rule, without pinning
or interception. New route elements are observed after navigation.

Reduced motion disables animation/transition, travel, parallax and scroll
choreography. Content is visible in the static first frame and without JS.
Sample-case, drawer and recovery-state transitions never determine completion
or preservation status. No percentages, fake progress or model/provider logs
were introduced.

## Verification

With the existing private API configured on port 8000:

```powershell
npm run build
npm run start
# In a second terminal, from the repository root:
npm run typecheck
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe scripts/verify_stage6_contrast.py
node scripts/verify_stage6_browser.mjs
```

The browser runner uses the installed Playwright Chromium, blocks non-loopback
origins, performs three real offline comparisons and sample recovery readback,
and retains sanitized API paths. It never applies connected recovery. It checks
360/390/768/1280/1440px for landing, imports, saved run and evidence modal;
reduced motion; no-JS first frame; 200% CSS zoom/reflow; focus, dropdown, FAQ,
refresh and navigation. Results, screenshot hashes and immediate repeated-capture
comparisons are in `verification/stage6/browser.json`. PNGs alongside it provide
the visual baselines. Full-height captures and original before screenshots are
private under `private/stage6/` and are not product assets.

CSS zoom is not a claim of browser-menu zoom equivalence. Chromium checks and
visual review are not cross-browser or screen-reader certification. Contrast
calculations cover listed opaque semantic text/surface pairs, not every possible
composite pixel. The Vercel skeleton still has no private API deployment; it
shows the existing actionable unavailable state when an API is required.

`scripts/prepare_stage6_fonts.py` is an optional asset rebuild tool requiring
fonttools 4.61.1 with WOFF support and network access to pinned official sources.
It is not needed at application runtime or during normal builds.
