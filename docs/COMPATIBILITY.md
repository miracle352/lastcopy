# Tested compatibility, not a universal export promise

Stage 1 format pin: **LastCopy device-manifest schema 1 / native-path ZIP v1**.
The committed representative archive is authored synthetic test material. It has
not been exported from a real ODK Collect installation. Its `collector_version`
is explicitly `unknown`; no Collect application version is claimed tested.

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
receipt. This does not establish real Collect export compatibility, historical
replacement behavior or automated recovery support.

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
