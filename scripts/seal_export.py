"""Publish an integrity marker for an already-finished operator-supplied ZIP.

Does not rewrite the ZIP. Use .partial while copying, rename to .zip only after
copying, then run this command. The monitor never receives filesystem paths
from the browser or from imported records.
"""
import argparse
import json
from pathlib import Path
from lastcopy.config import Settings
from lastcopy.inventory import digest,inventory


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('zip',type=Path);a=p.parse_args()
    if a.zip.suffix!='.zip' or a.zip.is_symlink():raise ValueError('Expected an ordinary finished .zip file')
    with a.zip.open('rb') as f:data=f.read(10485761)
    if len(data)>10485760:raise ValueError('ZIP exceeds 10 MiB')
    inventory(data,Settings({'SAMPLE_MODE':'true'}))  # local validation only; no services
    ready={'schema_version':1,'sha256':digest(data),'bytes':len(data)}
    dest=a.zip.with_name(a.zip.name+'.ready.json');raw=(json.dumps(ready,indent=2)+'\n').encode()
    if dest.exists():
        if dest.is_symlink() or json.loads(dest.read_bytes())!=ready:raise ValueError('Existing seal differs; refusing overwrite')
    else:
        with dest.open('xb') as f:f.write(raw)
    print(json.dumps({'sealed':a.zip.name,'sha256':ready['sha256'],'source_unchanged':True}))


if __name__=='__main__':main()
