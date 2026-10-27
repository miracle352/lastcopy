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
  {id: 'live', kicker: 'Live · 27 Oct', title: 'Five tablets through Zetaris and Nemotron', doc: live as unknown as RunDoc, live: true},
  {id: 'fleet', kicker: 'Example 1 · fleet', title: 'Which tablets are safe to wipe?', doc: e1 as unknown as RunDoc},
  {id: 'spreadsheet', kicker: 'Example 2 · export', title: 'The spreadsheet is missing answers', doc: e2 as unknown as RunDoc},
  {id: 'photo', kicker: 'Example 3 · media', title: 'Everything shows as received', doc: e3 as unknown as RunDoc},
  {id: 'stranded', kicker: 'Example 4 · stuck', title: 'The count matches', doc: e4 as unknown as RunDoc},
];

export default function Demo() {
  return <main id="main">
    <div className="page-head"><div className="wrap">
      <span className="kicker">Investigation replay</span>
      <h1>Watch the agents <span className="c-sky">argue</span>, and the bytes <span className="c-mint">settle it</span>.</h1>
      <p className="lede">Each of these is a real run, exported straight from LastCopy. Step through the World Model’s plan to see suspicions become hypotheses, the Reviewer push back, raw evidence overturn a guess, and the gate clear every tablet.</p>
    </div></div>
    <div className="wrap" style={{paddingBottom: 120}}>
      <Console runs={runs}/>
      <p className="fig" style={{marginTop: 28}}><i>Source</i>Full JSON and guideline-format traces are in <a href={`${REPO}/tree/main/output_examples`} style={{textDecoration: 'underline'}}>output_examples/</a> and <a href={`${REPO}/tree/main/logs`} style={{textDecoration: 'underline'}}>logs/</a>.</p>
    </div>
  </main>;
}
