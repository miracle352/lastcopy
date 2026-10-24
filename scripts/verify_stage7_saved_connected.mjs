/** Read an already completed real check; never start providers, jobs or Apply. */
import {chromium} from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
const rid=JSON.parse(await fs.readFile('private/stage7/post-recovery-run.json','utf8')).run_id;
const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1280,height:900},acceptDownloads:true});page.setDefaultTimeout(45000);
const mutations=[];page.on('request',r=>{if(r.method()==='POST')mutations.push(new URL(r.url()).pathname);});
try{
 const base='http://127.0.0.1:3000';await page.goto(base+'/runs/'+rid);await page.getByRole('heading',{name:'Matching copies were verified.',exact:true}).waitFor();
 await page.locator('main > details > summary').filter({hasText:'Evidence / Technical details'}).click();await page.getByRole('heading',{name:'Connected investigation: completed',exact:true}).waitFor();
 const response=await page.request.get(base+'/api/service/ui/runs/'+rid,{maxRetries:2});assert(response.ok());const view=await response.json(),job=view.investigation;
 assert.equal(job.state,'completed');assert.equal(job.result.mode,'connected');assert.equal(view.current_report.findings[0].verdict,'PRESERVED');
 const queries=job.events.filter(e=>e.kind==='query'),models=job.events.filter(e=>e.kind==='model'),reads=job.events.filter(e=>e.kind==='graph_read');
 assert.equal(queries.length,4);assert.equal(models.length,3);assert(reads.length>=3);assert.equal(job.result.critique_rounds,2);
 assert(models.every(e=>e.serving_model_resolved&&e.actual_serving_model.toLowerCase().includes('nemotron')));
 const folder='docs/verification/stage7/post-recovery-connected';await fs.mkdir(folder,{recursive:true});const downloads={};
 for(const name of ['Investigation record','Actual query rows and source references','World Model revisions','Redacted trace']){
  const link=page.getByRole('link',{name,exact:true});const wait=page.waitForEvent('download');await link.click();const d=await wait;const file=path.join(folder,d.suggestedFilename());await d.saveAs(file);downloads[d.suggestedFilename()]=createHash('sha256').update(await fs.readFile(file)).digest('hex');
 }
 await page.reload();await page.getByRole('heading',{name:'Matching copies were verified.',exact:true}).waitFor();assert.deepEqual(mutations,[]);
 await fs.writeFile('docs/verification/stage7/connected-browser.json',JSON.stringify({status:'passed',browser:browser.version(),run_id:rid,mode:'connected',verdict:'PRESERVED',query_ids:queries.map(e=>e.query_id),graph_next_actions:reads.map(e=>e.next_action),actual_models:[...new Set(models.map(e=>e.actual_serving_model))],critique_rounds:job.result.critique_rounds,provider_calls:job.result.provider_calls,downloads,no_post_requests:true,reload:true,scope:'Browser read/download of a fresh real API-created post-recovery investigation; no writes. Separate earlier browser recovery attempts and their sponsor failures remain retained.'},null,2)+'\n');
 console.log('PASS Saved fresh Connected investigation, real query/model/graph receipts, downloads and reload without writes');
}finally{await browser.close();}
