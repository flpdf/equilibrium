// uso: node stills.js "[t1,t2,...]" [prefixo]  -> stills/<prefixo>_<t>.jpg + stills/<prefixo>_grid.jpg (via python)
const {chromium}=require('playwright');
const times=JSON.parse(process.argv[2]); const pre=process.argv[3]||'s'; const port=process.env.PORT||8790;
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const p=await b.newPage({viewport:{width:1080,height:1920}});
p.on('pageerror',e=>console.log('PAGE ERROR:',e.message));p.on('console',m=>{if(m.type()==='error')console.log('CONSOLE:',m.text())});
await p.goto(`http://localhost:${port}/template.html`);await p.waitForFunction(()=>window.READY,{timeout:120000});
console.log('rep:',JSON.stringify(await p.evaluate(()=>window.TP)));
require('fs').mkdirSync('stills',{recursive:true});
for(const t of times){await p.evaluate(t=>window.renderAt(t),t);await p.screenshot({path:`stills/${pre}_${t}.jpg`,type:'jpeg',quality:80});}
await b.close();})();
