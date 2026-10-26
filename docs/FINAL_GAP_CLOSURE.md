# Final gap closure — 26 October 2026

Repository stays private; the owner will change visibility after review.
The earlier sealed release evidence remains unchanged. Read SUBMISSION_FINISH.md for the deployed follow-up and actual newer results.

## Approved activation and remaining policy

### Independent encrypted backups

Activated on 26 October: a private S3 Standard bucket in Singapore, Block Public Access,
BucketOwnerEnforced, versioning, HTTPS-only writes and server-side encryption.
Only CMS ciphertext and a non-secret checksum receipt leave the host. The existing
recipient private key stays on this PC. A dedicated uploader may write and verify
only the backup prefix; it cannot delete objects or read any application database.
Daily upload uses a bounded job, verifies the object checksum, retains every prior
copy and records failures. Earlier isolated database restore drills are retained;
the new S3 copy has a verified ciphertext readback, not a new full-machine restore
claim. No production restore or overwrite was performed.

The owner approved up to $0.10/month beyond the host. The private bucket and narrow uploader were provisioned through the signed-in AWS session. The real daily service uploaded fresh ciphertext and verified a full readback; the timer remains enabled. The 512 MiB application guard stops new copies without deleting older ones. It is not a hard AWS billing cap. See verification/submission-polish for actual receipts.

### Account/data retention

Existing instruction: keep evidence and all older backup copies; no deletion.
Prepared policy for review: a future reviewed closure would revoke access before erasure;
original evidence is purged only after authenticated explicit confirmation and
an operator review. Existing immutable backup copies remain retained under the
current no-deletion instruction. Do not promise complete erasure from backups.
The owner approved preparation of a 30-day encrypted-backup expiry policy, not its activation. Current authenticated requests only persist awaiting_operator_review. See RETENTION_POLICY_DRAFT.md; no expiry, revocation or deletion is implied by submitting a request.

## External acceptance

A physical Android phone is still unavailable. Emulator acceptance cannot stand
in for a physical-phone independent-backup claim. Native Chrome keyboard zoom did
not change devicePixelRatio; browser-internal settings navigation is blocked by
the available tool. CSS zoom is not native zoom. A person must check the real
browser Zoom menu at 200% until supported native controls are available.

A vendor-supported generic Linux Nightshift runtime remains unavailable in the
current official edition documentation. Direct NVIDIA is separate and works;
it cannot be renamed Nightshift. Full always-on sponsor deployment needs suitable
supported hardware or a vendor-supported runtime. An internal code audit does not
replace an independent external security review.
