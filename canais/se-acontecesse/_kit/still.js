// node still.js "[t1,t2,...]" prefixo [query]
const {chromium}=require('playwright'); const ts=JSON.parse(process.argv[2]); const pre=process.argv[3]||'s'; const q=process.argv[4]||'';
(async()=>{ const PORT=8800+Math.floor(Math.random()*90); await require('./serve.js')(PORT); const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const p=await b.newPage({viewport:{width:1080,height:1920}}); p.on('pageerror',e=>console.log('PAGE ERROR',e.message)); p.on('console',m=>{ if(m.type()==='error'||m.type()==='warning') console.log('C',m.text().slice(0,300)); });
const t0=Date.now(); await p.goto(`http://localhost:${PORT}/sim.html`+q); await p.waitForFunction(()=>window.READY,{timeout:300000}); console.log('load',Date.now()-t0);
require('fs').mkdirSync('out/st',{recursive:true});
for(const t of ts){ const a=Date.now(); await p.evaluate(t=>renderAt(t),t); await p.screenshot({path:`out/st/${pre}_${t}.jpg`,type:'jpeg',quality:85}); console.log(t,Date.now()-a,'ms'); }
await b.close(); process.exit(0); })();
