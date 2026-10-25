"""Real authenticated upload of bounded deterministic synthetic binary media.

Registration only: creates no run, submission or recovery operation. The source
ZIP is retained privately and reused so baseline/accepted hashes match.
"""
import argparse,json,random
import httpx
from lastcopy.config import ROOT,Settings
from lastcopy.inventory import inventory,read_archive,digest
from lastcopy.recovery import archive
from scripts.build_stage2_fixtures import example


def main():
    p=argparse.ArgumentParser();p.add_argument('--origin',required=True,choices=['https://lastcopy-five.vercel.app','https://app-18-141-113-136.sslip.io']);p.add_argument('--expected',type=int,choices=[201,413],required=True);args=p.parse_args()
    settings=Settings({'SAMPLE_MODE':'true'});path=ROOT/'private/cloud/upload-capacity-control.zip'
    if not path.exists():
        source=example('media')['device'];parsed=inventory(source,settings);files=read_archive(source,settings)
        slot=parsed.versions[0].media[0].archive_path
        files[slot]=random.Random(925071).randbytes(5*1024*1024)
        path.write_bytes(archive(files))
    data=path.read_bytes();assert 5*1024*1024<len(data)<10*1024*1024
    inventory(data,settings)
    secret=json.loads((ROOT/'private/cloud/access.json').read_text(encoding='utf-8'))
    with httpx.Client(timeout=90,trust_env=False,follow_redirects=False,headers={'Origin':args.origin}) as c:
        response=c.post(args.origin+'/api/session/login',json={'password':secret['owner_passphrase']});assert response.status_code==200
        response=c.post(args.origin+'/api/service/ui/devices',content=data,headers={'Content-Type':'application/zip'})
        result={'origin':args.origin,'status':response.status_code,'expected_status':args.expected,'source_sha256':digest(data),'source_bytes':len(data),
            'provenance':'Deterministically seeded synthetic binary media; registration only; no field record or run created'}
        if response.status_code==201:
            registered=response.json();assert registered['input_id']==digest(b'device\0'+data)
            assert registered['sha256']==digest(data)
            result.update(input_id=registered['input_id'],registered_source_hash_matches=True)
        (ROOT/'docs/verification/cloud'/('upload-capacity-'+str(args.expected)+'.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        c.post(args.origin+'/api/session/logout',json={})
        assert response.status_code==args.expected
    print(json.dumps(result))


if __name__=='__main__':main()
