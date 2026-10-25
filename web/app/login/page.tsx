import LoginForm from './login-form';
import AuthShell from '../auth-shell';
import AccountForm from '../account-form';
import Link from 'next/link';
import {ownerReturn} from '../../lib/return-path';
import {workspaceOrigin} from '../../lib/backend';
import {redirect} from 'next/navigation';
export default async function LoginPage({searchParams}:{searchParams:Promise<{next?:string}>}){const query=await searchParams;const remote=workspaceOrigin();if(remote)redirect(remote+'/login?next='+encodeURIComponent(ownerReturn(query.next)));return <AuthShell><p className="auth-welcome">Welcome back.</p><p className="auth-form-intro">Open your records and pick up where you left off.</p><AccountForm destination={ownerReturn(query.next)}/><details className="owner-access"><summary>Owner access</summary><LoginForm destination={ownerReturn(query.next)}/></details><Link className="auth-demo-link" href="/demo">Just looking? Explore a check without an account.</Link><p className="hint">Sessions last eight hours. Your files stay in your account's private evidence store.</p></AuthShell>;}
