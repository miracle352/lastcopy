# Docker 29.9.2 patch follow-up

**Status: approved and applied.** See `STACK_SECURITY_REVIEW.md` and
`verification/stack-review/docker-final-patch.json` for actual acceptance.
The preparation/approval history below is retained.

27 October 2026. A final fresh apt-index check after the approved vendor change
found **29.9.2** available. The first approved plan explicitly pinned **29.8.2**;
this follow-up does not silently expand that approval.

[Official Engine 29 release notes](https://docs.docker.com/engine/release-notes/29/)
list further Go runtime fixes and rejection of compromised eMudhra intermediate
certificate chains in 29.9.2. containerd 2.4.2 is already installed from the first
maintenance. This is a further security update, not a reason to call 29.8.2 the
latest release or to discard the successful earlier advisory remediation.

Prepared action: install only `docker-ce` and `docker-ce-cli`
**5:29.9.2-1~ubuntu.24.04~noble** from the verified official signed repository.
The exact apt simulation lists two upgrades, zero new packages and zero removals.
Download these and the currently installed 29.8.2 packages before starting;
keep all prior rollback images/cold-copy data. Run the existing encrypted backup.

Temporarily serve the maintenance response, gracefully stop the nine existing
containers, update only these two packages, then start the same container IDs.
Do not change the data root, snapshotter, volumes, private configuration, database
schema, container images, Compose configuration or Redis/kernel settings.
On failure reinstall the retained 29.8.2 packages and restart the same containers;
do not restore stale database bytes. Before reopening verify container/image/volume
identities, original source hash, Central reads and actual comparison. Then repeat
public HTTPS and recovery readback. Estimated interruption **1–3 minutes**, not a
guarantee. No additional paid infrastructure and no private data export.

Activation awaits approval for this exact package revision and maintenance step.
