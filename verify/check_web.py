"""Compare the web engine (web/html/engine.js) with MetaSynth renders in lab/renders.

Run from the repo root:  python3 verify/check_web.py
Needs node, numpy, scipy, pillow. Exit code 1 if any check fails its tolerance.
"""
import json, os, subprocess, sys, tempfile, warnings
import numpy as np
from PIL import Image
from scipy.io import wavfile
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import lsqr

warnings.filterwarnings('ignore')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STIM, REND = os.path.join(ROOT, 'lab', 'stimuli'), os.path.join(ROOT, 'lab', 'renders')
RUN = os.path.join(ROOT, 'verify', 'run_engine.js')
TMP = tempfile.mkdtemp()
IMG, OUT = os.path.join(TMP, 'img.json'), os.path.join(TMP, 'o.bin')


def load(png):
    a = np.asarray(Image.open(os.path.join(STIM, png + '.png')).convert('RGB'))
    json.dump({'r': a[:, :, 0].tolist(), 'g': a[:, :, 1].tolist()}, open(IMG, 'w'))
    return a


def render(spp, mp, phi, only=None):
    args = ['node', RUN, IMG, OUT, str(spp), mp, str(phi)] + ([str(only)] if only is not None else [])
    n = int(subprocess.check_output(args))
    return np.fromfile(OUT, np.float32).reshape(2, n).T.astype(float)


def ms(name):
    return wavfile.read(os.path.join(REND, name + '.wav'))[1].astype(float)


def joint_fit(png, wav, spp=321, mp='semi'):
    """Fit one phase per (row, channel) — valid because of the phase continuity rule (SPEC §3.2)."""
    a = load(png); H = a.shape[0]; m = ms(wav)
    rows = [H - 1 - y for y in range(H) if a[y, :, :2].any()]
    n = len(render(spp, mp, 0))
    worst, amps = 0.0, []
    for ch in (0, 1):
        data, ri, ci, j = [], [], [], 0
        for r in rows:
            for phi in (0, np.pi / 2):
                b = render(spp, mp, phi, r)[:, ch]; nz = np.flatnonzero(b)
                data += list(b[nz]); ri += list(nz); ci += [j] * len(nz); j += 1
        A = csc_matrix((data, (ri, ci)), shape=(n, j))
        c = lsqr(A, m[:n, ch], atol=1e-12, btol=1e-12, iter_lim=5000)[0]
        worst = max(worst, np.abs(m[:n, ch] - A @ c).max())
        amps += list(np.hypot(c[0::2], c[1::2]))
    return n, len(m), worst, np.array(amps)


results = []
def report(name, ok, msg):
    results.append(ok); print(f"{'PASS' if ok else 'FAIL'}  {name:12s} {msg}")

# T13, phase randomization = none: sample-by-sample (SPEC §7)
load('T13_phase_notes'); o = render(321, 'semi', 0); m = ms('T13_none')
e = np.abs(o - m[:len(o)])
report('T13_none', len(o) == len(m) and e.max() < 5e-4, f'len {len(o)}/{len(m)}, max err {e.max():.2e}, rms {np.sqrt((e**2).mean()):.2e}')

for png, wav, spp in [('T04_segment_lengths_r219', 'T04', 321), ('T04_segment_lengths_r219', 'T04_spp290', 290),
                      ('T05_brightness_steps_r219', 'T05', 321), ('T11_colors_r219', 'T11', 321),
                      ('T12_color_transitions', 'T12', 321)]:
    n, nm, worst, _ = joint_fit(png, wav, spp)
    report(wav, n == nm and worst < 5e-4, f'len {n}/{nm}, max residual {worst:.2e}')

# Exponential map (linear Hz), rows 128-255. Rows n=118..125 carry the accidental amp-map notch (SPEC §4.2).
n, nm, worst, amps = joint_fit('T15b_rows128-255', 'M_exp_b', 321, 'exp')
k = len(amps) // 2; idx = np.r_[np.arange(k), np.arange(k)]
a = load('T15b_rows128-255'); rows = np.array([255 - y for y in range(256) if a[y, :, :2].any()])
rr = np.r_[rows, rows]; clean = (rr < 118) | (rr > 125)
dev = np.abs(amps[clean] - 1).max()
report('M_exp_b', n == nm and dev < 5e-3, f'len {n}/{nm}, gain ratio off by at most {100*dev:.2f}% outside the notch rows')

sys.exit(0 if all(results) else 1)
