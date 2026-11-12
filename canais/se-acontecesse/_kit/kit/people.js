// pessoas: personagens Mixamo (FBX) + animações (FBX sem pele, Y Bot), reaproveitadas por cena
import * as THREE from 'three';
import {FBXLoader} from 'three/addons/loaders/FBXLoader.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';
import {worldMat} from './city.js';

const enc=s=>encodeURI(s);
function shrink(tex,max=512){ const im=tex.image; if(!im||!im.width||im.width<=max) return tex; const c=document.createElement('canvas'); const k=max/Math.max(im.width,im.height); c.width=Math.round(im.width*k); c.height=Math.round(im.height*k);
  c.getContext('2d').drawImage(im,0,0,c.width,c.height); const t=new THREE.CanvasTexture(c); t.flipY=tex.flipY; t.wrapS=tex.wrapS; t.wrapT=tex.wrapT; tex.dispose(); return t; }
export async function createPeople(E,cfg={}){
  const L=new FBXLoader();
  const charNames=cfg.chars||['Kate','Remy','Megan','Leonard','Josh','Sophie','David','Jody','Brian','Olivia','Martha','Shannon'];
  const animNames=cfg.anims||['FemaleWalk','BriefcaseWalk','CarefulWalk','HoldingWalk','TextingWalkF','Running','BreathingIdle','LookingAround','PhoneTalkF','Terrified','SadIdle','WavingBoth','PointingForward','StandingIdle','Texting'];
  const base=cfg.dir||'assets/mixamo/';
  const chars={}; const anims={};
  const GL=new GLTFLoader();
  await Promise.all(charNames.map(async n=>{ try{ let o; try{ o=(await GL.loadAsync(enc(base+'glb/'+n+'.glb'))).scene; }catch(e){ o=await L.loadAsync(enc(base+'chars/'+n+'.fbx')); }
      o.traverse(c=>{ if(c.isMesh){ c.castShadow=true; c.receiveShadow=true; c.frustumCulled=false;
        const ms=(Array.isArray(c.material)?c.material:[c.material]).map(m=>{ const s=new THREE.MeshStandardMaterial({map:m.map||null,color:m.map?0xffffff:(m.color||new THREE.Color(0xcccccc)),roughness:.75,metalness:0,transparent:false}); if(s.map){ s.map=shrink(s.map); s.map.colorSpace=THREE.SRGBColorSpace; } return worldMat(s); });
        c.material=Array.isArray(c.material)?ms:ms[0]; } });
      let pre='mixamorig'; o.traverse(c=>{ if(c.isBone&&/Hips$/.test(c.name)) pre=c.name.slice(0,-4); }); o.userData.pre=pre;
      chars[n]=o; }catch(e){ console.warn('char',n,e.message); } }));
  await Promise.all(animNames.map(async n=>{ try{ const o=await L.loadAsync(enc(base+'anims/'+n+'.fbx')); const c=o.animations[0]; c.name=n;
      // remove deslocamento de raiz (x,z) para controlar a posição por fora
      for(const tr of c.tracks){ if(/Hips\.position$/.test(tr.name)){ const v=tr.values; const x0=v[0],z0=v[2]; for(let i=0;i<v.length;i+=3){ v[i]=x0; v[i+2]=z0; } } }
      anims[n]=c; }catch(e){ console.warn('anim',n,e.message); } }));
  const names=Object.keys(chars); if(!names.length) throw new Error('nenhum personagem');
  // pool de instâncias
  const pool=[]; const G=new THREE.Group(); E.scene.add(G);
  function inst(charName){ let p=pool.find(p=>!p.used&&p.char===charName); if(!p){ const src=chars[charName]||chars[names[0]]; const m=SkeletonUtils.clone(src); m.scale.setScalar(0.01); G.add(m);
      p={char:charName,m,mixer:new THREE.AnimationMixer(m),acts:{},used:false}; pool.push(p); } p.used=true; p.m.visible=true; return p; }
  const clipCache={};
  function clipFor(anim,charName){ const pre=chars[charName]?.userData.pre||'mixamorig'; if(pre==='mixamorig') return anims[anim]; const k=anim+'|'+pre; if(!clipCache[k]){ const c=anims[anim].clone(); for(const tr of c.tracks) tr.name=tr.name.replace(/^mixamorig/,pre); clipCache[k]=c; } return clipCache[k]; }
  function play(p,anim,t,speed=1){ if(!anims[anim]) return; const clip=clipFor(anim,p.char); for(const k in p.acts) if(k!==anim) p.acts[k].stop();
    let a=p.acts[anim]; if(!a){ a=p.mixer.clipAction(clip); p.acts[anim]=a; } a.play(); p.mixer.setTime(((t*speed)%clip.duration+clip.duration)%clip.duration); }
  const R=(i,k)=>{ const s=Math.sin(i*127.1+k*311.7)*43758.5453; return s-Math.floor(s); };
  // gera uma multidão de calçada perto da câmera (determinística)
  function crowd(spec,t){ const out=[]; const n=spec.n||10; const xs=spec.xs||[-15.5,-17]; const z0=spec.z0??-20, z1=spec.z1??80;
    const walks=spec.walks||['FemaleWalk','BriefcaseWalk','CarefulWalk','TextingWalkF']; const sp=spec.speed??1.3;
    for(let i=0;i<n;i++){ const dir=R(i,1)<0.5?1:-1; const x=xs[Math.floor(R(i,2)*xs.length)]+(R(i,3)-0.5)*0.8; const len=z1-z0; let z=z0+R(i,4)*len+dir*sp*(0.85+R(i,5)*0.3)*t; z=((z-z0)%len+len)%len+z0;
      const stand=spec.stand&&R(i,6)<spec.stand; const ch=(spec.chars||names)[Math.floor(R(i,7)*(spec.chars||names).length)];
      out.push({char:ch,anim:stand?(spec.idles||['BreathingIdle','LookingAround','PhoneTalkF','Texting'])[Math.floor(R(i,8)*4)]:walks[Math.floor(R(i,9)*walks.length)],pos:stand?[x,0.18,z0+R(i,4)*len]:[x,0.18,z],rot:stand?R(i,10)*6.28:(dir>0?0:Math.PI),speed:stand?1:1}); }
    return out; }
  return { chars:names, update:(t,b,lt,env)=>{ for(const p of pool){ p.used=false; p.m.visible=false; }
      const list=[]; const ps=b.people; if(!ps) return;
      for(const s of ps){ if(s.crowd) list.push(...crowd(s.crowd,t)); else list.push(s); }
      for(const s of list){ const p=inst(s.char); let pos=[...s.pos]; if(s.walk){ pos[0]+=s.walk[0]*lt; pos[2]+=s.walk[1]*lt; }
        if(env.waterY>0.2&&s.wade!==false){ /* andar dentro d'água: mais devagar */ }
        p.m.position.set(...pos); p.m.rotation.set(0,s.rot||0,0); play(p,s.anim,t+(s.ofs||0),s.speed||1); p.m.updateMatrixWorld(true); } } };
}
