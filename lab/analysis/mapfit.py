import numpy as np, sys
from scipy.io import wavfile
from scipy.optimize import least_squares
sr=44100; SPP=321
def est(seg):
    n=len(seg); t=np.arange(n)/sr
    if np.max(np.abs(seg))<1e-6: return 0.0, 0.0
    grid=np.geomspace(15,22050,4000); best_f=None; best_r=1e9
    for g in grid:
        A=np.c_[np.sin(2*np.pi*g*t),np.cos(2*np.pi*g*t)]; c,res,*_=np.linalg.lstsq(A,seg,rcond=None)
        rr=np.sum((A@c-seg)**2)
        if rr<best_r: best_r=rr; best_f=g
    f0=best_f
    best=None
    for g in [f0]:
        def r(p): return p[1]*np.sin(2*np.pi*p[0]*t)+p[2]*np.cos(2*np.pi*p[0]*t)-seg
        s=least_squares(r,[g,0.05,0.05])
        if best is None or s.cost<best.cost: best=s
    return best.x[0], np.hypot(best.x[1],best.x[2])
def analyze(name, rows):
    _,x=wavfile.read(f'wav/{name}.wav'); m=x[:,0].astype(float); out=[]
    for i,r in enumerate(rows):
        a=int((i*4+2.45)*SPP); b=int((i*4+4)*SPP)-5
        f,amp=est(m[a:b]); out.append((r,f,amp))
    return np.array(out)
