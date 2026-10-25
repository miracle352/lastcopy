'use client';
import {useEffect,useState,useRef} from 'react';
import {useRouter} from 'next/navigation';
export default function LoginForm({destination='/app'}:{destination?:string}){
  const [busy,setBusy]=useState(false),[error,setError]=useState('');const input=useRef<HTMLInputElement>(null);const router=useRouter();
  const [checking,setChecking]=useState(true);
  useEffect(()=>{const abort=new AbortController();void fetch('/api/session/status',{cache:'no-store',signal:abort.signal}).then(async r=>{if(r.ok&&(await r.json()).authenticated){router.replace(destination);router.refresh();}}).catch(()=>{}).finally(()=>{if(!abort.signal.aborted)setChecking(false);});return()=>abort.abort();},[destination,router]);
  return <form onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');const password=new FormData(e.currentTarget).get('password');try{const r=await fetch('/api/session/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password}),cache:'no-store'});const data=await r.json();if(!r.ok)throw new Error(data.detail??'Sign-in could not finish');if(input.current)input.current.value='';router.replace(destination);router.refresh();}catch(err){setError(err instanceof Error?err.message:'Sign-in is unavailable');input.current?.focus();}finally{setBusy(false);}}}>
    <label htmlFor="owner-password">Owner passphrase</label><input ref={input} style={{width:'100%',margin:'10px 0 20px'}} id="owner-password" name="password" type="password" autoComplete="current-password" required maxLength={512} aria-describedby={error?'login-error':undefined}/>
    {checking&&<p role="status">Checking your saved sign-in…</p>}{error&&<p id="login-error" role="alert">{error}</p>}<button type="submit" disabled={busy||checking}>{busy?'Signing in…':'Open my records'}</button>
  </form>;
}
