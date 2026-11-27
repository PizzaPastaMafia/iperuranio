"""Compare the web effects (web/html/fx.js) with the MetaSynth effect outputs in lab/fx/out (SPEC.md §10).

Run from the repo root:  python3 verify/check_fx.py
Needs node, numpy, pillow. Exit code 1 if any exact effect differs by even one pixel value.
Reverb is approximate, so its error is reported but not checked.
"""
import glob, os, re, subprocess, sys, tempfile
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FX = os.path.join(ROOT, 'lab', 'fx')
JS = os.path.join(ROOT, 'web', 'html', 'fx.js')
TMP = tempfile.mkdtemp()
RUN = os.path.join(TMP, 'run.js')
open(RUN, 'w').write(f"""
const fx = require({JS!r}), fs = require('fs');
const [inp, grid, out, id, G, w, h] = process.argv.slice(2);
const b = fs.readFileSync(inp), n = +w * +h;
const img = {{ w: +w, h: +h, r: b.subarray(0, n), g: b.subarray(n) }};
const o = fx.apply(img, id, +G, new Uint8Array(fs.readFileSync(grid)));
fs.writeFileSync(out, Buffer.concat([Buffer.from(o.r), Buffer.from(o.g)]));
""")

load = lambda p: np.asarray(Image.open(p)).astype(np.uint8)
grid = load(os.path.join(FX, 'stimuli', 'grid_layer.png'))
gpath = os.path.join(TMP, 'grid.bin'); grid.tofile(gpath)
fails = 0
for path in sorted(glob.glob(os.path.join(FX, 'out', 's*_*_G*.png'))):
    s, eff, G = re.match(r's(\d)_(\w+)_G(\d+)\.png', os.path.basename(path)).groups()
    stim = load(os.path.join(FX, 'stimuli', f'stim_fx{s}.png'))
    h, w = stim.shape[:2]
    ip, op = os.path.join(TMP, 'in.bin'), os.path.join(TMP, 'out.bin')
    np.concatenate([stim[:, :, 0].ravel(), stim[:, :, 1].ravel()]).tofile(ip)
    subprocess.check_call(['node', RUN, ip, gpath, op, eff, G, str(w), str(h)])
    got = np.fromfile(op, np.uint8).reshape(2, h, w).astype(int)
    ms = load(path)
    want = np.stack([ms[:, :, 0], ms[:, :, 1]]).astype(int)
    err = np.abs(got - want)
    if eff == 'Reverb':
        print(f'{os.path.basename(path):28} approximate: max error {err.max()}, mean {err.mean():.3f}')
        continue
    bad = int((err > 0).sum())
    fails += bad > 0
    print(f'{os.path.basename(path):28} {"exact" if not bad else f"FAIL: {bad} values differ"}')
print('all exact effects match' if not fails else f'{fails} pictures differ')
sys.exit(1 if fails else 0)
