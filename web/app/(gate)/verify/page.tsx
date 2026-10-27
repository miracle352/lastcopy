import Verifier from './verifier';
import {REPO} from '../chrome';

export const metadata = {title: 'LastCopy · Verify a certificate'};

export default function Verify() {
  return <main id="main">
    <div className="page-head"><div className="wrap">
      <span className="kicker">Verify &amp; reset guard</span>
      <h1>Don’t trust us. <span className="c-mint">Check the bytes.</span></h1>
      <p className="lede">Every LastCopy decision ships with a certificate. This page re-checks them in your browser: it recomputes each certificate’s SHA-256, re-derives the decision from the wipe rule, and hashes the original archives. Then the reset guard says whether each tablet may be wiped. No LastCopy server, no model, and nothing leaves your machine.</p>
    </div></div>
    <div className="wrap" style={{paddingBottom: 120}}>
      <Verifier/>
      <div className="card" style={{padding: '22px 26px', marginTop: 28}}>
        <span className="kicker">The same guard, for device-management scripts</span>
        <pre className="mono" style={{margin: '14px 0 0', fontSize: 13.5, lineHeight: 1.7, whiteSpace: 'pre-wrap', color: 'var(--body)'}}>{`python -m scripts.reset_guard output_examples/live_connected_fleet.json \\
    --device tablet-01 --export fresh-tablet-01.zip [--max-age-hours 24] [--json]

exit 0  ALLOW   certificate valid, SAFE_TO_WIPE, export unchanged since the check
exit 3  BLOCK   anything else, with the reason`}</pre>
        <p className="fig" style={{marginTop: 14}}>Run it at the moment of reset with a fresh export. If anything was collected on the tablet after the check, the bytes no longer match the certificate and the reset is blocked. Source: <a href={`${REPO}/blob/main/scripts/reset_guard.py`} style={{textDecoration: 'underline'}}>scripts/reset_guard.py</a>.</p>
      </div>
    </div>
  </main>;
}
