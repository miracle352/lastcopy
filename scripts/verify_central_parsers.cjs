/** Isolated synthetic controls against the actual Central dependency tree. */
const assert = require('node:assert/strict');
const {createRequire} = require('node:module');
const requireCentral = createRequire('/usr/odk/package.json');
const proxyaddr = requireCentral('proxy-addr');
let trustsUnrelatedAddress = false;
try { trustsUnrelatedAddress = proxyaddr.compile(['::ffff:10.0.0.0/8'])('8.8.8.8', 0); }
catch (error) { assert(error instanceof Error); }
assert.equal(trustsUnrelatedAddress, false, 'Malformed trust prefix must not trust an unrelated IPv4 address');
const express = requireCentral('express'), bodyParser = requireCentral('body-parser'), multer = requireCentral('multer');
const app = express();
app.post('/answers', bodyParser.json({limit: '1kb'}), (req, res) => res.json(req.body));
app.post('/media', multer({storage: multer.memoryStorage(), limits: {fileSize: 1024, files: 1, fields: 2}}).single('photo'), (req, res) => res.json({bytes: req.file.size}));
app.use((error, req, res, next) => res.status(error.status ?? 400).json({error: 'Rejected synthetic input'}));
const server = app.listen(0, '127.0.0.1', async () => {
  const origin = `http://127.0.0.1:${server.address().port}`;
  try {
    let response = await fetch(origin + '/answers', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({condition: 'working'})});
    assert.equal(response.status, 200); assert.deepEqual(await response.json(), {condition: 'working'});
    response = await fetch(origin + '/answers', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{invalid'});
    assert.equal(response.status, 400);
    response = await fetch(origin + '/answers', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({value: 'x'.repeat(2048)})});
    assert.equal(response.status, 413);
    const form = new FormData(); form.set('photo', new Blob(['original synthetic bytes']), 'photo.txt');
    response = await fetch(origin + '/media', {method: 'POST', body: form});
    assert.equal(response.status, 200); assert.equal((await response.json()).bytes, 24);
    const large = new FormData(); large.set('photo', new Blob(['x'.repeat(2048)]), 'large.txt');
    response = await fetch(origin + '/media', {method: 'POST', body: large});assert.equal(response.status, 400);
    console.log(JSON.stringify({status: 'passed', malformed_proxy_subnet_trust: false, actual_json_and_multipart: true, oversized_inputs_rejected: true,
      packages: Object.fromEntries(['proxy-addr', 'body-parser', 'multer'].map(name => [name, requireCentral(name + '/package.json').version])), network: 'Docker none; HTTP loopback only'}));
  } catch (error) {console.error(error);process.exitCode = 1;}
  finally { server.closeAllConnections(); server.close(); }
});
