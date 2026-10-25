"""Seal the captured cloud receipts after all checks; refuse to rewrite a seal."""
import json
from lastcopy.config import ROOT
from lastcopy.inventory import digest


def main():
    root=ROOT/'docs/verification/cloud';target=root/'SHA256.json'
    if target.exists():raise ValueError('Cloud evidence is already sealed; use a new receipt directory')
    # Empty output from an interrupted sandbox launch is not an evidence receipt.
    for name in ('auth-red.txt','browser-live.txt'):
        p=root/name
        if p.exists() and p.stat().st_size==0:p.unlink()
    hashes={p.relative_to(root).as_posix():digest(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}
    target.write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
    assert all(digest((root/p).read_bytes())==sha for p,sha in hashes.items())
    print(json.dumps({'sealed_artifacts':len(hashes),'all_hashes_verified':True}))


if __name__=='__main__':main()
