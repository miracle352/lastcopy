'use client';
import {useEffect,useState} from 'react';
import {DECISION_TEXT,type Decision} from '../../lib/wipe-gate';

export type BoardRow={device:string;decision:Decision;counts:Record<string,number>;missing:string[];exported:boolean};
const CLS:Record<Decision,string>={SAFE_TO_WIPE:'mint',RECOVER_FIRST:'amber',HOLD:'rose'};

export default function FleetBoard({rows}:{rows:BoardRow[]}){
  const [i,setI]=useState(1);
  const [paused,setPaused]=useState(false);
  useEffect(()=>{
    if(paused||matchMedia('(prefers-reduced-motion: reduce)').matches)return;
    const t=setInterval(()=>setI(x=>(x+1)%rows.length),3400);return()=>clearInterval(t);
  },[paused,rows.length]);
  const r=rows[i];
  const matched=(r.counts.PRESERVED??0)+(r.counts.EXPORT_VIEW_ONLY??0);
  const only=(r.counts.MISSING_ATTACHMENT??0)+(r.counts.MISSING_SUBMISSION??0);
  const conflict=(r.counts.CONTENT_CONFLICT??0)+(r.counts.UNVERIFIABLE??0);
  const records=matched+only+conflict;
  return <figure style={{margin:0}} onMouseEnter={()=>setPaused(true)} onMouseLeave={()=>setPaused(false)}>
    <div className="flow" aria-live="polite">
      <div className="card node">
        <span className="tab-ico" aria-hidden="true"/>
        <div><div className="t mono" style={{fontSize:'.95rem'}}>{r.device}</div><div className="s">{r.exported?`ODK Collect export · ${records} completed record${records===1?'':'s'}`:'No export received'}</div></div>
        <span className="badge">{r.exported?'Exported':'Missing'}</span>
      </div>
      <div className="wires" aria-hidden="true"><svg viewBox="0 0 400 44" preserveAspectRatio="none"><path className="flowdash" d="M200 0 C200 22 100 18 100 44 M200 0 C200 22 300 18 300 44" fill="none" stroke="rgba(110,231,183,.55)" strokeWidth="1.2"/></svg></div>
      <div className="split">
        <div className="card"><div className="who"><span className="chip sky">SRV</span>On the server</div><div className="k sky">Matched</div>
          <p>{r.exported?(matched?`${matched} record${matched===1?'':'s'} byte-for-byte, every referenced file included.`:'Nothing from this tablet matched yet.'):'Cannot tell: nothing was compared.'}</p></div>
        <div className="card"><div className="who"><span className={`chip ${only?'amber':conflict?'rose':'mint'}`}>TAB</span>Only on the tablet</div>
          <div className={`k ${only?'amber':conflict?'rose':'mint'}`}>{only?'Last copy':conflict?'Conflict':'Nothing'}</div>
          <p>{!r.exported?'Unknown until the tablet is exported.':only?r.missing.join(' · '):conflict?'Server answers differ; a person must choose.':'No data exists only here.'}</p></div>
      </div>
      <div className="card gatebar"><span className={`chip ${CLS[r.decision]}`}>✓</span>Wipe gate<b className={CLS[r.decision]}>{DECISION_TEXT[r.decision]}</b></div>
    </div>
    <div style={{display:'flex',gap:6,marginTop:14}} role="group" aria-label="Choose a tablet">
      {rows.map((x,k)=><button key={x.device} type="button" onClick={()=>{setI(k);setPaused(true);}} aria-pressed={k===i} aria-label={x.device}
        style={{height:6,flex:1,borderRadius:6,border:0,padding:0,background:k===i?`var(--${CLS[x.decision]})`:'rgba(255,255,255,.08)',transition:'background .3s'}}/>)}
    </div>
    <figcaption className="fig"><i>Fig. 1</i>The five tablets from the live connected run on 27 Oct. For each one, code compares the original bytes with the server and the wipe gate decides. Nemotron only investigates and explains.</figcaption>
  </figure>;
}
