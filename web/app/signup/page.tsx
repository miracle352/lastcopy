import {redirect} from 'next/navigation';
import Link from 'next/link';
import {workspaceOrigin} from '../../lib/backend';
import AccountForm from '../account-form';
import AuthShell from '../auth-shell';
export const dynamic='force-dynamic';
export default function Signup(){const remote=workspaceOrigin();if(remote)redirect(remote+'/signup');return <AuthShell signup><p className="auth-welcome">A place for your fieldwork.</p><p className="auth-form-intro">Create a private record desk. Verify your email, then bring the files you want to check.</p><AccountForm initial="signup"/><Link className="auth-demo-link" href="/demo">Explore LastCopy first. No account needed.</Link><details className="auth-beta-details"><summary>What is included in the beta?</summary><p>Separate private imports and reports. Up to 100 accounts, 100 MiB of inputs and 25 saved checks per account. Connected collection setup is separate; your account does not inherit another coordinator's server credentials.</p></details><p className="hint">By creating an account you acknowledge the <Link href="/privacy">beta privacy and retention notice</Link>.</p></AuthShell>;}
