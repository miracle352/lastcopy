"""Stage 3 orchestration. The Stage 2 verifier remains the sole verdict authority.

Normalized synthetic rows are query evidence, not live Central readback. Raw objects
stay private. The World Model is rebuilt through the pinned actual reference.
"""
import csv
import io
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass
from typing import Literal
from pydantic import BaseModel, ConfigDict
from .config import ROOT, Settings
from .inventory import digest, inventory, read_archive, ImportRejected
from .models import RunManifest
from .snapshots import load_snapshot
from .xml_compare import xml_facts
from .reconcile import reconcile, RunCancelled, RunDeadline


class InvestigationError(ValueError):
    pass


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def seal_outputs(directory):
    seals = {str(path.relative_to(directory)).replace('\\', '/'): digest(path.read_bytes())
             for path in directory.rglob('*') if path.is_file() and path.name not in ('seals.json', 'cancel')}
    (directory / 'seals.json').write_bytes(encoded(seals) + b'\n')


class Action(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    action: Literal['investigate_gap', 'request_raw', 'keep_unresolved', 'export_guidance', 'manual_review']


def validate_action(value, allowed):
    try:
        action = Action.model_validate(value).action
        if action not in allowed:
            raise ValueError()
        return action
    except Exception:
        raise InvestigationError('Invalid or out-of-phase model action JSON') from None


class WorldJournal:
    """Private append-only revision records, replayed via real WorldModel.ingest.

    Deliberately single-writer: owned by the bounded investigation worker. No
    claim of distributed storage, search, or reference APIs absent from code.
    """
    def __init__(self, path, run_id='test'):
        self.path, self.run_id = Path(path), run_id

    def records(self):
        if not self.path.exists():
            return []
        if self.path.stat().st_size > 2097152:
            raise InvestigationError('World journal exceeds 2 MiB')
        records = [json.loads(line) for line in self.path.read_text(encoding='utf8').splitlines()]
        if len(records) > 512:
            raise InvestigationError('World journal exceeds 512 observations')
        if any(r.get('id') != digest(encoded({k: v for k, v in r.items() if k not in ('id', 'at')})) for r in records):
            raise InvestigationError('World observation content identity failed integrity check')
        return records

    def add(self, *, type, key, revision=0, evidence, **attrs):
        if type not in ('device_snapshot', 'form_version', 'submission_version', 'attachment', 'observation', 'hypothesis', 'recovery_operation') or not evidence:
            raise InvestigationError('World writes require typed identity and evidence provenance')
        record = dict(type=type, key=key, revision=revision, evidence=sorted(set(evidence)), **attrs)
        record['id'] = digest(encoded(record))
        records = self.records()
        for old in records:
            if (old['type'], old['key'], old['revision']) == (type, key, revision):
                if {k: v for k, v in old.items() if k != 'at'} != record:
                    raise InvestigationError('Append-only revision identity cannot be overwritten')
                return
        if len(records) >= 512:
            raise InvestigationError('World observation limit')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record['at'] = datetime.now(timezone.utc).isoformat()
        with self.path.open('ab') as output:
            output.write(encoded(record) + b'\n')

    def read(self, timeout=20):
        result = subprocess.run(['node', str(ROOT / 'node_modules/tsx/dist/cli.mjs'), str(ROOT / 'bridge/investigation-world.ts')],
            input=encoded({'records': self.records(), 'run_id': self.run_id}), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd=ROOT, timeout=timeout, check=False)
        if result.returncode:
            raise InvestigationError('Pinned World Model bridge failed; diagnostic body suppressed')
        if len(result.stdout) > 8388608:
            raise InvestigationError('World read exceeds bounded response')
        return json.loads(result.stdout)


@dataclass
class EvidencePack:
    run: RunManifest
    tables: dict
    objects: dict
    roles: dict
    settings: Settings
    capture_kind: str = 'supplied_synthetic_capture'

    def columns(self, name):
        if self.tables[name]:
            return sorted(self.tables[name][0])
        optional = {
            'media_references': 'run_id source_id version_id side form_id filename path indices object_id row_id',
            'attempt_logs': 'run_id source_id version_id evidence_id outcome http_status source_file response_hash captured_at row_id',
        }
        return sorted(optional[name].split())

    @classmethod
    def build(cls, manifest, devices, envelope, payload, settings, *, native_test_capture=False):
        run = RunManifest.model_validate(manifest)
        if not 1 <= len(devices) <= 8 or sum(map(len, [*devices, envelope, payload])) > 16777216:
            raise InvestigationError('Synthetic evidence pack exceeds 16 MiB / 8 devices')
        snapshot, server_files, _ = load_snapshot(envelope, payload, settings)
        inventories = [inventory(data, settings) for data in devices]
        native_ok=False
        if native_test_capture:
            from .odk_recovery import configured_target
            from .snapshots import scope_listing
            native_ok=(not settings.sample and settings.values.get('ODK_TEST_PROJECT')=='true'
                and run.mode=='connected' and run.destination.model_dump()==configured_target(settings)
                and snapshot.project_id==run.destination.project_id and snapshot.connection_id==run.destination.connection_id
                and snapshot.form_ids==[run.destination.form_id] and snapshot.scope_complete and snapshot.history_complete
                and scope_listing(snapshot,server_files,{r.evidence_id:r for r in snapshot.receipts}) is not None)
        if (not snapshot.synthetic and not native_ok) or any(not inv.manifest.synthetic for inv in inventories):
            raise InvestigationError('Stage 3 publication accepts explicitly synthetic evidence only')
        if set(run.source_snapshot_ids) != {snapshot.snapshot_id, *(inv.manifest.snapshot_id for inv in inventories)}:
            raise InvestigationError('Publication source identities do not match the run scope')
        if sum(len(inv.versions) for inv in inventories) + len(snapshot.versions) > 64:
            raise InvestigationError('Stage 3 synthetic pack exceeds 64 submission versions')
        tables = {key: [] for key in ('device_inventory', 'submission_versions', 'xml_facts', 'media_references', 'file_hashes', 'attempt_logs')}
        objects, roles = {}, {}

        def row(table, source, version='', **values):
            entry = {k: str(v) for k, v in dict(run_id=run.run_id, source_id=source, version_id=version, **values).items()}
            entry['row_id'] = digest(encoded({'table': table, **entry}))
            tables[table].append(entry)

        def object_row(data, source, path, role='file', version=''):
            oid = digest(data)
            objects[oid] = data
            if sum(map(len, objects.values())) > 67108864:
                raise InvestigationError('Private evidence objects exceed aggregate 64 MiB')
            row('file_hashes', source, version, object_id=oid, sha256=oid, source_file=path, role=role)
            if role != 'file':
                roles[source, role] = oid
            return oid

        def version_rows(source, versions, files, side):
            for version in versions:
                row('submission_versions', source, version.version_id, side=side, form_id=version.form_id,
                    form_version=version.form_version, logical_id=version.logical_submission_id,
                    xml_path=version.xml_path, xml_object=digest(files[version.xml_path]),
                    current=version.current, deprecated_id=version.deprecated_id)
                for fact in xml_facts(files[version.xml_path], settings):
                    row('xml_facts', source, version.version_id, side=side, form_id=version.form_id,
                        path=fact['path'], fact_json=encoded(fact).decode(), object_id=digest(files[version.xml_path]))
                for media in version.media:
                    row('media_references', source, version.version_id, side=side, form_id=version.form_id,
                        filename=media.filename, path=media.xml_path, indices=json.dumps(media.occurrence_indices),
                        object_id=media.sha256 or 'unavailable')

        for inv, archive in zip(inventories, devices):
            source = inv.manifest.snapshot_id
            files = read_archive(archive, settings)
            row('device_inventory', source, device_id=inv.manifest.device_id, captured_at=inv.manifest.captured_at)
            object_row(archive, source, 'original.zip', 'device')
            for path, data in files.items():
                object_row(data, source, path)
            version_rows(source, inv.versions, files, 'device')
        source = snapshot.snapshot_id
        object_row(envelope, source, 'server-snapshot.json', 'envelope')
        object_row(payload, source, 'server-payload.zip', 'payload')
        for path, data in server_files.items():
            object_row(data, source, path)
        version_rows(source, snapshot.versions, server_files, 'server')
        for view in snapshot.tabular_views:
            for data in csv.DictReader(io.StringIO(server_files[view.archive_path].decode('utf-8'))):
                for column, path in view.columns.items():
                    row('xml_facts', source, view.version_id, side='tabular', form_id=run.destination.form_id,
                        path=path, fact_json=encoded({'text': data.get(column)}).decode(), object_id=digest(server_files[view.archive_path]))
        for receipt in snapshot.receipts:
            row('attempt_logs', source, receipt.version_id or '', evidence_id=receipt.evidence_id,
                outcome=receipt.outcome, http_status=receipt.http_status, source_file=receipt.source_file,
                response_hash=receipt.response_sha256, captured_at=receipt.captured_at)
        for table, rows in tables.items():
            if (not rows and table not in ('media_references', 'attempt_logs')) or len(rows) > 5000:
                raise InvestigationError(f'Bounded evidence table required: {table}')
        if len(tables['media_references']) > 256:
            raise InvestigationError('Stage 3 synthetic pack exceeds 256 media references')
        result = cls(run, tables, objects, roles, settings,
            'native_synthetic_test_capture' if native_ok and not snapshot.synthetic else 'supplied_synthetic_capture')
        result.csv_files()  # Enforce physical scan bounds before any publication.
        return result

    def csv_files(self):
        result = {}
        for name, rows in self.tables.items():
            output = io.StringIO(newline='')
            # The verified Spark CSV reader uses backslash quote escaping.
            # Python's default doubled quotes corrupt JSON columns under that
            # reader. Quote every field and explicitly use its actual dialect.
            writer = csv.DictWriter(output, fieldnames=self.columns(name), quoting=csv.QUOTE_ALL,
                                    doublequote=False, escapechar='\\')
            writer.writeheader()
            writer.writerows(rows)
            data = output.getvalue().encode()
            if len(data) > 1048576:
                raise InvestigationError('Physical CSV evidence table exceeds 1 MiB')
            result[name] = data
        if sum(map(len, result.values())) > 4194304:
            raise InvestigationError('Physical CSV evidence pack exceeds 4 MiB')
        return result

    def resolve(self, row):
        oid = row.get('object_id')
        data = self.objects.get(oid)
        if data is None or digest(data) != row.get('sha256') or oid != row.get('sha256'):
            raise InvestigationError('Queried object hash/identity does not resolve to private evidence')
        expected = next((r for r in self.tables['file_hashes'] if r['row_id'] == row.get('row_id')), None)
        if row != expected:
            raise InvestigationError('Queried object row differs from immutable publication')
        return data


class Investigation:
    def __init__(self, directory, settings, cancel=lambda: False, clock=time.monotonic):
        self.directory, self.settings, self.cancel, self.clock = Path(directory), settings, cancel, clock
        self.events, self.steps, self.critiques, self.calls = [], 0, 0, 0

    def event(self, kind, **details):
        if 'elapsed_ms' in details:
            details['operation_elapsed_ms'] = details.pop('elapsed_ms')
        entry = dict(run_id=self.run.run_id, mode=self.mode, seq=len(self.events) + 1,
                     kind=kind, elapsed_ms=round((self.clock() - self.start) * 1000, 2), **details)
        self.events.append(entry)
        with (self.directory / 'events.jsonl').open('ab') as output:
            output.write(encoded(entry) + b'\n')

    def checkpoint(self):
        if self.cancel() or (self.directory / 'cancel').exists():
            raise RunCancelled()
        if self.clock() - self.start >= self.run.max_seconds:
            raise RunDeadline()

    def step(self, tool):
        self.checkpoint()
        if self.steps >= self.run.max_steps:
            raise InvestigationError('Investigation step budget exhausted')
        self.steps += 1
        self.event('tool', tool_id=f'tool-{self.steps}', tool=tool)

    def begin(self, pack, mode):
        self.run, self.mode, self.start = pack.run, mode, self.clock()
        self.directory.mkdir(parents=True, exist_ok=True)
        # Never append a second execution to a finished or interrupted trace.
        if (self.directory / 'events.jsonl').exists():
            raise InvestigationError('Investigation directory already has a trace; use a new attempt directory')
        self.event('started', limits={'steps': self.run.max_steps, 'critique_rounds': self.run.max_critique_rounds,
                                     'seconds': self.run.max_seconds}, source_kind=pack.capture_kind,
                   source_hashes=sorted(pack.objects), recovery_executed=False)
        objects = self.directory / 'objects'
        objects.mkdir()
        for oid, data in pack.objects.items():
            if digest(data) != oid:
                raise InvestigationError('Private source object integrity failure')
            with (objects / oid).open('xb') as output:
                output.write(data)
        (self.directory / 'run-manifest.json').write_bytes(encoded(self.run.model_dump(mode='json')) + b'\n')

    def sample(self, pack):
        if pack.run.mode != 'sample':
            raise InvestigationError('Sample execution requires a sample manifest; no mode fallback')
        return self._offline(pack, 'sample')

    def replay(self, pack):
        if pack.run.mode != 'replay' or self.settings.sample:
            raise InvestigationError('Replay requires an explicit replay manifest and SAMPLE_MODE=false; it makes no provider calls')
        return self._offline(pack, 'replay')

    def _offline(self, pack, mode):
        self.begin(pack, mode)
        self.checkpoint()
        devices = [pack.objects[oid] for (source, role), oid in pack.roles.items() if role == 'device']
        envelope = next(pack.objects[oid] for (_, role), oid in pack.roles.items() if role == 'envelope')
        payload = next(pack.objects[oid] for (_, role), oid in pack.roles.items() if role == 'payload')
        run = self.run
        report = reconcile(run, devices, envelope, payload, self.settings, cancel=self.cancel).model_dump(mode='json')
        report_bytes = encoded(report) + b'\n'
        (self.directory / 'report.json').write_bytes(report_bytes)
        self.event('comparison', report_sha256=digest(report_bytes), provenance=f'{mode}: offline deterministic supplied-capture comparison; no model or SQL calls')
        return self.finish('completed', report=report, report_sha256=digest(report_bytes))

    def finish(self, status, **values):
        self.event(status)
        models = [e for e in self.events if e['kind'] == 'model' and e.get('provider') == 'nightshift']
        values.setdefault('sponsor_status', {
            'zetaris': 'queried' if any(e['kind'] == 'query' and e.get('provider') == 'zetaris' for e in self.events)
                       else 'registered' if any(e['kind'] == 'publication' for e in self.events) else 'not_run',
            'world_model': 'read_write_reference' if any(e['kind'] == 'graph_read' for e in self.events) else 'not_run',
            'nightshift': 'inference_observed' if models else 'failed' if any(e['kind'] == 'provider_failure' for e in self.events) else 'not_run',
            'nvidia': 'verified' if any('nemotron' in (e.get('actual_serving_model') or '').lower() for e in models)
                      else 'blocked_no_verified_nemotron' if self.mode == 'connected' else 'not_exercised',
        })
        result = dict(run_id=self.run.run_id, mode=self.mode, status=status, provider_calls=self.calls,
                      steps=self.steps, critique_rounds=self.critiques, **values, events=self.events)
        (self.directory / 'investigation.json').write_bytes(encoded(result) + b'\n')
        seal_outputs(self.directory)
        return result

    def model(self, provider, role, prompt, allowed):
        self.step('nightshift_' + role)
        if role == 'reviewer':
            if self.critiques >= self.run.max_critique_rounds:
                raise InvestigationError('Critique budget exhausted')
            self.critiques += 1
        self.calls += 1
        started = self.clock()
        try:
            result, metadata = provider.action(role, prompt, allowed, self)
        except InvestigationError as error:
            self.event('provider_failure', provider='nightshift', role=role, attempt_id=f'model-{self.calls}',
                       error=str(error), elapsed_ms=round((self.clock() - started) * 1000, 2))
            raise
        self.checkpoint()
        action = validate_action(result, allowed)
        self.event('model', role=role, action=action, **metadata)
        return action

    def query(self, evidence, kind, pack):
        rows, receipt = evidence.query(kind, pack, self)
        self.checkpoint()
        data = encoded({'receipt': receipt, 'rows': rows})
        if len(data) > 2097152:
            raise InvestigationError('Query evidence exceeds 2 MiB')
        folder = self.directory / 'queries'
        folder.mkdir(exist_ok=True)
        oid = digest(data)
        (folder / (oid + '.json')).write_bytes(data)
        self.event('query', **receipt, evidence_object=oid)
        return rows, receipt

    def graph_read(self, world):
        self.checkpoint()
        remaining = self.run.max_seconds - (self.clock() - self.start)
        graph = world.read(timeout=max(.1, min(20, remaining)))
        self.checkpoint()
        self.event('graph_read', next_action=graph['next_action'], event_count=graph['event_count'])
        return graph

    def connected(self, pack, evidence, provider):
        self.begin(pack, 'connected')
        report = None
        try:
            if self.settings.sample:
                raise InvestigationError('Connected investigation requires SAMPLE_MODE=false')
            self.step('publish_synthetic_evidence')
            evidence.publish(pack)
            world = WorldJournal(self.directory / 'world.jsonl', self.run.run_id)
            # All imported text stays out of system instructions and tool parameters.
            self.step('query_export')
            gaps, query = self.query(evidence, 'export_gaps', pack)
            if not gaps:
                raise InvestigationError('No scoped export gap rows returned; cannot invent a hypothesis')
            device_facts = {r['row_id']: r for r in pack.tables['xml_facts'] if r['side'] == 'device'}
            if len({r.get('row_id') for r in gaps}) != len(gaps) or any(
                r.get('row_id') not in device_facts or any(device_facts[r['row_id']].get(k) != v for k, v in r.items()) for r in gaps):
                raise InvestigationError('Export gap query returned altered or out-of-scope rows')
            proof = [r['row_id'] for r in gaps]
            self.model(provider, 'investigator', {'evidence': 'Device XML paths absent from selected tabular view; raw server XML not checked.',
                       'row_ids': proof[:8], 'instruction': 'Investigate a possible missing-data hypothesis. Do not declare missing or preserved.'}, ['investigate_gap'])
            world.add(type='hypothesis', key='export-gap', revision=0, status='possible_missing_data',
                      next_action='review', evidence=proof)
            graph = self.graph_read(world)
            if graph['next_action'] != 'review':
                raise InvestigationError('World graph did not select unresolved review')
            critique = self.model(provider, 'reviewer', {'hypothesis': 'possible_missing_data',
                'proposed_action': 'consider_resubmission', 'evidence': 'Only a tabular export gap is known. Raw XML and retained history have not been fetched.',
                'instruction': 'Reject unsupported resubmission. Request raw XML/history evidence or keep unresolved.'}, ['request_raw', 'keep_unresolved'])
            self.event('critique', decision=critique, evidence=proof)
            if critique != 'request_raw':
                return self.finish('incomplete', error='Reviewer kept insufficient evidence unresolved; no raw comparison or recovery')
            world.add(type='hypothesis', key='export-gap', revision=1, status='needs_raw_evidence', next_action='fetch_raw', evidence=proof)
            graph = self.graph_read(world)
            if graph['next_action'] != 'fetch_raw':
                raise InvestigationError('Graph did not select raw evidence')
            self.step('fetch_scoped_raw_history_media')
            joined, join_query = self.query(evidence, 'versions', pack)
            rows, objects_query = self.query(evidence, 'objects', pack)
            # Fail closed on omitted, extra, duplicate, or tampered query rows.
            expected = [r for r in pack.tables['file_hashes'] if r['role'] != 'file']
            if sorted(rows, key=lambda r: r['row_id']) != sorted(expected, key=lambda r: r['row_id']):
                raise InvestigationError('Zetaris did not return the exact scoped source-object set')
            if not joined or len(joined) != len([v for v in pack.tables['submission_versions'] if v['side'] == 'device']):
                raise InvestigationError('Version join is incomplete or ambiguous')
            by_id = {r['row_id']: r for r in pack.tables['submission_versions']}
            seen = set()
            for row in joined:
                d, s = by_id.get(row.get('device_row')), by_id.get(row.get('server_row'))
                if (not d or d['side'] != 'device' or d['row_id'] in seen or
                    any(row.get(k) != d[k] for k in ('version_id', 'form_id', 'form_version')) or row.get('device_xml') != d['xml_object'] or
                    (s is not None and (s['side'] != 'server' or s['version_id'] != d['version_id'] or s['form_id'] != d['form_id'] or row.get('server_xml') != s['xml_object']))):
                    raise InvestigationError('Version join returned altered or ambiguous identities')
                seen.add(d['row_id'])
            devices, envelope, payload = [], None, None
            for row in rows:
                data = pack.resolve(row)
                if row['role'] == 'device':
                    devices.append(data)
                elif row['role'] == 'envelope':
                    envelope = data
                elif row['role'] == 'payload':
                    payload = data
                world.add(type='device_snapshot' if row['role'] == 'device' else 'observation', key=row['source_id'] + ':' + row['role'], evidence=[row['row_id']], object_id=row['object_id'])
            for row in joined:
                world.add(type='submission_version', key=row['device_row'], evidence=[row['device_row'], join_query['query_id']], version_id=row['version_id'])
            for form, version in sorted({(r['form_id'], r['form_version']) for r in joined}):
                world.add(type='form_version', key=form + ':' + version,
                    evidence=[r['device_row'] for r in joined if r['form_id'] == form and r['form_version'] == version], form_id=form)
            self.step('compare_payloads')
            report = reconcile(self.run.model_copy(update={'mode': 'connected'}), devices, envelope, payload, self.settings,
                cancel=lambda: self.cancel() or (self.directory / 'cancel').exists(),
                clock=self.clock).model_dump(mode='json')
            self.checkpoint()
            report_hash = digest(encoded(report) + b'\n')
            self.event('comparison', report_sha256=report_hash, query_ids=[query['query_id'], join_query['query_id'], objects_query['query_id']],
                       input_hashes=report['input_hashes'])
            self.step('query_media_references')
            media_rows, media_query = self.query(evidence, 'media', pack)
            if sorted(media_rows, key=lambda r: r['row_id']) != sorted(pack.tables['media_references'], key=lambda r: r['row_id']):
                raise InvestigationError('Media reference query is incomplete or changed')
            for row in media_rows:
                world.add(type='attachment', key=row['row_id'], evidence=[row['row_id'], media_query['query_id']], filename=row['filename'], object_id=row['object_id'])
            verdicts = [f['verdict'] for f in report['findings']]
            export_only = all(v in ('PRESERVED', 'EXPORT_VIEW_ONLY') for v in verdicts) and 'EXPORT_VIEW_ONLY' in verdicts
            allowed = ['export_guidance', 'manual_review'] if export_only else ['manual_review']
            proposed = self.model(provider, 'reviewer', {'deterministic_verdicts': verdicts,
                'raw_readback_hash': report_hash, 'evidence': 'Raw ordered XML and media were compared by code, including retained versions.',
                'instruction': 'Revise the initial hypothesis. Export omission requires export guidance and never resubmission. Conflicting/uncertain content remains manual review.'}, allowed)
            action = 'export_guidance' if export_only and proposed == 'export_guidance' else 'manual_review'
            status = 'rejected' if export_only else 'unresolved_conflict' if 'CONTENT_CONFLICT' in verdicts else 'unresolved'
            proofs = sorted(set(proof + [r['row_id'] for r in rows] + [report_hash, join_query['query_id']]))
            world.add(type='hypothesis', key='export-gap', revision=2, status=status, next_action=action, evidence=proofs)
            self.step('draft_guidance')
            world.add(type='recovery_operation', key='guidance', evidence=proofs, operation=action, executable=False)
            final_graph = self.graph_read(world)
            if final_graph['next_action'] != action:
                raise InvestigationError('Graph revision did not change next action')
            self.event('decision_changed', before='consider_resubmission', after=action, hypothesis=status, evidence=proofs)
            # Model output never enters report; independent verifier output is sealed separately.
            (self.directory / 'report.json').write_bytes(encoded(report) + b'\n')
            (self.directory / 'query-evidence.json').write_bytes(encoded({'gaps': gaps, 'versions': joined, 'objects': rows,
                'media': media_rows, 'queries': [query, join_query, objects_query, media_query]}) + b'\n')
            self.checkpoint()
            return self.finish('completed', report=report, report_sha256=report_hash, next_action=action,
                graph=final_graph,
                finding_resolution={f['finding_id']: {'query_ids': [join_query['query_id'], objects_query['query_id']],
                    'row_ids': [r['row_id'] for r in rows], 'verifier_receipts': f['evidence_ids']} for f in report['findings']})
        except (RunCancelled, KeyboardInterrupt):
            return self.finish('cancelled', error='Investigation cancelled; no recovery executed')
        except RunDeadline:
            return self.finish('failed', error='Investigation wall-time budget exhausted')
        except (InvestigationError, ImportRejected, subprocess.TimeoutExpired) as error:
            return self.finish('failed', error=str(error) if isinstance(error, (InvestigationError, ImportRejected)) else 'World read deadline exceeded')
        except Exception:
            return self.finish('failed', error='Investigation integration failure; private diagnostic bodies suppressed; no sample fallback')
