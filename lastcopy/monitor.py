"""Private export inbox -> durable bounded read-only checks. Never applies recovery.

Only operator-configured paths are read. Producers publish a .zip followed by
its .zip.ready.json seal. Original inputs are never moved, rewritten or deleted.
"""
import json
import time
import threading
import uuid
from pathlib import Path
from datetime import datetime,timezone
from itertools import islice
from .models import WatchReady,UIPrepareRequest,RunRequest
from .inventory import inventory,digest
from .store import RunStore,encoded
from .odk_recovery import configured_read_target


def stamp():return datetime.now(timezone.utc).isoformat()


class Monitor:
    def __init__(self,store):
        self.store=store
        with store.connect() as c:c.executescript('''
            CREATE TABLE IF NOT EXISTS watch_state(id TEXT PRIMARY KEY,enabled INTEGER NOT NULL DEFAULT 0,
                state TEXT NOT NULL DEFAULT 'paused',message TEXT NOT NULL DEFAULT 'Automatic checking is paused',
                due REAL NOT NULL DEFAULT 0,checks INTEGER NOT NULL DEFAULT 0,last_run TEXT,last_checked TEXT,heartbeat TEXT);
            CREATE TABLE IF NOT EXISTS watch_inputs(config TEXT,device TEXT,input_id TEXT,captured TEXT,PRIMARY KEY(config,device));
            CREATE TABLE IF NOT EXISTS watch_errors(config TEXT,filename TEXT,message TEXT,PRIMARY KEY(config,filename));
            CREATE TABLE IF NOT EXISTS watch_jobs(config TEXT,run_id TEXT PRIMARY KEY,state TEXT NOT NULL,source_ids BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS watch_events(seq INTEGER PRIMARY KEY AUTOINCREMENT,config TEXT,body BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS watch_rosters(id TEXT PRIMARY KEY,body BLOB NOT NULL);
        ''')

    def event(self,key,kind,**details):
        with self.store.connect() as c:
            if c.execute('SELECT COUNT(*) FROM watch_events').fetchone()[0]>=5000:raise ValueError('Monitor event budget reached')
            c.execute('INSERT INTO watch_events(config,body) VALUES(?,?)',(key,encoded({'event':kind,'at':stamp(),'details':details})))

    def config(self,roster_override=None):
        v=self.store.settings.values
        if self.store.settings.sample or not v.get('LASTCOPY_WATCH_INBOX'):raise ValueError('Automatic checking is not configured in this mode')
        root=Path(v['LASTCOPY_WATCH_INBOX']).absolute()
        if not root.is_dir() or root.is_symlink() or root.is_junction():raise ValueError('Configured export inbox must be an existing ordinary directory')
        target=configured_read_target(self.store.settings)
        roster_key=digest(encoded({'inbox':str(root.resolve()),'target':target}))
        with self.store.connect() as c:saved=c.execute('SELECT body FROM watch_rosters WHERE id=?',(roster_key,)).fetchone()
        roster=roster_override if roster_override is not None else json.loads(saved[0] if saved else v.get('LASTCOPY_WATCH_DEVICE_IDS','[]'))
        if not isinstance(roster,list) or not 1<=len(roster)<=8 or any(not isinstance(i,str) or not i or len(i)>512 for i in roster) or len(set(roster))!=len(roster):
            raise ValueError('Configure an explicit roster of one to eight unique device IDs')
        interval=int(v.get('LASTCOPY_WATCH_INTERVAL_SECONDS','60'));budget=int(v.get('LASTCOPY_WATCH_MAX_CHECKS','120'))
        if not 30<=interval<=3600 or not 1<=budget<=1000:raise ValueError('Automatic interval must be 30–3600 seconds and budget 1–1000 checks')
        identity=digest(encoded({'inbox':str(root.resolve()),'roster':roster,'target':target}))
        with self.store.connect() as c:c.execute('INSERT OR IGNORE INTO watch_state(id) VALUES(?)',(identity,))
        return identity,root,roster,interval,budget,target

    def accept_sources(self,body):
        if len(set(body.device_input_ids))!=len(body.device_input_ids):raise ValueError('Duplicate source input')
        key,root,roster,interval,budget,target=self.config(body.expected_device_ids)
        additions=[]
        for iid in body.device_input_ids:
            inv=inventory(self.store.input(iid,'device'),self.store.settings);m=inv.manifest
            if m.device_id not in roster or any(v.form_id!=target['form_id'] for v in inv.versions):raise ValueError('Device or form is outside the selected roster and configured read scope')
            if m.captured_at=='unknown':raise ValueError('Automatic sources require a known capture time; check this export manually')
            if any(a[0]==m.device_id for a in additions):raise ValueError('Select only one current export per device')
            with self.store.connect() as c:old=c.execute('SELECT input_id,captured FROM watch_inputs WHERE config=? AND device=?',(key,m.device_id)).fetchone()
            if old and old[0]!=iid and m.captured_at<=datetime.fromisoformat(old[1]):raise ValueError('Older or ambiguous export requires manual review')
            additions.append((m.device_id,iid,m.captured_at.isoformat()))
        roster_key=digest(encoded({'inbox':str(root.resolve()),'target':target}))
        with self.store.connect() as c:
            c.execute('INSERT OR REPLACE INTO watch_rosters VALUES(?,?)',(roster_key,encoded(roster)))
            for device,iid,captured in additions:c.execute('INSERT OR REPLACE INTO watch_inputs VALUES(?,?,?,?)',(key,device,iid,captured))
        self.update(key,due=0)
        self.event(key,'reviewed_sources_selected',device_ids=[a[0] for a in additions],expected_devices=roster)
        return self.control('start')

    def update(self,key,**values):
        allowed={'enabled','state','message','due','checks','last_run','last_checked','heartbeat'}
        if not set(values)<=allowed:raise ValueError('Unknown monitor state field')
        with self.store.connect() as c:c.execute('UPDATE watch_state SET '+','.join(k+'=?' for k in values)+' WHERE id=?',(*values.values(),key))

    def row(self,key):
        with self.store.connect() as c:
            c.row_factory=__import__('sqlite3').Row
            return dict(c.execute('SELECT * FROM watch_state WHERE id=?',(key,)).fetchone())

    def status(self):
        from .device_transfer import DeviceTransfer
        transfer=DeviceTransfer(self.store).status()
        try:key,root,roster,interval,budget,target=self.config()
        except (ValueError,KeyError,TypeError):return {'configured':False,'state':'not_configured','message':'Automatic export checking is not configured. Manual checks remain available.','device_transfer':transfer}
        s=self.row(key)
        with self.store.connect() as c:
            devices=[r[0] for r in c.execute('SELECT device FROM watch_inputs WHERE config=? ORDER BY device',(key,))]
            errors=[r[0]+': '+r[1] for r in c.execute('SELECT filename,message FROM watch_errors WHERE config=? LIMIT 10',(key,))]
        state=s['state'];message=s['message']
        if s['enabled'] and (not s['heartbeat'] or (datetime.now(timezone.utc)-datetime.fromisoformat(s['heartbeat'])).total_seconds()>150):
            state='waiting_for_worker';message='Waiting for the local automatic checker. Saved results are not fresh until another server capture completes.'
        return {'configured':True,'enabled':bool(s['enabled']),'state':state,'message':message,
            'project_id':target['project_id'],'form_id':target['form_id'],'expected_devices':roster,'received_devices':devices,
            'interval_seconds':interval,'checks_completed':s['checks'],'max_checks':budget,'last_run_id':s['last_run'],
            'last_checked_at':s['last_checked'],'heartbeat_at':s['heartbeat'],'input_errors':errors,'recovery_writes':0,'device_transfer':transfer}

    def control(self,action):
        key,*_=self.config()
        if action not in ('start','pause','check_now'):raise ValueError('Unknown automatic check action')
        if action=='pause':self.update(key,enabled=0,state='paused',message='Paused. A capture already in progress may finish; no further check will start.')
        else:self.update(key,enabled=1,due=0,state='waiting_for_worker',message='Waiting for the local automatic checker')
        self.event(key,'control',action=action)
        return self.status()

    def ingest(self,key,root,roster):
        entries=list(islice(root.iterdir(),101))
        if len(entries)>100:raise ValueError('Export inbox exceeds 100-file limit; move old exports to a separate archive yourself')
        changed=False
        for ready in sorted(p for p in entries if p.name.endswith('.zip.ready.json')):
            name=ready.name[:-11]  # strip .ready.json, retaining .zip
            p=root/name
            try:
                if ready.is_symlink() or p.is_symlink() or ready.is_junction() or p.is_junction() or p.resolve().parent!=root.resolve():raise ValueError('Linked export files are not accepted')
                with ready.open('rb') as f:seal=WatchReady.model_validate_json(f.read(4097))
                with p.open('rb') as f:data=f.read(self.store.settings.limit('MAX_UPLOAD_BYTES')+1)
                if len(data)!=seal.bytes or digest(data)!=seal.sha256:raise ValueError('Export is incomplete or its seal does not match')
                inv=inventory(data,self.store.settings);m=inv.manifest
                if m.device_id not in roster:raise ValueError('Device is outside the expected roster')
                if m.captured_at=='unknown':raise ValueError('Capture time is unknown; select this source manually')
                target=configured_read_target(self.store.settings)
                if any(v.form_id!=target['form_id'] for v in inv.versions):raise ValueError('Export form does not match configured read scope')
                captured=m.captured_at.isoformat()
                with self.store.connect() as c:old=c.execute('SELECT input_id,captured FROM watch_inputs WHERE config=? AND device=?',(key,m.device_id)).fetchone()
                registered=self.store.register('device',data)
                if old and old[0]==registered.input_id:
                    with self.store.connect() as c:c.execute('DELETE FROM watch_errors WHERE config=? AND filename=?',(key,ready.name))
                    continue
                if old and m.captured_at<=datetime.fromisoformat(old[1]):raise ValueError('Older or ambiguous same-time export retained for manual review')
                with self.store.connect() as c:
                    c.execute('INSERT OR REPLACE INTO watch_inputs VALUES(?,?,?,?)',(key,m.device_id,registered.input_id,captured))
                    c.execute('DELETE FROM watch_errors WHERE config=? AND filename=?',(key,ready.name))
                changed=True
                self.event(key,'export_registered',device_id=m.device_id,input_id=registered.input_id,sha256=registered.sha256)
            except (ValueError,KeyError,OSError) as e:
                # Only code-owned messages, never a raw provider response or credential.
                message=str(e) if isinstance(e,ValueError) and type(e) is ValueError else 'Could not validate this sealed export'
                with self.store.connect() as c:c.execute('INSERT OR REPLACE INTO watch_errors VALUES(?,?,?)',(key,ready.name,message[:180]))
        return changed

    def tick(self,now=None):
        now=time.time() if now is None else now
        key,root,roster,interval,budget,target=self.config()
        # Distinct OS lease serializes monitors without taking the comparator lease.
        with RunStore(self.store.directory/'watch-lease',self.store.settings).lease() as held:
            if not held:return
            s=self.row(key)
            if not s['enabled']:return
            self.update(key,heartbeat=stamp())
            try:
                if s['state']=='error' and now<s['due']:return
                changed=self.ingest(key,root,roster)
                with self.store.connect() as c:
                    inputs=dict(c.execute('SELECT device,input_id FROM watch_inputs WHERE config=?',(key,)))
                    pending=c.execute("SELECT run_id,source_ids FROM watch_jobs WHERE config=? AND state='pending' ORDER BY rowid LIMIT 1",(key,)).fetchone()
                if not inputs:self.update(key,state='waiting_for_exports',message='Waiting for a finished device export and its integrity seal');return
                if s['checks']>=budget:self.update(key,state='budget_reached',message='Automatic check budget reached. Review saved results and configure the next session.');return
                if not pending and not changed and now<s['due']:return
                if not self.row(key)['enabled']:return
                if pending:rid,raw=pending;ids=json.loads(raw)
                else:
                    ids=[inputs[d] for d in roster if d in inputs];rid='watch-'+str(uuid.uuid4())
                    with self.store.connect() as c:c.execute('INSERT INTO watch_jobs VALUES(?,?,?,?)',(key,rid,'pending',encoded(ids)))
                    self.event(key,'check_intent',run_id=rid,input_ids=ids)
                self.update(key,state='checking',message='Reading fresh server XML, versions and files',heartbeat=stamp())
                from .ui import Workspace
                ws=Workspace(self.store)
                try:meta=ws.metadata(rid)
                except KeyError:
                    meta=ws.prepare(UIPrepareRequest(device_input_ids=ids,expected_device_ids=roster,source='connection',confirm_scope=True),run_id=rid,automatic=True)
                self.store.enqueue(RunRequest.model_validate(meta['request']))
                self.store.drain()
                state=self.store.get(rid)
                if state.state in ('queued','running'):
                    self.update(key,state='queued',message='Comparison is queued; its result is not complete');return
                with self.store.connect() as c:c.execute("UPDATE watch_jobs SET state=? WHERE run_id=?",(state.state,rid))
                self.event(key,'check_finished',run_id=rid,state=state.state,preservation_outcome=state.preservation_outcome)
                enabled=self.row(key)['enabled']
                message=('Last check completed. Watching for exports and the next scheduled server read.' if enabled else 'Last check completed. Automatic checking is paused.') if state.state=='completed' else 'Check did not complete. Open the saved run; no preservation success was inferred.'
                self.update(key,state=('watching' if state.state=='completed' else state.state) if enabled else 'paused',message=message,
                    checks=s['checks']+1,last_run=rid,last_checked=stamp(),due=now+interval,heartbeat=stamp())
            except Exception as e:
                # No failed capture becomes absence or a fallback Sample report.
                self.update(key,state='error',message='Automatic check could not finish. Check access, scope, input errors and local service availability. No recovery was applied.',checks=s['checks']+1,due=now+interval,heartbeat=stamp())
                self.event(key,'check_failed',exception_type=type(e).__name__,preservation_proof=False)


class MonitorService:
    def __init__(self,store):self.monitor=Monitor(store);self.stop=threading.Event();self.thread=None
    def start(self):
        try:self.monitor.config()
        except (ValueError,KeyError,TypeError):return
        def work():
            while not self.stop.is_set():
                try:self.monitor.tick()
                except Exception:pass  # status/config route exposes invalid settings; never invent success
                self.stop.wait(5)
        self.thread=threading.Thread(target=work,name='lastcopy-read-only-monitor',daemon=True);self.thread.start()
    def close(self):
        self.stop.set()
        if self.thread:self.thread.join(timeout=2)
