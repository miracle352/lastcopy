# Synthetic XLSForm runtime control

`minimal.xlsx` is an independently authored deterministic XLSForm containing a
single text question, `condition`, and the form ID `lastcopy_runtime_control`.
It contains no field record, personal information, photo or audio. ZIP entries
use the fixed 1980-01-01 timestamp; strings and expected identity were specified
by hand. SHA-256:
`aea70b3daa3de8d5570a87d86d9a558b5bd239633faefdf33e881489396b107f`.

The project authors dedicate this synthetic fixture to CC0-1.0. Its intentionally
small size exercises the upstream HTTP wrapper reopening a still-buffered file.
The expected outcome is valid conversion with Java validation; a malformed
non-workbook control must return 400. Neither control creates a Central form.
