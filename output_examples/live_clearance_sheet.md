# Tablet clearance sheet: `sample-fleet-2026`

**Question:** Which of our five survey tablets are safe to wipe before the next round?  
**Mode:** connected · evidence: zetaris · judgement: nvidia/nemotron-3.5-lightning-30b-a3b · verdicts: deterministic code  
**Summary:** 1 safe to wipe · 2 recover first · 2 hold

| Tablet | Decision | Action | Items still only on the tablet / to review | Certificate |
|---|---|---|---|---|
| `tablet-01` | ✅ SAFE TO WIPE | Reset the tablet | - | `3817eee857f42fab` |
| `tablet-02` | 🟧 RECOVER FIRST | Do not reset. Upload the items listed, then re-run the check | file b.bin of `uuid:fleet-02-a` | `010021268577c77a` |
| `tablet-03` | 🟧 RECOVER FIRST | Do not reset. Upload the items listed, then re-run the check | whole record `uuid:fleet-03-b` | `d9283680e82a1fde` |
| `tablet-04` | ⛔ HOLD | Do not reset. A data manager must review first | conflicting answers in `uuid:fleet-04-a` | `2eccf72550b2e198` |
| `tablet-05` | ⛔ HOLD | Do not reset. A data manager must review first | no export received from this tablet | `231f4d0014245f30` |

## Why, in plain language

- **tablet-01:** SAFE_TO_WIPE: The export is view-only, but 2 completed records matched the server byte-for-byte, including every referenced file.  _(written by nvidia/nemotron-3.5-lightning-30b-a3b; citations checked)_
- **tablet-02:** RECOVER_FIRST: finding-3: the file b.bin for uuid:fleet-02-a is not on the server. Automatic recovery is not permitted, so recover it with a reviewed upload.  _(written by nvidia/nemotron-3.5-lightning-30b-a3b; citations checked)_
- **tablet-03:** RECOVER_FIRST: finding-5: the whole record for uuid:fleet-03-b is not on the server. Automatic recovery is not permitted, so recover it with a reviewed upload.  _(written by nvidia/nemotron-3.5-lightning-30b-a3b; citations checked)_
- **tablet-04:** HOLD: finding-6: the server copy of uuid:fleet-04-a has different answers; a person must choose.  _(written by nvidia/nemotron-3.5-lightning-30b-a3b; citations checked)_
- **tablet-05:** HOLD: No export was received from this device, so nothing on it has been checked.  _(written by nvidia/nemotron-3.5-lightning-30b-a3b; citations checked)_

## Sign-off

| Tablet | Reset by | Date | Signature |
|---|---|---|---|
| `tablet-01` | | | |

Verify every certificate independently: `python -m scripts.verify_certificate <this run's output JSON> --archive <export.zip> ...`

_A certificate proves which bytes were compared under rule lastcopy-wipe-gate/1. It covers only the exports supplied and does not prove the answers are true._
