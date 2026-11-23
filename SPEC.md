# MetaSynth CTX 2.0 — Image Synth: behavioral spec (clean-room)

Black-box notes from rendering test images in MetaSynth (MS) and measuring the audio.
No MS code or data files were read. Everything below comes from the UI and the rendered audio. The project's MS manual
was used only to find out which controls exist. Where the manual and the measurements disagree, the measurement is what's recorded (see §5).

- Sessions: 2026-11-11 (rev 1: §1–§5 core; rev 2: stereo, duration, phase modes, all pitch maps, amplitude map)
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
| T01_row128, T03/T04/T05_row128 | first versions (rows above the cutoff, silent; not used) | — |

State left in MS: ms-lab project, Semitones, A3, 512×256, spp 321, WaveSynth 4/10 ms, Preferences back to Small Stereo.
The amplitude-map notch from session 1 is still there.
