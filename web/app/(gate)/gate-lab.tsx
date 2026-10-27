'use client';
import {useEffect,useMemo,useState} from 'react';
import {DECISION_TEXT,VERDICTS,VERDICT_TEXT,wipeGate,type Verdict} from '../../lib/wipe-gate';

type Counts=Partial<Record<Verdict,number>>;
const COLOR:Record<Verdict,string>={PRESERVED:'#34d399',EXPORT_VIEW_ONLY:'#7dd3fc',MISSING_ATTACHMENT:'#fbbf24',MISSING_SUBMISSION:'#f59e0b',CONTENT_CONFLICT:'#fb7185',UNVERIFIABLE:'#a78bfa'};
const PRESETS:{label:string;exported:boolean;counts:Counts}[]=[
  {label:'All matched',exported:true,counts:{PRESERVED:3}},
  {label:'Spreadsheet looks short',exported:true,counts:{PRESERVED:1,EXPORT_VIEW_ONLY:2}},
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
  const total=VERDICTS.reduce((a,v)=>a+(counts[v]??0),0);
  const onlyHere=(counts.MISSING_ATTACHMENT??0)+(counts.MISSING_SUBMISSION??0);
  const cert=useMemo(()=>JSON.stringify({rule:'lastcopy-wipe-gate/1',device_id:'tablet-07',decision:result.decision,export_received:exported,
    counts:Object.fromEntries(VERDICTS.filter(v=>counts[v]).map(v=>[v,counts[v]]))}),[counts,exported,result.decision]);
  const [hash,setHash]=useState('');
  useEffect(()=>{let live=true;sha256(cert).then(h=>{if(live)setHash(h);});return()=>{live=false;};},[cert]);
  const set=(v:Verdict,d:number)=>setCounts(c=>({...c,[v]:Math.max(0,Math.min(9,(c[v]??0)+d))}));
  return <div className="card lab">
    <div className="lab-l">
      <span className="kicker">Try the gate</span>
      <h3>What would LastCopy say about this tablet?</h3>
      <p>Set what the verifier found when it compared the tablet’s export with the server, byte for byte.</p>
      <div className="inset toggle"><span>Export received from <span className="mono">tablet-07</span></span>
        <button type="button" aria-pressed={exported} aria-label="Export received" onClick={()=>setExported(e=>!e)}/></div>
      {VERDICTS.map(v=><div key={v} className="inset field" data-off={!exported}>
        <span className="fl">{VERDICT_TEXT[v]}</span><span className="fh">{v}</span>
        <output className="fv" aria-live="polite">{counts[v]??0}</output>
        <span className="ctl"><button type="button" aria-label={`Fewer ${v}`} disabled={!exported||!counts[v]} onClick={()=>set(v,-1)}>−</button>
          <button type="button" aria-label={`More ${v}`} disabled={!exported} onClick={()=>set(v,1)}>+</button></span>
      </div>)}
      <div className="presets">{PRESETS.map(p=><button type="button" key={p.label} onClick={()=>{setCounts(p.counts);setExported(p.exported);}}>{p.label}</button>)}</div>
    </div>
    <div className="lab-r" aria-live="polite">
      <span className="result-k">The wipe gate says</span>
      <div className="result dec" data-d={result.decision}>{DECISION_TEXT[result.decision]}</div>
      <p>{result.rule}</p>
      <div className="meter">
        <div className="mr"><span>Records on this tablet</span><b>{exported?total:'not checked'}</b></div>
        <div className="bar" aria-hidden="true">{exported&&total>0&&VERDICTS.filter(v=>counts[v]).map(v=><i key={v} style={{width:`${(counts[v]!/total)*100}%`,background:COLOR[v]}}/>)}</div>
      </div>
      <div className="row"><span>Only copy is on this tablet</span><b>{exported?onlyHere:'unknown'}</b></div>
      <div className="row" style={{marginTop:0}}><span>Decided by</span><b>code · no model can reach this rule</b></div>
      <div className="cert"><b>certificate</b> {cert}<br/><b>sha256</b> {hash||'…'}</div>
    </div>
  </div>;
}
