"""Persisted UI dispatch to the existing supervised Stage 3 worker. No provider fallback."""
import json
import os
import subprocess
import sys
import uuid
from .config import ROOT
from .inventory import digest,read_archive,inventory
from .models import RunManifest
from .store import encoded
from .store import RunStore
from .ui import Workspace


class UIInvestigation:
    def __init__(self,store):
        self.store=store
        with store.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS ui_investigations(run_id TEXT PRIMARY KEY, attempt_id TEXT NOT NULL, state TEXT NOT NULL, error TEXT)')

    def directory(self,rid,attempt): return self.store.directory/'investigations'/digest(rid.encode())/attempt

    def start(self,rid):
        ws=Workspace(self.store);meta=ws.metadata(rid)
        if self.store.settings.sample: raise ValueError('Sample mode never starts connected services')
        run=RunManifest.model_validate_json(self.store.input(meta['request']['manifest_id'],'manifest'))
        if run.mode!='connected' or meta.get('provenance')!='Authenticated configured Central capture':
            raise ValueError('Connected investigation requires a native capture from the configured synthetic test project')
        if self.store.get(rid).state!='completed': raise ValueError('Complete the deterministic comparison first')
        for i in meta['request']['device_input_ids']:
            if not inventory(self.store.input(i,'device'),self.store.settings).manifest.synthetic:
                raise ValueError('Connected publication supports explicitly synthetic test sources only')
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            old=c.execute('SELECT attempt_id FROM ui_investigations WHERE run_id=?',(rid,)).fetchone()
            if old: return self.status(rid)
            if c.execute("SELECT COUNT(*) FROM ui_investigations WHERE state IN ('queued','running')").fetchone()[0]>=1:
                raise ValueError('One connected investigation is already active; the deterministic comparison remains available')
            attempt=str(uuid.uuid4())
            c.execute("INSERT INTO ui_investigations VALUES(?,?,'queued',NULL)",(rid,attempt))
        try:
            env=dict(os.environ);env.update(self.store.settings.values)
            env.update(SAMPLE_MODE='false',LASTCOPY_DATA_DIR=str(self.store.directory))
            subprocess.Popen([sys.executable,'-m','scripts.ui_investigate','--run-id',rid,'--attempt-id',attempt],cwd=ROOT,
                env=env,
                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        except OSError:
            with self.store.connect() as c: c.execute("UPDATE ui_investigations SET state='failed',error='Could not start bounded investigation worker' WHERE run_id=?",(rid,))
        return self.status(rid)

    def unavailable(self,rid):
        with self.store.connect() as c:
            c.execute("INSERT OR IGNORE INTO ui_investigations VALUES(?,?,'failed','Connected investigation unavailable; deterministic results remain separate; no sample substitution')",(rid,str(uuid.uuid4())))

    def status(self,rid):
        with self.store.connect() as c: row=c.execute('SELECT attempt_id,state,error FROM ui_investigations WHERE run_id=?',(rid,)).fetchone()
        if not row: return None
        attempt,state,error=row;directory=self.directory(rid,attempt)
        if state=='running':
            lease=RunStore(directory.parent/('worker-lock-'+attempt),self.store.settings)
            with lease.lease() as free:
                if free:
                    # A dead supervisor cannot retain the OS lease. Do not
                    # repeat model/query operations or claim their completion.
                    with self.store.connect() as c:
                        c.execute("UPDATE ui_investigations SET state='interrupted',error='Investigation supervisor stopped; provider work is not automatically replayed' WHERE run_id=? AND attempt_id=? AND state='running'",(rid,attempt))
                    state,error='interrupted','Investigation supervisor stopped; provider work is not automatically replayed'
        events=[];result=None
        path=directory/'events.jsonl'
        if path.exists():
            if path.stat().st_size>2097152: raise ValueError('Investigation trace exceeds 2 MiB')
            try: events=[json.loads(l) for l in path.read_bytes().splitlines() if l]
            except ValueError: events=[]  # a partial final append is not a fabricated event
        finished=directory/'investigation.json'
        if state not in ('queued','running') and finished.exists():
            seals=json.loads((directory/'seals.json').read_bytes())
            if digest(finished.read_bytes())!=seals.get('investigation.json'): raise ValueError('Investigation result integrity failure')
            if path.exists() and digest(path.read_bytes())!=seals.get('events.jsonl'): raise ValueError('Investigation trace integrity failure')
            result=json.loads(finished.read_bytes())
        return {'state':state,'error':error,'attempt_id':attempt,'events':events,'result':result,
            'limits':{'steps':12,'critique_rounds':2,'seconds':300},
            'provenance':'Connected Stage 3 query/world/model worker, based on the original native synthetic capture; never a preservation override'}

    def cancel(self,rid):
        value=self.status(rid)
        if not value: raise KeyError('Investigation not found')
        if value['state'] in ('queued','running'):
            directory=self.directory(rid,value['attempt_id']);directory.mkdir(parents=True,exist_ok=True)
            (directory/'cancel').write_bytes(b'User requested cancellation\n')
        return value
