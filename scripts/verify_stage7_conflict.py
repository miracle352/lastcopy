"""Actual Central conflict control: create synthetic setup, never overwrite it."""
import argparse
import json
from urllib.parse import quote
from lastcopy.config import ROOT, Settings
from lastcopy.inventory import inventory, read_archive, digest
from lastcopy.models import RunManifest, RunRequest
from lastcopy.store import RunStore, encoded
from lastcopy.odk_recovery import CentralRecovery
from lastcopy.recovery import RecoveryEngine
from scripts.verify_stage4_live import fixture
from scripts.run import bundle_snapshot


def main(tag):
    settings = Settings.load()
    remote = CentralRecovery(settings)
    try:
        assert remote.base == 'http://localhost:8384' and not settings.sample
        remote.begin(); remote.login()
        status, body = remote.request('GET', f"/v1/projects/{remote.target['project_id']}")
        assert status == 200 and json.loads(body)['name'] == 'LastCopy synthetic Stage 4 recovery'
        device, vid, form = fixture(tag, 'conflict')
        inv = inventory(device, settings); files = read_archive(device, settings)
        path = remote.scope()+'/submissions/'+quote(vid, safe='')
        assert remote.request('GET', path)[0] == 404, 'Use a new synthetic tag; never overwrite an existing record'
        assert remote.request('GET', remote.scope()+'.xml') == (200, form)
        original = files[inv.versions[0].xml_path]
        assert b'<value>03</value>' in original
        conflicting = original.replace(b'<value>03</value>', b'<value>99</value>', 1)
        parts = [('xml_submission_file', ('original.xml', conflicting, 'application/xml'))]
        for filename in sorted({m.filename for m in inv.versions[0].media}):
            media = next(m for m in inv.versions[0].media if m.filename == filename)
            parts.append((filename, (filename, files[media.archive_path], 'application/octet-stream')))
        assert remote.request('POST', f"/v1/projects/{remote.target['project_id']}/submission", files=parts,
            headers={'X-OpenRosa-Version': '1.0'})[0] == 201
        run = RunManifest(schema_version=1, run_id='stage7-'+tag+'-conflict', mode='connected',
            source_snapshot_ids=[inv.manifest.snapshot_id, 'pending'], expected_device_ids=[inv.manifest.device_id],
            roster_provenance={'origin':'coordinator_attestation','reference':'stage7-synthetic-control'}, destination=remote.target)
        envelope, payload = remote.capture(run)
        run = run.model_copy(update={'source_snapshot_ids':[inv.manifest.snapshot_id,json.loads(envelope)['snapshot_id']]})
        store = RunStore(ROOT/'private/stage7'/('conflict-'+tag), settings)
        m = store.register('manifest',run.model_dump_json().encode()); d = store.register('device',device)
        s = store.register('server',bundle_snapshot(envelope,payload))
        store.enqueue(RunRequest(manifest_id=m.input_id,device_input_ids=[d.input_id],server_input_id=s.input_id));store.drain()
        report = json.loads(store.artifact(run.run_id,'report.json'));finding=report['findings'][0]
        assert finding['verdict']=='CONTENT_CONFLICT' and not finding['recovery_eligible']
        try:
            RecoveryEngine(store,remote.target,remote).stage(run.run_id,finding['finding_id'])
        except ValueError as e:
            assert 'not eligible' in str(e)
        else:
            raise AssertionError('Conflict produced an automatic plan')
        status, after = remote.request('GET',path+'.xml')
        assert status==200 and after==conflicting and store.input(d.input_id,'device')==device
        receipt={'mode':'connected','real_central':True,'synthetic_setup_only':True,'instance_id':vid,
            'verdict':'CONTENT_CONFLICT','automatic_plan_rejected':True,'recovery_writes':0,
            'server_conflicting_xml_unchanged':True,'source_unchanged':True,
            'source_sha256':digest(device),'server_xml_sha256':digest(after),'report_sha256':digest(store.artifact(run.run_id,'report.json'))}
        (ROOT/'docs/verification/stage7/real-conflict.json').write_bytes(encoded(receipt))
        print(json.dumps(receipt))
    finally:
        remote.client.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--tag',required=True);main(p.parse_args().tag)
