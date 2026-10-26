import AuthShell from '../auth-shell';
import AccountForm from '../account-form';
import Link from 'next/link';
import {ownerReturn} from '../../lib/return-path';
import {workspaceOrigin} from '../../lib/backend';
import {redirect} from 'next/navigation';
export default async function LoginPage({searchParams}:{searchParams:Promise<{next?:string}>}){const query=await searchParams;const remote=workspaceOrigin();if(remote)redirect(remote+'/login?next='+encodeURIComponent(ownerReturn(query.next)));return <AuthShell><p className="auth-welcome">Welcome back.</p><p className="auth-form-intro">Open your records and pick up where you left off.</p><AccountForm destination={ownerReturn(query.next)}/><Link className="auth-demo-link" href="/demo">Explore a check without an account <span aria-hidden="true">→</span></Link><p className="hint">Your session lasts eight hours. Your files stay private.</p></AuthShell>;}
