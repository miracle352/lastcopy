"""Run only inside a disposable --network none production container.

Self-checks the real HTTP API with providers unreachable; never mounts private sources.
"""
import hashlib
import io
import json
import socket
import subprocess
import sys
import time
import zipfile
from pathlib import Path
import httpx


def main():
    try:
        with socket.create_connection(('1.1.1.1',443),timeout=1):
            raise AssertionError('External network is reachable; offline verification refused')
    except OSError:
        pass
    sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('fixtures').rglob('*') if p.is_file()}
    child=subprocess.Popen([sys.executable,'-m','uvicorn','lastcopy.api:app','--host','127.0.0.1','--port','8000'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        with httpx.Client(base_url='http://127.0.0.1:8000',trust_env=False,timeout=30) as client:
            deadline=time.monotonic()+40
            while True:
                try:
                    if client.get('/health').status_code==200:break
                except httpx.TransportError:pass
                if time.monotonic()>deadline:raise AssertionError('Production API did not start')
                time.sleep(.1)
            expected={'media':['MISSING_ATTACHMENT'],'stranded':['PRESERVED','MISSING_SUBMISSION','MISSING_SUBMISSION'],
                      'export':['EXPORT_VIEW_ONLY'],'history':['PRESERVED'],'conflict':['CONTENT_CONFLICT']}
            results=[]
            for case,verdicts in expected.items():
                response=client.get('/public/demo/'+case);response.raise_for_status();view=response.json()
                report=view['current_report']
                assert view['manifest']['mode']=='sample' and report['provider_calls']==0
                assert [f['verdict'] for f in report['findings']]==verdicts
                downloads={}
                for name in ('report.txt','report.json','findings.json','trace.jsonl'):
                    data=client.get(f'/public/demo/{case}/downloads/{name}');data.raise_for_status()
                    downloads[name]=hashlib.sha256(data.content).hexdigest()
                results.append({'case':case,'verdicts':verdicts,'coverage_complete':report['coverage']['complete'],'downloads':downloads})
            bundle=client.get('/public/demo/media/bundle');bundle.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(bundle.content)) as archive:assert archive.testzip() is None
            after=client.post('/public/demo/media/readback');after.raise_for_status()
            assert after.json()['current_report']['preservation_outcome']=='verified'
            assert all(hashlib.sha256(Path(name).read_bytes()).hexdigest()==sha for name,sha in sources.items())
            print(json.dumps({'status':'passed','network':'Docker network none; external TCP probe refused',
                'api':'actual Uvicorn HTTP loopback','provider_calls':0,'source_files_unchanged':len(sources),
                'results':results,'bundle_sha256':hashlib.sha256(bundle.content).hexdigest(),
                'readback':'separately authored offline fixture; no upload performed'}))
    finally:
        child.terminate()
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:child.kill();child.wait()


if __name__=='__main__':main()
