# Freeze Time short

A 57-second 9:16 low-poly short, rendered from config by Blender and FFmpeg.

## Make it

```bash
make preview   # 540x960, Eevee, ~1.5-2 h on a 4-core CPU
make all       # 1080x1920, Cycles 128 samples (use a GPU machine; see below)
```

Outputs: `out/preview_9x16.mp4`, `out/final_9x16.mp4`. The run ends with a checklist report.
Renders resume: re-running `make` skips frames that already exist. After changing a scene or
camera, delete that beat's frames (`rm -rf build/preview/frames/beat_4`) or run `make clean-frames`.

## Change the video

- Story, captions, VO lines: `storyboard/storyboard.md`, then mirror them in `config/timeline.json`.
- Timing, freezes, HUD, camera moves: `config/timeline.json`. `make validate` refuses mismatches.
- Colors, fonts, text layout, audio levels: `config/style.json`.

## Assets to supply (all optional; placeholders are used until then)

| File | What |
|---|---|
| `assets/audio/vo/beat_01.wav` … `beat_08.wav` | Kid voiceover, one per beat. Lines are in beats 1, 4, 6, 8. |
| `assets/audio/music/lofi.mp3` | Lo-fi beat you have rights to. Looped. |
| `assets/audio/sfx/vinyl.wav` | Vinyl crackle loop. |
| `assets/audio/sfx/wind.wav` | Wind loop. |
| `assets/fonts/caption.ttf`, `hud_label.ttf`, `hud_value.ttf` | Licensed fonts. |

## Requirements

Blender 4.x, FFmpeg, Python 3 with Pillow and numpy. Headless Linux without a GPU also needs
`libegl1 libgl1-mesa-dri` for Eevee. Cycles runs on CPU here; at 1080x1920 and 128 samples a
CPU-only final takes many hours, so run `make final` on a machine with a GPU
(enable it in `scenes/build_scene.py`, Cycles section, `cy.device = "GPU"`).
