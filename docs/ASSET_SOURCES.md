# Assets and upstream provenance

No image-generation tool was used. No raster illustrations, video, stock photos,
community recordings or remote fonts are included. UI is plain HTML/CSS. Fixture
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

LastCopy source is MIT licensed; third-party files keep their own licenses.
