"""Single-user local SQLite ledger: immutable blobs, bounded jobs and output seals.

An OS lock grants one runner per store across processes. On lock acquisition,
leftover running jobs are explicitly interrupted rather than declared complete.
Cancellation is cooperative between bounded archive/XML/slot operations.
"""
import contextlib
import json
import os
import sqlite3
import threading
from pathlib import Path
from datetime import datetime, timezone
from .config import Settings
from .inventory import digest, inventory, read_archive, ImportRejected
from .models import RunManifest, RunRequest, RegisteredInput, JobStatus
from .snapshots import load_snapshot
from .reconcile import reconcile, RunCancelled, RunDeadline

ARTIFACTS = ('report.json', 'findings.json', 'receipts.json', 'events.jsonl')
_locks = {}
_guard = threading.Lock()


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')


class RunStore:
    def __init__(self, directory, settings=None):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db = self.directory / 'lastcopy.sqlite3'
        self.settings = settings or Settings.load()
        with _guard:
            self.lock = _locks.setdefault(str(self.directory), threading.Lock())
        with self.connect() as c:
            c.executescript('''
                CREATE TABLE IF NOT EXISTS inputs(id TEXT PRIMARY KEY, kind TEXT NOT NULL, sha TEXT NOT NULL, data BLOB NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs(run_id TEXT PRIMARY KEY, request BLOB NOT NULL, state TEXT NOT NULL,
                    cancel_requested INTEGER NOT NULL DEFAULT 0, error TEXT, outcome TEXT, hashes TEXT NOT NULL DEFAULT '{}');
                CREATE TABLE IF NOT EXISTS events(run_id TEXT NOT NULL, seq INTEGER NOT NULL, body BLOB NOT NULL, PRIMARY KEY(run_id,seq));
                CREATE TABLE IF NOT EXISTS artifacts(run_id TEXT NOT NULL, name TEXT NOT NULL, sha TEXT NOT NULL, data BLOB NOT NULL, PRIMARY KEY(run_id,name));
            ''')

    def connect(self):
        c = sqlite3.connect(self.db, timeout=10)
        c.execute('PRAGMA busy_timeout=10000')
        return c

    def register(self, kind, data):
        if kind not in ('device', 'server', 'manifest'):
            raise ValueError('Unsupported input kind')
        if not data or len(data) > self.settings.limit('MAX_UPLOAD_BYTES'):
            raise ImportRejected('Registration exceeds upload limit or is empty')
        if kind == 'device':
            inventory(data, self.settings)
        elif kind == 'manifest':
            if len(data) > 65536:
                raise ImportRejected('Run manifest exceeds 64 KiB')
            try:
                RunManifest.model_validate_json(data)
            except Exception:
                raise ImportRejected('Invalid RunManifest') from None
        else:
            files = read_archive(data, self.settings)
            if set(files) != {'server-snapshot.json', 'server-payload.zip'}:
                raise ImportRejected('Server registration requires server-snapshot.json and server-payload.zip only')
            load_snapshot(files['server-snapshot.json'], files['server-payload.zip'], self.settings)
        sha = digest(data)
        input_id = digest(kind.encode() + b'\0' + data)
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            total = c.execute('SELECT COALESCE(SUM(length(data)),0) FROM inputs').fetchone()[0]
            if total + len(data) > 536870912:
                raise ImportRejected('Local input store exceeds 512 MiB quota; use a separate configured store')
            c.execute('INSERT OR IGNORE INTO inputs VALUES(?,?,?,?)', (input_id, kind, sha, data))
        return RegisteredInput(input_id=input_id, kind=kind, sha256=sha)

    def input(self, input_id, kind):
        with self.connect() as c:
            row = c.execute('SELECT kind,sha,data FROM inputs WHERE id=?', (input_id,)).fetchone()
        if row is None or row[0] != kind:
            raise KeyError('Registered input not found or wrong kind')
        if digest(row[2]) != row[1] or digest(kind.encode() + b'\0' + row[2]) != input_id:
            raise ImportRejected('Registered source integrity check failed')
        return row[2]

    def enqueue(self, request: RunRequest):
        run = RunManifest.model_validate_json(self.input(request.manifest_id, 'manifest'))
        if self.settings.sample and run.mode != 'sample':
            raise ImportRejected('SAMPLE_MODE requires sample manifest')
        if len(set(request.device_input_ids)) != len(request.device_input_ids):
            raise ImportRejected('Duplicate registered device input')
        for input_id in request.device_input_ids:
            self.input(input_id, 'device')
        self.input(request.server_input_id, 'server')
        raw = encoded(request.model_dump())
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            old = c.execute('SELECT request FROM jobs WHERE run_id=?', (run.run_id,)).fetchone()
            if old:
                if old[0] != raw:
                    raise ValueError('Run ID already belongs to another request')
            else:
                if c.execute("SELECT COUNT(*) FROM jobs WHERE state IN ('queued','running')").fetchone()[0] >= 4:
                    raise ValueError('Run queue is full (maximum four active jobs)')
                if c.execute('SELECT COUNT(*) FROM jobs').fetchone()[0] >= 1000:
                    raise ValueError('Local ledger reached 1000 runs; use a separate configured store')
                c.execute("INSERT INTO jobs(run_id,request,state) VALUES(?,?,'queued')", (run.run_id, raw))
                self._event(c, run.run_id, 'queued', {'mode': run.mode})
        return self.get(run.run_id)

    @staticmethod
    def _event(c, run_id, kind, details):
        count = c.execute('SELECT COUNT(*) FROM events WHERE run_id=?', (run_id,)).fetchone()[0]
        if count >= 2000:
            raise ImportRejected('Run event limit exceeded')
        record = {'sequence': count + 1, 'run_id': run_id, 'event': kind,
                  'observed_at': datetime.now(timezone.utc).isoformat(), 'details': details}
        c.execute('INSERT INTO events VALUES(?,?,?)', (run_id, count + 1, encoded(record)))

    def get(self, run_id):
        with self.connect() as c:
            row = c.execute('SELECT state,error,outcome,hashes FROM jobs WHERE run_id=?', (run_id,)).fetchone()
        if row is None:
            raise KeyError('Run not found')
        return JobStatus(run_id=run_id, state=row[0], error=row[1], preservation_outcome=row[2], output_hashes=json.loads(row[3]))

    def cancel(self, run_id):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            row = c.execute('SELECT state FROM jobs WHERE run_id=?', (run_id,)).fetchone()
            if row is None:
                raise KeyError('Run not found')
            if row[0] in ('queued', 'running'):
                c.execute('UPDATE jobs SET cancel_requested=1,state=? WHERE run_id=?', ('cancelled' if row[0] == 'queued' else 'running', run_id))
                self._event(c, run_id, 'cancel_requested', {})
                if row[0] == 'queued':
                    self._event(c, run_id, 'cancelled', {})
        return self.get(run_id)

    def events(self, run_id):
        self.get(run_id)
        with self.connect() as c:
            return b''.join(row[0] for row in c.execute('SELECT body FROM events WHERE run_id=? ORDER BY seq', (run_id,)))

    def artifact(self, run_id, name):
        if name not in ARTIFACTS:
            raise KeyError('Artifact not registered')
        with self.connect() as c:
            row = c.execute('SELECT sha,data FROM artifacts WHERE run_id=? AND name=?', (run_id, name)).fetchone()
        if row is None:
            raise KeyError('Artifact not found')
        if digest(row[1]) != row[0]:
            raise ImportRejected('Output integrity check failed')
        return row[1]

    @contextlib.contextmanager
    def lease(self):
        if not self.lock.acquire(blocking=False):
            yield False
            return
        file = None
        locked = False
        try:
            file = (self.directory / 'runner.lock').open('a+b')
            if file.tell() == 0:
                file.write(b'0')
                file.flush()
            file.seek(0)
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except OSError:
                pass
            yield locked
        finally:
            if file:
                if locked:
                    file.seek(0)
                    if os.name == 'nt':
                        import msvcrt
                        msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(file.fileno(), fcntl.LOCK_UN)
                file.close()
            self.lock.release()

    def drain(self):
        with self.lease() as acquired:
            if not acquired:
                return
            with self.connect() as c:
                c.execute('BEGIN IMMEDIATE')
                for (rid,) in c.execute("SELECT run_id FROM jobs WHERE state='running'").fetchall():
                    c.execute("UPDATE jobs SET state='interrupted',error='Previous runner stopped; no preservation result committed' WHERE run_id=?", (rid,))
                    self._event(c, rid, 'interrupted', {})
            for _ in range(4):
                with self.connect() as c:
                    c.execute('BEGIN IMMEDIATE')
                    row = c.execute("SELECT run_id,request FROM jobs WHERE state='queued' ORDER BY rowid LIMIT 1").fetchone()
                    if row is None:
                        return
                    rid, raw = row
                    c.execute("UPDATE jobs SET state='running' WHERE run_id=?", (rid,))
                    self._event(c, rid, 'running', {})
                self._execute(rid, raw)

    def recover_interrupted(self):
        """Startup audit only. Never auto-resume recovery writes or model calls."""
        with self.lease() as held:
            if not held: return
            with self.connect() as c:
                c.execute('BEGIN IMMEDIATE')
                for (rid,) in c.execute("SELECT run_id FROM jobs WHERE state='running'").fetchall():
                    c.execute("UPDATE jobs SET state='interrupted',error='Previous runner stopped; no preservation result committed' WHERE run_id=?",(rid,))
                    self._event(c,rid,'interrupted',{})

    def _execute(self, rid, raw):
        def cancelled():
            with self.connect() as c:
                return bool(c.execute('SELECT cancel_requested FROM jobs WHERE run_id=?', (rid,)).fetchone()[0])

        def progress(kind, detail):
            with self.connect() as c:
                self._event(c, rid, kind, detail)

        try:
            request = RunRequest.model_validate_json(raw)
            manifest_raw = self.input(request.manifest_id, 'manifest')
            run = RunManifest.model_validate_json(manifest_raw)
            inputs = [self.input(i, 'device') for i in request.device_input_ids]
            bundle = read_archive(self.input(request.server_input_id, 'server'), self.settings)
            report = reconcile(run, inputs, bundle['server-snapshot.json'], bundle['server-payload.zip'], self.settings,
                               cancel=cancelled, event=progress)
            report.input_hashes['registration:manifest'] = digest(manifest_raw)
            report.input_hashes['registration:server-bundle'] = digest(self.input(request.server_input_id, 'server'))
            # Re-read all registered sources before publication; immutability is checked, never assumed.
            for input_id, kind in [(request.manifest_id, 'manifest'), (request.server_input_id, 'server'),
                                   *((i, 'device') for i in request.device_input_ids)]:
                self.input(input_id, kind)
            artifacts = {'report.json': encoded(report.model_dump(mode='json')),
                         'findings.json': encoded([f.model_dump(mode='json') for f in report.findings]),
                         'receipts.json': encoded([r.model_dump(mode='json') for r in report.receipts])}
            with self.connect() as c:
                c.execute('BEGIN IMMEDIATE')
                if c.execute('SELECT cancel_requested FROM jobs WHERE run_id=?', (rid,)).fetchone()[0]:
                    raise RunCancelled()
                self._event(c, rid, 'completed', {'preservation_outcome': report.preservation_outcome, 'coverage_complete': report.coverage.complete})
                artifacts['events.jsonl'] = b''.join(r[0] for r in c.execute('SELECT body FROM events WHERE run_id=? ORDER BY seq', (rid,)))
                if sum(map(len, artifacts.values())) > 33554432:
                    raise ImportRejected('Run outputs exceed 32 MiB limit')
                hashes = {name: digest(data) for name, data in artifacts.items()}
                for name, data in artifacts.items():
                    c.execute('INSERT INTO artifacts VALUES(?,?,?,?)', (rid, name, hashes[name], data))
                c.execute("UPDATE jobs SET state='completed',outcome=?,hashes=? WHERE run_id=?", (report.preservation_outcome, json.dumps(hashes), rid))
        except Exception as error:
            state = 'cancelled' if isinstance(error, RunCancelled) else 'failed'
            # Imported content and arbitrary exception text never become diagnostics.
            message = ('Run cancelled' if state == 'cancelled' else 'Run exceeded wall-time limit' if isinstance(error, RunDeadline)
                       else str(error) if isinstance(error, ImportRejected) else 'Run failed validation or processing; no preservation result committed')
            with self.connect() as c:
                c.execute('UPDATE jobs SET state=?,error=? WHERE run_id=?', (state, message, rid))
                self._event(c, rid, state, {'reason': message})
