"""Actual HTTPS/authentication/scope check. Never exports session credentials."""
import json
import httpx
from lastcopy.config import ROOT
from lastcopy.inventory import digest

BASE='https://api-18-141-113-136.sslip.io'


def main():
    secret=json.loads((ROOT/'private/cloud/access.json').read_text(encoding='utf-8'))
    receipts=[]
    with httpx.Client(timeout=30,trust_env=False,follow_redirects=False) as c:
        def req(method,path,**kwargs):
            response=c.request(method,BASE+path,**kwargs)
            receipts.append({'method':method,'path':path,'status':response.status_code,
                'response_sha256':digest(response.content),'tls_verified':True})
            return response
        assert req('GET','/ui/runs').status_code==401
        c.headers['Authorization']='Bearer '+secret['transport_key']
        assert req('GET','/ui/runs').status_code==401
        login=c.post(BASE+'/session/login',json={'password':secret['owner_passphrase']});assert login.status_code==200
        flags=login.headers['set-cookie'].lower()
        assert all(flag in flags for flag in ('secure','httponly','samesite=strict'))
        settings=req('GET','/ui/settings');assert settings.status_code==200
        settings=settings.json();assert settings['mode']=='connected' and settings['target']['project_id']==1
        connection=req('GET','/ui/connection');assert connection.status_code==200 and connection.json()['state']=='connected'
        assert connection.json()['project_name']=='Water Point Condition Check'
        watch=req('GET','/ui/watch');assert watch.status_code==200
        assert watch.json()['received_devices']==[] and watch.json()['last_run_id'] is None
        sample=req('GET','/public/examples/media');assert sample.status_code==200
        sample=sample.json();assert sample['manifest']['mode']=='sample' and sample['report']['provider_calls']==0
        assert sample['report']['findings'][0]['verdict']=='MISSING_ATTACHMENT'
        assert req('POST','/session/logout').status_code==200
        assert req('GET','/ui/runs').status_code==401
    result={'requests':receipts,'connected_read_scope':settings['target'],'connection':connection.json(),
        'empty_collection_honest':True,'private_reads_require_owner':True,'logout_revoked':True,
        'sample_isolated':True,'session_cookie_flags':['Secure','HttpOnly','SameSite=Strict'],'recovery_writes':0}
    (ROOT/'docs/verification/cloud/https-access.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PASS verified HTTPS, owner sessions, logout revocation, actual scoped Central connection, empty coverage and isolated real sample comparison')


if __name__=='__main__':main()
