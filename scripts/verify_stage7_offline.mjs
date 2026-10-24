/** Real offline sample API/UI acceptance; launch both services with audit fences. */
import {chromium} from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
const dir='docs/verification/stage7';await fs.mkdir(dir,{recursive:true});
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:390,height:844},acceptDownloads:true});
const page=await context.newPage();page.setDefaultTimeout(45000);
const external=[],errors=[],results=[],base='http://127.0.0.1:3000',api=base+'/api/service';
page.on('pageerror',e=>errors.push(e.message));
await context.route('**/*',r=>{const u=new URL(r.request().url());if(['localhost','127.0.0.1'].includes(u.hostname))return r.continue();external.push(u.origin);return r.abort();});
const get=async url=>{const r=await context.request.get(api+url);assert(r.ok(),await r.text());return r.json();};
try{
  assert.equal((await get('/ui/settings')).mode,'sample');assert.equal((await get('/ui/runs')).length,0);
  await page.goto(base+'/app');await page.getByText('No saved checks yet.',{exact:false}).waitFor();
  const expected={media:['MISSING_ATTACHMENT'],stranded:['MISSING_SUBMISSION','MISSING_SUBMISSION','PRESERVED'],export:['EXPORT_VIEW_ONLY'],history:['PRESERVED'],conflict:['CONTENT_CONFLICT']};
  for(const [id,verdicts] of Object.entries(expected)){
    await page.goto(base+'/app?sample='+id);await page.getByRole('button',{name:'Open sample',exact:true}).click();await page.getByRole('button',{name:'Run check',exact:true}).click();await page.getByRole('heading',{name:/Checked records/}).waitFor();
    const run=new URL(page.url()).pathname;const view=await get('/ui'+run);assert.equal(view.manifest.mode,'sample');assert.equal(view.investigation,null);
    assert.deepEqual(view.current_report.findings.map(f=>f.verdict).sort(),verdicts.sort());assert.equal(view.current_report.provider_calls,0);
    await page.getByRole('button',{name:'Inspect evidence for record 1',exact:true}).focus();await page.keyboard.press('Enter');await page.getByRole('heading',{name:'Device and server values',exact:true}).waitFor();await page.keyboard.press('Escape');
    const downloads={};
    for(const name of ['report.txt','findings.json','report.json','trace.jsonl']){const r=await context.request.get(api+'/ui'+run+'/downloads/'+name);assert(r.ok());const b=await r.body();assert(b.length);downloads[name]=createHash('sha256').update(b).digest('hex');}
    if(['media','stranded'].includes(id)){
      await page.getByRole('button',{name:/Prepare recovery bundle for record/}).first().click();await page.getByRole('checkbox',{name:/I reviewed the exact target/}).check();await page.getByRole('button',{name:'Confirm plan review',exact:true}).click();
      const link=page.getByRole('link',{name:'Download recovery bundle',exact:true});await link.waitFor();const r=await context.request.get(base+await link.getAttribute('href'));assert(r.ok());downloads['bundle.zip']=createHash('sha256').update(await r.body()).digest('hex');
      assert.equal(await page.getByRole('button',{name:'Apply reviewed recovery',exact:true}).count(),0);
    }else assert.equal(view.current_report.findings.some(f=>f.recovery_eligible),false);
    await page.reload();await page.getByRole('heading',{name:/Checked records/}).waitFor();results.push({case:id,run,verdicts,downloads});
  }
  assert.equal((await context.request.get(api+'/ui/settings',{headers:{host:'rebound.example:3000'}})).status(),403);
  assert.equal((await context.request.post(api+'/ui/samples/media',{headers:{origin:'https://untrusted.example'}})).status(),403);
  await page.goto(base);await page.evaluate(()=>document.fonts.ready);assert(await page.evaluate(()=>document.fonts.check('16px Figtree')&&document.fonts.check('24px Fraunces')));
  assert.deepEqual(external,[]);assert.deepEqual(errors,[]);
  await fs.writeFile(path.join(dir,'offline-browser.json'),JSON.stringify({status:'passed',browser:browser.version(),results,external_requests:external,errors,network_scope:'Python socket/DNS and Node TCP/fetch process fences; browser blocks non-loopback origins. Providers stopped by operator audit. Host firewall unchanged.'},null,2)+'\n');
}finally{await browser.close();}
