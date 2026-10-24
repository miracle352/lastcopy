import {Suspense} from 'react';
import RunClient from './run-client';
export default async function RunPage({params}:{params:Promise<{id:string}>}){const {id}=await params;return <Suspense fallback={<main id="main"><h1>Saved check</h1><p role="status">Loading saved evidence…</p></main>}><RunClient id={id}/></Suspense>;}
