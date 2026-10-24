/** Real local production UI. No mocked success, no provider/network substitution. */
import {chromium} from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
const output=path.resolve('docs/verification/redesign');await fs.mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
const page=await context.newPage();page.setDefaultTimeout(45000);
const base='http://127.0.0.1:3000',checks=[],screens=[],errors=[],external=[];
page.on('pageerror',e=>errors.push(e.message));
await context.route('**/*',route=>{const u=new URL(route.request().url());if(['127.0.0.1','localhost'].includes(u.hostname))return route.continue();external.push(u.origin);return route.abort();});
async function check(name,fn){await fn();checks.push({name,status:'passed'});console.log('PASS '+name);}
async function fits(){const r=await page.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth}));assert(r.document<=r.viewport,JSON.stringify(r));}
async function capture(name){await page.evaluate(()=>document.fonts.ready);await fits();const bytes=await page.screenshot({path:path.join(output,name+'.png'),animations:'disabled'});screens.push({file:name+'.png',sha256:createHash('sha256').update(bytes).digest('hex')});}
let run;
try{
 await check('Illustration is interactive, labelled, network-independent and pauses offscreen',async()=>{
   await page.goto(base);await page.getByRole('heading',{name:'Bring every record home.',exact:true}).waitFor();
   const requests=[];const listener=r=>requests.push(r.url());page.on('request',listener);
   await page.getByRole('button',{name:'02 Comparison',exact:true}).click();assert.equal(await page.locator('.record-scene').getAttribute('data-scene-step'),'2');
   await page.getByRole('button',{name:'Show illustrative recovery',exact:true}).click();assert.equal(await page.locator('.record-scene').getAttribute('data-illustration'),'readback');assert.match(await page.locator('figcaption').innerText(),/Illustrative data/);
   assert.equal(requests.filter(u=>u.includes('/api/')).length,0);page.off('request',listener);
   await page.getByRole('button',{name:'Reset illustration',exact:true}).click();
   await page.waitForFunction(()=>document.querySelector('.record-scene')?.classList.contains('in-viewport'));
   assert.equal(await page.locator('.scan-line').evaluate(e=>getComputedStyle(e).animationPlayState),'running');
   await page.locator('#faq').scrollIntoViewIfNeeded();await page.waitForFunction(()=>!document.querySelector('.record-scene')?.classList.contains('in-viewport'));assert.equal(await page.locator('.scan-line').evaluate(e=>getComputedStyle(e).animationPlayState),'paused');
 });
 await check('All five bundled cases use actual fixture comparisons and actual saved findings',async()=>{
   for(const [id,verdict] of [['media','MISSING_ATTACHMENT'],['stranded','MISSING_SUBMISSION'],['export','EXPORT_VIEW_ONLY'],['history','PRESERVED'],['conflict','CONTENT_CONFLICT']]){
     await page.goto(base+'/app?sample='+id);await page.getByRole('button',{name:'Open sample',exact:true}).click();await page.getByRole('button',{name:'Run check',exact:true}).click();await page.getByRole('heading',{name:/Checked records/}).waitFor();
     const runPath=new URL(page.url()).pathname;const view=await (await context.request.get(base+'/api/service/ui'+runPath)).json();
     assert(view.current_report.findings.some(f=>f.verdict===verdict));assert.equal(view.current_report.provider_calls,0);assert.equal(view.investigation,null);
     if(id==='media')run=runPath;
     if(['history','export','conflict'].includes(id))assert.equal(await page.getByRole('button',{name:/Prepare recovery bundle/}).count(),0);
   }
 });
 await check('Real findings, evidence focus trap and Escape return, review, bundle, readback and saved reports',async()=>{
   await page.goto(base+run);await page.getByRole('button',{name:'Inspect evidence for record 1',exact:true}).click();const dialog=page.getByRole('dialog');await dialog.getByRole('heading',{name:'Device and server values',exact:true}).waitFor();
   for(let i=0;i<8;i++){await page.keyboard.press('Tab');assert(await page.evaluate(()=>!!document.activeElement.closest('dialog')));}
   await page.keyboard.press('Escape');assert(await page.getByRole('button',{name:'Inspect evidence for record 1',exact:true}).evaluate(e=>e===document.activeElement));
   await page.getByRole('button',{name:'Prepare recovery bundle for record 1',exact:true}).click();await page.getByRole('heading',{name:'Review recovery',exact:true}).waitFor();
   const compare=page.getByRole('button',{name:'Compare offline readback example',exact:true});assert(await compare.isDisabled());
   await page.getByRole('checkbox',{name:/I reviewed the exact target/}).check();await page.getByRole('button',{name:'Confirm plan review',exact:true}).click();await compare.waitFor();
   const [bundle]=await Promise.all([page.waitForEvent('download'),page.getByRole('link',{name:'Download recovery bundle',exact:true}).click()]);assert(bundle.suggestedFilename().endsWith('.zip'));
   assert.equal(await page.getByRole('button',{name:'Apply reviewed recovery',exact:true}).count(),0);
   await compare.click();await page.getByRole('heading',{name:'Matching copies were verified.',exact:true}).waitFor();assert.match(await page.locator('main').innerText(),/No upload was performed/);await page.reload();await page.getByRole('heading',{name:'Matching copies were verified.',exact:true}).waitFor();
   const [report]=await Promise.all([page.waitForEvent('download'),page.getByRole('link',{name:'Plain-language report',exact:true}).click()]);assert(report.suggestedFilename().endsWith('.txt'));
   await page.goBack();assert.equal(new URL(page.url()).pathname,run);
 });
 await check('Five-width screenshots cover landing, workspace, imports, saved results, evidence and recovery',async()=>{
   for(const width of [360,390,768,1280,1440]){
     await page.setViewportSize({width,height:900});await page.goto(base);await capture('home-'+width);
     await page.goto(base+'/app');await page.waitForFunction(()=>!document.querySelector('.sample-picker>button').disabled);await capture('workspace-'+width);
     await page.goto(base+'/app?import=true');await page.getByLabel('Device ZIPs (up to eight)',{exact:true}).waitFor();await capture('import-'+width);
     await page.goto(base+run);await page.getByRole('heading',{name:/Checked records/}).waitFor();await capture('run-'+width);
     await page.getByRole('button',{name:'Inspect evidence for record 1',exact:true}).click();await page.getByRole('dialog').getByRole('heading',{name:'Device and server values',exact:true}).waitFor();await capture('evidence-'+width);await page.keyboard.press('Escape');
     await page.getByRole('heading',{name:'Review recovery',exact:true}).scrollIntoViewIfNeeded();await capture('recovery-'+width);
   }
 });
 await check('Mobile menu keyboard Escape, same-route New check, error state and dropdowns',async()=>{
   await page.setViewportSize({width:390,height:844});await page.goto(base+'/app');await page.getByRole('button',{name:'Open navigation',exact:true}).click();assert(await page.getByRole('navigation',{name:'Mobile navigation',exact:true}).isVisible());
   await page.getByRole('navigation',{name:'Mobile navigation',exact:true}).getByRole('link',{name:'Workspace',exact:true}).focus();await page.keyboard.press('Escape');assert(await page.getByRole('button',{name:'Open navigation',exact:true}).evaluate(e=>e===document.activeElement));
   await page.getByRole('link',{name:'New check',exact:true}).click();await page.getByLabel('Device ZIPs (up to eight)',{exact:true}).waitFor();
   await page.goto(base+'/app');await page.getByLabel('Sample case',{exact:true}).selectOption('history');await page.getByRole('button',{name:'Open sample',exact:true}).click();await page.getByRole('heading',{name:'Ready to check these copies',exact:true}).waitFor();
   await page.goto(base+'/runs/nonexistent-check');await page.locator('main').getByRole('alert').waitFor();assert.match(await page.locator('main').getByRole('alert').innerText(),/attention/);
 });
 await check('200% layout zoom, reduced-motion state and no-JavaScript first frame',async()=>{
   for(const route of ['', '/app',run]){await page.setViewportSize({width:1280,height:900});await page.goto(base+route);await page.evaluate(()=>document.documentElement.style.zoom='2');await fits();await capture('zoom-'+(route===run?'run':route==='/app'?'workspace':'home'));await page.evaluate(()=>document.documentElement.style.zoom='');}
   await page.emulateMedia({reducedMotion:'reduce'});await page.setViewportSize({width:390,height:844});await page.goto(base);assert.equal(await page.locator('.scan-line').evaluate(e=>getComputedStyle(e).animationName),'none');await page.getByRole('button',{name:'Show illustrative recovery',exact:true}).click();assert.equal(await page.locator('.record-scene').getAttribute('data-illustration'),'readback');await capture('reduced-motion-390');
   const nojs=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});const staticPage=await nojs.newPage();await staticPage.goto(base);assert(await staticPage.getByRole('link',{name:'Check a sample',exact:true}).first().isVisible());assert(await staticPage.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await nojs.close();
 });
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 await fs.writeFile(path.join(output,'browser.json'),JSON.stringify({status:'passed',build:'production',browser:browser.version(),mode:'sample',checks,screens,errors,external_requests:external,original_sample_run:run,limitations:['Chromium only','CSS 200% layout zoom; not native browser zoom UI','Sample recovery readback is a separate authored fixture, not a live upload']},null,2)+'\n');
}finally{await browser.close();}
