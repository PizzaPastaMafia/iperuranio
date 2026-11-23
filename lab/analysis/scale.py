import numpy as np, sys
for p in sys.argv[1:]:
    r=np.load(p+'.npy'); r=r[r[:,1]>0][::-1]; c=1200*np.log2(r[:,1]/r[0,1])
    names=['A','A#','B','C','C#','D','D#','E','F','F#','G','G#']
    print(p,'bottom %.4f'%r[0,1],'rows/oct', int(np.sum(c<1199.99)), 'first 9 cents', c[:9].round(3).tolist())
    print('   notes',[names[int(round(1200*np.log2(f/440)/100))%12] for f in r[:8,1]], ' top audible %.1f'%r[-1,1], 'row', int(r[-1,0]))
