"""Create the approved empty local collection project and a separate test pilot.

Never creates submissions, overwrites forms, modifies other projects or prints
credentials. Explicit loopback/version guard precedes every setup operation.
"""
import json
import subprocess
from pathlib import Path
from urllib.parse import quote
import httpx
from dotenv import dotenv_values,set_key
from lastcopy.config import ROOT
from lastcopy.inventory import digest
from scripts.setup_odk_test import CENTRAL_COMMIT,CENTRAL_RELEASE

FORM_ID='lastcopy_water_point_v1'
NAMES=('Water Point Condition Check','LastCopy water-point pilot (synthetic)')


def main():
    values=dotenv_values(ROOT/'.env');base='http://localhost:8384'
    if values.get('ODK_BASE_URL')!=base:raise ValueError('Setup is limited to the existing local Central')
    original=(ROOT/'forms/water-point-condition/water-point-condition.xml').read_bytes()
    revised=ROOT/'forms/water-point-condition/water-point-condition-v2.xml'
    form=revised.read_bytes() if revised.exists() else original;receipts=[]
    with httpx.Client(timeout=30,trust_env=False,follow_redirects=False) as c:
        def request(method,path,**kwargs):
            r=c.request(method,base+path,**kwargs)
            if r.status_code>=300:raise ValueError(f'Local setup {method} failed HTTP {r.status_code}')
            receipts.append({'method':method,'scope':path,'status':r.status_code,'response_sha256':digest(r.content)})
            return r
        version=request('GET','/version.txt').text
        if CENTRAL_COMMIT not in version:raise ValueError('Central version differs from reviewed local deployment')
        login=c.post(base+'/v1/sessions',json={'email':values['ODK_EMAIL'],'password':values['ODK_PASSWORD']})
        if login.status_code!=200:raise ValueError('Local setup authentication failed')
        c.headers['Authorization']='Bearer '+login.json()['token']
        projects=request('GET','/v1/projects').json();created=[]
        for name in NAMES:
            matches=[p for p in projects if p['name']==name]
            if len(matches)>1:raise ValueError('Ambiguous existing water-point project')
            project=matches[0] if matches else request('POST','/v1/projects',json={'name':name}).json()
            scope=f"/v1/projects/{project['id']}/forms"
            forms=request('GET',scope).json()
            if any(f['xmlFormId']==FORM_ID for f in forms):
                if request('GET',scope+'/'+FORM_ID+'.xml').content not in (form,original):raise ValueError('Existing form differs; refusing overwrite')
            else:request('POST',scope+'?publish=true',content=form,headers={'Content-Type':'application/xml'})
            served=request('GET',scope+'/'+FORM_ID+'.xml').content
            created.append({'id':project['id'],'name':name,'form_id':FORM_ID,'form_sha256':digest(served),'revision_needed':served!=form})
        output={'operation':'approved local water-point setup','central_version':CENTRAL_RELEASE,'projects':created,
            'requests':receipts,'submissions_created':0,'credentials':'existing private server-side settings only'}
        p=ROOT/'private/water-point';p.mkdir(exist_ok=True,parents=True)
        raw=(json.dumps(output,indent=2)+'\n').encode()
        receipt=p/('setup-'+digest(raw)[:20]+'.json')
        if not receipt.exists():receipt.write_bytes(raw)
        (p/'setup.json').write_bytes(raw)
        print(json.dumps(output,indent=2))


if __name__=='__main__':main()
