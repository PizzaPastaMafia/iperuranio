# MetaSynth CTX 2.0 — Image Synth: behavioral spec (clean-room)

Black-box notes from rendering test images in MetaSynth (MS) and measuring the audio.
No MS code or data files were read. Everything below comes from the UI and the rendered audio. The project's MS manual
was used only to find out which controls exist. Where the manual and the measurements disagree, the measurement is what's recorded (see §5).

- Sessions: 2026-11-11 (rev 1: §1–§5 core; rev 2: stereo, duration, phase modes, all pitch maps, amplitude map); 2026-11-27 (§10: image effects and the Effects Grid, pixel-exact)
- MS CTX 2.0 on macOS · project `ms-lab`
- Stimuli: `stimuli/` (PNG, black background) · Renders: `renders/` (float32 stereo WAV, converted losslessly from MS `.caf`)
- Analysis: numpy/scipy least-squares sine fits at known or fitted frequencies. Scripts are in `analysis/`

Confidence: **High** = exact or ≤0.1 % residual across several tests · **Medium** = consistent but
measured in only 1–2 conditions · **Low** = hypothesis.

---

## 0. Baseline settings (unless a section says otherwise)

| Setting (UI) | Value |
|---|---|
| Room | Image Synth |
| Map | Semitones · Master tuning **A 3** |
| Size x / Size y / Depth | 512 / 256 / 8 bits |
| Instrument | WaveSynth `WaveSynth1.syns`: sine wave table, Global volume 50, **Attack 4 ms, Release 10 ms**, fine tune 0, vibrato 0, Attack mode Constant, Filter none |
| Tempo/Duration | 257.593 BPM = **321 samples/pixel** |
| Preferences → Phase randomization | **Small Stereo** (default) · Overflow handler: MIN ceil |
| Output | 44 100 Hz stereo float32 `.caf` via "Render to disk & Save" (overwrites `IS Sounds/Sound01.caf` and saves the current state into preset #1) |

---

## 1. Pitch mapping

### 1.1 General rule — **High**
Every map is a fixed table: each row index maps to a frequency, and the **bottom row is the anchor**.
Changing Size y doesn't move the bottom-row pitch; it only adds or removes rows at the top (§1.4).
The result is the same whichever map was selected before (Semitones re-measured after six other maps: identical).

### 1.2 Measured maps (Size y = 256, Master tuning A3)
`n = 255 − row` (0 at the bottom). All values are exact to < 0.001 cent unless noted.

| Map | Formula | Bottom row | 220 Hz at n = | Rows/oct |
|---|---|---|---|---|
| **Semitones** | `55 · 2^(n/12)` | 55 Hz (A1) | 24 | 12 |
| **Quartertones** | `55 · 2^(n/24)` | 55 Hz | 48 | 24 |
| **Micro8** | `77.7817 · 2^(n/48)` (25 ¢/row) | 77.78 Hz (D♯2) | 72 | 48 |
| **Micro12** | `87.3071 · 2^(n/72)` (16.67 ¢) | 87.31 Hz (F2) | 96 | 72 |
| **Micro16** | `92.4986 · 2^(n/96)` (12.5 ¢) | 92.50 Hz (F♯2) | 120 | 96 |
| **Micro32** | `201.7409 · 2^(n/192)` (6.25 ¢) | 201.74 Hz | 24 | 192 |
| **Micro50** | `208.1327 · 2^(n/300)` (4 ¢) | 208.13 Hz | 24 | 300 |
| **Whole Tones** | `13.75 · 2^(n/6)` | 13.75 Hz (A−1) | 24 | 6 |
| **Exponential** | **`27.5 · (n + 1)` Hz — linear in Hz** (harmonic series of A0) | 27.5 Hz | n = 7 | — |
| **Major Scale** | A major, 12-TET, steps 2-2-1-2-2-2-1 | 55 Hz | row 241 = 220 | 7 |
| **Minor Harmonic** | A harmonic minor, 12-TET (2-1-2-2-1-3-1) | 55 Hz | | 7 |
| **Minor Melodic** | A melodic minor ascending, 12-TET (2-1-2-2-2-2-1) | 55 Hz | | 7 |
| **Pythagorean** | A **Lydian**: ratios 1, 9/8, 81/64, 729/512, 3/2, 27/16, 243/128 per octave | 55 Hz | | 7 |
| Custom Tuning… (&) | not measured (it loads a scale file) | | | |

- "MicroN" means **N steps per whole tone** (6N per octave).
- Despite its name, **"Exponential" is linear in Hz** (equal spacing of 27.5 Hz per row, so row k from the bottom is the
  (k+1)-th harmonic of A0). It goes up to 7040 Hz at 256 rows.
- Where the bottom sits doesn't follow one simple rule. In most maps 220 Hz is 24 rows above the bottom, but
  Quartertones/Micro8/12/16 put the range one octave lower than that rule predicts. **Use the table rather than a formula.** (Medium:
  measured on rows 128–255 for the Micro maps; formula extrapolated to the upper rows.)

### 1.3 Master tuning (A 3 ↑↓) — **High** (one step tested)
One click of ↑ changes "A 3" to "A 4" and **multiplies every row's frequency by 2** (Semitones bottom 55 → 110 Hz).
Steps are in octaves; there are no semitone steps on this control.

### 1.4 Size y — **High** (128 tested)
- With Size y = 128 (Semitones), the bottom row (127) is still 55 Hz and each row is still one semitone, so the map is anchored to the bottom.
- With Semitones only **64 / 128** can be selected in the Size y menu (192+ are greyed out). Exponential allows 64…1024.
  If you switch to Exponential, set 256, and switch back to Semitones, the size stays at 256 (that's how our baseline got 256 rows).

### 1.5 High-frequency cutoff — **High**
Rows whose frequency is **≥ ~20 kHz output nothing** (exactly zero). 19 912 Hz plays. 20 496 Hz and up are silent
(Quartertones and Semitones, any Size y, any tuning). The threshold is somewhere in (19 912, 20 496] Hz; most likely 20 000 Hz.
It's **not** Nyquist (22 050 Hz). Very low frequencies aren't cut: Whole Tones plays 13.75 Hz.

## 2. Time mapping — **High**

```
samples_per_pixel (spp) = integer                     (default 321)
displayed tempo BPM     = 44100·60 / (spp · 32)  = 82687.5 / spp      (32 px per beat)
note start of column c  = c · spp   (+1 sample)
file length             = W · spp + release_samples
```
- Confirmed at two settings: spp = 321 ↔ 257.593 BPM, spp = 290 ↔ 285.129 BPM (dragging the Tempo/Duration tool),
  and 320 ↔ 258.398 BPM in the tooltip. **Tempo is quantised to whole samples per pixel.** Onsets land exactly on `c·spp + 1`.
- The default 32 pixels per beat comes from the tooltip arithmetic. Double-clicking the tool didn't open the Tempo/Duration dialog
  in this build, so pixels-per-beat itself hasn't been changed (Medium).

## 3. Oscillator, phase and phase randomization

### 3.1 Waveform — **High**
With the sine wave table each lit row/channel is a pure sine (residual −129 dB). Voices sum linearly, with no normalisation.

### 3.2 Phase continuity rule — **High** (sample-level re-synthesis, §7)
Each (row, channel) oscillator has a phase that **advances only while the row is lit**:
```
phase at the start of a note = φ0 + 2π · f · (lit samples of this row so far) / sr
```
Within a note, including its release tail, the sine runs freely. At the next note-on it **continues from where the
previous note ended (at note-off)**, not from wall-clock time and not from zero.
(Measured: successive 1-px notes advance 1.2737 rad at 440 Hz = 2π·440·321/44100. 8-px notes advance 2π·f·2568/sr, which held at 440/880/1760 Hz.)

### 3.3 φ0 — Preferences "Phase randomization" — **High**
φ0 is drawn per (row, channel) at each render (T14: 90 simultaneous rows):

| Mode | φ0 (L) | φ0 (R) |
|---|---|---|
| none | 0 (sine starts at phase 0) | = L |
| Small Mono | uniform [0, π/2) | = L |
| Large Mono | uniform [0, 2π) | = L |
| **Small Stereo** (default) | uniform [0, π/2) | independent uniform [0, π/2) |
| Large Stereo | uniform [0, 2π) | independent uniform [0, 2π) |

(Ranges observed: Small 0.001–1.562 rad over 90 rows; Large resultant length 0.04–0.07, i.e. uniform.)

## 4. Amplitude

### 4.1 Brightness → amplitude — **High**
`amp ∝ v/255` for each colour channel (linear; tested 0…255).

### 4.2 Amplitude map (curve thumbnail, top right) = gain per vertical position — **High**
Each row's gain = the amplitude-map curve read at that row's **normalised height** (bottom = 0, top = 1):
- The default curve is a straight line. Peak per voice = `0.099025 · (1 + 0.2801 · h)`, where h = n/(Size y − 1).
  - Size y = 256: +0.0010984 per row.
  - Size y = 128: +0.0021746 per row. Over the full height that's the same rise, ≈ +28 % (0.2801 at 256 rows, 0.2762 at 128),
    so the curve is stretched to the canvas height.
- It depends on **row position, not frequency**. The same per-row values show up under Semitones and Exponential.
- Clicking the thumbnail draws on it directly. The notch I drew by accident sits at h ≈ 0.47–0.49. It shows up as a dip of up to −9 %
  on exactly those rows (rows 130–137 of 256; rows 65–68 of 128). Under Semitones those rows are above 20 kHz, which
  is why the first session couldn't see it.
- Absolute level vs the gain field (45.42) and Global volume (50): not tested yet.

## 5. Envelopes — **High**

For a note covering columns `s … e−1` on one channel (t = samples since `s·spp`):
```
A_s = attack_ms · sr/1000
R_s = release_ms · sr/1000 + spp                  ← release lasts one extra pixel (scales with spp)
level(t)   = channel brightness, crossfaded linearly over one pixel (spp samples) at each column boundary
attack(t)  = clip(t / A_s, 0, 1)
release(t) = clip(1 − (t − (e−s)·spp) / R_s, 0, 1)
env = level · attack · release                    ← multiplicative; attack keeps running after note-off
```
- **"+1 pixel" confirmed to scale with spp:** the tail after the last lit pixel was 760 samples at spp 321 and 729 samples at spp 290 (release 10 ms = 441).
- **Long attacks are NOT clamped to spp.** The manual says attack is limited to the samples-per-pixel time. Measured: a 50 ms
  attack ramped over the full 2205 samples with spp = 321.
- Re-triggering: after ≥1 dark pixel, the next lit pixel starts a new note (new attack). The old one releases in parallel.
- End of image: anything still sounding is also multiplied by a linear fade to 0 over `release_ms` after `W·spp`. (Medium)

## 6. Colour → stereo — **High**

```
L amplitude ∝ R/255        R amplitude ∝ G/255        Blue is ignored
```
- There's no pan law: red and green are two **independent gain channels** (yellow 255/255/0 = full level in both; 128/128/0 = half in both).
  Measured exactly for 12 colours (T11). Pure blue renders silence, and magenta = red.
- **Each channel has its own note on/off.** Red→green on adjacent pixels gives L a normal *release* (spp + release long)
  while R starts a fresh *attack* (4 ms). It's not a one-pixel crossfade. Red→yellow: L just continues, R attacks.
  A blue pixel counts as dark (blue→white starts with an attack on both channels).
- So the clean model is: **treat the R and G planes as two separate mono images, one per output channel**, each with its own
  phase (§3.3).

## 7. Verification
- Envelope model (§5) vs. renders: ≤ 0.083 % FS residual on T04 (4/10 and 50/100 ms), T05, T09, T10. File lengths
  match to the sample.
- **Full waveform re-synthesis**, sample by sample (pitch §1 + gain §4.2 + envelope §5 + phase rule §3.2 with φ0 = 0),
  vs. the T13 render with Phase randomization = none (3 rows, 96 notes): max error 4.1e-4 = **0.40 % of one voice's peak**,
  rms 7.2e-5. `analysis/synth.py`.
- Pitch analyser self-check: Semitones measured against the formula, max error 9e-6 cent.

## 8. Implementation notes for the Web Audio port (derived)
- Per (row, channel): one sine, frequency from the §1 table, gain from §4.2, envelope from §5, phase rule from §3.2, φ0 per §3.3.
- Silence rows ≥ 20 kHz. Quantise time to an integer spp. Render length = W·spp + release.
- Because the phase only advances while a row is lit, a faithful port needs a per-row "lit-sample counter", not
  `sin(2πft)` with wall-clock time.

## 9. Open questions / next experiments
1. Pixels-per-beat ≠ 32 (the dialog didn't open by double-click; maybe a different gesture/build).
2. Absolute level: gain field and Global volume. Overflow handler ("MIN ceil") behaviour when the sum clips.
3. Non-sine wave tables (band-limiting near 20 kHz?), vibrato, attack modes, the filter.
4. Custom Tuning maps (scale files); the bottom-anchor table for Micro maps above row 128 (extrapolated).
5. 16-bit images (brightness resolution).
6. Reverb (§10.4): an exact model. Next: single impulses at more G values, two impulses at varying distances (to test linearity / max-combining).
7. Does a selection change the effects' cell origin (column 0) or limit the processed area?
8. Pulse with odd G; Attack and Shorten at column 0; Motion Blur with G > 62 on wider pictures.

## 10. Image Synth effects (right-hand list) and the Effects Grid
Session 2026-11-27. Pixel-exact measurements: a test picture goes in, one effect is applied, the result is read back
and compared with a formula. Files: `lab/fx/` (stimuli, 65 MetaSynth outputs, models, verifier).

### 10.1 The Effects Grid control — **High**
- It's **one integer G, in pixels**, in the number field under the effects list. The list icon next to it offers
  8, 16, 32, 64, 128, 256, 12, 24, 48, 96, 192. Any integer can be typed, and the arrows step by 1.
- G only acts **horizontally (time)**. Every effect works row by row, and rows don't interact (except Maximum).
- Cells are anchored at **column 0**. There is no offset, angle or vertical size. To shift or skew the grid you'd
  have to move the picture.
- It's separate from the **Tool grid X/Y** (drawing snap) and from the blue **Grid Layer** (a grayscale picture,
  saved as `p NNN_00.png`). Only Grid Filter reads the Grid Layer.
- Shorten, Attack, Maximum and Grid Filter **ignore G**.
- R and G channels are processed independently with identical rules. Blue isn't touched (it's the Grid Layer).

### 10.2 Method
- Stimulus PNG written into the project's preset folder (`ms-lab.presets/Picts/p 001_01.png`), project reopened,
  effect applied, **Add Preset** writes the result as `p NNN_01.png`, then ⌘Z. The PNG round trip is exact (unchanged
  picture → identical bytes) and ⌘Z always restored the input.
- Three stimuli (`lab/fx/make_stimuli.py`): `stim_fx1` isolated impulses, bars, ramps, edges, pairs, colour cells;
  `stim_fx2` impulse ladders (every value 1–255) and Maximum/Reverb probes; `stim_fx3` level steps a→b→0 and short notes.
- G = 8, 12, 32, 64 for every effect on stim_fx1; extra runs on stim_fx2/3. 65 outputs in `lab/fx/out/`
  (`s{stim}_{Effect}_G{G}.png`).
- `lab/fx/fxmodel.py` has the models, and `lab/fx/verify_fx.py` checks them: **56/56 outputs match bit-exactly**
  (Reverb isn't modelled and is skipped).

### 10.3 Formulas
Notation: one row of one channel, x = input, y = output, c = column (0…W−1), `//` = floor division, all values 8-bit.

| Effect | Uses G | Rule (exact, verified) |
|---|---|---|
| **Motion Blur** | yes | R = min(G, 62). Weights w(d) = floor(32·exp(−2·(d/R)²)) for \|d\| ≤ R. **Wraps around** the row ends. y[c] = floor(Σ w(d)·x[c+d] / Σ w(d)). A symmetric, Gaussian-like blur, so G sets the blur width (σ ≈ R/2). |
| **Quantize** | yes | Cells [kG, kG+G). Each cell becomes floor((max + sum/G) / 2), i.e. the mean of the cell's max and its average. The **last column (W−1)** is left out of max and sum but still gets its cell's value. A partial last cell is still divided by G. |
| **Echo** | yes | y = x, then for c = G…W−1 from left to right: if y[c−G] > y[c], set y[c] = floor(x[c] + (y[c−G] − x[c]) / 3). It's recursive: each echo is ⅓ of the previous one, with copies every G px until it reaches 0 or the right edge. No wrap. |
| **Pre Echo** | yes | Echo mirrored: c = W−1−G…0 from right to left, using y[c+G]. |
| **Repeat** | yes | y = x, then c = G…W−1 from left to right: y[c] = max(y[c], y[c−G]). Full-strength copies every G px to the right edge. |
| **Pulse** | yes | y[c] = 0 where (c mod G) ≥ G//2, otherwise x. A 50 % gate, open first. (Only even G tested.) |
| **Saw** | yes | y[c] = floor(x[c]·(G − c mod G) / G). A ramp-down gain that restarts every G px. |
| **Shorten** | no | y[c] = 0 where x[c] > 0, x[c−1] > 0 and x[c+1] == 0, i.e. the last pixel of every note at least 2 px long is cleared. 1-px notes are kept. The right edge (c = W−1) doesn't count as a note end. |
| **Attack** | no | Where x[c] − x[c−1] > 16: y[c] = min(255, floor(1.5·x[c])) and y[c−1] = 0. A sharper onset: a dark gap before the jump and a 1.5× boost at the jump. A rise of ≤ 16 does nothing. |
| **Maximum** | no | The only vertical effect. Every pixel of a column becomes that column's maximum (per channel). |
| **Grid Filter** | no | y = floor(x·b / 256), where b = the Grid Layer (blue) pixel. A multiply-mask by the Grid Layer, so the "grid" here is the picture in the blue layer, not G. |
| **Reverb** | yes | Not modelled exactly. See §10.4. |

### 10.4 Reverb — **Medium** (properties) / **Low** (model)
- It only adds tails **after falls**. A constant level or a slow ramp is unchanged, and pixels before a note are unchanged.
- An isolated note gives a tail proportional to its amplitude (values 1–2 give no tail). The tail restarts with each note.
- The state carries through: after 128→8→0 the 128's tail is still visible after the 8. A fall to a non-zero level b
  roughly follows a·h[n] + b·(1 − (1 − 1/G)ⁿ), but that fit is poor (errors up to ≈ 57), so it isn't kept.
- G sets the tail length. Tail after one 255 pixel (h[1], h[2], …; also in `fxmodel.REVERB_TAIL_255`):
  - G 8 (22 px): 125 104 86 71 59 49 40 33 27 23 18 15 12 10 8 6 5 4 2 2 1 1
  - G 12 (29 px): 131 115 100 87 76 66 57 50 43 37 33 28 24 21 18 15 13 11 10 8 7 5 4 4 3 2 2 1 1
  - G 32 (56 px): 138 130 122 115 109 102 96 91 85 80 76 71 67 63 59 55 52 49 46 43 40 38 35 33 31 29 27 25 24 22 20 19 18 17 16 14 13 12 11 10 9 9 8 8 7 6 6 5 5 4 4 3 2 2 1 1
  - G 64 (87 px): 137 132 128 124 120 116 112 109 105 102 99 95 92 89 87 84 81 78 76 73 71 68 66 64 62 59 57 55 53 52 50 48 47 45 43 42 40 38 37 36 34 33 32 31 30 29 28 27 26 24 23 22 21 20 19 18 17 17 16 16 15 14 14 13 13 12 12 11 11 10 9 9 8 8 7 7 6 6 5 4 4 3 3 2 2 1 1
- The per-pixel decay ratio is ≈ 0.81 (G 8), ≈ 0.86 (G 12) and 0.926→0.941 (G 32). It drifts along the tail, so it isn't a
  single exponential. It's more likely a few comb/all-pass stages with lengths tied to G.

### 10.5 Implementation notes for the port
- An "Effects Grid" control = one integer G ≥ 1 passed to the G-dependent effects. Making the grid editable beyond that
  (offset, per-cell sizes, a vertical grid) would be our own extension, because MetaSynth has none of it.
- To match MetaSynth bit-for-bit, use integer floor arithmetic as in `lab/fx/fxmodel.py`, including the Quantize
  last-column quirk and the Motion Blur wrap-around.
- For Reverb, use the measured tails as an impulse response with max-style combining until an exact model exists.
  Scaling the 255 tail to the level before each fall and combining by maximum gets within 21 levels on every test
  picture (`web/html/fx.js`).
- Implemented in the web synth as `web/html/fx.js` (Effects panel). `verify/check_fx.py` checks it against all 56 exact
  outputs. The panel adds a grid offset, which MetaSynth doesn't have; at offset 0 the effects match MetaSynth.

## Appendix: test log
| ID | Image | Measured |
|---|---|---|
| T02, T06, T08 | row staircases (Semitones) | pitch, cutoff, per-row gain |
| T03, T04 (+50/100 ms, +spp 290) | clicks / segment lengths | spp, attack, release, +1 px scaling |
| T05, T09 | brightness steps / ramp | brightness law |
| T07 / T07b | two rows, rendered twice | purity, summing, random phase |
| T10 | brightness steps, on/off patterns | crossfade, retrigger |
| T11 | 12 colours | colour → L/R gains |
| T12 | red→green, red→yellow, blue→white | per-channel note logic |
| T13 (Small Stereo, none) | 32 notes × 3 rows | phase continuity rule; re-synthesis |
| T14 (5 modes) | 90-row chord | φ0 distributions |
| T15a/T15b × maps | every row 0–127 / 128–255, 4 px each | all pitch maps, cutoff, tuning A4, amp-map notch |
| T16 | every row of a 128-high canvas | Size y = 128 |
| FX1–FX3 (§10) | `lab/fx/stimuli/stim_fx1–3` × 12 effects × G 8/12/32/64 | effect formulas, Effects Grid; 65 outputs in `lab/fx/out/` |
| T01_row128, T03/T04/T05_row128 | first versions (rows above the cutoff, silent; not used) | — |

State left in MS: ms-lab project, Semitones, A3, 512×256, spp 321, WaveSynth 4/10 ms, Preferences back to Small Stereo.
The amplitude-map notch from session 1 is still there.
After the §10 session: ms-lab `p 001_01.png` holds `stim_fx3` (originals backed up in `metasynth-lab/lab/fx-lab/backup/`) and presets p 002–p 076 hold the effect outputs.
