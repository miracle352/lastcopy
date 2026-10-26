"""Read-only operator queue for authenticated account erasure-review requests.

Run on the host; identifiers stay private. This command never erases or revokes.
"""
import argparse,json,re,sqlite3
from contextlib import closing
from pathlib import Path


def pending(root):
    rows=[]
    for database in sorted((Path(root)/'accounts').glob('*/lastcopy.sqlite3')):
        if not re.fullmatch(r'[a-f0-9]{64}',database.parent.name) or database.is_symlink() or database.parent.is_symlink():
            raise ValueError('Unexpected account store identity')
        with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as c:
            if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='privacy_request'").fetchone():continue
            row=c.execute('SELECT requested_at,state FROM privacy_request WHERE id=1').fetchone()
        if row:rows.append({'account_id':database.parent.name,'requested_at':row[0],'state':row[1]})
        if len(rows)>100:raise ValueError('Privacy queue exceeds pilot account bound')
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--store',type=Path,required=True);args=p.parse_args()
    print(json.dumps({'requests':pending(args.store),'automatic_deletion':False,'backup_expiry_active':False},indent=2))


if __name__=='__main__':main()
