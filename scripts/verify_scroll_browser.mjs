import {chromium} from 'playwright-core';import fs from 'node:fs/promises';import assert from 'node:assert/strict';
const origin=process.env.LASTCOPY_BROWSER_ORIGIN??'http://localhost:3000',out='docs/verification/polish-risk/motion-browser';await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true});try{
 const context=await browser.newContext({viewport:{width:1440,height:900}}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(origin+'/');await page.evaluate(()=>document.fonts.ready);await page.mouse.wheel(0,1);await page.waitForFunction(()=>document.querySelector('#why')?.classList.contains('reveal-pending'));
 assert.equal(await page.getByRole('button',{name:/pause|resume|play/i}).count(),0);
 await page.screenshot({path:out+'/landing-1440.png',animations:'disabled'});
 const states=[];
 for(const target of [.12,.48,.84]){
  await page.evaluate(p=>{const e=document.querySelector('.chapter-layout'),r=e.getBoundingClientRect();scrollTo({top:scrollY+r.top-innerHeight*.65+p*(r.height-innerHeight*.2),behavior:'instant'});},target);
  await page.waitForFunction(p=>{const e=document.querySelector('.chapter-layout');return Math.abs(Number(e.style.getPropertyValue('--story-progress'))-p)<.025;},target);
  states.push(await page.locator('.chapter-layout').getAttribute('data-story-step'));
  await page.locator('.chapter-art').screenshot({path:out+'/chapter-'+states.at(-1)+'.png'});
 }
 assert.deepEqual(states,['1','2','3']);
 await page.locator('#why').scrollIntoViewIfNeeded();await page.waitForFunction(()=>document.querySelector('#why')?.classList.contains('revealed'));
 await page.waitForFunction(()=>getComputedStyle(document.querySelector('#why')).opacity==='1');
 for(const route of ['/','/demo','/signup','/login']){
  await page.goto(origin+route);if(route==='/demo')await page.locator('.demo-result h2').waitFor();
  for(const width of [360,390,768,1000,1280,1440]){
   await page.setViewportSize({width,height:900});await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),route+' overflow '+width);
   await page.screenshot({path:out+'/'+(route.slice(1)||'home')+'-'+width+'.png',animations:'disabled'});
  }
 }
 await page.goto(origin+'/demo');await page.locator('.demo-result h2').waitFor();const next=page.locator('input[name="example-case"][value="stranded"]');await next.waitFor({state:'attached'});await page.locator('input[name="example-case"][value="media"]').focus();await page.keyboard.press('ArrowRight');await next.waitFor({state:'attached'});await page.waitForFunction(()=>document.querySelector('input[value="stranded"]')?.checked);await page.locator('.demo-result h2').waitFor();
 await page.setViewportSize({width:1280,height:900});await page.evaluate(()=>document.documentElement.style.zoom='2');assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.evaluate(()=>document.documentElement.style.zoom='');
 await page.emulateMedia({reducedMotion:'reduce'});await page.goto(origin+'/');await page.locator('#faq').scrollIntoViewIfNeeded();assert(await page.locator('#faq').evaluate(e=>getComputedStyle(e).opacity==='1'));assert.equal(await page.locator('.journey-original').first().evaluate(e=>getComputedStyle(e).transform),'none');
 const staticContext=await browser.newContext({javaScriptEnabled:false});const staticPage=await staticContext.newPage();await staticPage.goto(origin+'/');assert(await staticPage.getByRole('heading',{name:'Bring every record home.'}).isVisible());await staticContext.close();
 assert.deepEqual(errors,[]);await fs.writeFile(out+'/result.json',JSON.stringify({status:'passed',origin,browser:browser.version(),scroll_steps:states,widths:[360,390,768,1000,1280,1440],checks:['No timed carousel or pause/play','Actual scroll transforms and once-only reveals','Native keyboard radio group','200% CSS layout zoom','Reduced motion','Static no-JavaScript first frame'],provider_calls:0},null,2)+'\n');console.log('PASS scroll choreography, case choices, responsive production UI and reduced motion');
}finally{await browser.close();}
