// node render_sim.js <ini> <fim> <saida_sem_ext> [query]
const {chromium}=require('playwright');const {spawn}=require('child_process');
const [a,b,outf,q]=[+process.argv[2],+process.argv[3],process.argv[4],process.argv[5]||'']; const FPS=30;
(async()=>{const PORT=8900+Math.floor(Math.random()*90); await require('./serve.js')(PORT); const br=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const p=await br.newPage({viewport:{width:1080,height:1920}});p.on('pageerror',e=>console.log('PAGE ERROR:',e.message));
await p.goto(`http://localhost:${PORT}/sim.html${q}`);await p.waitForFunction(()=>window.READY,{timeout:300000});
const ff=spawn('ffmpeg',['-y','-v','error','-f','image2pipe','-framerate',String(FPS),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-r',String(FPS),outf+'.part.mp4']);
const f0=Math.round(a*FPS), f1=Math.round(b*FPS); const t0=Date.now();
for(let f=f0;f<f1;f++){await p.evaluate(t=>window.renderAt(t),f/FPS);const buf=await p.screenshot({type:'jpeg',quality:92});if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));
  if((f-f0)%60===0) console.log(outf,f,'/',f1,Math.round((Date.now()-t0)/1000)+'s'); }
ff.stdin.end();const code=await new Promise(r=>ff.on('close',r));await br.close();
if(code!==0){console.log('ffmpeg falhou',code);process.exit(1);} require('fs').renameSync(outf+'.part.mp4',outf+'.mp4');console.log('ok',outf);process.exit(0);})();
