import {redirect} from 'next/navigation';
import {randomUUID} from 'node:crypto';
import {workspaceDestination} from '../../../../lib/backend';
export const dynamic='force-dynamic';
export default function NewCheck(){const remote=workspaceDestination('/app/new');if(remote)redirect(remote);redirect('/app?import=true&new='+randomUUID());}
