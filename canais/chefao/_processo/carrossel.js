// Carrossel "Chefão" (5 imagens 1080x1920) a partir de carrossel.json.
// uso: node carrossel.js <carrossel.json> <pasta_saida> [prefixo]
// Precisa do servidor http (python3 -m http.server 8790) rodando nesta pasta, com anims/ (e objetos/ se usar props).
// 1) fotografa o boneco 3D pelo template.html (mesmo motor dos vídeos, sem as camadas de texto)
// 2) monta os slides com carrossel.html e salva <prefixo>_1.jpg ... _5.jpg
const {chromium}=require('playwright'); const fs=require('fs'); const path=require('path');
const [,,cfgPath,outDir,prefix='carrossel']=process.argv; const port=process.env.PORT||8790;
const C=JSON.parse(fs.readFileSync(cfgPath,'utf8')); const id=(C.id||'c1').replace(/[^a-z0-9_-]/gi,'');
const work=`car_${id}`; fs.rmSync(work,{recursive:true,force:true}); fs.mkdirSync(`${work}/shots`,{recursive:true});
for(const d of ['template.html','node_modules','anims','objetos']) if(fs.existsSync(d)) fs.symlinkSync(path.resolve(d),`${work}/${d}`);
fs.writeFileSync(`${work}/carrossel.json`,JSON.stringify(C));
if(!Array.isArray(C.slides)||C.slides.length!==4) throw new Error('carrossel.json: "slides" precisa ter exatamente 4 itens (o 5º é o CTA)');

// episode.json mínimo para o template: o erro pedido ocupa o slot 1 (t=8.8 errado no fundo da repetição, t=12.0 certo)
function episode(o,err){ const e=Object.assign({label:'',check:'',view:'front',zone:['Hips'],deform:[]},err||{});
  return Object.assign({},o.cfg||{},{anim:o.anim,peak:o.peak||{bone:'Hips',metric:'minY'},watermark:'',topbar:{left:'',right:''},
    card:{name:[''],rows:[['','',''],['','',''],['','','']]},captions:Array(11).fill([['','']]),errors:[e,e,e],
    outro:{next:'',percent:40},cta:{cards:[['',''],['',''],['','']]}}); }
const jobs=[]; // {ep, t, file}
C.slides.forEach((s,i)=>{ const n=i+1;
  if(s.tipo==='erro'){ const ep=episode(s,s.erro); jobs.push({ep,t:8.8,file:`s${n}_errado.png`},{ep,t:12.0,file:`s${n}_certo.png`}); }
  else { const ep=episode(s,{view:s.view||'threequarter',zoom:s.zoom||1,deform:[],static:!!s.static});
    jobs.push({ep,t:s.pose==='repouso'?10.5:12.0,file:`s${n}.png`}); }});
{ const c=C.cta||{}; const ep=episode({anim:c.anim||'Fitness Idle.fbx',peak:c.peak,cfg:c.cfg},{view:c.view||'front',zoom:c.zoom||0.75,deform:[]});
  jobs.push({ep,t:12.0,file:'s5.png'}); }

(async()=>{ const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
  const p=await b.newPage({viewport:{width:1080,height:1920}}); let err=null;
  p.on('pageerror',e=>{err=e.message;console.log('PAGE ERROR:',e.message)});
  let last=null;
  for(const j of jobs){ const key=JSON.stringify(j.ep);
    if(key!==last){ fs.writeFileSync(`${work}/episode.json`,key); await p.goto(`http://localhost:${port}/${work}/template.html`);
      await p.waitForFunction(()=>window.READY,{timeout:120000}); await p.addStyleTag({content:'.layer{display:none!important}'}); last=key; }
    await p.evaluate(t=>window.renderAt(t),j.t);
    await p.screenshot({path:`${work}/shots/${j.file}`,clip:{x:0,y:660,width:1080,height:1060}}); }
  if(err) throw new Error('template falhou: '+err);
  // recorta cada foto no contorno do boneco (+ margem), para ele preencher o quadro do slide
  require('child_process').execFileSync('python3',['-c',`
import sys,glob
from PIL import Image,ImageChops
for f in glob.glob(sys.argv[1]+'/*.png'):
    im=Image.open(f).convert('RGB'); bg=Image.new('RGB',im.size,im.getpixel((5,5)))
    d=ImageChops.difference(im,bg).convert('L').point(lambda v:255 if v>28 else 0); b=d.getbbox()
    if not b: continue
    w,h=b[2]-b[0],b[3]-b[1]; m=int(max(w,h)*0.08)
    im.crop((max(0,b[0]-m),max(0,b[1]-m),min(im.width,b[2]+m),min(im.height,b[3]+m))).save(f)
`,`${work}/shots`]);
  fs.mkdirSync(outDir,{recursive:true});
  for(let i=1;i<=5;i++){ await p.goto(`http://localhost:${port}/carrossel.html?c=${work}&i=${i}`);
    await p.waitForFunction(()=>window.READY,{timeout:30000}); const o=await p.evaluate(()=>window.OVERFLOW);
    if(o&&o.length) console.log(`AVISO slide ${i}: texto estourando em ${o.join(', ')}`);
    await p.screenshot({path:`${outDir}/${prefix}_${i}.jpg`,type:'jpeg',quality:90}); console.log('ok',`${prefix}_${i}.jpg`); }
  await b.close(); })().catch(e=>{console.error(e.message);process.exit(1)});
