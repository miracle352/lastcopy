'use client';
import {useRef,useState} from 'react';
import {Icon} from './icons';
export default function RecordScene(){const [reviewed,setReviewed]=useState(false),ref=useRef<HTMLElement>(null);
  return <figure className="record-scene" ref={ref} data-ambient data-reveal data-illustration={reviewed?'readback':'gap'} onPointerMove={e=>{if(e.pointerType!=='mouse'||matchMedia('(prefers-reduced-motion: reduce)').matches)return;const r=e.currentTarget.getBoundingClientRect();e.currentTarget.style.setProperty('--px',`${(e.clientX-r.left)/r.width*8-4}px`);e.currentTarget.style.setProperty('--py',`${(e.clientY-r.top)/r.height*8-4}px`);}} onPointerLeave={e=>{e.currentTarget.style.setProperty('--px','0px');e.currentTarget.style.setProperty('--py','0px');}}>
    <div className="scene-topline"><span>CHAIN OF EVIDENCE</span><span>ILLUSTRATION / 01</span></div>
    <div className="scene-canvas"><div className="scene-coordinate scene-coordinate-a">ORIGINALS</div><div className="scene-coordinate scene-coordinate-b">READBACK</div>
      <svg className="scene-routes" viewBox="0 0 540 390" fill="none" aria-hidden="true"><path className="route-rail" d="M90 116H229Q270 116 270 156V241Q270 274 313 274H452"/><path className="route-rail route-rail-alt" d="M90 216H190Q230 216 230 250V320H452"/><path className="route-lit" d="M90 116H229Q270 116 270 156V241Q270 274 313 274H452"/><circle cx="270" cy="194" r="59" stroke="currentColor" strokeDasharray="2 8"/><path d="M20 365h30m-15-15v30M490 35h30m-15-15v30" stroke="currentColor" opacity=".4"/></svg>
      <div className="source-stack"><div className="paper paper-back"/><div className="paper paper-front"><Icon name="document" size={26}/><span>FIELD EXPORT</span><i/><i/><i className="short"/><small>Original XML + files</small></div><span className="stack-label"><Icon name="device" size={14}/> Device snapshot</span></div>
      <div className="checkpoint"><div className="checkpoint-icon"><Icon name="search" size={24}/></div><span>Compare<br/><b>every occurrence.</b></span><small>XML · version · bytes</small></div>
      <div className="checked-copy"><Icon name="file" size={28}/><span>CHECKED COPY</span><div className="copy-lines"><i/><i/><i/></div><span className="scene-result"><Icon name="check" size={14}/> Matching bytes</span></div>
      <div className="unresolved-copy"><Icon name={reviewed?'file':'document'} size={20}/><div><span>Referenced attachment</span><strong>{reviewed?'Read back & compared':'Awaiting a verified copy'}</strong></div><span className="slot-mark">{reviewed?<Icon name="check" size={15}/>:'?'}</span></div>
      <span className="travelling-document"><Icon name="document" size={18}/></span>
    </div>
    <figcaption><span><strong>Illustrative data.</strong> No files are uploaded here.</span><button className="scene-control quiet compact" type="button" aria-pressed={reviewed} onClick={()=>setReviewed(!reviewed)}>{reviewed?'Reset illustration':'Show illustrative recovery'}<Icon name="arrow" size={15}/></button></figcaption>
  </figure>;
}
