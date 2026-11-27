// Image brushes for Raster Organ. A brush is one or more 180×180 greyscale cells. Each cell is a force map:
// black paints with full force, white paints nothing, and transparent pixels count as white.
// Also reads GIMP brushes: .gbr (one cell) and .gih image pipes (several cells, picked per dab).
(function (root) {
  'use strict';
  const N = 180;

  // ---------- resampling (separable: box average when shrinking, bilinear when enlarging) ----------
  function weights(n, m) {
    const out = [];
    if (m < n) {
      const k = n / m;
      for (let i = 0; i < m; i++) {
        const a = i * k, b = a + k, w = [];
        for (let s = Math.floor(a); s < Math.ceil(b) && s < n; s++) {
          const cov = Math.min(b, s + 1) - Math.max(a, s);
          if (cov > 1e-9) w.push(s, cov / k);
        }
        out.push(w);
      }
    } else {
      const k = n / m;
      for (let i = 0; i < m; i++) {
        const x = Math.min(n - 1, Math.max(0, (i + 0.5) * k - 0.5)), s = Math.floor(x), f = x - s;
        out.push(f > 1e-9 && s + 1 < n ? [s, 1 - f, s + 1, f] : [s, 1]);
      }
    }
    return out;
  }
  function resample(src, sw, sh, dw, dh) {
    if (sw === dw && sh === dh) return src;
    const wx = weights(sw, dw), wy = weights(sh, dh), tmp = new Float32Array(dw * sh), out = new Float32Array(dw * dh);
    for (let y = 0; y < sh; y++) for (let x = 0; x < dw; x++) {
      const w = wx[x]; let s = 0;
      for (let k = 0; k < w.length; k += 2) s += src[y * sw + w[k]] * w[k + 1];
      tmp[y * dw + x] = s;
    }
    for (let y = 0; y < dh; y++) { const w = wy[y];
      for (let x = 0; x < dw; x++) { let s = 0; for (let k = 0; k < w.length; k += 2) s += tmp[w[k] * dw + x] * w[k + 1]; out[y * dw + x] = s; } }
    return out;
  }
  // fit a w×h force map into the 180×180 cell, keeping its proportions, centred
  function fit(force, w, h) {
    const k = N / Math.max(w, h), fw = Math.max(1, Math.round(w * k)), fh = Math.max(1, Math.round(h * k));
    const f = resample(force, w, h, fw, fh), cell = new Float32Array(N * N), ox = (N - fw) >> 1, oy = (N - fh) >> 1;
    for (let y = 0; y < fh; y++) for (let x = 0; x < fw; x++) cell[(y + oy) * N + x + ox] = Math.min(1, Math.max(0, f[y * fw + x]));
    return cell;
  }
  // RGBA pixels → force: darkness of the grey value, times alpha
  function forceFromRGBA(d, w, h) {
    const f = new Float32Array(w * h);
    for (let i = 0; i < w * h; i++) {
      const lum = 0.299 * d[4 * i] + 0.587 * d[4 * i + 1] + 0.114 * d[4 * i + 2];
      f[i] = (1 - lum / 255) * (d[4 * i + 3] / 255);
    }
    return f;
  }
  function fromImageData(data, w, h, name) {
    return { name, cells: [fit(forceFromRGBA(data, w, h), w, h)], dims: [], spacing: null, custom: true };
  }

  // ---------- GIMP .gbr ----------
  // Header (big-endian u32): header size, version, width, height, bytes per pixel, then for version 2+
  // the magic "GIMP" and the spacing (% of the brush width); the name fills the rest of the header.
  // Greyscale data: 0 = no paint, 255 = full paint. Colour (RGBA) brushes: converted with forceFromRGBA.
  function readGBR(dv, off) {
    const hs = dv.getUint32(off), ver = dv.getUint32(off + 4), w = dv.getUint32(off + 8), h = dv.getUint32(off + 12), bpp = dv.getUint32(off + 16);
    if (!(hs >= 20 && w > 0 && h > 0 && w <= 8192 && h <= 8192 && (bpp === 1 || bpp === 4))) throw new Error('not a GIMP brush');
    let spacing = null, name = '';
    if (ver >= 2) {
      if (dv.getUint32(off + 20) !== 0x47494D50) throw new Error('missing GIMP magic');
      spacing = dv.getUint32(off + 24);
    }
    const nameStart = off + (ver >= 2 ? 28 : 20), nameBytes = new Uint8Array(dv.buffer, dv.byteOffset + nameStart, Math.max(0, off + hs - nameStart));
    name = new TextDecoder().decode(nameBytes).replace(/\0[\s\S]*$/, '').trim();
    const start = off + hs, len = w * h * bpp;
    if (start + len > dv.byteLength) throw new Error('brush data is cut short');
    const px = new Uint8Array(dv.buffer, dv.byteOffset + start, len);
    let force;
    if (bpp === 1) { force = new Float32Array(w * h); for (let i = 0; i < w * h; i++) force[i] = px[i] / 255; }
    else force = forceFromRGBA(px, w, h);
    return { cell: fit(force, w, h), spacing, name, next: start + len };
  }
  function parseGBR(buf, fallback) {
    const g = readGBR(new DataView(buf), 0);
    return { name: g.name || fallback, cells: [g.cell], dims: [], spacing: g.spacing, custom: true };
  }

  // ---------- GIMP .gih image pipe ----------
  // Line 1: name. Line 2: "<ncells> ncells:N cellwidth:.. dim:D rank0:R sel0:incremental ...". Then N .gbr brushes.
  function parseGIH(buf, fallback) {
    const u8 = new Uint8Array(buf);
    let p = 0; const line = () => { const s = p; while (p < u8.length && u8[p] !== 10) p++; const t = new TextDecoder().decode(u8.subarray(s, p)); p++; return t.trim(); };
    const name = line() || fallback, params = line();
    const n = parseInt(params, 10);
    if (!(n > 0)) throw new Error('not a GIMP image pipe');
    const kv = {}; for (const m of params.matchAll(/(\w+):(\S+)/g)) kv[m[1]] = m[2];
    const dv = new DataView(buf), cells = [];
    let spacing = null;
    for (let i = 0; i < n && p < u8.length; i++) { const g = readGBR(dv, p); cells.push(g.cell); if (spacing == null) spacing = g.spacing; p = g.next; }
    if (!cells.length) throw new Error('the pipe has no brushes');
    const D = Math.max(1, parseInt(kv.dim || '1', 10)), dims = [];
    for (let d = 0; d < D; d++) dims.push({ rank: Math.max(1, parseInt(kv['rank' + d] || (d ? '1' : String(cells.length)), 10)), sel: kv['sel' + d] || 'incremental' });
    return { name, cells, dims, spacing, custom: true };
  }

  // ---------- cell selection for pipes (GIMP's selection modes) ----------
  // ctx: {count, angle (radians, stroke direction), pressure (0..1)}
  function pickCell(b, ctx) {
    if (b.cells.length === 1 || !b.dims.length) return b.cells[0];
    let idx = 0, stride = 1;
    for (let d = b.dims.length - 1; d >= 0; d--) {
      const { rank, sel } = b.dims[d]; let i;
      if (sel === 'random') i = Math.floor(Math.random() * rank);
      else if (sel === 'angular') i = Math.floor((((ctx.angle % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI)) / (2 * Math.PI) * rank);
      else if (sel === 'pressure') i = Math.floor(Math.min(0.999, Math.max(0, ctx.pressure)) * rank);
      else i = ctx.count % rank;   // incremental; velocity and tilt fall back to it
      idx += Math.min(rank - 1, i) * stride; stride *= rank;
    }
    return b.cells[idx % b.cells.length];
  }

  // ---------- a cell scaled to the drawn size, cached ----------
  const cache = new WeakMap();
  function scaled(cell, w, h) {
    let m = cache.get(cell); if (!m) cache.set(cell, m = new Map());
    const key = w + 'x' + h; let s = m.get(key);
    if (!s) { s = resample(cell, N, N, w, h); if (m.size > 24) m.clear(); m.set(key, s); }
    return s;
  }

  // ---------- built-in brushes ----------
  function make(name, f) { const c = new Float32Array(N * N);
    for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) c[y * N + x] = Math.min(1, Math.max(0, f((x + 0.5) / N * 2 - 1, (y + 0.5) / N * 2 - 1, x, y)));
    return { name, cells: [c], dims: [], spacing: null, custom: false }; }
  const ss = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
  function rng(seed) { return () => (seed = (seed * 16807) % 2147483647) / 2147483647; }
  function builtins() {
    const q = rng(11), noise = new Float32Array(N * N).map(() => q());
    const q2 = rng(5), dots = [];
    for (let k = 0; k < 40; k++) { const a = q2() * 6.283, r = Math.sqrt(q2()) * 0.85; dots.push([Math.cos(a) * r, Math.sin(a) * r, 0.03 + q2() * 0.05, 0.5 + q2() * 0.5]); }
    return [
      make('Soft disc', (x, y) => 1 - ss(0.2, 1, Math.hypot(x, y))),
      make('Hard disc', (x, y) => Math.hypot(x, y) <= 0.95 ? 1 : 0),
      make('Comb', (x, y, px, py) => (py % 15 < 4 ? 1 : 0) * (1 - ss(0.75, 1, Math.abs(x)))),
      make('Chalk', (x, y, px, py) => (1 - ss(0.55, 1, Math.hypot(x, y))) * (noise[py * N + px] > 0.45 ? 0.4 + noise[py * N + px] * 0.6 : 0)),
      make('Ring', (x, y) => 1 - ss(0.06, 0.16, Math.abs(Math.hypot(x, y) - 0.75))),
      make('Scatter', (x, y) => { let v = 0; for (const [cx, cy, r, s] of dots) if (Math.hypot(x - cx, y - cy) < r) v = Math.max(v, s); return v; }),
      make('Fade right', (x, y) => (1 - ss(0.7, 1, Math.abs(y))) * (0.5 - x / 2)),
    ];
  }

  // ---------- storage of imported brushes (bytes, base64) ----------
  function pack(b) {
    return { name: b.name, dims: b.dims, spacing: b.spacing, cells: b.cells.map(c => {
      let s = ''; for (let i = 0; i < c.length; i++) s += String.fromCharCode(Math.round(c[i] * 255)); return btoa(s); }) };
  }
  function unpack(o) {
    return { name: o.name, dims: o.dims || [], spacing: o.spacing ?? null, custom: true, cells: o.cells.map(s => {
      const t = atob(s), c = new Float32Array(N * N); for (let i = 0; i < c.length; i++) c[i] = t.charCodeAt(i) / 255; return c; }) };
  }

  // draw a cell as a picture: black ink on white, as the brush image looks
  function thumb(cell, cv) {
    const w = cv.width, h = cv.height, s = resample(cell, N, N, w, h), x = cv.getContext('2d'), id = x.createImageData(w, h);
    for (let i = 0; i < w * h; i++) { const v = Math.round(255 * (1 - s[i])); id.data[4 * i] = id.data[4 * i + 1] = id.data[4 * i + 2] = v; id.data[4 * i + 3] = 255; }
    x.putImageData(id, 0, 0);
  }

  const api = { SIZE: N, fromImageData, parseGBR, parseGIH, pickCell, scaled, builtins, pack, unpack, thumb, resample };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Brushes = api;
})(typeof window !== 'undefined' ? window : globalThis);
