/** Actual production UI over the running Central pilot; no response mocks. */
import {chromium} from 'playwright-core';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import path from 'node:path';
const base='http://127.0.0.1:3000',expected=process.env.LASTCOPY_EXPECTED_VERDICT??'PRESERVED',out=path.resolve(process.env.LASTCOPY_BROWSER_OUTPUT??'docs/verification/water-point');await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true});const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
const page=await context.newPage();page.setDefaultTimeout(60000);const errors=[],external=[],checks=[];
page.on('pageerror',e=>errors.push(e.message));
await context.route('**/*',r=>{const u=new URL(r.request().url());if(['localhost','127.0.0.1'].includes(u.hostname))return r.continue();external.push(u.origin);return r.abort();});
async function fit(){assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));}
async function shot(name){await page.evaluate(()=>document.fonts.ready);await fit();await page.screenshot({path:path.join(out,name+'.png'),animations:'disabled'});}
async function state(){return (await context.request.get(base+'/api/service/ui/watch')).json();}
try{
 await page.goto(base+'/app');await page.getByRole('heading',{name:'Keep checking as exports arrive',exact:true}).waitFor();await page.getByRole('button',{name:'Start automatic checks',exact:true}).waitFor();
 const before=await state();assert(before.configured&&!before.enabled);checks.push('Persisted paused monitor visible; previous report retained when present');
 await page.getByLabel('Device ZIPs (up to eight)',{exact:true}).setInputFiles('private/water-point/inbox-v2/water-emulator-v2.zip');
 await page.locator('li strong').filter({hasText:'water-emulator-01'}).waitFor();
 await page.getByRole('checkbox').check();await page.getByRole('button',{name:'Use these exports for automatic checks',exact:true}).click();
 await page.getByRole('button',{name:'Pause automatic checks',exact:true}).waitFor();
 const end=Date.now()+150000;let after;
 while(Date.now()<end){after=await state();if(after.last_run_id&&after.last_run_id!==before.last_run_id)break;await page.waitForTimeout(500);}
 assert(after.last_run_id!==before.last_run_id);checks.push('Uploaded registered export and reviewed roster start an actual automatic comparison without JSON editing');
 await page.getByRole('button',{name:'Pause automatic checks',exact:true}).click();await page.getByRole('button',{name:'Start automatic checks',exact:true}).waitFor();await page.reload();await page.getByRole('button',{name:'Start automatic checks',exact:true}).waitFor();
 const report=await (await context.request.get(base+'/api/service/ui/runs/'+after.last_run_id)).json();assert(report.automatic_check&&report.current_report.findings[0].verdict===expected);assert.equal(report.current_report.provider_calls,0);assert.equal(report.investigation,null);checks.push('Actual result '+expected+'; no model calls or recovery writes; pause survives reload');
 const title=expected==='PRESERVED'?'Matching copies were verified.':'1 record needs attention.';
 await page.getByRole('link',{name:'Open latest automatic report',exact:true}).click();await page.getByRole('heading',{name:title,exact:true}).waitFor();assert.equal(await page.getByRole('button',{name:/Prepare recovery bundle/}).count(),0);
 await page.getByRole('button',{name:'Inspect evidence for record 1',exact:true}).click();const dialog=page.getByRole('dialog');await dialog.getByRole('heading',{name:'Device and server values',exact:true}).waitFor();assert.match(await dialog.innerText(),/SYNTHETIC_TEST_v2_leaking_tap/);assert.match(await dialog.innerText(),/SYNTHETIC_TEST_v2_path_obstruction/);await page.keyboard.press('Escape');
 const download=page.waitForEvent('download');await page.getByRole('link',{name:'Plain-language report',exact:true}).click();assert((await download).suggestedFilename().endsWith('.txt'));await page.reload();await page.getByRole('heading',{name:title,exact:true}).waitFor();checks.push('Both original repeat values, evidence drawer, report download and saved-report refresh work');
 for(const width of [360,390,768,1280,1440]){await page.setViewportSize({width,height:900});await page.goto(base+'/app');await page.getByRole('heading',{name:'Keep checking as exports arrive',exact:true}).scrollIntoViewIfNeeded();await shot('monitor-'+width);}
 await page.setViewportSize({width:1280,height:900});await page.goto(base+'/app');await page.getByRole('heading',{name:'Keep checking as exports arrive',exact:true}).waitFor();await page.evaluate(()=>document.documentElement.style.zoom='2');await page.getByRole('heading',{name:'Keep checking as exports arrive',exact:true}).scrollIntoViewIfNeeded();await shot('monitor-zoom-200');
 await page.evaluate(()=>document.documentElement.style.zoom='');await page.emulateMedia({reducedMotion:'reduce'});await page.setViewportSize({width:390,height:844});await page.goto(base+'/app');await page.getByRole('heading',{name:'Keep checking as exports arrive',exact:true}).scrollIntoViewIfNeeded();await shot('monitor-reduced-motion-390');
 const button=page.getByRole('button',{name:'Start automatic checks',exact:true});await button.focus();await page.keyboard.press('Enter');await page.getByRole('button',{name:'Pause automatic checks',exact:true}).waitFor();await page.keyboard.press('Enter');await page.getByRole('button',{name:'Start automatic checks',exact:true}).waitFor();checks.push('Five responsive widths, 200% CSS layout zoom, reduced motion and keyboard start/pause');
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 await fs.writeFile(path.join(out,'browser.json'),JSON.stringify({status:'passed',build:'production',browser:browser.version(),checks,run_id:after.last_run_id,expected_verdict:expected,errors,external,limitations:['Chromium only','CSS layout zoom, not native browser zoom UI','Actual Central read with explicitly synthetic device evidence; not field visits','Device export transfer is operator/producer responsibility']},null,2)+'\n');console.log('PASS production automatic monitor workflow and responsive checks');
}finally{await browser.close();}
