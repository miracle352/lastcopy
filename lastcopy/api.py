from fastapi import FastAPI, Request, HTTPException
from .config import Settings, ROOT
from .models import Health, ConfigurationStatus, ImportInventory
from .inventory import inventory, ImportRejected

app = FastAPI(title="LastCopy", version="0.1.0", docs_url=None, redoc_url=None)


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
