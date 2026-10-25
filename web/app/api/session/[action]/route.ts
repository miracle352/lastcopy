import {backendOrigin,localRequest,validWriteOrigin,upstreamHeaders,workspaceGateway,cloudAccess} from '../../../../lib/backend';
export const dynamic='force-dynamic';
export async function GET(request:Request,{params}:{params:Promise<{action:string}>}){
  if(!localRequest(request))return Response.json({authenticated:false},{status:403});
  if((await params).action!=='status')return new Response(null,{status:404});
  const origin=backendOrigin();
  if(workspaceGateway()||!cloudAccess()||!origin)return Response.json({authenticated:false},{status:503});
  try{
    const result=await fetch(origin+'/ui/settings',{headers:upstreamHeaders(request),cache:'no-store',redirect:'error',signal:AbortSignal.timeout(10000)});
    return Response.json({authenticated:result.status===200},{status:result.status===200||result.status===401?200:503,headers:{'Cache-Control':'no-store'}});
  }catch{return Response.json({authenticated:false},{status:503,headers:{'Cache-Control':'no-store'}});}
}
export async function POST(request:Request,{params}:{params:Promise<{action:string}>}){
  if(!localRequest(request)||!validWriteOrigin(request))return Response.json({detail:'Use the configured application origin'},{status:403});
  if(workspaceGateway())return Response.json({detail:'Sign in at the private record workspace.'},{status:503});
  const {action}=await params;
  if(!['login','logout'].includes(action))return new Response(null,{status:404});
  const origin=backendOrigin();if(!origin)return Response.json({detail:'Owner access is not configured yet'},{status:503});
  const chunks:Uint8Array[]=[];let size=0;
  if(request.body){const reader=request.body.getReader();for(;;){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>2048){await reader.cancel();return new Response(null,{status:413});}chunks.push(value);}}
  const body=new Uint8Array(size);let offset=0;for(const c of chunks){body.set(c,offset);offset+=c.length;}
  try{
    const result=await fetch(origin+'/session/'+action,{method:'POST',headers:upstreamHeaders(request),body,cache:'no-store',redirect:'error',signal:AbortSignal.timeout(15000)});
    const headers=new Headers({'Content-Type':'application/json','Cache-Control':'no-store'});
    const cookie=result.headers.get('set-cookie');if(cookie)headers.set('Set-Cookie',cookie);
    return new Response(result.body,{status:result.status,headers});
  }catch{return Response.json({detail:'Sign-in service is unavailable. Try again when the connection returns.'},{status:503});}
}
