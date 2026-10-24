# Assets and upstream provenance

No image-generation tool was used. No raster illustrations, video, stock photos,
community recordings or browser-loaded remote fonts are included. UI visuals are
original HTML/CSS/SVG. Browser verification screenshots are evidence, not product
artwork. Fixture
media is original synthetic UTF-8 text from `scripts/build_fixture.py`; it contains
no field records or personal data. It is not a photo or an invented field observation.

The Meterless World Model reference is upstream Apache-2.0 code:
https://github.com/Meterless/Meterless/tree/1742dec56a66e58eef9dda2d2b865823758ca8cd/engines/world-model

Only reference source/test/scripts/config, conformance, docs, the specification
and license are included. No upstream images or prebuilt HTML are included.
`third_party/world-model/LICENSE` retains the full license. `UPSTREAM.json` pins
the commit and file hashes. `SPEC.md` is upstream AGENTS.md, renamed, otherwise
unchanged. All other copied files are unchanged. LastCopy's bridge is new work.
Root dependencies and locks remain separately licensed by their publishers.

## Stage 6 fonts and original geometry

Fraunces: Copyright 2018 The Fraunces Project Authors,
https://github.com/undercasetype/Fraunces .
Figtree: Copyright 2022 The Figtree Project Authors,
https://github.com/erikdkennedy/figtree .
Both are distributed under the SIL Open Font License 1.1. Exact license copies
are in `web/public/fonts/{fraunces,figtree}-OFL.txt`.

Downloaded from the official Google Fonts source, pinned commit
`e7db6ca603fd4862010383ff17ffd6cc4ffac1c0`:
https://github.com/google/fonts/tree/e7db6ca603fd4862010383ff17ffd6cc4ffac1c0/ofl/fraunces
and
https://github.com/google/fonts/tree/e7db6ca603fd4862010383ff17ffd6cc4ffac1c0/ofl/figtree .
`web/public/fonts/sources.json` records exact source URLs, source/output SHA-256,
axis choices and byte sizes. `scripts/prepare_stage6_fonts.py` builds Latin/Latin
extended + UI punctuation WOFF2 subsets with fonttools 4.61.1. Fraunces is instanced
at opsz 64, SOFT 50 and WONK 1, with weights 400–700 retained. Figtree retains
weights 400–700. Missing glyphs use system fallback; original source XML is never
rewritten. Combined WOFF2 bytes: 63,244. CSS uses font-display:swap. No browser
Google Fonts request or build-time Next font-service download is required.

The LastCopy document/checkmark identity, SVG favicon and small consistent outline
icons are original code geometry in `web/app/icons.tsx` and `web/app/icon.svg`.
The chain-of-evidence scene is HTML/CSS/SVG in `record-scene.tsx`; no external
illustrations, logos, stock assets or photo downloads are used.

Stripr (https://www.stripr.xyz/ and /app) was inspected in the browser on
2026-10-24 as a visual-discipline reference only. No Stripr assets, brand marks,
financial imagery, code or distinctive composition were imported. LastCopy uses
its own chain-of-custody narrative, source documents, evidence checkpoint and
readback vocabulary.

LastCopy source is MIT licensed; third-party files keep their own licenses.
