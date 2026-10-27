# Proposed Docker security maintenance

Prepared 27 October 2026 (Africa/Lagos). Existing host only; no new paid service.

The host has Ubuntu Docker `29.1.3-0ubuntu3~24.04.2`. Upstream advisory
[CVE-2026-92543](https://github.com/moby/moby/security/advisories/GHSA-7cfq-22r6-qp73)
fixes insecure registry DNS fallback in **29.8.2**. Ubuntu's
[tracker](https://ubuntu.com/security/CVE-2026-92543) still says “Needs evaluation”;
this assessment does not assume an unconfirmed backport. Swarm is inactive, so
the separate encrypted-overlay advisory does not describe this bridge setup.

Docker's official signed Noble repository provides the following simulated
replacement, following its [Ubuntu installation procedure](https://docs.docker.com/engine/install/ubuntu/):

- Remove the conflicting **software packages** `docker.io`, `docker-compose-v2`,
  `containerd` and `runc`, without purging configuration or deleting data.
- Install `docker-ce` and `docker-ce-cli` **5:29.8.2-1~ubuntu.24.04~noble**,
  `containerd.io` **2.4.2-3~ubuntu.24.04~noble**, Buildx **0.38.1** and Compose
  **5.6.1**, with no recommended extras. The apt simulation succeeds using a
  separate package-index directory; the host's active apt sources are untouched.
- The repository key fingerprint is
  `9DC858229FC7DD38854AE2D88D81803C0EBFCD88`. Retain repository signatures and
  downloaded package hashes; no convenience installer or arbitrary latest major.

Before installation, download both replacement and currently installed packages
for rollback. Run the already-approved encrypted backup service. Gracefully stop
containers and Docker/containerd, then make a **cold private on-host rollback
copy** of `/var/lib/docker` and `/var/lib/containerd`. This can contain private
data and container environment configuration: keep it root-only on the existing
AWS host, never export it or include it in the narrower S3 backup. Refuse if the
copy would breach the 5 GiB free-space reserve. Keep all originals and backups.

Install the reviewed packages, start Docker and restore the existing containers.
Preserve the existing containerd image store, data root, volumes and configuration.
Verify Engine version, image/container/volume identities, private port bindings,
firewall, scoped Central reads, recovery readback and the public browser flow.
If startup or data checks fail, stop and restore the old packages and cold data
copy; retain failed state privately for diagnosis instead of deleting it.

This is a package-vendor change beyond the earlier single-package host approval.
It needs explicit approval and a second maintenance window. Allow **5–15 minutes**
of service interruption for cold copying and restart; this is an estimate.
Package/data-store compatibility and downtime are material risks, so this plan
does not promise a zero-interruption upgrade or replace clean-host acceptance.
