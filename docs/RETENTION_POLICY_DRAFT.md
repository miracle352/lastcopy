# Proposed retention policy — not active

Prepared at the owner's request on 26 October 2026. Existing originals and backups
remain untouched. No S3 lifecycle rule or deletion job is enabled by this draft.

Verified accounts can download their registered originals and deterministic
reports from **Your data**, then submit an authenticated erasure-review request.
The request persists across restarts. It does not close the account, revoke
sessions or erase anything automatically.

Before activation, an operator must authenticate the requester, check legal or
preservation holds, identify their account and every retained copy, explain the
consequences and obtain explicit confirmation. Revoke sessions before a reviewed
live-data erasure. Record a minimal non-content fulfillment receipt.

Proposed encrypted-backup expiry is 30 days. It requires a separately reviewed
activation that replaces the current no-deletion instruction. Existing backup
copies must not be silently placed under a new expiry rule. A restore within
the expiry window must replay the erasure ledger before reopening access.
Until that mechanism is implemented and tested, do not promise complete erasure
or a 30-day deletion guarantee.

Read pending requests on the host without exporting account identifiers:

```sh
sudo docker exec lastcopy-cloud-api-1 python -m scripts.privacy_requests --store /app/private/application
```

This beta has no automated fulfillment or Cognito account-deletion tool. Requests
need operator follow-up. Indefinite retention and the proposed policy must be
disclosed until the replacement is explicitly activated.
