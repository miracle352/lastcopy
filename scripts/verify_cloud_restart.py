"""Real lost-ack/restart control, restricted to the dedicated cloud synthetic scope.

The fixture is explicitly authored from a retained synthetic native export. Its
new ID is chosen before testing, never as a response to a conflict/HTTP 409.
Run prepare, then crash (expected exit 73), restart host, then resume.
"""
import argparse,json,os,uuid
from lastcopy.config import Settings
from lastcopy.store import RunStore,encoded
from lastcopy.inventory import digest,inventory,read_archive
from lastcopy.models import RunManifest,RunRequest
from lastcopy.recovery import archive,RecoveryEngine
from lastcopy.odk_recovery import configured_target,CentralRecovery
from lastcopy.ui import Workspace
from lastcopy.device_transfer import immutable_write
from scripts.recover import capture_registered

RID='cloud-restart-control-20261025'
VID='uuid:'+str(uuid.uuid5(uuid.NAMESPACE_URL,'lastcopy/cloud/restart-control/20261025'))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','crash','resume']);action=parser.parse_args().action
    settings=Settings.load();v=settings.values
    if settings.sample or v.get('ODK_BASE_URL')!='https://central-18-141-113-136.sslip.io' or v.get('ODK_RECOVERY_PROJECT_ID')!='2' or v.get('ODK_RECOVERY_PROJECT_NAME')!='LastCopy cloud recovery (synthetic)':raise ValueError('Dedicated cloud synthetic target required')
    store=RunStore(v['LASTCOPY_DATA_DIR'],settings);ws=Workspace(store)
    original=(store.directory/'acceptance-device.zip').read_bytes()
    assert digest(original)=='25dadf67ef5c4f58e9d13ce85d5ed0e930abff1d2b5e311815694e5aa69382f3'
    native=inventory(original,settings);files=read_archive(original,settings)
    old=native.versions[0];xml=files[old.xml_path]
    assert xml.count(old.version_id.encode())==1
    files[old.xml_path]=xml.replace(old.version_id.encode(),VID.encode())
    manifest=json.loads(files['device-manifest.json'])
    manifest.update(snapshot_id='authored-cloud-restart-control-20261025',device_id='cloud-fault-control',captured_at='2026-10-25T00:00:00Z',synthetic=True,
        scope_complete=True,scope_provenance={'origin':'coordinator_attestation','reference':'Authored single-record fault-control fixture; not a new native collection'})
    files['device-manifest.json']=encoded(manifest);data=archive(files)
    immutable_write(store.directory/'restart-control-source.zip',data)
    try:meta=ws.metadata(RID)
    except KeyError:
        device=store.register('device',data)
        run=RunManifest(schema_version=1,run_id=RID,mode='connected',source_snapshot_ids=[manifest['snapshot_id'],'pending'],
            expected_device_ids=['cloud-fault-control'],roster_provenance={'origin':'coordinator_attestation','reference':'Authored synthetic restart test only'},destination=configured_target(settings))
        m=store.register('manifest',run.model_dump_json().encode());captured=capture_registered(store,m.input_id,[device.input_id])
        run=RunManifest.model_validate_json(store.input(captured['manifest_id'],'manifest'))
        meta=ws.draft(run,[device.input_id],captured['server_input_id'],sample_case=None,parent_run_id=None,captured_run_reference=None,
            provenance='Connected cloud synthetic lost-ack/restart control; authored fixture, not a new native collection; actual Central readback')
        store.enqueue(RunRequest.model_validate(meta['request']));store.drain()
    before=json.loads(store.artifact(RID,'report.json'));assert [f['verdict'] for f in before['findings']]==['MISSING_SUBMISSION']
    engine=RecoveryEngine(store,configured_target(settings));plan=engine.stage(RID,before['findings'][0]['finding_id'])
    assert plan['logical_submission_id']==VID and plan['target']['project_id']==2 and plan['operation']=='create_missing_submission'
    if action=='prepare':
        engine.review(plan['plan_id'],plan['plan_sha256'],plan['target'])
        print(json.dumps({'state':'prepared and reviewed','run_id':RID,'plan_id':plan['plan_id'],'instance_id':VID,'source_sha256':digest(data)}));return
    remote=CentralRecovery(settings);engine.remote=remote
    try:
        if action=='crash':
            native_write=remote.write
            def lost(*args,**kwargs):
                native_write(*args,**kwargs)
                os._exit(73)
            remote.write=lost
            engine.apply(plan['plan_id'])
            raise ValueError('Fault worker did not reach a successful upload; no lost-ack claim')
        def no_write(*args,**kwargs):raise AssertionError('Resume/repeated Apply attempted another upload')
        remote.write=no_write
        result=engine.apply(plan['plan_id']);assert result['state']=='verified'
        assert engine.apply(plan['plan_id'])['state']=='verified'
        after=result['after'];assert [f['verdict'] for f in after['findings']]==['PRESERVED']
        remote.begin();remote.login();status,body=remote.request('GET',remote.scope()+'/submissions');assert status==200
        rows=json.loads(body);assert len([r for r in rows if r['instanceId']==VID])==1
        assert digest(original)==digest((store.directory/'acceptance-device.zip').read_bytes())
        assert digest(data)==digest((store.directory/'restart-control-source.zip').read_bytes())
        receipt={'run_id':RID,'plan_id':plan['plan_id'],'fixture':'Explicitly authored synthetic fault-control derived from retained native synthetic source',
            'before':before,'result':result,'original_native_source_sha256':digest(original),'control_source_sha256':digest(data),
            'same_instance_count':1,'additional_resume_or_repeat_uploads':0,'sources_unchanged':True,'model_calls':0,'server_restart_receipt':'Recorded separately by operator from actual host boot IDs'}
        (store.directory/'restart-control-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        (store.directory/'restart-control-events.jsonl').write_bytes(engine.events(plan['plan_id']))
        print('PASS real cloud lost-ack control resumed through fresh XML/media readback; no second upload; original IDs and source hashes retained')
    finally:remote.client.close()


if __name__=='__main__':main()
