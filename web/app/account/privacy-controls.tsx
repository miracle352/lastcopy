'use client';
import {useEffect,useState} from 'react';
import {api,endpoint,message} from '../../lib/client';
import type {components} from '../../lib/api.generated';
type Status=components['schemas']['PrivacyStatus'];
export default function PrivacyControls(){
  const [status,setStatus]=useState<Status|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[confirm,setConfirm]=useState(false);
  useEffect(()=>{let live=true;void api<Status>('/ui/account').then(value=>{if(live)setStatus(value);}).catch(error=>{if(live)setError(message(error));});return()=>{live=false;};},[]);
  async function request(){setBusy(true);setError('');try{setStatus(await api<Status>('/ui/account/request',{confirm_reviewed_request:confirm}));setConfirm(false);}catch(error){setError(message(error));}finally{setBusy(false);}}
  return <>{error&&<p role="alert" className="notice">{error}</p>}{status&&<>
    <section className="glass-panel" style={{padding:28,marginBlock:24}}><h2>Keep your own copy.</h2><p>The download contains your registered originals, findings, reports and hashes. It excludes passwords, session tokens and server connection keys. Finish or cancel active checks before exporting.</p><a className="button quiet" href={endpoint('/ui/account/export')} download>Download my files and reports</a></section>
    <section className="glass-panel" style={{padding:28,marginBlock:24}}><h2>Request account erasure.</h2><p>This sends a private request to the operator. It does not immediately erase records, stop checks or delete your ODK server data. Download your files first. The operator must review the scope and backup copies before completing erasure.</p><p>{status.backup_policy}</p>{status.request_state==='awaiting_operator_review'?<p role="status" className="notice"><strong>Request saved; awaiting operator review.</strong> Requested {status.requested_at?new Date(status.requested_at).toLocaleString():''}. Your files remain available while the request is reviewed.</p>:<><label className="choice"><input type="checkbox" checked={confirm} disabled={busy} onChange={event=>setConfirm(event.target.checked)}/>I understand that this requests reviewed erasure and does not immediately delete my data.</label><button className="quiet" disabled={!confirm||busy} onClick={()=>void request()}>{busy?'Saving your request…':'Send erasure request'}</button></>}</section>
  </>}</>;
}
