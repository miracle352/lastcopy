# Stage 2 implementation and acceptance plan

Scope: deterministic supplied-snapshot comparisons, registered local inputs,
SQLite run ledger, bounded jobs, CLI/API, three offline samples and held-out tests.
No live exporter, investigation agent, recovery execution or marketing UI.

1. `xml_compare.py`: expanded ordered facts, exact meaningful text and attributes,
   explicit element-only whitespace policy, bounded difference detail.
2. `models.py`, `snapshots.py`: extend existing authoritative schemas for scoped
   listings/history/media receipts and tabular views. Hash payloads, validate
   identity and receipt ownership; unavailable evidence never establishes absence.
3. `reconcile.py`: six verdicts, separate finding codes/preservation, evidence
   receipts, historical edits, independent attachment slots and cautious coverage.
4. `store.py`: content-addressed immutable registrations, SQLite run IDs/status,
   request idempotency, local output hashes and JSONL events. Bounded queue and
   one worker per store, cooperative cancellation/deadlines and restart recovery.
5. `api.py`, `scripts/run.py`: registered IDs only on `/run`; JSON registration
   endpoints bound uploads; CLI explicitly reads locally selected files before
   registration. Same engine and persisted reports. API binds loopback on 8000.
6. `scripts/build_stage2_fixtures.py`, fixtures and tests: fixed seeds/IDs/paths,
   independently written expectations; stranded, media, export/history samples;
   held-out variant and uncertainty/hostile archive controls. No provider logs.
7. Regenerate OpenAPI/browser types; run full regression, CLI and HTTP API checks,
   evidence hash integrity, source immutability and meaningful mutation checks.
   Record actual checks and limits in HANDOFF and verification documentation.
