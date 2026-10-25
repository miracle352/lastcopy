import LoginForm from './login-form';
import {ownerReturn} from '../../lib/return-path';
import {workspaceOrigin} from '../../lib/backend';
import {redirect} from 'next/navigation';
export default async function LoginPage({searchParams}:{searchParams:Promise<{next?:string}>}){const query=await searchParams;const remote=workspaceOrigin();if(remote)redirect(remote+'/login?next='+encodeURIComponent(ownerReturn(query.next)));return <main id="main" className="section"><div className="glass-panel" style={{maxWidth:520,margin:'4rem auto',padding:'clamp(24px,5vw,48px)'}}><p className="eyebrow">Your private records</p><h1 style={{fontSize:'clamp(36px,6vw,56px)'}}>Welcome back.</h1><p>Sign in to check your field records and open saved reports.</p><LoginForm destination={ownerReturn(query.next)}/><p className="muted">Access lasts eight hours. Your files remain private on your configured server.</p></div></main>;}
