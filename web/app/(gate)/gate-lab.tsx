'use client';
import {useEffect,useMemo,useState} from 'react';
import {DECISION_TEXT,VERDICTS,VERDICT_TEXT,wipeGate,type Verdict} from '../../lib/wipe-gate';

type Counts=Partial<Record<Verdict,number>>;
const PRESETS:{label:string;exported:boolean;counts:Counts}[]=[
  {label:'All matched',exported:true,counts:{PRESERVED:3}},
  {label:'Spreadsheet looks short',exported:true,counts:{EXPORT_VIEW_ONLY:2}},
  {label:'One photo missing',exported:true,counts:{PRESERVED:2,MISSING_ATTACHMENT:1}},
  {label:'Edited on the server',exported:true,counts:{PRESERVED:1,CONTENT_CONFLICT:1}},
  {label:'Tablet never exported',exported:false,counts:{}},
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
  const cert=useMemo(()=>JSON.stringify({rule:'lastcopy-wipe-gate/1',device_id:'tablet-07',decision:result.decision,export_received:exported,
    counts:Object.fromEntries(VERDICTS.filter(v=>counts[v]).map(v=>[v,counts[v]]))}),[counts,exported,result.decision]);
  const [hash,setHash]=useState('');
  useEffect(()=>{let live=true;sha256(cert).then(h=>{if(live)setHash(h);});return()=>{live=false;};},[cert]);
  const set=(v:Verdict,d:number)=>setCounts(c=>({...c,[v]:Math.max(0,Math.min(9,(c[v]??0)+d))}));
  return <div className="card lab">
    <div className="lab-in">
      <div className="switch"><button type="button" aria-pressed={exported} aria-label="Export received from this tablet" onClick={()=>setExported(e=>!e)}/>
        <span>Export received from <span className="mono">tablet-07</span></span></div>
      {VERDICTS.map(v=><div className="row" key={v} style={{opacity:exported?1:.35}}>
        <div><div className="lbl">{VERDICT_TEXT[v]}</div><div className="sub mono">{v}</div></div>
        <div className="step"><button type="button" aria-label={`Fewer ${v}`} disabled={!exported||!(counts[v])} onClick={()=>set(v,-1)}>−</button>
          <output aria-live="polite">{counts[v]??0}</output>
          <button type="button" aria-label={`More ${v}`} disabled={!exported} onClick={()=>set(v,1)}>+</button></div>
      </div>)}
      <div className="presets">{PRESETS.map(p=><button type="button" key={p.label} onClick={()=>{setCounts(p.counts);setExported(p.exported);}}>{p.label}</button>)}</div>
    </div>
    <div className="lab-out" aria-live="polite">
      <span className="kicker">Wipe gate verdict</span>
      <div className="big-verdict" data-d={result.decision}>{DECISION_TEXT[result.decision]}.</div>
      <p>{result.rule}</p>
      <p style={{marginTop:14,color:'var(--muted)',fontSize:'.9rem'}}>No model can reach this line of code. Agents decide <i className="serif">where to look</i>; the verifier and this gate decide what is true.</p>
      <div className="cert" style={{marginTop:24}}><b>certificate</b> {cert}<br/><b>sha256</b> {hash||'…'}</div>
    </div>
  </div>;
}
