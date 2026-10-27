import exportCase from '../../../public/verification/sponsor-export-review.json';
import conflictCase from '../../../public/verification/sponsor-conflict.json';

type Capture={queries:{receipt:{query_kind:string;query_id:string;row_count:number;sql:string;rows_sha256:string};rows:Record<string,unknown>[]}[];world_revisions:{type:string;revision:number;status?:string;next_action?:string;evidence:string[];id:string}[];events:{kind:string;seq:number;role?:string;action?:string;actual_serving_model?:string}[]};
const cases:Record<string,Capture>={'export-review':exportCase,'conflict':conflictCase};

export default function CapturedProof({name}:{name:string}){
  const capture=cases[name];if(!capture)return null;
  return <details className="captured-proof"><summary>Inspect the actual queries, model actions and hypothesis history</summary>
    <p><strong>Replay evidence.</strong> These are rows from the saved connected run. Opening this view makes no provider calls.</p>
    <section aria-label="Captured Zetaris queries"><h4>Zetaris returned these rows</h4>{capture.queries.map(q=><details key={q.receipt.query_id}><summary>{q.receipt.query_kind} · {q.receipt.row_count} rows</summary><p>Query <code>{q.receipt.query_id}</code></p><pre tabIndex={0} aria-label="Actual scoped SQL">{q.receipt.sql}</pre><p>First returned rows; the download contains every row.</p><pre tabIndex={0} aria-label="Actual returned evidence rows">{JSON.stringify(q.rows.slice(0,2),null,2)}</pre><p>Rows SHA-256 <code>{q.receipt.rows_sha256}</code></p></details>)}</section>
    <section aria-label="Captured Nightshift model actions"><h4>Nightshift investigator and reviewer</h4><ol>{capture.events.filter(e=>e.kind==='model').map(e=><li key={e.seq}><strong>{e.role}</strong> → {e.action}<br/><small>{e.actual_serving_model}</small></li>)}</ol></section>
    <section aria-label="Captured World Model revisions"><h4>World Model kept the earlier evidence</h4><ol>{capture.world_revisions.filter(r=>r.type==='hypothesis').map(r=><li key={r.id}>Revision {r.revision}: <strong>{r.status}</strong> → {r.next_action}<br/>{r.evidence.length} evidence references retained<details><summary>Evidence identities</summary><pre tabIndex={0}>{r.evidence.join('\n')}</pre></details></li>)}</ol></section>
  </details>;
}
