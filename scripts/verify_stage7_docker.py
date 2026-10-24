"""Local Sample container acceptance, including actual restart persistence."""
import hashlib
import json
import subprocess
import time
from pathlib import Path
import httpx


def main():
    container='lastcopy-stage7-audit'
    with httpx.Client(base_url='http://127.0.0.1:3000/api/service',timeout=15,trust_env=False) as c:
        def ready():
            for _ in range(60):
                try:
                    r=c.get('/ui/settings')
                    if r.status_code==200:return r.json()
                except httpx.HTTPError:pass
                time.sleep(.5)
            raise AssertionError('Local container did not become ready')
        assert ready()['mode']=='sample'
        draft=c.post('/ui/samples/media').json();rid=draft['run_id']
        assert c.post('/ui/runs/'+rid+'/start').status_code==202
        for _ in range(100):
            view=c.get('/ui/runs/'+rid).json()
            if view['status']['state'] not in ('queued','running'):break
            time.sleep(.2)
        report=view['current_report'];assert report['findings'][0]['verdict']=='MISSING_ATTACHMENT'
        assert report['provider_calls']==0 and view['investigation'] is None
        plan=c.post('/ui/runs/'+rid+'/plans',json={'finding_id':report['findings'][0]['finding_id']}).json()
        bundle=c.get('/recovery/plans/'+plan['plan_id']+'/bundle');assert bundle.status_code==200
        bundle_hash=hashlib.sha256(bundle.content).hexdigest()
        lines=c.get('/ui/runs/'+rid+'/downloads/trace.jsonl').text.splitlines()
        assert all(isinstance(json.loads(line),dict) for line in lines)
        subprocess.run(['docker','restart',container],check=True,capture_output=True)
        assert ready()['mode']=='sample'
        after=c.get('/ui/runs/'+rid).json();assert after['current_report']==report
        assert hashlib.sha256(c.get('/recovery/plans/'+plan['plan_id']+'/bundle').content).hexdigest()==bundle_hash
        assert subprocess.check_output(['docker','exec',container,'id','-u'],text=True).strip()=='10001'
        subprocess.run(['docker','exec',container,'python','-c',"from pathlib import Path;assert not Path('/app/.env').exists();assert {p.name for p in Path('/app/private').iterdir()}=={'container'}"],check=True)
        runtime={name:subprocess.check_output(['docker','exec',container,*args],text=True).strip() for name,args in [('python',['python','--version']),('node',['node','--version'])]}
        result={'status':'passed','mode':'sample','runtime':runtime,'run_id':rid,'verdict':'MISSING_ATTACHMENT',
            'non_root_uid':10001,'private_config_absent':True,'restart_retains_report_and_bundle':True,
            'provider_calls':0,'bundle_sha256':bundle_hash,'jsonl_parseable':True,
            'image_id':subprocess.check_output(['docker','inspect','--format','{{.Image}}',container],text=True).strip(),
            'scope':'Actual local Docker production UI/API; Sample only; host-loopback published ports; no registry publication'}
        Path('docs/verification/stage7/docker.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
        print(json.dumps(result))


if __name__=='__main__':main()
