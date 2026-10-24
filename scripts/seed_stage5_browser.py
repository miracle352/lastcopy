"""Prepare bounded synthetic browser test inputs; no conflicts overwritten/deleted."""
import json
from urllib.parse import quote
from lastcopy.config import ROOT,Settings
from lastcopy.ui import Workspace
from lastcopy.store import RunStore,encoded
from lastcopy.models import RunRequest
from lastcopy.inventory import inventory,read_archive,digest
from lastcopy.odk_recovery import CentralRecovery
from scripts.verify_stage4_live import fixture


def prepare(tag='20261024-stage5-01'):
    settings=Settings.load()
    if settings.sample: raise ValueError('Use explicit connected settings for synthetic browser setup')
    store=RunStore(settings.values.get('LASTCOPY_DATA_DIR') or ROOT/'private/stage5/ui',settings)
    ws=Workspace(store)
    queued=ws.sample('stranded')
    store.enqueue(RunRequest.model_validate(queued['request']))  # genuine queued state, no delay/mock reasoning
    out=ROOT/'private/stage5/browser';out.mkdir(parents=True,exist_ok=True)
    (out/'invalid.zip').write_bytes(b'not an archive')
    data,vid,form=fixture(tag,'media')
    inv=inventory(data,settings);files=read_archive(data,settings)
    remote=CentralRecovery(settings);remote.begin();remote.login()
    if remote.base!='http://localhost:8384' or remote.target['project_id']!=int(settings.values['ODK_RECOVERY_PROJECT_ID']):
        raise ValueError('Only existing configured loopback recovery project is supported')
    status,raw=remote.request('GET',f"/v1/projects/{remote.target['project_id']}")
    if status!=200 or json.loads(raw)['name']!='LastCopy synthetic Stage 4 recovery': raise ValueError('Dedicated synthetic project does not match')
    status,raw=remote.request('GET',remote.scope()+'.xml')
    if status!=200 or raw!=form: raise ValueError('Original test XForm differs; no overwrite')
    base=remote.scope()+'/submissions/'+quote(vid,safe='')
    status,_=remote.request('GET',base)
    if status!=404: raise ValueError('Synthetic browser record already exists; select a new tag rather than deleting/replacing it')
    parts=[('xml_submission_file',('original.xml',files[inv.versions[0].xml_path],'application/xml'))]
    for name in ('sample.txt','a.bin'):
        m=next(m for m in inv.versions[0].media if m.filename==name)
        parts.append((name,(name,files[m.archive_path],'application/octet-stream')))
    status,_=remote.request('POST',f"/v1/projects/{remote.target['project_id']}/submission",files=parts,headers={'X-OpenRosa-Version':'1.0'})
    if status!=201: raise ValueError('Partial synthetic fixture setup failed')
    remote.client.close()
    (out/'live-device.zip').write_bytes(data)
    result={'queued_run_id':queued['run_id'],'device_id':inv.manifest.device_id,'live_version_id':vid,
        'source_sha256':digest(data),'target':remote.target,'tag':tag,
        'purpose':'Only setup: incomplete synthetic record for actual browser review/Apply; no recovery claimed'}
    (out/'inputs.json').write_bytes(encoded(result))
    print(json.dumps(result,indent=2))


def queue_only():
    settings=Settings.load();store=RunStore(settings.values.get('LASTCOPY_DATA_DIR') or ROOT/'private/stage5/ui',settings)
    queued=Workspace(store).sample('stranded');store.enqueue(RunRequest.model_validate(queued['request']))
    print(json.dumps({'run_id':queued['run_id']}))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--tag',default='20261024-stage5-01');p.add_argument('--queue-only',action='store_true');a=p.parse_args()
    queue_only() if a.queue_only else prepare(a.tag)
