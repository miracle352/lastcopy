from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import Response, JSONResponse
from typing import Literal
from .config import Settings, ROOT
from .models import Health, ConfigurationStatus, ImportInventory
from .inventory import inventory, ImportRejected
from .models import RunRequest, JobStatus, RegisteredInput
from .store import RunStore

app = FastAPI(title="LastCopy", version="0.1.0", docs_url=None, redoc_url=None)


@app.middleware('http')
async def run_body_limit(request, call_next):
    if request.url.path == '/run' and request.method == 'POST':
        try:
            request._body = await bounded_body(request, 65536)
        except HTTPException:
            return JSONResponse(status_code=413, content={'detail': 'Run request exceeds 64 KiB'})
    return await call_next(request)


def get_store():
    # Configured by the local operator only; never supplied by an HTTP request.
    settings = Settings.load()
    return RunStore(settings.values.get('LASTCOPY_DATA_DIR') or ROOT / 'private/stage2', settings)


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
