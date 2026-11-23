import numpy as np
SPP=321
def row_env(vals, att_ms, rel_ms, sr=44100):
    """vals: per-column brightness 0..255 for one row. returns list of (start,env) per note"""
    A=att_ms*sr/1000; R=rel_ms*sr/1000+SPP
    vals=np.asarray(vals,float)/255; W=len(vals); notes=[]; c=0
    while c<W:
        if vals[c]==0: c+=1; continue
        s=c
        while c<W and vals[c]>0: c+=1
        e=c  # exclusive
        n=(e-s)*SPP+int(R)+1; t=np.arange(n)
        # piecewise-linear pixel interpolation: value at pixel k reached at its start? ramp starts at boundary over 1 px
        lvl=np.empty(n); v=vals[s:e]
        for k in range(e-s):
            seg=t[k*SPP:(k+1)*SPP]-k*SPP
            prev=v[k-1] if k else v[0]
            lvl[k*SPP:(k+1)*SPP]=prev+(v[k]-prev)*seg/SPP
        lvl[(e-s)*SPP:]=v[-1]
        att=np.clip(t/A,0,1)
        rel=np.clip(1-(t-(e-s)*SPP)/R,0,1)
        notes.append((s*SPP,lvl*att*rel))
    return notes

def render_env(rows_vals, att_ms, rel_ms, W=512, sr=44100):
    """sum of envelopes for a single row (helper for checks) incl. end-of-image fade"""
    Rr=int(round(rel_ms*sr/1000)); n=W*SPP+Rr
    out=np.zeros(n+60000)
    for s,e in row_env(rows_vals,att_ms,rel_ms,sr): out[s:s+len(e)]+=e
    out=out[:n]; t=np.arange(n)-W*SPP
    out*=np.clip(1-t/Rr,0,1) if Rr>0 else 1
    return out
