# Backup activation and submission checks — 26 October 2026

The owner explicitly requested activation after reviewing the excluded-key
limitation. The existing AWS daily service now uses `--include-enketo`.
Only Enketo's Redis main store and its three generated keys were added;
provider credentials and the application environment remain excluded.

## Actual acceptance

- The real systemd job completed successfully, its timer is enabled, and the
  encrypted 5.55 MB backup was uploaded to the existing private S3 prefix.
  Full ciphertext download/readback matched SHA-256. Ten application databases,
  Central PostgreSQL and Enketo link state were included.
- A subsequent encrypted backup was downloaded from S3 and authenticated/decrypted
  on AWS using a temporary additional recipient. The owner's original recipient
  remains valid. The drill key and scratch plaintext were removed afterward;
  no plaintext Enketo key reached this PC.
- All **10 SQLite databases** passed integrity checks; **47 input hashes** and
  **76 artifact hashes** matched. Central's submissions, version/XML definitions
  and blobs matched an isolated restored database. The scratch database was
  removed; there were **zero live database writes**.
- Enketo RDB loaded in a network-disabled scratch Redis with no published port.
  Typed content and absolute expiry metadata matched live state; all **three
  generated key files** matched their retained bytes. No public Web Form link
  browser claim is made by that component check.
- No older backup, original source or live volume was deleted. The existing
  512 MiB upload guard and no-deletion policy remain; the prepared 30-day expiry
  policy remains inactive. The guard is not an AWS billing guarantee.

## Failed control and correction

The first actual drill failed closed: Redis `DUMP` serialization differed after
restore although the underlying hash contents were equal. A real synthetic
control reproduced this with 600 fields inserted in opposite orders.
`verify_enketo_restore.py` now fingerprints sorted hash/set contents, significant
list/zset order, value types and absolute expirations. Changed values, list order
and expiry still fail. The original failure is retained as a sanitized receipt.
This change is only to the backup drill, not the preservation verifier.

Repeat the synthetic controls on the existing host with:

```bash
cd /srv/lastcopy/source
sudo python3 -m scripts.verify_redis_semantics
```

## Other checks closed

**Native browser zoom:** actual Chromium `chrome.tabs.setZoom(2)` was verified
by `getZoom`, device pixel ratio 1→2 and layout width 1418→709. CSS zoom remained
1. The real public sample, evidence drawer, Escape/focus return and recovery
bundle controls worked without horizontal overflow. This is native Chromium tab
zoom, not a physical-phone check or manual verification of every browser.

**Current submission fields:** the owner transcribed Track, automatic Team Name,
Description (150–2000 characters), Video (max four minutes; link/upload), Github
Solution and optional Pitch Deck. [The submission checklist](../submission/SUBMIT_TOMORROW.md)
uses those fields and the finished narrated MP4. No authenticated form was filled
or submitted automatically.

## Remaining boundaries

Component restoration does not establish a clean-host rebuild. App/Central
environment, provider reconfiguration, Cognito identifiers, TLS, routing and
operator access still need a separately controlled host-rebuild drill. Keep a
second secure offline copy of the owner's recipient key. The PC does not need to
stay on for the hosted core, Central or daily backup; the combined local sponsor
runtime still depends on it.

Physical-phone backup and independent human security review remain unavailable.
The latest reference home-page performance median is 82 with median LCP 2.561s,
below target; `/demo` scored 91 with LCP 2.071s. Debian's retained 72 advisories
have no available stable upgrade in the recorded check. Mitigations and exact
scope remain in [RISK_CLOSURE_FOLLOWUP.md](RISK_CLOSURE_FOLLOWUP.md).

The repository is private. The finished branch is `codex/product-redesign`;
GitHub's default is `main`. The checklist provides the exact finished branch
link and owner source-access steps. Visibility, default branch, merge and final
submission are unchanged.
