"""Offline independent artifact verification. Hashes do not authenticate a server."""
import argparse
import json
from pathlib import Path
from lastcopy.config import Settings
from lastcopy.inventory import inventory, read_archive, digest
from lastcopy.models import RunManifest
from lastcopy.reconcile import reconcile
from lastcopy.store import encoded


def verify(folder):
    receipt=json.loads((folder/'receipt.json').read_bytes())
    for name,sha in receipt['files'].items():
        if Path(name).name!=name or digest((folder/name).read_bytes())!=sha:
            raise ValueError('Receipt output seal failed')
    settings=Settings({'SAMPLE_MODE':'false'})
    device=(folder/'device.zip').read_bytes()
    source=inventory(device,settings); files=read_archive(device,settings)
    if digest(device)!=receipt['source_archive_sha256']: raise ValueError('Source seal failed')
    plan=json.loads((folder/'plan.json').read_bytes())
    core={k:v for k,v in plan.items() if k not in ('plan_id','plan_sha256')}
    if digest(encoded(core))!=plan['plan_sha256']: raise ValueError('Plan seal failed')
    bundle=read_archive((folder/'bundle.zip').read_bytes(),settings)
    for name,sha in plan['source_hashes'].items():
        if digest(files[name])!=sha or files[name]!=bundle['files/'+name]: raise ValueError('Bundle source changed')
    result=json.loads((folder/'result.json').read_bytes())
    envelope=(folder/'before-envelope.json').read_bytes(); payload=(folder/'before-payload.zip').read_bytes()
    def check(envelope,payload,expected):
        snapshot=json.loads(envelope)
        run=RunManifest(schema_version=1,run_id=plan['run_id'],mode='connected',
            source_snapshot_ids=[source.manifest.snapshot_id,snapshot['snapshot_id']],
            expected_device_ids=[source.manifest.device_id],destination=plan['target'],
            roster_provenance={'origin':'coordinator_attestation','reference':'stage4-authored-roster'})
        actual=reconcile(run,[device],envelope,payload,settings).model_dump(mode='json')
        for key in ('findings','coverage','preservation_outcome','receipts'):
            if actual[key]!=expected[key]: raise ValueError('Independent comparison differs: '+key)
        return actual
    before=check(envelope,payload,result['before'])
    e,p=result['capture_hashes'][-1]
    after=check((folder/(e+'.evidence')).read_bytes(),(folder/(p+'.evidence')).read_bytes(),result['after'])
    if [f['verdict'] for f in before['findings']] != [receipt['before_verdict']]: raise ValueError('Before expectation failed')
    if [f['verdict'] for f in after['findings']] != ['PRESERVED']: raise ValueError('After expectation failed')
    events=[json.loads(line) for line in (folder/'events.jsonl').read_bytes().splitlines()]
    if len([e for e in events if e['state']=='write_intent'])!=1: raise ValueError('Unexpected write intent count')
    media=source.versions[0].media
    if [m.filename for m in media].count('sample.txt')!=2 or len({m.filename for m in media})!=3:
        raise ValueError('Semantic media controls absent')
    same={m.filename:m.sha256 for m in media}
    if same['a.bin']!=same['b.bin']: raise ValueError('Equal-byte control absent')
    return {'directory':str(folder),'source_hash_verified':True,'bundle_bytes_untouched':True,
        'independent_before_after_reconciler':True,'output_seals_verified':True,'one_write_intent':True,
        'historical_attachment_controls':True,'server_authentication_claim':'Recorded live execution provenance; hashes alone do not authenticate a server'}


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('directories',nargs='+',type=Path); p.add_argument('--receipt',type=Path)
    a=p.parse_args(); result=[verify(d) for d in a.directories]
    if a.receipt: a.receipt.write_bytes(encoded(result))
    print(json.dumps(result,indent=2))
