"""Mutation controls in a temporary source copy; never alter working evidence."""
import json,subprocess,sys,tempfile,shutil
from pathlib import Path
from lastcopy.config import ROOT

def main():
    out=ROOT/'docs/verification/public-beta';results=[]
    cases=[('owner-store-leak','lastcopy/api.py',"return getattr(request.state,'evidence_store',root)",'return root',
            'tests/test_accounts.py::test_accounts_are_verified_isolated_and_survive_restart_without_owner_secrets'),
           ('unbounded-account-jobs','lastcopy/accounts.py','if active>=4:','if False:',
            'tests/test_accounts.py::test_beta_queue_is_bounded_across_accounts_and_capacity_returns_after_completion'),
           ('model-adds-facts','lastcopy/nvidia_cloud.py',"set(action)!={'action'} or ",'',
            'tests/test_nvidia_cloud.py::test_cloud_cannot_add_facts_or_execute_unlisted_actions'),
           ('lost-nvidia-gateway-route','lastcopy/nvidia_cloud.py','DOCUMENTED_ROUTES.get(catalog_model,catalog_model)','catalog_model',
            'tests/test_nvidia_cloud.py::test_documented_bolt_route_is_distinct_from_inventory_and_serving_identity')]
    with tempfile.TemporaryDirectory(prefix='lastcopy-beta-mutations-') as temp:
        copy=Path(temp)
        for name in ('lastcopy','scripts','tests','fixtures','contracts'):
            shutil.copytree(ROOT/name,copy/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for name,file,before,after,test in cases:
            path=copy/file;original=path.read_text(encoding='utf-8');assert before in original
            path.write_text(original.replace(before,after,1),encoding='utf-8')
            try:
                r=subprocess.run([sys.executable,'-m','pytest',test,'-q'],cwd=copy,capture_output=True,text=True,timeout=90)
                (out/(name+'-red.txt')).write_text(r.stdout+r.stderr,encoding='utf-8')
                assert r.returncode==1 and 'FAILED' in r.stdout and 'ERROR collecting' not in r.stdout,name+' was not detected'
                results.append({'mutation':name,'detected':True,'pytest_exit_code':r.returncode})
            finally:path.write_text(original,encoding='utf-8')
    (out/'mutation-controls.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results))

if __name__=='__main__':main()
