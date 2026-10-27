# Tablet clearance sheet: `sample-stranded-41`

**Question:** The submission count matches what we expected. Is anything still stuck on the device?  
**Mode:** sample · evidence: local-sql · judgement: offline-policy · verdicts: deterministic code  
**Summary:** 0 safe to wipe · 1 recover first · 0 hold

| Tablet | Decision | Action | Items still only on the tablet / to review | Certificate |
|---|---|---|---|---|
| `device-41` | 🟧 RECOVER FIRST | Do not reset. Upload the items listed, then re-run the check | whole record `uuid:41-b`; whole record `uuid:41-c` | `a3f56da95a58806a` |

## Why, in plain language

- **device-41:** RECOVER_FIRST: device-41 still holds the only copy of data the server is missing. finding-2: the whole record for uuid:41-b is not on the server. finding-3: the whole record for uuid:41-c is not on the server.  _(written by offline-policy; citations checked)_

## Sign-off

| Tablet | Reset by | Date | Signature |
|---|---|---|---|

Verify every certificate independently: `python -m scripts.verify_certificate <this run's output JSON> --archive <export.zip> ...`

_A certificate proves which bytes were compared under rule lastcopy-wipe-gate/1. It covers only the exports supplied and does not prove the answers are true._

