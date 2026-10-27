# Proposed production host changes

Prepared 27 October 2026 (Africa/Lagos). Target: the existing LastCopy Singapore
host, `18.141.113.136`. No new server, billing service, IAM permission or public
repository is involved. Live host changes await explicit approval after automatic
review rejected the earlier combined backup/upgrade request.

1. Apply only the Ubuntu security update for **libbrotli1**, from
   `1.1.0-2build2` to `1.1.0-2ubuntu0.1`. Fresh apt simulation lists this one
   update, no new packages and no removals. Use `--only-upgrade`; do not run a
   distribution upgrade or force configuration replacement.
2. Apply key-only SSH hardening: prohibit direct root login, turn off X11
   forwarding and reduce authentication attempts to three. Preserve the existing
   SSH port, Ubuntu account/key access and TCP forwarding needed by the documented
   private link. Validate sshd configuration and open a fresh SSH connection.
3. Enable the host firewall with inbound TCP **22, 80 and 443** allowed, outgoing
   traffic allowed and other inbound traffic denied. Keep Docker data services
   unpublished. UFW alone does not control Docker-published ports; inspect and
   probe those separately. Preserve existing rules; never reset the rule set.
   Before activation, schedule a five-minute rollback to remove only the new
   SSH override and disable UFW, its original state. Cancel that timer only after
   fresh SSH and public HTTPS checks succeed.
4. Reboot once to activate the **already installed** `7.0.0-1014-aws` kernel.
   Current kernel is `7.0.0-1012-aws`, and Ubuntu reports a reboot required.
   Expect a brief service interruption, approximately 2–3 minutes; this is an
   estimate, not a guarantee. Verify a changed boot ID, the new kernel, Docker,
   Caddy, backup timer, scoped Central access and original hashes afterward.

Run the already approved encrypted backup service separately before maintenance;
verify its local/S3 status. Keep every original, prior backup and rollback image.
Keep SSH/provider secrets on AWS. Do not publish configuration or copy plaintext
database content to this PC. If a precondition fails, stop rather than broadening
the upgrade or firewall rules.

The container patch/isolation assessment is recorded separately. This host plan
does not claim physical-phone acceptance, a clean-host rebuild or a human audit.
