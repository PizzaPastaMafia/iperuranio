import numpy as np, sys
from scipy.io import wavfile
sr=44100; rows=np.arange(160,250); f=55*2**((255-rows)/12)
def ph(name):
    _,x=wavfile.read(f'wav/{name}.wav'); k=np.arange(400,64*321-50); t=k/sr
    A=np.concatenate([np.sin(2*np.pi*f[None,:]*t[:,None]),np.cos(2*np.pi*f[None,:]*t[:,None])],1)
    out=[]
    for ch in (0,1):
        c=np.linalg.lstsq(A,x[k,ch].astype(float),rcond=None)[0]; n=len(f)
        out.append((np.arctan2(c[n:],c[:n]),np.hypot(c[:n],c[n:])))
    return out
if __name__=='__main__':
    for name in sys.argv[1:]:
        (pL,aL),(pR,aR)=ph(name); d=np.angle(np.exp(1j*(pR-pL)))
        def cs(p): z=np.exp(1j*p).mean(); return np.angle(z),abs(z)
        print(f'== {name}: amp L {aL.min():.4f}-{aL.max():.4f}')
        print('   L phase: circ mean %.3f, resultant R %.3f, range [%.2f,%.2f], std %.3f'%(*cs(pL),pL.min(),pL.max(),np.std(pL)))
        print('   R-L    : circ mean %.3f, resultant R %.3f, range [%.3f,%.3f], std %.4f'%(*cs(d),d.min(),d.max(),np.std(d)))
        print('   first L',pL[:6].round(3),' d',d[:6].round(3))
