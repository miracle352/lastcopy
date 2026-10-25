from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import Response, JSONResponse
from typing import Literal
from .config import Settings, ROOT
from .models import Health, ConfigurationStatus, ImportInventory
from .inventory import inventory, ImportRejected
from .models import RunRequest, JobStatus, RegisteredInput
from .store import RunStore
from .models import RecoveryStageRequest, RecoveryReviewRequest, RecoveryCaptureRequest, RecoveryPlan, Digest
from .recovery import RecoveryEngine
from .odk_recovery import CentralRecovery, configured_target
from contextlib import asynccontextmanager
import httpx
from starlette.middleware.trustedhost import TrustedHostMiddleware

@asynccontextmanager
async def lifespan(application):
    factory=application.dependency_overrides.get(get_store,get_store)
    factory().recover_interrupted()
    from .monitor import MonitorService
    from .device_transfer import DeviceTransferService
    monitor=MonitorService(factory());monitor.start()
    transfer=DeviceTransferService(monitor.monitor.store);transfer.start()
    try:yield
    finally:transfer.close();monitor.close()


app = FastAPI(title="LastCopy", version="0.1.0", docs_url=None, redoc_url=None,lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost'])


@app.middleware('http')
async def hosted_owner_boundary(request,call_next):
    from .cloud_access import CloudAccess,COOKIE
    factory=app.dependency_overrides.get(get_store,get_store)
    try:gate=CloudAccess(factory())
    except HTTPException as error:return JSONResponse(status_code=error.status_code,content={'detail':error.detail})
    if gate.enabled:
        import hmac
        transfer=gate.store.settings.values.get('LASTCOPY_TRANSFER_KEY','')
        device=(request.url.path=='/device-transfer' and request.method=='POST') or (request.url.path=='/device-transfer/status' and request.method=='GET')
        device_ok=device and len(transfer)>=32 and hmac.compare_digest((request.headers.get('authorization') or '').encode(),('Bearer '+transfer).encode())
        if not device_ok and not gate.transport_ok(request.headers.get('authorization')):
            return JSONResponse(status_code=401,content={'detail':'Owner sign-in required'})
        public_example=request.method=='GET' and request.url.path in ('/public/examples/media','/public/examples/export','/public/examples/history')
        if not device_ok and not public_example and request.url.path!='/session/login' and not gate.owner_ok(request.cookies.get(COOKIE)):
            return JSONResponse(status_code=401,content={'detail':'Owner sign-in required'})
    return await call_next(request)


@app.get('/public/examples/{case}')
def public_example(case:Literal['media','export','history']):
    from .ui import Workspace
    store=app.dependency_overrides.get(get_store,get_store)()
    isolated=RunStore(store.directory/'public-examples',Settings({'SAMPLE_MODE':'true'}))
    workspace=Workspace(isolated)
    draft=workspace.example(case)
    isolated.enqueue(RunRequest.model_validate(draft['request']))
    isolated.drain()
    return workspace.view(draft['run_id'])


@app.post('/device-transfer',status_code=201)
async def device_delivery(request:Request):
    from .cloud_access import CloudAccess
    from .cloud_inbox import accept
    factory=app.dependency_overrides.get(get_store,get_store)
    store=factory()
    if not CloudAccess(store).enabled:raise HTTPException(409,'Remote device delivery requires configured hosted access')
    data=await bounded_body(request,store.settings.limit('MAX_UPLOAD_BYTES'))
    try:return accept(store,data)
    except (ValueError,KeyError):raise HTTPException(409,'Device export does not match the configured scope or delivery limits') from None


@app.get('/device-transfer/status')
def device_run_control(request:Request):
    from .cloud_access import CloudAccess
    from .cloud_inbox import poll
    store=app.dependency_overrides.get(get_store,get_store)()
    if not CloudAccess(store).enabled:raise HTTPException(409,'Hosted access is required')
    try:return poll(store,request.headers.get('x-lastcopy-device-state','waiting_for_device'))
    except (ValueError,KeyError):raise HTTPException(422,'The device link state or configured scope is invalid') from None


@app.post('/session/login')
async def owner_login(request:Request):
    # Resolve the same operator store used by the gate (including test overrides).
    import json
    from .cloud_access import CloudAccess,COOKIE
    factory=app.dependency_overrides.get(get_store,get_store)
    try:body=json.loads(await bounded_body(request,2048))
    except (ValueError,UnicodeError):raise HTTPException(422,'Enter your owner passphrase') from None
    if not isinstance(body,dict) or set(body)!={'password'} or not isinstance(body['password'],str) or not 1<=len(body['password'])<=512:
        raise HTTPException(422,'Enter your owner passphrase')
    token=CloudAccess(factory()).login(body['password'])
    response=JSONResponse({'authenticated':True},headers={'Cache-Control':'no-store'})
    response.set_cookie(COOKIE,token,max_age=28800,httponly=True,secure=True,samesite='strict',path='/')
    return response


@app.post('/session/logout')
def owner_logout(request:Request):
    from .cloud_access import CloudAccess,COOKIE
    factory=app.dependency_overrides.get(get_store,get_store)
    CloudAccess(factory()).logout(request.cookies.get(COOKIE))
    response=JSONResponse({'authenticated':False},headers={'Cache-Control':'no-store'})
    response.delete_cookie(COOKIE,path='/',secure=True,httponly=True,samesite='strict')
    return response


@app.middleware('http')
async def local_browser_boundary(request, call_next):
    # CLI clients have no Origin. Browser requests must come from the configured
    # local UI; reject simple cross-site requests before reading private data or
    # creating jobs. Host validation separately blocks DNS-rebinding reads.
    if request.headers.get('origin') not in (None, 'http://127.0.0.1:3000',
            'http://localhost:3000', 'http://127.0.0.1:8000', 'http://localhost:8000'):
        return JSONResponse(status_code=403, content={'detail': 'Use the local LastCopy application origin'})
    return await call_next(request)


@app.middleware('http')
async def run_body_limit(request, call_next):
    if (request.url.path == '/run' or request.url.path.startswith('/recovery/') or request.url.path.startswith('/ui/')
            and request.url.path not in ('/ui/devices','/ui/server')) and request.method == 'POST':
        try:
            request._body = await bounded_body(request, 65536)
        except HTTPException:
            return JSONResponse(status_code=413, content={'detail': 'Run request exceeds 64 KiB'})
    return await call_next(request)


def get_store():
    # Configured by the local operator only; never supplied by an HTTP request.
    settings = Settings.load()
    return RunStore(settings.values.get('LASTCOPY_DATA_DIR') or ROOT / 'private/stage2', settings)


def get_recovery(request:Request,store: RunStore = Depends(get_store)):
    # Sample/Replay plans remain offline even when this local API also has a
    # configured connection. Resolve mode only from a sealed persisted plan.
    import sqlite3,json
    from .ui import Workspace
    pid=request.path_params.get('plan_id')
    if pid:
        try:
            with store.connect() as c: row=c.execute('SELECT body FROM recovery_plans WHERE id=?',(pid,)).fetchone()
        except sqlite3.OperationalError: row=None
        if row and json.loads(row[0]).get('mode') in ('sample','replay'):
            offline=RunStore(store.directory,Settings(dict(store.settings.values,SAMPLE_MODE='true')))
            engine=RecoveryEngine(offline,None); engine.get(pid)
            return engine
        if row and request.method=='GET':
            engine=RecoveryEngine(store,None);engine.get(pid)
            return engine
    try: return RecoveryEngine(store,None if store.settings.sample else configured_target(store.settings))
    except (ValueError,KeyError): raise HTTPException(409,'Configure the dedicated ODK test connection on the server') from None


def recovery_error(action):
    try:
        return action()
    except KeyError:
        raise HTTPException(404, 'Registered recovery object not found') from None
    except ValueError as error:
        raise HTTPException(409, str(error)) from None
    except (TimeoutError,ConnectionError):
        raise HTTPException(503,'Connection unavailable; read back before retrying any write') from None
    except httpx.HTTPError:
        raise HTTPException(503,'The configured service is unavailable. No sample evidence was substituted; read back before retrying a write.') from None


@app.post('/recovery/capture', status_code=201)
def capture_recovery(body: RecoveryCaptureRequest, store: RunStore = Depends(get_store)):
    from scripts.recover import capture_registered
    return recovery_error(lambda: capture_registered(store,body.manifest_id,body.device_input_ids))


@app.post('/recovery/plans', status_code=201, response_model=RecoveryPlan)
def stage_recovery(body: RecoveryStageRequest, engine=Depends(get_recovery)):
    return recovery_error(lambda: engine.stage(body.run_id,body.finding_id))


@app.get('/recovery/plans/{plan_id}', response_model=RecoveryPlan)
def recovery_plan(plan_id: Digest, engine=Depends(get_recovery)):
    return recovery_error(lambda: engine.get(plan_id))


@app.get('/recovery/plans/{plan_id}/bundle')
def recovery_bundle(plan_id: Digest, engine=Depends(get_recovery)):
    data = recovery_error(lambda: engine.bundle(plan_id))
    return Response(data,media_type='application/zip',headers={'Content-Disposition':f'attachment; filename="recovery-{plan_id}.zip"'})


@app.post('/recovery/plans/{plan_id}/review')
def review_recovery(plan_id: Digest, body: RecoveryReviewRequest, engine=Depends(get_recovery)):
    return recovery_error(lambda: engine.review(plan_id,body.plan_sha256,body.target.model_dump()))


@app.post('/recovery/plans/{plan_id}/apply')
def apply_recovery(plan_id: Digest, body: RecoveryReviewRequest, request: Request, engine=Depends(get_recovery)):
    if request.headers.get('origin') not in (None,'http://localhost:3000','http://127.0.0.1:3000','http://localhost:8000','http://127.0.0.1:8000'):
        raise HTTPException(403,'Apply requires the local configured application origin')
    def apply():
        if engine.store.settings.sample: raise ValueError('SAMPLE_MODE prohibits Apply and network calls')
        plan = engine.get(plan_id)
        if body.plan_sha256 != plan['plan_sha256'] or body.target.model_dump() != engine.target:
            raise ValueError('Apply confirmation differs from reviewed configured target')
        engine.remote = CentralRecovery(engine.store.settings)
        try: return engine.apply(plan_id)
        finally: engine.remote.client.close()
    return recovery_error(apply)


@app.get('/recovery/plans/{plan_id}/events')
def recovery_events(plan_id: Digest, engine=Depends(get_recovery)):
    return Response(recovery_error(lambda: engine.events(plan_id)),media_type='application/x-ndjson')


@app.post('/recovery/plans/{plan_id}/recheck')
def recovery_recheck(plan_id:Digest,engine=Depends(get_recovery)):
    def read():
        if engine.store.settings.sample: raise ValueError('Sample mode cannot read a live server')
        engine.remote=CentralRecovery(engine.store.settings)
        try: return engine.recheck(plan_id)
        finally: engine.remote.client.close()
    return recovery_error(read)


@app.get('/recovery/plans/{plan_id}/result')
def recovery_result(plan_id: Digest, engine=Depends(get_recovery)):
    return recovery_error(lambda: engine.result(plan_id))


@app.get('/recovery/plans/{plan_id}/evidence/{sha}')
def recovery_evidence(plan_id: Digest, sha: Digest, engine=Depends(get_recovery)):
    return Response(recovery_error(lambda: engine.evidence(plan_id,sha)),media_type='application/octet-stream')


@app.exception_handler(ImportRejected)
async def rejected(request, error):
    return JSONResponse(status_code=422, content={'detail': str(error)})


async def bounded_body(request, limit):
    payload = bytearray()
    async for chunk in request.stream():
        if len(payload) + len(chunk) > limit:
            raise HTTPException(413, 'Input exceeds configured upload limit')
        payload.extend(chunk)
    return bytes(payload)


@app.post('/inputs/{kind}', response_model=RegisteredInput, status_code=201)
async def register_input(kind: Literal['device', 'server', 'manifest'], request: Request, store: RunStore = Depends(get_store)):
    data = await bounded_body(request, min(65536 if kind == 'manifest' else 10485760, store.settings.limit('MAX_UPLOAD_BYTES')))
    return store.register(kind, data)


@app.post('/run', response_model=JobStatus, status_code=202)
def start_run(body: RunRequest, background: BackgroundTasks, store: RunStore = Depends(get_store)):
    try:
        status = store.enqueue(body)
    except KeyError:
        raise HTTPException(404, 'Registered input not found or wrong kind') from None
    except ValueError as error:
        if isinstance(error, ImportRejected):
            raise
        raise HTTPException(409, str(error)) from None
    if status.state == 'queued':
        background.add_task(store.drain)
    return status


@app.get('/runs/{run_id}', response_model=JobStatus)
def run_status(run_id: str, store: RunStore = Depends(get_store)):
    try:
        return store.get(run_id)
    except KeyError:
        raise HTTPException(404, 'Run not found') from None


@app.post('/runs/{run_id}/cancel', response_model=JobStatus)
def cancel_run(run_id: str, store: RunStore = Depends(get_store)):
    try:
        return store.cancel(run_id)
    except KeyError:
        raise HTTPException(404, 'Run not found') from None


@app.get('/runs/{run_id}/events')
def run_events(run_id: str, store: RunStore = Depends(get_store)):
    try:
        return Response(store.events(run_id), media_type='application/x-ndjson')
    except KeyError:
        raise HTTPException(404, 'Run not found') from None


@app.get('/runs/{run_id}/artifacts/{name}')
def run_artifact(run_id: str, name: str, store: RunStore = Depends(get_store)):
    try:
        return Response(store.artifact(run_id, name), media_type='application/x-ndjson' if name.endswith('.jsonl') else 'application/json')
    except KeyError:
        raise HTTPException(404, 'Run artifact not found') from None


@app.get("/health", response_model=Health)
def health():
    return Health(mode="sample" if Settings.load().sample else "connected")


@app.get("/configuration", response_model=ConfigurationStatus)
def configuration():
    return Settings.load().status()


@app.get("/sample/inventory", response_model=ImportInventory)
def sample_inventory():
    # Explicit sample endpoint cannot silently replace connected behavior.
    if not Settings.load().sample:
        raise HTTPException(409, "Sample inventory requires SAMPLE_MODE=true")
    return inventory((ROOT / "fixtures/representative/device.zip").read_bytes(), Settings.load())


@app.post("/imports/validate", response_model=ImportInventory)
async def validate_import(request: Request):
    settings = Settings.load()
    if not settings.status().ready and settings.status().errors:
        raise HTTPException(503, "Invalid configuration; inspect /configuration")
    limit = settings.limit("MAX_UPLOAD_BYTES")
    payload = bytearray()
    async for chunk in request.stream():
        if len(payload) + len(chunk) > limit:
            raise HTTPException(413, "Archive exceeds MAX_UPLOAD_BYTES")
        payload.extend(chunk)
    try:
        return inventory(bytes(payload), settings)
    except ImportRejected as e:
        raise HTTPException(422, str(e)) from None


from .ui_api import router as ui_router
app.include_router(ui_router)
