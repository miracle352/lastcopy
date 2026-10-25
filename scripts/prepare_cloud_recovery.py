"""Prepare (do not apply) a genuine native synthetic recovery on cloud project 2.

Run inside the cloud API container after the original ZIP is copied privately.
No arbitrary filesystem input or destination; existing identifiers are untouched.
"""
import json
from lastcopy.config import ROOT,Settings
from lastcopy.store import RunStore
from lastcopy.inventory import inventory,digest
from lastcopy.models import RunManifest,RunRequest
from lastcopy.odk_recovery import configured_target
from lastcopy.ui import Workspace
from scripts.recover import capture_registered


def main():
    settings=Settings.load();v=settings.values
    if settings.sample or v.get('ODK_BASE_URL')!='https://central-18-141-113-136.sslip.io' or v.get('ODK_RECOVERY_PROJECT_ID')!='2' or v.get('ODK_RECOVERY_PROJECT_NAME')!='LastCopy cloud recovery (synthetic)':
        raise ValueError('Only the configured dedicated cloud synthetic project is allowed')
    store=RunStore(v['LASTCOPY_DATA_DIR'],settings)
    data=(store.directory/'acceptance-device.zip').read_bytes()
    # Actual native producer ZIP sealed by verification/realtime/actual-device.json.
    assert digest(data)=='25dadf67ef5c4f58e9d13ce85d5ed0e930abff1d2b5e311815694e5aa69382f3'
    source=inventory(data,settings)
    assert source.manifest.synthetic and len(source.versions)==1 and source.versions[0].completion_status=='complete'
    assert source.versions[0].form_id=='lastcopy_water_point_v1'
    rid='cloud-recovery-'+digest(data)[:24]
    ws=Workspace(store)
    try:
        existing=ws.view(rid)
        print(json.dumps({'run_id':rid,'state':existing['status']['state'],'existing':True}));return
    except KeyError:pass
    item=store.register('device',data)
    run=RunManifest(schema_version=1,run_id=rid,mode='connected',source_snapshot_ids=[source.manifest.snapshot_id,'pending'],
        expected_device_ids=[source.manifest.device_id],roster_provenance={'origin':'coordinator_attestation','reference':'Actual native synthetic cohort retained from dedicated emulator'},destination=configured_target(settings))
    manifest=store.register('manifest',run.model_dump_json().encode())
    captured=capture_registered(store,manifest.input_id,[item.input_id])
    run=RunManifest.model_validate_json(store.input(captured['manifest_id'],'manifest'))
    draft=ws.draft(run,[item.input_id],captured['server_input_id'],sample_case=None,parent_run_id=None,captured_run_reference=None,
        provenance='Actual native emulator synthetic source; fresh authenticated AWS Central test-project capture; no model calls')
    store.enqueue(RunRequest.model_validate(draft['request']));store.drain()
    report=json.loads(store.artifact(rid,'report.json'))
    assert [f['verdict'] for f in report['findings']]==['MISSING_SUBMISSION']
    assert report['provider_calls']==0
    plan=ws.engine(rid).stage(rid,report['findings'][0]['finding_id'])
    assert digest(data)==digest((store.directory/'acceptance-device.zip').read_bytes())
    output={'run_id':rid,'source_sha256':digest(data),'before_verdict':'MISSING_SUBMISSION','plan_id':plan['plan_id'],
        'mode':'Connected · actual native synthetic source and fresh cloud Central readback','target':plan['target'],'applied':False,'model_calls':0}
    (store.directory/'acceptance-prepared.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(output))


if __name__=='__main__':main()
