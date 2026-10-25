'use client';
import {useEffect,useRef,useState} from 'react';
import {Icon,Mark} from './icons';
import {usePresentationVisibility} from './use-presentation-visibility';

/** Automatic explanatory animation. It never writes or reports a real run. */
export default function RecordScene(){
  const [step,setStep]=useState(1),[paused,setPaused]=useState(false);const ref=useRef<HTMLElement>(null);
  const {active,reduced}=usePresentationVisibility(ref);const reviewed=reduced||step===3;
  useEffect(()=>{if(!active||reduced||paused)return;const timer=setInterval(()=>setStep(s=>s%3+1),4000);return()=>clearInterval(timer);},[active,reduced,paused]);
  return <figure ref={ref} className="record-scene" data-ambient data-paused={paused} data-illustration={reviewed?'readback':'gap'} data-scene-step={reduced?3:step} onPointerMove={e=>{if(e.pointerType!=='mouse'||reduced||paused)return;const r=e.currentTarget.getBoundingClientRect();e.currentTarget.style.setProperty('--px',`${((e.clientX-r.left)/r.width-.5)*8}px`);e.currentTarget.style.setProperty('--py',`${((e.clientY-r.top)/r.height-.5)*8}px`);}} onPointerLeave={e=>{e.currentTarget.style.setProperty('--px','0px');e.currentTarget.style.setProperty('--py','0px');}}>
    <div className="scene-topline"><span><i/> HOW A CHECK WORKS</span><span>ANIMATED EXAMPLE</span></div>
    <div className="scene-canvas">
      <div className="desk-rings" aria-hidden="true"><i/><i/><i/></div>
      <div className="archive-shadow" aria-hidden="true"/>
      <div className="field-sheet sheet-rear" aria-hidden="true"/>
      <div className="field-sheet sheet-middle" aria-hidden="true"><span>DEVICE EXPORT / ORIGINAL</span></div>
      <div className="field-sheet sheet-main">
        <div className="sheet-masthead"><span><Icon name="document" size={17}/> FIELD RECORD</span><span>0017</span></div>
        <div className="sheet-heading">Your field records.<br/><em>Every detail counts.</em></div>
        <div className="sheet-data"><span>Inspection ID</span><strong>0017</strong><span>Water points</span><strong>03 recorded</strong></div>
        <div className="sheet-repeats"><span>01 <i/> North inlet <Icon name="check" size={12}/></span><span>02 <i/> Upper crossing <Icon name="check" size={12}/></span><span>03 <i/> South outlet <Icon name="check" size={12}/></span></div>
        <div className="sheet-attachment"><Icon name="file" size={24}/><div><strong>site-photo.jpg</strong><span>Referenced in original XML</span></div></div>
        <div className="sheet-bottom"><span>ORIGINAL BYTES RETAINED</span><Icon name="shield" size={15}/></div>
        <div className="scan-line" aria-hidden="true"/>
      </div>
      <div className="copy-ticket"><div className="ticket-brand"><Mark/><span>SERVER COPY</span><Icon name="check" size={18}/></div><strong>Check every part.</strong><p>Keep the answers.<br/>Keep the photos.</p><div className="ticket-row"><span>Original answers</span><Icon name="check" size={14}/></div><div className="ticket-row"><span>Repeated answers</span><Icon name="check" size={14}/></div><div className="ticket-row ticket-file" data-checked={reviewed}><span>Attached photo</span><Icon name={reviewed?'check':'search'} size={14}/></div><div className="ticket-seal">{reviewed?'EXAMPLE COPY CHECKED':'ONE PHOTO NEEDS ATTENTION'}</div></div>
      <div className="scene-checkpoint" aria-hidden="true"><Mark/></div>
      <div className="gap-ticket" aria-live="off"><span className="gap-icon"><Icon name={reviewed?'check':'search'} size={18}/></span><div><small>{reviewed?'EXAMPLE: READ THE SERVER AGAIN':'EXAMPLE: A MISSING PHOTO'}</small><strong>{reviewed?'The restored photo matches the original.':'The record arrived. The photo didn’t.'}</strong></div></div>
      <span className="travelling-document" aria-hidden="true"><Icon name="document" size={20}/></span>
    </div>
    <ol className="scene-chapters" aria-label="How the animated example works">{['Your originals','Check the copy','Read it again'].map((name,i)=><li key={name} aria-current={(reduced?3:step)===i+1?'step':undefined}><span>0{i+1}</span>{name}</li>)}</ol>
    <figcaption><span><strong>Animated example.</strong> No files are uploaded.</span>{!reduced&&<button className="scene-control quiet compact" type="button" aria-pressed={paused} onClick={()=>setPaused(!paused)}>{paused?'Resume animation':'Pause animation'}</button>}</figcaption>
  </figure>;
}
