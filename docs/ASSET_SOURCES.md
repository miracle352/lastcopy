# Assets and upstream provenance

## 27 October runtime maintenance

The separate deployed Central stack remains upstream ODK Central v2026.3.1
(`7d6de621955c5bb6a68e098ca10c9cbb92285cdf`), with backend source
`de0d2a07fd7c9ff698cbc312e550dd40ff058340`. Its Apache-2.0 notices and source
licenses remain in the runtime. New first-party Docker layers apply stable OS
updates, same-major Node security patches and four explicit dependency-lock entries;
they do not claim authorship of Central or Enketo.

The pyxform-http v4.5.0 image retains its original application and upstream licenses.
The only wrapper source change is flushing the synthetic XLSX write buffer before
conversion. The original image and pinned source are documented at
[pyxform-http](https://github.com/getodk/pyxform-http/tree/v4.5.0).
The new `fixtures/stack-security/minimal.xlsx` is authored synthetic CC0 input,
not downloaded field data. See `STACK_SECURITY_REVIEW.md` for actual changes,
tests, exact image receipts and remaining upstream dependency advisories.

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

## Stage 7 display-font reduction

The same pinned official source and licenses were rebuilt with Fraunces fixed at
the actual display weight 450 (opsz 64, SOFT 50, WONK 1). Its WOFF2 is now 22,948
bytes; Figtree is unchanged at 20,352 bytes, for 43,300 combined bytes. Current
hashes and axes are in `web/public/fonts/sources.json`; the Stage 6 values above
describe that earlier verification. No source evidence files were changed.
## Water-point pilot media

The native Collect pilot uses an original 32×32 checkerboard created by
deterministic PNG code. Collect's saved attachment bytes are retained in the
synthetic `fixtures/water-point-collect-v2026.3.5/device.zip`. This is test media,
not a field photograph. No AI-generated imagery or community recording was used.

## Public beta interface

The account copy-path diagram, paper geometry and glass surfaces are original
HTML/CSS/SVG in `proof-route.tsx`, `auth-shell.tsx` and `atelier.css`. Existing
licensed local Fraunces/Figtree files and the existing icon geometry are reused.
The labelled illustration does not depict a live recovery. No new raster asset,
stock image, image-generation service or animation-library dependency was added.
# Scroll-story follow-up, 26 October 2026

The field-record/water-point SVG, transfer path and all scroll transforms are
original project code. No AI-generated image, downloaded photo or new font was
added. Existing self-hosted Fraunces/Figtree files and their licenses are reused.
The 21st plugin supplied metadata-only inspiration for Reading Text Reveal,
Cinematic Product Scroll Section and Segmented Control; no component source or
asset was retrieved. Stripr's public landing page was re-inspected in a browser
for visual discipline, with no brand, copy, code or images copied.

## Submission review assets — 26 October 2026

The deck and demo use actual LastCopy screenshots and a browser recording of
our synthetic cases. No generated imagery, stock imagery, community audio or
external pictures were added. The PPTX references installed Arial/Georgia; their
font binaries are not distributed. The app retains its existing local OFL fonts.
The recording is silent with authored captions; it contains no AI voice.

## Narrated film follow-up — 26 October 2026

`submission/LastCopy-demo-narrated.mp4` is a separate 2m38s film. The owner
explicitly chose spoken narration with captions. Speech was synthesized locally
using Kokoro `af_heart` at speed 0.95 through Hyperframes and kokoro-onnx 0.4.9.
It is a synthetic voice, not a community recording or an impersonation.
[kokoro-onnx code is MIT licensed](https://github.com/thewh1teagle/kokoro-onnx/blob/main/LICENSE);
[Kokoro-82M weights are Apache-2.0 licensed](https://huggingface.co/hexgrad/Kokoro-82M?inference_provider=deepinfra).
Model/voice weights and authoring-tool dependencies are not packaged in LastCopy.

The film uses actual LastCopy browser recordings and original HTML/SVG/GSAP
motion for the opening problem illustration. Replay footage shows actual saved
synthetic query rows and graph history; the new recovery footage shows actual
Central requests in dedicated test project 2. No AI-generated imagery, stock
art, downloaded community audio, fabricated SQL logs or fabricated model output
was used. Brag and Cinetic guided the edit. Existing OFL Figtree/Fraunces files
were reused locally; the caption font was converted locally from the same
licensed Figtree file. No font binaries are redistributed outside those licenses.
