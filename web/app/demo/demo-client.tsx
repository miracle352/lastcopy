'use client';

import {useEffect,useRef,useState} from 'react';

import Link from 'next/link';

import {label,message,type RunView,type Evidence,type Finding,type Plan} from '../../lib/client';

import {Mode,Hash,ErrorNote} from '../components';

import {Icon} from '../icons';

import './demo.css';

const cases=[['media','A photo did not arrive'],['stranded','Two records stayed on the device'],['export','The spreadsheet hid some answers'],['history','An answer was intentionally edited'],['conflict','The copies have different answers']];

export default function Demo(){

  const [selected,setSelected]=useState('media'),[view,setView]=useState<RunView|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[evidence,setEvidence]=useState<Evidence|null>(null),[plan,setPlan]=useState<Plan|null>(null);

  const dialog=useRef<HTMLDialogElement>(null),opener=useRef<HTMLElement|null>(null);

  const base='/api/demo/'+selected,root=base+(view?.parent_run_id?'/readback':'');

  async function request<T>(path:string,write=false,signal?:AbortSignal):Promise<T>{const r=await fetch(path,{method:write?'POST':'GET',cache:'no-store',signal});const value=await r.json();if(!r.ok)throw new Error(value.detail??'The example could not be checked');return value;}

  useEffect(()=>{const abort=new AbortController();setView(null);setPlan(null);setError('');setBusy(true);void request<RunView>('/api/demo/'+selected,false,abort.signal).then(setView).catch(e=>{if(!abort.signal.aborted)setError(message(e));}).finally(()=>{if(!abort.signal.aborted)setBusy(false);});return()=>abort.abort();},[selected]);

  const report=view?.current_report??view?.report;

  async function inspect(f:Finding,event:React.MouseEvent<HTMLButtonElement>){opener.current=event.currentTarget;setError('');try{setEvidence(await request<Evidence>(root+'/evidence/'+encodeURIComponent(f.finding_id)));dialog.current?.showModal();}catch(e){setError(message(e));}}

  const close=()=>{dialog.current?.close();opener.current?.focus();};

  async function readback(){setBusy(true);setError('');try{setView(await request<RunView>(base+'/readback',true));}catch(e){setError(message(e));}finally{setBusy(false);}}

  return <><div className="demo-toolbar"><Mode mode="sample"/><p>Synthetic files · actual offline comparison · no uploads or AI calls</p><Link className="text-link" href="/app/new">Check my own records <Icon name="arrow" size={16}/></Link></div>

    <label className="demo-select">Choose an example<select value={selected} disabled={busy} onChange={e=>setSelected(e.target.value)}>{cases.map(([id,title])=><option key={id} value={id}>{title}</option>)}</select></label>

    {error&&<ErrorNote>{error}</ErrorNote>}{busy&&<p role="status">{view?'Comparing the separate readback files…':'Comparing the original example files…'}</p>}

    {report&&<><section className="demo-result" aria-live="polite"><p className="eyebrow">WHAT THE FILES SHOW</p><h2>{report.preservation_outcome==='verified'?'The checked copies match.':report.preservation_outcome==='unresolved'?'Some records could not be verified.':'Some records still need attention.'}</h2><dl className="demo-counts"><div><dt>Investigation</dt><dd>Complete</dd></div><div><dt>Records compared</dt><dd>{report.findings.length}</dd></div><div><dt>Source coverage</dt><dd>{report.coverage.complete?'Complete for this example':'Incomplete'}</dd></div><div><dt>Recovery</dt><dd>No live writes</dd></div></dl><p>{view?.parent_run_id?'Readback example: a separate authored server snapshot was compared. Nothing was uploaded.':view?.provenance}</p>{report.coverage.limitations.map(text=><p key={text} className="notice">{text}</p>)}</section>

    <section aria-label="Affected records" className="demo-findings">{report.findings.map((f,i)=><article key={f.finding_id} className="finding" data-verdict={f.verdict}><div><p className="eyebrow">RECORD {i+1}</p><h3>{label(f)}</h3><p>{f.summary}</p><p className="hint">{f.next_action==='export_guidance'?'Use the original XML or a repeat-aware export. Do not resubmit.':f.next_action==='manual'?'Keep both copies and investigate the unresolved evidence.':f.recovery_eligible?'Review the original files and the permitted recovery bundle.':'Keep the original and the checked copy.'}</p></div><button className="quiet" onClick={e=>void inspect(f,e)}>Inspect evidence for record {i+1} <Icon name="search" size={17}/></button></article>)}</section>

    {report.findings.some(f=>f.recovery_eligible)&&!view?.parent_run_id&&<section className="demo-recovery"><p className="eyebrow">REVIEW BEFORE RECOVERY</p><h2>Keep the originals.<br/><em>Check the result again.</em></h2><p>The bundle contains untouched source files, target identities, hashes, evidence and instructions. This offline example writes nothing to a server.</p><div className="actions"><button className="quiet" disabled={busy} onClick={async()=>{setBusy(true);setError('');try{setPlan(await request<Plan>(base+'/plan'));}catch(e){setError(message(e));}finally{setBusy(false);}}}>Review recovery files</button>{plan&&<a className="button quiet" href={base+'/bundle'} download>Download recovery bundle</a>}<button disabled={busy} onClick={()=>void readback()}>Compare separate readback example <Icon name="arrow" size={17}/></button></div><div>{plan&&<details open><summary>Exact example recovery plan</summary><dl><dt>Target</dt><dd>Example project {plan.target.project_id} · form {plan.target.form_id} · {plan.environment.project_name??plan.environment.base_url}</dd><dt>Operation</dt><dd>{plan.operation.replaceAll('_',' ')}</dd><dt>Original submission / version</dt><dd>{plan.logical_submission_id} / {plan.version_id}</dd></dl><h3>Preconditions</h3><ul>{plan.preconditions.map(p=><li key={p}>{p}</li>)}</ul><h3>Unchanged required files</h3>{Object.entries(plan.source_hashes).map(([path,sha])=><div key={path}><p>{path}</p><Hash value={sha}/></div>)}{plan.limitations.map(text=><p key={text}>{text}</p>)}</details>}</div><p className="hint">A live Apply requires a reviewed plan in the configured synthetic test project. It is unavailable to anonymous visitors.</p></section>}

    <section className="demo-downloads"><h2>Take the evidence with you.</h2><div className="actions">{[['report.txt','Plain-language report'],['findings.json','Findings JSON'],['trace.jsonl','Redacted trace']].map(([name,title])=><a key={name} className="text-link" href={root+'/downloads/'+name} download>{title} <Icon name="arrow" size={16}/></a>)}</div><details><summary>Technical details and scope</summary><p>Run: {report.run_id}. The deterministic verifier decides preservation. This walkthrough uses actual bundled ZIP/XML/media fixtures with independently authored expected outcomes. No external service or model is called. Hashes establish byte integrity; they do not authenticate a server.</p><p>{report.provenance}</p></details></section></>}

    <dialog ref={dialog} className="demo-dialog" aria-labelledby="demo-evidence-heading" onCancel={e=>{e.preventDefault();close();}} onClose={()=>opener.current?.focus()}><div className="drawer-header"><h2 id="demo-evidence-heading">Source files and original bytes</h2><button autoFocus className="quiet compact" onClick={close} aria-label="Close evidence">Close</button></div>{evidence&&<div className="demo-evidence"><h3>{label(evidence.finding)}</h3><p>{evidence.scope}</p><h3>Source files</h3>{evidence.source_files.map(file=><div key={file.object_id+file.path} className="demo-source"><a href={root+'/objects/'+file.object_id} download>{file.path}</a><Hash value={file.sha256}/></div>)}<h3>Answers and repeated occurrences</h3>{evidence.compared_values.length?evidence.compared_values.map((value,i)=><div key={i} className="demo-value"><code>{value.path}</code><p>Occurrence indices: {value.occurrence_indices.join(', ')||'None'}</p><dl><dt>Device</dt><dd>{value.source_present?value.source_value:'Absent'}</dd><dt>Server</dt><dd>{value.server_present?value.server_value:'Absent'}</dd>{value.current_edit_value!==null&&<><dt>Current edit</dt><dd>{value.current_edit_value}</dd></>}</dl></div>):<p>This finding concerns attachment slots or missing evidence. Read the receipts below.</p>}<h3>Evidence receipts</h3>{evidence.receipts.map(r=><details key={r.evidence_id}><summary>{r.attachment_filename??r.xml_path??r.comparison??r.evidence_id}</summary><p>{r.comparison}</p><p>{r.request_scope}</p><p>{r.source_file} · {r.outcome}</p>{r.response_sha256&&<Hash value={r.response_sha256}/>}<code>{r.evidence_id}</code></details>)}</div>}</dialog>

  </>;

}
