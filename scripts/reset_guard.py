"""Reset guard: allow a factory reset only when a valid certificate proves the tablet is safe.

Run it at the moment of reset, with a fresh export of the tablet you are about to wipe:

  python -m scripts.reset_guard output_examples/live_connected_fleet.json \
      --device tablet-01 --export fixtures/fleet/tablet-01.zip

  ALLOW  tablet-01  certificate valid, SAFE_TO_WIPE, export unchanged since the check

Exit codes, for device-management (MDM) scripts and kiosk tools:
  0  ALLOW  every check passed; the reset may proceed
  3  BLOCK  the reset must not happen; the reason is printed (or in --json)
  2  usage error (missing file, unknown device)

The guard is deterministic code with no network and no model. It allows a reset only if all of these hold:
  1. the certificate's SHA-256 matches its canonical JSON (nothing was edited);
  2. its rule is lastcopy-wipe-gate/1 and its decision follows from its own verdicts;
  3. the decision is SAFE_TO_WIPE and no Adversary objection was left open;
  4. the fresh export hashes to the exact bytes the certificate was issued for,
     so anything collected on the tablet after the check blocks the reset;
  5. optionally (--max-age-hours) the run is recent enough.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.verify_certificate import expected_decision, sha256

ALLOW, BLOCK, USAGE = 0, 3, 2


def canonical_sha256(cert: dict) -> str:
    return sha256(json.dumps(cert, sort_keys=True, separators=(',', ':')).encode())


def guard(doc: dict, device: str, export_bytes: bytes | None, max_age_hours: float | None = None,
          now: datetime | None = None) -> dict:
    """Return {'verdict': 'ALLOW'|'BLOCK', 'device', 'reasons': [...], 'checks': [...]}."""
    match = [d for d in doc.get('decisions', []) if d.get('device_id') == device]
    if not match:
        raise KeyError(device)
    d = match[0]
    cert = d['certificate']
    checks: list[tuple[str, bool, str]] = []

    checks.append(('certificate hash', canonical_sha256(cert) == d.get('certificate_sha256'),
                   (d.get('certificate_sha256') or '')[:16]))
    rule_ok = cert.get('rule') == 'lastcopy-wipe-gate/1'
    checks.append(('rule version', rule_ok, str(cert.get('rule'))))
    if rule_ok:
        want = expected_decision(cert)
        checks.append(('decision follows rule', want == cert.get('decision') == d.get('decision'),
                       f"{cert.get('decision')} (rule gives {want})"))
    checks.append(('decision is SAFE_TO_WIPE', cert.get('decision') == 'SAFE_TO_WIPE', str(cert.get('decision'))))
    checks.append(('no open Adversary objection', not cert.get('challenge'),
                   'open objection' if cert.get('challenge') else 'none'))

    sealed = cert.get('device_export_sha256')
    if export_bytes is None:
        checks.append(('fresh export matches certificate', False, 'no fresh export supplied'))
    elif sealed is None:
        checks.append(('fresh export matches certificate', False, 'certificate names no export'))
    else:
        fresh = sha256(export_bytes)
        checks.append(('fresh export matches certificate', fresh == sealed,
                       'unchanged since the check' if fresh == sealed
                       else f'tablet changed since the check ({fresh[:12]}… ≠ {sealed[:12]}…)'))

    if max_age_hours is not None:
        captured = doc.get('captured_at')
        if not captured:
            checks.append(('run is recent', False, 'run has no captured_at time'))
        else:
            when = datetime.fromisoformat(captured.replace('Z', '+00:00'))
            age = ((now or datetime.now(timezone.utc)) - when).total_seconds() / 3600
            checks.append(('run is recent', age <= max_age_hours, f'{age:.1f} h old (limit {max_age_hours:g} h)'))

    failed = [f'{name}: {detail}' for name, ok, detail in checks if not ok]
    return {
        'verdict': 'BLOCK' if failed else 'ALLOW',
        'device': device,
        'run_id': doc.get('run_id'),
        'decision': cert.get('decision'),
        'reasons': failed or ['certificate valid, SAFE_TO_WIPE, export unchanged since the check'],
        'checks': [{'check': n, 'pass': ok, 'detail': det} for n, ok, det in checks],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('output', type=Path, help='a LastCopy output JSON holding the certificates')
    p.add_argument('--device', required=True, help='device id of the tablet about to be reset, e.g. tablet-01')
    p.add_argument('--export', type=Path, help='a fresh export of that tablet, taken just before the reset')
    p.add_argument('--max-age-hours', type=float, help='block if the check is older than this')
    p.add_argument('--json', action='store_true', help='print the result as JSON')
    a = p.parse_args()
    try:
        doc = json.loads(a.output.read_text(encoding='utf-8'))
        export = a.export.read_bytes() if a.export else None
        result = guard(doc, a.device, export, a.max_age_hours)
    except (OSError, ValueError) as exc:
        print(f'usage error: {exc}', file=sys.stderr)
        sys.exit(USAGE)
    except KeyError:
        print(f'usage error: no certificate for device {a.device!r} in {a.output}', file=sys.stderr)
        sys.exit(USAGE)
    if a.json:
        print(json.dumps(result, indent=2))
    else:
        for c in result['checks']:
            print(f"  {'PASS' if c['pass'] else 'FAIL'}  {c['check']:<34} {c['detail']}")
        print(f"\n{result['verdict']}  {a.device}  " + '; '.join(result['reasons']))
    sys.exit(ALLOW if result['verdict'] == 'ALLOW' else BLOCK)


if __name__ == '__main__':
    main()
