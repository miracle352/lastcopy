# Tablet clearance sheet: `sample-export-41`

**Question:** The server spreadsheet is missing answers from this tablet. Did we lose data?  
**Mode:** sample · evidence: local-sql · judgement: offline-policy · verdicts: deterministic code  
**Summary:** 1 safe to wipe · 0 recover first · 0 hold

| Tablet | Decision | Action | Items still only on the tablet / to review | Certificate |
|---|---|---|---|---|
| `device-41` | ✅ SAFE TO WIPE | Reset the tablet | - | `8af018d288dd5baa` |

## Why, in plain language

- **device-41:** SAFE_TO_WIPE: every completed record and file on device-41 was matched byte-for-byte on the server. The spreadsheet export omits some repeated answers, but the raw server XML holds all of them. 1 completed record matched the server byte-for-byte, including every referenced file.  _(written by offline-policy; citations checked)_

## Sign-off

| Tablet | Reset by | Date | Signature |
|---|---|---|---|
| `device-41` | | | |

Verify every certificate independently: `python -m scripts.verify_certificate <this run's output JSON> --archive <export.zip> ...`

_A certificate proves which bytes were compared under rule lastcopy-wipe-gate/1. It covers only the exports supplied and does not prove the answers are true._
