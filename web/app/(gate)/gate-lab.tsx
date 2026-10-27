'use client';
import {useEffect,useMemo,useState} from 'react';
import {DECISION_TEXT,wipeGate,type Verdict} from '../../lib/wipe-gate';

type Counts=Partial<Record<Verdict,number>>;
const FIELDS:{v:Verdict;label:string;hint:string;color:string}[]=[
  {v:'PRESERVED',label:'Matched on the server',hint:'byte-for-byte',color:'var(--mint-2)'},
  {v:'EXPORT_VIEW_ONLY',label:'Hidden by the spreadsheet only',hint:'raw XML has it',color:'var(--sky-2)'},
  {v:'MISSING_ATTACHMENT',label:'Photo or file not on the server',hint:'only on tablet',color:'var(--amber)'},
  {v:'MISSING_SUBMISSION',label:'Whole record not on the server',hint:'only on tablet',color:'#f59e0b'},
  {v:'CONTENT_CONFLICT',label:'Server answers differ',hint:'needs a person',color:'var(--rose)'},
];
const PRESETS:{label:string;exported:boolean;counts:Counts}[]=[
  {label:'Everything matched',exported:true,counts:{PRESERVED:3}},
  {label:'Spreadsheet looks short',exported:true,counts:{EXPORT_VIEW_ONLY:2}},
  {label:'One photo missing',exported:true,counts:{PRESERVED:2,MISSING_ATTACHMENT:1}},
  {label:'Edited on the server',exported:true,counts:{PRESERVED:1,CONTENT_CONFLICT:1}},
  {label:'Never exported',exported:false,counts:{}},
];

async function sha256(text:string){
  if(!globalThis.crypto?.subtle)return '';
  const buf=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map(b=>b.toString(16).padStart(2,'0')).join('');
}

export default function GateLab(){
  const [counts,setCounts]=useState<Counts>({PRESERVED:2,MISSING_ATTACHMENT:1});
  const [exported,setExported]=useState(true);
  const result=useMemo(()=>wipeGate(counts,exported),[counts,exported]);
  const total=FIELDS.reduce((a,f)=>a+(counts[f.v]??0),0);
  const onlyHere=(counts.MISSING_ATTACHMENT??0)+(counts.MISSING_SUBMISSION??0);
  const cert=useMemo(()=>JSON.stringify({rule:'lastcopy-wipe-gate/1',device_id:'tablet-07',export_received:exported,decision:result.decision,
    counts:Object.fromEntries(FIELDS.filter(f=>counts[f.v]).map(f=>[f.v,counts[f.v]]))}),[counts,exported,result.decision]);
  const [hash,setHash]=useState('');
  useEffect(()=>{let live=true;sha256(cert).then(h=>{if(live)setHash(h);});return()=>{live=false;};},[cert]);
  const bump=(v:Verdict,d:number)=>setCounts(c=>({...c,[v]:Math.max(0,Math.min(9,(c[v]??0)+d))}));
  return <div className="card lab">
    <div className="lab-in">
      <span className="kicker">Try the gate</span>
      <h3>What would LastCopy say about this tablet?</h3>
      <p className="small">Set what the verifier found on <span className="mono">tablet-07</span>. The decision below uses the same rule, in the same order, as the code that signs every certificate.</p>
      <div className="well toggle"><span>Export received from the tablet</span><button type="button" aria-pressed={exported} aria-label="Export received from the tablet" onClick={()=>setExported(e=>!e)}/></div>
      {FIELDS.map(f=><div key={f.v} className="well field" style={{opacity:exported?1:.4}}>
        <span className="l">{f.label}</span><span className="r mono">{f.v}</span>
        <span className="v"><output aria-live="polite">{counts[f.v]??0}</output>
          <span className="stepper"><button type="button" aria-label={`Fewer: ${f.label}`} disabled={!exported||!counts[f.v]} onClick={()=>bump(f.v,-1)}>−</button><button type="button" aria-label={`More: ${f.label}`} disabled={!exported} onClick={()=>bump(f.v,1)}>+</button></span></span>
        <span className="unit">{f.hint}</span>
      </div>)}
      <div className="presets">{PRESETS.map(p=><button type="button" key={p.label} onClick={()=>{setCounts(p.counts);setExported(p.exported);}}>{p.label}</button>)}</div>
    </div>
    <div className="lab-out" aria-live="polite">
      <span className="kicker" style={{color:'var(--dim)'}}>Wipe gate says</span>
      <div className="verdict-big" data-d={result.decision}>{DECISION_TEXT[result.decision]}</div>
      <p className="small" style={{color:'var(--text)'}}>{result.rule}</p>
      <div style={{marginTop:24}}>
        <div className="kv" style={{borderTop:0,paddingBottom:6}}><span>What the verifier found</span><b>{exported?`${total} item${total===1?'':'s'}`:'nothing checked'}</b></div>
        <div className="bar" aria-hidden="true">{exported&&total>0&&FIELDS.map(f=><i key={f.v} style={{width:`${((counts[f.v]??0)/total)*100}%`,background:f.color}}/>)}</div>
        <div className="kv"><span>Only copy is on this tablet</span><b className={onlyHere?'amber':''}>{exported?onlyHere:'unknown'}</b></div>
        <div className="kv"><span>Decided by</span><b>code · lastcopy-wipe-gate/1</b></div>
      </div>
      <div className="well cert" style={{marginTop:24}}><b>certificate</b> {cert}<br/><b>sha256</b> {hash||'…'}</div>
      <p className="fig" style={{marginTop:14}}>No model can reach this rule. Agents decide where to look; the verifier and this gate decide what is true.</p>
    </div>
  </div>;
}
