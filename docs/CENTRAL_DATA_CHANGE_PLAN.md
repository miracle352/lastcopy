# Central CSV and database-client dependency candidate

Prepared 27 October 2026. The candidate upgrades `csv-parse` to 7.0.3 and
overrides the UUID dependency used by Hyperid to 11.1.1. The resulting
production-only public dependency audit reports three high and eight moderate
entries; remaining advisories are not asserted to be harmless. The old Knex
and MinIO versions remain in place.

The exact image passed clean installation, parser limits, synthetic client
audit CSV value checks, clean database migrations and synthetic authenticated
API reads. These are targeted tests, not comprehensive compatibility proof for
every Central form, historical migration or external storage configuration.
The rollout preserves the existing volumes, source rows and archive hashes,
retains the existing image and override, gates traffic, checks both configured
scopes, and rolls back on failure. After the change, check the synthetic
recovery readback and verify it performs no repeated upload.

Deployed 27 October 2026. The fresh encrypted backup completed; source hashes,
mounts and authenticated reads matched, and synthetic recovery readback
remained preserved with zero additional uploads. The previous image and Compose
override were retained. The audit is `verification/central-final-pass/deployed-audit.json`.

An isolated attempt to eliminate all remaining entries reported zero in npm's
audit but broke actual MinIO loading and encoded query parsing. It was not
deployed. A Knex 3 experiment required changes to ten historical migrations;
it passed empty-database migration and synthetic login only. A populated older
database and full upgrade-path tests are still needed before any rollout.
