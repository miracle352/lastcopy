"""Download the official checksum-pinned local Android screen-control utility.

Private development runtime only. No global installer, field data or website asset.
"""
import hashlib,json,zipfile,urllib.request
from pathlib import Path,PurePosixPath
from lastcopy.config import ROOT

URL='https://github.com/Genymobile/scrcpy/releases/download/v5.0.1/scrcpy-win64-v5.0.1.zip'
SHA='b12a2c4ee8be317422451fc7dcf8ee20a71b5ea7ef9ad73ddd825a25316227a5'


def main():
    folder=ROOT/'private/android/scrcpy';folder.mkdir(exist_ok=True)
    path=folder/'scrcpy-win64-v5.0.1.zip'
    if not path.exists():
        with urllib.request.urlopen(URL,timeout=60) as r:data=r.read(20*1024*1024+1)
        assert len(data)<=20*1024*1024 and hashlib.sha256(data).hexdigest()==SHA
        path.write_bytes(data)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==SHA
    destination=folder/'scrcpy-win64-v5.0.1'
    if not destination.exists():
        with zipfile.ZipFile(path) as z:
            for member in z.infolist():
                p=PurePosixPath(member.filename)
                assert not p.is_absolute() and '..' not in p.parts and '\\' not in member.filename and ':' not in member.filename
                assert p.parts[0]=='scrcpy-win64-v5.0.1' and not (member.external_attr>>16)&0o170000==0o120000
            z.extractall(folder)
    assert (destination/'scrcpy.exe').is_file()
    result={'runtime':'scrcpy','version':'5.0.1','source':URL,'sha256':SHA,'license':'Apache-2.0',
        'purpose':'Interactive view/control of the explicitly paired AOSP emulator; no physical-phone support claim','global_install':False}
    (ROOT/'docs/verification/cloud/collect-window-runtime.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Verified official scrcpy 5.0.1 archive; extracted only inside ignored private/android/scrcpy. No global changes.')


if __name__=='__main__':main()
