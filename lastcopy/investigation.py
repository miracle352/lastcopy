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


def carry(record, *drop):
    """Attributes of a previous revision to repeat on the next one."""
    skip = {'id', 'at', 'key', 'revision', 'evidence', 'type', 'status', *drop}
    return {k: v for k, v in record.items() if k not in skip}


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
        if type not in ('device_snapshot', 'form_version', 'submission_version', 'attachment', 'observation', 'hypothesis', 'recovery_operation',
                        'triage', 'suspicion', 'verification', 'finding', 'remedy', 'device_decision', 'challenge', 'explanation') or not evidence:
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

    # ------------------------------------------------------------------ modes
    def sample(self, pack):
        """Full investigation with no network: local SQL engine + deterministic offline policy."""
        if pack.run.mode != 'sample':
            raise InvestigationError('Sample execution requires a sample manifest; no mode fallback')
        from .agents import LocalSQLEvidence, OfflinePolicy
        evidence = LocalSQLEvidence()
        try:
            return self.investigate(pack, evidence, OfflinePolicy(), 'sample')
        finally:
            evidence.close()

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
        report = reconcile(self.run, devices, envelope, payload, self.settings, cancel=self.cancel).model_dump(mode='json')
        report_bytes = encoded(report) + b'\n'
        (self.directory / 'report.json').write_bytes(report_bytes)
        self.event('comparison', report_sha256=digest(report_bytes), provenance=f'{mode}: offline deterministic supplied-capture comparison; no model or SQL calls')
        return self.finish('completed', report=report, report_sha256=digest(report_bytes))

    def connected(self, pack, evidence, provider):
        if self.settings.sample:
            self.begin(pack, 'connected')
            return self.finish('failed', error='Connected investigation requires SAMPLE_MODE=false')
        return self.investigate(pack, evidence, provider, 'connected')

    # ------------------------------------------------------------------ trace
    def finish(self, status, **values):
        self.event(status)
        models = [e for e in self.events if e['kind'] == 'model' and e.get('provider') == 'nightshift']
        local = getattr(self, 'mode', None) == 'sample'
        values.setdefault('sponsor_status', {
            'zetaris': 'local_sql_stand_in' if local else 'queried' if any(e['kind'] == 'query' and e.get('provider') == 'zetaris' for e in self.events)
                       else 'registered' if any(e['kind'] == 'publication' for e in self.events) else 'not_run',
            'world_model': 'planned_this_run' if any(e['kind'] == 'graph_read' for e in self.events) else 'not_run',
            'nightshift': 'offline_policy' if local else 'inference_observed' if models else 'failed' if any(e['kind'] == 'provider_failure' for e in self.events) else 'not_run',
            'nvidia': 'verified' if any('nemotron' in (e.get('actual_serving_model') or '').lower() for e in models)
                      else 'not_exercised' if local or self.mode != 'connected' else 'blocked_no_verified_nemotron',
        })
        result = dict(run_id=self.run.run_id, mode=self.mode, status=status, provider_calls=self.calls,
                      steps=self.steps, critique_rounds=self.critiques, **values, events=self.events)
        (self.directory / 'investigation.json').write_bytes(encoded(result) + b'\n')
        seal_outputs(self.directory)
        return result

    def agent(self, name, action, *, target=None, said=None, did=None, status='success', model=None, confidence=None, retry_count=0, **extra):
        """One guideline-format trace line: who acted, on what, for whom, with which engine."""
        self.event('agent', agent_name=name, action=action, target_agent=target, input_summary=said, output_summary=did,
                   model=model, confidence=confidence, retry_count=retry_count, status=status, **extra)

    def ask(self, provider, role, payload, ids, check):
        """A judgement call. Schema in, code validation out, one repair attempt, then labelled offline policy."""
        from .agents import schema, OfflinePolicy
        if self.calls >= 10:
            raise InvestigationError('Model call budget exhausted')
        errors = []
        for attempt in range(2):
            self.calls += 1
            started = self.clock()
            request = dict(payload, **({'previous_errors': errors} if errors else {}))
            try:
                value, metadata = provider.respond(role, request, schema(role, ids), self)
                self.checkpoint()
                errors = check(value)
            except InvestigationError as error:
                self.event('provider_failure', provider=getattr(provider, 'name', 'model'), role=role, attempt=attempt + 1,
                           error=str(error), elapsed_ms=round((self.clock() - started) * 1000, 2))
                errors, value, metadata = [str(error)], None, None
                if attempt == 0 and 'NVIDIA award blocked' in str(error):
                    raise
            if metadata:
                self.event('model', role=role, attempt=attempt + 1, valid=not errors, errors=errors[:6], **metadata)
            if value is not None and not errors:
                return value, metadata
        value, metadata = OfflinePolicy().respond(role, payload, schema(role, ids), self)
        self.event('fallback', role=role, provider='offline-policy', reason='; '.join(errors[:3]) or 'invalid response')
        return value, dict(metadata, fallback=True)

    @staticmethod
    def engine(metadata):
        return metadata.get('actual_serving_model') or metadata.get('routing_id') or metadata.get('provider')

    def graph_read(self, world):
        self.checkpoint()
        remaining = self.run.max_seconds - (self.clock() - self.start)
        graph = world.read(timeout=max(.1, min(20, remaining)))
        self.checkpoint()
        self.event('graph_read', next_action=graph['next_action'], focus=graph['focus'], why=graph['why'],
                   counts=graph['counts'], event_count=graph['event_count'])
        self.agent('World Model planner', 'select_next_action', target=graph['next_action'], said=f"graph holds {graph['counts']}",
                   did=graph['why'], model='meterless-world-model (pinned reference)')
        return graph

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

    # ------------------------------------------------------------------ the loop
    def investigate(self, pack, evidence, provider, mode):
        self.begin(pack, mode)
        self.pack, self.evidence, self.provider = pack, evidence, provider
        self.world = WorldJournal(self.directory / 'world.jsonl', self.run.run_id)
        self.suspicions, self.report, self.decisions, self.explanations, self.remedies = {}, None, [], {}, {}
        self.device_of = {r['source_id']: r['device_id'] for r in pack.tables['device_inventory']}
        handlers = {'triage': self._triage, 'classify': self._classify, 'review': self._review, 'fetch_evidence': self._fetch,
                    'evaluate': self._evaluate, 'remedy': self._remedy, 'decide': self._decide, 'challenge': self._challenge, 'explain': self._explain}
        try:
            while True:
                graph = final = self.graph_read(self.world)
                action = graph['next_action']
                if action == 'done':
                    break
                if action not in handlers:
                    raise InvestigationError('World Model selected an unknown action')
                self.step(action)
                handlers[action](graph)
            report_bytes = encoded(self.report) + b'\n'
            (self.directory / 'report.json').write_bytes(report_bytes)
            decisions = [dict(d, explanation=self.explanations.get(d['device_id'])) for d in self.decisions]
            (self.directory / 'decisions.json').write_bytes(encoded(decisions) + b'\n')
            return self.finish('completed', report=self.report, report_sha256=digest(report_bytes), decisions=decisions,
                               remedies=self.remedies, hypotheses=final['latest_hypotheses'], graph=final,
                               next_action=sorted({r['action'] for r in self.remedies.values()} or {'none'})[-1])
        except (RunCancelled, KeyboardInterrupt):
            return self.finish('cancelled', error='Investigation cancelled; no recovery executed')
        except RunDeadline:
            return self.finish('failed', error='Investigation wall-time budget exhausted')
        except (InvestigationError, ImportRejected, subprocess.TimeoutExpired) as error:
            return self.finish('failed', error=str(error) if isinstance(error, (InvestigationError, ImportRejected)) else 'World read deadline exceeded')
        except Exception:
            return self.finish('failed', error='Investigation integration failure; private diagnostic bodies suppressed')

    # 1. Scout: cross-source SQL finds where to look -----------------------------
    def _triage(self, graph):
        pack = self.pack
        receipt = self.evidence.publish(pack)
        if receipt:
            self.event('publication', **receipt)
        engine = getattr(self.evidence, 'name', 'evidence')
        signals = []
        for kind, signal in (('missing_versions', 'missing_version'), ('missing_media', 'missing_media'),
                             ('xml_mismatch', 'xml_mismatch'), ('export_gaps', 'export_gap')):
            rows, q = self.query(self.evidence, kind, pack)
            self.agent('Scout', 'cross_source_query', target='World Model planner', said=kind,
                       did=f'{len(rows)} row(s) via {engine}', model=engine, query_id=q['query_id'])
            groups = {}
            for row in rows:
                groups.setdefault((row['source_id'], row['version_id']), []).append(row)
            for (source, version), group in sorted(groups.items()):
                detail = {'rows': len(group)}
                if signal == 'missing_media':
                    detail['filenames'] = sorted({r['filename'] for r in group})
                if signal == 'export_gap':
                    detail['answer_paths_missing_from_spreadsheet'] = len(group)
                signals.append(dict(signal=signal, source_id=source, version_id=version, device_id=self.device_of.get(source, source),
                                    detail=detail, row_ids=sorted(r['row_id'] for r in group), query_id=q['query_id']))
        for n, s in enumerate(signals, 1):
            sid = f'S{n}'
            self.suspicions[sid] = dict(s, suspicion_id=sid)
            self.world.add(type='suspicion', key=sid, evidence=s['row_ids'][:32] + [s['query_id']], signal=s['signal'],
                           device_id=s['device_id'], version_id=s['version_id'], source_id=s['source_id'])
        self.world.add(type='triage', key='triage', evidence=[s['query_id'] for s in signals] or ['no-suspicions'],
                       suspicions=len(signals), engine=engine)

    def _public(self, sid):
        s = self.suspicions[sid]
        return {k: s[k] for k in ('suspicion_id', 'signal', 'device_id', 'version_id', 'detail')}

    # 2. Investigator: hypotheses (Nemotron) -----------------------------------
    def _classify(self, graph):
        from .agents import SIGNAL_DEFAULT
        latest = {h['key']: h for h in graph['latest_hypotheses']}
        focus = [k[2:] if k.startswith('H-') else k for k in graph['focus']]
        critique = {k[2:]: latest[k].get('review_reason') for k in graph['focus'] if k in latest}
        payload = {'suspicions': [self._public(s) for s in focus], 'critique': critique,
                   'signal_meaning': {'missing_version': 'device record version with no server version',
                                      'missing_media': 'device file reference with no server file of that name',
                                      'xml_mismatch': 'same version id, different XML bytes',
                                      'export_gap': 'device answer paths absent from the server spreadsheet export'}}

        def check(value):
            got = [h.get('suspicion_id') for h in value.get('hypotheses', [])]
            return [] if sorted(got) == sorted(focus) else ['return exactly one hypothesis for each suspicion_id: ' + ','.join(focus)]
        value, meta = self.ask(self.provider, 'investigator', payload, focus, check)
        by = {h['suspicion_id']: h for h in value['hypotheses']}
        for sid in focus:
            h = by.get(sid) or dict(zip(('hypothesis', 'evidence_needed', 'priority'), SIGNAL_DEFAULT[self.suspicions[sid]['signal']]))
            old = latest.get('H-' + sid)
            self.world.add(type='hypothesis', key='H-' + sid, revision=(old['revision'] + 1) if old else 0,
                           evidence=self.suspicions[sid]['row_ids'][:32], suspicion=sid, signal=self.suspicions[sid]['signal'],
                           device_id=self.suspicions[sid]['device_id'], version_id=self.suspicions[sid]['version_id'],
                           hypothesis=h['hypothesis'], evidence_needed=h['evidence_needed'], priority=int(h['priority']),
                           status='proposed', proposed_by=self.engine(meta), revised=bool(old))
            self.agent('Investigator', 'propose_hypothesis' if not old else 'revise_hypothesis', target='Reviewer',
                       said=f"{sid} {self.suspicions[sid]['signal']} on {self.suspicions[sid]['device_id']}",
                       did=f"{h['hypothesis']} - test with {h['evidence_needed']}", model=self.engine(meta),
                       retry_count=int(bool(old)), fallback=bool(meta.get('fallback')))

    # 3. Reviewer: critique with authority (Nemotron + code guard) -----------------
    def _review(self, graph):
        from .agents import REQUIRED_EVIDENCE
        if self.critiques >= self.run.max_critique_rounds:
            raise InvestigationError('Critique budget exhausted')
        self.critiques += 1
        latest = {h['key']: h for h in graph['latest_hypotheses']}
        focus = graph['focus']
        payload = {'hypotheses': [{'hypothesis_id': k, 'suspicion_id': latest[k]['suspicion'], 'signal': latest[k]['signal'],
                                   'device_id': latest[k]['device_id'], 'hypothesis': latest[k]['hypothesis'],
                                   'evidence_needed': latest[k]['evidence_needed'], 'detail': self.suspicions[latest[k]['suspicion']]['detail']}
                                  for k in focus]}

        def check(value):
            got = [r.get('hypothesis_id') for r in value.get('reviews', [])]
            return [] if sorted(got) == sorted(focus) else ['review each hypothesis_id exactly once: ' + ','.join(focus)]
        value, meta = self.ask(self.provider, 'reviewer', payload, focus, check)
        for r in value['reviews']:
            h = latest[r['hypothesis_id']]
            decision, reason, guarded = r['decision'], r['reason'], False
            if decision == 'approve' and h['evidence_needed'] not in REQUIRED_EVIDENCE[h['hypothesis']]:
                decision, reason, guarded = 'revise', 'wrong_evidence_for_hypothesis', True  # code guard: approval must be testable
            capped = decision == 'revise' and h['revision'] >= 2
            status = {'approve': 'approved', 'revise': 'revise', 'reject': 'rejected'}[decision]
            if capped:  # review budget spent: test it anyway; verification covers every record regardless
                status = 'approved'
            self.world.add(type='hypothesis', key=h['key'], revision=h['revision'] + 1, evidence=h['evidence'],
                           **carry(h, 'review_reason', 'reviewed_by', 'code_guard', 'review_capped'),
                           status=status, review_reason=reason, reviewed_by=self.engine(meta), code_guard=guarded, review_capped=capped)
            self.agent('Reviewer', 'critique', target='Investigator' if status == 'revise' else 'World Model planner',
                       said=f"{h['key']}: {h['hypothesis']} via {h['evidence_needed']}",
                       did=f"{decision}{' (code guard)' if guarded else ''}{' -> tested anyway (review cap)' if capped else ''}: {reason}",
                       model=self.engine(meta), status='needs_revision' if status == 'revise' else 'success', fallback=bool(meta.get('fallback')))

    # 4. Evidence + Verifier: raw bytes decide (code) ------------------------------
    def _fetch(self, graph):
        pack, evidence, world = self.pack, self.evidence, self.world
        joined, join_query = self.query(evidence, 'versions', pack)
        rows, objects_query = self.query(evidence, 'objects', pack)
        expected = [r for r in pack.tables['file_hashes'] if r['role'] != 'file']
        if sorted(rows, key=lambda r: r['row_id']) != sorted(expected, key=lambda r: r['row_id']):
            raise InvestigationError('Evidence engine did not return the exact scoped source-object set')
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
            else:
                payload = data
            world.add(type='device_snapshot' if row['role'] == 'device' else 'observation', key=row['source_id'] + ':' + row['role'],
                      evidence=[row['row_id']], object_id=row['object_id'])
        media_rows, media_query = self.query(evidence, 'media', pack)
        if sorted(media_rows, key=lambda r: r['row_id']) != sorted(pack.tables['media_references'], key=lambda r: r['row_id']):
            raise InvestigationError('Media reference query is incomplete or changed')
        self.agent('Evidence fetcher', 'resolve_raw_objects', target='Verifier', said='versions, objects, media',
                   did=f'{len(devices)} device export(s), server capture and {len(media_rows)} file reference(s); every hash re-checked',
                   model=getattr(evidence, 'name', 'evidence'))
        report = reconcile(self.run.model_copy(update={'mode': self.mode if self.mode != 'replay' else 'replay'}), devices, envelope, payload, self.settings,
                           cancel=lambda: self.cancel() or (self.directory / 'cancel').exists(), clock=self.clock).model_dump(mode='json')
        self.checkpoint()
        self.report = report
        report_hash = digest(encoded(report) + b'\n')
        self.event('comparison', report_sha256=report_hash, query_ids=[join_query['query_id'], objects_query['query_id'], media_query['query_id']],
                   input_hashes=report['input_hashes'])
        verdicts = [f['verdict'] for f in report['findings']]
        self.agent('Verifier', 'compare_original_bytes', target='World Model planner', said='ordered XML, repeats, every file slot, history',
                   did=', '.join(f'{v} x{verdicts.count(v)}' for v in sorted(set(verdicts))) or 'no completed records', model='deterministic code')
        world.add(type='verification', key='verify', evidence=[report_hash, join_query['query_id'], objects_query['query_id']],
                  findings=len(report['findings']), coverage_complete=report['coverage']['complete'])
        for f in report['findings']:
            world.add(type='finding', key=f['finding_id'], evidence=f['evidence_ids'], verdict=f['verdict'], version_id=f['version_id'],
                      device_id=self.device_of.get(f['snapshot_id'], f['snapshot_id']), recovery_eligible=f['recovery_eligible'])

    # 5. Hypotheses tested against verified verdicts (code) ------------------------
    def _evaluate(self, graph):
        from .agents import CONFIRMS
        latest = {h['key']: h for h in graph['latest_hypotheses']}
        for key in graph['focus']:
            h = latest[key]
            s = self.suspicions[h['suspicion']]
            verdicts = sorted({f['verdict'] for f in self.report['findings']
                               if f['version_id'] == s['version_id'] and f['snapshot_id'] == s['source_id']}) or ['NOT_FOUND']
            status = ('inconclusive' if 'UNVERIFIABLE' in verdicts or verdicts == ['NOT_FOUND'] else
                      'confirmed' if set(verdicts) <= CONFIRMS[h['hypothesis']] else 'refuted')
            self.world.add(type='hypothesis', key=key, revision=h['revision'] + 1, evidence=h['evidence'],
                           **carry(h, 'verified_verdicts'),
                           status=status, verified_verdicts=verdicts)
            self.agent('Verifier', 'test_hypothesis', target='World Model planner', said=f"{key}: {h['hypothesis']}",
                       did=f"{status} by raw evidence ({', '.join(verdicts)})", model='deterministic code')
            if status == 'refuted':
                self.event('decision_changed', hypothesis=key, before=h['hypothesis'], after=verdicts,
                           evidence=h['evidence'][:8], note='Raw evidence overturned the investigator\'s hypothesis')

    # 6. Remediation: code limits the options, the advisor chooses -----------------
    def _remedy(self, graph):
        from .agents import permitted_remedies
        findings = {f['finding_id']: f for f in self.report['findings']}
        open_choice = []
        for fid in graph['focus']:
            allowed = permitted_remedies(findings[fid])
            if len(allowed) == 1:
                self.remedies[fid] = {'action': allowed[0], 'decided_by': 'code (only permitted action)', 'permitted': allowed}
                self.world.add(type='remedy', key=fid, evidence=findings[fid]['evidence_ids'], action=allowed[0], decided_by='code')
                self.agent('Code guard', 'single_permitted_action', target='Wipe gate', said=f"{fid} {findings[fid]['verdict']}",
                           did=allowed[0], model='deterministic code')
            else:
                open_choice.append(fid)
        if not open_choice:
            return
        payload = {'findings': [{'finding_id': fid, 'verdict': findings[fid]['verdict'], 'summary': findings[fid]['summary'],
                                 'media_filenames': findings[fid]['media_filenames'], 'permitted_actions': permitted_remedies(findings[fid])}
                                for fid in open_choice]}

        def check(value):
            got = [a.get('finding_id') for a in value.get('actions', [])]
            return [] if sorted(got) == sorted(open_choice) else ['choose one action for each finding_id: ' + ','.join(open_choice)]
        value, meta = self.ask(self.provider, 'advisor', payload, open_choice, check)
        for a in value['actions']:
            allowed = permitted_remedies(findings[a['finding_id']])
            action, guarded = a['action'], a['action'] not in allowed
            if guarded:
                action = 'manual_review' if 'manual_review' in allowed else allowed[0]
            self.remedies[a['finding_id']] = {'action': action, 'decided_by': self.engine(meta), 'permitted': allowed, 'code_guard': guarded}
            self.world.add(type='remedy', key=a['finding_id'], evidence=findings[a['finding_id']]['evidence_ids'], action=action,
                           decided_by=self.engine(meta), code_guard=guarded)
            self.agent('Remediation advisor', 'choose_permitted_action', target='Wipe gate', said=f"{a['finding_id']} {findings[a['finding_id']]['verdict']}",
                       did=action + (' (code guard replaced an unpermitted choice)' if guarded else ''), model=self.engine(meta),
                       fallback=bool(meta.get('fallback')))

    # 7. Wipe gate (code) ---------------------------------------------------------
    def _decide(self, graph):
        from .agents import wipe_gate
        self.decisions = wipe_gate(self.report, self.pack)
        for d in self.decisions:
            d['actions'] = {r['finding_id']: self.remedies.get(r['finding_id'], {'action': 'no_action'})['action'] for r in d['records']}
            self.world.add(type='device_decision', key=d['device_id'], evidence=[d['certificate_sha256']] + [r['finding_id'] for r in d['records']],
                           decision=d['decision'], certificate_sha256=d['certificate_sha256'])
            self.agent('Wipe gate', 'clear_device', target='Explainer', said=d['device_id'],
                       did=f"{d['decision']} (certificate {d['certificate_sha256'][:12]})", model='deterministic code')

    # 7b. Adversary: try to break every clearance (Nemotron raises, code answers) ----
    def _challenge(self, graph):
        from .agents import answer_objection, reissue
        decisions = {d['device_id']: d for d in self.decisions}
        focus = graph['focus']
        payload = {'devices': [{k: decisions[d][k] for k in ('device_id', 'decision', 'counts', 'records')} for d in focus]}

        def check(value):
            raised = {}
            for o in value.get('objections', []):
                raised.setdefault(o.get('device_id'), set()).add(o.get('objection'))
            return [f'raise at least one objection for {d}' for d in focus if not raised.get(d)]
        value, meta = self.ask(self.provider, 'adversary', payload, focus, check)
        by_device = {}
        for o in value['objections']:
            if o['device_id'] in decisions and o['objection'] not in by_device.setdefault(o['device_id'], {}):
                by_device[o['device_id']][o['objection']] = o.get('reason', '')
        for device in focus:
            d = decisions[device]
            open_ = []
            for objection in sorted(by_device.get(device, {})):
                self.agent('Adversary', 'raise_objection', target='Verifier', said=device, did=objection.replace('_', ' '),
                           model=self.engine(meta), fallback=bool(meta.get('fallback')))
                answered, detail = answer_objection(objection, d, self.pack, self.report)
                self.agent('Verifier', 'answer_objection', target='Wipe gate', said=f'{device} {objection}',
                           did=('answered: ' if answered else 'OPEN: ') + detail, model='deterministic code')
                if not answered:
                    open_.append(f'{objection}: {detail}')
            if open_:
                new = reissue(d, self.report, self.pack, 'HOLD', 'Adversary objection could not be answered: ' + '; '.join(open_))
                self.event('decision_changed', note='An adversarial objection was not answered, so the clearance was withdrawn',
                           before='SAFE_TO_WIPE', after='HOLD', hypothesis=device)
                self.decisions = [new if x['device_id'] == device else x for x in self.decisions]
                self.world.add(type='device_decision', key=device, revision=1, evidence=[new['certificate_sha256']], decision='HOLD',
                               certificate_sha256=new['certificate_sha256'])
            self.world.add(type='challenge', key=device, evidence=[d['certificate_sha256']], objections=len(by_device.get(device, {})),
                           open=len(open_), raised_by=self.engine(meta))

    # 8. Explainer: plain language, every token checked (Nemotron + code) ----------
    def _explain(self, graph):
        from .agents import allowed_tokens, citation_errors, template_explanation
        decisions = {d['device_id']: d for d in self.decisions}
        focus = graph['focus']
        payload = {'devices': [{k: decisions[d][k] for k in ('device_id', 'decision', 'reasons', 'counts', 'records')} for d in focus]}

        def check(value):
            errors = []
            got = {e.get('device_id'): e.get('text') for e in value.get('explanations', [])}
            if sorted(got) != sorted(focus):
                return ['explain each device_id exactly once: ' + ','.join(focus)]
            for d in focus:
                errors += [f'{d}: {e}' for e in citation_errors(got[d], decisions[d], allowed_tokens(decisions[d]))]
            return errors
        value, meta = self.ask(self.provider, 'explainer', payload, focus, check)
        for e in value['explanations']:
            text = e['text'] if not citation_errors(e['text'], decisions[e['device_id']], allowed_tokens(decisions[e['device_id']])) else template_explanation(decisions[e['device_id']])
            self.explanations[e['device_id']] = {'text': text, 'written_by': self.engine(meta), 'citations_checked': True}
            self.world.add(type='explanation', key=e['device_id'], evidence=[decisions[e['device_id']]['certificate_sha256']],
                           written_by=self.engine(meta))
            self.agent('Explainer', 'explain_decision', target='Coordinator', said=e['device_id'], did=text[:160],
                       model=self.engine(meta), fallback=bool(meta.get('fallback')))
