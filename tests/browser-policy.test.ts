import test from 'node:test';
import assert from 'node:assert/strict';
import config from '../web/next.config';
test('production policy confines browser resources and forms to the application',async()=>{
 const previous=process.env.NODE_ENV;process.env.NODE_ENV='production';
 try{const headers=(await config.headers!())[0].headers;const csp=headers.find(h=>h.key==='Content-Security-Policy')?.value;
  assert(csp?.includes("object-src 'none'"));assert(csp.includes("frame-ancestors 'none'"));assert(csp.includes("form-action 'self'"));assert(csp.includes("connect-src 'self'"));assert(!csp.includes('unsafe-eval'));
 }finally{if(previous===undefined)delete process.env.NODE_ENV;else process.env.NODE_ENV=previous;}
});
