"""Provision only the approved empty cloud collection and synthetic test scope.

Fixed host/release guards; private credentials passed over verified SSH stdin.
Does not create submissions or modify existing form bytes.
"""
import json,secrets,subprocess
import httpx
from dotenv import dotenv_values
from lastcopy.config import ROOT
from lastcopy.inventory import digest
from scripts.setup_odk_test import CENTRAL_COMMIT,CENTRAL_RELEASE

BASE='https://central-18-141-113-136.sslip.io'
SSH=['C:/Program Files/Git/usr/bin/ssh.exe','-i','private/cloud/lightsail-ap-southeast-1.pem',
    '-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=52.77.228.162',
    '-o','UserKnownHostsFile=private/cloud/known_hosts','ubuntu@18.141.113.136']


def main():
    path=ROOT/'private/cloud/access.json';secret=json.loads(path.read_text(encoding='utf-8'))
    if 'agent_password' not in secret:
        secret.update(agent_email='lastcopy-agent@example.invalid',agent_password=secrets.token_urlsafe(32))
        path.write_text(json.dumps(secret,indent=2)+'\n',encoding='utf-8')
    receipts=[]
    def admin(email,command,password=None):
        assert email in (secret['central_email'],secret['agent_email']) and command in ('user-create','user-promote')
        result=subprocess.run(SSH+['sudo docker exec -i lastcopy-cloud-odk-service-1 odk-cmd --email '+email+' '+command],
            input=password+'\n' if password else None,text=True,capture_output=True,timeout=60,cwd=ROOT)
        if result.returncode:
            detail=result.stdout+result.stderr
            (ROOT/'private/cloud/account-error.txt').write_text(detail,encoding='utf-8')
            for value in secret.values():
                if isinstance(value,str) and len(value)>=8:detail=detail.replace(value,'[redacted]')
            raise ValueError('Central account command failed: '+detail[:1800])
    with httpx.Client(timeout=30,trust_env=False,follow_redirects=False) as c:
        def req(method,path,**kw):
            response=c.request(method,BASE+path,**kw)
            if response.status_code>=300:raise ValueError(f'Cloud setup {method} {path} failed HTTP {response.status_code}')
            if path!='/v1/sessions':receipts.append({'method':method,'scope':path,'status':response.status_code,'response_sha256':digest(response.content)})
            return response
        if CENTRAL_COMMIT not in req('GET','/version.txt').text:raise ValueError('Unexpected Central release')
        login=c.post(BASE+'/v1/sessions',json={'email':secret['central_email'],'password':secret['central_password']})
        if login.status_code==401:
            admin(secret['central_email'],'user-create',secret['central_password']);admin(secret['central_email'],'user-promote')
            login=req('POST','/v1/sessions',json={'email':secret['central_email'],'password':secret['central_password']})
        if login.status_code!=200:raise ValueError('Cloud administrator sign-in unavailable')
        c.headers['Authorization']='Bearer '+login.json()['token']
        projects=req('GET','/v1/projects').json();created=[]
        form=(ROOT/'forms/water-point-condition/water-point-condition-v2.xml').read_bytes();fid='lastcopy_water_point_v1'
        for name in ('Water Point Condition Check','LastCopy cloud recovery (synthetic)'):
            found=[p for p in projects if p['name']==name]
            if len(found)>1:raise ValueError('Ambiguous existing cloud project')
            project=found[0] if found else req('POST','/v1/projects',json={'name':name}).json()
            scope=f"/v1/projects/{project['id']}/forms"
            forms=req('GET',scope).json()
            if not any(f['xmlFormId']==fid for f in forms):req('POST',scope+'?publish=true',content=form,headers={'Content-Type':'application/xml'})
            if req('GET',scope+'/'+fid+'.xml').content!=form:raise ValueError('Existing form bytes differ; no overwrite permitted')
            count=len(req('GET',scope+'/'+fid+'/submissions').json())
            created.append({'id':project['id'],'name':name,'form_id':fid,'form_sha256':digest(form),'submissions':count})
        users=req('GET','/v1/users').json()
        found=[u for u in users if u.get('email')==secret['agent_email']]
        if not found:
            admin(secret['agent_email'],'user-create',secret['agent_password'])
            found=[u for u in req('GET','/v1/users').json() if u.get('email')==secret['agent_email']]
        if len(found)!=1:raise ValueError('Ambiguous automation account')
        actor=found[0]['id']
        for project,role in zip(created,('viewer','manager')):
            assignments=req('GET',f"/v1/projects/{project['id']}/assignments/{role}").json()
            if not any(a['id']==actor for a in assignments):req('POST',f"/v1/projects/{project['id']}/assignments/{role}/{actor}")
        # Scope collection credentials to the single form; no broad account token.
        pid=created[0]['id'];users=req('GET',f'/v1/projects/{pid}/app-users').json()
        found=[u for u in users if u.get('displayName')=='LastCopy paired collection device']
        user=found[0] if len(found)==1 else req('POST',f'/v1/projects/{pid}/app-users',json={'displayName':'LastCopy paired collection device'}).json() if not found else None
        if not user or not user.get('token'):raise ValueError('App User mapping requires review')
        scope=f'/v1/projects/{pid}/forms/{fid}/assignments/app-user'
        if not any(a['id']==user['id'] for a in req('GET',scope).json()):req('POST',scope+'/'+str(user['id']))
        settings={'general':{'server_url':BASE+'/v1/key/'+user['token']+f'/projects/{pid}','autosend':'wifi_only','delete_send':False},'admin':{},'project':{'name':'Water Point Condition Check','icon':'W','color':'#193A30'}}
        (ROOT/'private/cloud/collect-settings.json').write_text(json.dumps(settings,indent=2)+'\n',encoding='utf-8')
        base_values=dotenv_values(ROOT/'private/cloud/api.env')
        base_values.update(SAMPLE_MODE='false',ODK_BASE_URL=BASE,ODK_EMAIL=secret['agent_email'],ODK_PASSWORD=secret['agent_password'],
            ODK_CENTRAL_VERSION=CENTRAL_RELEASE,ODK_TEST_PROJECT='true',ODK_PROJECT_ID=str(created[1]['id']),ODK_FORM_ID=fid,
            ODK_RECOVERY_PROJECT_ID=str(created[1]['id']),ODK_RECOVERY_FORM_ID=fid,ODK_RECOVERY_PROJECT_NAME=created[1]['name'],ODK_CONNECTION_ID='aws-central-recovery',
            ODK_READ_PROJECT_ID=str(pid),ODK_READ_FORM_ID=fid,ODK_READ_PROJECT_NAME=created[0]['name'],ODK_READ_CONNECTION_ID='aws-central-collection',
            LASTCOPY_WATCH_INBOX='/app/private/inbox',LASTCOPY_WATCH_DEVICE_IDS='["water-field-01"]',LASTCOPY_WATCH_INTERVAL_SECONDS='60',LASTCOPY_WATCH_MAX_CHECKS='120')
        (ROOT/'private/cloud/api.env').write_text(''.join(k+'='+v+'\n' for k,v in base_values.items()),encoding='utf-8',newline='\n')
    output={'central_url':BASE,'central_release':CENTRAL_RELEASE,'projects':created,'requests':receipts,'submissions_created':0,
        'automation_permissions':'Viewer on collection; Manager on dedicated synthetic recovery project only','app_user_id':user['id']}
    (ROOT/'docs/verification/cloud/project-setup.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:output[k] for k in ('central_release','projects','submissions_created','automation_permissions')}))


if __name__=='__main__':main()
