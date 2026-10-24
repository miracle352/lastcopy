"""Real loopback Central acceptance. Only creates bounded synthetic data; no deletion.

Seeding an incomplete synthetic submission is setup, separately labelled. Recovery
then uses the same reviewed plan and Apply implementation as CLI/API. Lost-ack
acceptance terminates a worker after the real POST and resumes in another process.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from dotenv import dotenv_values, set_key
from lastcopy.config import ROOT, Settings
from lastcopy.inventory import inventory, digest, read_archive
from lastcopy.models import RunManifest, RunRequest
from lastcopy.store import RunStore, encoded
from lastcopy.recovery import RecoveryEngine, archive
from lastcopy.odk_recovery import CentralRecovery, configured_target
from scripts.run import bundle_snapshot
from scripts.setup_odk_test import CENTRAL_COMMIT


def fixture(tag, case):
    original = ROOT/'fixtures/representative/device'
    form = (original/'projects/field-a/forms/inspection.xml').read_bytes()
    vid = 'uuid:'+str(uuid.uuid5(uuid.NAMESPACE_URL,'lastcopy-stage4/'+tag+'/'+case))
    data = (original/'projects/field-a/instances/inspection_001/inspection-final.xml').read_bytes()
    data = data.replace(b'uuid:11111111-2222-4333-8444-555555555555',vid.encode())
    # Shared filename twice plus two different filenames with identical bytes.
    data = data.replace(b'  <meta>',b'  <reading><value>07</value><attachment>a.bin</attachment></reading>\n  <reading><value>09</value><attachment>b.bin</attachment></reading>\n  <meta>')
    manifest = json.loads((original/'device-manifest.json').read_bytes())
    manifest.update(snapshot_id='stage4-device-'+tag+'-'+case,device_id='stage4-synthetic-device',
        scope_complete=True,scope_provenance={'origin':'coordinator_attestation','reference':'stage4-authored-synthetic-scope'})
    files = {'device-manifest.json':encoded(manifest),'projects/field-a/forms/inspection.xml':form,
        'projects/field-a/instances/inspection_001/inspection-final.xml':data}
    for name in ('sample.txt','a.bin','b.bin'):
        files['projects/field-a/instances/inspection_001/'+name] = b'LastCopy Stage 4 synthetic bytes\x00\x01\x7f\xff\n'
    return archive(files),vid,form


def worker(directory,plan_id):
    settings = Settings.load()
    store = RunStore(directory,settings)
    remote = CentralRecovery(settings)
    engine = RecoveryEngine(store,configured_target(settings),remote)
    native_write = remote.write
    def lost(plan,files,filename=None):
        native_write(plan,files,filename)
        # Durable engine intent already exists; no local attempt_result recorded.
        os._exit(73)
    remote.write = lost
    engine.apply(plan_id)
    raise RuntimeError('Lost acknowledgement worker did not reach its write')


def verify(tag,case,via_api=False):
    config = dict(dotenv_values(ROOT/'.env')); config['SAMPLE_MODE']='false'
    if config.get('ODK_BASE_URL') != 'http://localhost:8384': raise ValueError('Acceptance only uses the pinned loopback stack')
    # Verify real served version before setup or credentials are sent.
    import httpx
    with httpx.Client(timeout=15,trust_env=False) as client:
        version = client.get(config['ODK_BASE_URL']+'/version.txt')
        if version.status_code!=200 or CENTRAL_COMMIT not in version.text: raise ValueError('Pinned Central not available')
    settings = Settings(config)
    remote = CentralRecovery(settings); remote.begin(); remote.login()
    def setup_request(method,path,**kwargs):
        status,body = remote.request(method,path,**kwargs)
        if status not in (200,201): raise ValueError(f'Synthetic setup HTTP {status}')
        return json.loads(body)
    projects = setup_request('GET','/v1/projects')
    matches = [p for p in projects if p['name']=='LastCopy synthetic Stage 4 recovery']
    if len(matches)>1: raise ValueError('Ambiguous dedicated synthetic project')
    project = matches[0] if matches else setup_request('POST','/v1/projects',json={'name':'LastCopy synthetic Stage 4 recovery'})
    config.update(ODK_RECOVERY_PROJECT_ID=str(project['id']),ODK_RECOVERY_FORM_ID='inspection')
    settings = Settings(config)
    remote.target = configured_target(settings)
    for key in ('ODK_RECOVERY_PROJECT_ID','ODK_RECOVERY_FORM_ID'):
        set_key(str(ROOT/'.env'),key,config[key])
    device,vid,form = fixture(tag,case)
    source_hash = digest(device)
    scope = remote.scope()
    forms = setup_request('GET',f"/v1/projects/{project['id']}/forms")
    if not any(f['xmlFormId']=='inspection' for f in forms):
        setup_request('POST',f"/v1/projects/{project['id']}/forms?publish=true",content=form,headers={'Content-Type':'application/xml'})
    else:
        status,body = remote.request('GET',scope+'.xml')
        if status!=200 or body!=form: raise ValueError('Existing test XForm differs; never overwrite')
    folder = ROOT/'private/stage4'/f'{tag}-{case}'
    folder.mkdir(parents=True,exist_ok=True)
    if (folder/'receipt.json').exists(): raise ValueError('Completed acceptance already exists; use a new synthetic tag for a new run')
    inv = inventory(device,settings); source = read_archive(device,settings)
    # Setup is strictly separate from Apply: intentionally incomplete attachment.
    if case=='media':
        parts = [('xml_submission_file',('original.xml',source[inv.versions[0].xml_path],'application/xml'))]
        for m in inv.versions[0].media:
            if m.filename=='b.bin' or any(n==m.filename for n,_ in parts): continue
            parts.append((m.filename,(m.filename,source[m.archive_path],'application/octet-stream')))
        status,_ = remote.request('POST',f"/v1/projects/{project['id']}/submission",files=parts,headers={'X-OpenRosa-Version':'1.0'})
        if status!=201: raise ValueError(f'Partial synthetic setup HTTP {status}')
    run = RunManifest(schema_version=1,run_id='stage4-'+tag+'-'+case,mode='connected',
        source_snapshot_ids=[inv.manifest.snapshot_id,'pending-capture'],expected_device_ids=[inv.manifest.device_id],
        roster_provenance={'origin':'coordinator_attestation','reference':'stage4-authored-roster'},destination=remote.target)
    envelope,payload = remote.capture(run)
    run = run.model_copy(update={'source_snapshot_ids':[inv.manifest.snapshot_id,json.loads(envelope)['snapshot_id']]})
    store = RunStore(folder/'ledger',settings)
    m = store.register('manifest',run.model_dump_json().encode()); d = store.register('device',device)
    s = store.register('server',bundle_snapshot(envelope,payload))
    store.enqueue(RunRequest(manifest_id=m.input_id,device_input_ids=[d.input_id],server_input_id=s.input_id)); store.drain()
    before = json.loads(store.artifact(run.run_id,'report.json'))
    wanted = 'MISSING_ATTACHMENT' if case=='media' else 'MISSING_SUBMISSION'
    if [f['verdict'] for f in before['findings']] != [wanted]: raise ValueError('Live before-state differs from independently authored expectation')
    engine = RecoveryEngine(store,remote.target,remote)
    plan = engine.stage(run.run_id,before['findings'][0]['finding_id'])
    # The harness is an explicit review of this concrete synthetic-only plan.
    engine.review(plan['plan_id'],plan['plan_sha256'],remote.target)
    if via_api:
        env = dict(os.environ,SAMPLE_MODE='false',LASTCOPY_DATA_DIR=str(folder/'ledger'))
        log = (folder/'api.log').open('wb')
        server = subprocess.Popen([sys.executable,'-m','uvicorn','lastcopy.api:app','--host','127.0.0.1','--port','8000'],
            cwd=ROOT,env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        try:
            with httpx.Client(base_url='http://127.0.0.1:8000',timeout=180,trust_env=False) as client:
                for _ in range(30):
                    if server.poll() is not None: raise ValueError('Acceptance API failed to start; port 8000 may be occupied')
                    try:
                        if client.get('/health').status_code==200: break
                    except httpx.TransportError: pass
                    time.sleep(0.5)
                staged=client.post('/recovery/plans',json={'run_id':run.run_id,'finding_id':before['findings'][0]['finding_id']})
                if staged.status_code!=201 or staged.json()!=plan: raise ValueError('HTTP stage does not match deterministic plan')
                base='/recovery/plans/'+plan['plan_id']
                if client.get(base+'/bundle').content!=engine.bundle(plan['plan_id']): raise ValueError('HTTP bundle differs')
                confirmation={'plan_sha256':plan['plan_sha256'],'target':remote.target}
                if client.post(base+'/review',json=confirmation).status_code!=200: raise ValueError('HTTP review failed')
                response=client.post(base+'/apply',json=confirmation)
                if response.status_code!=200: raise ValueError('HTTP Apply failed')
                after=response.json()
                if client.post(base+'/apply',json=confirmation).json()!=after: raise ValueError('HTTP repeated Apply differs')
        finally:
            server.terminate(); server.wait(timeout=15); log.close()
    elif case=='lost-ack':
        env = dict(os.environ,SAMPLE_MODE='false')
        result = subprocess.run([sys.executable,'-m','scripts.verify_stage4_live','--worker',str(folder/'ledger'),plan['plan_id']],cwd=ROOT,env=env,timeout=150)
        if result.returncode!=73: raise ValueError('Worker did not terminate after the real successful POST')
        # Restart in a different process through the documented CLI entrypoint.
        result = subprocess.run([sys.executable,'-m','scripts.recover','--data-dir',str(folder/'ledger'),'apply',plan['plan_id'],
            '--plan-sha256',plan['plan_sha256'],'--target-sha256',digest(encoded(remote.target))],cwd=ROOT,env=env,capture_output=True,timeout=150)
        if result.returncode: raise ValueError('CLI restart recovery failed; inspect sealed ledger')
        after = json.loads(result.stdout)
        after.pop('target_sha256',None)
    else:
        after = engine.apply(plan['plan_id'])
    if after['state']!='verified' or [f['verdict'] for f in after['after']['findings']]!=['PRESERVED']:
        raise ValueError('Live recovery not independently preserved: '+str(after.get('error')))
    repeat = engine.apply(plan['plan_id'])
    if repeat != after: raise ValueError('Repeated Apply changed completed work')
    events = engine.events(plan['plan_id'])
    intents = [json.loads(line) for line in events.splitlines() if json.loads(line)['state']=='write_intent']
    if len(intents)!=1: raise ValueError('Expected exactly one real write intent')
    if digest(device)!=source_hash or store.input(d.input_id,'device')!=device: raise ValueError('Original source changed')
    # Synthetic capture bodies contain no auth responses, headers, tokens or keys.
    output = ROOT/'docs/verification'/f'stage4-{tag}-{case}'
    output.mkdir(parents=True,exist_ok=False)
    (output/'device.zip').write_bytes(device)
    (output/'plan.json').write_bytes(encoded(plan))
    (output/'bundle.zip').write_bytes(engine.bundle(plan['plan_id']))
    (output/'before-envelope.json').write_bytes(envelope)
    (output/'before-payload.zip').write_bytes(payload)
    (output/'result.json').write_bytes(encoded(after))
    (output/'events.jsonl').write_bytes(events)
    for pair in after['capture_hashes']:
        for sha in pair:
            (output/(sha+'.evidence')).write_bytes(engine.evidence(plan['plan_id'],sha))
    receipt = {'mode':'connected','real_central':True,'central_commit':CENTRAL_COMMIT,'target':remote.target,
        'case':case,'instance_id':vid,'before_verdict':wanted,'after_verdict':'PRESERVED',
        'plan_id':plan['plan_id'],'one_write_intent':True,'repeat_apply_did_not_write':True,
        'lost_ack_worker_exit':73 if case=='lost-ack' else None,'fresh_same_reconciler':True,
        'entrypoint':'HTTP 127.0.0.1:8000 stage/download/review/apply/repeated-apply' if via_api else 'CLI restart after real write' if case=='lost-ack' else 'shared Python recovery engine',
        'source_archive_sha256':source_hash,'source_unchanged':True,
        'synthetic_media':'authored binary/text only; shared filename twice and equal bytes in differently named slots',
        'scope':'dedicated synthetic project on real local Central; not production or cloud recovery',
        'files':{p.name:digest(p.read_bytes()) for p in output.iterdir() if p.is_file()}}
    (output/'receipt.json').write_bytes(encoded(receipt)); (folder/'receipt.json').write_bytes(encoded(receipt))
    (folder/'entrypoints.json').write_bytes(encoded({'run_id':run.run_id,'plan_id':plan['plan_id'],'device_input_id':d.input_id,'manifest_id':m.input_id,'server_input_id':s.input_id}))
    print(json.dumps(receipt,indent=2)); remote.client.close()


if __name__=='__main__':
    p = argparse.ArgumentParser(); p.add_argument('--tag',default='20261024-01'); p.add_argument('--case',choices=['create','media','lost-ack'],default='create'); p.add_argument('--worker',nargs=2); p.add_argument('--api',action='store_true')
    a = p.parse_args()
    if a.worker: worker(*a.worker)
    else: verify(a.tag,a.case,a.api)
