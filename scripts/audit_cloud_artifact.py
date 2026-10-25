"""Check public working files/source archive against known private cloud secrets."""
import json,re,subprocess,tarfile,argparse
from lastcopy.config import ROOT


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='docs/verification/cloud/credential-scan.json');args=parser.parse_args()
    private=json.loads((ROOT/'private/cloud/access.json').read_text(encoding='utf-8'))
    values=[v.encode() for k,v in private.items() if re.search(r'password|passphrase|key',k) and isinstance(v,str) and len(v)>=12]
    settings=json.loads((ROOT/'private/cloud/collect-settings.json').read_text(encoding='utf-8'))
    url=settings['general']['server_url'];values.extend([url.encode(),url.split('/key/')[1].split('/')[0].encode()])
    findings=[];count=0
    names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode('utf-8').split('\0')
    for name in names:
        if not name or not (ROOT/name).is_file():continue
        count+=1;raw=(ROOT/name).read_bytes()
        if name.startswith('private/') or any(v in raw for v in values):findings.append({'path':name,'reason':'private source or known credential bytes'})
    artifacts=0
    with tarfile.open(ROOT/'private/cloud/source.tar.gz','r:gz') as archive:
        for member in archive:
            if not member.isfile():continue
            artifacts+=1;raw=archive.extractfile(member).read()
            if member.name.startswith(('private/','.env','.git/')) or any(v in raw for v in values):findings.append({'artifact_path':member.name,'reason':'private source or known credential bytes'})
    result={'public_working_files_checked':count,'source_archive_files_checked':artifacts,'known_private_values_checked':len(values),'findings':findings,
        'scope':'Exact configured cloud credentials and scoped Collect token; focused scan, not a guarantee against every possible secret format'}
    (ROOT/args.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result));return 1 if findings else 0


if __name__=='__main__':raise SystemExit(main())
