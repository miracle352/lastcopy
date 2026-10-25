# Water-point setup and automatic-check acceptance

Actual local work on 25 October 2026. The collection project is empty; the pilot
contains one native, explicitly synthetic Collect submission. No public deployment
or real field visit is represented here.

- `core-tests.txt`: 189 tests passed, one nonfailing deprecation warning, 211.71 s.
- `live-acceptance.json`, `native-delivery.jsonl`, `before-report.json` and
  `after-report.json`: actual pilot absence, native delivery, fresh authenticated
  XML/history/media capture and deterministic comparison. One 400 request lacked
  the required OpenRosa version header; a fresh absence check preceded the
  corrected 201. This is native delivery, not recovery Apply.
- `captured/`: exact registered synthetic inputs underlying those reports.
  Their manifests retain the original Connected capture identity. Recomputing them
  is an offline comparison of saved evidence, never a new Connected investigation.
  Run `python -m scripts.verify_water_point_captures` from the repo root with its
  virtual environment to exercise the documented CLI with socket connections denied.
  Both comparisons passed. An initial harness cleanup hit a Windows SQLite file
  lock; the corrected harness retains its private ledgers/results and exits cleanly.
- `browser.json`, `keyboard.json`: actual production pilot and separate keyboard
  sample/recovery/readback workflows. Root `monitor-*.png` are initial captures;
  they exposed a text-encoding defect that was subsequently corrected.
- `collection/browser.json` and its screenshots: final production verification
  against empty collection scope. The pilot source correctly yields
  MISSING_SUBMISSION; collection recovery remains unavailable. Five responsive
  widths, 200% CSS layout zoom, reduced motion, saved state and clean text checked.
- `ready/`: final production UI on the actual empty collection connection, monitor
  enabled and waiting for the first device export. Desktop/mobile, no overflow or
  browser errors. No source coverage or successful collection report is invented.
- `restart-receipt.json`: actual API restart restored saved monitor state.
- `integrity.json`: original draft files, native export and three previous evidence
  seals verified. `SHA256.json` seals this new directory after verification.
- `release-security.json` and `app-user-credential-audit.json`: focused current
  credential/history checks. Private QR/settings files are excluded.

Production build and TypeScript passed. Chromium 153 was used; CSS layout zoom
does not claim a native browser-zoom test. No new Lighthouse/Docker measurement,
physical-phone exporter, QR import, LAN/HTTPS deployment, sponsor inference or
recovery Apply is claimed for this follow-up. See `../../CONTINUOUS_CHECKS.md`.
