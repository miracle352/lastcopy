/** Read-only browser check of the empty, ready collection configuration. */
import {chromium} from 'playwright-core';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const out='docs/verification/water-point/ready';await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true});
try{
 const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage();
 const errors=[],external=[];page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/*',route=>{const host=new URL(route.request().url()).hostname;if(['localhost','127.0.0.1'].includes(host))return route.continue();external.push(host);return route.abort();});
 await page.goto('http://127.0.0.1:3000/app');
 await page.getByRole('button',{name:'Check connection',exact:true}).waitFor({timeout:90000});
 await page.locator('.connection-scope').filter({hasText:'Water Point Condition Check'}).waitFor();
 await page.getByRole('button',{name:'Pause automatic checks',exact:true}).waitFor();
 await page.getByText('Waiting for a finished device export and its integrity seal',{exact:true}).waitFor();
 const state=await (await context.request.get('http://127.0.0.1:3000/api/service/ui/watch')).json();
 assert(state.enabled&&state.state==='waiting_for_exports'&&state.received_devices.length===0&&state.last_run_id===null);
 assert.deepEqual(state.expected_devices,['water-field-01']);
 for(const width of [1440,390]){
   await page.setViewportSize({width,height:1000});
   await page.getByRole('heading',{name:'Keep checking as exports arrive',exact:true}).scrollIntoViewIfNeeded();
   await page.evaluate(()=>document.fonts.ready);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   const text=await page.locator('body').innerText();assert(!text.includes('Ã')&&!text.includes('Â'));
   await page.screenshot({path:`${out}/collection-ready-${width}.png`,animations:'disabled'});
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 await fs.writeFile(`${out}/browser.json`,JSON.stringify({status:'passed',build:'production',browser:browser.version(),scope:'Empty actual collection project; monitor enabled and waiting for first export',expected_devices:state.expected_devices,received_devices:state.received_devices,last_run_id:state.last_run_id,widths:[1440,390],errors,external},null,2)+'\n');
 console.log('PASS production collection ready state, actual connection, clean text and no page overflow');
}finally{await browser.close();}
