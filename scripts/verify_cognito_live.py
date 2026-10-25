"""Run in the signed-in AWS CloudShell. Suppressed-mail synthetic identities only.

This verifies actual Cognito -> hosted LastCopy identity/isolation. It does NOT
claim a human received verification/reset mail. Passwords/tokens never print.
Requires the operator's existing Cognito admin access, no new IAM permission.
"""
import argparse,json,secrets,subprocess,uuid,urllib.request,urllib.error,http.cookiejar

def main():
    p=argparse.ArgumentParser();p.add_argument('--pool-id',required=True);p.add_argument('--app-origin',required=True);a=p.parse_args()
    if a.app_origin!='https://app-18-141-113-136.sslip.io':raise ValueError('Unexpected LastCopy target')
    def aws(action,**kwargs):
        command=['aws','cognito-idp',action,'--user-pool-id',a.pool_id,'--region','ap-southeast-1','--output','json','--no-cli-pager']
        for key,value in kwargs.items():
            flag='--'+key.replace('_','-')
            if isinstance(value,bool):command.append(flag if value else '--no-'+key.replace('_','-'))
            else:command+=[flag,json.dumps(value) if isinstance(value,(dict,list)) else value]
        result=subprocess.run(command,capture_output=True,text=True,timeout=30)
        if result.returncode:raise RuntimeError('Cognito control operation failed; private diagnostic suppressed')
        return json.loads(result.stdout or '{}')
    def browser():return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def request(client,path,body=None):
        raw=json.dumps(body).encode() if body is not None else None
        req=urllib.request.Request(a.app_origin+path,data=raw,headers={'Content-Type':'application/json','Origin':a.app_origin})
        try:
            with client.open(req,timeout=45) as r:return r.status,json.loads(r.read())
        except urllib.error.HTTPError as e:return e.code,{}
    users=[];clients=[];checks=[]
    try:
        for i in range(2):
            email='lastcopy-control-'+uuid.uuid4().hex+'@example.invalid';password=secrets.token_urlsafe(24)+'aA7'
            aws('admin-create-user',username=email,message_action='SUPPRESS',user_attributes=[{'Name':'email','Value':email},{'Name':'email_verified','Value':'false'}]);users.append(email)
            aws('admin-set-user-password',username=email,password=password,permanent=True)
            client=browser();clients.append(client)
            assert request(client,'/api/account/login',{'email':email,'password':password})[0] in (401,403)
            checks.append('Actual unverified identity rejected')
            aws('admin-update-user-attributes',username=email,user_attributes=[{'Name':'email_verified','Value':'true'}])
            assert request(client,'/api/account/login',{'email':email,'password':password})[0]==200
            assert request(client,'/api/service/ui/runs')==(200,[])
        status,draft=request(clients[0],'/api/service/ui/samples/history',{})
        assert status==201;run=draft['run_id']
        assert request(clients[1],'/api/service/ui/runs/'+run)[0]==404
        assert request(clients[0],'/api/service/ui/runs/'+run)[0]==200
        assert request(clients[0],'/api/service/ui/cloud-ai')[0]==403
        assert request(clients[0],'/api/session/logout',{})[0]==200
        assert request(clients[0],'/api/service/ui/runs')[0]==401
        checks+=['Actual Cognito password auth and GetUser','Separate empty account stores','Cross-account run access rejected','Owner AI setup denied','Logout revocation']
        print(json.dumps({'status':'passed','provider':'AWS Cognito Lite','identity_control':'Synthetic admin-confirmed identities; mail SUPPRESS; not human email delivery verification','checks':checks,'field_or_recovery_writes':0,'passwords_or_tokens_exported':False,'cleanup':'Delete only these two generated Cognito control users; revoke local sessions'},indent=2))
    finally:
        for client in clients:request(client,'/api/session/logout',{})
        for email in users:aws('admin-delete-user',username=email)

if __name__=='__main__':main()
