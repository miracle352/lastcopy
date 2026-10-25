import {test} from 'node:test';
import assert from 'node:assert/strict';

test('public demo proxy exposes only fixed offline evidence and never forwards an owner cookie',async()=>{
  Object.assign(process.env,{LASTCOPY_CLOUD_ACCESS:'true',PUBLIC_APP_ORIGIN:'https://app.pilot.example',API_ORIGIN:'http://127.0.0.1:8000',LASTCOPY_TRANSPORT_KEY:'t'.repeat(48)});
  delete process.env.VERCEL;
  let route;try{route=await import('../web/app/api/demo/[...path]/route');}catch{assert.fail('Public evidence proxy is not implemented');}
  const original=globalThis.fetch,calls:string[]=[];
  globalThis.fetch=async(url,options)=>{calls.push(String(url));assert.equal(new Headers(options?.headers).get('cookie'),null);return Response.json({actual:'upstream'});};
  const request=(method='GET',origin?:string)=>new Request('https://app.pilot.example/api/demo/media',{method,headers:{host:'app.pilot.example',cookie:'lastcopy_session='+'x'.repeat(43),...(origin?{origin}:{})}});
  const params=(path:string[])=>({params:Promise.resolve({path})});
  try{
    assert.deepEqual(await (await route.GET(request(),params(['media']))).json(),{actual:'upstream'});
    for(const path of [['owner-run'],['media','apply'],['media','downloads','investigation.json'],['..','ui','runs']])assert.equal((await route.GET(request(),params(path))).status,404);
    assert.equal((await route.POST(request('POST','https://attacker.example'),params(['media','readback']))).status,403);
    assert.equal((await route.POST(request('POST','https://app.pilot.example'),params(['media','apply']))).status,404);
    assert.equal(calls.length,1);
    globalThis.fetch=async()=>{throw new Error('outage');};
    assert.equal((await route.GET(request(),params(['media']))).status,503);
  }finally{globalThis.fetch=original;}
});
