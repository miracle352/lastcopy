import {requireOwner} from '../../../lib/owner';
import PrivacyControls from './privacy-controls';
export const dynamic='force-dynamic';
export default async function AccountPage(){await requireOwner('/account');return <main id="main" className="section" style={{maxWidth:850,margin:'60px auto'}}><p className="eyebrow">YOUR PRIVATE ACCOUNT</p><h1>Your files.<br/><em>Your choices.</em></h1><p>Export your original files and reports, or submit an account-erasure request for review.</p><PrivacyControls/></main>;}
