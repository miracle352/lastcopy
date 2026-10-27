"""Independently re-check LastCopy wipe certificates. No LastCopy runtime, no network, no model.

  python -m scripts.verify_certificate output_examples/example_1_output.json
  python -m scripts.verify_certificate output_examples/example_1_output.json \
      --archive fixtures/fleet/tablet-01.zip --archive fixtures/fleet/tablet-02.zip \
      --archive fixtures/fleet/server-payload.zip

For every device it checks that:
  1. certificate_sha256 is the SHA-256 of the canonical certificate JSON (nothing was edited);
  2. the decision follows from the certificate's own verdicts under rule lastcopy-wipe-gate/1;
  3. any archive you pass hashes to the device-export or server-capture hash the certificate names.
Exit code 0 only if every check passes.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

MISSING = {'MISSING_SUBMISSION', 'MISSING_ATTACHMENT'}
UNCERTAIN = {'CONTENT_CONFLICT', 'UNVERIFIABLE'}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_decision(cert: dict) -> str:
    """lastcopy-wipe-gate/1, restated from the certificate alone."""
    verdicts = {r['verdict'] for r in cert['records']}
    if cert['device_export_sha256'] is None:
        return 'HOLD'
    if verdicts & MISSING:
        return 'RECOVER_FIRST'
    if verdicts & UNCERTAIN:
        return 'HOLD'
    if not verdicts:
        return 'HOLD'
    return 'SAFE_TO_WIPE'


def check(doc: dict, archives: dict[str, str]) -> list[tuple[str, str, bool, str]]:
    rows = []
    for d in doc['decisions']:
        cert, dev = d['certificate'], d['device_id']
        canonical = json.dumps(cert, sort_keys=True, separators=(',', ':')).encode()
        rows.append((dev, 'certificate hash', sha256(canonical) == d['certificate_sha256'], d['certificate_sha256'][:16]))
        if cert.get('rule') != 'lastcopy-wipe-gate/1':
            rows.append((dev, 'rule version', False, str(cert.get('rule'))))
            continue
        want = expected_decision(cert)
        rows.append((dev, 'decision follows rule', want == cert['decision'] == d['decision'], f"{cert['decision']} (rule gives {want})"))
        for label, key in (('device export', 'device_export_sha256'), ('server capture', 'server_capture_sha256')):
            h = cert.get(key)
            if h and h in archives:
                rows.append((dev, f'{label} bytes', True, f'{archives[h]} matches'))
    named = {d['certificate'].get(k) for d in doc['decisions'] for k in ('device_export_sha256', 'server_capture_sha256')}
    for h, name in archives.items():
        if h not in named:
            rows.append(('-', 'archive named by a certificate', False, f'{name} ({h[:16]}…) is not in any certificate'))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('output', type=Path, help='a LastCopy output JSON (output_examples/*.json)')
    parser.add_argument('--archive', type=Path, action='append', default=[], help='a device export or server payload to hash-check')
    args = parser.parse_args()
    doc = json.loads(args.output.read_text(encoding='utf-8'))
    archives = {sha256(p.read_bytes()): p.name for p in args.archive}
    rows = check(doc, archives)
    for dev, what, ok, detail in rows:
        print(f"  {'PASS' if ok else 'FAIL'}  {dev:<10} {what:<24} {detail}")
    failed = sum(not ok for *_, ok, _ in rows)
    print(f"\n{len(rows) - failed}/{len(rows)} checks passed for {len(doc['decisions'])} certificate(s) in run {doc['run_id']} ({doc['mode']}).")
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
