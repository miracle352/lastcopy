import {test} from 'node:test';
import assert from 'node:assert/strict';
import {backendOrigin,localRequest,validWriteOrigin,upstreamHeaders} from '../web/lib/backend';

test('hosted proxy accepts only its explicit HTTPS origin and backend, never forwarded hosts',()=>{
  Object.assign(process.env,{VERCEL:'1',LASTCOPY_CLOUD_ACCESS:'true',PUBLIC_APP_ORIGIN:'https://lastcopy-five.vercel.app',API_ORIGIN:'https://api.pilot.example',LASTCOPY_TRANSPORT_KEY:'t'.repeat(48)});
  assert.equal(backendOrigin(),'https://api.pilot.example');
  assert.equal(localRequest(new Request('https://lastcopy-five.vercel.app/api/service/ui/runs',{headers:{host:'lastcopy-five.vercel.app'}})),true);
  assert.equal(localRequest(new Request('https://evil.example/api/service/ui/runs',{headers:{host:'evil.example','x-forwarded-host':'lastcopy-five.vercel.app'}})),false);
  for(const value of ['http://api.pilot.example','https://user:pass@api.pilot.example','https://api.pilot.example/private','https://api.pilot.example/?x=secret']){
    process.env.API_ORIGIN=value;assert.equal(backendOrigin(),null);
  }
  process.env.API_ORIGIN='https://api.pilot.example';delete process.env.LASTCOPY_TRANSPORT_KEY;
  assert.equal(backendOrigin(),null);
});

test('hosted writes require same origin; transport/cookie headers are code-owned',()=>{
  Object.assign(process.env,{VERCEL:'1',LASTCOPY_CLOUD_ACCESS:'true',PUBLIC_APP_ORIGIN:'https://lastcopy-five.vercel.app',API_ORIGIN:'https://api.pilot.example',LASTCOPY_TRANSPORT_KEY:'server-key'.repeat(6)});
  const request=(origin?:string)=>new Request('https://lastcopy-five.vercel.app/api/service/ui/runs',{method:'POST',headers:{host:'lastcopy-five.vercel.app',...(origin?{origin}:{}),authorization:'Bearer attacker',cookie:'other=private; lastcopy_session='+ 'x'.repeat(43)}});
  assert.equal(validWriteOrigin(request()),false);
  assert.equal(validWriteOrigin(request('https://attacker.example')),false);
  assert.equal(validWriteOrigin(request('https://lastcopy-five.vercel.app')),true);
  const headers=upstreamHeaders(request());
  assert.equal(headers.get('authorization'),'Bearer '+'server-key'.repeat(6));
  assert.equal(headers.get('cookie'),'lastcopy_session='+'x'.repeat(43));
  delete process.env.PUBLIC_APP_ORIGIN;
  assert.equal(validWriteOrigin(request()),false);
});

test('proxy rejects arbitrary routes and returns actual outages without sample substitution',async()=>{
  Object.assign(process.env,{VERCEL:'1',LASTCOPY_CLOUD_ACCESS:'true',PUBLIC_APP_ORIGIN:'https://lastcopy-five.vercel.app',API_ORIGIN:'https://api.pilot.example',LASTCOPY_TRANSPORT_KEY:'t'.repeat(48)});
  const {GET,POST}=await import('../web/app/api/service/[...path]/route');
  const calls:{url:string,headers:Headers}[]=[];const original=globalThis.fetch;
  globalThis.fetch=async(url,options)=>{calls.push({url:String(url),headers:options!.headers as Headers});return Response.json({saved:'real-upstream-response'},{headers:{Authorization:'never-forward-this'}});};
  const req=(method='GET',origin?:string)=>new Request('https://lastcopy-five.vercel.app/api/service/ui/runs',{method,headers:{host:'lastcopy-five.vercel.app',cookie:'lastcopy_session='+'x'.repeat(43),...(origin?{origin}:{})}});
  try{
    const result=await GET(req(),{params:Promise.resolve({path:['ui','runs']})});
    assert.equal((await result.json()).saved,'real-upstream-response');assert.equal(result.headers.get('authorization'),null);
    assert.equal(calls[0].url,'https://api.pilot.example/ui/runs');assert.equal(calls[0].headers.get('authorization'),'Bearer '+'t'.repeat(48));
    assert.equal((await GET(req(),{params:Promise.resolve({path:['..','private']})})).status,404);
    assert.equal((await POST(req('POST','https://attacker.example'),{params:Promise.resolve({path:['ui','runs']})})).status,403);
    assert.equal(calls.length,1);
    globalThis.fetch=async()=>{throw new Error('Sponsor or backend outage');};
    const failed=await GET(req(),{params:Promise.resolve({path:['ui','runs']})});
    assert.equal(failed.status,503);assert.equal('saved' in await failed.json(),false);
  }finally{globalThis.fetch=original;}
});

test('owner sign-in resumes only supported local routes, never imported redirect URLs',async()=>{
  const {ownerReturn}=await import('../web/lib/return-path');
  assert.equal(ownerReturn('/app?sample=media'),'/app?sample=media');
  assert.equal(ownerReturn('/runs/cloud-recovery-123'),'/runs/cloud-recovery-123');
  assert.equal(ownerReturn('/integrations'),'/integrations');
  for(const value of ['https://attacker.example','//attacker.example','/app?next=https://attacker.example','/runs/%2f%2fattacker.example'])assert.equal(ownerReturn(value),'/app');
});

test('Vercel hands private flows to the configured HTTPS workspace and does not buffer field data',async()=>{
  const {workspaceDestination}=await import('../web/lib/backend');
  Object.assign(process.env,{VERCEL:'1',WORKSPACE_ORIGIN:'https://app.pilot.example',LASTCOPY_CLOUD_ACCESS:'true',PUBLIC_APP_ORIGIN:'https://lastcopy-five.vercel.app',API_ORIGIN:'https://api.pilot.example',LASTCOPY_TRANSPORT_KEY:'t'.repeat(48)});
  try{
    assert.equal(workspaceDestination('/app?sample=media'),'https://app.pilot.example/app?sample=media');
    assert.equal(workspaceDestination('/runs/check-123'),'https://app.pilot.example/runs/check-123');
    const {GET}=await import('../web/app/api/service/[...path]/route');
    const response=await GET(new Request('https://lastcopy-five.vercel.app/api/service/ui/runs',{headers:{host:'lastcopy-five.vercel.app'}}),{params:Promise.resolve({path:['ui','runs']})});
    assert.equal(response.status,503);
    for(const value of ['http://workspace.example','https://user:pass@workspace.example','https://workspace.example/path']){
      process.env.WORKSPACE_ORIGIN=value;assert.equal(workspaceDestination('/app'),null);
    }
    delete process.env.VERCEL;process.env.WORKSPACE_ORIGIN='https://app.pilot.example';
    assert.equal(workspaceDestination('/app'),null);
  }finally{delete process.env.WORKSPACE_ORIGIN;}
});

test('session resume returns only authenticated state after a real server check',async()=>{
  Object.assign(process.env,{LASTCOPY_CLOUD_ACCESS:'true',PUBLIC_APP_ORIGIN:'https://app.pilot.example',API_ORIGIN:'http://127.0.0.1:8000',LASTCOPY_TRANSPORT_KEY:'t'.repeat(48)});delete process.env.VERCEL;
  const {GET}=await import('../web/app/api/session/[action]/route');
  const original=globalThis.fetch;
  try{
    globalThis.fetch=async(url,options)=>{assert.equal(String(url),'http://127.0.0.1:8000/ui/settings');assert.equal(new Headers(options?.headers).get('authorization'),'Bearer '+'t'.repeat(48));return Response.json({private_settings:'must not be returned'});};
    const request=new Request('https://app.pilot.example/api/session/status',{headers:{host:'app.pilot.example',cookie:'lastcopy_session='+'x'.repeat(43)}});
    assert.deepEqual(await (await GET(request,{params:Promise.resolve({action:'status'})})).json(),{authenticated:true});
    globalThis.fetch=async()=>new Response(null,{status:401});
    assert.deepEqual(await (await GET(request,{params:Promise.resolve({action:'status'})})).json(),{authenticated:false});
  }finally{globalThis.fetch=original;}
});
