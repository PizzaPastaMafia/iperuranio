# iperuranio

A clean-room study of MetaSynth CTX 2.0's Image Synth, and a Web Audio image synth built from it.

- **`SPEC.md`**: the behavioural spec. It comes from rendering test images in MetaSynth and measuring the audio. No MetaSynth code or data files were read.
- **`lab/`**: the measurements behind the spec
  - `stimuli/`: test images (PNG)
  - `renders/`: MetaSynth's output for each stimulus (float32 stereo WAV, 44.1 kHz)
  - `analysis/`: the numpy/scipy scripts that produced the numbers in the spec
  - `ms-lab/`: the local MetaSynth project. It is **not committed**; see `.gitignore`.
- **`web/`**: Raster Organ, the browser synth
  - `html/index.html`: the page (UI, painting, maps, playback, WAV export)
  - `html/engine.js`: the synthesis engine. It runs as a Web Worker and implements the spec.
  - `docker-compose.yml`: nginx behind Traefik
- **`verify/`**: runs `engine.js` on the stimuli and compares the result with the renders

## Run the synth locally

```sh
cd web/html && python3 -m http.server 8000   # then open http://localhost:8000
```

The page has to be served over HTTP, because it loads `engine.js` as a Web Worker, so opening the file directly won't work.

## Deploy

```sh
cd web
cp .env.example .env          # set SITE_NAME and DOMAIN
chmod 755 html && chmod 644 html/*
docker compose up -d          # needs the external `internalProxy` network
```

## Check the engine against MetaSynth

```sh
pip install -r requirements.txt
python3 verify/check_web.py   # needs node; exits 1 if any check fails
```

| Check | What it tests |
|---|---|
| T13_none | Sample by sample, with phase randomization off: pitch, gain, envelopes and phase continuity |
| T04, T04_spp290, T05 | Envelopes, brightness and tempo |
| T11, T12 | Colour → stereo and per-channel note logic |
| M_exp_b | The Exponential (linear Hz) map and the per-row gain |

The scripts in `lab/analysis` were written against the lab's original folder layout (for example `wav/<name>.wav`), so their paths may need adjusting before you rerun them.
