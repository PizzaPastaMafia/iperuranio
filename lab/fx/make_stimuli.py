"""Stimuli for the Image Synth effects session (SPEC.md §10). 512x128 RGB, row 0 = top.
R = left plane, G = right plane, B = 0 (the blue grid layer is a separate picture, see grid_layer.png)."""
import numpy as np
from PIL import Image

W, H = 512, 128


def stim1():
    """Isolated test objects, one per row (rows 6..118 step 8)."""
    a = np.zeros((H, W, 3), np.uint8)
    Y = (255, 255, 0)
    a[6, 100] = Y                        # impulse, both channels
    a[14, 100, 0] = 255                  # impulse, red only
    a[22, 100, 1] = 255                  # impulse, green only
    a[30, 100, :2] = 128                 # half-level impulse
    a[38, 100:140, :2] = 255             # 40-px bar
    a[46, :, :2] = 255                   # full row
    for c in range(W):
        a[54, c, :2] = c // 2            # ramp 0..255
    a[62, 3] = Y; a[62, 508] = Y         # edges
    a[70, 117] = Y                       # off-grid impulse
    a[78, 37:53, :2] = 200               # 16-px bar at 200
    a[86, 200, :2] = 255; a[86, 204, :2] = 100   # pair
    a[94, 64:96, 0] = 255                # red bar exactly one 32-px cell
    a[102, 250:262, 1] = 255             # green bar
    a[110, 300] = Y; a[111, 300] = Y     # vertical pair
    a[118, :256, :2] = 255; a[118, 256:, :2] = 60   # step down
    return a


def stim2():
    """Impulse ladder (rows 0-99) for exact kernels, Maximum probes, Reverb probes (rows 120-127)."""
    a = np.zeros((H, W, 3), np.uint8)
    for r in range(100):
        a[r, 200, 0] = 255 - r
        a[r, 200, 1] = 100 + r
        a[r, 450, 0] = 1 + r
    a[105, 300, 0] = 50; a[110, 300, 0] = 90; a[103, 400, 1] = 70; a[108, 400, 0] = 30
    a[120, 50:60, :2] = 200
    a[121, 50, :2] = 255; a[121, 60, :2] = 255
    a[122, 50, :2] = 100; a[122, 55, :2] = 255
    a[123, 0:100, :2] = 255; a[123, 100:200, :2] = 128
    for c in range(256):
        a[124, c, :2] = 255 - c
    a[125, 100:300, :2] = 128
    a[126, 50, :2] = 255; a[126, 51, :2] = 200
    a[127, 40:81, :2] = 60; a[127, 50, :2] = 255
    return a


def stim3():
    """Level steps a->b->0 (rows 0-63) and 2-/3-px notes of value 1..32 (rows 64-95)."""
    a = np.zeros((H, W, 3), np.uint8)
    lv = [0, 8, 16, 17, 24, 32, 64, 128]
    for i, x in enumerate(lv):
        for j, y in enumerate(lv):
            r = i * 8 + j
            a[r, 20:60, :2] = x
            a[r, 60:100, :2] = y
    for k in range(32):
        a[64 + k, 200:202, :2] = k + 1
        a[64 + k, 300:303, :2] = k + 1
    return a


if __name__ == '__main__':
    for n, f in (('stim_fx1', stim1), ('stim_fx2', stim2), ('stim_fx3', stim3)):
        Image.fromarray(f()).save(f'stimuli/{n}.png')
