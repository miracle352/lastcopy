'use client';
import './proof-route.css';
import {useRef} from 'react';
import {usePresentationVisibility} from './use-presentation-visibility';
import {Icon} from './icons';
/** A labelled explanation, never a simulated live run. */
export default function ProofRoute({compact=false}:{compact?:boolean}){
  const ref=useRef<HTMLElement>(null),{active,reduced}=usePresentationVisibility(ref);
  return <figure ref={ref} className={'proof-route'+(compact?' proof-route-compact':'')} data-active={active&&!reduced}>
    <figcaption><span className="proof-caption-mark"/>HOW A COPY BECOMES EVIDENCE<span>Illustrative</span></figcaption>
    <div className="proof-map"><svg className="proof-connectors" viewBox="0 0 600 270" fill="none" aria-hidden="true"><path d="M115 125H263Q285 125 285 103V65Q285 45 310 45H455"/><path d="M115 125H263Q285 125 285 147V205Q285 225 310 225H455"/><path className="proof-travel" d="M115 125H263Q285 125 285 103V65Q285 45 310 45H455"/><path className="proof-travel proof-travel-late" d="M115 125H263Q285 125 285 147V205Q285 225 310 225H455"/></svg>
      <div className="proof-original"><div className="proof-file-tab">THE ORIGINAL</div><Icon name="document" size={39}/><span>Field record</span><i/><i/><i/><span className="proof-file-type">XML + media</span></div>
      <div className="proof-checkpoint"><Icon name="search" size={25}/><span>Compare<br/>every detail</span></div>
      <div className="proof-copy"><span className="proof-slot"><Icon name="layers" size={21}/></span><div><strong>Answers & versions</strong><span>Ordered. Repeated. Retained.</span></div><Icon name="check" size={18}/></div>
      <div className="proof-media"><span className="proof-slot"><Icon name="file" size={21}/></span><div><strong>Every referenced file</strong><span>Read the bytes. Check the match.</span></div><Icon name="check" size={18}/></div>
    </div><div className="proof-bottom"><span>Keep the original.</span><span>Read the copy again.<Icon name="arrow" size={15}/></span></div>
  </figure>;
}
