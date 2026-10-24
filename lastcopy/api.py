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

app = FastAPI(title="LastCopy", version="0.1.0", docs_url=None, redoc_url=None)


@app.middleware('http')
async def run_body_limit(request, call_next):
    if (request.url.path == '/run' or request.url.path.startswith('/recovery/')) and request.method == 'POST':
        try:
            request._body = await bounded_body(request, 65536)
        except HTTPException:
            return JSONResponse(status_code=413, content={'detail': 'Run request exceeds 64 KiB'})
    return await call_next(request)


def get_store():
    # Configured by the local operator only; never supplied by an HTTP request.
    settings = Settings.load()
    return RunStore(settings.values.get('LASTCOPY_DATA_DIR') or ROOT / 'private/stage2', settings)


def get_recovery(store: RunStore = Depends(get_store)):
    return RecoveryEngine(store, None if store.settings.sample else configured_target(store.settings))


def recovery_error(action):
    try:
        return action()
    except KeyError:
        raise HTTPException(404, 'Registered recovery object not found') from None
    except ValueError as error:
        raise HTTPException(409, str(error)) from None


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
