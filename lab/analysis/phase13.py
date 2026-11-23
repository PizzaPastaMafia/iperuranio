import numpy as np, sys
from scipy.io import wavfile
sr=44100
def phases(name):
    _,x=wavfile.read(f'wav/{name}.wav'); res={}
    for f,off in [(440,0),(880,0),(1760,4)]:
        out=[]
        for n in range(32):
            s=(n*16+off)*321
            k=np.arange(s+200,s+8*321-20)   # sustain part, relative to onset
            if k[-1]>=len(x): continue
            t=(k-s)/sr; A=np.c_[np.sin(2*np.pi*f*t),np.cos(2*np.pi*f*t)]
            ph=[np.arctan2(*np.linalg.lstsq(A,x[k,ch].astype(float),rcond=None)[0][::-1]) for ch in (0,1)]
            out.append(ph)
        res[f]=np.array(out)
    return res
def circstats(p):
    z=np.exp(1j*p); R=abs(z.mean()); return np.angle(z.mean()), np.sqrt(-2*np.log(max(R,1e-12)))
if __name__=='__main__':
    for name in sys.argv[1:]:
        r=phases(name); print('==',name)
        for f,p in r.items():
            L,R=p[:,0],p[:,1]; d=np.angle(np.exp(1j*(R-L)))
            mL,sL=circstats(L); md,sd=circstats(d)
            print(f' {f:5d}Hz  L: mean {mL:+.3f} circ-sd {sL:.3f} rad | R-L: mean {md:+.3f} sd {sd:.3f} | range L {np.ptp(np.unwrap(np.sort(L))):.2f} | first L {L[:4].round(3)} d {d[:4].round(3)}')
        # inter-row phase relationship
