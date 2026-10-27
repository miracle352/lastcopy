'use client';
import {useEffect,useMemo,useState} from 'react';
import {DECISION_TEXT,criteriaFor} from '../../../lib/wipe-gate';
import type {RunDoc,RunEvent} from '../../../lib/run-types';

export type RunEntry={id:string;kicker:string;title:string;doc:RunDoc;live?:boolean};

const CODE=new Set(['Verifier','Wipe gate','Code guard','Evidence fetcher','Orchestrator']);
const cap=(s:string)=>s.charAt(0).toUpperCase()+s.slice(1);
const fmt=(v:unknown)=>Array.isArray(v)?v.join(', '):String(v);

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

function badge(e:RunEvent,doc:RunDoc):[string,string]{
  const sql=doc.engines.evidence.includes('zetaris')?'Zetaris':'local SQL';
  if(e.kind==='query'||e.agent_name==='Scout')return ['sql',e.provider==='local-sql'?'local SQL':sql];
  if(e.kind==='model')return ['model',e.actual_serving_model||e.provider||'model'];
  if(CODE.has(e.agent_name||''))return ['code','code'];
  return ['model',e.model||(doc.mode==='sample'?'offline policy':'model')];
}

function Line({e,doc}:{e:RunEvent;doc:RunDoc}){
  if(e.kind==='decision_changed')return <div className="ln" data-kind="decision_changed"><div className="who"><b>Decision changed</b><small>raw bytes overrule a guess</small></div>
    <div className="what">{e.note||'A hypothesis was refuted by the verified bytes.'}<div className="tags">{e.hypothesis&&<span className="badge">{e.hypothesis}</span>}<span className="badge model">guessed: {fmt(e.before)}</span><span className="badge code">bytes say: {fmt(e.after)}</span></div></div></div>;
  if(e.kind==='fallback')return <div className="ln" data-kind="fallback"><div className="who"><b>Fallback</b><small>labelled, never silent</small></div><div className="what">{e.reason||e.note}</div></div>;
  const [k,t]=badge(e,doc);
  if(e.kind==='query')return <div className="ln"><div className="who"><b>SQL query</b><small>{e.query_kind}</small></div><div className="what">{e.row_count} row(s)<div className="tags"><span className={'badge '+k}>{t}</span></div></div></div>;
  if(e.kind==='model')return <div className="ln"><div className="who"><b>Model call</b><small>{e.role}{e.attempt&&e.attempt>1?` · attempt ${e.attempt}`:''}</small></div>
    <div className="what">{e.valid?'Schema-valid JSON':`Rejected: ${(e.errors||[]).join('; ')}`}<div className="tags"><span className={'badge '+k}>{t}</span>{e.provider&&e.actual_serving_model&&<span className="badge">via {e.provider}</span>}</div></div></div>;
  return <div className="ln"><div className="who"><b>{e.agent_name}</b><small>{e.action}</small></div>
    <div className="what">{e.output_summary}{e.target_agent&&<span className="to"> → {e.target_agent}</span>}
      <div className="tags"><span className={'badge '+k}>{t}</span>{e.retry_count?<span className="badge">retry {e.retry_count}</span>:null}{e.fallback?<span className="badge">fallback</span>:null}</div></div></div>;
}

export default function Console({runs}:{runs:RunEntry[]}){
  const [id,setId]=useState(runs[0].id);
  const entry=runs.find(r=>r.id===id)||runs[0];
  const doc=entry.doc;
  const plan=useMemo(()=>steps(doc.events),[doc]);
  const [at,setAt]=useState(0);
  const [playing,setPlaying]=useState(false);
  const [calls,setCalls]=useState(false);
  useEffect(()=>{setAt(0);setPlaying(false);},[id]);
  useEffect(()=>{
    if(!playing)return;
    if(at>=plan.length-1){setPlaying(false);return;}
    const t=setTimeout(()=>setAt(a=>a+1),1600);return()=>clearTimeout(t);
  },[playing,at,plan.length]);
  const cur=plan[at];
  const lines=(cur?.lines||[]).filter(e=>calls||(e.kind!=='model'&&e.kind!=='query'));
  const sample=doc.mode==='sample';
  return <>
    <div className="runs" role="group" aria-label="Choose an investigation">
      {runs.map(r=><button type="button" key={r.id} aria-pressed={r.id===id} onClick={()=>setId(r.id)}><small>{r.live&&<i className="lv"/>}{r.kicker}</small><span>{r.title}</span></button>)}
    </div>
    <div className="card ask">
      <div><small>The coordinator asks</small><p>{doc.question||doc.label}</p></div>
      <div className="meta">
        <span className={'badge '+(sample?'':'code')}>{sample?'Sample mode':'Connected · live'}</span>
        <span className="badge plan">World Model</span>
        <span className="badge sql">{doc.engines.evidence.includes('zetaris')?'Zetaris':'local SQL'}</span>
        <span className="badge model">{doc.engines.models.join(', ')}</span>
        <span className="badge">{doc.steps} steps · {doc.provider_calls} model calls · {doc.critique_rounds} critique</span>
      </div>
    </div>
    <p className="note">{sample?'Sample mode: a written offline policy stands in for the model roles and SQLite runs the same SQL. The planner, verifier, gate and checks are real, and every line names what actually answered.':'Connected run captured on 27 Oct 2026: every query answered by Zetaris and every judgement call by NVIDIA Nemotron through Meterless Nightshift, with no fallbacks.'}</p>

    <div className="console">
      <div className="card plan">
        <div className="panel-h"><span>World Model plan</span><span className="r">{at+1} / {plan.length}</span></div>
        <ol>{plan.map((s,i)=><li key={i}><button type="button" aria-current={i===at?'step':undefined} onClick={()=>{setAt(i);setPlaying(false);}}>
          <span className="num">{String(i+1).padStart(2,'0')}</span>
          <span><span className="act" data-future={i>at}>{s.action}</span><span className="why">{s.why}</span></span>
        </button></li>)}</ol>
        <div className="ctrls">
          <button type="button" className="btn sm" onClick={()=>{if(at>=plan.length-1)setAt(0);setPlaying(p=>!p);}}>{playing?'Pause':'Play'}</button>
          <button type="button" className="btn sm" onClick={()=>setAt(a=>Math.max(0,a-1))} aria-label="Previous step">←</button>
          <button type="button" className="btn sm" onClick={()=>setAt(a=>Math.min(plan.length-1,a+1))} aria-label="Next step">→</button>
          <span className="prog" aria-hidden="true"><i style={{width:`${((at+1)/plan.length)*100}%`}}/></span>
        </div>
      </div>
      <div className="card">
        <div className="panel-h"><span>Step {at+1} · <span className="mono c-mint">{cur?.action}</span>{cur?.focus?.length?<span className="mono" style={{color:'var(--muted)'}}> · {cur.focus.join(', ')}</span>:null}</span>
          <label style={{display:'flex',gap:8,alignItems:'center',cursor:'pointer',color:'var(--muted)',fontSize:12.5}}><input type="checkbox" checked={calls} onChange={e=>setCalls(e.target.checked)}/> model &amp; SQL calls</label></div>
        <div className="trace" aria-live="polite">
          {cur?.why&&<div className="ln" data-kind="planner"><div className="who"><b>World Model</b><small>select_next_action</small></div><div className="what">{cur.why}<div className="tags"><span className="badge plan">Meterless World Model</span></div></div></div>}
          {lines.map((e,i)=><Line key={`${id}-${at}-${e.seq}-${i}`} e={e} doc={doc}/>)}
        </div>
      </div>
    </div>

    <div className="sec-h"><h2>Outcome</h2><p>Decisions and certificates · <span className="mono">{doc.run_id}</span></p></div>
    <div className="dl">{doc.decisions.map(d=><article key={d.device_id} className="card dcard">
      <div className="l"><span className="dev">{d.device_id}</span><span className="dec" data-d={d.decision}><span className="dot" data-d={d.decision}/>{DECISION_TEXT[d.decision]}</span></div>
      <div className="r"><p className="expl">{cap(d.explanation.text.replace(/^(SAFE_TO_WIPE|RECOVER_FIRST|HOLD):\s*/,''))}</p>
        <div className="tags"><span className="badge model">written by {d.explanation.written_by}</span>{d.explanation.citations_checked&&<span className="badge code">citations checked</span>}
          {Object.entries(d.counts).map(([k,v])=><span key={k} className="badge">{k} × {v}</span>)}</div>
        <ul className="crit" aria-label="Evidence gate">{criteriaFor(d).map(([t,ok])=><li key={t} data-ok={ok}><span aria-hidden="true">{ok?'✓':'✕'}</span>{t}<span className="sr">{ok?' (passed)':' (failed)'}</span></li>)}</ul>
        <details><summary>Certificate <span className="mono">{d.certificate_sha256.slice(0,16)}…</span></summary>
          <ul><li>rule <span className="mono">{d.certificate.rule}</span></li><li>device export sha256 <span className="mono">{d.certificate.device_export_sha256??'no export received'}</span></li>
            <li>server capture sha256 <span className="mono">{d.certificate.server_capture_sha256}</span></li>
            {d.records.map(r=><li key={r.finding_id}>{r.finding_id}: <span className="mono">{r.verdict}</span> · {r.version_id}{r.media_filenames.length?` · ${r.media_filenames.join(', ')}`:''}</li>)}</ul></details>
      </div>
    </article>)}</div>

    <div className="sec-h"><h2>The Scout’s SQL</h2><p>Written by code, never by a model</p></div>
    <div className="card sql">{doc.queries.map(q=><details key={q.query_id}><summary><span>{q.kind}</span><span>{q.rows} rows · {q.provider} · {q.elapsed_ms} ms</span></summary><pre>{q.sql}</pre></details>)}</div>
  </>;
}
