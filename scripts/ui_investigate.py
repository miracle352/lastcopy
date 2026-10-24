"""Detached, bounded UI investigation supervisor; survives an API restart."""
import argparse
from lastcopy.config import Settings
from lastcopy.store import RunStore
from lastcopy.ui import Workspace
from lastcopy.ui_investigation import UIInvestigation
from lastcopy.models import RunManifest
from lastcopy.inventory import read_archive
from lastcopy.investigation import EvidencePack
from scripts.investigate import execute,supervise


def run(rid,attempt):
    settings=Settings.load();store=RunStore(settings.values['LASTCOPY_DATA_DIR'],settings)
    job=UIInvestigation(store)
    directory=job.directory(rid,attempt)
    lease=RunStore(directory.parent/('worker-lock-'+attempt),settings)
    with lease.lease() as held:
        if not held: raise ValueError('Investigation supervisor already active')
        return run_owned(rid,attempt,settings,store,job)


def run_owned(rid,attempt,settings,store,job):
    with store.connect() as c:
        row=c.execute('SELECT attempt_id,state FROM ui_investigations WHERE run_id=?',(rid,)).fetchone()
        if row!=(attempt,'queued'): raise ValueError('Job identity/state changed')
        c.execute("UPDATE ui_investigations SET state='running' WHERE run_id=?",(rid,))
    state,error='failed','Connected worker failed; no sample evidence substituted'
    try:
        meta=Workspace(store).metadata(rid);req=meta['request']
        manifest=RunManifest.model_validate_json(store.input(req['manifest_id'],'manifest'))
        if settings.sample or manifest.mode!='connected' or meta.get('provenance')!='Authenticated configured Central capture': raise ValueError('Unsupported connected input provenance')
        parts=read_archive(store.input(req['server_input_id'],'server'),settings)
        pack=EvidencePack.build(manifest.model_dump(mode='json'),[store.input(i,'device') for i in req['device_input_ids']],
            parts['server-snapshot.json'],parts['server-payload.zip'],settings,native_test_capture=True)
        directory=job.directory(rid,attempt)
        if (directory/'cancel').exists():
            state,error='cancelled','Cancelled before any provider call'
        else:
            result=supervise(execute,(pack,directory,settings,True,False),directory,manifest)
            state=result['status'];error=result.get('error')
        # Re-read immutable inputs after connected analysis; no source edits.
        for i,kind in [(req['manifest_id'],'manifest'),(req['server_input_id'],'server'),*((i,'device') for i in req['device_input_ids'])]: store.input(i,kind)
    except Exception:
        state,error='failed','Connected investigation could not complete; no sample evidence substituted'
    with store.connect() as c: c.execute('UPDATE ui_investigations SET state=?,error=? WHERE run_id=? AND attempt_id=?',(state,error,rid,attempt))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--attempt-id',required=True);a=p.parse_args();run(a.run_id,a.attempt_id)
