# What If? — low-poly reels

Vertical (1080×1920, 30 fps) 45–60 s shorts for Instagram Reels and YouTube Shorts:
blocky people, low-poly animals, flat colours, soft shadows, moving camera, a curious kid
asking "what if…?" in English with Chinese subtitles, ending on **"What do you think?"**

Everything is code: no 3D software, no keyframing by hand, no stock assets.

## The workflow (per episode)

1. **Give Claude the question.** e.g. *"New episode: What if dogs could talk?"*
   Claude writes two files in `episodes/<id>/`:
   - `lines.json`: the kid's lines (English + Chinese) and the pause before/after each.
   - `episode.js`: the world (built from the kit), what everyone does, and the camera shots, all timed to the lines.
2. **Run one command:**
   ```bash
   cd reels
   PY=/path/to/python KOKORO=/path/to/kokoro-models sh make.sh <id>
   ```
   It records the voice, renders every frame, scores and mixes the sound, and masters to −14 LUFS.
3. **Post** `videos/<id>.mp4`. Upload `episodes/<id>/out/subtitles.srt` too if you'd like platform captions (the video already has captions burned in).

Want a change? Say it in plain words ("slower ending", "make the cow bigger", "a different
voice") and Claude edits the episode. `sh make.sh <id> --no-voice` re-renders without
re-recording the voice.

### Checking before the full render
```bash
node engine/render.mjs <id> sheet 0:60:2   # contact sheet of frames, every 2 s → out/sheet.jpg
node engine/render.mjs <id> stills 12.5    # single frames
node engine/render.mjs <id> serve          # live preview in a browser (silent)
```

## One-time setup
- Node 20+, ffmpeg, Playwright with Chromium (`npm i playwright && npx playwright install chromium` on your own machine).
- `npm install` in `reels/` (installs three.js).
- A Python 3.11+ with `pip install kokoro-onnx numpy scipy soundfile`, and the Kokoro model files
  `kokoro-v1.0.onnx` + `voices-v1.0.bin` from https://github.com/thewh1teagle/kokoro-onnx/releases (model-files-v1.0).
- Fonts are fetched automatically (Google Fonts, OFL) the first time, and again when a new episode adds new Chinese characters.

## What's in the box

| File | What it does |
|---|---|
| `engine/kit.js` | builders: `person()` (blocky, posable: `POSES`, `walk()`), `cow()`, `squirrel()`, `bird()`, `tree()`, `bush()`, `rock()`, `cloud()`, `ground()`, `house()`, `fence()`, `stand()`, `sign()` (changeable text), `bill()`, `coin()`, `apple()`, `iceCream()`, `rake()` |
| `engine/engine.js` | the stage: soft sun + sky light, shadows that follow the shot, sky gradient and fog, captions, timeline from the voice; helpers `key()`, `poseTrack()`, `camTrack()` (with cuts), `drift()` |
| `engine/render.mjs` | headless capture: events, stills, contact sheet, full video (parallel workers) |
| `engine/tts.py` | the kid's voice (Kokoro `af_sky`, pitched up slightly) |
| `engine/mix.py` | original marimba score, 18 synthesised sound effects, ducking under the voice |
| `engine/master.sh`, `engine/finish.py` | loudness master; `.srt` subtitles |
| `make.sh` | the whole pipeline in one command |

## Style rules the episodes follow
- **Tone:** a kid thinking out loud ("So I was…", "wait", "hmm…"), one silly visual gag per idea, one real idea underneath (here: money is valuable because it's scarce).
- **Shape:** hook in the first second → the fun → "but hmm…" turn → the small insight → a quiet "What do you think?" close-up. No logo end card.
- **Frame:** captions sit at ~70 % height, clear of the Reels/Shorts buttons; key action stays in the middle third.
- **Camera:** every shot moves for a reason (follow, push, crane, orbit, whip); cuts on actions.
- **Sound:** silence before the insight, music comes back on the punchline.

## Credits
- three.js (MIT). Kokoro-82M via kokoro-onnx (Apache-2.0). Fonts: Fredoka, Noto Sans TC (SIL OFL 1.1).
- Directing checklist adapted from Lemo-Opuscar's DIRECTOR.md (MIT / CC BY 4.0).
