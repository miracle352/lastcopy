"""Record a non-secret backup service observation for the private owner UI."""
import argparse
import json
import os
from pathlib import Path
from datetime import datetime, timezone


def record(path, state, receipt=None):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    value={}
    if path.exists():
        if path.is_symlink() or path.stat().st_size>4096:raise ValueError('Invalid backup health file')
        value=json.loads(path.read_bytes())
    now=datetime.now(timezone.utc).isoformat()
    output={'state':state,'observed_at':now,'last_success':value.get('last_success')}
    if state=='success':
        receipt=json.loads(Path(receipt).read_bytes())
        if not receipt.get('central_database') or not receipt.get('application_databases'):raise ValueError('Incomplete backup receipt')
        output['last_success']=receipt['created_at']
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(output)+'\n',encoding='utf-8')
    os.chmod(temporary,0o644)  # Non-secret timestamps only; the API process has a separate UID.
    os.replace(temporary,path)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path',type=Path,required=True)
    parser.add_argument('--state',choices=['running','success','failed'],required=True)
    parser.add_argument('--receipt',type=Path)
    args=parser.parse_args()
    record(args.path,args.state,args.receipt)
