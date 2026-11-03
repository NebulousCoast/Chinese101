# Changelog

## Session 1 — 2026-11-03
- Created the pipeline: validate, Blender scene build (8 beats, 6 sets), HUD and caption overlays,
  audio mix with generated placeholders, FFmpeg compose, verification report.
- Storyboard updated per decisions: 30.0s bank draining 1:1, one freeze per beat (2–6s),
  holds at 46–48s (the lock) and 55–57s (final card), 57.0s duration, rain falls normally in
  beat 1, wind under beats 1/5/6/7/8, procedural ground instead of satellite texture.
- Storyboard HUD lines now match the timeline (beat 6 ends at 10.0s; red starts in beat 7).
- Installed in this container: Blender 4.0.2, pydub, Mesa EGL (for headless Eevee).
