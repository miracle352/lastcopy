"""UI boundary: registered IDs, sanitized configuration, downloadable evidence."""
from fastapi import APIRouter,Depends,Request,HTTPException,BackgroundTasks
from fastapi.responses import Response
from .api import get_store,bounded_body,recovery_error
from .ui import Workspace,CATALOG
from .config import LIMITS
from .models import UIPrepareRequest,UIFindingRequest
from .models import UISettings,UIConnection,UIDevice,UIServer,UIDraft,UIRunView,UIRecent,UIFindingEvidence,RecoveryPlan
from .models import UIImportSessionRequest,UIImportSession
from .inventory import digest
from .odk_recovery import configured_target,configured_read_target
from .models import RunRequest,JobStatus,RunManifest
from .models import WatchControl,WatchStatus,WatchSources

router=APIRouter(prefix='/ui')


def workspace(store=Depends(get_store)): return Workspace(store)


@router.get('/watch',response_model=WatchStatus)
def watch_status(ws=Depends(workspace)):
    from .monitor import Monitor
    return Monitor(ws.store).status()


@router.post('/watch/control',response_model=WatchStatus)
def watch_control(body:WatchControl,ws=Depends(workspace)):
    from .monitor import Monitor
    return recovery_error(lambda:Monitor(ws.store).control(body.action))


@router.post('/watch/sources',response_model=WatchStatus)
def watch_sources(body:WatchSources,ws=Depends(workspace)):
    from .monitor import Monitor
    return recovery_error(lambda:Monitor(ws.store).accept_sources(body))


@router.get('/settings',response_model=UISettings)
def ui_settings(ws=Depends(workspace)):
    settings=ws.store.settings
    target=None
    if not settings.sample:
        try: target=configured_read_target(settings)
        except (KeyError,ValueError): pass
    return {'mode':'sample' if settings.sample else 'connected','target':target,
        'connected_ready':bool(target and all(settings.values.get(k) for k in ('ODK_BASE_URL','ODK_EMAIL','ODK_PASSWORD'))),
        'limits':{k:settings.limit(k) for k in LIMITS},'samples':CATALOG,
        'backend_scope':('Private single-owner cloud evidence store; credentials remain on the server' if settings.values.get('LASTCOPY_CLOUD_ACCESS')=='true' else 'Single-user local evidence store; credentials remain on the server')}


@router.get('/runs',response_model=list[UIRecent])
def recent(ws=Depends(workspace)): return recovery_error(ws.recent)


@router.get('/connection',response_model=UIConnection)
def connection(ws=Depends(workspace)): return ws.connection()


@router.post('/examples/{case}',response_model=UIDraft)
def automatic_example(case:str,background:BackgroundTasks,ws=Depends(workspace)):
    def open_example():
        draft=ws.example(case)
        status=ws.store.enqueue(RunRequest.model_validate(draft['request']))
        if status.state=='queued':background.add_task(drain_then_investigate,ws.store,draft['run_id'])
        return draft
    return recovery_error(open_example)


@router.post('/samples/{case}',status_code=201,response_model=UIDraft)
def open_sample(case:str,ws=Depends(workspace)): return recovery_error(lambda:ws.sample(case))


@router.post('/devices',status_code=201,response_model=UIDevice)
async def import_device(request:Request,ws=Depends(workspace)):
    return ws.device(await bounded_body(request,ws.store.settings.limit('MAX_UPLOAD_BYTES')))


@router.post('/server',status_code=201,response_model=UIServer)
async def import_server(request:Request,ws=Depends(workspace)):
    return ws.server(await bounded_body(request,ws.store.settings.limit('MAX_UPLOAD_BYTES')))


@router.post('/prepare',status_code=201,response_model=UIDraft)
def prepare(body:UIPrepareRequest,ws=Depends(workspace)):
    return recovery_error(lambda:ws.prepare(body))


@router.post('/imports',status_code=201,response_model=UIImportSession)
def save_inputs(body:UIImportSessionRequest,ws=Depends(workspace)):
    return recovery_error(lambda:ws.save_import(body))


@router.get('/imports/{sid}',response_model=UIImportSession)
def restore_inputs(sid:str,ws=Depends(workspace)):
    return recovery_error(lambda:ws.load_import(sid))


@router.get('/runs/{rid}',response_model=UIRunView)
def run_view(rid:str,ws=Depends(workspace)): return recovery_error(lambda:ws.view(rid))


def drain_then_investigate(store,rid):
    store.drain()
    ws=Workspace(store);meta=ws.metadata(rid)
    run=RunManifest.model_validate_json(store.input(meta['request']['manifest_id'],'manifest'))
    if (store.get(rid).state=='completed' and run.mode=='connected'
        and run.destination.environment=='dedicated_synthetic_test' and not meta.get('automatic_check')):
        from .ui_investigation import UIInvestigation
        job=UIInvestigation(store)
        try: job.start(rid)
        except (ValueError,KeyError): job.unavailable(rid)


@router.post('/runs/{rid}/start',status_code=202,response_model=JobStatus)
def start_check(rid:str,background:BackgroundTasks,ws=Depends(workspace)):
    def start():
        req=RunRequest.model_validate(ws.metadata(rid)['request'])
        status=ws.store.enqueue(req)
        if status.state=='queued': background.add_task(drain_then_investigate,ws.store,rid)
        return status
    return recovery_error(start)


@router.post('/runs/{rid}/investigation/cancel')
def cancel_investigation(rid:str,ws=Depends(workspace)):
    from .ui_investigation import UIInvestigation
    return recovery_error(lambda:UIInvestigation(ws.store).cancel(rid))


@router.get('/runs/{rid}/findings/{fid}',response_model=UIFindingEvidence)
def finding(rid:str,fid:str,ws=Depends(workspace)): return recovery_error(lambda:ws.finding(rid,fid))


@router.get('/runs/{rid}/objects/{oid}')
def evidence_object(rid:str,oid:str,ws=Depends(workspace)):
    def get():
        objects=ws.objects(rid)
        if oid not in objects: raise KeyError('Object outside run')
        return objects[oid]
    obj=recovery_error(get)
    # Browser never renders imported XML/HTML as executable content.
    return Response(obj['data'],media_type='application/octet-stream',headers={
        'Content-Disposition':'attachment; filename="evidence-file.bin"','X-Content-SHA256':obj['sha256'],'X-Content-Type-Options':'nosniff'})


@router.get('/runs/{rid}/downloads/{name}')
def download(rid:str,name:str,ws=Depends(workspace)):
    body,kind=recovery_error(lambda:ws.download(rid,name))
    return Response(body,media_type=kind,headers={'Content-Disposition':f'attachment; filename="{name}"',
        'X-Content-SHA256':digest(body),'Cache-Control':'no-store'})


@router.post('/runs/{rid}/plans',status_code=201,response_model=RecoveryPlan)
def stage(rid:str,body:UIFindingRequest,ws=Depends(workspace)):
    return recovery_error(lambda:ws.engine(rid).stage(rid,body.finding_id))


@router.post('/runs/{rid}/sample-readback',status_code=201)
def sample_readback(rid:str,ws=Depends(workspace)):
    return recovery_error(lambda:ws.sample_readback(rid))
