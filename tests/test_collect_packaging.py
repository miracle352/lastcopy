"""Native completion metadata is preserved without disclosing other form rows."""
import json
import sqlite3
import pytest
from lastcopy.config import Settings
from lastcopy.inventory import read_archive
from scripts.build_stage2_fixtures import example
from scripts.package_collect_project import package


def copied_project(tmp_path,status='incomplete'):
    files=read_archive(example('media')['device'],Settings({}))
    manifest=json.loads(files['device-manifest.json']);source=tmp_path/'copied-project'
    instance=manifest['instances'][0]['xml_path'];form=manifest['form_definitions'][0]['xml_path']
    prefix='projects/field-a/'
    # Use the exact fixture's native paths, independent of their folder label.
    prefix=instance.split('instances/')[0]
    for name,data in files.items():
        if name.startswith(prefix):
            p=source/name[len(prefix):];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    (source/'metadata').mkdir(exist_ok=True)
    with sqlite3.connect(source/'metadata/instances.db') as c:
        c.execute('CREATE TABLE instances(_id INTEGER,jrFormId TEXT,jrVersion TEXT,instanceFilePath TEXT,status TEXT,lastStatusChangeDate INTEGER)')
        v=example('media')['run']['destination']['form_id']
        root=__import__('defusedxml.ElementTree',fromlist=['fromstring']).fromstring(files[instance])
        c.execute('INSERT INTO instances VALUES(1,?,?,?,?,123)',(v,root.get('version'),instance.split('instances/')[1],status))
        c.execute('INSERT INTO instances VALUES(2,?,?,?,?,123)',('unrelated-private-form','1','unrelated','complete'))
    return source,v


def test_draft_does_not_become_complete_and_unrelated_rows_stay_private(tmp_path):
    source,form=copied_project(tmp_path)
    data,inv=package(source,form,'operator-device',True)
    assert inv.versions[0].completion_status=='draft'
    assert 'Completion not established; excluded from automatic submission' in inv.limitations
    files=read_archive(data,Settings({}));assert not any(p.endswith('.db') for p in files)
    assert all(b'unrelated-private-form' not in b for b in files.values())
    assert inv.manifest.collector_version=='unknown'


def test_native_traversal_and_wrong_version_are_rejected(tmp_path):
    source,form=copied_project(tmp_path,'complete')
    with pytest.raises(ValueError,match='actual instance rows'):package(source,form,'device',form_version='missing-version')
    with sqlite3.connect(source/'metadata/instances.db') as c:c.execute("UPDATE instances SET instanceFilePath='../outside.xml' WHERE _id=1")
    with pytest.raises(ValueError,match='Unsupported native instance path'):package(source,form,'device')
