"""Fixed offline judge cases, physically separate from private user evidence.

No uploaded files, user paths, provider calls or arbitrary run/plan identifiers.
Readback uses a separately authored fixture and is never described as an upload.
"""
import threading
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,Request
from fastapi.responses import Response
from .config import Settings
from .store import RunStore
from .models import RunRequest,UIRunView,UIFindingEvidence,RecoveryPlan
from .ui import Workspace

router=APIRouter(prefix='/public/demo')
CASES=Literal['media','stranded','export','history','conflict']
_lock=threading.Lock()


def workspace():
    from .api import app,get_store
    base=app.dependency_overrides.get(get_store,get_store)()
    return Workspace(RunStore(base.directory/'public-examples',Settings({'SAMPLE_MODE':'true'})))


def opened(ws,case,readback=False):
    draft=ws.example(case)
    ws.store.enqueue(RunRequest.model_validate(draft['request']));ws.store.drain()
    view=ws.view(draft['run_id'])
    if readback:
        if not view['sample_readback_run_id']:raise KeyError()
        return ws.view(view['sample_readback_run_id'])
    return view


def safe(action):
    try:return action()
    except KeyError:raise HTTPException(404,'Example evidence not found') from None
    except ValueError:raise HTTPException(409,'This example action could not complete; no files were uploaded') from None


@router.get('/{case}',response_model=UIRunView)
def view(case:CASES,ws=Depends(workspace)):
    with _lock:return safe(lambda:opened(ws,case))


@router.get('/{case}/evidence/{finding_id}',response_model=UIFindingEvidence)
@router.get('/{case}/readback/evidence/{finding_id}',response_model=UIFindingEvidence)
def evidence(case:CASES,finding_id:str,request:Request,ws=Depends(workspace)):
    return safe(lambda:ws.finding(opened(ws,case,'/readback/' in request.url.path)['manifest']['run_id'],finding_id))


@router.get('/{case}/objects/{sha}')
@router.get('/{case}/readback/objects/{sha}')
def original(case:CASES,sha:str,request:Request,ws=Depends(workspace)):
    def read():
        objects=ws.objects(opened(ws,case,'/readback/' in request.url.path)['manifest']['run_id'])
        if sha not in objects:raise KeyError()
        return Response(objects[sha]['data'],media_type='application/octet-stream',headers={'X-Content-Type-Options':'nosniff'})
    return safe(read)


@router.get('/{case}/downloads/{name}')
@router.get('/{case}/readback/downloads/{name}')
def download(case:CASES,name:str,request:Request,ws=Depends(workspace)):
    if name not in ('report.txt','report.json','findings.json','trace.jsonl'):raise HTTPException(404,'Example download not found')
    def read():
        data,mime=ws.download(opened(ws,case,'/readback/' in request.url.path)['manifest']['run_id'],name)
        return Response(data,media_type=mime,headers={'Content-Disposition':f'attachment; filename="lastcopy-example-{name}"'})
    return safe(read)


def prepared(ws,case):
    current=opened(ws,case);findings=current['report']['findings']
    finding=next((f for f in findings if f['recovery_eligible']),None)
    if not finding:raise ValueError('No permitted example recovery')
    engine=ws.engine(current['manifest']['run_id'])
    return engine,engine.stage(current['manifest']['run_id'],finding['finding_id'])

@router.get('/{case}/plan',response_model=RecoveryPlan)
def plan(case:CASES,ws=Depends(workspace)):
    with _lock:return safe(lambda:prepared(ws,case)[1])

@router.get('/{case}/bundle')
def bundle(case:CASES,ws=Depends(workspace)):
    def stage():
        engine,plan=prepared(ws,case)
        return Response(engine.bundle(plan['plan_id']),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="lastcopy-offline-example-bundle.zip"'})
    with _lock:return safe(stage)


@router.post('/{case}/readback',response_model=UIRunView)
def readback(case:CASES,ws=Depends(workspace)):
    def check():
        before=opened(ws,case)
        draft=ws.sample_readback(before['manifest']['run_id'])
        ws.store.enqueue(RunRequest.model_validate(draft['request']));ws.store.drain()
        return ws.view(draft['run_id'])
    with _lock:return safe(check)
