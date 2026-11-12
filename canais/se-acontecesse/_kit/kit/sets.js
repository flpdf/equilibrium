// cenários extras do kit: morro com casas (deslizamento), marginal (rio), represa, mercado
import * as THREE from 'three';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';
import {worldMat,rng} from './city.js';

function noise2(R){ const P=[]; for(let i=0;i<64;i++) P.push([R()*6.28,R()*0.05+0.01,R()*0.05+0.01,R()]); return (x,z)=>{ let s=0; for(const [a,fx,fz,w] of P) s+=Math.sin(x*fx+a)*Math.cos(z*fz+a*1.7)*w; return s/8; }; }
function canvasTex(w,h,draw){ const c=document.createElement('canvas'); c.width=w; c.height=h; draw(c.getContext('2d'),w,h); const t=new THREE.CanvasTexture(c); t.colorSpace=THREE.SRGBColorSpace; t.wrapS=t.wrapT=THREE.RepeatWrapping; t.anisotropy=8; return t; }

// ---------- MORRO: comunidade em encosta; deslizamento controlado por p (0..1) ----------
export function buildHill(origin=[4000,0,0]){
  const R=rng(31); const G=new THREE.Group(); G.position.set(...origin); const n=noise2(R);
  const slopeH=(x,z)=> Math.max(0,(z+20))*0.42 + n(x,z)*6 + Math.max(0,z-120)*0.1; // sobe para +z
  const geo=new THREE.PlaneGeometry(420,420,140,140); geo.rotateX(-Math.PI/2); const p=geo.attributes.position; const col=[];
  for(let i=0;i<p.count;i++){ const x=p.getX(i), z=p.getZ(i); const y=slopeH(x,z); p.setY(i,y); const g=0.3+0.2*Math.sin(x*0.07)*Math.cos(z*0.05);
    col.push(0.30+g*0.2,0.42+g*0.25,0.22); }
  geo.setAttribute('color',new THREE.Float32BufferAttribute(col,3)); geo.computeVertexNormals();
  const terrain=new THREE.Mesh(geo,worldMat(new THREE.MeshStandardMaterial({vertexColors:true,roughness:.95}),{wetGround:true})); terrain.receiveShadow=true; G.add(terrain);
  // casas
  const pal=[0xb5653f,0xa85a37,0x9a9c9e,0xd9c9a3,0xe7d27a,0x8fb7c9,0xc98a7a,0xb98f63,0xdedbd2];
  const houses=[]; const slide=[]; // casas na faixa do deslizamento
  const tankGeo=new THREE.CylinderGeometry(0.8,0.8,1.2,10);
  for(let z=-10; z<170; z+=7.5) for(let x=-140; x<140; x+=6.5+R()*2){ if(R()<0.12) continue;
    const w=4+R()*3, d=4+R()*3, h=3+Math.floor(R()*3)*2.8; const y=slopeH(x,z)-0.5; const inSlide=Math.abs(x-10)<26&&z>40&&z<150;
    houses.push({x,z,w,d,h,y,c:pal[Math.floor(R()*pal.length)],inSlide,tank:R()<0.75,rot:(R()-0.5)*0.08}); }
  const mk=(list)=>{ const byC={}; for(const H of list){ const g=new THREE.BoxGeometry(H.w,H.h,H.d); g.rotateY(H.rot); g.translate(H.x,H.y+H.h/2,H.z); (byC[H.c]=byC[H.c]||[]).push(g);
      // janelas escuras na frente (-z)
      const wg=new THREE.BoxGeometry(1.0,0.9,0.05); wg.translate(H.x-H.w*0.2,H.y+H.h-1.7,H.z-H.d/2-0.03); (byC['win']=byC['win']||[]).push(wg);
      if(H.tank){ const t=tankGeo.clone(); t.translate(H.x+H.w*0.25,H.y+H.h+0.6,H.z+H.d*0.2); (byC['tank']=byC['tank']||[]).push(t); } }
    const grp=new THREE.Group(); for(const k in byC){ const mat=k==='win'?new THREE.MeshStandardMaterial({color:0x22262b,roughness:.4}):k==='tank'?new THREE.MeshStandardMaterial({color:0x2e6fd0,roughness:.5}):new THREE.MeshStandardMaterial({color:+k,roughness:.9});
      const m=new THREE.Mesh(mergeGeometries(byC[k]),worldMat(mat)); m.castShadow=m.receiveShadow=true; grp.add(m); } return grp; };
  G.add(mk(houses.filter(h=>!h.inSlide)));
  // faixa que desliza: casas individuais
  const slideG=new THREE.Group(); G.add(slideG);
  for(const H of houses.filter(h=>h.inSlide)){ const g=mk([{...H,x:0,z:0,y:0,rot:0}]); g.position.set(H.x,H.y,H.z); g.rotation.y=H.rot; g.userData={x:H.x,y:H.y,z:H.z,r:R()}; slideG.add(g); }
  // lama: língua de terra marrom que desce
  const mudGeo=new THREE.PlaneGeometry(70,170,30,60); mudGeo.rotateX(-Math.PI/2);
  const mud=new THREE.Mesh(mudGeo,worldMat(new THREE.MeshStandardMaterial({color:0x6b4a2c,roughness:.7}),{wetGround:true})); mud.receiveShadow=true; G.add(mud);
  const mp=mudGeo.attributes.position; const base=mp.array.slice();
  G.userData={slideG,mud,slopeH,setSlide:(pp)=>{
    // pp 0..1: a encosta (z 40..150) escorrega para baixo (z menor), casas tombam
    for(const c of slideG.children){ const u=c.userData; const k=Math.max(0,Math.min(1,(pp*1.4-(u.z-40)/220)))*1.0; const dz=-k*(60+u.r*30);
      const nz=u.z+dz; const nx=u.x+(u.r-0.5)*k*10; c.position.set(nx,slopeH(nx,nz)-0.5-k*2.5,nz); c.rotation.set(-k*0.6*(0.5+u.r),u.r*k*1.2,(u.r-0.5)*k*0.8); }
    const front=150-pp*175;
    for(let i=0;i<mp.count;i++){ const u=(base[i*3]+35)/70, v=(base[i*3+2]+85)/170; const z=150-v*(150-front); const wdt=46+30*v; const x=10+(u-0.5)*wdt+Math.sin(v*9+u*3)*3;
      mp.setXYZ(i,x,slopeH(x,z)+0.35+Math.sin(u*20+v*14)*0.35*(1-Math.abs(u-0.5)*2),z); }
    mp.needsUpdate=true; mudGeo.computeVertexNormals(); mud.visible=pp>0.02; }};
  G.userData.setSlide(0);
  return G;
}

// ---------- MARGINAL: rio canalizado + pistas; nível da água controlado fora (flood próprio) ----------
export function buildRiver(origin=[-4000,0,0]){
  const R=rng(41); const G=new THREE.Group(); G.position.set(...origin);
  const Wr=46, Dp=6; // largura e profundidade do canal
  const conc=worldMat(new THREE.MeshStandardMaterial({color:0x9a958c,roughness:.9}));
  const L=3000;
  const bed=new THREE.Mesh(new THREE.PlaneGeometry(Wr,L),worldMat(new THREE.MeshStandardMaterial({color:0x4b4436,roughness:1}))); bed.rotation.x=-Math.PI/2; bed.position.y=-Dp; G.add(bed);
  for(const s of [-1,1]){ const w=new THREE.Mesh(new THREE.BoxGeometry(1.2,Dp+0.6,L),conc); w.position.set(s*(Wr/2+0.6),-Dp/2+0.3,0); w.receiveShadow=true; G.add(w);
    // talude inclinado do lado de dentro (concreto) já é a parede; pistas
    const asph=canvasTex(256,256,(g,w2,h)=>{ g.fillStyle='#55585e'; g.fillRect(0,0,w2,h); for(let i=0;i<4000;i++){ const v=70+Math.random()*40; g.fillStyle=`rgba(${v},${v},${v},.3)`; g.fillRect(Math.random()*w2,Math.random()*h,2,2);} });
    asph.repeat.set(4,L/12);
    const road=new THREE.Mesh(new THREE.PlaneGeometry(28,L),worldMat(new THREE.MeshStandardMaterial({map:asph,roughness:.9}),{wetGround:true})); road.rotation.x=-Math.PI/2; road.position.set(s*(Wr/2+1.2+14),0.01,0); road.receiveShadow=true; G.add(road);
    const lines=[]; for(let z=-L/2;z<L/2;z+=10) for(const lx of [-7,0,7]){ const g=new THREE.PlaneGeometry(0.18,4); g.rotateX(-Math.PI/2); g.translate(s*(Wr/2+1.2+14)+lx,0.03,z); lines.push(g); }
    const lm=new THREE.Mesh(mergeGeometries(lines),worldMat(new THREE.MeshStandardMaterial({color:0xeeeeee}),{wetGround:true})); G.add(lm);
    const gr=new THREE.Mesh(new THREE.BoxGeometry(0.3,0.8,L),worldMat(new THREE.MeshStandardMaterial({color:0xc9c9c9,roughness:.4,metalness:.6}))); gr.position.set(s*(Wr/2+1.5),0.4,0); G.add(gr);
    const grass=new THREE.Mesh(new THREE.PlaneGeometry(200,L),worldMat(new THREE.MeshStandardMaterial({color:0x4f7a3a,roughness:1}),{wetGround:true})); grass.rotation.x=-Math.PI/2; grass.position.set(s*(Wr/2+30+100),0,0); G.add(grass);
  }
  // prédios ao fundo (skyline simples)
  const sk=[]; for(let i=0;i<120;i++){ const s=R()<0.5?-1:1; const x=s*(Wr/2+60+R()*400), z=(R()-0.5)*2400; const w=15+R()*25, h=15+Math.pow(R(),1.5)*110; const g=new THREE.BoxGeometry(w,h,w); g.translate(x,h/2,z); sk.push(g); }
  const skm=new THREE.Mesh(mergeGeometries(sk),worldMat(new THREE.MeshStandardMaterial({color:0xb7b4ad,roughness:.9}))); skm.castShadow=true; G.add(skm);
  // carros nas pistas (instanced simples)
  const n=160; const body=new THREE.BoxGeometry(1.8,1.2,4.3); body.translate(0,0.7,0);
  const cars=new THREE.InstancedMesh(body,worldMat(new THREE.MeshPhysicalMaterial({roughness:.35,clearcoat:.8})),n); cars.castShadow=true; cars.frustumCulled=false;
  const cs=[0xf2f2f0,0xbfc3c7,0x1d1f22,0x8d9196,0xb3261e,0x234e8c]; const list=[];
  for(let i=0;i<n;i++){ const s=i%2?-1:1; const lane=[-10.5,-3.5,3.5,10.5][Math.floor(R()*4)]; list.push({x:s*(Wr/2+1.2+14)+lane,z0:(R()-0.5)*L,v:(10+R()*8)*(lane<0?1:-1),r:R()}); cars.setColorAt(i,new THREE.Color(cs[Math.floor(R()*cs.length)])); }
  G.add(cars);
  const _m=new THREE.Matrix4(),_q=new THREE.Quaternion(),_e=new THREE.Euler(),_p=new THREE.Vector3(),_s=new THREE.Vector3(1,1,1);
  G.userData={Wr,Dp,update:(t,{speed=1,water=-3}={})=>{ list.forEach((c,i)=>{ const sp=speed*(water>0.3?0.05:1); let z=c.z0+c.v*t*sp; z=((z+L/2)%L+L)%L-L/2;
      const fl=Math.max(0,water-0.6); _e.set(fl*0.05*Math.sin(t+i),c.v>0?0:Math.PI+(fl>0?(c.r-0.5)*fl*0.6:0),0); _q.setFromEuler(_e); _p.set(c.x+(fl>0?(c.r-0.5)*fl*2:0),Math.max(0,fl*0.6),z); _m.compose(_p,_q,_s); cars.setMatrixAt(i,_m); });
    cars.instanceMatrix.needsUpdate=true; }};
  return G;
}

// ---------- REPRESA: morros verdes, água clara, barragem; nível controlado fora ----------
export function buildDam(origin=[0,0,6000]){
  const R=rng(51); const G=new THREE.Group(); G.position.set(...origin); const n=noise2(R);
  const hgt=(x,z)=>{ const r=Math.hypot(x*0.8,z); return Math.max(-25,(r-180)*0.35)+n(x,z)*18+ Math.sin(x*0.013)*12; };
  const geo=new THREE.PlaneGeometry(1600,1600,160,160); geo.rotateX(-Math.PI/2); const p=geo.attributes.position; const col=[];
  for(let i=0;i<p.count;i++){ const x=p.getX(i), z=p.getZ(i); const y=hgt(x,z); p.setY(i,y);
    const dirt=y<2? 1:0; const g=0.5+0.5*Math.sin(x*0.03+z*0.02); col.push(dirt?0.55:0.22+0.08*g, dirt?0.40:0.38+0.1*g, dirt?0.28:0.16); }
  geo.setAttribute('color',new THREE.Float32BufferAttribute(col,3)); geo.computeVertexNormals();
  const ter=new THREE.Mesh(geo,worldMat(new THREE.MeshStandardMaterial({vertexColors:true,roughness:.95}))); ter.receiveShadow=true; ter.castShadow=true; G.add(ter);
  // barragem
  const dam=new THREE.Mesh(new THREE.BoxGeometry(220,32,14),worldMat(new THREE.MeshStandardMaterial({color:0xb9b5aa,roughness:.85}))); dam.position.set(0,-10,250); dam.castShadow=dam.receiveShadow=true; G.add(dam);
  // árvores (cones low-poly) nos morros
  const tg=[]; for(let i=0;i<900;i++){ const x=(R()-0.5)*1400, z=(R()-0.5)*1400; const y=hgt(x,z); if(y<6) continue; const c=new THREE.ConeGeometry(2.5+R()*2,7+R()*5,6); c.translate(x,y+4,z); tg.push(c); }
  const trees=new THREE.Mesh(mergeGeometries(tg),worldMat(new THREE.MeshStandardMaterial({color:0x2f5a2a,roughness:.9}))); trees.castShadow=true; G.add(trees);
  G.userData={hgt};
  return G;
}

// ---------- MERCADO: corredor com prateleiras; estoque controlado por fill (0..1) ----------
export function buildMarket(origin=[0,0,-6000]){
  const R=rng(61); const G=new THREE.Group(); G.position.set(...origin);
  const floorT=canvasTex(256,256,(g,w,h)=>{ g.fillStyle='#d9d6cf'; g.fillRect(0,0,w,h); g.strokeStyle='#b9b5ac'; g.lineWidth=3; g.strokeRect(0,0,w,h); }); floorT.repeat.set(30,60);
  const floor=new THREE.Mesh(new THREE.PlaneGeometry(40,80),worldMat(new THREE.MeshStandardMaterial({map:floorT,roughness:.25}),{wetGround:true})); floor.rotation.x=-Math.PI/2; floor.receiveShadow=true; G.add(floor);
  const ceil=new THREE.Mesh(new THREE.PlaneGeometry(40,80),new THREE.MeshStandardMaterial({color:0x8c8f93,side:THREE.DoubleSide})); ceil.rotation.x=Math.PI/2; ceil.position.y=6; G.add(ceil);
  for(const s of [-1,1]){ const w=new THREE.Mesh(new THREE.BoxGeometry(0.3,6,80),new THREE.MeshStandardMaterial({color:0xe9e6df})); w.position.set(s*20,3,0); G.add(w); }
  const back=new THREE.Mesh(new THREE.BoxGeometry(40,6,0.3),new THREE.MeshStandardMaterial({color:0xe9e6df})); back.position.set(0,3,40); G.add(back);
  // luminárias
  const lg=[]; for(let z=-35;z<40;z+=6) for(const x of [-6,6]){ const g=new THREE.BoxGeometry(0.4,0.08,4); g.translate(x,5.9,z); lg.push(g); }
  G.add(new THREE.Mesh(mergeGeometries(lg),new THREE.MeshBasicMaterial({color:0xf4f8ff})));
  const pl1=new THREE.PointLight(0xf2f5ff,250,40,1.6); pl1.position.set(0,5.5,-5); const pl2=pl1.clone(); pl2.position.set(0,5.5,15); G.add(pl1,pl2);
  // prateleiras (dois corredores)
  const sh=[]; const slots=[]; const shelfM=worldMat(new THREE.MeshStandardMaterial({color:0xd0d3d6,roughness:.5,metalness:.4}));
  for(const x of [-11,-3.5,3.5,11]){ const b=new THREE.BoxGeometry(1.2,2.2,50); b.translate(x,1.1,8); sh.push(b);
    for(let lv=0;lv<5;lv++){ const s=new THREE.BoxGeometry(1.6,0.05,50); s.translate(x,0.25+lv*0.48,8); sh.push(s);
      for(let z=-16.5;z<32.5;z+=0.42) for(const side of [-1,1]){ slots.push([x+side*0.55,0.25+lv*0.48,z,lv]); } } }
  const shm=new THREE.Mesh(mergeGeometries(sh),shelfM); shm.receiveShadow=true; G.add(shm);
  const prod=new THREE.InstancedMesh(new THREE.BoxGeometry(0.34,0.36,0.34),worldMat(new THREE.MeshStandardMaterial({roughness:.6})),slots.length);
  const pc=[0xd8392b,0xf0b429,0x2d7dd2,0x39a845,0xf28c28,0xffffff,0x8e44ad,0xe74c3c]; const keep=[];
  slots.forEach((s,i)=>{ prod.setColorAt(i,new THREE.Color(pc[Math.floor(R()*pc.length)])); keep.push(R()); });
  prod.frustumCulled=false; G.add(prod);
  // placa
  const signT=canvasTex(1024,256,(g,w,h)=>{ g.fillStyle='#f5f1e8'; g.fillRect(0,0,w,h); g.fillStyle='#c0392b'; g.fillRect(0,0,w,26); g.fillRect(0,h-26,w,26);
    g.fillStyle='#c0392b'; g.font='bold 92px Inter, Arial'; g.textAlign='center'; g.fillText('SEM REPOSIÇÃO',w/2,h*0.52); g.fillStyle='#333'; g.font='600 44px Inter, Arial'; g.fillText('CEAGESP ALAGADA · SEM ENTREGAS',w/2,h*0.8); });
  const sign=new THREE.Mesh(new THREE.PlaneGeometry(4.8,1.2),new THREE.MeshStandardMaterial({map:signT,roughness:.7,emissive:0x222222})); sign.position.set(0,3.6,-8); sign.rotation.y=Math.PI; G.add(sign);
  const _m=new THREE.Matrix4();
  G.userData={setFill:(f)=>{ slots.forEach((s,i)=>{ const on=keep[i]<f; _m.makeTranslation(s[0],s[1]+0.2,s[2]); if(!on) _m.makeScale(0.0001,0.0001,0.0001); prod.setMatrixAt(i,_m); }); prod.instanceMatrix.needsUpdate=true; }, sign};
  G.userData.setFill(1);
  return G;
}
