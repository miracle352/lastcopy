"""Actual synthetic Collect -> sealed inbox -> Central sync -> automatic readback.

Only the reviewed loopback project 4 pilot can receive the one native upload.
This is ordinary synthetic test delivery, not a claim that recovery Apply ran.
"""
import json,time
from pathlib import Path
from urllib.parse import quote
import httpx
from dotenv import dotenv_values
from lastcopy.config import ROOT,Settings
from lastcopy.inventory import inventory,read_archive,digest,parse_xml


def main():
    cfg=dotenv_values(ROOT/'.env');base='http://localhost:8384';api='http://127.0.0.1:8000'
    if cfg.get('ODK_BASE_URL')!=base or cfg.get('ODK_READ_PROJECT_ID')!='4':raise ValueError('Exact local pilot read scope required')
    source=ROOT/'private/water-point/inbox-v2/water-emulator-v2.zip';data=source.read_bytes();sha=digest(data)
    inv=inventory(data,Settings({'SAMPLE_MODE':'false'}));assert inv.manifest.synthetic and not inv.limitations and len(inv.versions)==1
    v=inv.versions[0];assert v.completion_status=='complete' and v.form_version=='2026102502'
    files=read_archive(data,Settings({}));xml=files[v.xml_path];root=parse_xml(xml,Settings({}))
    observations=root.findall('{urn:lastcopy:water-point}observations')
    assert [r.findtext('{urn:lastcopy:water-point}issue_notes') for r in observations]==['SYNTHETIC_TEST_v2_leaking_tap','SYNTHETIC_TEST_v2_path_obstruction']
    assert len(v.media)==1 and v.media[0].sha256
    receipts=[]
    with httpx.Client(timeout=45,trust_env=False,follow_redirects=False) as c:
        def get_status():
            r=c.get(api+'/ui/watch');r.raise_for_status();return r.json()
        def action(name):
            r=c.post(api+'/ui/watch/control',json={'action':name});r.raise_for_status();return r.json()
        def wait_report(old):
            end=time.monotonic()+180
            while time.monotonic()<end:
                s=get_status()
                if s['last_run_id'] and s['last_run_id']!=old:
                    r=c.get(api+'/ui/runs/'+s['last_run_id']);r.raise_for_status();view=r.json()
                    if view['status']['state']=='completed':return view,s
                if s['state']=='error':raise ValueError('Actual automatic check failed; no fallback')
                time.sleep(1)
            raise ValueError('Actual automatic comparison did not complete in 180 seconds')
        # Monitor discovers the finished ZIP from the private inbox by itself.
        previous=get_status()['last_run_id'];action('start');before,bs=wait_report(previous);action('pause')
        assert before['current_report']['findings'][0]['verdict']=='MISSING_SUBMISSION'
        auth=c.post(base+'/v1/sessions',json={'email':cfg['ODK_EMAIL'],'password':cfg['ODK_PASSWORD']})
        if auth.status_code!=200:raise ValueError('Pilot authentication failed')
        headers={'Authorization':'Bearer '+auth.json()['token'],'X-OpenRosa-Version':'1.0'}
        def req(method,path,**kwargs):
            r=c.request(method,base+path,headers=headers,**kwargs)
            receipts.append({'method':method,'scope':path,'status':r.status_code,'response_sha256':digest(r.content)})
            with (ROOT/'private/water-point/delivery-attempts.jsonl').open('a',encoding='utf-8') as log:
                log.write(json.dumps({**receipts[-1],'at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()})+'\n')
            return r
        p=req('GET','/v1/projects/4');assert p.status_code==200 and p.json()['name']=='LastCopy water-point pilot (synthetic)'
        scope='/v1/projects/4/forms/lastcopy_water_point_v1/submissions/'+quote(v.version_id,safe='')
        absent=req('GET',scope+'.xml');assert absent.status_code==404
        blobs={'xml_submission_file':('water-point.xml',xml,'application/xml')}
        blobs.update({m.filename:(m.filename,files[m.archive_path],'image/png') for m in v.media})
        upload=req('POST','/v1/projects/4/submission',files=blobs)
        if upload.status_code not in (200,201):raise ValueError(f'Native upload returned HTTP {upload.status_code}; read back before any retry')
        action('check_now');after,ss=wait_report(bs['last_run_id']);action('pause')
        assert after['current_report']['findings'][0]['verdict']=='PRESERVED'
        assert after['current_report']['coverage']['complete']
        raw=req('GET',scope+'.xml');assert raw.status_code==200 and raw.content==xml
        for m in v.media:
            r=req('GET',scope+'/attachments/'+quote(m.filename,safe=''));assert r.status_code==200 and digest(r.content)==m.sha256
        current=req('GET','/v1/projects/4/forms/lastcopy_water_point_v1/submissions');assert current.status_code==200 and len(current.json())==1
        assert digest(source.read_bytes())==sha
    output={'mode':'connected','source':'Actual finalized synthetic Collect v2026.3.5 record; selected form version 2026102502',
        'before_run':bs['last_run_id'],'after_run':ss['last_run_id'],'before':'MISSING_SUBMISSION','after':'PRESERVED',
        'source_sha256':sha,'source_unchanged':True,'repeat_count':len(observations),'attachment_slots':len(v.media),
        'native_uploads':1,'monitor_recovery_writes':0,'recovery_apply_exercised':False,'model_calls':0,
        'requests':receipts,'scope':'Dedicated synthetic pilot, selected version/device snapshot; not an actual campaign'}
    out=ROOT/'private/water-point/live-acceptance.json';out.write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    (out.parent/'before-view.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
    (out.parent/'after-view.json').write_text(json.dumps(after,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
