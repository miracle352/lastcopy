'use client';
import Link from 'next/link';
import {useState} from 'react';
import {Icon} from './icons';
export function Mode({mode}:{mode:string}){return <span className="badge" data-mode={mode}><Icon name={mode==='sample'?'document':mode==='replay'?'layers':'shield'} size={13}/>{mode==='sample'?'Sample · example records':mode==='replay'?'Replay · saved server export':'Connected · ODK Central'}</span>;}
export function Steps({current,draft}:{current:number;draft?:string}){return <ol className="steps" aria-label="Check workflow">{['Add exports','Check copies','Review gaps','Verify recovery'].map((name,i)=><li key={name} aria-current={current===i+1?'step':undefined}><span aria-hidden="true">{i+1}</span>{i===0&&draft?<Link href={'/app?draft='+encodeURIComponent(draft)}>{name}</Link>:name}</li>)}</ol>;}
export function Hash({value}:{value:string}){const [copied,setCopied]=useState(false);return <div className="hash-control"><code title={value}>{value.slice(0,12)}…{value.slice(-8)}</code><button type="button" className="quiet compact" aria-label={'Copy full hash '+value} onClick={async()=>{try{await navigator.clipboard.writeText(value);setCopied(true);}catch{setCopied(false);}}}>{copied?'Copied':'Copy'}</button><details><summary>Full hash</summary><code>{value}</code></details></div>;}
export function ErrorNote({children}:{children:React.ReactNode}){return <div role="alert" className="notice error"><strong>Action needs attention.</strong> {children}</div>;}
