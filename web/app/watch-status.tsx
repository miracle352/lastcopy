'use client';
import {useEffect,useRef,useState} from 'react';
import Link from 'next/link';
import {api,enc,message,type Watch} from '../lib/client';
import {Icon} from './icons';

export default function WatchStatus({onRun}:{onRun:()=>void}){
 const [value,setValue]=useState<Watch|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const last=useRef<string|null>(null),callback=useRef(onRun);callback.current=onRun;
 const focusAfter=useRef<HTMLButtonElement|null>(null);
 useEffect(()=>{if(!busy&&focusAfter.current?.isConnected){focusAfter.current.focus({preventScroll:true});focusAfter.current=null;}},[busy]);
 useEffect(()=>{const abort=new AbortController();let timer:ReturnType<typeof setTimeout>;
  async function read(){try{const v=await api<Watch>('/ui/watch',undefined,abort.signal);if(abort.signal.aborted)return;setValue(v);setError('');if(v.last_run_id!==last.current){last.current=v.last_run_id??null;callback.current();}}catch(e){if(!abort.signal.aborted)setError(message(e));}finally{if(!abort.signal.aborted)timer=setTimeout(()=>void read(),5000);}}
  void read();return()=>{abort.abort();clearTimeout(timer);};
 },[]);
 async function control(action:'start'|'pause'|'check_now'){if(document.activeElement instanceof HTMLButtonElement)focusAfter.current=document.activeElement;setBusy(true);setError('');try{setValue(await api<Watch>('/ui/watch/control',{action}));}catch(e){setError(message(e));}finally{setBusy(false);}}
 if(!value?.configured)return error?<p role="alert">Automatic checker status unavailable. {error}</p>:null;
 const missing=(value.expected_devices??[]).filter(d=>!(value.received_devices??[]).includes(d));
 const transfer=value.device_transfer;
 return <section className="connection-card watch-card" aria-labelledby="watch-heading">
  <div className="connection-symbol"><Icon name="layers" size={24}/></div>
  <div>
   <p className="eyebrow">AUTOMATIC COPY CHECKS</p>
   <h2 id="watch-heading">Keep checking as exports arrive</h2>
   <p role="status">{value.message}</p>
   <p>{value.enabled?'Enabled':'Paused'} · fresh server checks every {value.interval_seconds} seconds while enabled.</p>
   <p className="hint">Read-only comparison. No recovery uploads or AI requests. {transfer?.configured?'The paired device link supplies integrity-sealed exports automatically.':'Devices must deliver a sealed export to the configured private inbox.'}</p>
   {transfer?.configured&&<div className="device-link" aria-label="Automatic device link">
    <p><strong>{transfer.synthetic?'Test emulator · synthetic records':'Paired collection device'}</strong> · {transfer.device_id}</p>
    <p>{transfer.message}</p>
    {transfer.last_device_seen_at&&<p className="hint">Device last checked: <time dateTime={transfer.last_device_seen_at}>{new Date(transfer.last_device_seen_at).toLocaleString()}</time>.</p>}
    {!value.enabled&&<p className="hint">Device polling is paused with automatic checks.</p>}
   </div>}
   {missing.length>0&&<p className="notice">Still waiting for files from {missing.join(', ')}. These devices are not covered by a completed check yet.</p>}
   {value.last_checked_at&&<p>Last comparison: <time dateTime={value.last_checked_at}>{new Date(value.last_checked_at).toLocaleString()}</time></p>}
   {value.last_run_id&&<Link prefetch={false} href={'/runs/'+enc(value.last_run_id)}>Open latest automatic report</Link>}
   <details><summary>Automatic check details</summary>
    <p>Project {value.project_id} · form {value.form_id}</p>
    <p>{value.checks_completed} of {value.max_checks} bounded attempts used for this configured session. Interval is a schedule, not a guarantee of completion time.</p>
    {transfer?.configured&&<p>{transfer.exports_completed} of {transfer.max_exports} device exports retained. Device polling interval: {transfer.interval_seconds} seconds; changing or inaccessible files are not accepted as a fresh complete export.</p>}
    <p>Source evidence is retained. Device timestamps describe observations, not uninterrupted coverage. Offline devices cannot be observed before their export arrives.</p>
    {(value.input_errors??[]).map(e=><p key={e} className="error">{e}</p>)}
   </details>
   {error&&<p role="alert" className="error">{error}</p>}
  </div>
  <div className="watch-actions">
   <button className="quiet compact" disabled={busy} onClick={()=>void control(value.enabled?'pause':'start')}>{value.enabled?'Pause automatic checks':'Start automatic checks'}</button>
   <button className="quiet compact" disabled={busy||value.state==='checking'} onClick={()=>void control('check_now')}>Check inbox and server now</button>
  </div>
 </section>;
}
