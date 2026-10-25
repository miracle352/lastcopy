import {cookies} from 'next/headers';
import {redirect} from 'next/navigation';
import {cloudAccess,backendOrigin,workspaceDestination,workspaceGateway} from './backend';
import {ownerReturn} from './return-path';
export async function requireOwner(destination='/app'){
  if(workspaceGateway()){
    const url=workspaceDestination(destination);
    if(!url)throw new Error('The private workspace origin is not configured correctly');
    redirect(url);
  }
  if(!cloudAccess())return;
  const login='/login?next='+encodeURIComponent(ownerReturn(destination));
  const session=(await cookies()).get('lastcopy_session')?.value;
  if(!session)redirect(login);
  const origin=backendOrigin();if(!origin)redirect(login);
  // The API owns expiry/revocation. Cookie presence alone grants no access.
  let status=503;
  try{status=(await fetch(origin+'/ui/settings',{headers:{Authorization:'Bearer '+process.env.LASTCOPY_TRANSPORT_KEY,Cookie:'lastcopy_session='+session},cache:'no-store',redirect:'error',signal:AbortSignal.timeout(10000)})).status;}catch{/* The client shows the actual service outage. */}
  if(status===401)redirect(login);
}
