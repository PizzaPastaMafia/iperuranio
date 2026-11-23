// Raster Organ synthesis engine (Web Worker).
// Implements SPEC.md: pitch rows from the page, gain per row, envelopes (§5), phase continuity (§3.2),
// per-channel notes (§6), 20 kHz cutoff (§1.5), end-of-image fade. Runs in the browser and in verify/.
const TS=4096, tables={}, CUT=20000;
function harm(w,k){if(w==='sine')return k===1?1:0;if(w==='saw')return 1/k;if(w==='square')return k%2?1/k:0;if(w==='tri')return k%2?(((k-1)/2)%2?-1:1)/(k*k):0;return 0;}
function table(w,n){const key=w+n;if(tables[key])return tables[key];const t=new Float64Array(TS+1);let pk=0;
  for(let i=0;i<TS;i++){let s=0;const ph=2*Math.PI*i/TS;for(let k=1;k<=n;k++){const a=harm(w,k);if(a)s+=a*Math.sin(k*ph);}t[i]=s;if(Math.abs(s)>pk)pk=Math.abs(s);}
  for(let i=0;i<TS;i++)t[i]/=pk||1;t[TS]=t[0];return tables[key]=t;}
self.onmessage=e=>{
  const {id,L,R,W,H,freqs,gains,sr,spp,att,rel,wave,phiL,phiR}=e.data;
  const As=att*sr/1000, relS=Math.round(rel*sr/1000), Rs=rel*sr/1000+spp;   // release = setting + one pixel (§5)
  const end=W*spp, N=end+relS, oL=new Float32Array(N), oR=new Float32Array(N);
  // R and G planes are two independent mono images, one per output channel (§6)
  for(const [P,out,phi] of [[L,oL,phiL],[R,oR,phiR]]){
    for(let r=0;r<H;r++){
      const f=freqs[r]; if(!(f>0)||f>=CUT)continue;                         // rows >= 20 kHz are silent (§1.5)
      const g=gains[r], base=r*W;
      const nh=wave==='sine'?1:Math.max(1,Math.min(512,Math.floor((CUT-1)/f)));
      const T=table(wave,nh), inc=f*TS/sr, ph0=phi[r]*TS/(2*Math.PI);
      let lit=0, c=0;                                                         // lit-sample counter (§3.2)
      while(c<W){
        if(!P[base+c]){c++;continue;}
        const s=c; while(c<W&&P[base+c])c++;
        const n=c-s, noteEnd=n*spp, len=noteEnd+Math.ceil(Rs)+1, t0=s*spp;
        let ph=(ph0+inc*lit)%TS;
        for(let t=0;t<len;t++){
          const o=t0+t; if(o>=N)break;
          const k=Math.floor(t/spp);
          let lvl; if(k<n){const v=P[base+s+k], p=k?P[base+s+k-1]:v; lvl=p+(v-p)*(t-k*spp)/spp;} else lvl=P[base+c-1];
          const a=As>0?Math.min(1,t/As):1, rl=t<noteEnd?1:Math.max(0,1-(t-noteEnd)/Rs), env=lvl*a*rl;
          if(env>0){const ix=ph|0,fr=ph-ix;out[o]+=g*env*(T[ix]+(T[ix+1]-T[ix])*fr);}
          ph+=inc; if(ph>=TS)ph-=TS;
        }
        lit+=noteEnd;
      }
    }
  }
  for(let o=end;o<N;o++){const k=relS>0?Math.max(0,1-(o-end)/relS):0;oL[o]*=k;oR[o]*=k;}   // end-of-image fade (§5)
  let pk=0; for(let i=0;i<N;i++){const a=Math.abs(oL[i]),b=Math.abs(oR[i]);if(a>pk)pk=a;if(b>pk)pk=b;}
  self.postMessage({id,oL,oR,peak:pk},[oL.buffer,oR.buffer]);
};
