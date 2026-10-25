"""Export only fixed synthetic acceptance receipts, never credentials/field data."""
import json
from lastcopy.config import Settings
from lastcopy.store import RunStore
from lastcopy.recovery import RecoveryEngine
from lastcopy.odk_recovery import configured_target,CentralRecovery
from lastcopy.inventory import digest
from lastcopy.ui import Workspace


def main():
    settings=Settings.load();v=settings.values
    assert v.get('ODK_BASE_URL')=='https://central-18-141-113-136.sslip.io' and v.get('ODK_RECOVERY_PROJECT_ID')=='2'
    store=RunStore(v['LASTCOPY_DATA_DIR'],settings);ws=Workspace(store)
    run='cloud-recovery-25dadf67ef5c4f58e9d13ce8';view=ws.view(run)
    assert view['synthetic_source'] and view['manifest']['destination']['project_id']==2
    plan=view['plans'][0]['plan'];engine=RecoveryEngine(store,configured_target(settings));engine.remote=CentralRecovery(settings)
    try:
        result=engine.result(plan['plan_id']);assert result['state']=='verified'
        fresh=engine.recheck(plan['plan_id']);assert fresh['state']=='preserved'
        assert [f['verdict'] for f in fresh['report']['findings']]==['PRESERVED']
        original=(store.directory/'acceptance-device.zip').read_bytes()
        assert digest(original)=='25dadf67ef5c4f58e9d13ce85d5ed0e930abff1d2b5e311815694e5aa69382f3'
        receipt={'run_id':run,'mode':'Connected · actual native synthetic source and real cloud Central','before':view['report'],
            'plan':plan,'result':result,'independent_fresh_readback':fresh,'original_source_sha256':digest(original),
            'sources_unchanged':True,'model_calls':0,'scope':'Dedicated synthetic project 2 only; no real field-project write'}
        (store.directory/'native-cloud-recovery.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        (store.directory/'native-cloud-recovery-events.jsonl').write_bytes(engine.events(plan['plan_id']))
    finally:engine.remote.client.close()
    print('PASS exported native synthetic before/plan/attempt/after plus independent fresh XML/media readback; original archive hash retained')


if __name__=='__main__':main()
