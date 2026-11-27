"""Reference models of the Image Synth effects (SPEC.md §10), measured on MetaSynth CTX 2.0.

img: int array (H, W, 3) or (H, W) of 0..255, row 0 = top, columns = time.
Every effect works on each colour plane (R = left, G = right) on its own and, except Maximum,
on each row on its own. G = Effects Grid size in pixels. Results are 8-bit (floor).
"""
import math
import numpy as np


def _planes(f):
    def run(img, G, **kw):
        out = img.copy()
        if out.ndim == 2:
            return f(out.astype(np.int64), G, **kw)
        for ch in (0, 1):
            out[:, :, ch] = f(img[:, :, ch].astype(np.int64), G, **kw)
        return out
    run.__name__ = f.__name__
    return run


def _rows(f):
    def plane(P, G, **kw):
        return np.array([f(row.copy(), G, **kw) for row in P])
    plane.__name__ = f.__name__
    return _planes(plane)


@_rows
def echo(x, G):
    """Copies every G px to the right, each at 1/3 of the gap to the pixel already there (recursive)."""
    y = x.copy()
    for c in range(G, len(x)):
        p = y[c - G]
        if p > y[c]:
            y[c] = math.floor(x[c] + (p - x[c]) / 3)
    return y


@_rows
def pre_echo(x, G):
    """Echo mirrored in time: copies every G px to the left."""
    y = x.copy()
    for c in range(len(x) - G - 1, -1, -1):
        p = y[c + G]
        if p > y[c]:
            y[c] = math.floor(x[c] + (p - x[c]) / 3)
    return y


@_rows
def repeat(x, G):
    """Full-level copies every G px up to the right edge (running maximum with period G)."""
    y = x.copy()
    for c in range(G, len(x)):
        y[c] = max(y[c], y[c - G])
    return y


@_rows
def quantize(x, G):
    """Each G-px cell (cells start at column 0) becomes one flat value: (max + sum/G) / 2.
    The last column of the picture is left out of the max and the sum, but still gets its cell's value."""
    W = len(x)
    y = x.copy()
    for c0 in range(0, W, G):
        seg = x[c0:min(c0 + G, W - 1)]
        y[c0:c0 + G] = math.floor((seg.max() + seg.sum() / G) / 2) if len(seg) else 0
    return y


@_rows
def pulse(x, G):
    """Keeps the first G/2 px of every cell and clears the rest."""
    y = x.copy()
    for c in range(len(x)):
        if c % G >= G // 2:
            y[c] = 0
    return y


@_rows
def saw(x, G):
    """Inside every cell, scales by (G - position)/G: full at the cell start, falling towards 0."""
    return np.array([math.floor(v * (G - (c % G)) / G) for c, v in enumerate(x)])


@_rows
def shorten(x, G):
    """Clears the last pixel of every note that is at least 2 px long and is followed by black.
    Ignores G."""
    y = x.copy()
    for c in range(1, len(x) - 1):
        if x[c] > 0 and x[c - 1] > 0 and x[c + 1] == 0:
            y[c] = 0
    return y


@_rows
def attack(x, G):
    """Where a pixel is more than 16 above the pixel before it, boosts it to 1.5x (max 255) and
    clears the pixel before it (a gap that retriggers the note). Ignores G."""
    y = x.copy()
    for c in range(1, len(x)):
        if x[c] - x[c - 1] > 16:
            y[c] = min(255, math.floor(x[c] * 1.5))
            y[c - 1] = 0
    return y


@_planes
def motion_blur(P, G):
    """Horizontal Gaussian-shaped blur with wrap-around. Radius R = min(G, 62);
    integer weights w(d) = floor(32 * exp(-2 (d/R)^2)) for |d| <= R; output floor(sum(w x) / sum(w))."""
    R = min(G, 62)
    d = np.arange(-R, R + 1)
    w = np.floor(32 * np.exp(-2.0 * (d / R) ** 2)).astype(np.int64)
    acc = np.zeros_like(P)
    for i, wi in enumerate(w):
        acc += wi * np.roll(P, i - R, axis=1)
    return acc // w.sum()


@_planes
def maximum(P, G):
    """Every column becomes its brightest pixel, top to bottom. Ignores G."""
    return np.repeat(P.max(axis=0, keepdims=True), P.shape[0], axis=0)


def grid_filter(img, G, grid):
    """Multiplies the picture by the blue grid layer: floor(x * blue / 256). Ignores G."""
    out = img.copy()
    for ch in (0, 1):
        out[:, :, ch] = (img[:, :, ch].astype(np.int64) * grid) // 256
    return out


# Reverb is not modelled (SPEC.md §10.4). What a single 255 pixel turns into, n = 1, 2, ... px after it:
REVERB_TAIL_255 = {
    8:  [125, 104, 86, 71, 59, 49, 40, 33, 27, 23, 18, 15, 12, 10, 8, 6, 5, 4, 2, 2, 1, 1],
    12: [131, 115, 100, 87, 76, 66, 57, 50, 43, 37, 33, 28, 24, 21, 18, 15, 13, 11, 10, 8, 7, 5, 4, 4, 3, 2,
         2, 1, 1],
    32: [138, 130, 122, 115, 109, 102, 96, 91, 85, 80, 76, 71, 67, 63, 59, 55, 52, 49, 46, 43, 40, 38, 35, 33,
         31, 29, 27, 25, 24, 22, 20, 19, 18, 17, 16, 14, 13, 12, 11, 10, 9, 9, 8, 8, 7, 6, 6, 5, 5, 4, 4, 3,
         2, 2, 1, 1],
    64: [137, 132, 128, 124, 120, 116, 112, 109, 105, 102, 99, 95, 92, 89, 87, 84, 81, 78, 76, 73, 71, 68, 66,
         64, 62, 59, 57, 55, 53, 52, 50, 48, 47, 45, 43, 42, 40, 38, 37, 36, 34, 33, 32, 31, 30, 29, 28, 27,
         26, 24, 23, 22, 21, 20, 19, 18, 17, 17, 16, 16, 15, 14, 14, 13, 13, 12, 12, 11, 11, 10, 9, 9, 8, 8,
         7, 7, 6, 6, 5, 4, 4, 3, 3, 2, 2, 1, 1],
}


EFFECTS = {
    'MotionBlur': motion_blur, 'Quantize': quantize, 'Echo': echo, 'PreEcho': pre_echo,
    'Repeat': repeat, 'Pulse': pulse, 'Saw': saw, 'Shorten': shorten, 'Attack': attack,
    'Maximum': maximum, 'GridFilter': grid_filter,
}
