"""Turn a LastCopy run into a one-page clearance sheet the field lead can print and sign.

  python -m scripts.clearance_sheet output_examples/live_connected_fleet.json > clearance.md

Everything on the sheet is copied from code-made decisions and certificates; nothing is re-worded by a model.
"""
import argparse
import json
from pathlib import Path

ACTION = {'SAFE_TO_WIPE': 'Reset the tablet',
          'RECOVER_FIRST': 'Do not reset. Upload the items listed, then re-run the check',
          'HOLD': 'Do not reset. A data manager must review first'}
LABEL = {'SAFE_TO_WIPE': '✅ SAFE TO WIPE', 'RECOVER_FIRST': '🟧 RECOVER FIRST', 'HOLD': '⛔ HOLD'}


def items(d):
    out = []
    for r in d['records']:
        if r['verdict'] == 'MISSING_ATTACHMENT':
            out.append(f"file {', '.join(r['media_filenames']) or '(unnamed)'} of `{r['version_id']}`")
        elif r['verdict'] == 'MISSING_SUBMISSION':
            out.append(f"whole record `{r['version_id']}`")
        elif r['verdict'] == 'CONTENT_CONFLICT':
            out.append(f"conflicting answers in `{r['version_id']}`")
        elif r['verdict'] == 'UNVERIFIABLE':
            out.append(f"unreadable `{r['version_id']}`")
    if not d['certificate'].get('device_export_sha256'):
        out.append('no export received from this tablet')
    return '; '.join(out) or '-'


def sheet(doc):
    ds = doc['decisions']
    n = {k: sum(d['decision'] == k for d in ds) for k in ACTION}
    models = ', '.join(doc['engines']['models'])
    lines = [f"# Tablet clearance sheet: `{doc['run_id']}`", '',
             f"**Question:** {doc.get('question') or doc.get('label')}  ",
             f"**Mode:** {doc['mode']} · evidence: {', '.join(doc['engines']['evidence'])} · judgement: {models} · verdicts: deterministic code  ",
             f"**Summary:** {n['SAFE_TO_WIPE']} safe to wipe · {n['RECOVER_FIRST']} recover first · {n['HOLD']} hold", '',
             '| Tablet | Decision | Action | Items still only on the tablet / to review | Certificate |',
             '|---|---|---|---|---|']
    for d in ds:
        lines.append(f"| `{d['device_id']}` | {LABEL[d['decision']]} | {ACTION[d['decision']]} | {items(d)} | `{d['certificate_sha256'][:16]}` |")
    lines += ['', '## Why, in plain language', '']
    for d in ds:
        lines.append(f"- **{d['device_id']}:** {d['explanation']['text']}  _(written by {d['explanation']['written_by']}; "
                     f"citations {'checked' if d['explanation'].get('citations_checked') else 'not checked'})_")
    lines += ['', '## Sign-off', '',
              '| Tablet | Reset by | Date | Signature |', '|---|---|---|---|']
    lines += [f"| `{d['device_id']}` | | | |" for d in ds if d['decision'] == 'SAFE_TO_WIPE']
    lines += ['', f"Verify every certificate independently: `python -m scripts.verify_certificate <this run's output JSON> --archive <export.zip> ...`",
              '', '_A certificate proves which bytes were compared under rule lastcopy-wipe-gate/1. It covers only the exports supplied and does not prove the answers are true._', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('output', type=Path)
    print(sheet(json.loads(parser.parse_args().output.read_text(encoding='utf-8'))))


if __name__ == '__main__':
    main()
