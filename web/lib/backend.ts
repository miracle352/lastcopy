/** Explicit server-only transport; browser headers never choose the destination. */
import {ownerReturn} from './return-path';
export const workspaceGateway=()=>Boolean(process.env.VERCEL&&process.env.WORKSPACE_ORIGIN);
export function workspaceOrigin():string|null {
  if(!workspaceGateway())return null;
  try{const u=new URL(process.env.WORKSPACE_ORIGIN!);return u.protocol==='https:'&&!u.username&&!u.password&&!u.search&&!u.hash&&u.pathname==='/'?u.origin:null;}catch{return null;}
}
export function workspaceDestination(path:string):string|null {
  const origin=workspaceOrigin();return origin?origin+ownerReturn(path):null;
}
export const cloudAccess=()=>process.env.LASTCOPY_CLOUD_ACCESS==='true';
export function appOrigin():string|null {
  try {const u=new URL(process.env.PUBLIC_APP_ORIGIN??'');return u.protocol==='https:'&&!u.username&&!u.password&&!u.search&&!u.hash&&u.pathname==='/'?u.origin:null;}catch{return null;}
}
export function localRequest(request: Request): boolean {
  const host=request.headers.get('host')?.toLowerCase()??'';
  return (!process.env.VERCEL&&['127.0.0.1:3000','localhost:3000'].includes(host)) ||
    Boolean(cloudAccess()&&appOrigin()&&host===new URL(appOrigin()!).host);
}
export function validWriteOrigin(request:Request):boolean {
  const origin=request.headers.get('origin');
  return cloudAccess()?Boolean(origin&&origin===appOrigin()):origin===null||['http://127.0.0.1:3000','http://localhost:3000'].includes(origin);
}
export function upstreamHeaders(request:Request):Headers {
  const h=new Headers();
  if(cloudAccess()){
    h.set('Authorization','Bearer '+(process.env.LASTCOPY_TRANSPORT_KEY??''));
    const cookie=request.headers.get('cookie')?.match(/(?:^|;\s*)lastcopy_session=([A-Za-z0-9_-]{43})(?:;|$)/);
    if(cookie)h.set('Cookie','lastcopy_session='+cookie[1]);
  }
  if(request.method==='POST') {h.set('Origin','http://127.0.0.1:3000');h.set('Content-Type',request.headers.get('content-type')??'application/json');}
  return h;
}

export function backendOrigin(): string | null {
  if(cloudAccess()&&(!appOrigin()||(process.env.LASTCOPY_TRANSPORT_KEY??'').length<32))return null;
  if (process.env.VERCEL&&!cloudAccess()) return null;
  const value = process.env.API_ORIGIN ?? "http://127.0.0.1:8000";
  try {
    const url = new URL(value);
    const local=['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname)&&url.protocol==='http:'&&!process.env.VERCEL;
    const remote=cloudAccess()&&url.protocol==='https:';
    if ((!local&&!remote) || url.username || url.password || url.search || url.hash || url.pathname !== '/') return null;
    return url.origin;
  } catch { return null; }
}
