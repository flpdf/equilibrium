// Kit "E Se Fosse Real" — cidade low-poly (unidades: metros). Determinístico por semente.
import * as THREE from 'three';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';

export function rng(seed){ let s=seed>>>0||1; return ()=>{ s^=s<<13; s>>>=0; s^=s>>17; s^=s<<5; s>>>=0; return (s%100000)/100000; }; }

// ---------- uniforms globais do mundo (chuva, água, noite, apagão) ----------
export const WU={ uTime:{value:0}, uWet:{value:0}, uWaterY:{value:-10}, uMud:{value:new THREE.Color(0x5a4a38)}, uNight:{value:0},
  uLit:{value:0.55}, uBlack:{value:0}, uBlackC:{value:new THREE.Vector2(0,0)}, uBlackR:{value:0}, uFlash:{value:0}, uSunTint:{value:1} };

const HASH=`
float h11(float n){ return fract(sin(n*127.1)*43758.5453); }
float h21(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
float vnoise(vec2 p){ vec2 i=floor(p),f=fract(p); f=f*f*(3.-2.*f); return mix(mix(h21(i),h21(i+vec2(1,0)),f.x),mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x),f.y); }`;

// injeta: umidade (chão escuro e brilhante), água barrenta acima do nível, janelas acesas à noite e apagão por região
export function worldMat(mat,{wetGround=false,windows=false,ground=false}={}){
  mat.onBeforeCompile=(sh)=>{ Object.assign(sh.uniforms,WU);
    sh.vertexShader=sh.vertexShader.replace('#include <common>','#include <common>\nvarying vec3 vWP; varying vec2 vUv2; attribute float bid;\nvarying float vBid;')
      .replace('#include <project_vertex>',`#include <project_vertex>
      { vec4 wp=vec4(transformed,1.0);
        #ifdef USE_INSTANCING
        wp=instanceMatrix*wp;
        #endif
        vWP=(modelMatrix*wp).xyz; }
      vUv2=uv; vBid=${windows?'bid':'0.0'};`);
    sh.fragmentShader=sh.fragmentShader.replace('#include <common>',`#include <common>
varying vec3 vWP; varying vec2 vUv2; varying float vBid;
uniform float uTime,uWet,uWaterY,uNight,uLit,uBlack,uBlackR,uFlash,uSunTint; uniform vec3 uMud; uniform vec2 uBlackC;`+HASH)
    .replace('#include <roughnessmap_fragment>',`#include <roughnessmap_fragment>
      ${wetGround?`{ float puddle=smoothstep(0.45,0.7,vnoise(vWP.xz*0.18)); float w=uWet*(0.55+0.45*puddle);
        roughnessFactor=mix(roughnessFactor,0.06,w); diffuseColor.rgb*=1.0-0.3*w; }`:''}`)
    .replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
      ${wetGround?`if(uWet>0.01){ vec2 q=vWP.xz*2.2; vec2 c=floor(q); vec2 f=fract(q)-0.5; float ph=fract(uTime*1.7+h21(c)); float r=length(f); float ring=sin((r-ph*0.5)*60.)*exp(-r*8.)*(1.-ph)*step(0.6,h21(c+7.));
        normal=normalize(normal+vec3(f.x,0.,f.y)*ring*0.6*uWet); }`:''}`)
    .replace('#include <emissivemap_fragment>',`#include <emissivemap_fragment>
      ${windows?`{ vec2 cell=floor(vUv2); vec2 f=fract(vUv2); float win=step(0.18,f.x)*step(f.x,0.82)*step(0.28,f.y)*step(f.y,0.86);
        float lit=step(h21(cell+vBid*97.13),uLit)*win;
        float dist=length(vWP.xz-uBlackC); float off=step(dist,uBlackR)*step(0.08,h11(vBid*13.7))+step(h11(vBid*3.1),uBlack);
        lit*=1.0-clamp(off,0.,1.);
        vec3 wc=mix(vec3(1.0,0.78,0.48),vec3(0.85,0.92,1.0),step(0.7,h21(cell*1.3+vBid)));
        totalEmissiveRadiance+=wc*lit*uNight*(0.55+0.5*h21(cell*2.7+vBid)); }`:''}`)
    .replace('#include <fog_fragment>',`{
      ${windows?'gl_FragColor.rgb*=mix(0.55,1.0,smoothstep(0.0,9.0,vWP.y));':''}
      // água barrenta: o que está abaixo do nível fica turvo
      float under=uWaterY-vWP.y; if(under>0.0){ float k=1.0-exp(-under*2.2); gl_FragColor.rgb=mix(gl_FragColor.rgb*vec3(0.75,0.68,0.55),uMud*(0.35+0.65*uSunTint),k); }
      gl_FragColor.rgb+=vec3(0.55,0.6,0.75)*uFlash*0.35;
    }
    #include <fog_fragment>`);
  };
  mat.customProgramCacheKey=()=>'wm'+(+wetGround)+(+windows)+(+ground);
  return mat;
}

// ---------- texturas de canvas ----------
function canvasTex(w,h,draw,repeat=true){ const c=document.createElement('canvas'); c.width=w; c.height=h; const g=c.getContext('2d'); draw(g,w,h);
  const t=new THREE.CanvasTexture(c); t.colorSpace=THREE.SRGBColorSpace; if(repeat){ t.wrapS=t.wrapT=THREE.RepeatWrapping; } t.anisotropy=8; return t; }
// célula de fachada = 1 janela (u=1 coluna, v=1 andar)
function facadeTex(kind){
  return canvasTex(128,128,(g,w,h)=>{
    const P={ glass:['#7e9ab5','#253a52','#3b5878'], beige:['#d9cbb0','#2f3640','#b9ab90'], white:['#e8e6e0','#30363e','#c9c6bf'], brick:['#a8644a','#2a2f36','#8a5038'], gray:['#9a9c9e','#2b3036','#7d8084'], pink:['#d7a9a0','#31363f','#b98d85'] }[kind];
    g.fillStyle=P[0]; g.fillRect(0,0,w,h);
    if(kind==='glass'){ const gr=g.createLinearGradient(0,0,0,h); gr.addColorStop(0,'#4f6f92'); gr.addColorStop(1,'#2b4664'); g.fillStyle=gr; g.fillRect(4,4,w-8,h-14);
      g.fillStyle='#9fb4c8'; g.fillRect(0,h-10,w,10); g.fillRect(0,0,4,h); return; }
    // janela
    g.fillStyle=P[1]; g.fillRect(w*0.18,h*0.14,w*0.64,h*0.58);
    const gr=g.createLinearGradient(0,h*0.14,w,h*0.72); gr.addColorStop(0,'rgba(140,170,200,.35)'); gr.addColorStop(1,'rgba(20,30,40,0)'); g.fillStyle=gr; g.fillRect(w*0.18,h*0.14,w*0.64,h*0.58);
    g.fillStyle=P[2]; g.fillRect(w*0.14,h*0.72,w*0.72,h*0.06); // peitoril
    g.fillStyle='rgba(0,0,0,.07)'; g.fillRect(0,h*0.94,w,h*0.06);
  });
}
// OBS: v=0 em baixo na textura do three (flipY) — a janela fica entre 0.28 e 0.86 de v (ver shader)

function boxUV(w,h,d,colW=2.6,floorH=3.1){ colW=boxUV.cw||colW; // caixa com UV em "células" (janela por coluna x andar)
  const g=new THREE.BoxGeometry(w,h,d); const uv=g.attributes.uv; const n=g.attributes.normal;
  for(let i=0;i<uv.count;i++){ const nx=Math.abs(n.getX(i)), ny=Math.abs(n.getY(i)); const u=uv.getX(i), v=uv.getY(i);
    if(ny>0.5){ uv.setXY(i,0.02,0.02); continue; } // topo: sem janela
    const span=nx>0.5?d:w; uv.setXY(i,u*Math.max(1,Math.round(span/colW)),v*Math.max(1,Math.round(h/floorH))); }
  return g; }

// ---------- cidade ----------
export function buildCity(opt={}){
  const R=rng(opt.seed||7); const G=new THREE.Group(); G.name='city';
  const N=opt.blocks||6, B=80, S=20, AV=34; // quarteirão, rua, avenida principal (no eixo z, x=0)
  const kinds=['glass','beige','white','brick','gray','pink'];
  const facMat={}; for(const k of kinds){ facMat[k]=worldMat(new THREE.MeshStandardMaterial({map:facadeTex(k),roughness:k==='glass'?0.25:0.85,metalness:k==='glass'?0.35:0.0,emissive:0x000000}),{windows:true}); }
  const roofMat=worldMat(new THREE.MeshStandardMaterial({color:0x8d8f91,roughness:.95}));
  const shopMat=worldMat(new THREE.MeshStandardMaterial({map:canvasTex(256,128,(g,w,h)=>{ g.fillStyle='#3a3f46'; g.fillRect(0,0,w,h); g.fillStyle='#d8d2c4'; g.fillRect(0,0,w,h*0.22);
     const cs=['#c0392b','#2e86c1','#f1c40f','#27ae60','#e67e22','#8e44ad']; g.fillStyle=cs[Math.floor(Math.random()*cs.length)]; g.fillRect(w*0.05,h*0.03,w*0.4,h*0.15);
     g.fillStyle='#9fb6c8'; g.fillRect(w*0.06,h*0.32,w*0.4,h*0.6); g.fillRect(w*0.54,h*0.32,w*0.4,h*0.6); g.fillStyle='rgba(255,255,255,.25)'; g.fillRect(w*0.06,h*0.32,w*0.4,h*0.1);}),roughness:.6}));
  const geos={}; for(const k of kinds) geos[k]=[]; const roofs=[], shops=[], tanks=[];
  const lots=[]; // para referência (câmera/efeitos)
  const span=(N*(B+S));
  for(let bx=-N;bx<N;bx++) for(let bz=-N;bz<N;bz++){
    // limites do quarteirão (avenida larga no x=0)
    let x0=bx*(B+S)+S/2, x1=x0+B; if(bx===0){ x0+= (AV-S)/2; } if(bx===-1){ x1-=(AV-S)/2; }
    const z0=bz*(B+S)+S/2, z1=z0+B; if(opt.skip&&opt.skip(x0,z0,x1,z1)) continue;
    const dist=Math.hypot((x0+x1)/2,(z0+z1)/2); const cityCore=Math.exp(-dist/650);
    // lotes 2x2 ou 3x2
    const nx=R()<0.5?2:3, nz=R()<0.5?2:3; const lw=(x1-x0)/nx, ld=(z1-z0)/nz;
    for(let i=0;i<nx;i++) for(let j=0;j<nz;j++){
      if(R()<0.06) continue; // lote vazio/praça
      const w=lw*(0.72+R()*0.22), d=ld*(0.72+R()*0.22); const cx=x0+lw*(i+0.5)+(R()-0.5)*(lw-w)*0.6, cz=z0+ld*(j+0.5)+(R()-0.5)*(ld-d)*0.6;
      let h=(R()<0.35?(8+R()*16):(14+Math.pow(R(),1.7)*115))*(0.6+cityCore*0.8); h=Math.max(9,Math.round(h/3.1)*3.1); boxUV.cw=2.1+R()*1.6; if((bx===0&&i===0)||(bx===-1&&i===nx-1)){ h=Math.min(h,Math.round((14+R()*(R()<0.25?70:26))/3.1)*3.1); }
      const k=kinds[Math.floor(R()*kinds.length)]; const bid=R();
      const addBox=(gw,gh,gd,px,py,pz,kind)=>{ const g=boxUV(gw,gh,gd); g.translate(px,py,pz); const a=new Float32Array(g.attributes.position.count).fill(bid); g.setAttribute('bid',new THREE.BufferAttribute(a,1)); geos[kind].push(g); };
      // térreo com lojas na beira da avenida/rua
      const shopH=4.5; const sg=new THREE.BoxGeometry(w,shopH,d); sg.translate(cx,shopH/2,cz); shops.push(sg);
      addBox(w,h,d,cx,shopH+h/2,cz,k);
      // recuo no topo (escalonado)
      if(h>40&&R()<0.5){ const h2=Math.round((8+R()*20)/3.1)*3.1; addBox(w*0.7,h2,d*0.7,cx,shopH+h+h2/2,cz,k); h+=h2; }
      const rg=new THREE.BoxGeometry(w*0.98,0.6,d*0.98); rg.translate(cx,shopH+h+0.3,cz); roofs.push(rg);
      if(R()<0.8){ const tg=new THREE.BoxGeometry(4+R()*3,3,4+R()*3); tg.translate(cx+(R()-0.5)*w*0.4,shopH+h+2,cz+(R()-0.5)*d*0.4); tanks.push(tg); } // caixa d'água
      lots.push({cx,cz,w,d,h:h+shopH,bid});
    }
  }
  for(const k of kinds){ if(!geos[k].length) continue; const m=new THREE.Mesh(mergeGeometries(geos[k]),facMat[k]); m.castShadow=m.receiveShadow=true; G.add(m); }
  const rm=new THREE.Mesh(mergeGeometries(roofs.concat(tanks)),roofMat); rm.castShadow=rm.receiveShadow=true; G.add(rm);
  const sm=new THREE.Mesh(mergeGeometries(shops),shopMat); sm.castShadow=sm.receiveShadow=true; G.add(sm);
  G.userData={lots,N,B,S,AV,span};
  return G;
}

// ---------- chão: asfalto, calçadas, faixas ----------
export function buildGround(city){
  const {N,B,S,AV}=city.userData; const G=new THREE.Group(); const size=N*(B+S)*2+400;
  const asph=canvasTex(512,512,(g,w,h)=>{ g.fillStyle='#5d6066'; g.fillRect(0,0,w,h); for(let i=0;i<9000;i++){ const v=75+Math.random()*45; g.fillStyle=`rgba(${v},${v},${v+4},.35)`; g.fillRect(Math.random()*w,Math.random()*h,2,2);} });
  asph.repeat.set(size/12,size/12);
  const road=new THREE.Mesh(new THREE.PlaneGeometry(size,size),worldMat(new THREE.MeshStandardMaterial({map:asph,roughness:.92}),{wetGround:true}));
  road.rotation.x=-Math.PI/2; road.receiveShadow=true; G.add(road);
  // calçadas (um bloco elevado por quarteirão, um pouco maior que o quarteirão)
  const swTex=canvasTex(256,256,(g,w,h)=>{ g.fillStyle='#b9b5ad'; g.fillRect(0,0,w,h); g.strokeStyle='rgba(80,80,80,.35)'; g.lineWidth=2; for(let i=0;i<=4;i++){ g.beginPath(); g.moveTo(i*64,0); g.lineTo(i*64,h); g.stroke(); g.beginPath(); g.moveTo(0,i*64); g.lineTo(w,i*64); g.stroke(); } });
  const swGeo=[];
  for(let bx=-N;bx<N;bx++) for(let bz=-N;bz<N;bz++){ let x0=bx*(B+S)+S/2, x1=x0+B; if(bx===0) x0+=(AV-S)/2; if(bx===-1) x1-=(AV-S)/2; const z0=bz*(B+S)+S/2, z1=z0+B;
    const pad=4; const g=new THREE.BoxGeometry(x1-x0+pad*2,0.18,z1-z0+pad*2); const uv=g.attributes.uv; for(let i=0;i<uv.count;i++) uv.setXY(i,uv.getX(i)*(x1-x0+8)/4,uv.getY(i)*(z1-z0+8)/4);
    g.translate((x0+x1)/2,0.09,(z0+z1)/2); swGeo.push(g); }
  swTex.wrapS=swTex.wrapT=THREE.RepeatWrapping;
  const sw=new THREE.Mesh(mergeGeometries(swGeo),worldMat(new THREE.MeshStandardMaterial({map:swTex,roughness:.85}),{wetGround:true})); sw.receiveShadow=true; G.add(sw);
  // faixas: tracejado central e faixas de pedestre perto da avenida
  const lineGeo=[]; const yl=0.02;
  for(let z=-N*(B+S);z<N*(B+S);z+=8){ for(const lx of [-AV/4,0,AV/4]){ const g=new THREE.PlaneGeometry(lx===0?0.25:0.15,lx===0?8:3.5); g.rotateX(-Math.PI/2); g.translate(lx,yl,z+(lx===0?4:0)); lineGeo.push(g);} }
  for(let bz=-N;bz<=N;bz++){ const zc=bz*(B+S); for(let k=-7;k<=7;k++){ const g=new THREE.PlaneGeometry(1.2,5); g.rotateX(-Math.PI/2); g.translate(k*2.2,yl,zc+S/2+5.5); lineGeo.push(g);} }
  const lines=new THREE.Mesh(mergeGeometries(lineGeo),worldMat(new THREE.MeshStandardMaterial({color:0xf2f0ea,roughness:.6}),{wetGround:true})); lines.receiveShadow=true; G.add(lines);
  return G;
}

// ---------- mobiliário: árvores cúbicas, postes, semáforos, fiação ----------
export function buildStreetProps(city,opt={}){
  const {N,B,S,AV}=city.userData; const R=rng(opt.seed||11); const G=new THREE.Group();
  const trunkM=worldMat(new THREE.MeshStandardMaterial({color:0x5a4634,roughness:.9}));
  const leafM=worldMat(new THREE.MeshStandardMaterial({color:0x3f7a35,roughness:.8}));
  const leafM2=worldMat(new THREE.MeshStandardMaterial({color:0x56913f,roughness:.8}));
  const poleM=worldMat(new THREE.MeshStandardMaterial({color:0x6f7378,roughness:.5,metalness:.4}));
  const trees=[]; const pts=[];
  for(let bz=-N;bz<N;bz++) for(const side of [-1,1]){ const x=side*(AV/2+1.6);
    for(let z=bz*(B+S)+S/2+6; z<bz*(B+S)+S/2+B-4; z+=9+R()*4){ if(R()<0.18) continue; pts.push([x+(R()-0.5)*0.4,z]); } }
  for(let bx=-N;bx<N;bx++) for(let bz=-N;bz<N;bz++){ if(R()<0.55) continue; const x0=bx*(B+S)+S/2, z0=bz*(B+S)+S/2; for(let k=0;k<4;k++) pts.push([x0+R()*B,z0-1.6]); }
  const tg=[],lg=[],lg2=[]; const treeList=[];
  for(const [x,z] of pts){ const s=0.8+R()*0.6, h=3+R()*1.5;
    const t=new THREE.BoxGeometry(0.3,h,0.3); t.translate(x,h/2+0.18,z); tg.push(t);
    const c1=new THREE.BoxGeometry(3.4*s,2.6*s,3.4*s); c1.translate(x,h+1.0*s,z); (R()<0.5?lg:lg2).push(c1);
    const c2=new THREE.BoxGeometry(2.2*s,1.6*s,2.2*s); c2.translate(x+(R()-0.5),h+2.6*s,z+(R()-0.5)); (R()<0.5?lg:lg2).push(c2);
    treeList.push({x,z,h:h+3*s}); }
  for(const [geo,mat] of [[tg,trunkM],[lg,leafM],[lg2,leafM2]]){ const m=new THREE.Mesh(mergeGeometries(geo),mat); m.castShadow=m.receiveShadow=true; G.add(m); }
  // postes de luz + fiação aérea (lado oeste da avenida)
  const pg=[]; const wires=[]; const lampPos=[];
  for(let z=-N*(B+S); z<N*(B+S); z+=30){ for(const side of [-1,1]){ const x=side*(AV/2+0.6);
    const p=new THREE.CylinderGeometry(0.13,0.18,9,6); p.translate(x,4.5,z); pg.push(p);
    const arm=new THREE.BoxGeometry(2.4,0.12,0.12); arm.translate(x-side*1.1,8.8,z); pg.push(arm);
    const lamp=new THREE.BoxGeometry(0.7,0.18,0.35); lamp.translate(x-side*2.2,8.7,z); pg.push(lamp); lampPos.push([x-side*2.2,8.55,z]);
    if(side<0){ const cr=new THREE.BoxGeometry(1.8,0.1,0.1); cr.translate(x,8.0,z); pg.push(cr); for(const dx of [-0.8,-0.25,0.3,0.8]) wires.push([x+dx,z]); } } }
  const pm=new THREE.Mesh(mergeGeometries(pg),poleM); pm.castShadow=true; G.add(pm);
  // fios: catenárias entre postes do lado oeste (tubos finos)
  const wireGeo=[]; const sag=0.7;
  for(const [wx,wz] of wires){ const pts=[]; for(let i=0;i<=8;i++){ const f=i/8; pts.push(new THREE.Vector3(wx,8.0-sag*4*f*(1-f),wz+f*30)); }
    wireGeo.push(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts),8,0.018,3,false)); }
  const wm=new THREE.Mesh(mergeGeometries(wireGeo),worldMat(new THREE.MeshStandardMaterial({color:0x1a1a1a,roughness:.6}))); G.add(wm);
  // semáforos nos cruzamentos da avenida
  const sem=[]; const semLights=[];
  for(let bz=-N;bz<=N;bz++){ const z=bz*(B+S)+S/2+2; for(const side of [-1,1]){ const x=side*(AV/2+0.8);
    const p=new THREE.CylinderGeometry(0.1,0.1,5.5,6); p.translate(x,2.75,z); sem.push(p);
    const box=new THREE.BoxGeometry(0.45,1.2,0.4); box.translate(x,5.0,z); sem.push(box); semLights.push([x,5.0,z]); } }
  const smm=new THREE.Mesh(mergeGeometries(sem),worldMat(new THREE.MeshStandardMaterial({color:0x2c2f33,roughness:.5}))); smm.castShadow=true; G.add(smm);
  // luzes (emissivas) dos postes e semáforos
  const bulbs=new THREE.InstancedMesh(new THREE.BoxGeometry(0.6,0.06,0.28),new THREE.MeshBasicMaterial({color:0xffd9a0}),lampPos.length);
  lampPos.forEach((p,i)=>bulbs.setMatrixAt(i,new THREE.Matrix4().makeTranslation(...p))); G.add(bulbs);
  const semB=new THREE.InstancedMesh(new THREE.SphereGeometry(0.13,8,6),new THREE.MeshBasicMaterial({color:0xffffff}),semLights.length);
  semLights.forEach((p,i)=>{ semB.setMatrixAt(i,new THREE.Matrix4().makeTranslation(p[0],p[1]+0.3,p[2]+(p[0]<0?0.21:-0.21))); semB.setColorAt(i,new THREE.Color(0x30ff60)); }); G.add(semB);
  G.userData={trees:treeList,bulbs,semB,lampPos};
  return G;
}

// ---------- carros e ônibus ----------
function carGeo(){ // carro sedã low-poly (comprimento no eixo z)
  const body=new THREE.BoxGeometry(1.8,0.62,4.3); body.translate(0,0.62,0);
  const cab=new THREE.BoxGeometry(1.6,0.58,2.2); const p=cab.attributes.position; for(let i=0;i<p.count;i++){ if(p.getY(i)>0){ p.setX(i,p.getX(i)*0.88); p.setZ(i,p.getZ(i)*0.78-0.1); } } cab.translate(0,1.2,-0.15);
  return {body,cab}; }
export function buildTraffic(opt={}){
  const R=rng(opt.seed||21); const G=new THREE.Group();
  const cols=[0xf2f2f0,0xf2f2f0,0xbfc3c7,0x1d1f22,0x8d9196,0xb3261e,0x234e8c,0xf2f2f0,0x2f3337,0x7a1f1f];
  const n=opt.count||70; const {body,cab}=carGeo();
  const paint=new THREE.MeshPhysicalMaterial({roughness:.35,metalness:.3,clearcoat:.8,clearcoatRoughness:.2});
  const glass=worldMat(new THREE.MeshStandardMaterial({color:0x1b232c,roughness:.1,metalness:.6}));
  const wheelM=worldMat(new THREE.MeshStandardMaterial({color:0x111111,roughness:.8}));
  const bodies=new THREE.InstancedMesh(body,worldMat(paint),n), cabs=new THREE.InstancedMesh(cab,glass,n);
  const wg=new THREE.CylinderGeometry(0.34,0.34,0.24,12); wg.rotateZ(Math.PI/2); const wheels=new THREE.InstancedMesh(wg,wheelM,n*4);
  const hl=new THREE.InstancedMesh(new THREE.BoxGeometry(1.5,0.12,0.05),new THREE.MeshBasicMaterial({color:0xfff2d0}),n);
  const tl=new THREE.InstancedMesh(new THREE.BoxGeometry(1.5,0.12,0.05),new THREE.MeshBasicMaterial({color:0xff2a1a}),n);
  for(const m of [bodies,cabs,wheels]){ m.castShadow=true; m.receiveShadow=true; m.frustumCulled=false; } hl.frustumCulled=tl.frustumCulled=false;
  const cars=[]; for(let i=0;i<n;i++){ const lane=[-3,-1,1,3][Math.floor(R()*4)]; const dir=lane<0?1:-1; const c=new THREE.Color(cols[Math.floor(R()*cols.length)]);
    bodies.setColorAt(i,c); cars.push({x:lane*3.6+(R()-0.5)*0.3,z0:R()*1200-600,v:(8+R()*6)*dir,dir,ph:R()}); }
  G.add(bodies,cabs,wheels,hl,tl);
  G.userData={cars,bodies,cabs,wheels,hl,tl,L:1200};
  return G;
}
const _m=new THREE.Matrix4(),_q=new THREE.Quaternion(),_s=new THREE.Vector3(1,1,1),_p=new THREE.Vector3(),_e=new THREE.Euler();
// t = tempo (s); speed = multiplicador (0 = parados); stall = carros param (alagamento); drift = carros boiando
export function updateTraffic(T,t,{speed=1,stallY=-1,float=0,lights=0,zc=0}={}){
  const U=T.userData;
  U.cars.forEach((c,i)=>{ let z=c.z0+c.v*t*speed; z=((z-zc+U.L/2)%U.L+U.L)%U.L-U.L/2+zc; const yaw=c.dir>0?0:Math.PI;
    const fl=float*(0.5+0.5*Math.sin(i*1.7)); const y=Math.max(0,stallY>0?Math.min(stallY-0.5,stallY*fl):0)+fl*Math.sin(t*1.3+i)*0.05;
    _e.set(fl*0.08*Math.sin(t+i),yaw+fl*0.5*Math.sin(i*2.3),fl*0.06*Math.cos(t*0.8+i)); _q.setFromEuler(_e);
    _p.set(c.x,y,z); _m.compose(_p,_q,_s); U.bodies.setMatrixAt(i,_m); U.cabs.setMatrixAt(i,_m);
    for(let k=0;k<4;k++){ const wx=k%2?0.85:-0.85, wz=k<2?1.35:-1.35; const w=new THREE.Vector3(wx,0.34,wz).applyQuaternion(_q).add(_p); _m.compose(w,_q,_s); U.wheels.setMatrixAt(i*4+k,_m); }
    const f=new THREE.Vector3(0,0.75,2.16).applyQuaternion(_q).add(_p); _m.compose(f,_q,_s.set(lights?1:0.0001,1,1)); U.hl.setMatrixAt(i,_m);
    const b=new THREE.Vector3(0,0.85,-2.16).applyQuaternion(_q).add(_p); _m.compose(b,_q,_s); U.tl.setMatrixAt(i,_m); _s.set(1,1,1); });
  for(const m of [U.bodies,U.cabs,U.wheels,U.hl,U.tl]) m.instanceMatrix.needsUpdate=true;
}
