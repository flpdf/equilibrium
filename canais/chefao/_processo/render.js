// uso: node render.js <inicio> <fim> <saida_sem_ext>
const {chromium}=require('playwright');const {spawn}=require('child_process');
const [a,b,outf]=[+process.argv[2],+process.argv[3],process.argv[4]]; const port=process.env.PORT||8790;
(async()=>{const br=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const p=await br.newPage({viewport:{width:1080,height:1920}});p.on('pageerror',e=>console.log('PAGE ERROR:',e.message));
await p.goto(`http://localhost:${port}/template.html`);await p.waitForFunction(()=>window.READY,{timeout:120000});
const ff=spawn('ffmpeg',['-y','-v','error','-f','image2pipe','-framerate','30','-c:v','mjpeg','-i','-','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-r','30',outf+'.part.mp4']);
for(let f=Math.round(a*30);f<Math.round(b*30);f++){await p.evaluate(t=>window.renderAt(t),f/30);const buf=await p.screenshot({type:'jpeg',quality:92});if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));}
ff.stdin.end();const code=await new Promise(r=>ff.on('close',r));await br.close();
if(code!==0){console.log('ffmpeg falhou',code);process.exit(1);} require('fs').renameSync(outf+'.part.mp4',outf+'.mp4');console.log('ok',outf);})();
