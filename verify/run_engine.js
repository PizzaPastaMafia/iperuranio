// Runs web/html/engine.js (the exact code the page uses) on a stimulus and writes float32 L then R.
// usage: node run_engine.js img.json out.bin spp map phi_rad [only_row_from_bottom]
const fs=require('fs'), path=require('path');
const src=fs.readFileSync(path.join(__dirname,'..','web','html','engine.js'),'utf8');
const self={};let res;self.postMessage=m=>res=m;new Function('self',src)(self);
const [img,out,spp,map,phi,only]=process.argv.slice(2);
const g=JSON.parse(fs.readFileSync(img));const W=512,H=g.r.length;
const L=new Float32Array(W*H),R=new Float32Array(W*H);
for(let y=0;y<H;y++)for(let c=0;c<W;c++){const r=H-1-y;if(only!==undefined&&r!==+only)continue;L[r*W+c]=g.r[y][c]/255;R[r*W+c]=g.g[y][c]/255;}
const f=n=>map==='exp'?27.5*(n+1):55*Math.pow(2,n/12);
const freqs=new Float32Array(H).map((_,r)=>f(r));
const gains=new Float32Array(H).map((_,r)=>0.099025*(1+0.2801*r/(H-1)));
const ph=new Float32Array(H).fill(+phi);
self.onmessage({data:{id:1,L,R,W,H,freqs,gains,sr:44100,spp:+spp,att:4,rel:10,wave:'sine',phiL:ph,phiR:ph}});
fs.writeFileSync(out,Buffer.concat([Buffer.from(res.oL.buffer),Buffer.from(res.oR.buffer)]));
console.log(res.oL.length);
