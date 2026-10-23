/** Optional low-RAM text lane. Actual observed local admin contract, no media. */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
const name = 'SmolLM2-360M-Instruct-Q4_K_M.gguf';
const sha = '2fa3f013dcdd7b99f9b237717fa0b12d75bbb89984cc1274be1471a465bac9c2';
const size = 270590880;
const input = process.argv[2];
if (process.platform !== 'win32' || !input || !process.env.LOCALAPPDATA) throw Error('Windows, LOCALAPPDATA and verified GGUF path required');
async function hash(file) {
  const h = crypto.createHash('sha256');
  for await (const chunk of fs.createReadStream(file)) h.update(chunk);
  return h.digest('hex');
}
if (fs.statSync(input).size !== size || await hash(input) !== sha) throw Error('Pinned model integrity mismatch');
let key = 0xcbf29ce484222325n;
for (const byte of Buffer.from(process.env.LOCALAPPDATA.toLowerCase())) key = ((key ^ BigInt(byte)) * 0x100000001b3n) & 0xffffffffffffffffn;
const socketPath = `\\\\.\\pipe\\ai.meterless.runtime-${(key & 0xffffffffffffn).toString(16).padStart(12,'0')}-runtime`;
async function admin(method, route, body) {
  return new Promise((resolve,reject) => {
    const raw = body === undefined ? undefined : JSON.stringify(body);
    const r = http.request({socketPath, method, path:route, headers:{host:'meterlessd',accept:'application/json',
      ...(raw ? {'content-type':'application/json','content-length':Buffer.byteLength(raw)} : {})}}, res => {
      let text='';res.on('data',d=>{text+=d;if(text.length>1048576)r.destroy(Error('Response bound'));});
      res.on('end',()=>{try {const j=JSON.parse(text);if(res.statusCode!==200||j.error)reject(Error(`HTTP ${res.statusCode}: ${String(j.error).slice(0,250)}`));else resolve(j);}catch(e){reject(e);}});
    });r.setTimeout(120000,()=>r.destroy(Error('Control deadline')));r.on('error',reject);r.end(raw);
  });
}
const status = await admin('GET','/admin/status');
const directory = path.join(process.env.LOCALAPPDATA,'ai.meterless.runtime','models');
if (status.version !== '1.2.3' || path.resolve(status.models_dir).toLowerCase() !== path.resolve(directory).toLowerCase()) throw Error('Verified runtime identity changed');
const destination = path.join(directory,name);
if (!fs.existsSync(destination)) fs.copyFileSync(input,destination,fs.constants.COPYFILE_EXCL);
if (await hash(destination) !== sha) throw Error('Installed model integrity mismatch; refusing replacement');
const existing = status.lanes.find(l=>l.id==='lastcopy-small-text');
if (existing && existing.model !== name) throw Error('Different existing lane; refusing replacement');
if (!existing) await admin('POST','/admin/lanes',{id:'lastcopy-small-text',model:name,kind:'local',port:11502,
  ctx_per_slot:2048,parallel:1,backend:'cpu',autostart:false,races:true,role:'race',family:'smollm',
  active_gb:0.6,extra_flags:[]});
await admin('POST','/admin/lanes/lastcopy-small-text/start',{});
const after = await admin('GET','/admin/status');
const lane = after.lanes.find(l=>l.id==='lastcopy-small-text');
console.log(JSON.stringify({version:after.version,lane:lane&&{id:lane.id,model:lane.model,state:lane.state},
  model_sha256:sha,bytes:size,license:'Apache-2.0',source_revision:'7be6f65f1db715fe5dc5a4634c0d459b4eed42ec',inference_verified:false}));
