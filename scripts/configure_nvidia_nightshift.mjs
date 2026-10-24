/** Private human key entry through the observed Nightshift 1.2.3 key API.
 * Never pass a key as an argument, echo it, or put it in a LastCopy file.
 */
import http from 'node:http';
import path from 'node:path';
import fs from 'node:fs';
import readline from 'node:readline';
import {Writable} from 'node:stream';
import {fileURLToPath} from 'node:url';

function fail(code) { const e=new Error(code);e.code=code;throw e; }
export async function storeNvidiaKey(key, admin, local, {replace=false}={}) {
  if(typeof key!=='string'||!key.startsWith('nvapi-')||key.length<26||key.length>4096||/\s/.test(key)||key.split('nvapi-').length!==2) fail('KEY_FORMAT');
  const before=await admin('GET','/admin/status');
  const expected=path.win32.resolve(local,'ai.meterless.runtime','models').toLowerCase();
  if(before.version!=='1.2.3'||typeof before.models_dir!=='string'||path.win32.resolve(before.models_dir).toLowerCase()!==expected||!Array.isArray(before.keys_configured)) fail('RUNTIME_IDENTITY');
  const existing=before.keys_configured.some(p=>String(p).toLowerCase()==='nvidia');
  if(existing&&!replace) fail('ALREADY_CONFIGURED');
  const saved=await admin('POST','/admin/keys',{provider:'nvidia',value:key});
  if(saved.ok!==true) fail('NOT_STORED');
  const after=await admin('GET','/admin/status');
  if(!after.keys_configured?.includes('nvidia')) fail('NOT_STORED');
  return {provider:'nvidia',key_stored:true,replaced_existing:existing,inference_verified:false,observed_at:new Date().toISOString()};
}

async function main() {
  const replace=process.argv.length===3&&process.argv[2]==='--replace';
  if(process.platform!=='win32'||!process.stdin.isTTY||!process.stdout.isTTY||!process.env.LOCALAPPDATA||(!replace&&process.argv.length!==2)) fail('INTERACTIVE_CONSOLE_REQUIRED');
  process.title=replace?'LastCopy - RE-ENTER NVIDIA key privately':'LastCopy private Nightshift key entry';
  const local=process.env.LOCALAPPDATA;
  let hash=0xcbf29ce484222325n;
  for(const b of Buffer.from(local.toLowerCase())) hash=((hash^BigInt(b))*0x100000001b3n)&0xffffffffffffffffn;
  const socketPath=`\\\\.\\pipe\\ai.meterless.runtime-${(hash&0xffffffffffffn).toString(16).padStart(12,'0')}-runtime`;
  const admin=(method,route,body)=>new Promise((resolve,reject)=>{
    const raw=body===undefined?undefined:JSON.stringify(body);
    const r=http.request({socketPath,path:route,method,headers:{host:'meterlessd',accept:'application/json',
      ...(raw?{'content-type':'application/json','content-length':Buffer.byteLength(raw)}:{})}},res=>{
      let data='';res.on('data',part=>{data+=part;if(data.length>1048576)r.destroy(new Error('CONTROL_UNAVAILABLE'));});
      res.on('end',()=>{try{if(res.statusCode!==200)throw Error('CONTROL_UNAVAILABLE');resolve(JSON.parse(data));}catch{reject(Object.assign(new Error('CONTROL_UNAVAILABLE'),{code:'CONTROL_UNAVAILABLE'}));}});
    });r.setTimeout(20000,()=>r.destroy(Error('CONTROL_UNAVAILABLE')));r.on('error',()=>reject(Object.assign(new Error('CONTROL_UNAVAILABLE'),{code:'CONTROL_UNAVAILABLE'})));r.end(raw);
  });
  const receiptPath=path.resolve(fileURLToPath(new URL('../private/smoke/nightshift-nvidia-key-entry.json',import.meta.url)));
  fs.mkdirSync(path.dirname(receiptPath),{recursive:true});
  console.log('LASTCOPY - PRIVATE NVIDIA KEY ENTRY\nThe Nightshift Setup screen is not working. This prompt uses its background service.\nPaste your NVIDIA API key below. Input is hidden. Nothing is saved to chat or LastCopy configuration.\nPress Ctrl+C to cancel.');
  if(replace) console.log('\nRE-ENTRY: submitting will replace ONLY the NVIDIA key currently stored in Nightshift.\nPaste exactly ONE copy. Doubled pastes are rejected before any change.');
  const muted=new Writable({write(chunk,encoding,done){done();}});
  const rl=readline.createInterface({input:process.stdin,output:muted,terminal:true});
  let cancelled=false;
  let key=await new Promise(resolve=>{
    rl.once('SIGINT',()=>{cancelled=true;rl.close();resolve('');});
    process.stdout.write('\nNVIDIA API key (hidden): ');
    rl.question('',answer=>{rl.history=[];rl.close();resolve(answer.trim());});
  });
  let receipt;
  try {
    if(cancelled) receipt={status:'cancelled',key_stored:false,inference_verified:false};
    else receipt={status:'stored',...await storeNvidiaKey(key,admin,local,{replace})};
  } catch(error) {
    const allowed=['KEY_FORMAT','RUNTIME_IDENTITY','ALREADY_CONFIGURED','NOT_STORED','CONTROL_UNAVAILABLE'];
    receipt={status:'failed',error_code:allowed.includes(error.code)?error.code:'CONTROL_UNAVAILABLE',inference_verified:false};
  } finally {key='';}
  fs.writeFileSync(receiptPath,JSON.stringify(receipt,null,2)+'\n',{mode:0o600});
  console.log('\n\n'+(receipt.status==='stored'?'Saved in Nightshift. Return to Codex and say saved. Inference still needs verification.':receipt.status==='cancelled'?'Cancelled. No key was submitted.':'Not completed: '+receipt.error_code+'. Return to Codex; do not paste the key into chat.'));
  process.stdout.write('\nPress Enter to close this window.');
  await new Promise(resolve=>{const close=readline.createInterface({input:process.stdin,output:muted,terminal:true});close.question('',()=>{close.history=[];close.close();resolve();});});
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  main().catch(()=>{console.error('Private key entry could not start. No credential was printed.');process.exitCode=1;});
}
