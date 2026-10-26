import './../demo-route.css';
import type {Metadata} from 'next';
import Demo from './demo-client';
import ProofRoute from '../proof-route';
export const metadata:Metadata={title:'Try LastCopy · An evidence walkthrough',description:'Run the real verifier on example field records. No account needed.',robots:{index:true,follow:true},alternates:{canonical:'https://lastcopy-five.vercel.app/demo'}};
export default function Page(){return <main id="main" className="workspace demo-page"><header className="page-heading"><div><p className="eyebrow">TRY LASTCOPY · NO ACCOUNT NEEDED</p><h1>A gap you can<br/><em>check for yourself.</em></h1><p>Open an example, inspect the original files, and see exactly what needs attention.</p></div><ProofRoute compact/></header><Demo/></main>;}
