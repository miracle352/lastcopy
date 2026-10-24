import {Suspense} from 'react';
import ImportFlow from './import-flow';
export default function AppPage(){return <Suspense fallback={<main id="main" className="workspace-loading"><h1>Check copies</h1><p role="status">Loading your workspace…</p></main>}><ImportFlow/></Suspense>;}
