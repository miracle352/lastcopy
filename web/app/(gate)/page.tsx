import GateLab from './gate-lab';
import HeroFigure from './hero-figure';
import {Icon, REPO} from './chrome';
import live from '../../public/runs/live-fleet.json';
import type {RunDoc} from '../../lib/run-types';
import {DECISION_TEXT} from '../../lib/wipe-gate';
import bench from '../../public/runs/benchmark.json';

const run = live as unknown as RunDoc;
const strip = (t: string) => {const s = t.replace(/^(SAFE_TO_WIPE|RECOVER_FIRST|HOLD):\s*/, ''); return s.charAt(0).toUpperCase() + s.slice(1);};
const zetaris = run.queries.filter(q => q.provider === 'zetaris').length;
const modelCalls = run.events.filter(e => e.kind === 'model' && e.valid).length;
const fallbacks = run.events.filter(e => e.kind === 'fallback').length;
const B = bench as {seeds: string; fleets: number; fleets_correct: number; tablets: number; tablets_correct: number; wrongly_cleared: number;
  by_truth: Record<string, string>; by_planted_condition: Record<string, string>; mean_seconds_per_fleet: number};
const COND: Record<string, string> = {ok: 'Record matched the server', view_only: 'Spreadsheet hides answers (raw XML has them)', no_photo: 'Photo never uploaded',
  never_arrived: 'Whole record never arrived', edited: 'Answer edited on the server', 'no export': 'Tablet never exported'};

export default function Home() {
  return <main id="main">
    {/* ---------------- hero ---------------- */}
    <section className="hero"><div className="wrap">
      <div>
        <span className="kicker">Wipe clearance for field-data tablets</span>
        <h1>Wipe a tablet only after its <span className="c-sky">last copy</span> is <span className="c-mint">safe</span>.</h1>
        <p className="lede">Survey teams reset their tablets between rounds, and that reset is when unsent records and photos disappear for good. LastCopy compares every tablet’s original export with the server, byte for byte, and gives the coordinator one answer per device: safe to wipe, recover first or hold, with a certificate that proves why.</p>
        <div className="btns"><a className="btn primary" href="/demo">Open the replay</a><a className="btn" href="#how">See how it works</a></div>
        <div className="hero-stats">
          <div><span>Tablets cleared live</span><b>{run.decisions.length} of {run.decisions.length} correct</b></div>
          <div><span>Blind tablets wrongly cleared</span><b>{B.wrongly_cleared} of {B.tablets.toLocaleString('en')}</b></div>
          <div><span>Judgement model</span><b>Nemotron 3.5</b></div>
        </div>
      </div>
      <HeroFigure decisions={run.decisions}/>
    </div></section>

    {/* ---------------- at a glance ---------------- */}
    <section className="s" style={{paddingTop: 0, borderTop: 0}}><div className="wrap">
      <div className="card glance">
        <div className="glance-title">LastCopy at a glance</div>
        <div className="gh"><span/><span>Field tablets today</span><span>With LastCopy</span></div>
        {[
          ['Before a reset', 'Wipe when the server count looks right', 'One answer per tablet: safe to wipe, recover first or hold'],
          ['Missing photos', 'Invisible: the record shows as received', 'Every file reference compared, byte for byte'],
          ['“Missing” answers', 'The CSV looks short, so people panic or resubmit', 'Raw XML checked; export-only gaps are recognised as safe'],
          ['Proof', 'Someone’s word', 'A hashed certificate of exactly which bytes were compared'],
          ['Explanation', 'Open the XML yourself', 'A plain sentence where every ID and filename is checked against the evidence'],
        ].map(([a, b, c]) => <div className="gr" key={a}><b>{a}</b><span>{b}</span><span>{c}</span></div>)}
      </div>
    </div></section>

    {/* ---------------- problem ---------------- */}
    <section className="s alt" id="problem"><div className="wrap">
      <div className="head"><span className="kicker">The problem</span><h2>Field data went digital. Its last mile still runs on trust.</h2>
        <p className="sub">More than 2 million people use ODK to send over 250 million submissions a year, in 194 countries, including WHO surveillance for polio and cholera. Before every reset, someone has to decide whether a tablet still holds the only copy of something.</p></div>
      <div className="g3">
        <article className="card pcard"><span className="ico"><Icon name="checkc"/></span><h3>“Received” isn’t “complete”</h3><p>A submission can arrive without its photo. The count shows every record as received, while the image survives only on the tablet.</p></article>
        <article className="card pcard"><span className="ico"><Icon name="eyeoff"/></span><h3>The spreadsheet lies by omission</h3><p>Repeated answers drop out of the CSV export, so data looks lost even though the raw XML on the server has all of it.</p></article>
        <article className="card pcard"><span className="ico"><Icon name="alert"/></span><h3>Checking by hand doesn’t scale</h3><p>The only real check is opening XML and media files one by one, for every tablet, at the end of a long field day. So nobody does it.</p></article>
      </div>
      <p className="fig" style={{marginTop: 20}}>Sources: <a href="https://getodk.org/" style={{textDecoration: 'underline'}}>getodk.org</a> · <a href="https://digitalpublicgoods.net/registry/odk.html" style={{textDecoration: 'underline'}}>Digital Public Goods registry</a>.</p>
    </div></section>

    {/* ---------------- how it works ---------------- */}
    <section className="s" id="how"><div className="wrap">
      <div className="head"><span className="kicker">How it works</span><h2>Agents decide where to look. Code decides what’s true.</h2>
        <p className="sub">An investigation is a loop planned by a World Model. Nemotron forms and critiques hypotheses, a deterministic verifier settles them against the original bytes, and a fixed rule clears each tablet.</p></div>
      <div className="g4">
        {[
          ['01', 'search', 'Scout the gaps', 'Four cross-source SQL joins over tablet exports, the server capture and the spreadsheet view find every suspicious record.', 'Zetaris', 'sql'],
          ['02', 'git', 'Argue about it', 'The Investigator turns each suspicion into a testable hypothesis. The Reviewer approves it or sends it back, before anything is fetched.', 'Nemotron', 'model'],
          ['03', 'scale', 'Settle it in bytes', 'The verifier compares original XML and every file slot. A refuted hypothesis is logged as a changed decision.', 'Code', 'code'],
          ['04', 'shield', 'Attack, then clear', 'The gate clears only what the bytes prove. An Adversary then tries to break every clearance, and code must answer each objection or the tablet is held.', 'Code + Nemotron', 'code'],
        ].map(([n, ic, h, p, e, k]) => <article className="card step" key={n}><div className="n"><b>{n}</b><Icon name={ic}/></div><h3>{h}</h3><p>{p}</p><div className="eng"><span className={'badge ' + k}>{e}</span></div></article>)}
      </div>
    </div></section>

    {/* ---------------- three answers ---------------- */}
    <section className="s alt" id="answers"><div className="wrap">
      <div className="head"><span className="kicker">The decisions</span><h2>One tablet, one answer, zero ambiguity.</h2>
        <p className="sub">Each verified record lands in exactly one bucket, and the buckets decide the answer in a fixed order: anything missing wins, then anything uncertain, and only then “safe”.</p></div>
      <div className="card equation">
        <span className="chip">Records on the tablet</span><em>=</em><span className="chip"><span className="dot" data-d="SAFE_TO_WIPE"/>matched</span><em>+</em>
        <span className="chip"><span className="dot" data-d="RECOVER_FIRST"/>only on the tablet</span><em>+</em><span className="chip"><span className="dot" data-d="HOLD"/>needs a person</span>
      </div>
      <div className="g3">
        {[
          ['SAFE_TO_WIPE', 'Every completed record and file is on the server.', 'PRESERVED, EXPORT_VIEW_ONLY', 'Reset the tablet', 'tablet-01 in the live run'],
          ['RECOVER_FIRST', 'The tablet holds the only copy of something.', 'MISSING_SUBMISSION, MISSING_ATTACHMENT', 'Upload the named record or file, then check again', 'tablet-02 and tablet-03'],
          ['HOLD', 'A person must look before anything happens.', 'CONTENT_CONFLICT, UNVERIFIABLE, no export', 'Review the conflict or collect the export', 'tablet-04 and tablet-05'],
        ].map(([d, m, t, a, e]) => <article className="card answer" key={d}>
          <div className="ah"><i className="dec" data-d={d}><span className="dot" data-d={d}/></i><div><b className="dec" data-d={d}>{DECISION_TEXT[d as 'HOLD']}</b><small className="c-mint" style={{color: 'var(--muted)'}}>{d}</small></div></div>
          <div className="kv"><span>Means</span><b>{m}</b></div>
          <div className="kv"><span>Triggered by</span><b className="mono">{t}</b></div>
          <div className="kv"><span>Next step</span><b>{a}</b></div>
          <div className="kv"><span>Example</span><b>{e}</b></div>
        </article>)}
      </div>
    </div></section>

    {/* ---------------- try the gate ---------------- */}
    <section className="s" id="gate"><div className="wrap">
      <GateLab/>
      <p className="fig"><i>Fig. 2</i>The same rule, in the same order, as <span className="mono">lastcopy/agents.py · wipe_gate</span>. Missing data always beats “looks fine”, and a tablet that never exported is never treated as clean.</p>
    </div></section>


    {/* ---------------- blind tests ---------------- */}
    <section className="s alt" id="blind"><div className="wrap">
      <div className="head"><span className="kicker">Blind tests</span><h2>Hidden problems, planted at random. Found every time.</h2>
        <p className="sub">The obvious question is whether the answers were planted. So a generator builds fleets the agents have never seen, with a random hidden condition on every tablet, and the full loop runs: planner, SQL, hypotheses, verifier, gate and Adversary. The truth is revealed only after each decision.</p></div>
      <div className="g2">
        <div className="card live">
          <div className="lh"><div><span className="src">python -m scripts.blind_eval --seeds {B.seeds}</span><h3>Result</h3></div></div>
          <div className="tbl-wrap"><table className="tbl"><tbody>
            <tr><td>Fleets decided entirely correctly</td><td className="mono">{B.fleets_correct} / {B.fleets}</td></tr>
            <tr><td>Tablets decided correctly</td><td className="mono">{B.tablets_correct.toLocaleString('en')} / {B.tablets.toLocaleString('en')}</td></tr>
            <tr><td><b>Tablets wrongly cleared to wipe</b></td><td className="mono c-mint"><b>{B.wrongly_cleared}</b></td></tr>
            {Object.entries(B.by_truth).map(([k, v]) => <tr key={k}><td>Truth: <span className="dec" data-d={k}>{DECISION_TEXT[k as 'HOLD']}</span></td><td className="mono">{v}</td></tr>)}
          </tbody></table></div>
          <div className="lf">Sample mode: the written offline policy fills the model roles; everything else is the production code. Full results with every planted condition: <a href={`${REPO}/blob/main/eval/blind-benchmark.json`} style={{textDecoration: 'underline'}}>eval/blind-benchmark.json</a>.</div>
        </div>
        <div className="card live">
          <div className="lh"><div><span className="src">by hidden condition</span><h3>Every kind of loss, caught</h3></div></div>
          <div className="tbl-wrap"><table className="tbl"><tbody>
            {Object.entries(B.by_planted_condition).map(([k, v]) => <tr key={k}><td>{COND[k] || k}</td><td className="mono">{v}</td></tr>)}
          </tbody></table></div>
          <div className="lf">A tablet can carry several conditions at once; the strongest one decides. A tablet that never exported is always held, never guessed.</div>
        </div>
      </div>
    </div></section>

    {/* ---------------- who it's for ---------------- */}
    <section className="s alt"><div className="wrap">
      <div className="head"><span className="kicker">Who it’s for</span><h2>Different people need different parts of the answer.</h2></div>
      <div className="g3">
        {[
          ['tablet', 'Field coordinators', 'Reset twenty tablets before tomorrow’s round without gambling on any of them.', 'A list of tablets to wipe now, and the exact file to upload from each of the others.'],
          ['table', 'Data managers', 'Stop chasing “missing” answers that are really just artefacts of the export view.', 'Raw-XML checks that separate export gaps from real loss, with SQL and hashes to audit.'],
          ['chart', 'Programme & M&E leads', 'Show funders and ethics boards that nothing collected was silently lost.', 'A hashed certificate per tablet, and a trace of how every decision was reached.'],
        ].map(([ic, h, p, w]) => <article className="card persona" key={h}><span className="ico"><Icon name={ic}/></span><h3>{h}</h3><p>{p}</p><div className="with"><span>With LastCopy</span><p>{w}</p></div></article>)}
      </div>
    </div></section>

    {/* ---------------- under the hood ---------------- */}
    <section className="s" id="hood"><div className="wrap">
      <div className="head"><span className="kicker">Under the hood</span><h2>Ten roles, one planner, and a rule no model can touch.</h2>
        <p className="sub">The Meterless World Model holds the investigation as a graph and picks each next step from its state. Python only runs the step it picks.</p></div>
      <div className="hood">
        <div className="card">
          <div className="list-h">Agents and what runs them</div>
          <div className="ilist">
            {[
              ['World Model planner', 'Selects the next action from graph state: triage, classify, review, fetch, evaluate, remedy, decide, explain.', 'Meterless', 'plan'],
              ['Scout', 'Four cross-source joins that find suspicious records.', 'Zetaris', 'sql'],
              ['Investigator', 'Proposes a hypothesis and the evidence that would test it.', 'Nemotron', 'model'],
              ['Reviewer', 'Approves, revises or rejects. A code guard enforces it.', 'Nemotron', 'model'],
              ['Evidence fetcher', 'Resolves exact source objects and re-checks every hash.', 'Zetaris', 'sql'],
              ['Verifier', 'Compares original bytes. The only source of verdicts.', 'Code', 'code'],
              ['Remediation advisor', 'Chooses only among the actions code permits.', 'Nemotron', 'model'],
              ['Wipe gate', 'Seven criteria must all hold; one decision and a hashed certificate per tablet.', 'Code', 'code'],
              ['Adversary', 'Tries to break every clearance; each objection is re-checked from the raw tables.', 'Nemotron', 'model'],
              ['Explainer', 'Plain sentence; every ID and filename checked.', 'Nemotron', 'model'],
            ].map(([n, p, b, k]) => <div className="it" key={n}><b>{n}</b><p>{p}</p><span className={'badge ' + k}>{b}</span></div>)}
          </div>
        </div>
        <div style={{display: 'grid', gap: 16}}>
          <div className="card code">
            <div className="ch"><span>Wipe gate</span><span>lastcopy/agents.py</span></div>
            <pre><span className="c"># decided by code from verified findings only</span>{'\n'}<span className="k">if</span> device <span className="k">in</span> missing_devices:{'\n'}    decision = <span className="s">'HOLD'</span>          <span className="c"># never exported</span>{'\n'}<span className="k">elif</span> <span className="f">any</span>(v <span className="k">in</span> MISSING <span className="k">for</span> v <span className="k">in</span> verdicts):{'\n'}    decision = <span className="s">'RECOVER_FIRST'</span> <span className="c"># only copy is here</span>{'\n'}<span className="k">elif</span> <span className="f">any</span>(v <span className="k">in</span> UNCERTAIN <span className="k">for</span> v <span className="k">in</span> verdicts):{'\n'}    decision = <span className="s">'HOLD'</span>          <span className="c"># a person decides</span>{'\n'}<span className="k">elif not</span> findings:{'\n'}    decision = <span className="s">'HOLD'</span>{'\n'}<span className="k">else</span>:{'\n'}    decision = <span className="s">'SAFE_TO_WIPE'</span></pre>
            <div className="cf">Simplified. The certificate records the rule version, both archive hashes and every finding.</div>
          </div>
          <div className="props">
            {[
              ['lock', 'Models can’t make a tablet look safe', 'Verdicts come only from the byte comparison; the gate never reads model output.'],
              ['list', 'Schema-bound, with labelled fallbacks', 'Strict JSON from every model call; one repair attempt, then a fallback that the trace names as one.'],
              ['clock', 'Bounded by design', '12 steps, 2 critique rounds, 10 model calls, 300 seconds, or a controlled failure.'],
            ].map(([ic, b, p]) => <div className="card prop" key={b}><span className="ico"><Icon name={ic}/></span><b>{b}</b><p>{p}</p></div>)}
          </div>
        </div>
      </div>
    </div></section>

    {/* ---------------- live run ---------------- */}
    <section className="s alt" id="live"><div className="wrap">
      <div className="head"><span className="kicker">Live connected run</span><h2>Run live through Zetaris and Nemotron, not mocked.</h2>
        <p className="sub">On 27 October the five-tablet fleet ran end to end: evidence through a local Zetaris install, judgement through NVIDIA Nemotron via Meterless Nightshift. The decisions match the keyless sample run, because code makes them.</p></div>
      <div className="card live">
        <div className="lh"><div><span className="src">Captured 27 Oct 2026 · connected mode</span><h3>What each tablet got</h3></div><a href={`${REPO}/blob/main/output_examples/live_connected_fleet.json`}>Verify on GitHub ↗</a></div>
        <div className="tbl-wrap"><table className="tbl">
          <thead><tr><th>Tablet</th><th>Decision</th><th>Explanation written by Nemotron, citations checked</th><th>Certificate</th></tr></thead>
          <tbody>{run.decisions.map(d => <tr key={d.device_id}>
            <td className="mono">{d.device_id}</td>
            <td><span className="dec" data-d={d.decision} style={{display: 'inline-flex', alignItems: 'center', gap: 8, whiteSpace: 'nowrap'}}><span className="dot" data-d={d.decision}/>{DECISION_TEXT[d.decision]}</span></td>
            <td className="why">{strip(d.explanation.text)}</td>
            <td className="m mono">{d.certificate_sha256.slice(0, 12)}…</td>
          </tr>)}</tbody>
        </table></div>
        <div className="lf">{zetaris} Zetaris queries · {modelCalls} Nemotron calls (<span className="mono">{run.engines.models[0]}</span>) · {run.critique_rounds} critique rounds · {fallbacks} fallbacks · the Reviewer sent every hypothesis back once before testing.</div>
      </div>
      <div className="g3" style={{marginTop: 16}}>
        <article className="card sponsor"><span className="kicker">Evidence layer</span><h3>Zetaris</h3><p>Tablet exports, server capture, spreadsheet view and file references are registered as tables. The Scout’s joins over them are the only way the agents learn where to look.</p><div className="where">agents.py · evidence_sql</div><div className="proof">Sample mode runs the identical SQL on SQLite and says so on every trace line.</div></article>
        <article className="card sponsor"><span className="kicker">Planner</span><h3>Meterless World Model</h3><p>Suspicions, hypothesis revisions, findings, remedies and decisions live in its graph, and it chooses every next action from that state.</p><div className="where">bridge/investigation-world.ts</div><div className="proof">Pinned reference · conformance 8/8.</div></article>
        <article className="card sponsor"><span className="kicker">Judgement</span><h3>Nemotron via Nightshift</h3><p>Investigator, Reviewer, Advisor, Adversary and Explainer run on NVIDIA Nemotron through Meterless Nightshift. Every trace line records the model that actually answered.</p><div className="where">connected.py · Nightshift.respond</div><div className="proof">If the provider fails, the run says so. Nothing is fabricated.</div></article>
      </div>
    </div></section>

    {/* ---------------- roadmap ---------------- */}
    <section className="s" id="roadmap"><div className="wrap">
      <div className="head"><span className="kicker">Roadmap</span><h2>From a hackathon gate to the step before every reset.</h2></div>
      <div className="g3">
        {[
          ['Shipped', 'Now', [['Five-tablet investigation with per-device decisions and certificates', 1], ['World Model planner, Reviewer loop and code guards', 1], ['Live run through Zetaris and Nemotron via Nightshift', 1], ['Keyless Sample mode, JSONL traces and 303 tests', 1], ['Reviewed recovery into a synthetic ODK test project', 1], ['Printable clearance sheet and an independent certificate verifier', 1], ['Adversary agent and a blind benchmark of 500 random fleets', 1]]],
          ['Next', 'Pilot', [['Pull exports straight from Collect over USB', 0], ['Read-only connection to a team’s ODK Central', 0], ['Batch mode for whole cohorts of tablets', 0]]],
          ['Later', 'Scale', [['KoboToolbox and other ODK-compatible servers', 0], ['Encrypted-form support with on-device keys', 0], ['Offline coordinator app for low-connectivity sites', 0], ['Independent security review', 0]]],
        ].map(([h, k, items]) => <article className="card road" key={h as string}><div className="rk"><span className="kicker">{k as string}</span></div><h3>{h as string}</h3><ul>
          {(items as [string, number][]).map(([t, done]) => <li key={t} className={done ? '' : 'todo'}><Icon name={done ? 'checkc' : 'circle'}/>{t}</li>)}</ul></article>)}
      </div>
    </div></section>

    {/* ---------------- faq ---------------- */}
    <section className="s alt" id="faq"><div className="wrap">
      <div className="head center" style={{textAlign: 'center'}}><span className="kicker">FAQ</span><h2>Questions, answered.</h2></div>
      <div className="faq">
        {[
          ['Can the AI ever make a tablet look safe?', 'No. Verdicts come only from the deterministic byte comparison, and the wipe gate reads only those verdicts. Models choose where to look, critique hypotheses, pick among permitted remedies and write the explanation, and that explanation is checked token by token against the evidence.'],
          ['What exactly does “safe to wipe” prove?', 'That every completed record and every referenced file from that tablet’s export was found on the server with identical bytes. The certificate names the rule version, both archive hashes and every finding. It does not prove the answers are true, and it only covers the exports you supplied.'],
          ['Why is a short spreadsheet considered safe?', 'Because the CSV export can leave out repeated answers that the server actually holds. LastCopy checks the raw server XML; when every answer is there, the gap is in the view, not in the data.'],
          ['Does it run without keys or internet?', 'Yes. python run.py runs the full loop in Sample mode in a few seconds: planner, SQL on SQLite, verifier, gate and checks. Only the model roles are replaced by a written policy, and every trace line says so.'],
          ['Does LastCopy modify the original exports?', 'Never. Archives are read-only and sealed with SHA-256. Live recovery writes only to a dedicated synthetic ODK Central test project.'],
          ['Which formats are supported?', 'ODK Collect v2026.3.5 exports against ODK Central v2026.3.1. Encrypted forms and KoboToolbox are on the roadmap, not claimed today.'],
        ].map(([q, a]) => <details key={q}><summary>{q}</summary><p>{a}</p></details>)}
      </div>
    </div></section>

    {/* ---------------- final ---------------- */}
    <section className="s"><div className="wrap">
      <div className="card final">
        <h2>Check your first fleet in ten seconds.</h2>
        <p>No keys, no network. Clone the repo and run one command, or step through the live investigation in your browser.</p>
        <div className="btns"><a className="btn primary" href="/demo">Open the replay</a><a className="btn" href={REPO}>Read the README</a></div>
        <pre className="inset term"><span className="d">$</span> python run.py{'\n'}<span className="d">  tablet-01  </span><span className="g">SAFE_TO_WIPE </span>  raw XML holds every answer{'\n'}<span className="d">  tablet-02  </span><span className="y">RECOVER_FIRST</span>  b.bin is not on the server{'\n'}<span className="d">  tablet-04  </span><span className="r">HOLD         </span>  server answers differ; a person must choose</pre>
      </div>
    </div></section>
  </main>;
}
