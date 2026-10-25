"""Provision least-privilege local Collect accounts for the approved two forms.

Private settings contain App User tokens and must never be printed or committed.
No submission, deletion, admin grant, network exposure or cloud provisioning.
"""
import json,zlib,base64
import httpx
from dotenv import dotenv_values
from lastcopy.config import ROOT
from scripts.setup_water_point import FORM_ID,NAMES


def main():
    v=dotenv_values(ROOT/'.env');base='http://localhost:8384'
    if v.get('ODK_BASE_URL')!=base:raise ValueError('Existing loopback Central only')
    receipts=[]
    with httpx.Client(timeout=30,trust_env=False,follow_redirects=False) as c:
        login=c.post(base+'/v1/sessions',json={'email':v['ODK_EMAIL'],'password':v['ODK_PASSWORD']})
        if login.status_code!=200:raise ValueError('Authentication failed')
        c.headers['Authorization']='Bearer '+login.json()['token']
        for pid,name in ((3,NAMES[0]),(4,NAMES[1])):
            p=c.get(base+f'/v1/projects/{pid}')
            if p.status_code!=200 or p.json()['name']!=name:raise ValueError('Project identity differs')
            users=c.get(base+f'/v1/projects/{pid}/app-users');users.raise_for_status()
            label='LastCopy water-point '+('collection' if pid==3 else 'synthetic pilot')
            found=[x for x in users.json() if x.get('displayName')==label]
            if len(found)>1:raise ValueError('Ambiguous Collect account')
            if found:user=found[0]
            else:
                response=c.post(base+f'/v1/projects/{pid}/app-users',json={'displayName':label})
                response.raise_for_status();user=response.json()
            if not user.get('token'):raise ValueError('Existing Collect account has been revoked; operator review required')
            scope=f'/v1/projects/{pid}/forms/{FORM_ID}/assignments/app-user'
            assignments=c.get(base+scope);assignments.raise_for_status()
            if not any(x['id']==user['id'] for x in assignments.json()):
                assigned=c.post(base+scope+'/'+str(user['id']));assigned.raise_for_status()
            url=base+'/v1/key/'+user['token']+f'/projects/{pid}'
            # A separate client avoids sending conflicting admin/App User credentials.
            result=httpx.get(url+'/formList',headers={'X-OpenRosa-Version':'1.0'},timeout=30,trust_env=False)
            if result.status_code!=200 or FORM_ID.encode() not in result.content:raise ValueError('Collect form list did not verify')
            config={'general':{'server_url':url.replace('localhost','10.0.2.2'),'autosend':'off','delete_send':False},
                'admin':{},'project':{'name':name,'icon':'W','color':'#193A30'}}
            directory=ROOT/'private/water-point'/('collection-collect' if pid==3 else 'pilot-collect')
            directory.mkdir(exist_ok=True)
            (directory/'settings.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
            (directory/'qr-data.txt').write_text(base64.b64encode(zlib.compress(json.dumps(config).encode())).decode(),encoding='utf-8')
            receipts.append({'project_id':pid,'app_user_id':user['id'],'role':'app-user on the single water-point form',
                'form_list_status':result.status_code,'settings':'private local emulator configuration; tokens omitted'})
    output={'operation':'scoped Collect accounts configured','accounts':receipts,'submissions_created':0,'public_access_links_created':0}
    (ROOT/'private/water-point/collect-setup-receipt.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
