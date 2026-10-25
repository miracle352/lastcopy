"""Move only the empty, dedicated AOSP collection's server setting to HTTPS.

Native record files/DB bytes are hash-checked around the settings update. Refuses
any collected record rather than silently moving an active collection's target.
"""
import json,subprocess,io,tarfile,sqlite3,tempfile
from xml.etree import ElementTree as ET
from defusedxml import ElementTree as SafeET
import httpx
from lastcopy.config import ROOT
from lastcopy.inventory import digest

PROJECT='f385a2ba-b12a-4d58-a4be-02e2bfb3df57'


def main():
    adb=ROOT/'private/android/sdk/platform-tools/adb.exe'
    def command(*args):
        r=subprocess.run([str(adb),'-s','emulator-5558',*args],capture_output=True,timeout=45)
        if r.returncode:raise ValueError('Dedicated emulator setup failed; no raw diagnostics exported')
        return r.stdout
    assert command('shell','getprop','ro.kernel.qemu').strip()==b'1'
    assert command('shell','id','-u').strip()==b'0'
    settings=json.loads((ROOT/'private/cloud/collect-settings.json').read_text(encoding='utf-8'))
    url=settings['general']['server_url']
    assert url.startswith('https://central-18-141-113-136.sslip.io/v1/key/')
    with httpx.Client(timeout=20,trust_env=False,follow_redirects=False) as client:
        r=client.get(url+'/formList',headers={'X-OpenRosa-Version':'1.0'});assert r.status_code==200
        listing=SafeET.fromstring(r.content)
        download=next(n.text for n in listing.iter() if n.tag.endswith('downloadUrl'))
        assert download.startswith('https://central-18-141-113-136.sslip.io/')
        r=client.get(download,headers={'X-OpenRosa-Version':'1.0'});assert r.status_code==200
        assert r.content==(ROOT/'forms/water-point-condition/water-point-condition-v2.xml').read_bytes()
    command('shell','am','force-stop','org.odk.collect.android')
    root='/sdcard/Android/data/org.odk.collect.android/files/projects/'+PROJECT
    def sources():
        raw=command('exec-out','tar','-C',root,'-cf','-','forms','instances','metadata')
        from lastcopy.device_transfer import unpack
        files=unpack(raw)
        with tempfile.TemporaryDirectory() as temp:
            p=__import__('pathlib').Path(temp)/'instances.db';p.write_bytes(files['metadata/instances.db'])
            con=sqlite3.connect('file:'+p.as_posix()+'?mode=ro',uri=True)
            try:assert con.execute('SELECT COUNT(*) FROM instances').fetchone()[0]==0,'Collection is not empty; target unchanged'
            finally:con.close()
        return {p:digest(data) for p,data in files.items()}
    before=sources()
    prefs='/data/data/org.odk.collect.android/shared_prefs/general_prefs'+PROJECT+'.xml'
    original=command('exec-out','cat',prefs)
    backup=ROOT/'private/cloud/native-settings-before.xml'
    if not backup.exists():backup.write_bytes(original)
    tree=SafeET.fromstring(original)
    for name,value in (('server_url',url),('autosend','wifi_only')):
        entry=next(n for n in tree if n.get('name')==name);entry.text=value
    entry=next(n for n in tree if n.get('name')=='delete_send');entry.set('value','false')
    changed=ET.tostring(tree,encoding='utf-8',xml_declaration=True)
    path=ROOT/'private/cloud/native-settings-current.xml';path.write_bytes(changed)
    identity=command('shell','stat','-c','%u:%g',prefs).decode().strip()
    assert all(p.isdigit() for p in identity.split(':'))
    command('push',str(path),prefs);command('shell','chown',identity,prefs);command('shell','chmod','600',prefs);command('shell','restorecon',prefs)
    assert command('exec-out','cat',prefs)==changed
    assert sources()==before
    command('shell','monkey','-p','org.odk.collect.android','-c','android.intent.category.LAUNCHER','1')
    cloud=json.loads((ROOT/'private/cloud/access.json').read_text(encoding='utf-8'))
    inbox=ROOT/'private/cloud/native-inbox';inbox.mkdir(exist_ok=True)
    values={'SAMPLE_MODE':'false','LASTCOPY_DEVICE_TRANSFER_ENABLED':'true','LASTCOPY_ADB_PATH':str(adb),
        'LASTCOPY_DEVICE_SERIAL':'emulator-5558','LASTCOPY_COLLECT_PROJECT_ID':PROJECT,'LASTCOPY_TRANSFER_DEVICE_ID':'water-field-01',
        'LASTCOPY_TRANSFER_FORM_ID':'lastcopy_water_point_v1','LASTCOPY_TRANSFER_SYNTHETIC':'false','LASTCOPY_TRANSFER_COLLECTOR_VERSION':'v2026.3.5',
        'LASTCOPY_WATCH_INBOX':str(inbox),'LASTCOPY_TRANSFER_INTERVAL_SECONDS':'30','LASTCOPY_TRANSFER_MAX_EXPORTS':'40',
        'LASTCOPY_CLOUD_ORIGIN':'https://api-18-141-113-136.sslip.io','LASTCOPY_TRANSFER_KEY':cloud['transfer_key']}
    (ROOT/'private/cloud/device-link.env').write_text(''.join(k+'='+v+'\n' for k,v in values.items()),encoding='utf-8',newline='\n')
    receipt={'scope':'Empty dedicated AOSP emulator collection only','central_url':'https://central-18-141-113-136.sslip.io',
        'native_project_id':PROJECT,'native_records':0,'source_file_hashes':before,'sources_unchanged':True,
        'settings_changed':['server_url','autosend','delete_send'],'autosend':'wifi_only','delete_after_send':False,
        'form_download_matches_original':True,'submissions_created':0,'physical_phone_claim':False}
    (ROOT/'docs/verification/cloud/native-setup.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('PASS empty emulator paired with cloud HTTPS; form bytes verified; native source/DB hashes unchanged; scoped link config saved privately')


if __name__=='__main__':
    try:main()
    except Exception:
        import traceback
        (ROOT/'private/cloud/native-setup-error.txt').write_text(traceback.format_exc(),encoding='utf-8')
        print('Cloud pairing did not complete. Diagnostics retained privately; no source preservation or connection success claimed.')
        raise SystemExit(1)
