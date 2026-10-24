/** Presentation regression + actual offline comparator. No live recovery writes. */
import {chromium} from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
const root=process.cwd(),out=path.resolve(root,process.env.LASTCOPY_BROWSER_OUTPUT??'private/stage6/final'),publicOut=path.resolve(root,process.env.LASTCOPY_BROWSER_EVIDENCE??'docs/verification/stage6');
await fs.mkdir(out,{recursive:true});await fs.mkdir(publicOut,{recursive:true});
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
const page=await context.newPage();page.setDefaultTimeout(45000);
const errors=[],requests=[],checks=[],shots=[],external=[];
page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{const u=new URL(r.url());if(u.pathname.startsWith('/api/service/'))requests.push({method:r.method(),path:u.pathname});});
await context.route('**/*',route=>{const u=new URL(route.request().url());if(['127.0.0.1','localhost'].includes(u.hostname))return route.continue();external.push(u.origin);return route.abort();});
const base='http://127.0.0.1:3000';
const hash=b=>createHash('sha256').update(b).digest('hex');
async function check(name,fn){const start=performance.now();await fn();checks.push({name,status:'passed',elapsed_ms:Math.round(performance.now()-start)});console.log('PASS '+name);}
async function fits(){return await page.evaluate(()=>({width:innerWidth,document:document.documentElement.scrollWidth,offenders:[...document.querySelectorAll('main *')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.right>innerWidth+1&&!e.closest('dialog:not([open])');}).map(e=>e.tagName+'.'+String(e.className)).slice(0,15)}));}
async function capture(name){await page.evaluate(()=>document.fonts.ready);const size=await fits();assert(size.document<=size.width,JSON.stringify(size));const file=name+'.png';const bytes=await page.screenshot({path:path.join(publicOut,file),animations:'disabled'});const again=await page.screenshot({animations:'disabled'});shots.push({name,file,sha256:hash(bytes),immediate_repeat_identical:hash(bytes)===hash(again),...size});await page.screenshot({path:path.join(out,name+'-full.png'),fullPage:true,animations:'disabled'});}
let originalRun,readbackRun;
try{
  await check('Useful static first frame with JavaScript disabled',async()=>{
    const nojs=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});const p=await nojs.newPage();await p.goto(base);await p.getByRole('heading',{name:'Bring every record home.',exact:true}).waitFor();assert.equal(await p.getByRole('link',{name:'Check a sample',exact:true}).first().isVisible(),true);assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);await p.screenshot({path:path.join(publicOut,'no-js-390.png'),fullPage:true});await nojs.close();
  });
  await check('Illustration explicitly labelled, user-controlled and independent of API',async()=>{
    await page.goto(base);await page.getByRole('heading',{name:'Bring every record home.',exact:true}).waitFor();
    const before=requests.length;await page.getByRole('button',{name:'Show illustrative recovery',exact:true}).click();assert.equal(await page.locator('.record-scene').getAttribute('data-illustration'),'readback');assert.match(await page.locator('figcaption').innerText(),/Illustrative data/);assert.equal(requests.length,before);await page.getByRole('button',{name:'Reset illustration',exact:true}).click();
  });
  await check('Ambient loops pause offscreen; scroll-linked story tracks native scrolling',async()=>{
    await page.locator('.record-scene').scrollIntoViewIfNeeded();await page.waitForFunction(()=>document.querySelector('.record-scene')?.classList.contains('in-viewport'));
    assert.equal(await page.locator('.travelling-document').evaluate(e=>getComputedStyle(e).animationPlayState),'running');
    await page.locator('#faq').scrollIntoViewIfNeeded();await page.waitForFunction(()=>!document.querySelector('.record-scene')?.classList.contains('in-viewport'));
    assert.equal(await page.locator('.travelling-document').evaluate(e=>getComputedStyle(e).animationPlayState),'paused');
    await page.locator('#why').scrollIntoViewIfNeeded();await page.waitForFunction(()=>{const value=parseFloat(getComputedStyle(document.querySelector('#why')).getPropertyValue('--story-progress'));return value>0&&value<1;});
    const story=await page.locator('#why').evaluate(e=>getComputedStyle(e).getPropertyValue('--story-progress'));assert(Number(story)>0&&Number(story)<1);
  });
  await check('Actual landing sample cases return independently checked verifier outputs',async()=>{
    await page.locator('#try-sample').scrollIntoViewIfNeeded();
    for(const [name,verdict] of [['A missing file','MISSING_ATTACHMENT'],['An incomplete export','EXPORT_VIEW_ONLY'],['An intentional edit','PRESERVED']]){
      await page.getByRole('button',{name:new RegExp(name)}).click();await page.getByRole('button',{name:'Run this sample',exact:true}).click();await page.locator('.sample-result').waitFor();
      const link=page.getByRole('link',{name:'Inspect the actual evidence',exact:false});const url=await link.getAttribute('href');
      const view=await (await context.request.get(base+'/api/service/ui'+url)).json();assert.equal(view.current_report.findings[0].verdict,verdict);assert.equal(view.current_report.provider_calls,0);assert.equal(view.current_report.recovery_executed,false);assert.equal(view.investigation,null);
      if(verdict==='MISSING_ATTACHMENT')originalRun=url;
    }
  });
  await check('Existing UI sample review, bundle and offline readback semantics remain intact',async()=>{
    await page.goto(base+originalRun);await page.getByRole('button',{name:'Prepare recovery bundle for record 1',exact:true}).click();await page.getByRole('heading',{name:'Review recovery',exact:true}).waitFor();
    await page.getByRole('checkbox',{name:/I reviewed the exact target/}).check();await page.getByRole('button',{name:'Confirm plan review',exact:true}).click();await page.getByRole('button',{name:'Compare offline readback example',exact:true}).waitFor();
    const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('link',{name:'Download recovery bundle',exact:true}).click()]);await download.saveAs(path.join(out,'recovery.zip'));
    assert.equal(await page.getByRole('button',{name:'Apply reviewed recovery',exact:true}).count(),0);
    await page.getByRole('button',{name:'Compare offline readback example',exact:true}).click();await page.getByRole('heading',{name:'Matching copies were verified.',exact:true}).waitFor();readbackRun=new URL(page.url()).pathname;assert.match(await page.locator('main').innerText(),/No upload was performed/);
    await page.reload();await page.getByRole('heading',{name:'Matching copies were verified.',exact:true}).waitFor();
  });
  await check('Screenshot matrix: home, real imports, saved run and modal at all requested widths',async()=>{
    for(const width of [360,390,768,1280,1440]){
      await page.setViewportSize({width,height:900});
      for(const [name,url] of [['home','/'],['imports','/app?import=true'],['run',originalRun]]){
        await page.goto(base+url);await page.locator('main h1').waitFor();if(name==='imports')await page.getByRole('radio',{name:'Read configured Central test connection',exact:true}).waitFor();if(name==='run')await page.getByRole('heading',{name:'Review recovery',exact:true}).waitFor();await capture(name+'-'+width);
      }
      const open=page.getByRole('button',{name:'Inspect evidence for record 1',exact:true});await open.focus();await page.keyboard.press('Enter');const dialog=page.getByRole('dialog');await dialog.getByRole('heading',{name:'Device and server values',exact:true}).waitFor();
      assert.equal(await dialog.evaluate(e=>e.scrollWidth<=e.clientWidth),true);
      assert.equal(await dialog.getByRole('button',{name:'Close evidence',exact:true}).evaluate(e=>{const a=e.getBoundingClientRect();return a.left>=0&&a.right<=innerWidth&&a.top>=0&&a.bottom<=innerHeight;}),true);
      await capture('evidence-'+width);await page.keyboard.press('Escape');await dialog.waitFor({state:'hidden'});assert.equal(await open.evaluate(e=>e===document.activeElement),true);
    }
  });
  await check('Reduced motion is a complete static presentation',async()=>{
    await page.emulateMedia({reducedMotion:'reduce'});await page.setViewportSize({width:1280,height:900});await page.goto(base);await page.locator('.record-scene').waitFor();
    assert.equal(await page.locator('.route-lit').evaluate(e=>getComputedStyle(e).display),'none');assert.equal(await page.locator('.hero h1').evaluate(e=>getComputedStyle(e).animationName),'none');assert.equal(await page.locator('.scene-canvas').evaluate(e=>getComputedStyle(e).transform),'none');
    await page.getByRole('button',{name:'Show illustrative recovery',exact:true}).click();assert.match(await page.locator('.unresolved-copy').innerText(),/Read back & compared/);await capture('reduced-motion-1280');
  });
  await check('200 percent zoom reflows landing, imports, saved run and accessible drawer',async()=>{
    await page.setViewportSize({width:1280,height:900});
    for(const [name,url] of [['home','/'],['imports','/app?import=true'],['run',originalRun]]){
      await page.goto(base+url);await page.locator('h1').waitFor();if(name==='run')await page.getByRole('heading',{name:'Review recovery',exact:true}).waitFor();await page.evaluate(()=>document.documentElement.style.zoom='2');await capture('zoom200-'+name);
      if(name==='run'){await page.getByRole('button',{name:'Inspect evidence for record 1',exact:true}).click();await page.getByRole('dialog').getByRole('heading',{name:'Device and server values',exact:true}).waitFor();assert.equal(await page.getByRole('dialog').evaluate(e=>e.scrollWidth<=e.clientWidth),true);await capture('zoom200-evidence');await page.keyboard.press('Escape');}
    }
  });
  await check('Keyboard focus, dropdown, FAQ and composed navigation remain usable',async()=>{
    await page.goto(base+'/app');await page.locator('#sample-case').selectOption('export');assert.equal(await page.locator('#sample-case').inputValue(),'export');
    await page.locator('#sample-case').focus();const focus=await page.locator('#sample-case').evaluate(e=>({style:getComputedStyle(e).outlineStyle,width:getComputedStyle(e).outlineWidth}));assert.notEqual(focus.style,'none');assert.notEqual(focus.width,'0px');
    await page.goto(base+'/#faq');const faq=page.locator('.faq-list details').first();await faq.locator('summary').focus();await page.keyboard.press('Enter');assert.equal(await faq.getAttribute('open'),'');
    await page.getByRole('link',{name:'Technical notes',exact:true}).click();await page.getByRole('heading',{name:'What stands behind a checked copy.',exact:true}).waitFor();
    await page.getByRole('link',{name:'LastCopy home',exact:true}).click();await page.getByRole('heading',{name:'Bring every record home.',exact:true}).waitFor();
    assert.equal(await page.locator('body > header').count(),1);assert.equal(await page.locator('body > footer').count(),1);assert.equal(errors.length,0);assert.equal(external.length,0);
    assert.equal(requests.some(r=>r.path.endsWith('/apply')||r.path.endsWith('/recheck')||r.path.endsWith('/recovery/capture')),false);
  });
  await fs.writeFile(path.join(publicOut,'browser.json'),JSON.stringify({status:'passed',browser:browser.version(),base,checks,shots,errors,external_requests:external,api_requests:requests,original_sample_run:originalRun,offline_readback_run:readbackRun,zoom_method:'CSS zoom 2 at 1280px, plus real narrow viewport reflow; not browser-menu zoom',scope:'Real local UI/API sample comparisons only; no connected provider calls or recovery writes'},null,2)+'\n');
}catch(e){await page.screenshot({path:path.join(out,'failure.png'),fullPage:true}).catch(()=>{});await fs.writeFile(path.join(out,'failure.json'),JSON.stringify({error:String(e),url:page.url(),checks,shots,errors},null,2));throw e;}finally{await browser.close();}
