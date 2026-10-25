import {requireOwner} from '../../lib/owner';
import CloudSetup from './setup-client';
export const dynamic='force-dynamic';
export default async function Integrations(){await requireOwner('/integrations');return <main id="main" className="workspace integration-workspace"><header className="page-heading"><div><p className="eyebrow">OWNER SETTINGS · SERVER-SIDE CREDENTIALS</p><h1>Cloud AI,<br/><em>clearly connected.</em></h1><p>Configure a direct NVIDIA connection on AWS. Your PC can be off for this provider. The deterministic verifier still decides preservation.</p></div></header><CloudSetup/></main>;}
