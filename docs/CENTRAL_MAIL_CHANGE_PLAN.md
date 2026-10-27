# Central mailer patch

Prepared 27 October 2026. Replace only the Central service image with
`lastcopy-stack:central-mail-minimal-20261027`, retaining the current image and
Compose override for rollback. The patch upgrades Nodemailer to 10.2.1, checks
the exact upstream manifest and lock hashes, and leaves Knex unchanged. The
public-only production dependency audit reports three high and twelve moderate
entries; this is not a claim that the remaining entries are harmless.

The exact candidate passed clean install, parser controls, clean synthetic
database migrations, synthetic authenticated API reads, a synthetic SMTP
password-reset message, and connection verification using the configured SMTP
settings in memory on the host. No message was sent to a real address. A fresh
encrypted backup completed successfully. Rollout uses a maintenance gate,
on-host source hashes, unchanged-volume checks, authenticated reads, and the
retained previous image and override if verification fails. Afterward, rerun
the synthetic recovery readback with no uploads.

Deployed 27 October 2026. Authenticated reads and source-hash and mount checks
passed, and the synthetic recovery readback remained preserved with zero
additional uploads. The previous image and override remain for rollback. This
mailer image was subsequently replaced by the tested CSV/UUID image described
in [CENTRAL_DATA_CHANGE_PLAN.md](CENTRAL_DATA_CHANGE_PLAN.md).
