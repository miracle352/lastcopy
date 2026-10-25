/** Real deployed UI and API, no mocked results. No owner credentials required. */
import {chromium} from 'playwright-core';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const origin=process.env.LASTCOPY_BROWSER_ORIGIN??'https://app-18-141-113-136.sslip.io';
const output='docs/verification/public-beta/browser';await fs.mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true});const errors=[],foreign=[];
try{
  const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage();
  context.setDefaultTimeout(45000);context.setDefaultNavigationTimeout(60000);
  page.on('pageerror',e=>errors.push(e.message));
  await context.route('**/*',r=>{if(new URL(r.request().url()).origin===origin)return r.continue();foreign.push(new URL(r.request().url()).origin);return r.abort();});
  await page.goto(origin+'/demo');await page.getByRole('heading',{name:'Some records still need attention.'}).waitFor();
  assert.equal((await context.request.get(origin+'/api/service/ui/runs')).status(),401);
  assert(await page.getByText('Sample · example records',{exact:true}).isVisible());
  const evidenceButton=page.getByRole('button',{name:'Inspect evidence for record 1'});
  await evidenceButton.click();const dialog=page.getByRole('dialog');await dialog.getByRole('heading',{name:'Source files and original bytes'}).waitFor();
  await dialog.getByRole('button',{name:'Close evidence'}).focus();await page.keyboard.press('Escape');await dialog.waitFor({state:'hidden'});
  assert(await evidenceButton.evaluate(e=>document.activeElement===e));
  await page.getByRole('button',{name:'Review recovery files',exact:true}).click();await page.getByText('Exact example recovery plan',{exact:true}).waitFor();
  const [bundle]=await Promise.all([page.waitForEvent('download'),page.getByRole('link',{name:'Download recovery bundle',exact:true}).click()]);
  await bundle.saveAs(output+'/example-recovery.zip');assert.equal(await bundle.failure(),null);
  await page.getByRole('button',{name:'Compare separate readback example',exact:true}).click();
  await page.getByRole('heading',{name:'The checked copies match.'}).waitFor();
  await page.getByRole('button',{name:'Inspect evidence for record 1'}).click();await dialog.getByRole('heading',{name:'Source files and original bytes'}).waitFor();await page.keyboard.press('Escape');
  const report=await context.request.get(origin+'/api/demo/media/readback/downloads/report.json');assert(report.ok());
  assert.equal((await report.json()).preservation_outcome,'verified');
  const results=[];
  await page.reload();await page.locator('.demo-result h2').waitFor();
  for(const sample of ['media','stranded','export','history','conflict']){
    if(await page.getByLabel('Choose an example').inputValue()!==sample){
      await Promise.all([page.waitForResponse(r=>r.url()===origin+'/api/demo/'+sample&&r.status()===200),page.getByLabel('Choose an example').selectOption(sample)]);
    }
    await page.locator('.demo-result h2').waitFor();
    const response=await context.request.get(origin+'/api/demo/'+sample);assert(response.ok());const view=await response.json();
    assert.equal(view.manifest.mode,'sample');assert.equal(view.current_report.provider_calls,0);
    results.push({case:sample,verdicts:view.current_report.findings.map(f=>f.verdict),coverage:view.current_report.coverage.complete});
  }
  for(const width of [360,390,768,1280,1440]){
    await page.setViewportSize({width,height:900});await page.evaluate(()=>document.fonts.ready);
    await page.locator('.demo-downloads').scrollIntoViewIfNeeded();
    await page.evaluate(()=>{document.activeElement?.blur();window.scrollTo(0,0);});
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Page overflow at '+width);
    await page.screenshot({path:`${output}/demo-${width}.png`,fullPage:true,animations:'disabled'});
  }
  await page.setViewportSize({width:1280,height:900});await page.evaluate(()=>document.documentElement.style.zoom='2');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:output+'/demo-200.png',fullPage:true,animations:'disabled'});
  await page.evaluate(()=>document.documentElement.style.zoom='');await page.emulateMedia({reducedMotion:'reduce'});await page.reload();
  await page.locator('.demo-result h2').waitFor();await page.getByRole('link',{name:'Plain-language report',exact:true}).waitFor();
  await page.goto(origin+'/signup');await page.getByLabel('Email address').waitFor();await page.reload();await page.getByLabel('Email address').waitFor();
  await page.getByRole('button',{name:'Back to sign in',exact:true}).click();await page.getByRole('button',{name:'Forgot password?',exact:true}).click();
  assert(await page.getByRole('button',{name:'Reset your password',exact:true}).isVisible());
  await page.goto(origin+'/collect');await page.getByText('Open the form',{exact:true}).waitFor();
  await page.goto(origin+'/login');await page.getByText('Owner access',{exact:true}).click();await page.getByLabel('Owner passphrase').waitFor();
  assert.deepEqual(errors,[]);assert.deepEqual(foreign,[]);
  await fs.writeFile(output+'/browser.json',JSON.stringify({status:'passed',origin,browser:browser.version(),actual_production_api:true,no_account_required:true,
    external_browser_requests:foreign,checks:['All five actual sample cases','Evidence drawer and Escape focus return','Exact recovery plan','Recovery ZIP download','Separate readback comparison and matching report','Readback evidence resolves','Five responsive widths','200% CSS layout zoom','Reduced motion','Signup/reset empty states','Reload','Owner access separated','Collection instructions'],results},null,2)+'\n');
  console.log('PASS public production walkthrough, evidence, recovery bundle, readback, responsive layouts and account empty states');
}catch(e){await fs.writeFile(output+'/failure.json',JSON.stringify({status:'failed',message:e.message},null,2)+'\n');throw e;}finally{await browser.close();}
