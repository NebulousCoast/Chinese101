# CLAUDE.md: "What If I Could Freeze Time Whenever I Wanted?"

## Goal
Build a repeatable pipeline that renders one 9:16 vertical short (45–60 seconds) in a minimalist low-poly 3D storytelling style. The user runs one command and gets an MP4 ready for Instagram Reels and YouTube Shorts.

Work with the minimum manual steps. Automate everything that can be automated. When an asset must come from the user, use a clearly labeled placeholder and tell the user exactly what to supply.

## Source of truth
- `storyboard/storyboard.md`: beats, captions, and visual notes. Do not change the story without asking.
- `config/timeline.json`: all timings, camera keyframes, caption text, and HUD values. Generate this from the storyboard. Every other script reads from it.
- `config/style.json`: palette, fonts, safe zones, and audio levels.

If these files disagree with each other, stop and report the mismatch. Do not guess. (`make validate` checks this.)

## Decisions already made (session 1)
- Time bank starts at **30.0s** and drains at exactly 1 second per second, only inside freeze windows.
- One freeze per beat, growing in length: 3–5, 9–12, 16–20, 24–29, 33–39, 41–46, 50–55s. Beat 1 has no freeze (rain falls normally).
- Holds (world stopped, frozen look, no drain, music out): 46–48s (the lock in beat 7) and 55–57s (final card).
- Duration is **57.0s**: the bank hits 0.0 at 55.0s and the final card holds 2s.
- Wind under beats 1, 5, 6, 7, 8. Ground is procedural (no satellite texture).

## Technical spec (non-negotiable)
- Resolution: 1080 × 1920 (9:16). Preview renders: 540 × 960.
- Frame rate: 30 fps.
- Duration: 45–60 seconds. Verify with ffprobe after every final render.
- Video codec: H.264, yuv420p, `-movflags +faststart`.
- Audio: AAC 192 kbps stereo, 48 kHz, loudness normalized to −14 LUFS.
- Output: `out/final_9x16.mp4` and `out/preview_9x16.mp4`.

## Visual style
- Low-poly, flat-shaded geometry. No photorealistic textures.
- Flat colors from `style.json`. Use at most 6 base colors plus one accent for the HUD.
- Blocky human characters, low-poly animals, simple geometric environments.
- Ground may use satellite-style texture only if a licensed image is provided in `assets/satellite/`. Otherwise, use a procedural flat-colored ground.
- Soft lighting: one key area light, one fill, soft shadows via a shadow catcher.
- Cinematic camera: slow dolly-ins, orbits during freezes, and a final pull-out. Use keyframes from `timeline.json`. No shaky cam.
- Do not copy any existing creator's assets, characters, or exact compositions. Use the style as a general reference only.

## Freeze-time effect
- A "freeze" stops all character and object animation at the current frame.
- Visually mark a freeze: desaturate the frame by about 60%, add a faint vinyl-grain overlay, and hold the camera orbit.
- Freezes are defined by `start`, `end`, and `bank_drain` in `timeline.json`.

## HUD (the ticking number)
- Label: `TIME BANK`. Value format: `00.0s` (one decimal place).
- Position: top-center, below the safe-zone top margin.
- The value is computed from the timeline's `hud_keyframes` (time → value). Interpolate linearly during freezes. Do not hand-type values per frame.
- When the value is below 10s, the number turns red (`style.json: hud_warning`).
- The HUD must hold at `0.0s` for the final card.

## Captions and question
- Question: shown from 0.0s to 2.0s at the top of the frame, in bold sans-serif, and it must be readable without sound.
- Other captions: appear at the start time in `timeline.json` and fade out at the end time. Maximum 2 lines, maximum 32 characters per line.
- Keep all text inside the safe zone: top 250 px and bottom 350 px are reserved for platform UI.
- Render captions as transparent PNG overlays using Pillow, then composite with FFmpeg. Do not use FFmpeg `drawtext` for multi-line captions.

## Audio
- Voiceover: `assets/audio/vo/*.wav`, one file per beat, named `beat_01.wav` through `beat_08.wav`. If a file is missing, insert silence of the correct length and warn the user.
- Music: `assets/audio/music/lofi.mp3`. Loop it to fill the full duration.
- Duck music by about 8 dB during voiceover.
- Drop music entirely during freeze windows. Keep only the vinyl crackle layer (`assets/audio/sfx/vinyl.wav`) during freezes.
- Wind SFX: `assets/audio/sfx/wind.wav`, under outdoor beats (beats 1, 5, 6, 7, and 8), at −18 dB.
- If any audio asset is missing, use a generated placeholder tone or silence and list the missing files in your final report.

## Pipeline and file layout
```
project/
├── CLAUDE.md
├── README.md                  # Human-facing instructions (keep short)
├── config/
│   ├── timeline.json
│   ├── style.json
│   ├── timeline_lib.py        # Shared clocks/HUD/wrap helpers (also imported by Blender)
│   └── validate.py            # make validate
├── storyboard/storyboard.md
├── scenes/
│   ├── build_scene.py         # Blender scene builder (bpy) + beat choreography
│   ├── characters.py          # Blocky human and animal rigs
│   ├── environment.py         # Ground, town, props
│   ├── camera.py              # Keyframe camera paths
│   └── geo.py                 # Mesh helpers, shared materials, keyframe recorder
├── overlays/
│   ├── make_hud.py            # HUD PNG sequence from hud_keyframes
│   └── make_captions.py       # Caption PNGs from timeline
├── audio/
│   └── mix.py                 # Builds final audio track (ffmpeg / numpy)
├── compose/
│   ├── compose.sh             # Final FFmpeg assembly
│   └── verify.py              # Acceptance checklist + report
├── assets/                    # User-supplied, never overwritten
│   ├── audio/vo, music, sfx
│   ├── fonts/                 # optional: caption.ttf, hud_label.ttf, hud_value.ttf
│   └── satellite/
├── build/                     # Intermediate renders (safe to delete); build/<mode>/frames/beat_<n>/
├── out/                       # Final outputs only
└── Makefile
```

Build stages, in order:
1. `make validate`: check JSON schema, storyboard/timeline consistency, and that required assets exist.
2. `make scenes`: run Blender headless to render the beat frames as PNG sequences:
   `blender -b --factory-startup -P scenes/build_scene.py -- --beat <n> --out build/<mode>/frames/beat_<n>/ --mode <mode>`
3. `make overlays`: generate HUD and caption PNG sequences.
4. `make audio`: build `build/<mode>/audio/mix.wav`.
5. `make compose`: FFmpeg overlays HUD and captions on frames, then muxes with audio.
6. `make preview` runs stages 1–5 at 540×960 with `--samples 16`.
7. `make final` runs stages 1–5 at 1080×1920 with `--samples 128`, then verifies duration and resolution.

Provide a single entry point: `make all` runs `final`.

## Blender rules
- Use Blender in background mode only. No GUI.
- Use Eevee for previews and Cycles for final renders. Keep both paths working.
- Set the flat-shading material mode on all meshes. Use a small set of shared materials from `style.json`.
- Keep the scene in one file, with each beat as a collection. Animate with keyframes, not Python-driven per-frame logic, unless necessary.
- Seed any randomness (`random.seed(42)`) so renders are reproducible.

## Working rules for you (Claude Code)
- Before writing code, read `CLAUDE.md`, `config/timeline.json`, `config/style.json`, and `storyboard/storyboard.md`.
- Create or update the files above. Do not create other top-level directories without asking.
- Never overwrite files in `assets/`. Never delete anything outside `build/` without asking.
- Do not download music, images, or fonts from the internet. Tell the user what to supply instead.
- Do not add network calls to the build. The pipeline must run offline after setup.
- If Blender or FFmpeg is missing, stop, report the exact install step for the user's OS, and wait.
- Commit nothing without asking. Keep a short `CHANGELOG.md` of what changed in each session.
- When a render fails, read the log, fix the cause, and retry once. If it fails again, report the error and your best hypothesis.

## Setup checks (run first)
```
blender --version
ffmpeg -version
ffprobe -version
python3 -c "import PIL; print('Pillow ok')"
```
Install Python dependencies only with `pip install --break-system-packages pillow numpy pydub` if the user approves.
Headless Linux without a GPU also needs Mesa EGL for Eevee: `apt-get install libegl1 libgl1-mesa-dri`.

## Acceptance checklist (every final render)
- [ ] `ffprobe` reports 1080×1920, 30 fps, duration between 45.0 and 60.0 seconds.
- [ ] The question is visible at 0.0–2.0 s.
- [ ] HUD starts at 30.0s (`bank_start`), drains during each freeze, and ends at 0.0s.
- [ ] Every caption is inside the safe zone and matches `timeline.json`.
- [ ] Music drops out during freezes. Voiceover is audible over the music.
- [ ] Loudness is −14 LUFS ±1.
- [ ] No frames are missing (frame count equals duration × 30).
- [ ] Report any missing assets, placeholders used, and anything that differs from the storyboard.

## Output report format (end of every run)
1. What was built, with output file paths.
2. Verification results against the checklist.
3. Missing user-supplied assets (if any).
4. One suggested next change.
