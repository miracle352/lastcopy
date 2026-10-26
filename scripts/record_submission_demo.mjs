/** Actual public-browser recording. Pauses allow reading, never simulate reasoning. */
import {chromium} from 'playwright-core';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const origin=process.env.LASTCOPY_BROWSER_ORIGIN??'https://lastcopy-five.vercel.app';
const out='private/submission-build/video';await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true});const context=await browser.newContext({viewport:{width:1280,height:720},recordVideo:{dir:out,size:{width:1280,height:720}},acceptDownloads:true});
const captions=[],requests=[];let started=Date.now();
const page=await context.newPage();page.setDefaultTimeout(45000);
page.on('request',r=>{if(r.method()==='POST')requests.push(new URL(r.url()).pathname);});
async function hold(text,seconds=12){const begin=(Date.now()-started)/1000;await page.waitForTimeout(seconds*1000);captions.push({start:begin,end:(Date.now()-started)/1000,text});}
async function scroll(selector){await page.locator(selector).evaluate(e=>e.scrollIntoView({behavior:'smooth',block:'center'}));await page.waitForTimeout(1100);}
function time(value){const ms=Math.floor(value*1000);return `${String(Math.floor(ms/3600000)).padStart(2,'0')}:${String(Math.floor(ms/60000)%60).padStart(2,'0')}:${String(Math.floor(ms/1000)%60).padStart(2,'0')},${String(ms%1000).padStart(3,'0')}`;}
try{
 await page.goto(origin+'/');await page.evaluate(()=>document.fonts.ready);
 await hold('LastCopy checks whether field answers and photos reached the server. The originals stay unchanged.',10);
 await scroll('#why');await hold('The illustration follows your scroll. It explains a copy check; it does not claim a live recovery.',9);
 await page.goto(origin+'/demo');await page.getByRole('heading',{name:'Some records still need attention.'}).waitFor();
 await hold('Sample: authored synthetic files, compared by the real offline verifier. One referenced photo is missing.',12);
 await page.getByRole('button',{name:'Inspect evidence for record 1'}).click();await page.getByRole('dialog').getByRole('heading',{name:'Source files and original bytes'}).waitFor();
 await hold('Open the original file, exact XML occurrence and evidence receipt. File hashes are available for inspection.',14);
 await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'Review recovery files',exact:true}).click();await page.getByText('Exact example recovery plan',{exact:true}).waitFor();
 const download=page.waitForEvent('download');await page.getByRole('link',{name:'Download recovery bundle',exact:true}).click();await(await download).saveAs(path.join(out,'shown-example-bundle.zip'));
 await hold('Review the exact operation and untouched files. This Sample bundle does not upload anything.',12);
 await page.getByRole('button',{name:'Compare separate readback example',exact:true}).click();await page.getByRole('heading',{name:'The checked copies match.'}).waitFor();
 await hold('Sample readback uses a separate authored fixture. Its matching result is not presented as a real server write.',12);
 await page.goto(origin+'/technical');await scroll('.sponsor-replays');await page.getByRole('heading',{name:'The reviewer changed the next action.'}).waitFor();
 await hold('Replay: this captured Connected investigation made actual Zetaris queries and real Nightshift calls. Opening it makes no provider calls.',15);
 await scroll('.sponsor-replays article:first-of-type');
 await hold('The reviewer requested original XML. World Model reads changed the next action to export guidance: do not resubmit.',13);
 await page.locator('.sponsor-replays article').nth(1).evaluate(e=>e.scrollIntoView({behavior:'smooth',block:'center'}));
 await hold('The second captured investigation kept conflicting answers unresolved. It did not schedule an overwrite.',12);
 const proof=page.locator('#recovery-proof');if(await proof.count()){await scroll('#recovery-proof');await hold('Real Central recovery was checked again on 26 October. Fresh XML and media matched; repeat Apply made no upload or duplicate.',13);}
 await page.goto(origin+'/demo');await page.locator('input[name="example-case"][value="history"]').check();await page.locator('.demo-result h2').waitFor();
 await hold('Correct control: the original remains in history beside an intentional server edit. Recovery must preserve that edit.',12);
 await page.goto(origin+'/');await hold('Try LastCopy without an account at lastcopy-five.vercel.app/demo. The hosted core works while the PC is off; local sponsor runtime remains separate.',10);
 assert(requests.every(url=>url==='/api/demo/media/readback'),'Unexpected write route in public recording');
 const video=page.video();await context.close();const file=await video.path();await fs.copyFile(file,path.join(out,'lastcopy-demo.webm'));
 const srt=captions.map((c,i)=>`${i+1}\n${time(c.start)} --> ${time(c.end)}\n${c.text}\n`).join('\n');await fs.writeFile(path.join(out,'captions.srt'),srt,'utf8');
 await fs.writeFile(path.join(out,'receipt.json'),JSON.stringify({status:'recorded',origin,kind:'Actual browser recording; silent with captions',modes:['Sample','Replay'],new_connected_upload_performed:false,public_post_routes:requests,captions},null,2)+'\n');
 console.log('Recorded actual public workflow with truthful Sample/Replay captions.');
}finally{await context.close().catch(()=>{});await browser.close();}
