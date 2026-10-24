"""Read-only real CLI/HTTP capture -> registered /run acceptance on an existing fixture."""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
import httpx
from lastcopy.config import ROOT, Settings
from lastcopy.store import RunStore, encoded
from lastcopy.inventory import digest
from lastcopy.models import RunManifest


def verify(directory, inputs, output):
    ids=json.loads(inputs.read_bytes())
    settings=Settings.load()
    if settings.sample: raise ValueError('Explicit connected mode is required')
    store=RunStore(directory,settings)
    run=RunManifest.model_validate_json(store.input(ids['manifest_id'],'manifest'))
    run=run.model_copy(update={'run_id':run.run_id+'-capture-entrypoint'})
    m=store.register('manifest',run.model_dump_json().encode())
    env=dict(os.environ,SAMPLE_MODE='false',LASTCOPY_DATA_DIR=str(directory.resolve()))
    cli=subprocess.run([sys.executable,'-m','scripts.recover','--data-dir',str(directory),'capture',m.input_id,
        '--device-input-id',ids['device_input_id']],cwd=ROOT,env=env,capture_output=True,timeout=150)
    if cli.returncode: raise ValueError('Documented CLI capture failed')
    captured=json.loads(cli.stdout)
    if captured['mode']!='connected': raise ValueError('CLI capture mode changed')
    server=subprocess.Popen([sys.executable,'-m','uvicorn','lastcopy.api:app','--host','127.0.0.1','--port','8000'],
        cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    try:
        with httpx.Client(base_url='http://127.0.0.1:8000',timeout=150,trust_env=False) as client:
            for _ in range(40):
                if server.poll() is not None: raise ValueError('Temporary API could not start on port 8000')
                try:
                    if client.get('/health').status_code==200: break
                except httpx.TransportError: pass
                time.sleep(0.25)
            response=client.post('/recovery/capture',json={'manifest_id':m.input_id,'device_input_ids':[ids['device_input_id']]})
            if response.status_code!=201: raise ValueError('HTTP registered-ID capture failed')
            http_capture=response.json()
            response=client.post('/run',json={'manifest_id':http_capture['manifest_id'],
                'device_input_ids':[ids['device_input_id']],'server_input_id':http_capture['server_input_id']})
            if response.status_code!=202: raise ValueError('Registered captured inputs failed /run')
            for _ in range(60):
                status=client.get('/runs/'+run.run_id).json()
                if status['state'] not in ('queued','running'): break
                time.sleep(0.25)
            if status['state']!='completed': raise ValueError('Captured run did not complete')
            report=client.get('/runs/'+run.run_id+'/artifacts/report.json').content
            if [f['verdict'] for f in json.loads(report)['findings']]!=['PRESERVED']:
                raise ValueError('Captured live data does not preserve the actual fixture')
    finally:
        server.terminate(); server.wait(timeout=15)
    receipt={'mode':'connected','actual_central_capture':True,'cli_registered_capture':captured,
        'http_registered_capture':http_capture,'run_id':run.run_id,'run_status':status,
        'report_sha256':digest(report),'verdicts':['PRESERVED'],'writes':0,
        'scope':'Actual port-8000 capture and /run with registered IDs; no arbitrary paths or sample fallback'}
    output.write_bytes(encoded(receipt)); print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--data-dir',type=Path,required=True); p.add_argument('--inputs',type=Path,required=True); p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args(); verify(a.data_dir,a.inputs,a.receipt)
