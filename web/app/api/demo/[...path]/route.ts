import {backendOrigin,localRequest,validWriteOrigin,upstreamHeaders} from '../../../../lib/backend';
export const dynamic='force-dynamic';
export const maxDuration=60;
const allowed=/^(media|stranded|export|history|conflict)(?:\/(plan|bundle|readback|(?:readback\/)?(?:evidence\/[A-Za-z0-9_.:-]{1,128}|objects\/[a-f0-9]{64}|downloads\/(?:report\.txt|report\.json|findings\.json|trace\.jsonl))))?$/;
async function proxy(request:Request,context:{params:Promise<{path:string[]}>}){
  if(!localRequest(request))return Response.json({detail:'Use the configured LastCopy website'},{status:403});
  const {path}=await context.params,joined=path.join('/');
  if(!allowed.test(joined)||path.some(p=>p==='.'||p==='..'||p.includes('/')||p.includes('\\'))||
     (request.method==='POST')!==joined.endsWith('/readback'))return Response.json({detail:'Example action not available'},{status:404});
  if(request.method==='POST'&&!validWriteOrigin(request))return Response.json({detail:'Use this website to compare the readback'},{status:403});
  const origin=backendOrigin();if(!origin)return Response.json({detail:'The example comparator is unavailable. No result has been fabricated.'},{status:503});
  const headers=upstreamHeaders(request);headers.delete('Cookie');
  try{
    const response=await fetch(origin+'/public/demo/'+path.map(encodeURIComponent).join('/'),{method:request.method,headers,redirect:'error',cache:'no-store',signal:AbortSignal.timeout(55000)});
    const output=new Headers({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});
    for(const name of ['content-type','content-disposition']){const value=response.headers.get(name);if(value)output.set(name,value);}
    return new Response(response.body,{status:response.status,headers:output});
  }catch{return Response.json({detail:'The example service did not respond. Retry the comparison when it is available.'},{status:503});}
}
export const GET=proxy;
export const POST=proxy;
