/** Real production UI over the running native device producer; no response mocks. */
import {chromium} from 'playwright-core';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const out='docs/verification/realtime/browser';await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true});
try{
 const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage();
 const errors=[],external=[];page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/*',r=>{const host=new URL(r.request().url()).hostname;if(['localhost','127.0.0.1'].includes(host))return r.continue();external.push(host);return r.abort();});
 const state=async()=>{const r=await context.request.get('http://127.0.0.1:3000/api/service/ui/watch');assert(r.ok());return r.json();};
 await page.goto('http://127.0.0.1:3000/app');
 await page.getByRole('button',{name:'Check connection',exact:true}).waitFor({timeout:90000});
 await page.locator('.connection-scope').filter({hasText:'Water Point Condition Check'}).waitFor();
 await page.locator('.device-link').getByText('Paired collection device',{exact:true}).waitFor();
 let before=await state();assert(before.enabled&&before.device_transfer.configured&&before.device_transfer.state==='waiting_for_records');
 assert.deepEqual(before.received_devices,[]);assert.equal(before.last_run_id,null);
 for(const width of [360,390,768,1280,1440]){
  await page.setViewportSize({width,height:900});await page.locator('.watch-card').scrollIntoViewIfNeeded();await page.evaluate(()=>document.fonts.ready);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.locator('.watch-card').screenshot({path:`${out}/device-link-${width}.png`,animations:'disabled'});
 }
 await page.setViewportSize({width:1280,height:900});await page.evaluate(()=>document.documentElement.style.zoom='2');
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.locator('.watch-card').screenshot({path:`${out}/device-link-zoom-200.png`,animations:'disabled'});
 await page.evaluate(()=>document.documentElement.style.zoom='');await page.emulateMedia({reducedMotion:'reduce'});await page.setViewportSize({width:390,height:844});
 const pause=page.getByRole('button',{name:'Pause automatic checks',exact:true});await pause.focus();await page.keyboard.press('Enter');
 await page.getByRole('button',{name:'Start automatic checks',exact:true}).waitFor();await page.reload();await page.getByRole('button',{name:'Start automatic checks',exact:true}).waitFor();
 await page.getByText('Device polling is paused with automatic checks.',{exact:true}).waitFor();assert(!(await state()).enabled);
 const start=page.getByRole('button',{name:'Start automatic checks',exact:true});await start.focus();await page.keyboard.press('Enter');await page.getByRole('button',{name:'Pause automatic checks',exact:true}).waitFor();
 const deadline=Date.now()+45000;let after;
 do{after=await state();if(after.device_transfer.last_device_seen_at!==before.device_transfer.last_device_seen_at&&after.state==='waiting_for_exports')break;await page.waitForTimeout(500);}while(Date.now()<deadline);
 assert(after.enabled&&after.device_transfer.last_device_seen_at!==before.device_transfer.last_device_seen_at);assert.equal(after.device_transfer.exports_completed,0);assert.equal(after.last_run_id,null);
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 await fs.writeFile(`${out}/browser.json`,JSON.stringify({status:'passed',build:'production',browser:browser.version(),mode:'Connected · actual empty local collection and paired emulator',
  checks:['Actual server connection','Native device-link status and changing real observation time','No invented export, completed report or source coverage','Five responsive widths','200% CSS layout zoom','Reduced motion','Keyboard pause/resume','Pause survives reload'],
  before_device_observation:before.device_transfer.last_device_seen_at,after_device_observation:after.device_transfer.last_device_seen_at,errors,external,
  limitations:['Chromium only','CSS zoom, not native browser zoom UI','No physical-phone or public-hosting acceptance claim']},null,2)+'\n');
 console.log('PASS production device-link state, real polling, persistence, keyboard and responsive browser checks');
}finally{await browser.close();}
