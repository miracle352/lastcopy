# Central dependency candidate — 27 October 2026

The hosted Central service was switched to the tested candidate on 27 October
2026. The previous image `lastcopy-stack:central-20261027` and its Compose
override remain on the host for rollback. The candidate image is
`lastcopy-stack:central-dependency-candidate-20261027` (image manifest
`sha256:a70bed12dfcf68b8e27e9e8ffcbb362a427b969603423ab7d33c5e5df2bd234f`).
It starts with the same pinned upstream code and runtime, validates the upstream
lock hash, applies the explicit package additions/replacements and obsolete-node
removals, and validates the resulting lock hash
`a1f8532ccbe477eb3818f95570a0bf12a8a0ac4fb03687113aed3bff4e6425fc`.

The production-only npm advisory report on the public-only lock falls from
13 high and 16 moderate entries to 4 high and 12 moderate. These are dependency
entries, not counts of independently exploitable vulnerabilities. The remaining
high entries include knex, braces and micromatch in the Knex migration tree,
and Nodemailer. Knex and Nodemailer need major-version compatibility work;
they are not declared fixed by this candidate. Other remaining entries include
the pinned MinIO and Slonik trees. See the retained audit report for details.

The candidate installed cleanly, passed the existing malformed proxy-address,
bounded JSON and multipart parser controls, loaded bcrypt and Central modules,
and ran all database migrations on an empty, disposable, network-isolated
PostgreSQL database. An isolated Central process authenticated a synthetic user
and read its project list. These checks do not prove all Central functions or
all upgrade paths. The first synthetic database setup failed to start because
the production PostgreSQL wrapper waits for an upgrade marker; the retry used
the standard PostgreSQL entrypoint and passed.

The approved encrypted backup service returned `Result=success` before rollout.
Only Central's service container was replaced. Source-table and native-archive
hashes and volume identities matched before and after, authenticated reads of
both configured scopes succeeded, and fresh synthetic recovery readback found
the source preserved. Repeated Apply made zero uploads. The maintenance gate
was removed after the checks. The encrypted backup and previous image remain.

A separate experiment upgrading Knex 3.3.0, Nodemailer 10.2.1 and MinIO 8.0.7
reported zero high and eight moderate entries but failed a real clean-database
migration: `20171030-01-add-default-authz-records.js` attempted to insert a
value too long for `varchar(36)`. It was not deployed. This needs a targeted
review of upstream migration return values and compatibility, rather than a
forced dependency upgrade.

An independent Nodemailer 10.2.1 experiment reported three high and twelve
moderate entries; clean migrations, synthetic login, parser controls and a
loopback SMTP password-reset message passed. It is not deployed: live transport
compatibility and a reproducible production patch still need verification.
The audit reports are in `verification/central-dependency-pass/`.

No source records, database volumes or earlier backups should be deleted.
Major dependency upgrades require separate compatibility and migration tests.
