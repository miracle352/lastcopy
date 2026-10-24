"""Reviewed, durable, narrow synthetic recovery. The existing reconciler is authority.

No retry follows an unknown write without a new capture. SQLite commits intent
before transport; an OS lease serializes all recovery (stronger than per-record).
No remote transaction/CAS is available: concurrent external writers remain a
documented limitation and are detected by fresh version/byte checks and readback.
"""
import io
import json
import zipfile
import time
from datetime import datetime, timezone
from .inventory import inventory, read_archive, digest, parse_xml
from .models import RunManifest, ReconciliationReport, RecoveryPlan
from .reconcile import reconcile
from .store import RunStore, encoded


def archive(files):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 24, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    return out.getvalue()


class RecoveryEngine:
    def __init__(self, store, target, remote=None, *, allow_fixture=False):
        self.store, self.target, self.remote = store, target, remote
        # Test injection is explicit in Python only, never reachable via HTTP/CLI.
        self.allow_fixture = allow_fixture
        with store.connect() as c:
            c.executescript('''
                CREATE TABLE IF NOT EXISTS recovery_plans(id TEXT PRIMARY KEY, sha TEXT NOT NULL,
                    body BLOB NOT NULL, bundle BLOB NOT NULL, bundle_sha TEXT NOT NULL, reviewed INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS recovery_attempts(plan_id TEXT NOT NULL, seq INTEGER NOT NULL,
                    body BLOB NOT NULL, sha TEXT NOT NULL, PRIMARY KEY(plan_id,seq));
                CREATE TABLE IF NOT EXISTS recovery_results(plan_id TEXT PRIMARY KEY, body BLOB NOT NULL, sha TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS recovery_result_revisions(sha TEXT PRIMARY KEY, plan_id TEXT NOT NULL, body BLOB NOT NULL);
                CREATE TABLE IF NOT EXISTS recovery_captures(sha TEXT PRIMARY KEY, body BLOB NOT NULL);
            ''')

    def environment(self):
        if self.store.settings.sample:
            return {'base_url':'offline-sample','central_version':'not applicable',
                'dedicated_test_project':False,'project_name':None}
        values = self.store.settings.values
        return {'base_url':values.get('ODK_BASE_URL','offline-fixture' if self.allow_fixture else 'offline-sample'),
            'central_version':values.get('ODK_CENTRAL_VERSION','unavailable'),
            'dedicated_test_project':values.get('ODK_TEST_PROJECT')=='true',
            'project_name':values.get('ODK_RECOVERY_PROJECT_NAME','LastCopy synthetic Stage 4 recovery')
                if values.get('ODK_RECOVERY_PROJECT_ID') else None}

    def context(self, run_id):
        report = ReconciliationReport.model_validate_json(self.store.artifact(run_id, 'report.json'))
        with self.store.connect() as c:
            row = c.execute('SELECT request FROM jobs WHERE run_id=? AND state=\'completed\'', (run_id,)).fetchone()
        if row is None: raise ValueError('Run must be completed')
        req = json.loads(row[0])
        run = RunManifest.model_validate_json(self.store.input(req['manifest_id'], 'manifest'))
        devices = [self.store.input(i, 'device') for i in req['device_input_ids']]
        if self.target is None and self.store.settings.sample:
            self.target = run.destination.model_dump()
        if run.destination.model_dump() != self.target:
            raise ValueError('Run target differs from configured test environment')
        return run, devices, report

    def stage(self, run_id, finding_id):
        run, devices, report = self.context(run_id)
        matches = [f for f in report.findings if f.finding_id == finding_id]
        if len(matches) != 1: raise ValueError('Finding does not resolve uniquely')
        f = matches[0]
        if not f.recovery_eligible or f.verdict not in ('MISSING_SUBMISSION', 'MISSING_ATTACHMENT'):
            raise ValueError('Finding is not eligible for automatic recovery')
        if report.coverage.missing_devices or any(x != 'Required record or attachment readback absent' for x in report.coverage.limitations):
            raise ValueError('Incomplete source coverage prevents automatic recovery')
        source = []
        for raw in devices:
            inv = inventory(raw, self.store.settings)
            if not inv.manifest.synthetic: raise ValueError('Only dedicated synthetic sources are supported')
            for v in inv.versions:
                if v.snapshot_id == f.snapshot_id and v.version_id == f.version_id:
                    source.append((inv, v, read_archive(raw, self.store.settings)))
        if len(source) != 1: raise ValueError('Source mapping is ambiguous')
        inv, v, files = source[0]
        if v.limitations or v.completion_status != 'complete' or v.deprecated_id or v.logical_submission_id != v.version_id:
            raise ValueError('Completion, original XForm, source media or edit-chain requirements not met')
        if f.current_version_id not in (None, v.version_id):
            raise ValueError('Historical attachment writes are unsupported')
        required = {v.xml_path: files[v.xml_path], 'device-manifest.json':files['device-manifest.json']}
        for definition in inv.manifest.form_definitions:
            required[definition.xml_path] = files[definition.xml_path]
        media = {}
        for m in v.media:
            if m.sha256 is None or m.archive_path not in files: raise ValueError('Required source media absent')
            if m.filename in media and media[m.filename] != m.archive_path:
                raise ValueError('Ambiguous attachment source')
            media[m.filename] = m.archive_path
            required[m.archive_path] = files[m.archive_path]
        selected = sorted(media) if f.verdict == 'MISSING_SUBMISSION' else sorted(set(f.media_filenames))
        if not set(selected) <= set(media) or (f.verdict == 'MISSING_ATTACHMENT' and not selected):
            raise ValueError('Missing attachment does not resolve to source bytes')
        core = {'schema_version':1, 'run_id':run_id, 'finding_id':finding_id, 'target':self.target,
                'environment':self.environment(),
                'mode':run.mode, 'snapshot_id':f.snapshot_id, 'logical_submission_id':v.logical_submission_id,
                'version_id':v.version_id, 'form_version':v.form_version,
                'operation':'create_missing_submission' if f.verdict == 'MISSING_SUBMISSION' else 'restore_missing_media',
                'xml_path':v.xml_path, 'media_paths':media, 'media_filenames':selected,
                'form_paths':[d.xml_path for d in inv.manifest.form_definitions],
                'source_hashes':{k:digest(b) for k,b in required.items()},
                'source_archive_hashes':{digest(b):len(b) for b in devices},
                'evidence_ids':f.evidence_ids, 'expected_current_version':f.current_version_id,
                'before_verdict':f.verdict,
                'preconditions':['Explicit review of this exact plan and configured target',
                    'Fresh authenticated scope, version metadata, original XML and media readback before every write',
                    'No current version change, conflicting answers or conflicting accessible attachment bytes',
                    'No historical writes, deletion, clearing, identifier replacement or inferred completion'],
                'limitations':['Central provides no atomic compare-and-swap for attachment POST; use an isolated test project without concurrent external writers']}
        sha = digest(encoded(core))
        plan = dict(core, plan_id=sha, plan_sha256=sha)
        RecoveryPlan.model_validate(plan)
        bundle_files = {'files/'+k:b for k,b in required.items()}
        bundle_files.update({'operation.json':encoded(plan), 'evidence/report-before.json':report.model_dump_json(indent=2).encode(),
            'INSTRUCTIONS.txt':b'Review operation.json and its exact configured target. Keep sources unchanged.\nUse LastCopy review then Apply; never upload manually on a 409 or replace instance IDs.\nSample bundles are offline evidence, not live recovery authorization.\nApply re-reads versions/XML/media and verifies fresh readback with the existing reconciler.\nConflicts and unsupported history require manual review.\n'})
        bundle = archive(bundle_files)
        read_archive(bundle, self.store.settings)  # enforce same archive limits before persisting
        with self.store.connect() as c:
            if c.execute('SELECT COUNT(*) FROM recovery_plans').fetchone()[0] >= 1000:
                raise ValueError('Recovery plan limit reached')
            if c.execute('SELECT COALESCE(SUM(length(bundle)),0) FROM recovery_plans').fetchone()[0]+len(bundle)>134217728:
                raise ValueError('Recovery bundle store exceeds 128 MiB quota')
            c.execute('INSERT OR IGNORE INTO recovery_plans(id,sha,body,bundle,bundle_sha) VALUES(?,?,?,?,?)',
                      (sha, sha, encoded(plan), bundle, digest(bundle)))
        return plan

    def get(self, plan_id):
        with self.store.connect() as c:
            row = c.execute('SELECT body,sha FROM recovery_plans WHERE id=?', (plan_id,)).fetchone()
        if row is None: raise KeyError('Recovery plan not found')
        plan = json.loads(row[0]); core = {k:v for k,v in plan.items() if k not in ('plan_id','plan_sha256')}
        RecoveryPlan.model_validate(plan)
        if digest(encoded(core)) != row[1] or plan_id != row[1] or plan['plan_sha256'] != row[1]:
            raise ValueError('Recovery plan integrity failure')
        if self.target is None and self.store.settings.sample: self.target = plan['target']
        return plan

    def bundle(self, plan_id):
        self.get(plan_id)
        with self.store.connect() as c:
            row = c.execute('SELECT bundle,bundle_sha FROM recovery_plans WHERE id=?', (plan_id,)).fetchone()
        if digest(row[0]) != row[1]: raise ValueError('Recovery bundle integrity failure')
        return row[0]

    def review(self, plan_id, plan_sha256, target):
        plan = self.get(plan_id)
        if plan_sha256 != plan['plan_sha256'] or target != plan['target'] or target != self.target:
            raise ValueError('Review hash/target differs from configured plan')
        if plan['environment'] != self.environment(): raise ValueError('Configured target origin/version changed since staging')
        self.context(plan['run_id'])
        with self.store.connect() as c:
            c.execute('UPDATE recovery_plans SET reviewed=1 WHERE id=?', (plan_id,))
        self.event(plan_id, 'reviewed', {'plan_sha256':plan_sha256, 'target':target})
        return {'plan_id':plan_id, 'state':'reviewed', 'target':target}

    def event(self, plan_id, state, details):
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            count = c.execute('SELECT COUNT(*) FROM recovery_attempts WHERE plan_id=?', (plan_id,)).fetchone()[0]
            if count >= 500: raise ValueError('Recovery attempt limit reached')
            body = encoded({'sequence':count+1, 'plan_id':plan_id, 'state':state,
                'at':datetime.now(timezone.utc).isoformat(), 'details':details})
            c.execute('INSERT INTO recovery_attempts VALUES(?,?,?,?)', (plan_id,count+1,body,digest(body)))

    def events(self, plan_id):
        self.get(plan_id)
        with self.store.connect() as c:
            rows = c.execute('SELECT body,sha FROM recovery_attempts WHERE plan_id=? ORDER BY seq', (plan_id,)).fetchall()
        if any(digest(b) != sha for b,sha in rows): raise ValueError('Attempt integrity failure')
        return b''.join(b for b,_ in rows)

    def result(self, plan_id):
        self.get(plan_id)
        with self.store.connect() as c:
            row = c.execute('SELECT body,sha FROM recovery_results WHERE plan_id=?',(plan_id,)).fetchone()
        if not row:
            attempted = any(json.loads(line)['state']=='write_intent' for line in self.events(plan_id).splitlines())
            return {'plan_id':plan_id,'state':'pending_readback' if attempted else 'not_applied','events_available':True}
        if digest(row[0]) != row[1]: raise ValueError('Recovery result integrity failure')
        return json.loads(row[0])

    def evidence(self, plan_id, sha):
        result = self.result(plan_id)
        hashes = [h for pair in result.get('capture_hashes',[]) for h in pair]
        for line in self.events(plan_id).splitlines():
            hashes.extend(json.loads(line)['details'].get('capture_hashes',[]))
        if sha not in hashes: raise KeyError('Evidence outside this plan')
        with self.store.connect() as c:
            row = c.execute('SELECT body FROM recovery_captures WHERE sha=?',(sha,)).fetchone()
        if not row or digest(row[0]) != sha: raise ValueError('Capture integrity failure')
        return row[0]

    def recheck(self,plan_id):
        """Read-only UI checkpoint; never retries a write after a reload/timeout."""
        if self.store.settings.sample: raise ValueError('Sample mode cannot read a live server')
        plan=self.get(plan_id)
        if plan['target']!=self.target or plan['environment']!=self.environment(): raise ValueError('Configured target changed')
        run,devices,_=self.context(plan['run_id'])
        report,_,_,seals=self.capture(run,devices)
        f=self.finding(report,plan)
        unchanged=f['current_version_id'] in (plan['expected_current_version'],plan['version_id'])
        coverage_ok=not report['coverage']['missing_devices'] and all(
            x=='Required record or attachment readback absent' for x in report['coverage']['limitations'])
        checked={'checked_at':datetime.now(timezone.utc).isoformat(),'capture_hashes':seals,'report':report,
            'state':'preserved' if unchanged and f['verdict'] in ('PRESERVED','EXPORT_VIEW_ONLY') else 'ready' if
                coverage_ok and f['recovery_eligible'] and f['current_version_id']==plan['expected_current_version'] else 'blocked',
            'writes':0}
        self.event(plan_id,'ui_readback',checked)
        return checked

    def capture(self, run, devices):
        envelope, payload = self.remote.capture(run)
        # Persist raw capture objects before comparison; sources remain immutable.
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            used = c.execute('SELECT COALESCE(SUM(length(body)),0) FROM recovery_captures').fetchone()[0]
            if used+len(envelope)+len(payload)>536870912: raise ValueError('Recovery capture store exceeds 512 MiB quota')
            for b in (envelope,payload):
                c.execute('INSERT OR IGNORE INTO recovery_captures VALUES(?,?)', (digest(b),b))
        snap = json.loads(envelope)
        fresh = run.model_copy(update={'source_snapshot_ids':[inventory(b,self.store.settings).manifest.snapshot_id for b in devices]+[snap['snapshot_id']]})
        report = reconcile(fresh, devices, envelope, payload, self.store.settings).model_dump(mode='json')
        return report, snap, read_archive(payload, self.store.settings), [digest(envelope), digest(payload)]

    @staticmethod
    def finding(report, plan):
        matches = [f for f in report['findings'] if f['snapshot_id']==plan['snapshot_id'] and f['version_id']==plan['version_id']]
        if len(matches) != 1: raise ValueError('Fresh finding is ambiguous')
        return matches[0]

    def apply(self, plan_id):
        deadline = time.monotonic()+300
        if self.store.settings.sample: raise ValueError('SAMPLE_MODE never applies or contacts external services')
        plan = self.get(plan_id)
        if plan['target'] != self.target: raise ValueError('Configured target changed')
        if plan['environment'] != self.environment(): raise ValueError('Configured target origin/version changed since review')
        if plan['mode'] != 'connected' and not self.allow_fixture: raise ValueError('Only connected plans may Apply')
        if self.remote is None: raise ValueError('No configured Central transport')
        self.remote.apply_deadline = deadline
        with self.store.connect() as c:
            reviewed = c.execute('SELECT reviewed FROM recovery_plans WHERE id=?', (plan_id,)).fetchone()[0]
        if not reviewed: raise ValueError('Explicit plan review is required')
        # A separate OS lock avoids interfering with the run worker's lease/state.
        lease = RunStore(self.store.directory / 'recovery-lock', self.store.settings)
        with lease.lease() as acquired:
            if not acquired: raise ValueError('Another recovery is active; resume after it completes')
            run, devices, before = self.context(plan['run_id'])
            source_files = {}
            for raw in devices:
                inv = inventory(raw,self.store.settings)
                if inv.manifest.snapshot_id == plan['snapshot_id']: source_files = read_archive(raw,self.store.settings)
            if {digest(b):len(b) for b in devices} != plan['source_archive_hashes'] or any(digest(source_files[k])!=sha for k,sha in plan['source_hashes'].items()):
                raise ValueError('Original source hash changed')
            with self.store.connect() as c:
                old = c.execute('SELECT body,sha FROM recovery_results WHERE plan_id=?', (plan_id,)).fetchone()
            if old:
                if digest(old[0]) != old[1]: raise ValueError('Recovery result integrity failure')
                if json.loads(old[0])['state'] == 'verified': return json.loads(old[0])
            captures, write_receipts = [], []
            try:
                after, snap, raw, seals = self.capture(run,devices); captures.append(seals)
                current = self.finding(after,plan)
                ops = [None] if plan['operation']=='create_missing_submission' else plan['media_filenames']
                for filename in ops:
                    if time.monotonic() >= deadline: raise ValueError('Apply wall-time budget exceeded; resume with readback')
                    # Each write uses new original XML/version/slot bytes, including
                    # after process restart and after every preceding write.
                    after,snap,raw,seals = self.capture(run,devices); captures.append(seals)
                    current = self.finding(after,plan)
                    if after['coverage']['missing_devices'] or any(x != 'Required record or attachment readback absent' for x in after['coverage']['limitations']):
                        raise ValueError('Fresh capture/source coverage is incomplete')
                    if current['current_version_id'] != plan['expected_current_version'] and not (
                        plan['expected_current_version'] is None and current['current_version_id'] == plan['version_id']
                        and current['verdict'] in ('PRESERVED','EXPORT_VIEW_ONLY')):
                        raise ValueError('Target version changed since review')
                    if current['verdict'] in ('PRESERVED','EXPORT_VIEW_ONLY'): break
                    if current['verdict'] not in ('MISSING_SUBMISSION','MISSING_ATTACHMENT') or not current['recovery_eligible']:
                        raise ValueError('Fresh evidence is conflicting or unverifiable')
                    if current['current_version_id'] != plan['expected_current_version']:
                        # A lost create acknowledgement may now have the original
                        # version plus missing media. It requires a newly reviewed plan.
                        raise ValueError('Target version changed since review')
                    if filename is None and current['verdict'] != 'MISSING_SUBMISSION':
                        raise ValueError('Target is no longer absent; review a new plan')
                    if filename is not None:
                        if current['verdict'] != 'MISSING_ATTACHMENT': raise ValueError('Target missing or changed')
                        if filename not in current['media_filenames']: continue
                    if not self.allow_fixture:
                        from .xml_compare import compare_xml
                        form_receipts = [r for r in snap['receipts'] if r['request_scope'].endswith('/'+self.target['form_id']+'.xml')]
                        if len(form_receipts) != 1: raise ValueError('Current original XForm readback unavailable')
                        form = raw[form_receipts[0]['source_file']]
                        definitions = [source_files[k] for k in plan['form_paths']]
                        if not any(compare_xml(f,form,self.store.settings)['equal'] for f in definitions):
                            raise ValueError('Target original XForm changed or differs from source')
                    self.event(plan_id,'write_intent',{'filename':filename, 'capture_hashes':seals,
                        'expected_version':plan['expected_current_version'], 'source_hashes':plan['source_hashes']})
                    receipt = self.remote.write(plan,source_files,filename)
                    # If the process dies here, durable intent survives; next Apply
                    # starts with fresh readback and never assumes that POST failed.
                    self.event(plan_id,'attempt_result',receipt); write_receipts.append(receipt)
                after,snap,raw,seals = self.capture(run,devices); captures.append(seals)
                current = self.finding(after,plan)
                state = 'verified' if current['verdict'] in ('PRESERVED','EXPORT_VIEW_ONLY') else 'with_gaps'
                error = None
                if current['current_version_id'] not in (plan['version_id'],plan['expected_current_version']):
                    state = 'blocked'
                    error = 'Target version changed during readback; review required'
            except Exception as exc:
                # No automatic transport retry. Unknown outcomes remain resumable.
                state, error = 'blocked', type(exc).__name__ + ': ' + str(exc)[:240]
                self.event(plan_id,'readback_or_precondition_failed',{'error':error})
                if 'after' not in locals(): after = None
            _, fresh_devices, _ = self.context(plan['run_id'])
            unchanged = ({digest(b):len(b) for b in fresh_devices} == plan['source_archive_hashes']
                and fresh_devices == devices)
            if not unchanged: raise ValueError('Source archive integrity failure after operation')
            prior = self.finding(before.model_dump(mode='json'),plan)
            final = self.finding(after,plan) if after else None
            preserved = final and final['verdict'] in ('PRESERVED','EXPORT_VIEW_ONLY')
            result = {'plan_id':plan_id,'state':state,'error':error,'target':self.target,
                'before':before.model_dump(mode='json'),'after':after,'capture_hashes':captures,
                'write_receipts':write_receipts,'source_hashes_verified':unchanged,
                'disappeared':[prior['verdict']] if preserved else [],
                'remaining':[] if preserved else [final['verdict'] if final else 'UNVERIFIABLE'],
                'new_conflicts':[final['verdict']] if final and final['verdict']=='CONTENT_CONFLICT' else [],
                'scope':'Only this operation; run completion and whole-source preservation remain separate'}
            def gaps(report):
                return {(f['snapshot_id'],f['version_id']):f['verdict'] for f in report['findings'] if f['preservation']!='preserved'}
            old_gaps = gaps(before.model_dump(mode='json'))
            new_gaps = gaps(after) if after else old_gaps
            result['run_delta'] = {
                'disappeared':[{'snapshot_id':k[0],'version_id':k[1],'verdict':v} for k,v in old_gaps.items() if k not in new_gaps],
                'remaining':[{'snapshot_id':k[0],'version_id':k[1],'verdict':v} for k,v in new_gaps.items()],
                'new_conflicts':[{'snapshot_id':k[0],'version_id':k[1],'verdict':v} for k,v in new_gaps.items() if v=='CONTENT_CONFLICT' and old_gaps.get(k)!=v]}
            body = encoded(result)
            with self.store.connect() as c:
                c.execute('INSERT OR IGNORE INTO recovery_result_revisions VALUES(?,?,?)',(digest(body),plan_id,body))
                c.execute('INSERT OR REPLACE INTO recovery_results VALUES(?,?,?)',(plan_id,body,digest(body)))
            self.event(plan_id,state,{'result_sha256':digest(body), 'source_hashes_verified':unchanged})
            return result
