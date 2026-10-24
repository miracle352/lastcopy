import {test} from 'node:test';
import assert from 'node:assert/strict';
import {storeNvidiaKey} from '../scripts/configure_nvidia_nightshift.mjs';

const local = 'C:\\test-local';
const key = 'nvapi-' + 'x'.repeat(40); // Non-secret test input.
function fake({version='1.2.3', existing=false}={}) {
  const calls=[]; let saved=existing;
  return {calls, admin:async (method,route,body)=>{
    calls.push({method,route,body});
    if(method==='GET') return {version,models_dir:local+'\\ai.meterless.runtime\\models',keys_configured:saved?['nvidia']:[]};
    saved=true; return {ok:true};
  }};
}
test('invalid keys cannot change configuration',async()=>{
  const f=fake(); await assert.rejects(storeNvidiaKey('not-a-key',f.admin,local));
  assert.equal(f.calls.length,0);
});
test('a doubled paste is rejected before any request',async()=>{
  const f=fake(); await assert.rejects(storeNvidiaKey(key+key,f.admin,local));
  assert.equal(f.calls.length,0);
});
test('preserve an existing NVIDIA configuration',async()=>{
  const f=fake({existing:true}); await assert.rejects(storeNvidiaKey(key,f.admin,local));
  assert.ok(f.calls.every(c=>c.method==='GET'));
});
test('explicit re-entry replaces only the NVIDIA entry',async()=>{
  const f=fake({existing:true});const receipt=await storeNvidiaKey(key,f.admin,local,{replace:true});
  assert.equal(receipt.replaced_existing,true);
  assert.deepEqual(f.calls.find(c=>c.method==='POST').body,{provider:'nvidia',value:key});
  assert.ok(!JSON.stringify(receipt).includes(key));
});
test('check runtime identity before transmitting a key',async()=>{
  const f=fake({version:'unexpected'}); await assert.rejects(storeNvidiaKey(key,f.admin,local));
  assert.ok(f.calls.every(c=>c.method==='GET'));
});
test('use the observed provider/value API and never return the key',async()=>{
  const f=fake(); const receipt=await storeNvidiaKey(key,f.admin,local);
  assert.deepEqual(f.calls.find(c=>c.method==='POST'),{method:'POST',route:'/admin/keys',body:{provider:'nvidia',value:key}});
  assert.equal(receipt.key_stored,true);assert.equal(receipt.inference_verified,false);
  assert.ok(!JSON.stringify(receipt).includes(key));
});
