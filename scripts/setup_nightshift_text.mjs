/** Install the vendor-manifest starter text model; never start media engines.
 * Usage: node scripts/setup_nightshift_text.mjs <downloaded-gguf>
 * Windows only. Uses the installed shell's observed named-pipe HTTP contract.
 */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';

const filename = 'Llama-3.2-1B-Instruct-Q4_K_M.gguf';
const expected = '6f85a640a97cf2bf5b8e764087b1e83da0fdb51d7c9fab7d0fece9385611df83';
if (process.platform !== 'win32' || !process.env.LOCALAPPDATA || !process.argv[2]) {
  throw new Error('Requires Windows, LOCALAPPDATA and a downloaded starter GGUF path');
}
const local = process.env.LOCALAPPDATA;
let key = 0xcbf29ce484222325n;
for (const byte of Buffer.from(local.toLowerCase())) {
  key = ((key ^ BigInt(byte)) * 0x100000001b3n) & 0xffffffffffffffffn;
}
const socketPath = `\\\\.\\pipe\\ai.meterless.runtime-${(key & 0xffffffffffffn).toString(16).padStart(12, '0')}-runtime`;
async function admin(method, route, body) {
  return new Promise((resolve, reject) => {
    const raw = body === undefined ? undefined : JSON.stringify(body);
    const req = http.request({ socketPath, method, path: route, headers: {
      host: 'meterlessd', accept: 'application/json',
      ...(raw ? { 'content-type': 'application/json', 'content-length': Buffer.byteLength(raw) } : {}),
    } }, res => {
      let data = '';
      res.on('data', chunk => { data += chunk; if (data.length > 1048576) req.destroy(new Error('Oversized admin response')); });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          if (res.statusCode !== 200 || parsed.error || parsed.ok === false) {
            reject(new Error(`Nightshift ${route}: HTTP ${res.statusCode}, ${String(parsed.error || 'refused')}`));
          } else resolve(parsed);
        } catch (error) { reject(error); }
      });
    });
    req.setTimeout(120000, () => req.destroy(new Error('Nightshift control deadline exceeded')));
    req.on('error', reject);
    req.end(raw);
  });
}
const status = await admin('GET', '/admin/status');
const modelDir = path.join(local, 'ai.meterless.runtime', 'models');
if (status.version !== '1.2.3' || path.resolve(status.models_dir).toLowerCase() !== path.resolve(modelDir).toLowerCase()) {
  throw new Error('Runtime version or model-directory ownership differs from the verified setup');
}
const input = fs.readFileSync(process.argv[2]);
if (input.length !== 807694464 || crypto.createHash('sha256').update(input).digest('hex') !== expected) {
  throw new Error('Starter GGUF does not match the verified public source size and SHA256');
}
const destination = path.join(modelDir, filename);
if (!fs.existsSync(destination)) fs.writeFileSync(destination, input, { flag: 'wx' });
else if (crypto.createHash('sha256').update(fs.readFileSync(destination)).digest('hex') !== expected) {
  throw new Error('Refusing to replace a different existing model');
}
const existing = status.lanes.find(lane => lane.id === 'lastcopy-text');
if (existing && existing.model !== filename) throw new Error('Refusing to replace a different LastCopy lane');
if (!existing) await admin('POST', '/admin/lanes', {
  id: 'lastcopy-text', model: filename, kind: 'local', port: 11501,
  ctx_per_slot: 2048, parallel: 1, backend: 'llamacpp', autostart: false,
  races: true, role: 'race', family: 'llama', active_gb: 1, extra_flags: [],
});
await admin('POST', '/admin/lanes/lastcopy-text/start', {});
const after = await admin('GET', '/admin/status');
const lane = after.lanes.find(item => item.id === 'lastcopy-text');
const receipt = { observed_at: new Date().toISOString(), version: after.version,
  model: filename, model_sha256: expected, model_bytes: input.length,
  source: 'Nightshift WIN manifest starter-brain; bartowski GGUF',
  llama_cpp_ref: after.llama_cpp_ref,
  lane: lane && { id: lane.id, model: lane.model, state: lane.state, port: lane.port },
  inference_verified: false,
};
fs.mkdirSync('private/smoke', { recursive: true });
fs.writeFileSync('private/smoke/nightshift-text-installation.json', JSON.stringify(receipt, null, 2) + '\n');
console.log(JSON.stringify(receipt, null, 2));
