"""Owner-only cloud setup. Keys remain in a mode-0600 private server file."""
import json,os,re,uuid,time,sqlite3
from datetime import datetime,timezone
from starlette.concurrency import run_in_threadpool
from fastapi import APIRouter,Request,HTTPException
from pydantic import BaseModel
from .cloud_access import CloudAccess,COOKIE
from .config import Settings
from .inventory import digest
from .nvidia_cloud import NvidiaCloud,chat_models
from .investigation import InvestigationError
from .store import encoded

router=APIRouter(prefix='/ui/cloud-ai')

class CloudAIStatus(BaseModel):
    configured:bool
    model:str|None
    provider:str
    nightshift:str
    zetaris:str
    award_path_eligible:bool=False
    private_key_returned:bool=False
    last_receipt_id:str|None=None
    last_completed_at:str|None=None
    test_remaining:int=10
    test_resets_at:str|None=None

class CloudAIConnect(BaseModel):
    models:list[str]
    configured:bool
    inference_verified:bool

class CloudAITest(BaseModel):
    mode:str
    source:str
    report_sha256:str
    before:dict
    after:dict
    decision_changed:bool
    receipts:list[dict]
    nightshift_used:bool=False
    zetaris_used:bool=False
    preservation_authority:str
    award_path_eligible:bool=False
    receipt_id:str

def configuration(settings):
    from pathlib import Path
    directory=settings.values.get('LASTCOPY_DATA_DIR')
    if not directory:return {}
    path=Path(directory)/'cloud-ai.json'
    if not path.exists():return {}
    if path.is_symlink() or path.stat().st_size>4096:raise ValueError('Invalid private cloud configuration')
    value=json.loads(path.read_bytes())
    if not isinstance(value,dict) or set(value)-{'NVIDIA_API_KEY','NVIDIA_MODEL_ID','AI_PROVIDER'}:raise ValueError('Invalid cloud configuration keys')
    return value

def owner(request):
    from .api import app,get_store
    store=app.dependency_overrides.get(get_store,get_store)();gate=CloudAccess(store)
    if not gate.enabled or not gate.owner_ok(request.cookies.get(COOKIE)):raise HTTPException(403,'Cloud AI setup is available only to the owner')
    if store.settings.sample:raise HTTPException(409,'Sample mode never calls an external provider')
    return store

def save(store,body):
    path=store.directory/'cloud-ai.json';temporary=store.directory/('cloud-ai-'+str(uuid.uuid4())+'.tmp')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as file:file.write(encoded(body))
    os.replace(temporary,path)

def latest_success(store):
    folder=store.directory/'cloud-ai-receipts'
    if not folder.exists():return None
    for path in sorted(folder.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:50]:
        if not re.fullmatch(r'[a-f0-9-]{36}',path.stem) or path.stat().st_size>65536:continue
        value=json.loads(path.read_bytes())
        if value.get('mode')=='live_direct_provider_smoke' and len(value.get('receipts',[]))==2:
            return path,value
    return None

@router.get('',response_model=CloudAIStatus)
def status(request:Request):
    store=owner(request);config=configuration(store.settings)
    saved=latest_success(store) if config.get('AI_PROVIDER')=='nvidia_direct' else None
    try:
        with store.connect() as c:used,first=c.execute('SELECT COUNT(*),MIN(at) FROM cloud_ai_budget WHERE at>?',(time.time()-86400,)).fetchone()
    except sqlite3.OperationalError:used,first=0,None
    return {'configured':bool(config.get('NVIDIA_API_KEY')),'model':config.get('NVIDIA_MODEL_ID'),
        'provider':'NVIDIA direct cloud' if config.get('AI_PROVIDER')=='nvidia_direct' else 'Not selected',
        'nightshift':'Separate PC runtime; always-on cloud path not verified',
        'zetaris':'Cloud query deployment not configured; full connected sponsor investigation remains blocked',
        'award_path_eligible':False,'private_key_returned':False,
        'last_receipt_id':saved[0].stem if saved else None,
        'last_completed_at':datetime.fromtimestamp(saved[0].stat().st_mtime,timezone.utc).isoformat() if saved else None,
        'test_remaining':max(0,10-used),'test_resets_at':datetime.fromtimestamp(first+86400,timezone.utc).isoformat() if first else None}

@router.get('/last-test',response_model=CloudAITest)
def last_test(request:Request):
    saved=latest_success(owner(request))
    if not saved:raise HTTPException(404,'No completed provider test has been saved')
    return dict(saved[1],receipt_id=saved[0].stem)

@router.post('/{action}',response_model=CloudAIConnect|CloudAITest)
async def setup(action:str,request:Request):
    from .api import bounded_body
    store=owner(request)
    if action not in ('connect','test'):raise HTTPException(404,'Unknown cloud AI action')
    try:body=json.loads(await bounded_body(request,4096))
    except ValueError:raise HTTPException(422,'Invalid cloud configuration request') from None
    return await run_in_threadpool(configure_bounded,store,action,body)

@router.get('/models',response_model=CloudAIConnect)
async def saved_models(request:Request):
    return await run_in_threadpool(configure_bounded,owner(request),'models',{})

def configure_bounded(store,action,body):
    from .store import RunStore
    with RunStore(store.directory/'cloud-ai-jobs',store.settings).lease() as held:
        if not held:raise HTTPException(409,'One cloud setup/test job is already running. Wait for it to finish.')
        with store.connect() as c:
            table='cloud_ai_inventory_budget' if action in ('connect','models') else 'cloud_ai_budget'
            period,limit=(3600,30) if action in ('connect','models') else (86400,10)
            c.execute(f'CREATE TABLE IF NOT EXISTS {table}(at REAL NOT NULL)')
            c.execute(f'DELETE FROM {table} WHERE at<?',(time.time()-period,))
            if c.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]>=limit:raise HTTPException(429,'Cloud setup/test budget reached. No further provider request was started.')
            c.execute(f'INSERT INTO {table} VALUES(?)',(time.time(),))
        return configure(store,action,body)

def configure(store,action,body):
    config=configuration(store.settings)
    if not isinstance(body,dict):raise HTTPException(422,'Invalid cloud configuration request')
    if action=='connect':
        if set(body)!={'api_key'} or not isinstance(body['api_key'],str) or not re.fullmatch(r'[A-Za-z0-9_.-]{20,512}',body['api_key']):raise HTTPException(422,'Enter exactly one NVIDIA key privately')
        config={'NVIDIA_API_KEY':body['api_key']}
    elif action=='test':
        if set(body)!={'model'} or not isinstance(body['model'],str) or not re.fullmatch(r'[A-Za-z0-9_./:-]{1,160}',body['model']):raise HTTPException(422,'Choose an advertised model')
        config.update(NVIDIA_MODEL_ID=body['model'])
    provider=None
    try:
        provider=NvidiaCloud(Settings(dict(store.settings.values,**config)))
        models=chat_models(provider.models())
        if action in ('connect','models'):
            if action=='connect':save(store,config)
            return {'models':models,'configured':True,'inference_verified':False}
        # Actual fixture comparison supplies reviewer evidence. This is a LIVE
        # direct-provider smoke test using synthetic files, not a Sample run or
        # proof of Zetaris/Nightshift/full connected investigation acceptance.
        from .public_demo import opened
        from .ui import Workspace
        from .store import RunStore
        view=opened(Workspace(RunStore(store.directory/'ai-smoke-fixtures',Settings({'SAMPLE_MODE':'true'}))),'export')
        report=view['current_report'];proof=digest(encoded(report))
        before,receipt1=provider.choose('investigator',{'observation':'A tabular export omits repeated answers; raw XML has not been considered in this hypothesis.','source':'synthetic export fixture'},['fetch_raw_xml','manual_review'],None)
        after,receipt2=provider.choose('reviewer',{'previous_hypothesis':before,'verifier_findings':report['findings'],'report_sha256':proof,
            'instruction':'Raw XML positively preserves these answers. Use export guidance; do not resubmit.'},['export_guidance','manual_review'],None)
        result={'mode':'live_direct_provider_smoke','source':'Synthetic fixture; actual offline verifier report supplied to reviewer','report_sha256':proof,
            'before':before,'after':after,'decision_changed':before!=after,'receipts':[receipt1,receipt2],
            'nightshift_used':False,'zetaris_used':False,'preservation_authority':'deterministic verifier','award_path_eligible':False}
        folder=store.directory/'cloud-ai-receipts';folder.mkdir(exist_ok=True)
        receipt_id=str(uuid.uuid4());(folder/(receipt_id+'.json')).write_bytes(encoded(result))
        events=[{'kind':'model','role':'investigator','action':before,**receipt1},
            {'kind':'evidence','report_sha256':proof,'input_hashes':report['input_hashes'],'source':'actual synthetic verifier comparison'},
            {'kind':'model','role':'reviewer','action':after,'evidence_report_sha256':proof,**receipt2},
            {'kind':'decision_changed' if before!=after else 'decision_retained','before':before,'after':after,'verifier_outputs_changed':False}]
        (folder/(receipt_id+'.jsonl')).write_bytes(b''.join(encoded(dict(event,seq=i+1,run_id='cloud-ai-'+receipt_id,mode='live_direct_provider_smoke')) for i,event in enumerate(events)))
        config['AI_PROVIDER']='nvidia_direct';save(store,config)
        return dict(result,receipt_id=receipt_id)
    except (ValueError,KeyError,InvestigationError) as error:
        text=str(error);match=re.search(r'Provider HTTP (\d{3})',text);http_status=int(match[1]) if match else None
        detail={401:'NVIDIA did not accept this key. Replace it with one complete API key.',403:'NVIDIA denied access to this model. Check this key’s model access.',404:'NVIDIA lists this model, but its inference route is unavailable. Choose another chat model.',429:'NVIDIA rate or credit limit reached. Wait or check your NVIDIA allowance.'}.get(http_status)
        if not detail:detail='The model did not return a valid bounded action, or the connection failed. Try another chat model; no verifier result was changed.'
        folder=store.directory/'cloud-ai-receipts';folder.mkdir(exist_ok=True)
        receipt_id=str(uuid.uuid4())
        (folder/(receipt_id+'.json')).write_bytes(encoded({'status':'failed','provider':'nvidia_direct','http_status':http_status,'catalog_model':config.get('NVIDIA_MODEL_ID'),'action':action,'message':detail,'sample_fallback':False}))
        (folder/(receipt_id+'.jsonl')).write_bytes(encoded({'seq':1,'run_id':'cloud-ai-'+receipt_id,'mode':'live_direct_provider_smoke','kind':'failed','provider':'nvidia_direct','http_status':http_status,'action':action,'catalog_model':config.get('NVIDIA_MODEL_ID'),'sample_fallback':False}))
        raise HTTPException(503,detail+' Reference: '+receipt_id) from None
    finally:
        if provider:provider.close()
