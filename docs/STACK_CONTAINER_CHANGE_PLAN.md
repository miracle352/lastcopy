# Proposed container patch and isolation rollout

Prepared 27 October 2026 (Africa/Lagos). This is separate from the completed,
approved Ubuntu/SSH/firewall/kernel and Docker Engine maintenance.

Target: the existing LastCopy Central stack on `18.141.113.136`. Replace only
its eight existing service containers using tested local images:

- Central: same pinned upstream source/release, Node **24.22.1**, stable OS
  updates, and four reviewed lockfile entries: proxy-addr **2.0.8**, body-parser
  **1.20.9**, its nested qs **6.16.1**, and multer **2.5.0**. No major Knex change.
- Enketo: same **7.6.4** application with Node **22.23.4** and stable OS updates.
- PostgreSQL remains **14.24**; Redis remains **8.10.1**, with stable OS updates.
- nginx and private mail container receive stable OS updates.
- pyxform remains **4.5.0**, with Python **3.12.15**, updated Alpine/OpenSSL and
  one write-buffer flush before reopening an XLSX file. A deterministic tiny
  XLSX fails on the original and passes actual conversion/Java validation with
  this fix. Malformed input is rejected.

The merged Compose configuration retains the same volumes, private configuration,
generated keys, memory limits and loopback Central proxy. Add separate internal
PostgreSQL and Redis networks, with only their required application clients
attached. Add no-new-privileges, a 256 PID limit and bounded local logs.
Routine Compose rebuilds must not silently overwrite the patched images.

Preconditions already exercised: compatible Node/bcrypt/Express controls,
PostgreSQL synthetic dump/restore, Redis RDB readback, parser red/green control,
actual XLSForm conversion and merged Compose validation. The original database
and Redis volumes were not mounted by those isolated controls. An encrypted
backup was completed before preparing activation; all earlier backups are retained.

During rollout, temporarily serve an honest public maintenance response. Hash
the existing project/form/submission/XML/attachment/blob rows, original native
source and three generated Enketo keys **on AWS only**, without exporting their
plaintext. Stop the eight stack containers, replace the small non-secret cloud
override file, and recreate them without rebuilding/pulling. Do not delete any
volume or record; preserve the LastCopy application container/environment.

Before reopening public access, verify exact candidate images and original
volume identities, authenticated reads in collection project 1 and synthetic
recovery project 2, source-row/key/hash equality and actual offline comparison.
Then perform public browser/readback checks and final advisory matching. Keep
old image tags and the original override for automatic rollback on failure.
Rollback restores container images/configuration, never overwrites the database
as a convenience. Failure receipts stay private until redacted.

Expected interruption is **2–5 minutes**, not a guarantee. This is no new paid
service, no credential export and no database major-version migration. There
remain upstream application dependency advisories; this plan does not claim
zero vulnerabilities, a human audit or clean-host disaster-recovery acceptance.

Activation is pending explicit approval because automatic review rejected this
separate rollout as outside the previous Docker maintenance approval.
