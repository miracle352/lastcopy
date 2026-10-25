/** Production product checks: actual API comparisons and downloads, no mocked success. */
import {chromium} from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
const output=path.resolve('docs/verification/product');await fs.mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
const page=await context.newPage();page.setDefaultTimeout(45000);
const base='http://127.0.0.1:3000',checks=[],screens=[],errors=[],external=[];
page.on('pageerror',e=>errors.push(e.message));
await context.route('**/*',route=>{const u=new URL(route.request().url());if(['127.0.0.1','localhost'].includes(u.hostname))return route.continue();external.push(u.origin);return route.abort();});
async function check(name,fn){await fn();checks.push({name,status:'passed'});console.log('PASS '+name);}
async function fits(){const r=await page.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth}));assert(r.document<=r.viewport,JSON.stringify(r));}
async function capture(name){await page.evaluate(()=>document.fonts.ready);await fits();const bytes=await page.screenshot({path:path.join(output,name+'.png'),animations:'disabled'});screens.push({file:name+'.png',sha256:createHash('sha256').update(bytes).digest('hex')});}
async function view(id){return (await context.request.get(base+'/api/service/ui/runs/'+encodeURIComponent(id))).json();}
let run;
try{
 await check('Hero advances automatically, can pause, and logo color stays stable on hover',async()=>{
  await page.goto(base);const scene=page.locator('.record-scene');await scene.scrollIntoViewIfNeeded();
  const initial=await scene.getAttribute('data-scene-step');await page.waitForFunction(s=>document.querySelector('.record-scene').dataset.sceneStep!==s,initial);
  await page.getByRole('button',{name:'Pause animation',exact:true}).click();const paused=await scene.getAttribute('data-scene-step');await page.waitForTimeout(4200);assert.equal(await scene.getAttribute('data-scene-step'),paused);
  assert.equal(await page.getByRole('button',{name:/Show illustrative recovery|Reset illustration/}).count(),0);
  const brand=page.locator('.brand').first();await brand.scrollIntoViewIfNeeded();const color=await brand.evaluate(e=>getComputedStyle(e).color);await brand.hover();assert.equal(await brand.evaluate(e=>getComputedStyle(e).color),color);
 });
 await check('Landing examples compare actual files automatically and reuse one saved run per case',async()=>{
  await page.locator('.sample-workbench').scrollIntoViewIfNeeded();await page.mouse.move(0,0);await page.locator('.sample-result').waitFor();
  assert.equal(await page.getByRole('button',{name:'Run this sample',exact:true}).count(),0);
  const first=await page.locator('.sample-result .text-link').getAttribute('href');const initial=await view(first.split('/').pop());assert.equal(initial.current_report.provider_calls,0);assert.equal(initial.investigation,null);
  await page.waitForFunction(old=>document.querySelector('.sample-result .text-link')?.getAttribute('href')!==old,first,{timeout:20000});
  for(const [name,id,verdict] of [['A missing file','media','MISSING_ATTACHMENT'],['An incomplete export','export','EXPORT_VIEW_ONLY'],['An intentional edit','history','PRESERVED']]){
   await page.getByRole('button',{name:new RegExp(name)}).click();await page.waitForFunction(id=>document.querySelector('.sample-context h3')&&document.querySelector('.sample-result .text-link')&&document.querySelector('.sample-choices button[aria-pressed="true"]')?.textContent.includes(id),name);
   const a=await (await context.request.post(base+'/api/service/ui/examples/'+id,{data:{}})).json();const b=await (await context.request.post(base+'/api/service/ui/examples/'+id,{data:{}})).json();assert.equal(a.run_id,b.run_id);
   const result=await view(a.run_id);assert(result.current_report.findings.some(f=>f.verdict===verdict));assert.equal(result.current_report.provider_calls,0);assert.equal(result.investigation,null);
  }
 });
 await check('My records is the default; connection is real; synthetic reports are clearly separated',async()=>{
  await page.goto(base+'/app');await page.getByText('ODK Central on this PC',{exact:true}).waitFor();await page.getByText('Connected · Local test project',{exact:false}).waitFor();assert.equal(await page.getByRole('button',{name:'My records',exact:true}).getAttribute('aria-pressed'),'true');
  assert(await page.getByRole('heading',{name:'No reports for your records yet.',exact:true}).isVisible());const history=page.locator('.example-history');assert.equal(await history.getAttribute('open'),null);await history.locator('summary').click();assert(!/check-[0-9a-f]{8}-/.test(await history.innerText()));
  await page.getByLabel('Expected devices, one identifier per line',{exact:true}).fill('unsaved-device');await page.getByRole('link',{name:'Start another check',exact:true}).click();await page.waitForURL(/new=/);assert.equal(await page.getByLabel('Expected devices, one identifier per line',{exact:true}).inputValue(),'');const first=page.url();
  await page.getByLabel('Expected devices, one identifier per line',{exact:true}).fill('another-unsaved-device');await page.getByRole('link',{name:'Start another check',exact:true}).click();await page.waitForURL(u=>u.href!==first&&u.searchParams.has('new'));assert.equal(await page.getByLabel('Expected devices, one identifier per line',{exact:true}).inputValue(),'');
 });
 await check('Explicit sample supports actual evidence, reviewed bundle, offline readback, report and refresh',async()=>{
  await page.goto(base+'/app?sample=media');await page.getByRole('button',{name:'Open sample',exact:true}).click();await page.getByRole('button',{name:'Run check',exact:true}).click();await page.getByRole('heading',{name:/Checked records/}).waitFor();run=new URL(page.url()).pathname;
  await page.getByRole('button',{name:'Inspect evidence for record 1',exact:true}).click();await page.getByRole('dialog').getByRole('heading',{name:'Device and server values',exact:true}).waitFor();
  for(let i=0;i<8;i++){await page.keyboard.press('Tab');assert(await page.evaluate(()=>!!document.activeElement.closest('dialog')));}await page.keyboard.press('Escape');assert(await page.getByRole('button',{name:'Inspect evidence for record 1',exact:true}).evaluate(e=>e===document.activeElement));
  await page.getByRole('button',{name:'Prepare recovery bundle for record 1',exact:true}).click();await page.getByRole('checkbox',{name:/I reviewed the exact target/}).check();await page.getByRole('button',{name:'Confirm plan review',exact:true}).click();
  const [bundle]=await Promise.all([page.waitForEvent('download'),page.getByRole('link',{name:'Download recovery bundle',exact:true}).click()]);assert(bundle.suggestedFilename().endsWith('.zip'));
  await page.getByRole('button',{name:'Compare offline readback example',exact:true}).click();await page.getByRole('heading',{name:'Matching copies were verified.',exact:true}).waitFor();await page.reload();await page.getByRole('heading',{name:'Matching copies were verified.',exact:true}).waitFor();
  const [report]=await Promise.all([page.waitForEvent('download'),page.getByRole('link',{name:'Plain-language report',exact:true}).click()]);assert(report.suggestedFilename().endsWith('.txt'));
 });
 await check('Production screenshots at five widths, connected input, results and evidence without page overflow',async()=>{
  for(const width of [360,390,768,1280,1440]){
   await page.setViewportSize({width,height:900});await page.goto(base);await capture('home-'+width);
   await page.goto(base+'/app');await page.getByLabel('Device ZIPs (up to eight)',{exact:true}).waitFor();await page.getByText('Connected · Local test project',{exact:false}).waitFor();await capture('app-'+width);
   await page.goto(base+run);await page.getByRole('heading',{name:/Checked records/}).waitFor();await capture('run-'+width);await page.getByRole('button',{name:'Inspect evidence for record 1',exact:true}).click();await page.getByRole('dialog').getByRole('heading',{name:'Device and server values',exact:true}).waitFor();await capture('evidence-'+width);await page.keyboard.press('Escape');
  }
 });
 await check('200% layout zoom and reduced motion retain usable static states',async()=>{
  for(const route of ['', '/app',run]){await page.setViewportSize({width:1280,height:900});await page.goto(base+route);await page.evaluate(()=>document.documentElement.style.zoom='2');await capture('zoom-'+(route===run?'run':route==='/app'?'app':'home'));await page.evaluate(()=>document.documentElement.style.zoom='');}
  await page.emulateMedia({reducedMotion:'reduce'});await page.setViewportSize({width:390,height:844});await page.goto(base);await page.waitForFunction(()=>document.querySelector('.record-scene')?.dataset.sceneStep==='3');assert.equal(await page.locator('.scan-line').evaluate(e=>getComputedStyle(e).animationName),'none');assert.equal(await page.getByRole('button',{name:'Pause animation',exact:true}).count(),0);await capture('reduced-motion-390');
 });
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 await fs.writeFile(path.join(output,'browser.json'),JSON.stringify({status:'passed',build:'production',browser:browser.version(),checks,screens,errors,external_requests:external,sample_run:run,limitations:['Chromium only','CSS 200% layout zoom; not native browser zoom UI','Sample readback is an authored fixture, not a live upload','Real connected investigation separately recorded; this browser sequence makes no Central record writes']},null,2)+'\n');
}finally{await browser.close();}
