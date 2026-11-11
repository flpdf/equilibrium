// servidor estático mínimo: require('./serve.js')(porta) -> Promise
const http=require('http'),fs=require('fs'),path=require('path');
const MIME={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.woff2':'font/woff2','.png':'image/png','.jpg':'image/jpeg','.fbx':'application/octet-stream','.glb':'model/gltf-binary','.mp3':'audio/mpeg'};
module.exports=(port)=>new Promise(r=>{ const root=__dirname; const s=http.createServer((req,res)=>{ let p=decodeURIComponent(req.url.split('?')[0]); if(p.endsWith('/')) p+='index.html'; const f=path.join(root,p);
  if(!f.startsWith(root)){ res.writeHead(403); return res.end(); } fs.readFile(f,(e,d)=>{ if(e){ res.writeHead(404); return res.end(); } res.writeHead(200,{'Content-Type':MIME[path.extname(f)]||'application/octet-stream'}); res.end(d); }); });
  s.listen(port,()=>r(s)); });
