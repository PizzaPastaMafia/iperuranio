import numpy as np, sys; sys.path.insert(0,'.')
from mapfit import analyze
def run(prefix, halves=('a','b')):
    parts=[]
    for h in halves:
        rows=range(0,128) if h=='a' else range(128,256)
        try: parts.append(analyze(f'{prefix}_{h}',rows))
        except FileNotFoundError: pass
    r=np.concatenate(parts); np.save(prefix+'.npy',r); return r
