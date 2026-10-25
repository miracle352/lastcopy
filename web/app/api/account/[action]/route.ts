import {backendOrigin,localRequest,validWriteOrigin,upstreamHeaders,workspaceGateway} from '../../../../lib/backend';
export const dynamic='force-dynamic';
export async function POST(request:Request,{params}:{params:Promise<{action:string}>}){
  if(!localRequest(request)||!validWriteOrigin(request))return Response.json({detail:'Use the configured LastCopy website'},{status:403});
  const {action}=await params;if(!['signup','confirm','resend','login','forgot','reset'].includes(action))return new Response(null,{status:404});
  const origin=backendOrigin();if(!origin||workspaceGateway())return Response.json({detail:'Open the account page on the private record server.'},{status:503});
  const chunks:Uint8Array[]=[];let size=0;
  if(request.body){const reader=request.body.getReader();for(;;){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>2048){await reader.cancel();return new Response(null,{status:413});}chunks.push(value);}}
  const body=new Uint8Array(size);let offset=0;for(const chunk of chunks){body.set(chunk,offset);offset+=chunk.length;}
  const headers=upstreamHeaders(request);headers.delete('Cookie');
  try{
    const response=await fetch(origin+'/account/'+action,{method:'POST',headers,body,redirect:'error',cache:'no-store',signal:AbortSignal.timeout(45000)});
    const out=new Headers({'Content-Type':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});
    const cookie=response.headers.get('set-cookie');if(cookie)out.set('Set-Cookie',cookie);
    return new Response(response.body,{status:response.status,headers:out});
  }catch{return Response.json({detail:'Account verification is unavailable. Please try again later.'},{status:503});}
}
