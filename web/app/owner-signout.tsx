'use client';
import {useState} from 'react';
import {usePathname} from 'next/navigation';
export default function OwnerSignout(){const [busy,setBusy]=useState(false),[error,setError]=useState('');const path=usePathname();if(!path.startsWith('/app')&&!path.startsWith('/runs/'))return null;return <span><button className="quiet compact" disabled={busy} onClick={async()=>{setBusy(true);try{const r=await fetch('/api/session/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});if(r.ok||r.status===401)window.location.assign('/login');else throw new Error();}catch{setError('Sign-out could not reach the server.');setBusy(false);}}}>{busy?'Signing out…':'Sign out'}</button>{error&&<span role="alert">{error}</span>}</span>;}
