"""Sample runtime/restart verification inside a network-disabled local image."""
import json
import subprocess
from uuid import uuid4
from pathlib import Path

WORKER=r'''
import hashlib,json,time
from pathlib import Path
import httpx
checkpoint=Path('/app/private/container/redesign-checkpoint.json')
with httpx.Client(base_url='http://127.0.0.1:3000',timeout=15,trust_env=False) as c:
 for _ in range(60):
  try:
   if c.get('/api/service/ui/settings').status_code==200:break
  except httpx.HTTPError:pass
  time.sleep(.5)
 else:raise AssertionError('Container UI/API did not become ready')
 assert c.get('/api/service/ui/settings').json()['mode']=='sample'
 assert c.get('/').status_code==200
 for font in ['figtree-latin.woff2','fraunces-latin.woff2']:
  response=c.get('/fonts/'+font);assert response.status_code==200 and len(response.content)>10000
 if not checkpoint.exists():
  rid=c.post('/api/service/ui/samples/media').json()['run_id']
  assert c.post('/api/service/ui/runs/'+rid+'/start').status_code==202
  for _ in range(100):
   view=c.get('/api/service/ui/runs/'+rid).json()
   if view['status']['state'] not in ('queued','running'):break
   time.sleep(.2)
  report=view['current_report']
  assert report['findings'][0]['verdict']=='MISSING_ATTACHMENT'
  assert report['provider_calls']==0 and view['investigation'] is None
  pid=c.post('/api/service/ui/runs/'+rid+'/plans',json={'finding_id':report['findings'][0]['finding_id']}).json()['plan_id']
  bundle=c.get('/api/service/recovery/plans/'+pid+'/bundle');assert bundle.status_code==200
  saved={'run_id':rid,'plan_id':pid,'report':report,'bundle_sha256':hashlib.sha256(bundle.content).hexdigest()}
  checkpoint.write_text(json.dumps(saved),encoding='utf8')
  print(json.dumps({'phase':'created','run_id':rid,'bundle_sha256':saved['bundle_sha256']}))
 else:
  saved=json.loads(checkpoint.read_text(encoding='utf8'))
  assert c.get('/api/service/ui/runs/'+saved['run_id']).json()['current_report']==saved['report']
  bundle=c.get('/api/service/recovery/plans/'+saved['plan_id']+'/bundle');assert bundle.status_code==200
  assert hashlib.sha256(bundle.content).hexdigest()==saved['bundle_sha256']
  assert not Path('/app/.env').exists()
  print(json.dumps({'phase':'restored','run_id':saved['run_id'],'bundle_sha256':saved['bundle_sha256'],'provider_calls':0,'preserved_report':True,'private_config_absent':True,'self_hosted_fonts':True}))
'''

def main():
    name='lastcopy-redesign-check-'+uuid4().hex[:8]
    image='lastcopy:redesign'
    subprocess.run(['docker','run','-d','--pull=never','--name',name,'--network','none',image],check=True,capture_output=True)
    try:
        def verify():
            result=subprocess.run(['docker','exec','-i',name,'python','-'],input=WORKER.encode(),capture_output=True,check=True,timeout=150)
            return json.loads(result.stdout)
        before=verify()
        subprocess.run(['docker','restart',name],check=True,capture_output=True)
        after=verify()
        assert before['run_id']==after['run_id']
        assert subprocess.check_output(['docker','exec',name,'id','-u'],text=True).strip()=='10001'
        runtime={key:subprocess.check_output(['docker','exec',name,*command],text=True).strip() for key,command in [('node',['node','--version']),('python',['python','--version'])]}
        result={'status':'passed','mode':'sample','network':'none','container':name,'non_root_uid':10001,'runtime':runtime,'before':before,'after_restart':after,'image_id':subprocess.check_output(['docker','inspect','--format','{{.Image}}',name],text=True).strip(),'scope':'Actual container production UI/API and comparator. Container-local loopback only; no host published ports, models or external evidence.'}
        Path('docs/verification/redesign/container.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
        print(json.dumps(result))
    finally:
        subprocess.run(['docker','stop',name],check=True,capture_output=True)

if __name__=='__main__':main()
