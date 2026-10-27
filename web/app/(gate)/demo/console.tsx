'use client';
import {useEffect,useMemo,useState} from 'react';
import {DECISION_TEXT} from '../../../lib/wipe-gate';
import type {RunDoc,RunEvent} from '../../../lib/run-types';

export type RunEntry={id:string;kicker:string;title:string;doc:RunDoc};

const ACTION_TEXT:Record<string,string>={triage:'triage',classify:'classify',review:'review',fetch_evidence:'fetch_evidence',evaluate:'evaluate',remedy:'remedy',decide:'decide',explain:'explain',done:'done'};
const CODE=new Set(['Verifier','Wipe gate','Code guard','Evidence fetcher','Orchestrator']);

function steps(events:RunEvent[]){
  const out:{action:string;why:string;focus:string[];lines:RunEvent[]}[]=[];
  for(const e of events){
    if(e.kind==='graph_read'){out.push({action:e.next_action||'?',why:e.why||'',focus:e.focus||[],lines:[]});continue;}
    if(!out.length)continue;
    if(e.kind==='agent'&&e.agent_name==='World Model planner')continue;
    if(['agent','fallback','decision_changed','query','model','provider_failure'].includes(e.kind))out[out.length-1].lines.push(e);
  }
  return out;
}

function engineOf(e:RunEvent,doc:RunDoc){
  if(e.kind==='query')return {cls:'sql',text:e.provider==='zetaris'?'Zetaris SQL':'local SQL'};
  if(e.kind==='model')return {cls:'model',text:e.actual_serving_model||e.provider||'model'};
  if(CODE.has(e.agent_name||''))return {cls:'code',text:'code'};
  if(e.agent_name==='Scout')return {cls:'sql',text:doc.engines.evidence.includes('zetaris')?'Zetaris':'local SQL'};
  return {cls:'model',text:e.model||(doc.mode==='sample'?'offline policy':'model')};
}

const cap=(s:string)=>s.charAt(0).toUpperCase()+s.slice(1);
const fmt=(v:unknown)=>Array.isArray(v)?v.join(', '):String(v);

function Line({e,doc}:{e:RunEvent;doc:RunDoc}){
  const eng=engineOf(e,doc);
  if(e.kind==='decision_changed')return <div className="line" data-kind="decision_changed"><div className="who">Decision changed<small>raw evidence wins</small></div>
    <div className="what">{e.note||'A hypothesis was refuted by the verified bytes, so the plan changed.'}<div className="tags">{e.hypothesis&&<span className="tag">{e.hypothesis}</span>}<span className="tag model">guess: {fmt(e.before)}</span><span className="tag code">bytes say: {fmt(e.after)}</span></div></div></div>;
  if(e.kind==='fallback')return <div className="line" data-kind="fallback"><div className="who">Fallback<small>labelled, never silent</small></div><div className="what">{e.reason||e.note}</div></div>;
  if(e.kind==='query')return <div className="line" data-kind="query"><div className="who">SQL<small>{e.query_kind}</small></div><div className="what">{e.row_count} row(s)<div className="tags"><span className={'tag '+eng.cls}>{eng.text}</span>{e.engine&&<span className="tag">{e.engine}</span>}</div></div></div>;
  if(e.kind==='model')return <div className="line" data-kind="model"><div className="who">Model call<small>{e.role}{e.attempt&&e.attempt>1?` · attempt ${e.attempt}`:''}</small></div>
    <div className="what">{e.valid?'schema-valid JSON':`rejected: ${(e.errors||[]).join('; ')}`}<div className="tags"><span className="tag model">{e.actual_serving_model||e.provider}</span>{e.provider&&e.actual_serving_model&&<span className="tag">via {e.provider}</span>}</div></div></div>;
  return <div className="line" data-kind={e.kind}><div className="who">{e.agent_name}<small>{e.action}</small></div>
    <div className="what">{e.output_summary}{e.target_agent&&<span className="arrow"> → {e.target_agent}</span>}
      <div className="tags"><span className={'tag '+eng.cls}>{eng.text}</span>{e.retry_count?<span className="tag">retry {e.retry_count}</span>:null}{e.fallback?<span className="tag">fallback</span>:null}</div></div></div>;
}

export default function Console({runs}:{runs:RunEntry[]}){
  const [id,setId]=useState(runs[0].id);
  const entry=runs.find(r=>r.id===id)||runs[0];
  const doc=entry.doc;
  const plan=useMemo(()=>steps(doc.events),[doc]);
  const [at,setAt]=useState(0);
  const [playing,setPlaying]=useState(false);
  const [showModel,setShowModel]=useState(false);
  useEffect(()=>{setAt(0);setPlaying(false);},[id]);
  useEffect(()=>{
    if(!playing)return;
    if(at>=plan.length-1){setPlaying(false);return;}
    const t=setTimeout(()=>setAt(a=>a+1),1500);return()=>clearTimeout(t);
  },[playing,at,plan.length]);
  const cur=plan[at];
  const lines=(cur?.lines||[]).filter(e=>showModel||(e.kind!=='model'&&e.kind!=='query'));
  const sample=doc.mode==='sample';
  return <>
    <div className="tabs" role="group" aria-label="Choose an investigation">
      {runs.map(r=><button type="button" key={r.id} aria-pressed={r.id===id} onClick={()=>setId(r.id)}><small>{r.kicker}</small><span>{r.title}</span></button>)}
    </div>
    <div className="question"><small>The coordinator asks</small>{doc.question||doc.label}</div>
    <div className="engines">
      <span className="pill">{sample?'Sample mode':doc.mode==='connected'?'Connected (live capture)':doc.mode}</span>
      <span className="pill">planner: World Model</span>
      <span className="pill">evidence: {doc.engines.evidence.join(', ')}</span>
      <span className="pill">judgement: {doc.engines.models.join(', ')}</span>
      <span className="pill">verdicts: code</span>
      <span className="pill">{doc.steps} steps · {doc.provider_calls} model calls · {doc.critique_rounds} critique</span>
    </div>
    {sample&&<p className="fig" style={{marginTop:10}}>In Sample mode, a written offline policy fills the model roles and local SQLite runs the same SQL. The planner, verifier, gate and checks all run for real. Every line is labelled with what actually answered.</p>}

    <div className="grid2">
      <div className="card plan">
        <div className="card-head"><span>World Model plan</span><span className="mono">{at+1}/{plan.length}</span></div>
        <ol>{plan.map((s,i)=><li key={i}><button type="button" aria-current={i===at?'step':undefined} onClick={()=>{setAt(i);setPlaying(false);}}>
          <span className="num">{String(i+1).padStart(2,'0')}</span>
          <span><span className="act" data-future={i>at}>{ACTION_TEXT[s.action]||s.action}</span><span className="why" style={{display:'block'}}>{s.why}</span></span>
        </button></li>)}</ol>
        <div className="controls">
          <button type="button" onClick={()=>{if(at>=plan.length-1)setAt(0);setPlaying(p=>!p);}}>{playing?'❚❚ Pause':'▶ Play'}</button>
          <button type="button" onClick={()=>setAt(a=>Math.max(0,a-1))} aria-label="Previous step">←</button>
          <button type="button" onClick={()=>setAt(a=>Math.min(plan.length-1,a+1))} aria-label="Next step">→</button>
          <span className="prog" aria-hidden="true"><i style={{width:`${((at+1)/plan.length)*100}%`}}/></span>
        </div>
      </div>
      <div className="card">
        <div className="card-head"><span>Step {at+1}: <b className="mono" style={{color:'var(--sky)'}}>{cur?.action}</b>{cur?.focus?.length?<span className="mono"> · focus {cur.focus.join(', ')}</span>:null}</span>
          <label style={{display:'flex',gap:8,alignItems:'center',cursor:'pointer'}}><input type="checkbox" checked={showModel} onChange={e=>setShowModel(e.target.checked)}/> show model &amp; SQL calls</label></div>
        <div className="trace" aria-live="polite">
          {cur?.why&&<div className="line"><div className="who" style={{color:'var(--sky)'}}>World Model<small>select_next_action</small></div><div className="what">{cur.why}<div className="tags"><span className="tag">Meterless World Model</span></div></div></div>}
          {lines.map((e,i)=><Line key={`${at}-${e.seq}-${i}`} e={e} doc={doc}/>)}
          {!lines.length&&at===plan.length-1&&<div className="empty">Done. Every device has an explained decision that code made.</div>}
        </div>
      </div>
    </div>

    <div className="h3row"><h2>Outcome</h2><p>Decisions and certificates from <span className="mono">{doc.run_id}</span></p></div>
    <div className="decisions">{doc.decisions.map(d=><article key={d.device_id} className="card dcard">
      <div className="l"><span className="dev">{d.device_id}</span><span className="verdict" data-d={d.decision}>{DECISION_TEXT[d.decision]}</span></div>
      <div className="r"><p className="expl">{cap(d.explanation.text.replace(/^(SAFE_TO_WIPE|RECOVER_FIRST|HOLD):\s*/,''))}</p>
        <div className="meta"><span className="tag">written by {d.explanation.written_by}</span>{d.explanation.citations_checked&&<span className="tag code">citations checked</span>}
          {Object.entries(d.counts).map(([k,v])=><span key={k} className="tag">{k} × {v}</span>)}</div>
        <details><summary>Certificate <span className="mono">{d.certificate_sha256.slice(0,16)}…</span></summary>
          <ul><li>rule <span className="mono">{d.certificate.rule}</span></li><li>device export sha256 <span className="mono">{d.certificate.device_export_sha256??'none received'}</span></li>
            <li>server capture sha256 <span className="mono">{d.certificate.server_capture_sha256}</span></li>
            {d.records.map(r=><li key={r.finding_id}>{r.finding_id}: <span className="mono">{r.verdict}</span> · {r.version_id}{r.media_filenames.length?` · ${r.media_filenames.join(', ')}`:''}</li>)}</ul></details>
      </div>
    </article>)}</div>

    <div className="h3row"><h2>The Scout’s SQL</h2><p>Code-owned queries, never written by a model</p></div>
    <div className="card sql">{doc.queries.map(q=><details key={q.query_id}><summary><span className="mono">{q.kind}</span><span>{q.rows} rows · {q.provider} · {q.elapsed_ms} ms</span></summary><pre>{q.sql}</pre></details>)}</div>
  </>;
}
