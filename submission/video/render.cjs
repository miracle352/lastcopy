const {chromium}=require('playwright');const {spawn}=require('child_process');
const mode=process.argv[2]||'preview';
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()!=='log')errs.push(m.text())});
await p.goto('file://'+__dirname+'/film.html');await p.evaluate(()=>window.ready);await p.waitForTimeout(400);
const D=await p.evaluate(()=>DURATION);
if(mode==='info'){console.log(JSON.stringify(await p.evaluate(()=>({D:DURATION,S:START}))),errs);await b.close();return;}
if(mode==='preview'){const ts=process.argv.slice(3).map(Number);for(const t of ts){await p.evaluate(t=>seek(t),t);await p.screenshot({path:`pv_${t}.png`});}console.log('errs',errs);await b.close();return;}
const fps=30,from=Number(process.argv[3]||0),to=Number(process.argv[4]||D+1),out=process.argv[5]||'video.mp4';
const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','16','-preset','medium','-r','30',out],{stdio:['pipe','inherit','inherit']});
for(let i=Math.round(from*fps);i<Math.round(to*fps);i++){await p.evaluate(t=>seek(t),i/fps);const buf=await p.screenshot({type:'jpeg',quality:94});if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));}
ff.stdin.end();await new Promise(r=>ff.on('close',r));console.log('done',out,errs.slice(0,5));await b.close();})();
