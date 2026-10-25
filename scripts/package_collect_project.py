"""Package a stopped-app copied Collect project for one explicitly selected form.

Read-only SQLite metadata supplies actual completion state. This is an operator
CLI, never a browser filesystem API. It does not copy or root a field phone.
"""
import argparse
import json
import sqlite3
from pathlib import Path
from datetime import datetime,timezone
from lastcopy.inventory import inventory,parse_xml,digest
from lastcopy.config import Settings
from lastcopy.recovery import archive


def package(source,form_id,device_id,synthetic=False,collector_version='unknown',form_version=None):
    source=Path(source).resolve();settings=Settings({'SAMPLE_MODE':'true'})
    count=total=0
    for p in source.rglob('*'):
        count+=1
        if count>500:raise ValueError('Copied project exceeds 500 entries')
        if p.is_symlink() or p.is_junction():raise ValueError('Linked project files are not accepted')
        if p.is_file():
            total+=p.stat().st_size
            if p.stat().st_size>10485760 or total>33554432:raise ValueError('Copied project exceeds byte budget')
    db=source/'metadata/instances.db'
    db_sha=digest(db.read_bytes())
    with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True) as c:
        c.row_factory=sqlite3.Row
        sql='SELECT * FROM instances WHERE jrFormId=?'+(' AND jrVersion=?' if form_version else '')
        rows=[dict(r) for r in c.execute(sql,(form_id,form_version) if form_version else (form_id,))]
    if not rows or len(rows)>100:raise ValueError('Expected 1–100 actual instance rows for the selected form')
    forms=[]
    for p in (source/'forms').glob('*.xml'):
        data=p.read_bytes();xml=parse_xml(data,settings)
        nodes=xml.findall('.//{http://www.w3.org/2002/xforms}model/{http://www.w3.org/2002/xforms}instance')
        if nodes and len(nodes[0])==1 and nodes[0][0].get('id')==form_id and (not form_version or nodes[0][0].get('version')==form_version):forms.append((p,data))
    if not forms:raise ValueError('Original form definition is absent')
    at=datetime.now(timezone.utc).isoformat();files={};instances=[]
    reference='projects/'+source.name+'/metadata/selected-instances.json'
    for row in rows:
        relative=Path(row['instanceFilePath'])
        if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsupported native instance path; retain the export for manual mapping')
        p=source/'instances'/relative
        if not p.is_file():raise ValueError('Native instance row does not resolve to original XML')
        status={'complete':'complete','submitted':'complete','submissionFailed':'complete','incomplete':'draft'}.get(row['status'],'unknown')
        path='projects/'+source.name+'/instances/'+relative.as_posix()
        instances.append({'xml_path':path,'completion_status':status,'completion_provenance':{'origin':'exporter_metadata','reference':reference}})
        for item in p.parent.iterdir():
            if item.is_file():files['projects/'+source.name+'/'+item.relative_to(source).as_posix()]=item.read_bytes()
    definitions=[]
    for p,data in forms:
        name='projects/'+source.name+'/'+p.relative_to(source).as_posix();files[name]=data;definitions.append({'xml_path':name})
    if digest(db.read_bytes())!=db_sha:raise ValueError('Source database changed during packaging; export again with Collect stopped')
    # Preserve the original database privately. Do not package unrelated form rows.
    selected=[{k:row.get(k) for k in ('_id','jrFormId','jrVersion','instanceFilePath','status','lastStatusChangeDate')} for row in rows]
    files[reference]=(json.dumps({'derivation':'Selected native completion metadata; original database retained in private source export',
        'source_database_sha256':db_sha,'form_id':form_id,'selected_form_version':form_version,'rows':selected},indent=2)+'\n').encode()
    identity=digest(archive(files))
    manifest={'schema_version':1,'snapshot_id':'collect-'+identity[:32],'device_id':device_id,'captured_at':at,
        'collector_version':collector_version,'synthetic':synthetic,
        'scope_complete':True,'scope_provenance':{'origin':'coordinator_attestation','reference':'Explicit selected form '+form_id+' version '+(form_version or 'all copied versions')+'; all matching copied native rows included. Other scopes are not assessed.'},
        'device_provenance':{'origin':'coordinator_attestation','reference':'Operator selected device identity'},
        'instances':instances,'form_definitions':definitions}
    files['device-manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    data=archive(files);inv=inventory(data,settings)
    return data,inv


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--form-id',required=True);p.add_argument('--device-id',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--synthetic',action='store_true');p.add_argument('--collector-version',default='unknown');p.add_argument('--form-version');a=p.parse_args()
    data,inv=package(a.source,a.form_id,a.device_id,a.synthetic,a.collector_version,a.form_version)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('xb') as f:f.write(data)
    print(json.dumps({'archive_sha256':digest(data),'records':len(inv.versions),'limitations':inv.limitations,'synthetic':a.synthetic}))


if __name__=='__main__':main()
