"""Start the approved read-only cloud monitor after checking its actual scope."""
import json
import httpx
from lastcopy.config import ROOT


def main():
    values=json.loads((ROOT/'private/cloud/access.json').read_text(encoding='utf-8'))
    base='https://api-18-141-113-136.sslip.io'
    with httpx.Client(timeout=30,trust_env=False,follow_redirects=False,headers={'Authorization':'Bearer '+values['transport_key']}) as client:
        login=client.post(base+'/session/login',json={'password':values['owner_passphrase']});assert login.status_code==200
        connection=client.get(base+'/ui/connection');assert connection.status_code==200
        connection=connection.json();assert connection['state']=='connected' and connection['project_id']==1 and connection['project_name']=='Water Point Condition Check'
        status=client.post(base+'/ui/watch/control',json={'action':'start'});assert status.status_code==200
        status=status.json();assert status['enabled'] and status['expected_devices']==['water-field-01']
        assert status['received_devices']==[] and status['last_run_id'] is None
        client.post(base+'/session/logout').raise_for_status()
    (ROOT/'docs/verification/cloud/monitor-start.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    print('PASS actual cloud read-only monitor enabled for water-field-01; empty source coverage retained; no record or recovery write')


if __name__=='__main__':main()
