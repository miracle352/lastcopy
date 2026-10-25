import {backendOrigin,localRequest,upstreamHeaders} from '../../../../lib/backend';
export const dynamic='force-dynamic';
export async function GET(request:Request,{params}:{params:Promise<{case:string}>}){
  if(!localRequest(request))return new Response(null,{status:403});
  const {case:sample}=await params;
  if(!['media','export','history'].includes(sample))return new Response(null,{status:404});
  const origin=backendOrigin();if(!origin)return Response.json({detail:'Example service is not configured yet'},{status:503});
  try{
    const result=await fetch(origin+'/public/examples/'+sample,{headers:upstreamHeaders(request),cache:'no-store',redirect:'error',signal:AbortSignal.timeout(15000)});
    return new Response(result.body,{status:result.status,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
  }catch{return Response.json({detail:'The example could not be checked. Try again when the connection returns.'},{status:503});}
}
