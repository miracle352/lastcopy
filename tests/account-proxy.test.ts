import {test} from 'node:test';import assert from 'node:assert/strict';
test('account gateway validates origin/action/body and returns only a secure session cookie',async()=>{
  Object.assign(process.env,{LASTCOPY_CLOUD_ACCESS:'true',PUBLIC_APP_ORIGIN:'https://app.pilot.example',API_ORIGIN:'http://127.0.0.1:8000',LASTCOPY_TRANSPORT_KEY:'t'.repeat(48)});delete process.env.VERCEL;
  let route;try{route=await import('../web/app/api/account/[action]/route');}catch{assert.fail('Account gateway not implemented');}
  const req=(origin='https://app.pilot.example',body='{}')=>new Request('https://app.pilot.example/api/account/login',{method:'POST',headers:{host:'app.pilot.example',origin,'Content-Type':'application/json',cookie:'lastcopy_session='+'x'.repeat(43)},body});
  const p=(action:string)=>({params:Promise.resolve({action})});const original=globalThis.fetch;let calls=0;
  try{
    globalThis.fetch=async(url,options)=>{calls++;assert.equal(String(url),'http://127.0.0.1:8000/account/login');assert.equal(new Headers(options?.headers).get('cookie'),null);return Response.json({authenticated:true},{headers:{'Set-Cookie':'lastcopy_session='+'y'.repeat(43)+'; Secure; HttpOnly; SameSite=Strict',Authorization:'never-expose'}});};
    assert.equal((await route.POST(req('https://attacker.example'),p('login'))).status,403);
    assert.equal((await route.POST(req(),p('../session/login'))).status,404);
    assert.equal((await route.POST(req(undefined,'a'.repeat(2049)),p('login'))).status,413);
    const r=await route.POST(req(),p('login'));assert.equal(r.status,200);assert.match(r.headers.get('set-cookie')!,/HttpOnly/);assert.equal(r.headers.get('authorization'),null);assert.equal(calls,1);
  }finally{globalThis.fetch=original;}
});
