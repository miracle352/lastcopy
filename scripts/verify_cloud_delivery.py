"""Live native-export -> HTTPS delivery -> automatic cloud comparator acceptance.

Temporarily uses the dedicated synthetic project/inbox, then restores the exact
original field configuration. No submissions or recovery writes are performed.
Run only after the scoped-receipt tests pass and the source archive is packaged.
"""
import json,subprocess,time
import httpx
from lastcopy.config import ROOT,Settings
from lastcopy.inventory import digest,read_archive
from lastcopy.store import RunStore
from lastcopy.device_transfer import DeviceTransfer
from lastcopy.cloud_relay import Relay
from scripts.cloud_device_link import cycle
from scripts.setup_cloud_project import SSH

SCP=['C:/Program Files/Git/usr/bin/scp.exe','-S',SSH[0],*SSH[1:-1]]
HOST=SSH[-1];PRIVATE='/srv/lastcopy/private/'
BASE='https://api-18-141-113-136.sslip.io'
COMPOSE='cd /srv/lastcopy/source && sudo docker compose -p lastcopy-cloud -f deploy/aws/compose.api.yaml '


def command(args,timeout=180):
    result=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=timeout)
    if result.returncode:
        (ROOT/'private/cloud/last-delivery-command-error.txt').write_bytes(result.stdout+result.stderr)
        raise ValueError('Cloud verification command failed; diagnostics retained privately')
    return result.stdout


def upload(path,name):command(SCP+[path.relative_to(ROOT).as_posix(),HOST+':'+PRIVATE+name])


def main():
    folder=ROOT/'private/cloud'
    secret=json.loads((folder/'access.json').read_text(encoding='utf-8'))
    upload(folder/'source.tar.gz','source.tar.gz')
    command(SSH+['tar -xzf /srv/lastcopy/private/source.tar.gz -C /srv/lastcopy/source && '+COMPOSE+'up -d --build > /srv/lastcopy/automatic-image-update.log 2>&1'],timeout=240)
    # Switch only non-secret scope lines on the server; credentials stay there.
    control='python3 /srv/lastcopy/source/scripts/cloud_scope_control.py '
    original_sha=command(SSH+['sha256sum /srv/lastcopy/private/api.env']).decode().split()[0]
    changed=False
    try:
        command(SSH+['sudo install -d -o 10001 -g 10001 -m 0700 /srv/lastcopy/private/application/automatic-acceptance-inbox'])
        changed=True;switched=command(SSH+[control+'test']).decode().strip();assert switched==original_sha
        command(SSH+[COMPOSE+'up -d --no-build --pull never > /srv/lastcopy/automatic-scope-start.log 2>&1'])
        with httpx.Client(timeout=25,trust_env=False,follow_redirects=False,headers={'Authorization':'Bearer '+secret['transport_key']}) as client:
            def ready(expected):
                end=time.monotonic()+90
                while time.monotonic()<end:
                    try:
                        response=client.post(BASE+'/session/login',json={'password':secret['owner_passphrase']})
                        if response.status_code==200:
                            response=client.get(BASE+'/ui/settings')
                            if response.status_code==200 and response.json()['target']['project_id']==expected:return
                    except httpx.HTTPError:pass
                    time.sleep(2)
                raise ValueError('Configured scope did not become ready')
            ready(2)
            response=client.post(BASE+'/ui/watch/control',json={'action':'start'});response.raise_for_status()
            inbox=folder/'automatic-native-inbox';inbox.mkdir(exist_ok=True)
            config=Settings({'SAMPLE_MODE':'false','LASTCOPY_DEVICE_TRANSFER_ENABLED':'true',
                'LASTCOPY_ADB_PATH':str(ROOT/'private/android/sdk/platform-tools/adb.exe'),'LASTCOPY_DEVICE_SERIAL':'emulator-5558',
                'LASTCOPY_COLLECT_PROJECT_ID':'c7ee4de9-247c-42ac-8d78-d5bb9e7d8d4d','LASTCOPY_TRANSFER_DEVICE_ID':'water-emulator-01',
                'LASTCOPY_TRANSFER_FORM_ID':'lastcopy_water_point_v1','LASTCOPY_TRANSFER_FORM_VERSION':'2026102502',
                'LASTCOPY_TRANSFER_SYNTHETIC':'true','LASTCOPY_TRANSFER_COLLECTOR_VERSION':'v2026.3.5',
                'LASTCOPY_WATCH_INBOX':str(inbox),'LASTCOPY_TRANSFER_MAX_EXPORTS':'1',
                'LASTCOPY_CLOUD_ORIGIN':BASE,'LASTCOPY_TRANSFER_KEY':secret['transfer_key']})
            store=RunStore(folder/'automatic-native-ledger',config);transfer=DeviceTransfer(store);relay=Relay(store)
            try:
                sent=cycle(transfer,relay);assert sent['state']=='watching'
                assert relay.flush()==0
            finally:relay.close()
            archive=next(inbox.glob('*.zip'));data=archive.read_bytes()
            old=next((ROOT/'private/realtime-pilot-inbox').glob('*.zip')).read_bytes()
            a=read_archive(data,config);b=read_archive(old,config)
            assert {p:v for p,v in a.items() if p!='device-manifest.json'}=={p:v for p,v in b.items() if p!='device-manifest.json'}
            end=time.monotonic()+90;view=None
            while time.monotonic()<end:
                watch=client.get(BASE+'/ui/watch').json()
                if watch.get('last_run_id'):
                    response=client.get(BASE+'/ui/runs/'+watch['last_run_id']);response.raise_for_status();candidate=response.json()
                    if candidate['status']['state']=='completed':view=candidate;break
                time.sleep(2)
            assert view and view['automatic_check'] and view['manifest']['mode']=='connected'
            report=view['current_report'];assert [f['verdict'] for f in report['findings']]==['PRESERVED']
            assert digest(data) in report['input_hashes'].values() and report['provider_calls']==0 and not report['recovery_executed']
            assert watch['device_transfer']['exports_completed']==1
            result={'mode':'Connected · actual native synthetic cohort and actual HTTPS/cloud readback','run_id':view['manifest']['run_id'],
                'device_export_sha256':digest(data),'prior_native_export_sha256':digest(old),'original_xml_forms_media_unchanged':True,
                'delivery_deduplicated':True,'report':report,'watch':watch,'submissions_or_recovery_writes':0,'model_calls':0,
                'scope':'Separate synthetic project/inbox; the real collection remains empty'}
            (ROOT/'docs/verification/cloud/automatic-native-delivery.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
            client.post(BASE+'/ui/watch/control',json={'action':'pause'}).raise_for_status()
            client.post(BASE+'/session/logout').raise_for_status()
    finally:
        if changed:
            assert command(SSH+[control+'restore']).decode().strip()==original_sha
            command(SSH+[COMPOSE+'up -d --no-build --pull never > /srv/lastcopy/field-scope-restored.log 2>&1'])
            restored=command(SSH+['sha256sum /srv/lastcopy/private/api.env']).decode().split()[0]
            assert restored==original_sha,'Field configuration was not restored exactly'
    print('PASS actual native export, authenticated HTTPS delivery, automatic fresh cloud comparison and deduplication; original field configuration restored exactly')


if __name__=='__main__':main()
