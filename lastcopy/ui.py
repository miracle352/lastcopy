"""Single-user UI adapters over immutable registered inputs and existing engines.

No browser-supplied filesystem paths, credentials or target URLs. Sample readback
is a separate explicitly synthetic export, never an upload or live recovery.
"""
import json
import uuid
import sqlite3
from datetime import datetime,timezone
from .config import ROOT,Settings
from .inventory import inventory,read_archive,digest
from .models import RunManifest,RunRequest,UIPrepareRequest
from .store import RunStore,encoded
from .recovery import RecoveryEngine,archive
from .odk_recovery import configured_target,configured_read_target
from scripts.run import bundle_snapshot

CATALOG=[
    {'id':'media','title':'A missing attachment','description':'Check repeated file references and separate files containing identical bytes.'},
    {'id':'stranded','title':'Device records to reconcile','description':'Compare individual records when overall server totals can be misleading.'},
    {'id':'export','title':'An incomplete spreadsheet export','description':'Compare a tabular view with the retained original XML and repeated answers.'},
    {'id':'history','title':'An intentional server edit','description':'Check whether the original version is retained in history.'},
    {'id':'conflict','title':'Different answers under one version','description':'Investigate a same-version difference without overwriting either source.'}]


def new_id(): return 'check-'+str(uuid.uuid4())


class Workspace:
    def __init__(self,store):
        self.store=store
        with store.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS ui_runs(run_id TEXT PRIMARY KEY, body BLOB NOT NULL, sha TEXT NOT NULL)')
            c.execute('CREATE TABLE IF NOT EXISTS ui_imports(id TEXT PRIMARY KEY, body BLOB NOT NULL, sha TEXT NOT NULL)')

    def save_import(self,body):
        for i in body.device_input_ids: self.store.input(i,'device')
        if body.server_input_id: self.store.input(body.server_input_id,'server')
        sid=body.session_id or 'inputs-'+str(uuid.uuid4())
        raw=encoded(body.model_dump(exclude={'session_id'}))
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            if body.session_id and not c.execute('SELECT id FROM ui_imports WHERE id=?',(sid,)).fetchone(): raise KeyError('Saved inputs not found')
            if not body.session_id and c.execute('SELECT COUNT(*) FROM ui_imports').fetchone()[0]>=1000: raise ValueError('Saved input limit reached')
            c.execute('INSERT OR REPLACE INTO ui_imports VALUES(?,?,?)',(sid,raw,digest(raw)))
        return self.load_import(sid)

    def load_import(self,sid):
        with self.store.connect() as c: row=c.execute('SELECT body,sha FROM ui_imports WHERE id=?',(sid,)).fetchone()
        if not row: raise KeyError('Saved inputs not found')
        if digest(row[0])!=row[1]: raise ValueError('Saved input integrity failure')
        data=json.loads(row[0])
        return {'session_id':sid,'devices':[self.device_summary(i) for i in data['device_input_ids']],
            'roster':data['roster'],'source':data['source'],'server':self.server_summary(data['server_input_id']) if data['server_input_id'] else None,
            'captured_run_reference':data['captured_run_reference']}

    def metadata(self,rid):
        with self.store.connect() as c: row=c.execute('SELECT body,sha FROM ui_runs WHERE run_id=?',(rid,)).fetchone()
        if row:
            if digest(row[0])!=row[1]: raise ValueError('Saved UI metadata integrity failure')
            return json.loads(row[0])
        # CLI-created runs are first-class saved results too.
        with self.store.connect() as c: row=c.execute('SELECT request FROM jobs WHERE run_id=?',(rid,)).fetchone()
        if not row: raise KeyError('Run not found')
        return {'request':json.loads(row[0]),'parent_run_id':None,'sample_case':None,'captured_run_reference':None}

    def remember(self,run,request,**metadata):
        body=encoded({'request':request.model_dump(),**metadata})
        with self.store.connect() as c:
            if c.execute('SELECT COUNT(*) FROM ui_runs').fetchone()[0]>=1000: raise ValueError('Saved check limit reached')
            c.execute('INSERT INTO ui_runs VALUES(?,?,?)',(run.run_id,body,digest(body)))

    def device(self,data):
        registered=self.store.register('device',data)
        return self.device_summary(registered.input_id)

    def device_summary(self,input_id):
        data=self.store.input(input_id,'device')
        inv=inventory(data,self.store.settings)
        return {'input_id':input_id,'sha256':digest(data),'inventory':inv.model_dump(mode='json')}

    def server(self,data):
        registered=self.store.register('server',data)
        return self.server_summary(registered.input_id)

    def server_summary(self,input_id):
        data=self.store.input(input_id,'server')
        parts=read_archive(data,self.store.settings)
        snapshot=json.loads(parts['server-snapshot.json'])
        return {'input_id':input_id,'sha256':digest(data),'snapshot':{
            k:snapshot.get(k) for k in ('snapshot_id','connection_id','project_id','form_ids','captured_at','scope_complete','history_complete','synthetic')}}

    def draft(self,run,devices,server,**metadata):
        m=self.store.register('manifest',run.model_dump_json().encode())
        req=RunRequest(manifest_id=m.input_id,device_input_ids=devices,server_input_id=server)
        inventories=[inventory(self.store.input(i,'device'),self.store.settings) for i in devices]
        metadata={**metadata,'synthetic_source':any(i.manifest.synthetic for i in inventories)}
        self.remember(run,req,**metadata)
        return {'run_id':run.run_id,'request':req.model_dump(),'manifest':run.model_dump(mode='json'),
                'devices':[i.model_dump(mode='json') for i in inventories],**metadata}

    def sample(self,case,parent=None,*,run_id=None):
        if case not in [c['id'] for c in CATALOG]: raise KeyError('Unknown sample')
        from scripts.build_stage2_fixtures import example
        data=example(case)
        run=RunManifest.model_validate(dict(data['run'],run_id=run_id or new_id()))
        d=self.store.register('device',data['device'])
        s=self.store.register('server',bundle_snapshot(encoded(data['snapshot']),data['server']))
        return self.draft(run,[d.input_id],s.input_id,sample_case=case,parent_run_id=parent,
            captured_run_reference=None,provenance='Authored synthetic fixture; offline comparator; no model, SQL query or upload')

    def example(self,case):
        """One actual offline result per fixture/core revision, including concurrent opens."""
        if case not in [c['id'] for c in CATALOG]: raise KeyError('Unknown example')
        from scripts.build_stage2_fixtures import example
        data=example(case)
        fingerprint=digest(data['device']+data['server']+encoded(data['snapshot'])+b''.join(
            (ROOT/'lastcopy'/name).read_bytes() for name in ('reconcile.py','inventory.py','snapshots.py','models.py')))
        rid='example-'+fingerprint[:32]
        try: meta=self.metadata(rid)
        except KeyError:
            try: return self.sample(case,run_id=rid)
            except sqlite3.IntegrityError: pass  # another request registered this same immutable example
            meta=self.metadata(rid)
        req=meta['request'];run=RunManifest.model_validate_json(self.store.input(req['manifest_id'],'manifest'))
        return {'run_id':rid,'manifest':run.model_dump(mode='json'),
            'devices':[inventory(self.store.input(i,'device'),self.store.settings).model_dump(mode='json') for i in req['device_input_ids']],**meta}

    def connection(self):
        """Authenticate and read the configured scope; never write a field record."""
        from .odk_recovery import CentralRecovery
        at=datetime.now(timezone.utc).isoformat()
        result={'state':'not_configured','checked_at':at,'record_writes':0,'receipts':[],
            'message':'A live server connection has not been enabled. Examples are available separately.'}
        if self.store.settings.values.get('LASTCOPY_CONNECTION_ERROR')=='true':
            return dict(result,state='unavailable',message='The saved connection could not be validated. Review and save its scope again; your files and reports are unchanged.')
        if self.store.settings.sample or (self.store.settings.values.get('LASTCOPY_ACCOUNT_STORE')=='true' and
                not all(self.store.settings.values.get(k) for k in ('ODK_BASE_URL','ODK_EMAIL','ODK_PASSWORD'))):return result
        remote=None
        try:
            remote=CentralRecovery(self.store.settings,read_only=True)
            result.update(server_url=remote.base,project_id=remote.target['project_id'],form_id=remote.target['form_id'])
            remote.begin();remote.login()
            values=[]
            for path in (f"/v1/projects/{remote.target['project_id']}",remote.scope()):
                status,body=remote.request('GET',path)
                if status!=200:raise ValueError('Configured project or form is not accessible')
                values.append(json.loads(body))
                result['receipts'].append({'method':'GET','scope':path,'status':status,'sha256':digest(body)})
            project,form=values
            expected=self.store.settings.values.get('ODK_READ_PROJECT_NAME') if self.store.settings.values.get('ODK_READ_PROJECT_ID') else self.store.settings.values.get('ODK_RECOVERY_PROJECT_NAME','LastCopy synthetic Stage 4 recovery')
            if project.get('name')!=expected or form.get('xmlFormId')!=remote.target['form_id']:
                raise ValueError('Configured project or form identity changed')
            result.update(state='connected',project_name=project.get('name'),form_name=form.get('name'),
                dedicated_test_project=remote.target['environment']=='dedicated_synthetic_test',
                message='The configured ODK Central project and form were read successfully.')
        except (ValueError,KeyError,TypeError):
            result.update(state='unavailable',message='The configured project or form could not be verified. Check the server and its access settings; no records were changed.')
        except Exception:
            result.update(state='unavailable',message='ODK Central is not responding. Start the configured server, then check the connection again. No records were changed.')
        finally:
            if remote:remote.client.close()
        return result

    def prepare(self,body:UIPrepareRequest,*,run_id=None,automatic=False):
        if self.store.settings.sample: raise ValueError('This API is configured for Sample only. An operator must configure Connected mode to check imported captures.')
        if not body.confirm_scope: raise ValueError('Confirm the device roster and target scope before checking')
        if len(set(body.device_input_ids))!=len(body.device_input_ids) or len(set(body.expected_device_ids))!=len(body.expected_device_ids):
            raise ValueError('Duplicate device inputs or roster labels')
        sources=[inventory(self.store.input(i,'device'),self.store.settings) for i in body.device_input_ids]
        if body.source=='connection':
            target=configured_read_target(self.store.settings)
            mode='connected'; server_id=None
        else:
            if not body.server_input_id or not body.captured_run_reference: raise ValueError('A scoped server snapshot and captured-run reference are required')
            parts=read_archive(self.store.input(body.server_input_id,'server'),self.store.settings)
            snapshot=json.loads(parts['server-snapshot.json'])
            if len(snapshot['form_ids'])!=1: raise ValueError('One explicitly scoped form is supported per check')
            target={'connection_id':snapshot['connection_id'],'project_id':snapshot['project_id'],'form_id':snapshot['form_ids'][0],
                'environment':'dedicated_synthetic_test','mapping_provenance':{'origin':'coordinator_attestation','reference':'UI reviewed supplied snapshot scope'}}
            server_id=body.server_input_id; mode='replay'
        run=RunManifest(schema_version=1,run_id=run_id or new_id(),mode=mode,source_snapshot_ids=[s.manifest.snapshot_id for s in sources]+['pending-capture'],
            expected_device_ids=body.expected_device_ids,roster_provenance={'origin':'coordinator_attestation','reference':'Coordinator roster explicitly confirmed in UI'},destination=target)
        if body.source=='connection':
            from scripts.recover import capture_registered
            m=self.store.register('manifest',run.model_dump_json().encode())
            captured=capture_registered(self.store,m.input_id,body.device_input_ids,read_only=True)
            run=RunManifest.model_validate_json(self.store.input(captured['manifest_id'],'manifest'))
            server_id=captured['server_input_id']
        else:
            run=run.model_copy(update={'source_snapshot_ids':[s.manifest.snapshot_id for s in sources]+[snapshot['snapshot_id']]})
        return self.draft(run,body.device_input_ids,server_id,sample_case=None,parent_run_id=None,
            captured_run_reference=body.captured_run_reference,automatic_check=automatic,
            provenance=('Automatic comparison; fresh authenticated Central capture; no assisted provider calls' if automatic else 'Authenticated configured Central capture') if mode=='connected' else 'Replay of supplied capture; no live server request')

    def engine(self,rid,read_only=False):
        meta=self.metadata(rid)
        run=RunManifest.model_validate_json(self.store.input(meta['request']['manifest_id'],'manifest'))
        settings=self.store.settings
        if run.mode!='connected':
            settings=Settings(dict(settings.values,SAMPLE_MODE='true'))
        store=RunStore(self.store.directory,settings)
        target=None
        if not settings.sample:
            try: target=configured_target(settings)
            except (ValueError,KeyError):
                if not read_only: raise
        return RecoveryEngine(store,target)

    def plans(self,rid):
        engine=self.engine(rid,read_only=True)
        with self.store.connect() as c: rows=c.execute('SELECT id,body,reviewed FROM recovery_plans ORDER BY rowid DESC LIMIT 1000').fetchall()
        result=[]
        for pid,body,reviewed in rows:
            if json.loads(body).get('run_id')!=rid: continue
            plan=engine.get(pid)
            state=engine.result(pid)
            events=[json.loads(l) for l in engine.events(pid).splitlines()]
            checks=[e for e in events if e['state']=='ui_readback']
            result.append({'plan':plan,'reviewed':bool(reviewed),'result':state,'events':events,
                'readback':checks[-1]['details'] if checks else None})
        return result

    @staticmethod
    def latest_report(report,plans):
        current=report; newer=''
        for item in plans:
            result=item['result']
            after=result.get('after')
            stamp=item['events'][-1]['at'] if item['events'] else ''
            if after and stamp>newer: current,newer=after,stamp
            check=item['readback']
            if check and check['checked_at']>newer: current,newer=check['report'],check['checked_at']
        return current,newer

    def view(self,rid):
        meta=self.metadata(rid); req=meta['request']
        run=RunManifest.model_validate_json(self.store.input(req['manifest_id'],'manifest'))
        try: status=self.store.get(rid).model_dump(mode='json')
        except KeyError: status={'run_id':rid,'state':'draft','preservation_outcome':None,'error':None}
        report=json.loads(self.store.artifact(rid,'report.json')) if status['state']=='completed' else None
        plans=self.plans(rid) if report else []
        current,_=self.latest_report(report,plans)
        with self.store.connect() as c: children=c.execute('SELECT run_id,body FROM ui_runs ORDER BY rowid DESC LIMIT 1000').fetchall()
        child=next((i for i,b in children if json.loads(b).get('parent_run_id')==rid),None)
        from .ui_investigation import UIInvestigation
        return {'manifest':run.model_dump(mode='json'),'status':status,'report':report,'current_report':current,
            'events':[json.loads(l) for l in self.store.events(rid).splitlines()] if status['state']!='draft' else [],
            'plans':plans,'sample_readback_run_id':child,'investigation':UIInvestigation(self.store).status(rid),**meta}

    def recent(self):
        with self.store.connect() as c:
            rows=c.execute('SELECT run_id FROM jobs ORDER BY rowid DESC LIMIT 1000').fetchall()
        result=[];counts={'sample':0,'records':0}
        for (rid,) in rows:
            meta=self.metadata(rid)
            run=RunManifest.model_validate_json(self.store.input(meta['request']['manifest_id'],'manifest'))
            group='sample' if run.mode=='sample' else 'records'
            if counts[group]>=30:continue
            counts[group]+=1
            status=self.store.get(rid).model_dump(mode='json')
            report=json.loads(self.store.artifact(rid,'report.json')) if status['state']=='completed' else None
            report,newer=self.latest_report(report,self.plans(rid)) if report else (None,'')
            events=self.store.events(rid).splitlines()
            case=meta.get('sample_case');device_count=len(meta['request']['device_input_ids'])
            synthetic=meta.get('synthetic_source')
            if synthetic is None:synthetic=any(inventory(self.store.input(i,'device'),self.store.settings).manifest.synthetic for i in meta['request']['device_input_ids'])
            title=next((c['title']+' — example' for c in CATALOG if c['id']==case),
                f"Records from {device_count} {'device' if device_count==1 else 'devices'}")
            result.append({'run_id':rid,'mode':run.mode,'status':status,'title':title,'sample_case':case,
                'checked_at':newer or (json.loads(events[-1])['observed_at'] if events else None),
                'record_count':len(report['findings']) if report else None,
                'attention_count':sum(f['preservation']!='preserved' for f in report['findings']) if report else None,
                'coverage_complete':report['coverage']['complete'] if report else None,
                'synthetic_source':synthetic,
                'captured_run_reference':meta.get('captured_run_reference')})
        return result

    def objects(self,rid):
        meta=self.metadata(rid); req=meta['request']; objects={}
        def add(sid,files,versions,server_side=True):
            xmls={v['xml_path']:v['version_id'] for v in versions}
            for path,data in files.items():
                oid=digest((sid+'\0'+path).encode())
                objects[oid]={'object_id':oid,'snapshot_id':sid,'path':path,'sha256':digest(data),'data':data,
                    'xml_version_id':xmls.get(path),'server_side':server_side}
        for i in req['device_input_ids']:
            raw=self.store.input(i,'device'); inv=inventory(raw,self.store.settings)
            add(inv.manifest.snapshot_id,read_archive(raw,self.store.settings),[v.model_dump() for v in inv.versions],False)
        parts=read_archive(self.store.input(req['server_input_id'],'server'),self.store.settings)
        snapshot=json.loads(parts['server-snapshot.json'])
        add(snapshot['snapshot_id'],read_archive(parts['server-payload.zip'],self.store.settings),snapshot['versions'])
        for item in self.plans(rid):
            pairs=item['result'].get('capture_hashes',[])
            if item['readback']: pairs=pairs+[item['readback']['capture_hashes']]
            if not pairs: continue
            e,p=pairs[-1]
            engine=self.engine(rid,read_only=True)
            envelope=json.loads(engine.evidence(item['plan']['plan_id'],e))
            payload=engine.evidence(item['plan']['plan_id'],p)
            add(envelope['snapshot_id'],read_archive(payload,self.store.settings),envelope['versions'])
        return objects

    def finding(self,rid,fid):
        view=self.view(rid); report=view['current_report']
        if not report: raise ValueError('Comparison is not complete')
        matches=[f for f in report['findings'] if f['finding_id']==fid]
        if len(matches)!=1: raise KeyError('Finding not found')
        f=matches[0]; receipts=[r for r in report['receipts'] if r['evidence_id'] in f['evidence_ids']]
        if f['original_retained_in_history']:
            receipts += [r for r in report['receipts'] if r['version_id']==f['current_version_id'] and r['source_file']
                and (r['source_file'].endswith('.xml') or r['request_scope'].endswith('.xml')) and r not in receipts]
        objects=self.objects(rid)
        required=set()
        for i in view['request']['device_input_ids']:
            inv=inventory(self.store.input(i,'device'),self.store.settings)
            if inv.manifest.snapshot_id!=f['snapshot_id']: continue
            v=next((v for v in inv.versions if v.version_id==f['version_id']),None)
            if v: required={v.xml_path,'device-manifest.json',*(m.archive_path for m in v.media),*(d.xml_path for d in inv.manifest.form_definitions)}
        source_files=[]
        for obj in objects.values():
            if obj['snapshot_id']==f['snapshot_id'] and obj['path'] in required or any(r['source_snapshot_id']==obj['snapshot_id'] and r['source_file']==obj['path'] for r in receipts):
                source_files.append({k:obj[k] for k in ('object_id','snapshot_id','path','sha256')})
        from .xml_compare import xml_facts
        def facts_for(version,side):
            for obj in objects.values():
                if obj['xml_version_id']!=version: continue
                if side=='source' and obj['snapshot_id']!=f['snapshot_id']: continue
                if side=='server' and not obj['server_side']: continue
                valid=any(r['source_snapshot_id']==obj['snapshot_id'] and r['source_file']==obj['path']
                    and r['outcome'] in ('success','synthetic') and r['response_sha256']==obj['sha256'] for r in report['receipts'])
                if valid: return {a['path']:a for a in xml_facts(obj['data'],self.store.settings)}
            return {}
        left=facts_for(f['version_id'],'source');right=facts_for(f['version_id'],'server')
        edit=facts_for(f['current_version_id'],'server') if f['original_retained_in_history'] else {}
        paths=list(dict.fromkeys([*left,*right,*edit]));values=[]
        for path in paths:
            a,b,c=left.get(path),right.get(path),edit.get(path)
            if not any(n and n['text'] is not None for n in (a,b,c)): continue
            values.append({'path':path,'occurrence_indices':(a or b or c)['indices'],
                'source_value':a['text'] if a else None,'server_value':b['text'] if b else None,
                'current_edit_value':c['text'] if c else None,'source_present':a is not None,'server_present':b is not None})
        return {'finding':f,'receipts':receipts,'source_files':source_files,
            'scope':'Only supplied snapshots and this explicitly scoped readback are assessed','compared_values':values[:500],
            'server_xml_available':bool(right),'current_edit_available':bool(edit),'values_truncated':len(values)>500}

    def sample_readback(self,rid):
        meta=self.metadata(rid); case=meta.get('sample_case')
        if case not in ('media','stranded'): raise ValueError('No offline recovery readback example for this check')
        current=self.view(rid)
        if current['sample_readback_run_id']:
            child=self.metadata(current['sample_readback_run_id'])
            return {'run_id':current['sample_readback_run_id'],'request':child['request']}
        from scripts.build_stage5_fixtures import recovery_readback
        data=recovery_readback(case)
        run=RunManifest.model_validate(dict(data['run'],run_id=new_id()))
        d=self.store.register('device',data['device']); s=self.store.register('server',bundle_snapshot(encoded(data['snapshot']),data['server']))
        return self.draft(run,[d.input_id],s.input_id,sample_case=None,parent_run_id=rid,captured_run_reference=rid,
            provenance='Separate authored synthetic readback example; comparison only; no upload or external service')

    def download(self,rid,name):
        view=self.view(rid); report=view['current_report']
        if not report: raise ValueError('Check has no completed report')
        if name=='findings.json': return encoded(report['findings']),'application/json'
        if name=='report.json': return encoded(report),'application/json'
        if name=='trace.jsonl':
            safe=[]
            for event in view['events']:
                safe.append({k:event[k] for k in ('sequence','event','observed_at')})
                safe[-1]['details']={k:v for k,v in event['details'].items() if k in ('mode','preservation_outcome','coverage_complete','verdict')}
            job=view.get('investigation')
            if job:
                allowed=('kind','seq','elapsed_ms','provider','role','action','actual_serving_model','route_id','query_id','request_id','source_hashes','status','mode')
                for event in job['events']: safe.append({'stream':'connected_investigation',**{k:v for k,v in event.items() if k in allowed}})
            return encoded({'redaction':'Allowlisted event metadata only; no source values, credentials, model prompts or SQL bodies'})+b''.join(encoded(e) for e in safe),'application/x-ndjson'
        if name in ('investigation.json','query-evidence.json','world-model.jsonl'):
            from .ui_investigation import UIInvestigation
            job=UIInvestigation(self.store);state=job.status(rid)
            if not state or state['state'] in ('queued','running'): raise ValueError('Connected investigation artifact is not complete')
            directory=job.directory(rid,state['attempt_id']);native_name='world.jsonl' if name=='world-model.jsonl' else name;path=directory/native_name
            if not path.exists(): raise KeyError('Connected artifact unavailable')
            seals=json.loads((directory/'seals.json').read_bytes());body=path.read_bytes()
            if len(body)>8388608 or digest(body)!=seals.get(native_name): raise ValueError('Connected artifact integrity failure')
            return body,'application/x-ndjson' if name.endswith('jsonl') else 'application/json'
        if name!='report.txt': raise KeyError('Download not available')
        lines=['LastCopy evidence report',f"Mode: {view['manifest']['mode']}",f'Check: {rid}',
            f"Investigation: {view['status']['state']}",f"Preservation outcome: {report['preservation_outcome']}",
            f"Source coverage complete: {report['coverage']['complete']}",
            'Only supplied sources and checked scope are assessed. This is not permission to erase a device.','']
        for f in report['findings']: lines.extend([f"{f['version_id']}: {f['verdict']}",f['summary'],'Evidence: '+', '.join(f['evidence_ids']),''])
        lines+=['Coverage limitations:']+report['coverage']['limitations']
        return ('\n'.join(lines)+'\n').encode(),'text/plain; charset=utf-8'
