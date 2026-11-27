"""Compares fxmodel.py with every picture MetaSynth produced in the effects session (lab/fx/out)."""
import glob, os, re
import numpy as np
from PIL import Image
import fxmodel

here = os.path.dirname(os.path.abspath(__file__))
load = lambda p: np.array(Image.open(p)).astype(np.int64)
grid = load(f'{here}/stimuli/grid_layer.png')
stims = {k: load(f'{here}/stimuli/stim_fx{k}.png') for k in '123'}
total = bad = 0
for path in sorted(glob.glob(f'{here}/out/s*_*_G*.png')):
    s, eff, g = re.match(r's(\d)_(\w+)_G(\d+)\.png', os.path.basename(path)).groups()
    G = int(g)
    if eff == 'Reverb':
        continue
    f = fxmodel.EFFECTS[eff]
    pred = f(stims[s], G, grid=grid) if eff == 'GridFilter' else f(stims[s], G)
    ms = load(path)
    n = int((ms[:, :, :2] != pred[:, :, :2]).sum())
    total += 1; bad += n > 0
    print(f'{os.path.basename(path):28} {"exact" if n == 0 else f"{n} px differ"}')
print(f'{total - bad}/{total} pictures match exactly (Reverb not modelled exactly, skipped)')
