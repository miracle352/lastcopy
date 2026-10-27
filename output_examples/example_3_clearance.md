# Tablet clearance sheet: `sample-media-41`

**Question:** Every record shows as received. Can we reset this tablet?  
**Mode:** sample · evidence: local-sql · judgement: offline-policy · verdicts: deterministic code  
**Summary:** 0 safe to wipe · 1 recover first · 0 hold

| Tablet | Decision | Action | Items still only on the tablet / to review | Certificate |
|---|---|---|---|---|
| `device-41` | 🟧 RECOVER FIRST | Do not reset. Upload the items listed, then re-run the check | file b.bin of `uuid:41-a` | `314d2a56aec3499c` |

## Why, in plain language

- **device-41:** RECOVER_FIRST: device-41 still holds the only copy of data the server is missing. finding-1: the file b.bin for uuid:41-a is not on the server.  _(written by offline-policy; citations checked)_

## Sign-off

| Tablet | Reset by | Date | Signature |
|---|---|---|---|

Verify every certificate independently: `python -m scripts.verify_certificate <this run's output JSON> --archive <export.zip> ...`

_A certificate proves which bytes were compared under rule lastcopy-wipe-gate/1. It covers only the exports supplied and does not prove the answers are true._
