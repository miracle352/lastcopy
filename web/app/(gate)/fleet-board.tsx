'use client';
import {useEffect,useState} from 'react';
import {DECISION_TEXT,type Decision} from '../../lib/wipe-gate';

export type BoardRow={device:string;decision:Decision;why:string};

function short(text:string){const s=text.replace(/^(SAFE_TO_WIPE|RECOVER_FIRST|HOLD):\s*/,'');return s.charAt(0).toUpperCase()+s.slice(1);}

export default function FleetBoard({rows,runId,seconds}:{rows:BoardRow[];runId:string;seconds?:number}){
  const [shown,setShown]=useState(rows.length);
  const [run,setRun]=useState(0);
  useEffect(()=>{
    if(run===0)return;
    setShown(0);
    let i=0;const t=setInterval(()=>{i+=1;setShown(i);if(i>=rows.length)clearInterval(t);},520);
    return()=>clearInterval(t);
  },[run,rows.length]);
  useEffect(()=>{if(!matchMedia('(prefers-reduced-motion: reduce)').matches)setRun(1);},[]);
  const counts=rows.reduce((a,r)=>({...a,[r.decision]:(a[r.decision]||0)+1}),{} as Record<string,number>);
  return <figure style={{margin:0}}>
    <div className="card" role="group" aria-label="Five-tablet sample result">
      <div className="card-head">
        <span className="dots" aria-hidden="true"><i/><i/><i/></span>
        <span className="mono">python run.py · {runId}</span>
        <button className="pill live" onClick={()=>setRun(r=>r+1)} style={{background:'transparent'}} aria-label="Replay the fleet check">replay</button>
      </div>
      <div className="board">
        {rows.map((r,i)=>{const done=i<shown;return <div key={r.device+run} className={'tablet'+(done&&run?' scan':'')} data-d={done?r.decision:'pending'}>
          <span className="ico" aria-hidden="true"/>
          <div><div className="name">{r.device}</div><div className="why">{done?short(r.why):'Comparing original bytes with the server…'}</div></div>
          <span className="verdict" data-d={done?r.decision:'pending'}>{done?DECISION_TEXT[r.decision]:'checking'}</span>
        </div>;})}
      </div>
      <div className="board-foot"><span>{counts.SAFE_TO_WIPE||0} safe · {counts.RECOVER_FIRST||0} recover · {counts.HOLD||0} hold</span><span>{seconds?`${seconds}s · `:''}no network · no keys</span></div>
    </div>
    <figcaption className="fig"><b>Fig. 1</b>Five tablets, one sample run. Every decision was made by code; the sentences were checked against the evidence.</figcaption>
  </figure>;
}
