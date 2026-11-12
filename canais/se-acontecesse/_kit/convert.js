const {chromium}=require('playwright'); const fs=require('fs');
(async()=>{ const PORT=8600+Math.floor(Math.random()*90); await require('./serve.js')(PORT); const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader']});
const p=await b.newPage(); p.on('pageerror',e=>console.log('ERR',e.message)); await p.goto(`http://localhost:${PORT}/convert.html`); await p.waitForFunction(()=>window.R);
fs.mkdirSync('assets/mixamo/glb',{recursive:true});
for(const n of process.argv.slice(2)){ try{ const s=await p.evaluate(n=>conv(n),n); fs.writeFileSync(`assets/mixamo/glb/${n}.glb`,Buffer.from(s,'base64')); console.log(n,fs.statSync(`assets/mixamo/glb/${n}.glb`).size); }catch(e){ console.log(n,'FAIL',e.message.slice(0,200)); } }
await b.close(); process.exit(0); })();
