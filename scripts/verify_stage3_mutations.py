"""Meaningful in-memory broken-behavior controls; never edits production sources."""
import json
import subprocess
import sys
from lastcopy.config import ROOT


def main():
    mutations = [
        ('accept_untrusted_action_fields', "m.validate_action=lambda value,allowed:value['action']", 'test_actions_cannot_smuggle_paths_or_verdicts'),
        ('graph_read_ignores_revisions', "original=m.WorldJournal.read\ndef broken(self,*a,**k):\n r=original(self,*a,**k);r['next_action']='review';return r\nm.WorldJournal.read=broken", 'test_graph_rebuild_idempotency_revision_and_next_action'),
        ('wrong_csv_quote_dialect', "import csv\noriginal=csv.DictWriter\ndef broken(*a,**k):\n k.update(doublequote=True,escapechar=None,quoting=csv.QUOTE_MINIMAL);return original(*a,**k)\ncsv.DictWriter=broken", 'test_csv_json_survives_actual_spark_dialect'),
    ]
    receipts = []
    folder = ROOT / 'private/verification'
    folder.mkdir(parents=True, exist_ok=True)
    for name, mutation, test in mutations:
        source = 'import lastcopy.investigation as m\nimport pytest\n' + mutation + f"\nraise SystemExit(pytest.main(['tests/test_stage3.py::{test}','-q']))"
        result = subprocess.run([sys.executable, '-c', source], cwd=ROOT, capture_output=True, timeout=60)
        (folder / ('stage3-mutation-' + name + '.log')).write_bytes(result.stdout + result.stderr)
        receipts.append({'mutation': name, 'test': test, 'exit_code': result.returncode, 'caught': result.returncode == 1})
    (ROOT / 'docs/verification/stage3-mutations.json').write_text(json.dumps(receipts, indent=2) + '\n')
    if not all(r['caught'] for r in receipts):
        raise SystemExit('A mutation was not caught by a failing assertion')
    print(json.dumps(receipts, indent=2))


if __name__ == '__main__':
    main()
