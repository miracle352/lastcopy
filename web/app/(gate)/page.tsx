import FleetBoard,{type BoardRow} from './fleet-board';
import GateLab from './gate-lab';
import {REPO} from './chrome';
import liveDoc from '../../public/runs/live-fleet.json';
import type {RunDoc} from '../../lib/run-types';
import {DECISION_TEXT} from '../../lib/wipe-gate';

const live = liveDoc as unknown as RunDoc;
type ModelEvent = {role?: string; actual_serving_model?: string; operation_elapsed_ms?: number; usage?: {total_tokens?: number}; valid?: boolean};
const I = {
  check: <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.2"/><path d="M5.3 8.2l1.8 1.8 3.6-3.8" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>,
  half: <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.2"/><path d="M8 1.5a6.5 6.5 0 010 13z" fill="currentColor" opacity=".55"/></svg>,
  open: <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.2" strokeDasharray="2 2.2"/></svg>,
};
const ico = (d: string, c = 'var(--rose)') => <span className="ico" style={{color: c}} aria-hidden="true"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d={d}/></svg></span>;
const decisionClass = (d: string) => d === 'SAFE_TO_WIPE' ? 'mint' : d === 'RECOVER_FIRST' ? 'amber' : 'rose';

const ANSWERS = [
  ['mint', '✓', 'Safe to wipe', 'SAFE_TO_WIPE', [['Means', 'Every completed record and file from this tablet is positively on the server'], ['Triggered by', 'Only PRESERVED or EXPORT_VIEW_ONLY verdicts'], ['Do next', 'Reset the tablet; keep the certificate'], ['Example', 'tablet-01: the CSV hid answers, the XML had all of them']]],
  ['amber', '↑', 'Recover first', 'RECOVER_FIRST', [['Means', 'This tablet holds the only copy of something the server lacks'], ['Triggered by', 'Any MISSING_ATTACHMENT or MISSING_SUBMISSION'], ['Do next', 'Re-upload the named file or record, then re-check'], ['Example', 'tablet-02: b.bin never reached the server']]],
  ['rose', '‖', 'Hold', 'HOLD', [['Means', 'A person must decide before anything is wiped'], ['Triggered by', 'CONTENT_CONFLICT, UNVERIFIABLE, or no export at all'], ['Do next', 'Compare versions by hand, or export the tablet'], ['Example', 'tablet-05: no export was received']]],
] as const;
const AGENTS = [
  ['World Model planner', 'Chooses triage, classify, review, fetch, evaluate, remedy, decide, explain', 'Meterless', 'sky'],
  ['Scout', 'Four cross-source joins that say where to look', 'Zetaris', 'amber'],
  ['Investigator', 'Turns a suspicion into a testable hypothesis', 'Nemotron', 'sky'],
  ['Reviewer', 'Approves, revises or rejects before evidence is fetched', 'Nemotron', 'sky'],
  ['Evidence fetcher', 'Resolves exact objects and re-checks every hash', 'Zetaris', 'amber'],
  ['Verifier', 'Compares original bytes; the only source of verdicts', 'Code', 'mint'],
  ['Hypothesis test', 'Confirms or refutes; a refutation is logged as a changed decision', 'Code', 'mint'],
  ['Remediation advisor', 'Picks among the actions code permits for the verdict', 'Nemotron', 'sky'],
  ['Wipe gate', 'Safe, recover first or hold, with a hashed certificate', 'Code', 'mint'],
  ['Explainer', 'Writes the sentence; every ID and number is checked', 'Nemotron', 'sky'],
] as const;
const FAQ = [
  ['Does “safe to wipe” mean the data is correct?', 'It means every completed record and referenced file from that tablet was found on the server, byte for byte. The certificate proves which bytes were compared, not that the answers themselves are true.'],
  ['Can the AI make a tablet look safe?', 'No. Verdicts come only from the deterministic verifier, and the wipe gate is plain code. Models choose where to look, critique hypotheses, pick among permitted remedies and write explanations, and every explanation is checked against the evidence.'],
  ['What happens if Nemotron or Zetaris is unavailable?', 'Connected runs fail closed with a structured error; nothing is fabricated. Sample mode runs the same planner, SQL, verifier and gate locally, and every trace line says which engine answered.'],
  ['Why is the spreadsheet example “safe to wipe”?', 'ODK’s CSV export can omit repeated answers. LastCopy checks the raw server XML. When every answer is there, the gap is in the view, not the data, and the Investigator’s “missing answers” hypothesis is refuted.'],
  ['Does LastCopy upload anything to my server?', 'Checks are read-only. The guarded recovery path writes only to a dedicated synthetic ODK Central test project, after a reviewed plan and a fresh read-back.'],
  ['Which ODK versions are supported?', 'Tested with ODK Central v2026.3.1 and Collect v2026.3.5 exports. Encrypted forms and Kobo are not claimed yet.'],
  ['Can I run it myself?', 'Yes. Clone the repository and run python run.py. The five-tablet example runs in about four seconds with no keys or network, and writes the trace and outputs.'],
];

export default function Home() {
  const rows: BoardRow[] = live.decisions.map(d => ({
    device: d.device_id, decision: d.decision, counts: d.counts as Record<string, number>, exported: d.certificate.device_export_sha256 !== null,
    missing: d.records.filter(r => r.verdict === 'MISSING_ATTACHMENT' || r.verdict === 'MISSING_SUBMISSION')
      .map(r => r.verdict === 'MISSING_ATTACHMENT' ? `${r.media_filenames.join(', ')} for ${r.version_id}` : `whole record ${r.version_id}`),
  }));
  const calls = live.events.filter(e => e.kind === 'model') as unknown as ModelEvent[];
  const maxMs = Math.max(...calls.map(e => e.operation_elapsed_ms || 0));
  const tokens = calls.reduce((a, e) => a + (e.usage?.total_tokens || 0), 0);
  const revised = live.events.filter(e => e.agent_name === 'Reviewer' && (e.output_summary || '').startsWith('revise')).length;
  return <main id="main">
    <section className="hero"><div className="wrap">
      <div>
        <span className="kicker">Wipe clearance for field survey tablets</span>
        <h1>Wipe a tablet only after its <span className="sky">last copy</span> is <span className="mint">safe</span>.</h1>
        <p className="lead">Survey teams reset their tablets between rounds, and that reset is when unsent records and photos are lost for good. LastCopy compares every tablet’s original export with the server, byte for byte, and gives the coordinator one answer per device: safe to wipe, recover first or hold, with a certificate that proves why.</p>
        <div className="actions"><a className="btn primary" href="/demo">Watch the live run</a><a className="btn ghost" href="#how">See how it works</a></div>
        <div className="hstats">
          <div><span>Tablets cleared live</span><b>5 of 5 correct</b></div>
          <div><span>Judgement model</span><b>Nemotron 3.5</b></div>
          <div><span>Verdicts by a model</span><b className="mint">0</b></div>
        </div>
      </div>
      <FleetBoard rows={rows}/>
    </div></section>

    <div className="wrap" data-r><div className="card glance">
      <div className="gh">LastCopy at a glance</div>
      <div className="gg">
        <div><span className="kicker">Problem</span><p>“Received” on the server is not “preserved”. Photos go missing, records stay stuck on a tablet and spreadsheets hide answers, so coordinators wipe devices on trust.</p></div>
        <div><span className="kicker">Solution</span><p>A per-tablet wipe gate. Code compares original device bytes with the server, agents decide where to look and explain the result, and the gate signs a hashed certificate.</p></div>
        <div><span className="kicker">How it’s built</span><p>A Meterless World Model plans every step, Zetaris answers four cross-source SQL joins, Nemotron via Nightshift fills four judgement roles, and a deterministic verifier owns every verdict.</p></div>
        <div><span className="kicker">Status</span><p>Ran live on 27 Oct with Zetaris and Nemotron: 0 fallbacks, 5 of 5 decisions correct. 292 tests pass. <span className="mono">python run.py</span> reproduces it with no keys. Not yet piloted with a real field team.</p></div>
      </div>
    </div></div>

    <section className="s" id="problem" style={{marginTop: 112}}><div className="wrap">
      <div className="head" data-r><span className="kicker">The problem</span><h2>The count says received. The tablet still holds the only copy.</h2>
        <p className="lead">ODK is the open-source standard for offline data collection: over 2 million people send more than 250 million submissions a year, in 194 countries, including WHO polio and cholera surveillance. Every round ends with a reset.</p></div>
      <div className="g3" data-r>
        <article className="card pcard">{ico('M4 5h16v14H4zM4 15l4-4 4 4 3-3 5 5', 'var(--amber)')}<h3>The photo never arrived</h3><p>The record reached the server but a referenced image did not. Every count looks complete, and the tablet holds the last copy of the file.</p></article>
        <article className="card pcard">{ico('M4 4h16v16H4zM4 9h16M9 9v11', 'var(--sky)')}<h3>The spreadsheet looks short</h3><p>Repeated answers are missing from the CSV export, so it looks as if data was lost. The raw server XML has every answer, so there is nothing to recover.</p></article>
        <article className="card pcard">{ico('M12 3v12M7 10l5 5 5-5M5 21h14')}<h3>A record never left</h3><p>A completed form is stuck on the device while other uploads make the totals match. Only a device-to-server comparison shows it.</p></article>
      </div>
      <div className="card compare" data-r>
        <div className="row h"><div/><div>Wiping today</div><div>With LastCopy</div></div>
        <div className="row"><div>Evidence</div><div>A submission count on the server</div><div>Original device bytes against server XML, history and every file</div></div>
        <div className="row"><div>Decision</div><div>Wipe on trust at the end of the day</div><div>Safe to wipe, recover first or hold, per tablet</div></div>
        <div className="row"><div>Proof</div><div>None; a loss is found months later, if ever</div><div>A hashed certificate naming exactly which bytes were compared</div></div>
      </div>
    </div></section>

    <section className="s alt" id="how"><div className="wrap">
      <div className="head" data-r><span className="kicker">How it works</span><h2>Four steps from a tablet export to a signed answer.</h2>
        <p className="lead">Agents decide where to look. Code decides what is true. A World Model plans every step, so the path changes with what the evidence shows.</p></div>
      <div className="g4" data-r>
        <article className="card step"><div className="n"><b>01</b><span className="badge amber">Zetaris</span></div><h3>Capture both sides</h3><p>The tablet’s ODK Collect export and a read-only capture of the server are sealed with SHA-256 and registered as tables.</p><div className="tags"><span className="tag">seal</span><span className="tag">register_sources</span></div></article>
        <article className="card step"><div className="n"><b>02</b><span className="badge sky">Nemotron</span></div><h3>Scout and hypothesise</h3><p>Four cross-source joins surface suspicions. The Investigator turns each into a testable hypothesis, and the Reviewer can send it back.</p><div className="tags"><span className="tag">triage</span><span className="tag">classify</span><span className="tag">review</span></div></article>
        <article className="card step"><div className="n"><b>03</b><span className="badge mint">Code</span></div><h3>Verify the bytes</h3><p>The verifier compares original XML, retained history and every attachment slot. Raw evidence can overturn the model’s guess.</p><div className="tags"><span className="tag">fetch_evidence</span><span className="tag">evaluate</span></div></article>
        <article className="card step"><div className="n"><b>04</b><span className="badge mint">Code</span></div><h3>Clear or hold</h3><p>The wipe gate decides per tablet and signs a certificate. Nemotron writes the sentence, and every ID in it is checked.</p><div className="tags"><span className="tag">remedy</span><span className="tag">decide</span><span className="tag">explain</span></div></article>
      </div>
      <div id="gate" data-r><GateLab/></div>
    </div></section>

    <section className="s" id="answers"><div className="wrap">
      <div className="head" data-r><span className="kicker">The answers</span><h2>Three answers, zero ambiguity.</h2>
        <p className="lead">LastCopy never says “probably fine”. Missing data always outranks “looks fine”, and a tablet that was never exported is never treated as clean.</p></div>
      <div className="card eq" data-r>
        <span className="pillbig"><span className="tab-ico" style={{width: 18, height: 24, borderRadius: 4}} aria-hidden="true"/>1 tablet</span><span className="op">=</span>
        <span className="pillbig"><span className="chip mint">✓</span>Safe to wipe</span><span className="op">or</span>
        <span className="pillbig"><span className="chip amber">↑</span>Recover first</span><span className="op">or</span>
        <span className="pillbig"><span className="chip rose">‖</span>Hold</span>
      </div>
      <div className="g3" style={{marginTop: 14}} data-r>
        {ANSWERS.map(([c, sym, t, k, rows]) => <article key={k} className="card spec">
          <div className="top"><span className={`chip ${c}`} style={{width: 34, height: 34, fontSize: '.85rem'}}>{sym}</span><div><h3>{t}</h3><small className={`${c} mono`}>{k}</small></div></div>
          <dl>{rows.map(([a, b]) => <div key={a}><dt>{a}</dt><dd>{b}</dd></div>)}</dl>
        </article>)}
      </div>
    </div></section>

    <section className="s alt" id="who"><div className="wrap">
      <div className="head" data-r><span className="kicker">Who it’s for</span><h2>Different people, one question before the reset.</h2>
        <p className="lead">Everyone downstream of a field round depends on the tablets being cleared correctly.</p></div>
      <div className="g3" data-r>
        <article className="card persona">{ico('M12 12a4 4 0 100-8 4 4 0 000 8zM4 21a8 8 0 0116 0', 'var(--mint)')}<h3>Field coordinators</h3><p>Collect twenty tablets at the end of a round and need to hand them back clean the next morning.</p><div className="with"><span className="kicker">With LastCopy</span><p>One list: which tablets to reset now, which to plug back in, which to escalate.</p></div></article>
        <article className="card persona">{ico('M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3zM4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3', 'var(--sky)')}<h3>Data managers</h3><p>Own the ODK Central project and get blamed for gaps found months later in analysis.</p><div className="with"><span className="kicker">With LastCopy</span><p>Findings down to the record, the repeat and the filename, with SQL and certificates they can audit.</p></div></article>
        <article className="card persona">{ico('M4 19V5M4 19h16M8 15l3-4 3 2 5-6', 'var(--amber)')}<h3>Programme leads</h3><p>Answer to funders and health ministries for complete, defensible survey data.</p><div className="with"><span className="kicker">With LastCopy</span><p>A per-round record that nothing was wiped before it was safe, signed by code rather than trust.</p></div></article>
      </div>
    </div></section>

    <section className="s" id="hood"><div className="wrap">
      <div className="head" data-r><span className="kicker">Under the hood</span><h2>Agents that can be overruled. Code that cannot.</h2>
        <p className="lead">The World Model holds the investigation as a graph and picks every next action from its state. Each model role is schema-bound, budgeted and checked; each verdict comes from a byte comparison.</p></div>
      <div className="hood" data-r>
        <div className="card panel"><span className="kicker">Investigation graph</span>
          <div className="well box hl"><b>World Model<small>Meterless · pinned reference</small></b><p>Holds suspicions, hypotheses, revisions, findings, remedies and decisions. Selects the next action from graph state; Python only dispatches it.</p></div>
          <div className="sub">plans over</div>
          <div className="boxes3"><div className="well box"><b>Suspicion</b><p>a Scout SQL row</p></div><div className="well box"><b>Hypothesis</b><p>reviewed, revisable</p></div><div className="well box"><b>Finding</b><p>a verified verdict</p></div></div>
          <div className="sub">decided by code</div>
          <div className="boxes2"><div className="well box hl2"><b>Verifier</b><p>Original bytes vs server XML, history and files</p></div><div className="well box hl2"><b>Wipe gate</b><p>Per-tablet decision and certificate</p></div></div>
          <div style={{borderTop: '1px dashed var(--line-2)', margin: '18px 0'}}/>
          <div className="well box"><b>Budgets</b><p>12 steps · 2 critique rounds · 10 model calls · 300 s. Exceeding one is a controlled failure with the trace so far.</p></div>
          <div className="well box" style={{marginTop: 8}}><b>Trace</b><p>One JSONL line per agent action: agent, action, target, model, retries, status. Every example ships its log.</p></div>
        </div>
        <div className="card panel"><span className="kicker">Agents</span>
          <div className="ilist">{AGENTS.map(([n, d, b, c]) => <div key={n}><b>{n}</b><span className={`badge ${c}`}>{b}</span><p>{d}</p></div>)}</div>
        </div>
      </div>
      <div className="hood" style={{marginTop: 16}} data-r>
        <div className="card code"><div className="ch"><span>The wipe gate</span><span>lastcopy/agents.py</span></div>
<pre><span className="c"># per tablet, from verified findings only</span>{'\n'}<span className="k">if</span> device <span className="k">in</span> coverage[<span className="s">&apos;missing_devices&apos;</span>]:{'\n'}    decision = <span className="r">&apos;HOLD&apos;</span>           <span className="c"># never exported</span>{'\n'}<span className="k">elif</span> any(v <span className="k">in</span> MISSING <span className="k">for</span> v <span className="k">in</span> verdicts):{'\n'}    decision = <span className="y">&apos;RECOVER_FIRST&apos;</span>  <span className="c"># only copy is here</span>{'\n'}<span className="k">elif</span> any(v <span className="k">in</span> CONFLICT <span className="k">for</span> v <span className="k">in</span> verdicts):{'\n'}    decision = <span className="r">&apos;HOLD&apos;</span>           <span className="c"># a person decides</span>{'\n'}<span className="k">elif not</span> findings:{'\n'}    decision = <span className="r">&apos;HOLD&apos;</span>{'\n'}<span className="k">else</span>:{'\n'}    decision = <span className="s">&apos;SAFE_TO_WIPE&apos;</span>   <span className="c"># all preserved</span>{'\n\n'}certificate_sha256 = sha256(canonical(certificate))</pre>
          <div className="cf">Simplified from <span className="mono">wipe_gate()</span>. A model’s output never reaches this function.</div></div>
        <div className="props">
          <div className="card prop">{I.check}<div><h3>Code owns every verdict</h3><p>Models propose, critique, choose and explain. They cannot change a verdict or make a tablet look safe.</p></div></div>
          <div className="card prop">{I.check}<div><h3>The AI can be proved wrong</h3><p>“Missing answers” refuted by raw XML becomes export guidance, not a resubmission, and the trace logs the change.</p></div></div>
          <div className="card prop">{I.check}<div><h3>Schema-bound, never silent</h3><p>Strict JSON per role, one repair with the errors, then a labelled fallback. Explanations are checked token by token.</p></div></div>
          <div className="card prop">{I.check}<div><h3>Originals untouched</h3><p>Source archives are sealed and never modified. Recovery writes only to a dedicated synthetic ODK test project.</p></div></div>
        </div>
      </div>
    </div></section>

    <section className="s alt" id="live"><div className="wrap">
      <div className="head" data-r><span className="kicker">Live run</span><h2>Run live on 27 October, with every sponsor in the loop.</h2>
        <p className="lead">Zetaris answered every query for the five-tablet fleet, and NVIDIA Nemotron answered every judgement call through Meterless Nightshift. The decisions match the keyless sample run because code makes them.</p></div>
      <div className="card live" data-r>
        <div className="lh"><div><span className="livedot">Live connected run</span><h3>Every judgement call, as Nightshift reported it</h3></div><a className="small" href="/demo">Open the full trace ↗</a></div>
        <div className="tblwrap"><table className="tbl">
          <thead><tr><th>Role</th><th>Model that answered</th><th>Latency</th><th className="num">Tokens</th><th className="num">Output</th></tr></thead>
          <tbody>{calls.map((x, k) => { const ms = x.operation_elapsed_ms || 0;
            return <tr key={k}><td className="who" style={{textTransform: 'capitalize'}}>{x.role}</td><td className="mono" style={{color: 'var(--sky)'}}>{x.actual_serving_model}</td>
              <td><div className="meter"><i style={{width: `${Math.max(6, (ms / maxMs) * 110)}px`}}/><span>{(ms / 1000).toFixed(1)} s</span></div></td>
              <td className="num">{x.usage?.total_tokens ?? '–'}</td><td className="num" style={{color: x.valid ? 'var(--mint)' : 'var(--rose)'}}>{x.valid ? 'schema-valid' : 'rejected'}</td></tr>; })}</tbody>
        </table></div>
        <div className="lf">{calls.length} model calls, {tokens.toLocaleString('en-US')} tokens, 0 fallbacks. The Reviewer sent all five hypotheses back for revision; after {live.critique_rounds} critique rounds the cap forced them to be tested ({revised} review decisions logged). {live.queries.length} evidence queries ran on Zetaris.</div>
      </div>
      <div className="side" data-r>
        <div style={{display: 'grid', gap: 12}}>
          <div className="card feat">{ico('M4 6h16M4 12h16M4 18h10', 'var(--amber)')}<div><h3>Zetaris: the evidence layer</h3><p>Each run registers device exports, the server capture, the spreadsheet view and file references as tables in an isolated database. The Scout’s joins are the only way the agents learn where to look.</p></div></div>
          <div className="card feat">{ico('M12 3l8 4.5v9L12 21l-8-4.5v-9zM12 12l8-4.5M12 12v9M12 12L4 7.5', 'var(--sky)')}<div><h3>Meterless World Model: the planner</h3><p>The pinned reference (conformance 8/8) rebuilds the run’s graph after every step and returns the next action, its focus and its reason, all shown in the replay.</p></div></div>
          <div className="card feat">{ico('M13 2L4 14h7l-1 8 9-12h-7z', 'var(--mint)')}<div><h3>Nemotron via Nightshift: judgement</h3><p>Investigator, Reviewer, Advisor and Explainer run on Nemotron through Nightshift, the only provider in connected mode. The model on every trace line is the one Nightshift reported.</p></div></div>
        </div>
        <div className="card receipt">
          <span className="livedot">From the live trace</span>
          <div className="rt"><span className="nv">NV</span><div><b>Nemotron 3.5 Lightning</b><small className="mono">nvidia/nemotron-3.5-lightning-30b-a3b</small></div></div>
          {[['Provider path', 'Nightshift → NVIDIA'], ['Model calls', String(calls.length)], ['Fallbacks', '0'], ['Critique rounds', String(live.critique_rounds)], ['Planner steps', String(live.steps)]].map(([a, b]) => <div className="kv" key={a}><span>{a}</span><b>{b}</b></div>)}
          <div className="tags">{live.decisions.map(d => <span key={d.device_id} className={`badge ${decisionClass(d.decision)}`}>{d.device_id} · {DECISION_TEXT[d.decision]}</span>)}</div>
          <p className="note">Nemotron wrote the explanations for all five tablets, and each one passed the citation check. Full export: <a className="mono" href={`${REPO}/blob/main/output_examples/live_connected_fleet.json`} style={{textDecoration: 'underline'}}>live_connected_fleet.json</a></p>
        </div>
      </div>
    </div></section>

    <section className="s" id="roadmap"><div className="wrap">
      <div className="head" data-r><span className="kicker">Roadmap</span><h2>From a hackathon gate to the end-of-round checklist.</h2>
        <p className="lead">What ships today, and what it takes to put LastCopy in front of real ODK field teams.</p></div>
      <div className="g3" data-r>
        <article className="card rm now"><div className="rh"><span className="badge mint"><span className="dot"/>Now</span><span>01</span></div><h3>Hackathon build</h3><ul>
          {['Per-tablet wipe gate with hashed certificates', 'World Model–planned agent loop with Reviewer pushback', 'Zetaris cross-source evidence and a byte-level verifier', 'Live connected run with Nemotron via Nightshift', 'python run.py: four examples and traces, no keys', '292 tests; guarded recovery to a synthetic ODK project'].map(t => <li key={t} className="mint">{I.check}<span style={{color: 'var(--text)'}}>{t}</span></li>)}</ul></article>
        <article className="card rm"><div className="rh"><span className="badge">Next</span><span>02</span></div><h3>Field pilot</h3><ul>
          {['A coordinator checklist for a whole round of tablets', 'Direct USB export from ODK Collect devices', 'Pilot with a partner survey team, synthetic data first'].map((t, k) => <li key={t} style={{color: k === 0 ? 'var(--amber)' : 'var(--dim)'}}>{k === 0 ? I.half : I.open}<span style={{color: 'var(--text)'}}>{t}</span></li>)}</ul></article>
        <article className="card rm"><div className="rh"><span className="badge">Later</span><span>03</span></div><h3>Every ODK deployment</h3><ul>
          {['KoboToolbox and other ODK-compatible servers', 'Encrypted form support', 'Independent security review before real field data'].map(t => <li key={t} style={{color: 'var(--dim)'}}>{I.open}<span style={{color: 'var(--text)'}}>{t}</span></li>)}</ul></article>
      </div>
    </div></section>

    <section className="s alt" id="faq"><div className="wrap">
      <div className="head center" data-r><span className="kicker">FAQ</span><h2>Questions, answered.</h2>
        <p className="lead center">What LastCopy guarantees, and what it does not do yet.</p></div>
      <div className="faq" data-r>{FAQ.map(([q, a]) => <details key={q}><summary>{q}</summary><p>{a}</p></details>)}</div>
    </div></section>

    <section className="s" style={{paddingTop: 96}}><div className="wrap" data-r>
      <div className="card cta"><h2>Clear your first tablet in four seconds.</h2><p>Clone the repo, run <span className="mono">python run.py</span> and watch five tablets get a signed answer. No keys, no network.</p>
        <div className="actions"><a className="btn primary" href={REPO}>Get the code</a><a className="btn ghost" href="/demo">Watch the live run</a></div></div>
    </div></section>
  </main>;
}
