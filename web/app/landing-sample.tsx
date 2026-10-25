'use client';
import {useEffect,useRef,useState} from 'react';
import Link from 'next/link';
import {enc,label,message,type RunView} from '../lib/client';
import {Icon} from './icons';
import {usePresentationVisibility} from './use-presentation-visibility';
const cases=[
 {id:'media',name:'A missing file',description:'The answers arrived, but one file did not. LastCopy identifies the file that still needs a server copy.'},
 {id:'export',name:'An incomplete export',description:'The spreadsheet left out repeated answers. The original server record still contains them, so nothing needs resubmitting.'},
 {id:'history',name:'An intentional edit',description:'Someone updated the record. LastCopy finds the original in its history and leaves the newer answers alone.'}
];
export default function LandingSample(){
 const ref=useRef<HTMLDivElement>(null),{active,reduced}=usePresentationVisibility(ref);
 const [selected,setSelected]=useState('media'),[busy,setBusy]=useState(false),[view,setView]=useState<RunView|null>(null),[error,setError]=useState('');
 const [paused,setPaused]=useState(false),[focused,setFocused]=useState(false),[hovered,setHovered]=useState(false);
 useEffect(()=>{
  if(!active)return;
  const abort=new AbortController();
  setError('');setBusy(true);setView(v=>v?.sample_case===selected?v:null);
  // The public endpoint executes/reuses the actual comparator in a separate
  // offline store. It cannot read the owner's records or call providers.
  void fetch('/api/examples/'+selected,{cache:'no-store',signal:abort.signal}).then(async r=>{const data=await r.json();if(!r.ok)throw new Error(data.detail??'Comparison unavailable');if(!abort.signal.aborted){setView(data);setBusy(false);}}).catch(e=>{if(!abort.signal.aborted){setError(message(e));setBusy(false);}});
  return()=>abort.abort();
 },[active,selected]);
 const report=view?.current_report;
 useEffect(()=>{
  if(!active||reduced||paused||focused||hovered||busy||!report)return;
  // Reading time between completed examples. This never completes a real job.
  const timer=setTimeout(()=>setSelected(id=>cases[(cases.findIndex(c=>c.id===id)+1)%cases.length].id),9000);
  return()=>clearTimeout(timer);
 },[active,reduced,paused,focused,hovered,busy,report]);
 return <div ref={ref} className="sample-workbench automatic-examples" data-reveal onFocusCapture={()=>setFocused(true)} onBlurCapture={e=>{if(!e.currentTarget.contains(e.relatedTarget))setFocused(false);}} onPointerEnter={e=>{if(e.pointerType==='mouse')setHovered(true);}} onPointerLeave={()=>setHovered(false)}>
  <div className="example-toolbar"><span className="badge" data-mode="sample">Sample · automatic examples</span>{!reduced&&<button className="quiet compact" onClick={()=>setPaused(!paused)} aria-pressed={paused}>{paused?'Resume examples':'Pause examples'}</button>}</div>
  <div className="sample-choices" role="group" aria-label="Choose an example">{cases.map((c,i)=><button key={c.id} type="button" disabled={busy} aria-pressed={selected===c.id} onClick={()=>setSelected(c.id)}><span>0{i+1}</span>{c.name}<Icon name="arrow" size={16}/></button>)}</div>
  <div className="sample-workbench-body"><div className="sample-context" key={selected}><span className="eyebrow">AN EXAMPLE THAT CHECKS ITSELF</span><h3>{cases.find(c=>c.id===selected)?.name}</h3><p>{cases.find(c=>c.id===selected)?.description}</p><Link prefetch={false} className="button" href="/app/new">Check my records <Icon name="arrow" size={17}/></Link><p className="hint">Synthetic example files. Your own records stay separate.</p></div>
   <div className="sample-output"><div className="output-caption"><span>WHAT THE FILES SHOW</span><Icon name="layers" size={16}/></div>
   {error?<div role="alert"><p className="error">The example could not be checked. {error}</p><Link prefetch={false} href="/app">Open record check</Link></div>:report?<div className="sample-result" key={view?.manifest.run_id}><span className="result-state"><Icon name="check" size={18}/>Example comparison complete</span><h4>{label(report.findings[0])}</h4><dl><div><dt>Records compared</dt><dd>{report.findings.length}</dd></div><div><dt>Source coverage</dt><dd>{report.coverage.complete?'Complete for this example':'Some evidence is missing'}</dd></div><div><dt>Uploads made</dt><dd>None</dd></div></dl><Link prefetch={false} className="text-link" href={'/app?sample='+enc(selected)}>Explore this case <Icon name="arrow" size={16}/></Link></div>:view&&!busy?<div role="status"><p>The example {view.status.state}. No final result was saved.</p><p>{view.status.error??'Your own records have not been changed.'}</p></div>:<div className="sample-empty"><Icon name="document" size={38}/><p role="status">{busy?'Checking the example files…':'The example will check itself here.'}</p><span>Results come from the actual saved comparison.</span></div>}
   </div></div>
 </div>;
}
