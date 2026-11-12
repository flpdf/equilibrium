// motor: renderer + pós-processamento + mundo + ambiente
import * as THREE from 'three';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {ShaderPass} from 'three/addons/postprocessing/ShaderPass.js';
import {GTAOPass} from 'three/addons/postprocessing/GTAOPass.js';
import {WU,buildCity,buildGround,buildStreetProps,buildTraffic,updateTraffic} from './city.js';
import {SKY,buildSky,buildRain,buildFlood,buildBolt} from './weather.js';
import {buildHill,buildRiver,buildDam,buildMarket} from './sets.js';

export const W=1080, H=1920;
export function createEngine(opt={}){
  const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true,powerPreference:'high-performance'});
  const RS=opt.scale||1; const RW=Math.round(W*RS), RH=Math.round(H*RS); renderer.setPixelRatio(1); renderer.setSize(RW,RH,false); renderer.domElement.style.width=W+'px'; renderer.domElement.style.height=H+'px'; renderer.outputColorSpace=THREE.SRGBColorSpace; renderer.toneMapping=THREE.ACESFilmicToneMapping; renderer.toneMappingExposure=1.0;
  renderer.shadowMap.enabled=true; renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  document.getElementById('stage').appendChild(renderer.domElement);
  const scene=new THREE.Scene(); scene.fog=new THREE.Fog(0xb8c4d0,200,1800);
  const cam=new THREE.PerspectiveCamera(42,W/H,0.1,6000);
  const hemi=new THREE.HemisphereLight(0xcfe0ff,0x5b5348,1.1); scene.add(hemi);
  const sun=new THREE.DirectionalLight(0xfff1dc,3.0); sun.castShadow=true; sun.shadow.mapSize.set(opt.shadowMap||2048,opt.shadowMap||2048); sun.shadow.bias=-0.0004; sun.shadow.normalBias=0.04;
  Object.assign(sun.shadow.camera,{left:-120,right:120,top:120,bottom:-120,near:1,far:1200}); scene.add(sun,sun.target);
  const sky=buildSky(); scene.add(sky);
  const city=buildCity({seed:opt.seed||7,blocks:opt.blocks||6}); scene.add(city);
  const ground=buildGround(city); scene.add(ground);
  const props=buildStreetProps(city); scene.add(props);
  const traffic=buildTraffic({count:90}); scene.add(traffic);
  const rain=buildRain(12000); scene.add(rain);
  const flood=buildFlood(); scene.add(flood); scene.add(flood.userData.ref); scene.userData.rain=rain;
  const bolt=buildBolt(); scene.add(bolt);
  const hill=buildHill([4000,0,0]); scene.add(hill);
  const river=buildRiver([-4000,0,0]); scene.add(river);
  const riverWater=buildFlood(300,3000); riverWater.position.set(-4000,-3,0); riverWater.userData.ref.position.copy(riverWater.position); scene.add(riverWater,riverWater.userData.ref); riverWater.userData.U.uFlow.value.set(0,-3.5);
  const dam=buildDam([0,0,6000]); scene.add(dam);
  const damWater=buildFlood(1600); damWater.position.set(0,-8,6000); damWater.userData.ref.position.copy(damWater.position); damWater.userData.U.uClear.value=1; scene.add(damWater,damWater.userData.ref);
  const market=buildMarket([0,0,-6000]); scene.add(market);
  // pós
  const composer=new EffectComposer(renderer); composer.setPixelRatio(1); composer.setSize(RW,RH);
  composer.addPass(new RenderPass(scene,cam));
  let gtao=null; if(opt.ao!==false){ gtao=new GTAOPass(scene,cam,RW,RH); gtao.output=GTAOPass.OUTPUT.Default; gtao.updateGtaoMaterial({radius:2.5,distanceExponent:1.5,thickness:2,scale:1.2,samples:12}); gtao.blendIntensity=0.85; composer.addPass(gtao); }
  const bloom=new UnrealBloomPass(new THREE.Vector2(RW/2,RH/2),0.25,0.35,0.85); composer.addPass(bloom);
  // gradação final: vinheta + grão leve + leve desfoque de lente nas bordas (tilt)
  const grade=new ShaderPass({uniforms:{tDiffuse:{value:null},uTime:{value:0},uVig:{value:0.35},uSat:{value:1},uTint:{value:new THREE.Vector3(1,1,1)}},
    vertexShader:`varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
    fragmentShader:`uniform sampler2D tDiffuse; uniform float uTime,uVig,uSat; uniform vec3 uTint; varying vec2 vUv;
    float h(vec2 p){ return fract(sin(dot(p,vec2(12.9898,78.233))+uTime)*43758.5453); }
    void main(){ vec4 c=texture2D(tDiffuse,vUv); float l=dot(c.rgb,vec3(.299,.587,.114)); c.rgb=mix(vec3(l),c.rgb,uSat)*uTint;
      vec2 q=vUv-0.5; c.rgb*=1.-uVig*dot(q,q)*1.6; c.rgb+=(h(vUv*1000.)-0.5)*0.018; gl_FragColor=c; }`});
  composer.addPass(new OutputPass()); composer.addPass(grade);
  const pmrem=new THREE.PMREMGenerator(renderer); const envScene=new THREE.Scene(); const envSky=buildSky(); envSky.material=sky.material; envScene.add(envSky); const envCache={};
  const updateEnv=(st,nt)=>{ const k=Math.round(st*4)+'_'+Math.round(nt*4); if(!envCache[k]){ const s0=SKY.uStorm.value,n0=SKY.uNight.value; SKY.uStorm.value=Math.round(st*4)/4; SKY.uNight.value=Math.round(nt*4)/4; envCache[k]=pmrem.fromScene(envScene,0.04).texture; SKY.uStorm.value=s0; SKY.uNight.value=n0; } scene.environment=envCache[k]; };
  const E={THREE,renderer,scene,cam,hemi,sun,sky,city,ground,props,traffic,rain,flood,bolt,composer,gtao,bloom,grade,WU,SKY,hill,river,riverWater,dam,damWater,market};
  E.setWater=(m,y,on=true)=>{ m.visible=on; m.position.y=y; m.userData.ref.visible=on; m.userData.ref.position.y=y; };
  // ambiente: storm 0..1, rain 0..1, wet 0..1, waterY (m), night 0..1, lit (janelas), black (apagão global), flash
  E.setEnv=(e={})=>{
    const st=e.storm??0, nt=e.night??0;
    SKY.uStorm.value=st; SKY.uNight.value=nt; WU.uNight.value=nt; WU.uWet.value=e.wet??0; WU.uWaterY.value=e.waterY??-10; WU.uLit.value=e.lit??0.55; WU.uBlack.value=e.black??0;
    WU.uBlackR.value=e.blackR??0; if(e.blackC) WU.uBlackC.value.set(...e.blackC); WU.uFlash.value=e.flash??0; WU.uSunTint.value=1-nt*0.85;
    updateEnv(st,nt); const ei=e.envI??(0.5+0.4*(e.wet??0)); scene.traverse(o=>{ if(o.isMesh&&o.material&&'envMapIntensity' in o.material) o.material.envMapIntensity=ei; });
    rain.userData.U.uInt.value=e.rain??0; const ws=e.water||'city'; const wy=e.waterY??-10;
    E.setWater(flood,wy,ws==='city'&&wy>-1); E.setWater(riverWater,wy,ws==='river'); E.setWater(damWater,wy,ws==='dam');
    for(const f of [flood,riverWater,damWater]) f.userData.U.uRefK.value=e.refl??1;
    WU.uMud.value.set(ws==='dam'?0x2c5560:0x5a4a38); flood.userData.U.uRain.value=e.rain??0; flood.userData.U.uClear.value=e.clearWater??0;
    const dayK=1-nt; const sunK=(1-st*0.92)*dayK;
    sun.intensity=3.4*sunK; E.envI=(e.envI??0.55); sun.castShadow=sunK>0.05; hemi.intensity=(0.75-st*0.0)*(0.25+0.75*dayK)+ (e.flash??0)*3;
    hemi.color.setRGB(0.81-st*0.12,0.88-st*0.1,1.0-st*0.05); hemi.groundColor.setRGB(0.36-st*0.1,0.33-st*0.08,0.28-st*0.05);
    const fogC=new THREE.Color().setRGB(0.68-st*0.24,0.77-st*0.27,0.88-st*0.31).lerp(new THREE.Color(0.03,0.035,0.05),nt);
    scene.fog.color.copy(fogC); scene.fog.near=e.fogNear??(220-st*190); scene.fog.far=e.fogFar??(1800-st*1250);
    renderer.toneMappingExposure=(e.exposure??1)*(1-nt*0.1);
    grade.uniforms.uSat.value=e.sat??(1.12-st*0.32); grade.uniforms.uVig.value=0.35+st*0.15+nt*0.2;
    bloom.strength=0.15+nt*0.45; bloom.threshold=nt>0.3?0.7:0.9; bloom.enabled=nt>0.25;
    const lampsOn=e.lamps??(nt>0.3||st>0.6); props.userData.bulbs.visible=lampsOn&&!(e.black>0.9);
    E.carLights=e.carLights??(st>0.5||nt>0.3);
  };
  E.frame=(t,o={})=>{ WU.uTime.value=t; sky.position.copy(cam.position); SKY.uTime.value=t; grade.uniforms.uTime.value=t%10;
    const inCity=Math.abs(cam.position.x)<1500&&Math.abs(cam.position.z)<1500;
    const near=(g,r=2200)=>Math.hypot(cam.position.x-g.position.x,cam.position.z-g.position.z)<r;
    hill.visible=near(hill); river.visible=near(river); dam.visible=near(dam); market.visible=near(market,400);
    city.visible=ground.visible=props.visible=inCity||Math.hypot(cam.position.x,cam.position.z)<2600; traffic.visible=inCity; if(inCity) updateTraffic(traffic,t,{speed:o.traffic??1,stallY:o.stallY??-1,float:o.float??0,lights:E.carLights,zc:cam.position.z});
    rain.userData.U.uCam.value.copy(cam.position);
    // sombra acompanha o alvo da câmera
    const tg=o.shadowTarget||new THREE.Vector3(cam.position.x,0,cam.position.z);
    sun.target.position.copy(tg); sun.position.copy(tg).add(SKY.uSun.value.clone().multiplyScalar(500)); sun.target.updateMatrixWorld();
    const sc=o.shadowSize||120; Object.assign(sun.shadow.camera,{left:-sc,right:sc,top:sc,bottom:-sc}); sun.shadow.camera.updateProjectionMatrix();
    if(o.bolt){ bolt.visible=true; bolt.material.opacity=o.bolt; bolt.position.set(...(o.boltPos||[300,0,600])); } else bolt.visible=false;
    composer.render(); };
  E.look=(pos,tgt,fov=42)=>{ cam.position.set(...pos); cam.fov=fov; cam.updateProjectionMatrix(); cam.lookAt(...tgt); };
  return E;
}
