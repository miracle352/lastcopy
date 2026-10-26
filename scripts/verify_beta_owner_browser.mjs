/** Production owner pages; never sends another inference or recovery write. */
import {chromium} from 'playwright-core';import fs from 'node:fs/promises';import assert from 'node:assert/strict';
const origin='https://app-18-141-113-136.sslip.io',out='docs/verification/polish-risk/owner-browser';await fs.mkdir(out,{recursive:true});
const secrets=JSON.parse(await fs.readFile('private/cloud/access.json','utf8'));
const browser=await chromium.launch({headless:true});const errors=[];
try{
 const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage();context.setDefaultTimeout(45000);
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto(origin+'/login');assert.equal(await page.getByText('Owner access',{exact:true}).count(),0);assert.equal(await page.getByLabel('Password',{exact:true}).getAttribute('maxlength'),'512');await page.getByLabel('Password',{exact:true}).fill(secrets.owner_passphrase);await page.getByRole('button',{name:'Open records',exact:true}).click();
 await page.getByRole('button',{name:'Check connection',exact:true}).waitFor();
 for(const route of ['/app','/integrations','/signup']){
  await page.goto(origin+route);
  if(route==='/app')await page.getByRole('button',{name:'Check connection',exact:true}).waitFor();
  if(route==='/integrations'){
   await page.getByRole('heading',{name:'Last completed provider test'}).waitFor();
   assert.equal(await page.locator('#nvidia-key').inputValue(),'');
   assert(await page.getByRole('button',{name:'Test investigator and reviewer',exact:true}).isDisabled());
   assert(await page.getByText(/Connection-test allowance used/).isVisible());
   assert(await page.getByText(/Replay - saved test/).isVisible());
  }
  if(route==='/signup')await page.getByLabel('Email address').waitFor();
  for(const width of [360,390,768,1280,1440]){
   await page.setViewportSize({width,height:1000});await page.evaluate(()=>document.fonts.ready);
   await page.evaluate(()=>{document.activeElement?.blur();scrollTo(0,0);});await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),route+' overflow '+width);
   await page.screenshot({path:out+'/'+route.slice(1)+'-'+width+'.png',fullPage:true,animations:'disabled'});
  }
 }
 const rid='cloud-recovery-25dadf67ef5c4f58e9d13ce8';const response=await context.request.get(origin+'/api/service/ui/runs/'+rid);assert(response.ok());assert.equal((await response.json()).synthetic_source,true);
 await page.goto(origin+'/runs/'+rid);await page.getByRole('button',{name:'Inspect evidence for record 1'}).click();await page.getByRole('dialog').getByRole('heading',{name:'Source files and original bytes'}).waitFor();
 await page.setViewportSize({width:390,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.getByRole('dialog').screenshot({path:out+'/evidence-390.png',animations:'disabled'});await page.keyboard.press('Escape');
 await page.goto(origin+'/app');await page.getByRole('button',{name:'Check connection',exact:true}).waitFor();await page.getByRole('link',{name:'Check records',exact:true}).click();await page.waitForURL(/\/app\?import=true&new=/);await page.getByLabel('Device ZIPs (up to eight)').waitFor();
 await page.setViewportSize({width:1280,height:1000});await page.evaluate(()=>document.documentElement.style.zoom='2');assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.evaluate(()=>document.documentElement.style.zoom='');
 await page.emulateMedia({reducedMotion:'reduce'});await page.reload();await page.getByRole('button',{name:'Check connection',exact:true}).waitFor();
 assert(await page.locator('.site-header').isVisible());if(!await page.getByRole('button',{name:'Sign out',exact:true}).isVisible())await page.getByRole('button',{name:'Open navigation',exact:true}).click();await page.getByRole('button',{name:'Sign out',exact:true}).click();await page.getByLabel('Email address').waitFor();assert.equal((await context.request.get(origin+'/api/service/ui/runs')).status(),401);
 assert.deepEqual(errors,[]);await fs.writeFile(out+'/owner-browser.json',JSON.stringify({status:'passed',browser:browser.version(),origin,
 checks:['Actual owner sign-in/logout','Signup/app/integrations at five widths','Saved provider receipt restored as Replay','Key input empty after reload','Exhausted test disabled with actual allowance','Synthetic saved-run evidence drawer on mobile','Start another check remounts import flow','200% CSS zoom','Reduced motion'],model_calls:0,recovery_writes:0},null,2)+'\n');console.log('PASS actual production owner screens and saved provider state; no inference or recovery writes');
}finally{await browser.close();}
