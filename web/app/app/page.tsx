import {Suspense} from 'react';
import ImportFlow from './import-flow';
import {requireOwner} from '../../lib/owner';
export const dynamic='force-dynamic';
export default async function AppPage({searchParams}:{searchParams:Promise<{sample?:string}>}){const query=await searchParams;await requireOwner(query.sample?'/app?sample='+query.sample:'/app');return <Suspense fallback={<main id="main" className="workspace-loading"><h1>Check copies</h1><p role="status">Loading your workspace…</p></main>}><ImportFlow/></Suspense>;}
