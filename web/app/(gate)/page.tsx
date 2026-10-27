import FleetBoard from './fleet-board';
import GateLab from './gate-lab';
import {REPO} from './chrome';
import fleet from '../../public/runs/example-1.json';
import type {RunDoc} from '../../lib/run-types';

const run = fleet as unknown as RunDoc;
const Arrow = () => <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>;

export default function Home() {
  const rows = run.decisions.map(d => ({device: d.device_id, decision: d.decision, why: d.explanation.text}));
  return <main id="main">
    <section className="hero"><div className="wrap">
      <div>
        <span className="kicker">Field data · before the reset</span>
        <h1>Is it safe to <span className="mint">wipe</span> this <i className="serif sky">tablet?</i></h1>
        <p className="lead">Survey teams reset their tablets between rounds. That reset is when unsent records and photos are lost for good, and the server’s “received” count can’t tell you what still exists only on the device. LastCopy gives each tablet one answer: <b style={{color: 'var(--mint2)'}}>safe to wipe</b>, <b style={{color: 'var(--amber)'}}>recover first</b> or <b style={{color: 'var(--rose)'}}>hold</b>, and it proves why down to the record and the photo file.</p>
        <div className="actions">
          <a className="btn primary" href="/demo">Watch the agents investigate <Arrow/></a>
          <a className="btn ghost" href="#gate">Try the gate yourself</a>
        </div>
        <p className="note">Reproduce Fig. 1 with no keys: <code>python run.py</code></p>
      </div>
      <FleetBoard rows={rows} runId={run.run_id} seconds={run.execution_time_seconds}/>
    </div></section>

    <div className="stats"><div className="wrap">
      <div className="stat"><strong>2M<span className="mint">+</span></strong><span>people use ODK</span></div>
      <div className="stat"><strong>250M<span className="mint">+</span></strong><span>submissions a year</span></div>
      <div className="stat"><strong>194</strong><span>countries deployed</span></div>
      <div className="stat"><strong className="sky">0</strong><span>verdicts made by a model</span></div>
      <p className="src">ODK is the open-source standard for offline data collection, used for WHO disease surveillance including polio and cholera. Sources: <a href="https://getodk.org/">getodk.org</a> · <a href="https://digitalpublicgoods.net/registry/odk.html">Digital Public Goods registry</a>.</p>
    </div></div>

    <section className="s" id="problem"><div className="wrap">
      <div className="s-head">
        <div><span className="kicker">The problem</span><h2>“Submitted” is not <i className="serif amber">preserved.</i></h2></div>
        <p className="lead">Coordinators wipe on trust because checking by hand means opening XML and photo files one by one, for every tablet, at the end of a long field day. Three ways a full count still loses data:</p>
      </div>
      <div className="trio">
        <article className="card"><span className="n">01 · MISSING_ATTACHMENT</span><h3>The record arrived. <span className="amber">The photo didn’t.</span></h3><p>Every submission shows as received, but one referenced image never reached the server. The tablet holds the only copy.</p><div className="tagrow"><span className="verdict" data-d="RECOVER_FIRST">Recover first</span></div></article>
        <article className="card"><span className="n">02 · EXPORT_VIEW_ONLY</span><h3>The spreadsheet looks <span className="sky">short.</span></h3><p>Repeated answers are missing from the CSV export, so it looks like data was lost. The raw server XML has every answer. Nothing to recover.</p><div className="tagrow"><span className="verdict" data-d="SAFE_TO_WIPE">Safe to wipe</span></div></article>
        <article className="card"><span className="n">03 · MISSING_SUBMISSION</span><h3>The totals match. <span className="rose">A record is stuck.</span></h3><p>A completed form never left the device, but other uploads made the count look right. Only a device-to-server comparison shows it.</p><div className="tagrow"><span className="verdict" data-d="RECOVER_FIRST">Recover first</span></div></article>
      </div>
    </div></section>

    <section className="s" id="gate" style={{paddingTop: 40}}><div className="wrap">
      <div className="s-head">
        <div><span className="kicker">Try the gate</span><h2>One rule decides. <i className="serif mint">You can read it.</i></h2></div>
        <p className="lead">Set what the verifier found on a tablet and watch the decision change. This is the same rule, in the same order, as the code that issues every LastCopy certificate.</p>
      </div>
      <GateLab/>
      <p className="fig"><b>Fig. 2</b>The wipe gate (<span className="mono">lastcopy/agents.py · wipe_gate</span>). Missing data always wins over “looks fine”, and a missing export is never treated as clean.</p>
    </div></section>

    <section className="s" id="agents" style={{paddingTop: 40}}><div className="wrap">
      <div className="s-head">
        <div><span className="kicker">How it works</span><h2>Agents decide where to look. <i className="serif sky">Code decides what’s true.</i></h2></div>
        <p className="lead">A Meterless World Model holds the investigation as a graph and picks every next step from its state. Nemotron does the judgement work: forming hypotheses, critiquing them, choosing remedies and explaining. A deterministic verifier compares the original bytes, and only the verifier issues verdicts.</p>
      </div>
      <div className="flow">
        <div className="agent" data-k="plan"><div><div className="who"><span>Planner</span></div><h3>World Model</h3></div>
          <div className="loop" aria-label="Planner loop"><span>triage</span><i>→</i><span>classify</span><i>→</i><span>review</span><i>⇄</i><span>fetch evidence</span><i>→</i><span>evaluate</span><i>→</i><span>remedy</span><i>→</i><span>decide</span><i>→</i><span>explain</span></div>
          <span className="pill">Meterless · pinned reference</span></div>
        <div className="agent" data-k="sql"><div className="who"><span>Scout</span><span>Zetaris SQL</span></div><h3>Finds suspicions</h3><p>Four cross-source joins: device records with no server copy, missing files, mismatched XML, answers hidden by the export.</p></div>
        <div className="agent" data-k="model"><div className="who"><span>Investigator</span><span>Nemotron</span></div><h3>Forms hypotheses</h3><p>Turns each suspicion into a testable hypothesis and names the evidence that would settle it.</p></div>
        <div className="agent" data-k="model"><div className="who"><span>Reviewer</span><span>Nemotron + guard</span></div><h3>Pushes back</h3><p>Approves, sends back for revision, or rejects before any evidence is fetched. A code guard enforces its authority.</p></div>
        <div className="agent" data-k="code"><div className="who"><span>Verifier</span><span>Code</span></div><h3>Compares bytes</h3><p>Original device XML and files against server XML, retained history and every attachment slot. The only source of verdicts.</p></div>
        <div className="agent" data-k="code"><div className="who"><span>Hypothesis test</span><span>Code</span></div><h3>Can overturn the AI</h3><p>“Missing answers” refuted by the raw XML → the remedy changes from resubmission to export guidance, and the change is logged.</p></div>
        <div className="agent" data-k="model"><div className="who"><span>Advisor</span><span>Nemotron · limited</span></div><h3>Chooses a remedy</h3><p>Only among the actions code permits for that verdict. With one permitted action, code decides without asking.</p></div>
        <div className="agent" data-k="code"><div className="who"><span>Wipe gate</span><span>Code</span></div><h3>Clears a device</h3><p>Safe, recover first or hold, with a hashed certificate of exactly which bytes were compared.</p></div>
        <div className="agent" data-k="model"><div className="who"><span>Explainer</span><span>Nemotron + check</span></div><h3>Says it plainly</h3><p>Every ID, filename and number is checked against the evidence. One repair attempt, then a template.</p></div>
      </div>
      <div className="rule">
        <div><strong>Schema-bound</strong><p>Every model call returns strict JSON. Invalid output gets one repair, then a labelled fallback, never a silent guess.</p></div>
        <div><strong>Bounded</strong><p>12 steps, 2 critique rounds, 10 model calls, 300 seconds. Exceeding any of these is a controlled failure with the trace so far.</p></div>
        <div><strong>Traced</strong><p>One JSONL line per agent action: agent, action, target, model, retries, status. In <span className="mono">logs/</span> for every example.</p></div>
      </div>
    </div></section>

    <section className="s" id="sponsors" style={{paddingTop: 40}}><div className="wrap">
      <div className="s-head">
        <div><span className="kicker">Under the hood</span><h2>Each sponsor does <i className="serif mint">one real job.</i></h2></div>
        <p className="lead">LastCopy uses each sponsor technology for a specific job. If you removed any one of them, an actual part of the product would stop working.</p>
      </div>
      <div className="sponsors">
        <article className="card sponsor"><span className="role">Evidence layer</span><h3>Zetaris</h3><p>Each run registers the device exports, the server capture, the spreadsheet view and the file references as tables, and the Scout queries across them. Those rows are the only way the agents learn where to look.</p><code>agents.py · evidence_sql</code><span className="proof">Sample mode runs the identical SQL on local SQLite, and every trace line says which engine answered.</span></article>
        <article className="card sponsor"><span className="role">Planner</span><h3>Meterless World Model</h3><p>Holds suspicions, hypothesis revisions, findings, remedies and decisions as a graph, and <b>selects every next action from that state</b>. Python only runs what the graph chooses.</p><code>bridge/investigation-world.ts</code><span className="proof">Pinned reference · conformance 8/8.</span></article>
        <article className="card sponsor"><span className="role">Judgement</span><h3>Nemotron via Nightshift</h3><p>The four judgement roles run on NVIDIA Nemotron through Meterless Nightshift, the only model provider in connected mode. Every trace line records the model that actually answered.</p><code>connected.py · Nightshift.respond</code><span className="proof">Never fabricated: if the provider fails, the run says so.</span></article>
      </div>
    </div></section>

    <section className="s" style={{paddingTop: 0}}><div className="wrap">
      <div className="card cta-band">
        <div><span className="kicker">Run it yourself</span><h2 style={{marginTop: 14, fontSize: 'clamp(1.8rem,3.4vw,2.6rem)'}}>Ten seconds. <i className="serif sky">No keys.</i></h2>
          <pre className="term" style={{padding: '18px 0 0'}}><span className="c">$</span> python run.py{'\n'}<span className="c">  tablet-01 </span> <span className="g">SAFE_TO_WIPE </span>  raw XML has every answer{'\n'}<span className="c">  tablet-02 </span> <span className="y">RECOVER_FIRST</span>  b.bin is not on the server{'\n'}<span className="c">  tablet-04 </span> <span className="r">HOLD         </span>  server answers differ</pre></div>
        <div className="actions"><a className="btn primary" href="/demo">Open the replay <Arrow/></a><a className="btn ghost" href={REPO}>Read the README</a></div>
      </div>
    </div></section>
  </main>;
}
