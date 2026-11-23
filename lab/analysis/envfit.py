import numpy as np
from scipy.io import wavfile
def env(x,ch,a,b,f=440,sr=44100,w=100,h=10):
    out=[]
    for s in range(max(a,0),b,h):
        k=np.arange(s,s+w); A=np.c_[np.sin(2*np.pi*f*k/sr),np.cos(2*np.pi*f*k/sr)]
        out.append((s+w/2,np.hypot(*np.linalg.lstsq(A,x[k,ch].astype(float),rcond=None)[0])))
    return np.array(out)
def bursts(m,gap=300,thr=1e-7):
    idx=np.flatnonzero(np.abs(m)>thr); return np.split(idx,np.flatnonzero(np.diff(idx)>gap)+1)
