"""Authored offline readback scenario, never a recovery application or live trace.

Expected outcomes are specified here independently of the production comparator.
All records/media are synthetic. Raw source files are copied byte-for-byte.
"""
import json
import hashlib
import xml.etree.ElementTree as ET
from scripts.build_stage2_fixtures import example,pack,AT


def recovery_readback(case):
    data=example(case)
    import io,zipfile
    def unpack(raw):
        with zipfile.ZipFile(io.BytesIO(raw)) as z: return {n:z.read(n) for n in z.namelist()}
    source=unpack(data['device']); old=unpack(data['server'])
    dm=json.loads(source['device-manifest.json'])
    sid='authored-readback-'+case
    files={}; versions=[]; receipts=[]; lists={}
    sha=lambda b:hashlib.sha256(b).hexdigest()
    def receipt(path,version=None,attachment=None):
        rid=f'{sid}-evidence-{len(receipts)+1}'
        receipts.append({'evidence_id':rid,'source_snapshot_id':sid,'source_file':path,'archive_sha256':None,
            'captured_at':AT,'query_receipt_id':None,'request_method':'LOCAL','outcome':'synthetic','http_status':None,
            'request_scope':'Authored offline readback example; no HTTP request or upload',
            'response_sha256':sha(files[path]),'comparison':None,'form_id':'inspection','version_id':version,
            'xml_path':None,'repeat_indices':[],'attachment_filename':attachment})
        return rid
    inputs=[]
    for entry in dm['instances']:
        xml=source[entry['xml_path']]; folder=entry['xml_path'].rsplit('/',1)[0]
        inputs.append((xml,{n:source[folder+'/'+n] for n in ('same.bin','a.bin','b.bin')}))
    for v in data['snapshot']['versions']:
        if v['version_id']=='uuid:41-other':
            inputs.append((old[v['xml_path']],{m['filename']:old[m['archive_path']] for m in v['media']}))
    for i,(xml,media) in enumerate(inputs):
        root=ET.fromstring(xml); vid=root.findtext('./{*}meta/{*}instanceID')
        xp=f'raw/{i}/original.xml'; files[xp]=xml; receipt(xp,vid)
        lp=f'raw/{i}/attachments.json'; files[lp]=json.dumps({'version_id':vid,'filenames':sorted(media)}).encode()
        lists[vid]=receipt(lp,vid)
        refs=[]
        for name,blob in media.items():
            mp=f'raw/{i}/media/{name}'; files[mp]=blob
            refs.append({'version_id':vid,'filename':name,'xml_path':'/authored-media-slot','occurrence_indices':[],
                'archive_path':mp,'sha256':sha(blob),'readback_receipt_id':receipt(mp,vid,name)})
        versions.append({'snapshot_id':sid,'form_id':'inspection','form_version':'1','logical_submission_id':vid,
            'version_id':vid,'deprecated_id':None,'xml_path':xp,'xml_sha256':sha(xml),'completion_status':'complete',
            'current':True,'media':refs,'limitations':[]})
    fields=['form_id','form_version','logical_submission_id','version_id','deprecated_id','current']
    files['scope.json']=json.dumps({'connection_id':'synthetic-offline-only','project_id':7,'form_ids':['inspection'],
        'history_complete':True,'versions':[{k:v[k] for k in fields} for v in versions]}).encode()
    listing=receipt('scope.json'); payload=pack(files)
    data['snapshot']={'schema_version':1,'snapshot_id':sid,'kind':'central_raw','archive_sha256':sha(payload),
        'captured_at':AT,'synthetic':True,'scope_complete':True,'connection_id':'synthetic-offline-only','project_id':7,
        'form_ids':['inspection'],'limitations':[],'receipt_ids':[r['evidence_id'] for r in receipts],'receipts':receipts,
        'versions':versions,'listing_receipt_id':listing,'history_complete':True,'attachment_listing_receipt_ids':lists,'tabular_views':[]}
    data['server']=payload; data['run']['source_snapshot_ids']=[dm['snapshot_id'],sid]
    data['expected']={'verdicts':['PRESERVED']*(3 if case=='stranded' else 1),'operation_executed':False,'network_calls':0}
    return data
