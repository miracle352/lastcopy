"""Local-only advisory matching. Never export image/package metadata.

Downloads Debian's complete public JSON once, then uses dpkg's own version
comparison inside a network-disabled local container. Not Docker Scout.
"""
import hashlib
import argparse
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

WORKER = r'''
import collections,json,subprocess
db=json.load(open('/audit.json'))
raw=subprocess.check_output(['dpkg-query','-W','-f','${source:Package}\t${source:Version}\n'],text=True)
packages=sorted(set(tuple(line.split('\t')) for line in raw.splitlines() if '\t' in line))
findings=[]
for package,version in packages:
 for cve,entry in db.get(package,{}).items():
  row=entry.get('releases',{}).get('bookworm')
  if not row:continue
  status=row.get('status');fixed=row.get('fixed_version')
  if status=='resolved' and (fixed=='0' or fixed and subprocess.run(['dpkg','--compare-versions',version,'ge',fixed]).returncode==0):continue
  findings.append({'package':package,'installed':version,'cve':cve,'status':status,'urgency':row.get('urgency'),'fixed_version':fixed})
print(json.dumps({'source_packages_checked':len(packages),'findings':findings,'urgency_counts':dict(collections.Counter(f['urgency'] for f in findings))}))
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',default='lastcopy:local')
    parser.add_argument('--output',default='docs/verification/stage7/debian-image.json')
    parser.add_argument('--database',default='private/stage7/debian-security.json')
    parser.add_argument('--reuse-database',action='store_true')
    args=parser.parse_args()
    path=Path(args.database).resolve();path.parent.mkdir(parents=True,exist_ok=True)
    url='https://security-tracker.debian.org/tracker/data/json'
    if args.reuse_database:
        if path.stat().st_size>128*1024*1024:raise ValueError('Advisory database exceeds decoded bound')
        data=path.read_bytes()
    else:
        import httpx
        with httpx.Client(timeout=60,trust_env=False) as client:
            with client.stream('GET',url) as response:
                response.raise_for_status();data=bytearray()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data)>128*1024*1024:raise ValueError('Public advisory database exceeds 128 MiB decoded bound')
        path.write_bytes(data)
    image_id=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',args.image],text=True).strip()
    command=['docker','run','--rm','--pull=never','--network','none','--read-only','--memory','768m','--pids-limit','64','-i',
        '--mount',f'type=bind,source={path},target=/audit.json,readonly','--entrypoint','python',image_id,'-']
    result=subprocess.run(command,input=WORKER.encode(),capture_output=True,timeout=120,check=True)
    report=json.loads(result.stdout)
    report.update(observed_at=datetime.now(timezone.utc).isoformat(),database_url=url,
        database_sha256=hashlib.sha256(data).hexdigest(),database_reused=args.reuse_database,image=args.image,image_id=image_id,metadata_exported=False,scanner_network='none',
        scope='Debian bookworm dpkg source packages only; bundled Node/CPython binaries and all application-level vulnerabilities are outside this database. Urgency/status are Debian labels, not invented CVSS scores.')
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='findings'}))


if __name__=='__main__':main()
