'use client';
import {useState} from 'react';
import {Icon,Mark} from './icons';

/** An interactive teaching illustration. It never writes or reports a real run. */
export default function RecordScene(){
  const [step,setStep]=useState(1),[reviewed,setReviewed]=useState(false);
  return <figure className="record-scene" data-ambient data-illustration={reviewed?'readback':'gap'} data-scene-step={step} onPointerMove={e=>{if(e.pointerType!=='mouse'||matchMedia('(prefers-reduced-motion: reduce)').matches)return;const r=e.currentTarget.getBoundingClientRect();e.currentTarget.style.setProperty('--px',`${((e.clientX-r.left)/r.width-.5)*8}px`);e.currentTarget.style.setProperty('--py',`${((e.clientY-r.top)/r.height-.5)*8}px`);}} onPointerLeave={e=>{e.currentTarget.style.setProperty('--px','0px');e.currentTarget.style.setProperty('--py','0px');}}>
    <div className="scene-topline"><span><i/> THE RECORD JOURNEY</span><span>INTERACTIVE ILLUSTRATION</span></div>
    <div className="scene-canvas">
      <div className="desk-rings" aria-hidden="true"><i/><i/><i/></div>
      <div className="archive-shadow" aria-hidden="true"/>
      <div className="field-sheet sheet-rear" aria-hidden="true"/>
      <div className="field-sheet sheet-middle" aria-hidden="true"><span>DEVICE EXPORT / ORIGINAL</span></div>
      <div className="field-sheet sheet-main">
        <div className="sheet-masthead"><span><Icon name="document" size={17}/> FIELD RECORD</span><span>0017</span></div>
        <div className="sheet-heading">A day in the field.<br/><em>Every detail counts.</em></div>
        <div className="sheet-data"><span>Inspection ID</span><strong>0017</strong><span>Water points</span><strong>03 recorded</strong></div>
        <div className="sheet-repeats"><span>01 <i/> North inlet <Icon name="check" size={12}/></span><span>02 <i/> Upper crossing <Icon name="check" size={12}/></span><span>03 <i/> South outlet <Icon name="check" size={12}/></span></div>
        <div className="sheet-attachment"><Icon name="file" size={24}/><div><strong>site-photo.jpg</strong><span>Referenced in original XML</span></div></div>
        <div className="sheet-bottom"><span>ORIGINAL BYTES RETAINED</span><Icon name="shield" size={15}/></div>
        <div className="scan-line" aria-hidden="true"/>
      </div>
      <div className="copy-ticket"><div className="ticket-brand"><Mark/><span>COPY CHECK</span><Icon name="check" size={18}/></div><strong>Follow the original.</strong><p>Answers, versions<br/>and every file slot.</p><div className="ticket-row"><span>Original XML</span><Icon name="check" size={14}/></div><div className="ticket-row"><span>Repeat occurrences</span><Icon name="check" size={14}/></div><div className="ticket-row ticket-file" data-checked={reviewed}><span>Referenced photo</span><Icon name={reviewed?'check':'search'} size={14}/></div><div className="ticket-seal">{reviewed?'ILLUSTRATIVE READBACK':'ONE QUESTION REMAINS'}</div></div>
      <div className="scene-checkpoint" aria-hidden="true"><Mark/></div>
      <div className="gap-ticket" role="status"><span className="gap-icon"><Icon name={reviewed?'check':'search'} size={18}/></span><div><small>{reviewed?'ILLUSTRATIVE READBACK':'A GAP WORTH FINDING'}</small><strong>{reviewed?'Photo read back. Bytes compared.':'The record arrived. The photo didn’t.'}</strong></div></div>
      <span className="travelling-document" aria-hidden="true"><Icon name="document" size={20}/></span>
    </div>
    <div className="scene-chapters" role="group" aria-label="Explore the illustrative record journey">{['Original','Comparison','Readback'].map((name,i)=><button key={name} type="button" aria-pressed={step===i+1} onClick={()=>{setStep(i+1);setReviewed(i===2);}}><span>0{i+1}</span>{name}</button>)}</div>
    <figcaption><span><strong>Illustrative data.</strong> No upload or live recovery.</span><button className="scene-control quiet compact" type="button" aria-pressed={reviewed} onClick={()=>{setReviewed(!reviewed);setStep(reviewed?1:3);}}>{reviewed?'Reset illustration':'Show illustrative recovery'}<Icon name="arrow" size={14}/></button></figcaption>
  </figure>;
}
