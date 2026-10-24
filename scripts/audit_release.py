"""Read-only tracked/history credential checks; reports locations, never values.

This focused audit is not a guarantee that all possible secret formats are known.
"""
import json
import re
import subprocess
from pathlib import Path
from dotenv import dotenv_values
from lastcopy.config import ROOT


def main():
    values = []
    for key, value in dotenv_values(ROOT/'.env').items():
        if not value or not re.search(r'TOKEN|PASSWORD|SECRET|HEADERS', key):
            continue
        if len(value) >= 12:
            values.append(value.encode())
        if key.endswith('JSON'):
            try:
                values += [str(v).encode() for v in json.loads(value).values() if len(str(v)) >= 12]
            except (ValueError, AttributeError):
                pass
    patterns = [rb'nvapi-[A-Za-z0-9_-]{24,}', rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
    tracked = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    assert '.env' not in tracked and not any(p.startswith('private/') for p in tracked)
    findings = []
    working_count = 0
    for path in tracked:
        if not path or not (ROOT/path).is_file():
            continue
        data = (ROOT/path).read_bytes(); working_count += 1
        if any(v in data for v in values) or any(re.search(p, data) for p in patterns):
            findings.append({'path':path,'reason':'working-tree credential pattern or configured secret bytes'})
    rows = subprocess.check_output(['git', 'rev-list', '--objects', '--all'], cwd=ROOT).decode().splitlines()
    worker = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    count = 0
    try:
        for row in rows:
            oid, _, path = row.partition(' ')
            worker.stdin.write(oid.encode()+b'\n'); worker.stdin.flush()
            header = worker.stdout.readline().decode().split()
            data = worker.stdout.read(int(header[2])); worker.stdout.read(1)
            if header[1] != 'blob':
                continue
            count += 1
            if any(v in data for v in values) or any(re.search(p, data) for p in patterns):
                findings.append({'object': oid, 'path': path, 'reason': 'credential pattern or configured private secret bytes'})
    finally:
        worker.stdin.close(); worker.wait(timeout=10)
    result = {'history_blobs_checked': count, 'working_files_checked':working_count, 'configured_secret_values_checked': len(values),
        'tracked_env_or_private_files': False, 'findings': findings,
        'scope': 'All Git history blobs against current configured secret bytes and explicit key patterns; not an exhaustive entropy scanner. No stored NVIDIA key was read.'}
    target = ROOT/'docs/verification/stage7/release-security.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2)+'\n', encoding='utf8')
    print(json.dumps(result))
    return 1 if findings else 0


if __name__ == '__main__':
    raise SystemExit(main())
