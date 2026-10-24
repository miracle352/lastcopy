/** Real UI actions against actual local API. No successful response mocks. */
import {chromium} from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
const root=process.cwd(),out=path.join(root,'private/stage5/browser');
await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:1280,height:900},acceptDownloads:true});
const requests=[],errors=[],results=[];
await context.route('**/*',route=>{const u=new URL(route.request().url());if(['127.0.0.1','localhost'].includes(u.hostname))return route.continue();requests.push({external_blocked:u.origin});return route.abort();});
const page=await context.newPage();page.setDefaultTimeout(45000);
page.on('pageerror',e=>errors.push(e.message));
page.on('request',r=>{if(r.url().includes('/api/service'))requests.push({method:r.method(),path:new URL(r.url()).pathname});});
const base='http://127.0.0.1:3000';
const savedIndex=process.argv.indexOf('--verify-saved');
async function step(name,fn){if(savedIndex>=0&&!name.startsWith('Connected query,'))return;if(process.argv.includes('--connected-only')&&!/^(Connected|No credentials)/.test(name))return;const start=performance.now();await fn();results.push({name,status:'passed',elapsed_ms:Math.round(performance.now()-start)});console.log('PASS '+name);}
async function sample(which='media'){
  await page.goto(base+'/app?sample='+which);
  await page.getByRole('button',{name:'Open sample',exact:true}).click();
  await page.getByRole('heading',{name:'Ready to check these copies'}).waitFor();
  await page.getByRole('button',{name:'Run check',exact:true}).click();
  await page.waitForURL(/\/runs\/check-/);
  await page.getByRole('heading',{name:/Checked records/}).waitFor();
  return new URL(page.url()).pathname;
}
let samplePath,livePath;
try{
  if(savedIndex>=0){livePath=process.argv[savedIndex+1];const previous=JSON.parse(await fs.readFile(path.join(out,'failure.json'),'utf8'));assert.equal(previous.url,base+livePath);results.push(...previous.results);await page.goto(base+livePath);}
  await step('Introduction and actual offline sample',async()=>{
    await page.goto(base);await page.locator('main').getByRole('link',{name:'Check a sample',exact:true}).first().click();
    await page.getByRole('button',{name:'Open sample',exact:true}).click();
    await page.getByRole('button',{name:'Run check',exact:true}).click();
    await page.getByRole('heading',{name:'File missing on server',exact:true}).waitFor();
    samplePath=new URL(page.url()).pathname;
    assert.match(await page.locator('main').innerText(),/Sample · synthetic/);
    assert.match(await page.locator('.status-grid').innerText(),/Completed[\s\S]*Incomplete[\s\S]*No operation applied/);
  });
  await step('Evidence dialog, keyboard focus, original files and downloads',async()=>{
    const open=page.getByRole('button',{name:'Inspect evidence for record 1',exact:true});await open.focus();await page.keyboard.press('Enter');
    const dialog=page.getByRole('dialog');await dialog.waitFor();
    await dialog.getByRole('heading',{name:'Source files and original bytes'}).waitFor();
    assert.match(await dialog.innerText(),/Occurrence indices/);assert.match(await dialog.innerText(),/b\.bin/);
    await page.keyboard.press('Escape');await dialog.waitFor({state:'hidden'});assert.equal(await open.evaluate(e=>e===document.activeElement),true);
    for(const name of ['Plain-language report','Findings JSON','Redacted trace']){
      const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('link',{name,exact:true}).click()]);
      await download.saveAs(path.join(out,download.suggestedFilename()));
    }
    const report=await fs.readFile(path.join(out,'report.txt'),'utf8');assert.match(report,/MISSING_ATTACHMENT/);
  });
  await step('Persisted sample plan, bundle, explicit review and real offline readback comparison',async()=>{
    await page.getByRole('button',{name:'Prepare recovery bundle for record 1',exact:true}).click();
    await page.getByRole('heading',{name:'Review recovery',exact:true}).waitFor();
    const [bundle]=await Promise.all([page.waitForEvent('download'),page.getByRole('link',{name:'Download recovery bundle',exact:true}).click()]);
    await bundle.saveAs(path.join(out,'sample-recovery.zip'));
    await page.getByRole('checkbox',{name:/I reviewed the exact target/}).check();await page.getByRole('button',{name:'Confirm plan review',exact:true}).click();
    await page.getByText('Saved for this exact plan and target',{exact:false}).waitFor();
    await page.reload();await page.getByRole('button',{name:'Compare offline readback example',exact:true}).waitFor();
    assert.equal(await page.getByRole('button',{name:'Apply reviewed recovery',exact:true}).count(),0);
    await page.getByRole('button',{name:'Compare offline readback example',exact:true}).click();
    await page.getByRole('heading',{name:'Matching copies were verified.',exact:true}).waitFor();
    assert.match(await page.locator('main').innerText(),/No upload was performed/);
    await page.reload();await page.getByRole('link',{name:'Return to the original gaps and plan',exact:true}).click();
    await page.getByRole('heading',{name:'Review recovery',exact:true}).waitFor();
    await page.goBack();await page.getByRole('heading',{name:'Matching copies were verified.',exact:true}).waitFor();
  });
  await step('Export/history/conflict/stranded controls use actual comparator outputs',async()=>{
    const controls=[['export','Answers present; export omitted them'],['history','Original retained in history'],['conflict','Answers or files differ'],['stranded','Record missing in checked server scope']];
    for(const [which,title] of controls){await sample(which);await page.getByRole('heading',{name:title,exact:true}).first().waitFor();if(which==='stranded')assert.equal(await page.getByRole('heading',{name:title,exact:true}).count(),2);else assert.equal(await page.getByRole('button',{name:/Prepare recovery bundle for record/}).count(),0);}
  });
  await step('Mobile/tablet/narrow reflow and reduced-motion evidence dialog',async()=>{
    await page.goto(base+samplePath);await page.getByRole('heading',{name:'File missing on server',exact:true}).waitFor();
    for(const width of [390,768,1280]){await page.setViewportSize({width,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);await page.screenshot({path:path.join(out,`run-${width}.png`),fullPage:true});}
    await page.setViewportSize({width:640,height:450});await page.emulateMedia({reducedMotion:'reduce'});
    await page.getByRole('button',{name:'Inspect evidence for record 1',exact:true}).click();
    assert.equal(await page.getByRole('dialog').evaluate(e=>e.scrollWidth<=e.clientWidth),true);
    await page.keyboard.press('Escape');await page.setViewportSize({width:1280,height:900});
  });
  const setup=JSON.parse(await fs.readFile(path.join(out,'inputs.json'),'utf8'));
  await step('Real queued cancellation persists without preservation result',async()=>{
    const queued=JSON.parse(execFileSync(path.join(root,'.venv/Scripts/python.exe'),['-m','scripts.seed_stage5_browser','--queue-only'],{cwd:root,env:{...process.env,SAMPLE_MODE:'false',LASTCOPY_DATA_DIR:path.join(root,'private/stage5/ui')},encoding:'utf8',timeout:45000}));
    await page.goto(base+'/runs/'+queued.run_id);await page.getByRole('button',{name:'Cancel check',exact:true}).click();
    await page.getByText('Check cancelled.',{exact:false}).waitFor();await page.reload();await page.getByText('Check cancelled.',{exact:false}).waitFor();
    assert.equal(await page.getByRole('heading',{name:/Checked records/}).count(),0);
  });
  await step('Invalid file validation is actionable',async()=>{
    await page.goto(base+'/app?import=true');await page.locator('#device-files').setInputFiles(path.join(out,'invalid.zip'));
    await page.getByRole('alert').filter({hasText:/ZIP|archive/i}).waitFor();
  });
  await step('Connected browser import, explicit roster and actual Central capture',async()=>{
    await page.goto(base+'/app?import=true');await page.locator('#device-files').setInputFiles(path.join(out,'live-device.zip'));
    await page.getByText(setup.device_id,{exact:true}).first().waitFor();await page.locator('#roster').fill(setup.device_id);
    await page.getByRole('radio',{name:'Read configured Central test connection',exact:true}).check();
    await page.getByRole('button',{name:'Save inputs for later',exact:true}).click();
    await page.waitForURL(/inputs=inputs-/);await page.reload();
    await page.getByText(setup.device_id,{exact:true}).first().waitFor();
    assert.equal(await page.locator('#roster').inputValue(),setup.device_id);
    assert.equal(await page.getByRole('radio',{name:'Read configured Central test connection',exact:true}).isChecked(),true);
    await page.getByRole('checkbox',{name:'I reviewed the expected devices and this project/form scope.',exact:true}).check();
    await page.getByRole('button',{name:'Prepare check',exact:true}).click();await page.getByRole('heading',{name:'Ready to check these copies',exact:true}).waitFor({timeout:150000});
    await page.getByRole('button',{name:'Run check',exact:true}).click();await page.getByRole('heading',{name:'File missing on server',exact:true}).waitFor();
    livePath=new URL(page.url()).pathname;assert.match(await page.locator('main').innerText(),/Connected · configured test server/);
  });
  await step('Connected reviewed Apply, fresh readback and reload without duplicate work',async()=>{
    await page.getByRole('button',{name:'Prepare recovery bundle for record 1',exact:true}).click();
    await page.getByRole('heading',{name:'Review recovery',exact:true}).waitFor();
    assert.match(await page.locator('.recovery-review').innerText(),new RegExp('Project '+setup.target.project_id));
    await page.getByRole('checkbox',{name:/I reviewed the exact target/}).check();await page.getByRole('button',{name:'Confirm plan review',exact:true}).click();
    await page.getByRole('button',{name:'Read server before Apply',exact:true}).waitFor();
    assert.equal(await page.getByRole('button',{name:'Apply reviewed recovery',exact:true}).isDisabled(),true);
    await page.getByRole('button',{name:'Read server before Apply',exact:true}).click();
    await page.waitForFunction(()=>{const b=Array.from(document.querySelectorAll('button')).find(b=>b.textContent==='Apply reviewed recovery');return b&&!b.disabled;},null,{timeout:150000});
    await page.reload();await page.getByRole('heading',{name:'Review recovery',exact:true}).waitFor();
    assert.equal(await page.getByRole('button',{name:'Apply reviewed recovery',exact:true}).isDisabled(),true);
    await page.getByRole('button',{name:'Read server before Apply',exact:true}).click();
    await page.waitForFunction(()=>{const b=Array.from(document.querySelectorAll('button')).find(b=>b.textContent==='Apply reviewed recovery');return b&&!b.disabled;},null,{timeout:150000});
    // Lose only the browser acknowledgement after the REAL HTTP request finishes.
    // This is a transport-failure control, never a mocked successful response.
    await page.route('**/api/service/recovery/plans/*/apply',async route=>{await route.fetch({timeout:300000});await route.abort();},{times:1});
    await page.getByRole('button',{name:'Apply reviewed recovery',exact:true}).click();
    await page.getByRole('heading',{name:'Matching copies were verified.',exact:true}).waitFor({timeout:300000});
    await page.reload();await page.getByText('No additional upload is needed.',{exact:false}).waitFor();
    assert.equal(await page.getByRole('button',{name:'Apply reviewed recovery',exact:true}).count(),0);
    const view=await (await context.request.get(base+'/api/service/ui'+livePath)).json();
    assert.equal(view.plans[0].events.filter(e=>e.state==='write_intent').length,1);
    assert.equal(view.current_report.findings[0].verdict,'PRESERVED');
    await page.getByRole('button',{name:'Inspect evidence for record 1',exact:true}).click();await page.getByRole('dialog').getByRole('heading',{name:'Source files and original bytes'}).waitFor();await page.keyboard.press('Escape');
    await fs.writeFile(path.join(out,'connected-result.json'),JSON.stringify(view,null,2));
  });
  await step('No credentials in browser storage; saved check remains navigable',async()=>{
    assert.deepEqual(await page.evaluate(()=>({local:Object.keys(localStorage),session:Object.keys(sessionStorage)})),{local:[],session:[]});
    await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Saved checks',exact:true}).click();await page.getByRole('heading',{name:'Saved checks',exact:true}).waitFor();
    await page.getByRole('link',{name:livePath.split('/').pop(),exact:true}).click();await page.getByRole('heading',{name:'Matching copies were verified.',exact:true}).waitFor();
    assert.equal(errors.length,0);
  });
  await step('Connected query, World Model and actual Nightshift investigation stay separate from preservation',async()=>{
    let view;const deadline=Date.now()+340000;
    do{view=await (await context.request.get(base+'/api/service/ui'+livePath)).json();if(view.investigation&&!['queued','running'].includes(view.investigation.state))break;await new Promise(resolve=>setTimeout(resolve,800));}while(Date.now()<deadline);
    const inv=view.investigation;
    assert.equal(inv.state,'completed',inv.error??'Connected worker failed');
    assert(inv.events.filter(e=>e.kind==='query'&&e.provider==='zetaris').length>=4);
    assert(inv.events.some(e=>e.kind==='graph_read'));
    assert(inv.events.some(e=>e.kind==='model'&&typeof e.actual_serving_model==='string'));
    assert(inv.result.provider_calls>0);
    assert.equal(view.current_report.findings[0].verdict,'PRESERVED');
    assert.equal(inv.result.report.findings[0].verdict,'MISSING_ATTACHMENT');
    await page.reload();await page.getByRole('heading',{name:'Matching copies were verified.',exact:true}).waitFor();
    await page.locator('main > details > summary').filter({hasText:'Evidence / Technical details'}).click();
    await page.getByRole('heading',{name:'Connected investigation: completed',exact:true}).waitFor();
    for(const name of ['Investigation record','Actual query rows and source references','World Model revisions']){
      const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('link',{name,exact:true}).click()]);
      await download.saveAs(path.join(out,download.suggestedFilename()));
    }
    await fs.writeFile(path.join(out,'connected-result.json'),JSON.stringify(view,null,2));
  });
  await fs.writeFile(path.join(root,'docs/verification/stage5-browser.json'),JSON.stringify({status:'passed',browser:browser.version(),base,results,sample_run:samplePath,connected_run:livePath,requests,errors,scope:'Actual browser/UI/API and real dedicated synthetic Central. No successful comparison/recovery responses were mocked.'},null,2)+'\n');
}catch(error){await page.screenshot({path:path.join(out,'failure.png'),fullPage:true}).catch(()=>{});await fs.writeFile(path.join(out,'failure.json'),JSON.stringify({message:String(error),url:page.url(),results,errors},null,2));throw error;}
finally{await browser.close();}
