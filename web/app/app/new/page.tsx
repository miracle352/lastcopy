import {redirect} from 'next/navigation';
import {randomUUID} from 'node:crypto';
export const dynamic='force-dynamic';
export default function NewCheck(){redirect('/app?import=true&new='+randomUUID());}
