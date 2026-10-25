'use client';
import {useEffect,useState} from 'react';
import {api,message,type Connection} from '../lib/client';
import {Icon} from './icons';
export default function ConnectionCard(){
  const [value,setValue]=useState<Connection|null>(null),[busy,setBusy]=useState(true),[error,setError]=useState('');
  async function read(){setBusy(true);setError('');try{setValue(await api<Connection>('/ui/connection'));}catch(e){setError(message(e));}finally{setBusy(false);}}
  useEffect(()=>{void read();},[]);
  return <section className="connection-card" aria-labelledby="server-heading" data-state={value?.state??'checking'}><div className="connection-symbol"><Icon name={value?.state==='connected'?'check':'device'} size={25}/></div><div><p className="eyebrow">YOUR CONNECTED SERVER</p><h2 id="server-heading">ODK Central on this PC</h2><p role="status">{busy?'Checking access to the configured project and form…':error||value?.message}</p>{value?.state==='connected'&&<p className="connection-scope"><strong>Connected</strong> · {value.dedicated_test_project?'Local test project':value.project_name} · form {value.form_name??value.form_id}</p>}<details><summary>Connection details</summary><dl><dt>Project</dt><dd>{value?.project_name??'Not verified yet'}</dd><dt>Form</dt><dd>{value?.form_id??'Not verified yet'}</dd><dt>Last server check</dt><dd>{value?new Date(value.checked_at).toLocaleString():'Not checked yet'}</dd></dl><p>No field records are changed by this connection check.</p>{value?.server_url&&<a href={value.server_url} target="_blank" rel="noreferrer">Open ODK Central</a>}</details></div><button className="quiet compact" disabled={busy} onClick={()=>void read()}>{busy?'Checking connection…':'Check connection'}</button></section>;
}
