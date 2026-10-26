"""On-host read-only acceptance; credentials never leave the existing host.

Uses a temporary account store and the operator's existing Viewer credential.
This does not claim public Central provisioning or another Cognito signup.
"""
import json
import stat
import tempfile
from pathlib import Path
from lastcopy.config import Settings
from lastcopy.accounts import AccountStore
from lastcopy.account_connection import ConnectionSetup,save_connection,load
from lastcopy.odk_recovery import configured_target
from lastcopy import odk_recovery
from lastcopy.inventory import digest


def main():
    root=Settings.load()
    assert not root.sample
    receipts=[]
    original=odk_recovery.CentralRecovery
    class Observed(original):
        def request(self,method,path,**kwargs):
            assert method=='GET' or method=='POST' and path=='/v1/sessions'
            code,body=super().request(method,path,**kwargs)
            if method=='GET':receipts.append({'method':method,'path':path,'status':code,'sha256':digest(body)})
            return code,body
    odk_recovery.CentralRecovery=Observed
    try:
        with tempfile.TemporaryDirectory(prefix='lastcopy-account-connection-') as folder:
            selected=Settings({'SAMPLE_MODE':'false','LASTCOPY_ACCOUNT_STORE':'true',
                               'LASTCOPY_ALLOWED_CENTRAL_ORIGIN':root.values['ODK_BASE_URL']})
            first=AccountStore(Path(folder)/'a',selected,Path(folder))
            second=AccountStore(Path(folder)/'b',selected,Path(folder))
            assert not load(second.directory,selected)
            result=save_connection(first,ConnectionSetup(
                project_id=int(root.values['ODK_READ_PROJECT_ID']),form_id=root.values['ODK_READ_FORM_ID'],
                email=root.values['ODK_EMAIL'],password=root.values['ODK_PASSWORD']))
            assert result['state']=='connected' and result['record_writes']==0
            saved=load(first.directory,selected)
            assert saved['ODK_READ_PROJECT_ID']==root.values['ODK_READ_PROJECT_ID']
            assert stat.S_IMODE((first.directory/'central-connection.json').stat().st_mode)==0o600
            assert not load(second.directory,selected)
            try:configured_target(first.settings)
            except ValueError:pass
            else:raise AssertionError('Account connection unexpectedly enabled recovery')
            print(json.dumps({'status':'passed','scope':'Temporary account stores; actual configured Central Viewer GETs',
                'public_signup_repeated':False,'central_provisioning_claimed':False,'credentials_exported':False,
                'second_account_configured':False,'record_writes':0,'recovery_enabled':False,'receipts':receipts}))
    finally:odk_recovery.CentralRecovery=original


if __name__=='__main__':main()
