import numpy as np, sys; sys.path.insert(0,'.')
from model import row_env, SPP
def synth_row(vals, f, gain, att_ms=4, rel_ms=10, W=512, sr=44100, phi0=0.0):
    Rr=int(round(rel_ms*sr/1000)); n=W*SPP+Rr; out=np.zeros(n+60000)
    lit_so_far=0
    for s,e in row_env(vals,att_ms,rel_ms,sr):
        t=np.arange(len(e)); ph=phi0+2*np.pi*f*(lit_so_far+t)/sr
        out[s:s+len(e)]+=gain*e*np.sin(ph)
        # lit length of this note
        k=s//SPP; L=0
        while k+L<len(vals) and vals[k+L]>0: L+=1
        lit_so_far+=L*SPP
    out=out[:n]; t=np.arange(n)-W*SPP; out*=np.clip(1-t/Rr,0,1)
    return out
