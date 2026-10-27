const {chromium}=require('playwright');const {spawn}=require('child_process');
const mode=process.argv[2]||'preview';
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1350}});
const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()!=='log')errs.push(m.text())});
await p.goto('file://'+__dirname+'/film.html');await p.evaluate(()=>window.ready);await p.waitForTimeout(300);
if(mode==='preview'){const ts=process.argv.slice(3).map(Number);for(const t of ts){await p.evaluate(t=>seek(t),t);await p.screenshot({path:`prev_${t}.png`});}console.log('errs',errs);await b.close();return;}
const fps=30,D=await p.evaluate(()=>DURATION),N=Math.round(D*fps);
const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','17','-preset','medium','-movflags','+faststart','silent.mp4'],{stdio:['pipe','inherit','inherit']});
for(let i=0;i<N;i++){await p.evaluate(t=>seek(t),i/fps);const buf=await p.screenshot({type:'jpeg',quality:93});if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));}
ff.stdin.end();await new Promise(r=>ff.on('close',r));console.log('frames',N,'errs',errs);await b.close();})();
