import { backendOrigin } from '../../../../lib/backend';
export const dynamic='force-dynamic';
export const runtime='nodejs';
const allowed=/^(ui\/(settings|prepare|devices|server|imports(?:\/[^/]+)?|runs|samples\/(media|stranded|export|history|conflict)|runs\/[^/]+(?:\/findings\/[^/]+|\/objects\/[a-f0-9]{64}|\/downloads\/(report\.txt|report\.json|findings\.json|trace\.jsonl|investigation\.json|query-evidence\.json|world-model\.jsonl)|\/plans|\/sample-readback|\/start|\/investigation\/cancel)?)|run|runs\/[^/]+(?:\/cancel|\/events|\/artifacts\/(report\.json|findings\.json|receipts\.json|events\.jsonl))?|recovery\/plans\/[a-f0-9]{64}(?:\/bundle|\/review|\/apply|\/recheck|\/result|\/events)?)$/;
async function proxy(request:Request,context:{params:Promise<{path:string[]}>}){
  const {path}=await context.params;
  if(path.some(p=>!p || p==='.' || p==='..' || p.includes('/') || p.includes('\\')) || !allowed.test(path.join('/')))return Response.json({detail:'Unsupported local API route'},{status:404});
  const origin=backendOrigin();
  if(!origin)return Response.json({detail:'The private evidence API is available only in the local application. Start the local API and web app.'},{status:503});
  // Next's internal Request URL can use localhost even when the browser uses
  // 127.0.0.1. Accept only the two documented loopback UI origins, not arbitrary
  // forwarded Host headers or remote browser origins.
  if(request.method==='POST' && request.headers.get('origin') && !['http://127.0.0.1:3000','http://localhost:3000'].includes(request.headers.get('origin')!))return Response.json({detail:'Use the local application to perform this action'},{status:403});
  try{
    const limit=/^ui\/(devices|server)$/.test(path.join('/'))?10485760:65536;
    const chunks:Uint8Array[]=[];let bytes=0;
    if(request.method==='POST' && request.body){const reader=request.body.getReader();while(true){const {done,value}=await reader.read();if(done)break;bytes+=value.length;if(bytes>limit){await reader.cancel();return Response.json({detail:'Request exceeds the visible upload limit'},{status:413});}chunks.push(value);}}
    const body=new Uint8Array(bytes);let offset=0;for(const chunk of chunks){body.set(chunk,offset);offset+=chunk.length;}
    const upstream=await fetch(`${origin}/${path.map(encodeURIComponent).join('/')}`,{method:request.method,cache:'no-store',signal:AbortSignal.timeout(320000),headers:request.method==='POST'?{'Content-Type':request.headers.get('content-type')??'application/json','Origin':'http://127.0.0.1:3000'}:undefined,body:request.method==='POST'?body:undefined});
    const headers=new Headers({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});
    for(const name of ['content-type','content-disposition','x-content-sha256']){const value=upstream.headers.get(name);if(value)headers.set(name,value);}
    return new Response(upstream.body,{status:upstream.status,headers});
  }catch{return Response.json({detail:'The local API did not respond. Check the saved run before retrying; a timed-out write may have reached the server.'},{status:503});}
}
export const GET=proxy;
export const POST=proxy;
