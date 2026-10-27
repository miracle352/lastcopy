import Console,{type RunEntry} from './console';
import {REPO} from '../chrome';
import live from '../../../public/runs/live-fleet.json';
import e1 from '../../../public/runs/example-1.json';
import e2 from '../../../public/runs/example-2.json';
import e3 from '../../../public/runs/example-3.json';
import e4 from '../../../public/runs/example-4.json';
import type {RunDoc} from '../../../lib/run-types';

export const metadata = {title: 'LastCopy · Investigation replay'};

const runs: RunEntry[] = [
  {id: 'live', kicker: 'Live · Zetaris + Nemotron', title: 'Five tablets, connected run (27 Oct)', doc: live as unknown as RunDoc},
  {id: 'fleet', kicker: 'Example 1 · five tablets', title: 'Which tablets are safe to wipe?', doc: e1 as unknown as RunDoc},
  {id: 'spreadsheet', kicker: 'Example 2 · export', title: 'The spreadsheet is missing answers', doc: e2 as unknown as RunDoc},
  {id: 'photo', kicker: 'Example 3 · media', title: 'Everything shows as received', doc: e3 as unknown as RunDoc},
  {id: 'stranded', kicker: 'Example 4 · stuck records', title: 'The count matches', doc: e4 as unknown as RunDoc},
];

export default function Demo() {
  return <main id="main" className="wrap" style={{paddingBottom: 100}}>
    <div className="console-top">
      <span className="kicker">Investigation replay</span>
      <h1>Watch the agents <span className="sky">argue</span>, then let the <span className="mint">bytes</span> decide.</h1>
      <p className="lead">These are real runs exported from <span className="mono">python run.py</span>. Step through the World Model’s plan and you can see suspicions become hypotheses, the Reviewer push back, the raw bytes overturn a guess, and the gate clear each tablet.</p>
    </div>
    <Console runs={runs}/>
    <p className="fig" style={{marginTop: 28}}><i>Source</i>Each run’s full JSON and its guideline-format trace are in <a href={`${REPO}/tree/main/output_examples`} style={{textDecoration: 'underline'}}>output_examples/</a> and <a href={`${REPO}/tree/main/logs`} style={{textDecoration: 'underline'}}>logs/</a>.</p>
  </main>;
}
