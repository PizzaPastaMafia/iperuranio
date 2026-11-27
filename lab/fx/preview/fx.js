// Image Synth effects as measured on MetaSynth CTX 2.0 (SPEC.md §10). A JavaScript port of lab/fx/fxmodel.py.
// An image is {w, h, r, g}: r and g are Uint8Array planes (row-major, row 0 = top, columns = time).
// R and G are processed separately; every effect except Maximum works row by row. G = Effects Grid size in px.
(function (root) {
  'use strict';
  const fl = Math.floor;

  // row effects: (x: Int32Array input row, G) -> Int32Array output row
  const rowFx = {
    Echo(x, G) {
      const y = Int32Array.from(x);
      for (let c = G; c < x.length; c++) { const p = y[c - G]; if (p > y[c]) y[c] = fl(x[c] + (p - x[c]) / 3); }
      return y;
    },
    PreEcho(x, G) {
      const y = Int32Array.from(x);
      for (let c = x.length - G - 1; c >= 0; c--) { const p = y[c + G]; if (p > y[c]) y[c] = fl(x[c] + (p - x[c]) / 3); }
      return y;
    },
    Repeat(x, G) {
      const y = Int32Array.from(x);
      for (let c = G; c < x.length; c++) if (y[c - G] > y[c]) y[c] = y[c - G];
      return y;
    },
    Quantize(x, G) {
      const W = x.length, y = Int32Array.from(x);
      for (let c0 = 0; c0 < W; c0 += G) {
        const end = Math.min(c0 + G, W - 1);
        let mx = -1, sum = 0;
        for (let c = c0; c < end; c++) { if (x[c] > mx) mx = x[c]; sum += x[c]; }
        const v = end > c0 ? fl((mx + sum / G) / 2) : 0;
        for (let c = c0; c < Math.min(c0 + G, W); c++) y[c] = v;
      }
      return y;
    },
    Pulse(x, G) {
      const y = Int32Array.from(x), half = fl(G / 2);
      for (let c = 0; c < x.length; c++) if (c % G >= half) y[c] = 0;
      return y;
    },
    Saw(x, G) {
      const y = new Int32Array(x.length);
      for (let c = 0; c < x.length; c++) y[c] = fl(x[c] * (G - (c % G)) / G);
      return y;
    },
    Shorten(x) {
      const y = Int32Array.from(x);
      for (let c = 1; c < x.length - 1; c++) if (x[c] > 0 && x[c - 1] > 0 && x[c + 1] === 0) y[c] = 0;
      return y;
    },
    Attack(x) {
      const y = Int32Array.from(x);
      for (let c = 1; c < x.length; c++) if (x[c] - x[c - 1] > 16) { y[c] = Math.min(255, fl(x[c] * 1.5)); y[c - 1] = 0; }
      return y;
    },
    MotionBlur(x, G) {
      const R = Math.min(G, 62), W = x.length, w = [];
      let ws = 0;
      for (let d = -R; d <= R; d++) { const v = fl(32 * Math.exp(-2 * (d / R) ** 2)); w.push(v); ws += v; }
      const y = new Int32Array(W);
      for (let c = 0; c < W; c++) {
        let acc = 0;
        for (let i = 0; i < w.length; i++) acc += w[i] * x[(((c + i - R) % W) + W) % W];
        y[c] = fl(acc / ws);
      }
      return y;
    },
    // NOT exact (SPEC.md §10.4): after every fall, the measured tail of a 255 pixel, scaled to the level before
    // the fall, is laid over the picture; overlapping tails and the picture combine by maximum.
    Reverb(x, G) {
      const h = reverbTail(G), W = x.length, y = Int32Array.from(x);
      for (let c = 0; c < W - 1; c++) {
        if (x[c] - x[c + 1] <= 2) continue;
        for (let n = 1; n <= h.length && c + n < W; n++) {
          const v = fl(x[c] * h[n - 1] / 255);
          if (v > y[c + n]) y[c + n] = v;
        }
      }
      return y;
    },
  };

  const TAIL = {
    8: [125, 104, 86, 71, 59, 49, 40, 33, 27, 23, 18, 15, 12, 10, 8, 6, 5, 4, 2, 2, 1, 1],
    12: [131, 115, 100, 87, 76, 66, 57, 50, 43, 37, 33, 28, 24, 21, 18, 15, 13, 11, 10, 8, 7, 5, 4, 4, 3, 2, 2, 1, 1],
    32: [138, 130, 122, 115, 109, 102, 96, 91, 85, 80, 76, 71, 67, 63, 59, 55, 52, 49, 46, 43, 40, 38, 35, 33, 31, 29, 27, 25, 24, 22, 20, 19, 18, 17, 16, 14, 13, 12, 11, 10, 9, 9, 8, 8, 7, 6, 6, 5, 5, 4, 4, 3, 2, 2, 1, 1],
    64: [137, 132, 128, 124, 120, 116, 112, 109, 105, 102, 99, 95, 92, 89, 87, 84, 81, 78, 76, 73, 71, 68, 66, 64, 62, 59, 57, 55, 53, 52, 50, 48, 47, 45, 43, 42, 40, 38, 37, 36, 34, 33, 32, 31, 30, 29, 28, 27, 26, 24, 23, 22, 21, 20, 19, 18, 17, 17, 16, 16, 15, 14, 14, 13, 13, 12, 12, 11, 11, 10, 9, 9, 8, 8, 7, 7, 6, 6, 5, 4, 4, 3, 3, 2, 2, 1, 1],
  };
  // Measured tails for G 8/12/32/64; other G values are interpolated on log(G) (outside 8..64: nearest measured).
  function reverbTail(G) {
    if (TAIL[G]) return TAIL[G];
    const gs = [8, 12, 32, 64];
    if (G <= 8) return TAIL[8];
    if (G >= 64) return TAIL[64];
    let i = 0; while (gs[i + 1] < G) i++;
    const a = TAIL[gs[i]], b = TAIL[gs[i + 1]], t = Math.log(G / gs[i]) / Math.log(gs[i + 1] / gs[i]);
    const n = Math.round(a.length + (b.length - a.length) * t), out = [];
    for (let k = 0; k < n; k++) {
      const va = a[Math.round(k * (a.length - 1) / (n - 1))], vb = b[Math.round(k * (b.length - 1) / (n - 1))];
      out.push(Math.round(va + (vb - va) * t));
    }
    return out;
  }

  function mapRows(P, w, h, f, G) {
    const out = new Uint8Array(P.length), row = new Int32Array(w);
    for (let r = 0; r < h; r++) {
      for (let c = 0; c < w; c++) row[c] = P[r * w + c];
      const y = f(row, G);
      for (let c = 0; c < w; c++) out[r * w + c] = y[c];
    }
    return out;
  }

  function maximumPlane(P, w, h) {
    const out = new Uint8Array(P.length);
    for (let c = 0; c < w; c++) {
      let m = 0;
      for (let r = 0; r < h; r++) if (P[r * w + c] > m) m = P[r * w + c];
      for (let r = 0; r < h; r++) out[r * w + c] = m;
    }
    return out;
  }

  function gridFilterPlane(P, grid) {
    const out = new Uint8Array(P.length);
    for (let i = 0; i < P.length; i++) out[i] = (P[i] * grid[i]) >> 8;
    return out;
  }

  const EFFECTS = [
    { id: 'MotionBlur', name: 'Motion Blur', usesG: true, exact: true },
    { id: 'Quantize', name: 'Quantize', usesG: true, exact: true },
    { id: 'Echo', name: 'Echo', usesG: true, exact: true },
    { id: 'PreEcho', name: 'Pre Echo', usesG: true, exact: true },
    { id: 'Reverb', name: 'Reverb', usesG: true, exact: false },
    { id: 'Repeat', name: 'Repeat', usesG: true, exact: true },
    { id: 'GridFilter', name: 'Grid Filter', usesG: false, exact: true },
    { id: 'Pulse', name: 'Pulse', usesG: true, exact: true },
    { id: 'Saw', name: 'Saw', usesG: true, exact: true },
    { id: 'Shorten', name: 'Shorten', usesG: false, exact: true },
    { id: 'Attack', name: 'Attack', usesG: false, exact: true },
    { id: 'Maximum', name: 'Maximum', usesG: false, exact: true },
  ];

  // apply(img, effectId, G, gridLayer?) -> new img. gridLayer = Uint8Array (w*h), only used by GridFilter.
  function apply(img, id, G, grid) {
    G = Math.max(1, G | 0);
    const plane = P => id === 'Maximum' ? maximumPlane(P, img.w, img.h)
      : id === 'GridFilter' ? gridFilterPlane(P, grid)
      : mapRows(P, img.w, img.h, rowFx[id], G);
    return { w: img.w, h: img.h, r: plane(img.r), g: plane(img.g) };
  }

  const api = { apply, EFFECTS, reverbTail, rowFx };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.MSFX = api;
})(typeof window !== 'undefined' ? window : globalThis);
