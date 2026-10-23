# Tested compatibility, not a universal export promise

Stage 1 format pin: **LastCopy device-manifest schema 1 / native-path ZIP v1**.
The original representative archive remains authored synthetic material with
unknown Collect version. A second fixture now records an actual **ODK Collect
v2026.3.5 (versionCode 5551)** run on the dedicated AOSP Android 11 / API 30
x86_64 emulator, revision 11, using Android Emulator 37.2.12 and platform-tools
37.0.1. User explicitly requested emulator use. This is synthetic test data
entered and finalized in the actual app, then copied through documented `adb`
transfer; it is not a physical-phone or historical-version compatibility claim.

`fixtures/collect-v2026.3.5/device.zip` preserves original project-relative XForm,
instance XML, Collect-renamed text attachment, last-saved XML and form/instance
metadata databases. The original full project capture remains private. LastCopy's
manifest and ZIP were added by code without rewriting the copied native bytes.
Completion comes from the selected `instances` database row (`status=complete`,
non-null finalizationDate), corroborated by the Finalize action and Ready to send
count. Device identity is a coordinator label. No submission was sent to Central.
Receipt: `verification/collect-export-2026-10-23.json`.

The first authored form inherited the XForms namespace in its data template;
Collect saved its instance without that namespace. LastCopy correctly surfaced
an unmatched-form limitation. That private capture remains unchanged. A corrected
form with explicit empty data namespace and a new form ID was filled and finalized
separately. The regression suite preserves the mismatch as a negative control;
no namespace stripping or relaxed matching was added to the inventory.

The normalizer accepts an unencrypted ZIP with root `device-manifest.json`,
explicit instance XML filenames and matching original XForms. Project directories
are retained. Instance XML identity comes from the root `id`, `version`,
`meta/instanceID` and `meta/deprecatedID`; an incomplete edit chain remains limited.
Completion and device labels require provenance. Draft/unknown entries remain in
inventory and are excluded from automatic submission. Missing source files cannot
be reconstructed. First-release binary binds supported by this inventory use
absolute unprefixed nodeset paths; complex XPath becomes a limitation.

Destination is an explicit RunManifest connection/project/form mapping, separate
from the device manifest. `validate_run_import` checks mapping and roster scope.
No filename-based destination inference exists.

Raw server snapshot contract: `SourceSnapshot` schema 1, `kind=central_raw`,
explicit project/forms, capture time, completeness, versions, media, request
receipts and limitations. The envelope `server-snapshot.json` is external to its
hashed `server-payload.zip` so the manifest hash is not self-referential.
`scripts.validate_snapshot` checks payload, identity and receipt references.
The representative server pack is **synthetic**, generated locally, not obtained
from Central. The real read-only exporter is future work; synthetic LOCAL receipts
must never be passed off as HTTP evidence. A CSV is only a diagnostic view.

**Central v2026.3.1 has been live-tested for this synthetic read-only path.** The
official checkout is pinned to `7d6de621955c5bb6a68e098ca10c9cbb92285cdf`;
the served `/version.txt` contained that commit before local seeding. Authentication,
project metadata, exact submission version XML and actual attachment bytes passed
the connected smoke on 2026-10-23. See LOCAL_SETUP.md and the committed sanitized
receipt. The separate Collect capture above establishes only its documented native-path
export compatibility. Historical replacement and automated recovery remain untested.

Stage 2 XML policy: compare expanded names, attributes and ordered child/repeat
occurrences. Ignore attribute order and prefix spelling. Formatting-only whitespace
between element-only children may be ignored unless `xml:space=preserve` applies;
leaf text, mixed-content text/tails, Unicode and leading zeros must remain exact.
No blanket ignorable-field list. That comparator and its tests are not Stage 1 work.

Archive defaults: 10 MiB compressed upload, 32 MiB total uncompressed, 500 entries;
XML: 1 MiB per file, depth 64, 10,000 nodes, 524,288 text characters. Environment
overrides may lower limits, not exceed those hard ceilings. XML DTD/entities,
ZIP traversal, symlinks, encryption and duplicate normalized paths are rejected.
No files are extracted and original archives remain untouched.
