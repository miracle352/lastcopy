"""Fresh scoped status and integrity receipt; no credential values exported."""
import json
from datetime import datetime,timezone
import httpx
from lastcopy.config import ROOT
from lastcopy.inventory import digest


def main():
    values=json.loads((ROOT/'private/cloud/access.json').read_text(encoding='utf-8'))
    base='https://api-18-141-113-136.sslip.io'
    with httpx.Client(timeout=25,trust_env=False,follow_redirects=False,headers={'Authorization':'Bearer '+values['transport_key']}) as c:
        login=c.post(base+'/session/login',json={'password':values['owner_passphrase']});assert login.status_code==200
        settings=c.get(base+'/ui/settings');settings.raise_for_status();settings=settings.json()
        assert settings['mode']=='connected' and settings['target']['project_id']==1
        watch=c.get(base+'/ui/watch');watch.raise_for_status();watch=watch.json()
        assert watch['enabled'] and watch['received_devices']==[] and watch['last_run_id'] is None
        assert watch['device_transfer']['state']=='waiting_for_records' and watch['device_transfer']['exports_completed']==0
        connection=c.get(base+'/ui/connection');connection.raise_for_status();connection=connection.json()
        assert connection['state']=='connected' and connection['project_name']=='Water Point Condition Check'
        c.post(base+'/session/logout').raise_for_status()
    areas={}
    for area in ('stage7','redesign','product','water-point','realtime'):
        folder=ROOT/'docs/verification'/area;seal=json.loads((folder/'SHA256.json').read_text(encoding='utf-8'))
        for path,sha in seal.items():assert digest((folder/path).read_bytes())==sha,f'Prior evidence changed in {area}'
        areas[area]=len(seal)
    before=(ROOT/'docs/verification/cloud/host-before-restart.txt').read_text(encoding='utf-8-sig').splitlines()[0]
    after=(ROOT/'docs/verification/cloud/host-after-restart.txt').read_text(encoding='utf-8-sig').splitlines()[0]
    assert before!=after
    original=next((ROOT/'private/realtime-pilot-inbox').glob('*.zip')).read_bytes()
    assert digest(original)=='25dadf67ef5c4f58e9d13ce85d5ed0e930abff1d2b5e311815694e5aa69382f3'
    out={'checked_at':datetime.now(timezone.utc).isoformat(),'workspace':'https://app-18-141-113-136.sslip.io/app',
        'public_site':'https://lastcopy-five.vercel.app/','settings':settings,'watch':watch,'connection':connection,
        'previous_evidence_seals_verified':areas,'actual_host_restart':True,'boot_id_before':before,'boot_id_after':after,
        'original_native_source_hash':digest(original),'field_submissions_created_by_this_work':0,
        'cloud_sponsor_inference':'Not configured; automatic comparator makes no provider calls'}
    (ROOT/'docs/verification/cloud/final-state.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'passed','scope':'Actual connected empty collection; live desktop link; no invented field coverage',
        'previous_seals_verified':areas,'host_restart_verified':True,'original_native_source_unchanged':True}))


if __name__=='__main__':main()
