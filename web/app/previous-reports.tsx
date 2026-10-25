'use client';
import Link from 'next/link';
import {useState} from 'react';
import {enc,type Recent} from '../lib/client';
import {Icon} from './icons';
function summary(r:Recent){
  if(r.status.state==='completed'){
    if(r.attention_count)return `${r.attention_count} ${r.attention_count===1?'record needs':'records need'} attention`;
    return r.coverage_complete?'Checked copies match':'Copies match; source coverage is incomplete';
  }
  return {queued:'Waiting to start',running:'Checking records…',failed:'Check could not finish',cancelled:'Check cancelled',interrupted:'Check interrupted'}[r.status.state]??'No final result yet';
}
function Cards({items}:{items:Recent[]}){return <ul className="saved-list report-cards">{items.map(r=><li key={r.run_id} data-attention={!!r.attention_count}><Link href={'/runs/'+enc(r.run_id)}><div className="report-card-top"><span>{r.mode==='connected'?(r.synthetic_source?'Connected · test-record server readback':'Connected · server readback'):r.mode==='replay'?'Replay · saved server export':'Sample · example records'}</span>{r.checked_at&&<time dateTime={r.checked_at}>{new Date(r.checked_at).toLocaleString('en-GB',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'})}</time>}</div><h3>{r.title}</h3><p className="report-card-result"><Icon name={r.attention_count||!r.coverage_complete?'search':'check'} size={17}/>{summary(r)}</p><div className="report-card-bottom"><span>{r.record_count===null?'No completed comparison':`${r.record_count} ${r.record_count===1?'record':'records'} checked`}</span><span>Open report <Icon name="arrow" size={16}/></span></div></Link></li>)}</ul>;}
export default function PreviousReports({recent}:{recent:Recent[]}){
  const [all,setAll]=useState(false),records=recent.filter(r=>r.mode!=='sample'&&!r.synthetic_source),examples=recent.filter(r=>r.mode==='sample'||r.synthetic_source);
  return <section id="saved-checks" className="saved-checks"><div className="section-heading"><div><p className="eyebrow">PICK UP WHERE YOU LEFT OFF</p><h2>Previous reports</h2></div><p>Open a report to see what was checked and what still needs attention.</p></div>
    {records.length?<><Cards items={all?records:records.slice(0,6)}/>{records.length>6&&<button className="quiet compact" onClick={()=>setAll(!all)}>{all?'Show fewer reports':`Show all ${records.length} recent reports`}</button>}</>:<div className="workspace-empty"><Icon name="layers" size={36}/><div><h3>No reports for your records yet.</h3><p>Add a device export above to check it against the connected server.</p></div></div>}
    {examples.length>0&&<details className="example-history"><summary>Test and example reports ({examples.length})</summary><p>These used synthetic test records. Connected checks here read the actual test server; Sample checks use offline examples. Your own reports stay separate.</p><Cards items={examples}/></details>}
  </section>;
}
