"""Publish the reviewed namespace correction as a new local form version.

Retains both source definitions and existing server history. No submissions.
"""
import json
import httpx
from dotenv import dotenv_values
from lastcopy.config import ROOT
from lastcopy.inventory import digest
from scripts.setup_water_point import FORM_ID,NAMES


def main():
    v=dotenv_values(ROOT/'.env');base='http://localhost:8384'
    if v.get('ODK_BASE_URL')!=base:raise ValueError('Local Central only')
    old=(ROOT/'forms/water-point-condition/water-point-condition.xml').read_bytes()
    new=(ROOT/'forms/water-point-condition/water-point-condition-v2.xml').read_bytes();receipts=[]
    with httpx.Client(timeout=30,trust_env=False,follow_redirects=False) as c:
        r=c.post(base+'/v1/sessions',json={'email':v['ODK_EMAIL'],'password':v['ODK_PASSWORD']})
        if r.status_code!=200:raise ValueError('Authentication failed')
        c.headers['Authorization']='Bearer '+r.json()['token']
        def req(method,path,**kw):
            r=c.request(method,base+path,**kw)
            if r.status_code!=200:raise ValueError(f'Form revision failed HTTP {r.status_code}')
            receipts.append({'method':method,'scope':path,'status':r.status_code,'response_sha256':digest(r.content)})
            return r
        for pid,name in ((3,NAMES[0]),(4,NAMES[1])):
            if req('GET',f'/v1/projects/{pid}').json()['name']!=name:raise ValueError('Project identity changed')
            scope=f'/v1/projects/{pid}/forms/{FORM_ID}'
            current=req('GET',scope+'.xml').content
            if current==new:continue
            if current!=old:raise ValueError('Unexpected form contents; refusing replacement')
            req('POST',scope+'/draft',content=new,headers={'Content-Type':'application/xml'})
            assert req('GET',scope+'/draft.xml').content==new
            req('POST',scope+'/draft/publish')
            assert req('GET',scope+'.xml').content==new
            history=req('GET',scope+'/versions').json()
            assert {'2026102501','2026102502'}<={str(x['version']) for x in history}
        output={'operation':'local form version 2026102502 published; prior version retained','requests':receipts,
            'old_form_sha256':digest(old),'new_form_sha256':digest(new),'submissions_created':0}
        (ROOT/'private/water-point/form-revision.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'version':'2026102502','history_retained':True,'submissions_created':0}))


if __name__=='__main__':main()
