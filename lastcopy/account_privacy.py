"""Account-owned export and reviewed erasure requests; never automatic deletion."""
import time
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from fastapi.responses import Response
from .api import request_store
from .accounts import AccountStore
from .models import Contract
from .inventory import digest
from .recovery import archive
from .store import encoded,RunStore

router=APIRouter(prefix='/ui/account')


def account(store=Depends(request_store)):
    if not isinstance(store,AccountStore):raise HTTPException(403,'This control belongs to a verified private account, not operator access.')
    return store


class ErasureRequest(Contract):
    confirm_reviewed_request: bool


class PrivacyStatus(Contract):
    request_state: str
    requested_at: str | None
    automatic_deletion: bool=False
    backup_policy: str='Existing encrypted backups are retained. The proposed 30-day expiry policy is not active.'


def status(store):
    with store.connect() as c:
        c.execute('CREATE TABLE IF NOT EXISTS privacy_request(id INTEGER PRIMARY KEY CHECK(id=1),requested_at TEXT NOT NULL,state TEXT NOT NULL)')
        row=c.execute('SELECT requested_at,state FROM privacy_request WHERE id=1').fetchone()
    return {'request_state':row[1] if row else 'not_requested','requested_at':row[0] if row else None,
            'automatic_deletion':False,'backup_policy':PrivacyStatus.model_fields['backup_policy'].default}


@router.get('',response_model=PrivacyStatus)
def privacy_status(store=Depends(account)):return status(store)


@router.post('/request',response_model=PrivacyStatus)
def request_erasure(body:ErasureRequest,store=Depends(account)):
    if not body.confirm_reviewed_request:raise HTTPException(422,'Confirm that this is a reviewed erasure request, not an immediate deletion.')
    status(store)
    with store.connect() as c:
        c.execute('INSERT OR IGNORE INTO privacy_request VALUES(1,?,?)',(datetime.now(timezone.utc).isoformat(),'awaiting_operator_review'))
    return status(store)


@router.get('/export')
def export_sources(store=Depends(account)):
    files={};total=0;deadline=time.monotonic()+15
    with RunStore(store.account_root/'account-export-admission',store.settings).lease() as admitted, store.lease() as held:
        if not admitted or not held:raise HTTPException(409,'Wait for the current check or export to finish before exporting.')
        with store.connect() as c:
            c.execute('BEGIN')
            if c.execute("SELECT 1 FROM jobs WHERE state IN ('queued','running')").fetchone():
                raise HTTPException(409,'Finish or cancel queued checks before exporting.')
            for identifier,kind,expected,data in c.execute('SELECT id,kind,sha,data FROM inputs ORDER BY id'):
                if kind not in ('device','server','manifest') or digest(data)!=expected or digest(kind.encode()+b'\0'+data)!=identifier:
                    raise HTTPException(409,'Original input integrity could not be verified.')
                total+=len(data)
                if total>128*1024**2 or len(files)>=4000 or time.monotonic()>deadline:raise HTTPException(413,'Private export exceeds the bounded beta export limit.')
                files[f'originals/{identifier}.{kind}']=data
            for rid,name,expected,data in c.execute('SELECT run_id,name,sha,data FROM artifacts ORDER BY run_id,name'):
                if digest(data)!=expected:raise HTTPException(409,'Report integrity could not be verified.')
                total+=len(data)
                if total>128*1024**2 or len(files)>=4000 or time.monotonic()>deadline:raise HTTPException(413,'Private export exceeds the bounded beta export limit.')
                # Stored identities are validated again before becoming archive paths.
                import re
                if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',rid) or name not in ('report.json','findings.json','receipts.json','events.jsonl'):
                    raise HTTPException(409,'Unexpected stored report identity.')
                files[f'reports/{rid}/{name}']=data
        files['manifest.json']=encoded({'scope':'Your registered originals and deterministic reports; no passwords, account session tokens, connection files or provider keys',
            'files':{name:digest(data) for name,data in sorted(files.items())}})
        body=archive(files)
    return Response(body,media_type='application/zip',headers={'Content-Disposition':'attachment; filename="lastcopy-private-files.zip"',
        'Cache-Control':'no-store','X-Content-SHA256':digest(body),'X-Content-Type-Options':'nosniff'})
