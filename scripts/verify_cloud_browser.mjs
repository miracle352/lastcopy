/** Actual Vercel production + AWS API, no response mocks or provider calls. */
import {chromium} from 'playwright-core';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const origin='https://lastcopy-five.vercel.app',run='cloud-recovery-25dadf67ef5c4f58e9d13ce8';
const workspace='https://app-18-141-113-136.sslip.io';
const output='docs/verification/cloud/browser';await fs.mkdir(output,{recursive:true});
const secrets=JSON.parse(await fs.readFile('private/cloud/access.json','utf8'));
const serverSecrets=['transport_key','session_key','transfer_key','central_password','agent_password'].map(k=>secrets[k]).filter(Boolean);
const browser=await chromium.launch({headless:true});const errors=[],foreign=[],responses=[],unavailableBodies=[];
const mark=async step=>{console.log(step);await fs.writeFile('private/cloud/browser-progress.json',JSON.stringify({step,at:new Date().toISOString()}));};
const budget=setTimeout(()=>{errors.push('Browser acceptance exceeded its 480-second budget');void browser.close();},480000);
try{
 const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage();
 context.setDefaultTimeout(45000);context.setDefaultNavigationTimeout(60000);
 page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/*',r=>{if([origin,workspace].includes(new URL(r.request().url()).origin))return r.continue();foreign.push(new URL(r.request().url()).origin);return r.abort();});
 // Read only finished response bodies. Redirect/aborted navigation responses
 // have no retrievable body and must not leave the observer waiting forever.
 page.on('requestfinished',request=>{responses.push((async()=>{const r=await request.response();if(!r||r.status()>=300&&r.status()<400||!/json|javascript|text\/html/.test(r.headers()['content-type']??''))return;const text=await r.text();assert(!serverSecrets.some(secret=>text.includes(secret)),'A server credential was exposed to the browser');})().catch(e=>{if(/No resource with given identifier|body is not available for a response that was navigated away/.test(e.message))unavailableBodies.push(new URL(request.url()).pathname);else errors.push('Finished response inspection: '+e.message);}));});
 await mark('Owner sign-in');await page.goto(origin+'/app');await page.getByLabel('Owner passphrase').waitFor({timeout:60000});
 assert(new URL(page.url()).pathname==='/login');
 assert.equal(new URL(page.url()).origin,workspace);
 await page.getByLabel('Owner passphrase').fill(secrets.owner_passphrase);
 await page.getByRole('button',{name:'Open my records',exact:true}).click();
 await page.getByRole('button',{name:'Check connection',exact:true}).waitFor({timeout:90000});
 await page.locator('.connection-scope').filter({hasText:'Water Point Condition Check'}).waitFor();
 const state=await context.request.get(workspace+'/api/service/ui/watch');assert(state.ok());const watch=await state.json();
 assert(watch.enabled&&watch.device_transfer.configured);assert.deepEqual(watch.received_devices,[]);assert.equal(watch.last_run_id,null);
 await mark('Responsive cloud watch');for(const width of [360,390,768,1280,1440]){
   await page.setViewportSize({width,height:900});await page.locator('.watch-card').scrollIntoViewIfNeeded();await page.evaluate(()=>document.fonts.ready);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.locator('.watch-card').screenshot({path:`${output}/cloud-watch-${width}.png`,animations:'disabled'});
 }
 await page.setViewportSize({width:1280,height:900});await page.evaluate(()=>document.documentElement.style.zoom='2');
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.locator('.watch-card').screenshot({path:`${output}/cloud-watch-200.png`,animations:'disabled'});
 await page.evaluate(()=>document.documentElement.style.zoom='');await page.emulateMedia({reducedMotion:'reduce'});
 await page.reload();await page.getByRole('button',{name:'Check connection',exact:true}).waitFor();
 await mark('Saved evidence');await page.goto(workspace+'/runs/'+run);await page.getByRole('button',{name:'Inspect evidence for record 1'}).waitFor({timeout:60000});
 await page.getByRole('button',{name:'Inspect evidence for record 1'}).click();await page.getByRole('dialog').getByRole('heading',{name:'Source files and original bytes'}).waitFor();
 await page.getByRole('button',{name:'Close evidence'}).focus();await page.keyboard.press('Escape');await page.getByRole('dialog').waitFor({state:'hidden'});
 assert(await page.getByRole('button',{name:'Inspect evidence for record 1'}).evaluate(e=>document.activeElement===e));
 const before=await context.request.get(workspace+'/api/service/ui/runs/'+run);assert(before.ok());const view=await before.json();
 assert.equal(view.manifest.mode,'connected');assert.equal(view.manifest.destination.project_id,2);assert.equal(view.synthetic_source,true);
 const [bundle]=await Promise.all([page.waitForEvent('download'),page.getByRole('link',{name:'Download recovery bundle',exact:true}).click()]);
 await bundle.saveAs(`${output}/recovery-bundle.zip`);assert.equal(await bundle.failure(),null);
 const report=await context.request.get(workspace+'/api/service/ui/runs/'+run+'/downloads/report.txt');assert(report.ok());await fs.writeFile(`${output}/report.txt`,await report.body());
 let appliedThisRun=false;
 if(process.argv.includes('--apply')&&view.plans[0].result.state!=='verified'){
   await mark('Reviewed recovery apply');
   await page.getByRole('checkbox',{name:'I reviewed the exact target, original identifiers, unchanged files and preconditions.'}).check();
   await page.getByRole('button',{name:'Confirm plan review',exact:true}).click();
   await page.getByRole('button',{name:'Read server before Apply',exact:true}).waitFor();
   await page.getByRole('button',{name:'Read server before Apply',exact:true}).click();
   const apply=page.getByRole('button',{name:'Apply reviewed recovery',exact:true});await apply.waitFor();
   await page.waitForFunction(()=>Array.from(document.querySelectorAll('button')).some(b=>b.textContent==='Apply reviewed recovery'&&!b.disabled));
   await apply.click();appliedThisRun=true;await page.getByText('Fresh readback preserved the source.',{exact:true}).waitFor({timeout:180000});
   await page.reload();await page.getByText('Fresh readback preserved the source.',{exact:true}).waitFor();
 }
 await mark('Automatic real public example');await page.goto(origin+'/#try-sample');await page.locator('.automatic-examples').scrollIntoViewIfNeeded();
 await page.getByText('Example comparison complete',{exact:true}).waitFor({timeout:60000});
 // This must open a supported sample flow, not an ID in the separate public DB.
 const explore=page.locator('.automatic-examples a.text-link');
 assert.match(await explore.getAttribute('href'),/^\/app\?sample=(media|export|history)$/);
 await explore.click();await page.getByRole('button',{name:'Open sample',exact:true}).waitFor();
 await mark('Owner sign-out');await page.goto(workspace+'/app');await page.getByRole('button',{name:'Check connection',exact:true}).waitFor();
 await page.getByRole('button',{name:'Sign out',exact:true}).click();await page.getByLabel('Owner passphrase').waitFor();
 assert.equal((await context.request.get(workspace+'/api/service/ui/runs')).status(),401);
 await mark('Response integrity');await Promise.race([Promise.all(responses),new Promise((_,reject)=>setTimeout(()=>reject(new Error('Browser response inspection exceeded 30 seconds')),30000))]);assert.deepEqual(errors,[]);assert.deepEqual(foreign,[]);
 await fs.writeFile(`${output}/browser.json`,JSON.stringify({status:'passed',browser:browser.version(),site:origin,workspace,build:'Vercel landing and AWS production workspace',
  checks:['Anonymous redirect','Owner login','Real cloud connection','Empty source coverage','Five widths','200% CSS layout zoom','Reduced motion','Evidence drawer keyboard/focus','Saved run reload','Automatic real isolated example','Working sample link','Logout revocation','Known server credentials absent from retrievable completed browser responses'],
  response_bodies_unavailable_after_navigation:unavailableBodies,
  recovery_apply_requested:process.argv.includes('--apply'),recovery_apply_executed_this_browser_attempt:appliedThisRun,
  already_verified_on_open:view.plans[0].result.state==='verified',cloud_watch:watch},null,2)+'\n');
 console.log('PASS actual production cloud browser flow');
}catch(e){await fs.writeFile(`${output}/failure.json`,JSON.stringify({status:'failed',message:e.message},null,2)+'\n');throw e;}
finally{clearTimeout(budget);await browser.close();}
