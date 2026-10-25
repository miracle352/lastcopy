/** Product controls use Tab/Enter/Space/Escape only; actual API sample, no mocks. */
import {chromium} from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:390,height:844},acceptDownloads:true});page.setDefaultTimeout(45000);
const actions=[];
async function tabTo(target,name){await target.waitFor({state:'visible'});for(let i=0;i<120;i++){if(await target.evaluate(e=>e===document.activeElement)){actions.push(name);return;}await page.keyboard.press('Tab');}throw new Error('Keyboard could not reach '+name);}
async function activate(name){const b=page.getByRole('button',{name,exact:true});await tabTo(b,name);await page.keyboard.press('Enter');}
try{
 await page.goto('http://127.0.0.1:3000/app?sample=media');await activate('Open sample');await activate('Run check');await page.getByRole('heading',{name:/Checked records/}).waitFor();const original=page.url();
 await activate('Inspect evidence for record 1');const dialog=page.getByRole('dialog');await dialog.getByRole('heading',{name:'Device and server values',exact:true}).waitFor();
 for(let i=0;i<8;i++){await page.keyboard.press('Tab');assert(await page.evaluate(()=>!!document.activeElement.closest('dialog')));}
 await page.keyboard.press('Escape');assert(await page.getByRole('button',{name:'Inspect evidence for record 1',exact:true}).evaluate(e=>e===document.activeElement));
 await activate('Prepare recovery bundle for record 1');await page.getByRole('heading',{name:'Review recovery',exact:true}).waitFor();
 const review=page.getByRole('checkbox',{name:/I reviewed the exact target/});await tabTo(review,'Exact-target review');await page.keyboard.press('Space');assert(await review.isChecked());await activate('Confirm plan review');
 const bundle=page.getByRole('link',{name:'Download recovery bundle',exact:true});await tabTo(bundle,'Recovery bundle download');const download=page.waitForEvent('download');await page.keyboard.press('Enter');assert((await download).suggestedFilename().endsWith('.zip'));
 await activate('Compare offline readback example');await page.getByRole('heading',{name:'Matching copies were verified.',exact:true}).waitFor();const verified=page.url();await page.reload();await page.getByRole('heading',{name:'Matching copies were verified.',exact:true}).waitFor();
 const report=page.getByRole('link',{name:'Plain-language report',exact:true});await tabTo(report,'Plain-language report');const saved=page.waitForEvent('download');await page.keyboard.press('Enter');assert((await saved).suggestedFilename().endsWith('.txt'));
 await page.goBack();await page.getByRole('heading',{name:/Checked records/}).waitFor();assert.equal(new URL(page.url()).pathname,new URL(original).pathname);
 await fs.writeFile(process.env.LASTCOPY_KEYBOARD_OUTPUT??'docs/verification/stage7/keyboard.json',JSON.stringify({status:'passed',browser:browser.version(),width:390,actions,original,verified,dialog_focus_trap:true,escape_focus_return:true,refresh:true,back:true,mode:'sample',scope:'Actual product workflow controls used Tab/Enter/Space/Escape only. Initial navigation/reload/back are browser test setup; no pointer/focus injection or response mocks.'},null,2)+'\n');
 console.log('PASS Keyboard-only sample/evidence/review/bundle/readback/report with refresh and back');
}finally{await browser.close();}
