'use client';
import {useEffect,useState} from 'react';
import {DECISION_TEXT} from '../../lib/wipe-gate';
import type {RunDecision} from '../../lib/run-types';
import {Icon} from './chrome';

const ACCENT={SAFE_TO_WIPE:'#34d399',RECOVER_FIRST:'#fbbf24',HOLD:'#fb7185'} as const;

function describe(d:RunDecision){
  const matched=(d.counts.PRESERVED??0)+(d.counts.EXPORT_VIEW_ONLY??0);
  const total=d.records.length;
  const sub=d.certificate.device_export_sha256?`ODK Collect export · ${total} completed record${total===1?'':'s'}`:'No export received';
  const left=d.certificate.device_export_sha256?(matched?`${matched} record${matched===1?'':'s'} byte-for-byte, every referenced file included.`:'Nothing from this tablet matched the server.'):'Nothing to compare yet.';
  const miss=d.records.find(r=>r.verdict==='MISSING_ATTACHMENT'||r.verdict==='MISSING_SUBMISSION');
  const conflict=d.records.find(r=>r.verdict==='CONTENT_CONFLICT');
  let k='NOTHING',right='Every record and file is already on the server.';
  if(miss){k='LAST COPY';right=miss.verdict==='MISSING_ATTACHMENT'?`The file ${miss.media_filenames.join(', ')} of ${miss.version_id}`:`The whole record ${miss.version_id}`;}
  else if(conflict){k='NEEDS A PERSON';right=`Server answers differ for ${conflict.version_id}`;}
  else if(!d.certificate.device_export_sha256){k='NOT CHECKED';right='Collect the export before deciding.';}
  return {sub,left,lk:matched?'MATCHED':'NONE MATCHED',k,right};
}

export default function HeroFigure({decisions}:{decisions:RunDecision[]}){
  const [i,setI]=useState(2);
  const [auto,setAuto]=useState(true);
  useEffect(()=>{
    if(!auto||matchMedia('(prefers-reduced-motion: reduce)').matches)return;
    const t=setInterval(()=>setI(x=>(x+1)%decisions.length),3400);return()=>clearInterval(t);
  },[auto,decisions.length]);
  const d=decisions[i];const v=describe(d);const accent=ACCENT[d.decision];
  return <figure className="diagram" style={{margin:0}}>
    <div className="card d-top">
      <span className="glyph"><Icon name="tablet" size={19}/></span>
      <div><b className="mono" style={{fontSize:15}}>{d.device_id}</b><small>{v.sub}</small></div>
      <span className="chip">{d.certificate.device_export_sha256?'Exported':'Missing'}</span>
    </div>
    <div className="d-wires" aria-hidden="true"><svg viewBox="0 0 470 58" preserveAspectRatio="none"><path d="M235 0v14M235 14C235 30 117 26 117 40v18M235 14C235 30 353 26 353 40v18" stroke="currentColor" strokeWidth="1.3" strokeDasharray="4 5" fill="none"/></svg></div>
    <div className="d-pair" key={d.device_id}>
      <div className="card d-cell fade" style={{['--accent' as string]:'#7dd3fc'}}><div className="t"><i>S</i>On the server</div><span className="k">{v.lk}</span><p>{v.left}</p></div>
      <div className="card d-cell fade" style={{['--accent' as string]:accent}}><div className="t"><i>T</i>Only on the tablet</div><span className="k">{v.k}</span><p>{v.right}</p></div>
    </div>
    <div className="card d-foot"><span className="g"><Icon name="shield" size={12}/></span>Wipe gate<b className="dec" data-d={d.decision}>{DECISION_TEXT[d.decision]}</b></div>
    <div className="ticks" role="group" aria-label="Choose a tablet">{decisions.map((x,j)=><button key={x.device_id} type="button" aria-label={x.device_id} aria-pressed={j===i} onClick={()=>{setI(j);setAuto(false);}} style={j===i?{background:ACCENT[x.decision]}:undefined}/>)}</div>
    <figcaption className="fig"><i>Fig. 1</i>The five tablets from the live connected run on 27 Oct. Code compares the original bytes with the server and the wipe gate decides; Nemotron only investigates and explains.</figcaption>
  </figure>;
}
