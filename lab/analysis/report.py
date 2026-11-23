import numpy as np, sys; sys.path.insert(0,'.')
from mapsum import run
def rep(prefix):
    r=run(prefix); ok=r[:,1]>0
    print('==',prefix,'silent rows:',(r[~ok,0].astype(int).tolist() if (~ok).sum()<40 else f'{(~ok).sum()} rows {int(r[~ok,0].min())}-{int(r[~ok,0].max())}'))
    rr=r[ok]; c=1200*np.log2(rr[:,1]/440)
    print('   row 255 f=%.4f'%rr[rr[:,0]==255,1][0] if (rr[:,0]==255).any() else '')
    st=-np.diff(c)  # cents per row going up (rows decreasing)
    st=np.diff(c[::-1])
    vals,cnt=np.unique(np.round(st,2),return_counts=True)
    print('   step cents (going up) distinct:',dict(zip(vals[:15],cnt[:15])))
    print('   rows/f sample:',[(int(a),round(b,3)) for a,b,_ in rr[::max(1,len(rr)//10)]])
    return r
if __name__=='__main__':
    for p in sys.argv[1:]: rep(p)
