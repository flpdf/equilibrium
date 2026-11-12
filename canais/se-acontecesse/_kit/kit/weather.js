// céu (sol -> nublado -> tempestade -> noite), chuva, respingos, água de enchente, raio
import * as THREE from 'three';
import {WU} from './city.js';
import {Reflector} from 'three/addons/objects/Reflector.js';

const NOISE=`
float h21(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
float vn(vec2 p){ vec2 i=floor(p),f=fract(p); f=f*f*(3.-2.*f); return mix(mix(h21(i),h21(i+vec2(1,0)),f.x),mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x),f.y); }
float fbm(vec2 p){ float a=0.5,s=0.; for(int i=0;i<5;i++){ s+=a*vn(p); p*=2.03; a*=0.5; } return s; }`;

export const SKY={ uTime:{value:0}, uStorm:{value:0}, uNight:{value:0}, uSun:{value:new THREE.Vector3(-0.38,0.82,-0.42).normalize()}, uFlash:WU.uFlash, uCloudSpeed:{value:1} };
export function buildSky(){
  const m=new THREE.Mesh(new THREE.SphereGeometry(4000,48,24),new THREE.ShaderMaterial({side:THREE.BackSide,depthWrite:false,fog:false,uniforms:SKY,
    vertexShader:`varying vec3 vD; void main(){ vD=normalize(position); gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); gl_Position.z=gl_Position.w; }`,
    fragmentShader:`varying vec3 vD; uniform float uTime,uStorm,uNight,uFlash,uCloudSpeed; uniform vec3 uSun;`+NOISE+`
    void main(){ vec3 d=normalize(vD); float y=max(d.y,0.);
      vec3 clear=mix(vec3(0.66,0.79,0.94),vec3(0.20,0.45,0.84),pow(y,0.5));
      float sd=max(dot(d,uSun),0.); clear+=vec3(1.,0.9,0.7)*pow(sd,400.)*4.+vec3(1.,0.85,0.6)*pow(sd,8.)*0.25;
      vec2 cp=d.xz/(d.y+0.12)*1.4+vec2(uTime*0.012*uCloudSpeed,uTime*0.004*uCloudSpeed);
      float c=fbm(cp); float cov=mix(0.62,0.22,uStorm); float cl=smoothstep(cov,cov+0.25,c);
      vec3 cloudCol=mix(vec3(0.97,0.97,0.98),vec3(0.36,0.39,0.44),uStorm)*(0.85+0.3*fbm(cp*2.+3.));
      vec3 col=mix(clear,cloudCol,cl*(0.55+0.45*uStorm));
      vec3 storm=mix(vec3(0.42,0.45,0.50),vec3(0.24,0.27,0.31),pow(y,0.6))*(0.8+0.4*fbm(cp*0.7+uTime*0.02));
      col=mix(col,storm,smoothstep(0.55,1.,uStorm));
      vec3 night=mix(vec3(0.05,0.06,0.09),vec3(0.015,0.02,0.04),pow(y,0.5))+vec3(0.08,0.06,0.04)*(1.-y)*0.6;
      col=mix(col,night*(1.+uStorm*0.4*fbm(cp)),uNight);
      col+=vec3(0.75,0.8,1.)*uFlash*(0.6+0.4*fbm(cp*3.));
      col=mix(col,col*0.92,d.y<0.?1.:0.);
      gl_FragColor=vec4(col,1.);
      #include <colorspace_fragment>
    }`}));
  m.frustumCulled=false; m.renderOrder=-10; return m;
}

// chuva: gotas como traços verticais, numa caixa em volta da câmera (determinística pelo tempo)
export function buildRain(n=9000){
  const g=new THREE.InstancedBufferGeometry(); const base=new THREE.PlaneGeometry(1,1); g.index=base.index; g.attributes.position=base.attributes.position; g.attributes.uv=base.attributes.uv;
  const seed=new Float32Array(n*4); for(let i=0;i<n;i++){ seed[i*4]=Math.random(); seed[i*4+1]=Math.random(); seed[i*4+2]=Math.random(); seed[i*4+3]=Math.random(); }
  g.setAttribute('aSeed',new THREE.InstancedBufferAttribute(seed,4)); g.instanceCount=n;
  const U={uTime:WU.uTime,uCam:{value:new THREE.Vector3()},uInt:{value:0},uBox:{value:new THREE.Vector3(60,40,60)},uWind:{value:new THREE.Vector2(2.5,0.8)},uFlash:WU.uFlash,uNight:WU.uNight,uWaterY:WU.uWaterY};
  const m=new THREE.Mesh(g,new THREE.ShaderMaterial({uniforms:U,transparent:true,depthWrite:false,side:THREE.DoubleSide,blending:THREE.AdditiveBlending,
    vertexShader:`attribute vec4 aSeed; uniform float uTime,uInt,uWaterY; uniform vec3 uCam,uBox; uniform vec2 uWind; varying float vA; varying vec2 vUv;
    void main(){ vUv=uv; float sp=9.0+aSeed.w*4.0; vec3 p=vec3(aSeed.x,aSeed.y,aSeed.z)*uBox; p.y-=uTime*sp; p.xz+=uWind*uTime*(0.8+aSeed.w*0.4);
      vec3 rel=mod(p-uCam+uBox*0.5,uBox)-uBox*0.5; vec3 wp=uCam+rel; wp.y=uCam.y+rel.y;
      float vis=step(aSeed.w,uInt)*step(uWaterY,wp.y)*step(0.,wp.y);
      // billboard vertical alongado na direção da queda
      vec3 fall=normalize(vec3(uWind.x,-sp,uWind.y)); vec3 toCam=normalize(cameraPosition-wp); vec3 side=normalize(cross(fall,toCam));
      float len=0.8+aSeed.x*0.7; float wid=0.016+0.014*aSeed.y; float d=length(cameraPosition-wp); wid*=max(1.,d*0.04);
      wp+=side*position.x*wid - fall*position.y*len;
      vA=vis*(0.9-0.55*smoothstep(8.,55.,d))*smoothstep(0.5,2.5,d);
      gl_Position=projectionMatrix*viewMatrix*vec4(wp,1.); }`,
    fragmentShader:`varying float vA; varying vec2 vUv; uniform float uFlash,uNight; void main(){ float e=1.-abs(vUv.x-.5)*2.; float a=vA*e*smoothstep(0.,0.3,vUv.y)*(0.5+0.5*vUv.y);
      vec3 c=mix(vec3(0.75,0.8,0.86),vec3(0.35,0.4,0.5),uNight)+uFlash*0.6; gl_FragColor=vec4(c*a,a); }`}));
  m.frustumCulled=false; m.renderOrder=20; m.userData.U=U; return m;
}

// água de enchente: plano barrento com anéis de gota, reflexo do céu e espuma nas bordas
export function buildFlood(size=3000,sizeZ=size){
  const ref=new Reflector(new THREE.PlaneGeometry(size,sizeZ),{textureWidth:540,textureHeight:960,clipBias:0.02,multisample:0}); ref.material.colorWrite=false; ref.material.depthWrite=false; ref.rotation.x=-Math.PI/2; ref.renderOrder=4;
  const U={tRef:{value:ref.getRenderTarget().texture},uTexM:{value:ref.material.uniforms.textureMatrix.value},uRefK:{value:1},uTime:WU.uTime,uWaterY:WU.uWaterY,uRain:{value:0},uNight:WU.uNight,uFlash:WU.uFlash,uStorm:SKY.uStorm,uFlow:{value:new THREE.Vector2(0,0.4)},uClear:{value:0}};
  Object.assign(U,THREE.UniformsUtils.clone(THREE.UniformsLib.fog));
  const m=new THREE.Mesh(new THREE.PlaneGeometry(size,sizeZ,1,1),new THREE.ShaderMaterial({uniforms:U,transparent:true,depthWrite:true,
    vertexShader:`#include <fog_pars_vertex>
uniform mat4 uTexM; varying vec4 vRef; varying vec3 vW; void main(){ vRef=uTexM*vec4(position,1.); vec4 w=modelMatrix*vec4(position,1.); vW=w.xyz; vec4 mvPosition=viewMatrix*w; gl_Position=projectionMatrix*mvPosition;
#include <fog_vertex>
}`,
    fragmentShader:`#include <fog_pars_fragment>
uniform sampler2D tRef; uniform float uRefK; varying vec4 vRef; varying vec3 vW; uniform float uTime,uRain,uNight,uFlash,uStorm,uClear; uniform vec2 uFlow;`+NOISE+`
    void main(){ vec2 p=vW.xz; vec2 fl=p-uFlow*uTime;
      vec2 gr=vec2(vn(fl*0.35+uTime*0.2)-0.5,vn(fl.yx*0.35-uTime*0.17)-0.5)*0.35;
      // anéis de gota
      for(int k=0;k<2;k++){ vec2 q=p*(1.6+float(k)*1.3); vec2 c=floor(q); vec2 f=fract(q)-0.5; float ph=fract(uTime*(1.3+float(k)*0.4)+h21(c+float(k)*13.)); float r=length(f);
        float ring=sin((r-ph*0.45)*55.)*exp(-r*7.)*(1.-ph)*step(0.35,h21(c+float(k)*5.)); gr+=f*ring*1.4*uRain; }
      vec3 n=normalize(vec3(-gr.x,1.,-gr.y)); vec3 V=normalize(cameraPosition-vW);
      float fr=0.04+0.96*pow(1.-max(dot(n,V),0.),5.);
      vec3 R=reflect(-V,n); float ry=max(R.y,0.);
      vec3 sky=mix(mix(vec3(0.62,0.70,0.80),vec3(0.38,0.42,0.48),uStorm),vec3(0.03,0.04,0.06),uNight)*(0.85+0.3*ry)+uFlash*0.5;
      vec3 mud=mix(vec3(0.25,0.20,0.14),vec3(0.06,0.20,0.24),uClear)*(1.-0.75*uNight)*(0.85+0.3*vn(p*0.05));
      vec4 rp=vRef; rp.xy+=gr*rp.w*0.045; vec3 refl=texture2DProj(tRef,rp).rgb; sky=mix(sky,refl,uRefK);
      vec3 col=mix(mud,sky,clamp(fr*0.9+0.22,0.,1.));
      float foam=smoothstep(0.62,0.9,vn(fl*0.6))*0.15; col+=foam*(1.-uNight*0.8);
      gl_FragColor=vec4(col,0.93);
      #include <colorspace_fragment>
      #include <fog_fragment>
    }`,fog:true}));
  m.rotation.x=-Math.PI/2; m.userData.U=U; m.renderOrder=5; m.userData.ref=ref;
  const ob=ref.onBeforeRender; ref.onBeforeRender=function(r,s,c){ if(!m.visible||U.uRefK.value<=0) return; m.visible=false; const rv=s.userData.rain; if(rv) rv.visible=false; ob.call(ref,r,s,c); m.visible=true; if(rv) rv.visible=true; };
  return m;
}

// raio: linha quebrada brilhante
export function buildBolt(){
  const pts=[]; let x=0,y=600,z=0; const R=()=>Math.random()-0.5; while(y>0){ pts.push(new THREE.Vector3(x,y,z)); x+=R()*40; z+=R()*40; y-=20+Math.random()*30; } pts.push(new THREE.Vector3(x,0,z));
  const g=new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts,false,'catmullrom',0),120,1.6,4,false);
  const m=new THREE.Mesh(g,new THREE.MeshBasicMaterial({color:0xe8eeff,transparent:true,opacity:0,fog:false})); m.visible=false; return m;
}
