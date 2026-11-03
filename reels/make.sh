#!/bin/sh
# One command per episode:  sh make.sh <episode> [--no-voice]
#   1. voice     Kokoro TTS for every line in episodes/<ep>/lines.json   (skipped with --no-voice)
#   2. events    timeline + sound cues exported from the 3D page
#   3. picture   every frame rendered headless → out/video.mp4 (1080×1920, 30 fps)
#   4. sound     score + foley + voice → out/mix.wav
#   5. master    -14 LUFS → videos/<ep>.mp4, plus out/subtitles.srt
# Setup once: see README.md (PY = a Python with kokoro-onnx numpy scipy soundfile; KOKORO = model folder).
set -e
cd "$(dirname "$0")"
EP=$1; [ -f "episodes/$EP/episode.js" ] || { echo "usage: sh make.sh <episode>   (episodes: $(ls episodes | tr '\n' ' '))"; exit 2; }
PY=${PY:-python3}; WORKERS=${WORKERS:-3}; FPS=${FPS:-30}
[ "$2" = "--no-voice" ] || { echo "1/5 voice"; "$PY" engine/tts.py "$EP" "${KOKORO:?set KOKORO to the folder with kokoro-v1.0.onnx and voices-v1.0.bin}" "${VOICE:-af_sky}"; }
[ -f fonts/fredoka-600.woff2 ] && [ "$(find episodes -name lines.json -newer fonts/notosanstc-700-subset.woff2 | head -1)" = "" ] || python3 engine/fonts.py
echo "2/5 events";  node engine/render.mjs "$EP" events
echo "3/5 picture"; node engine/render.mjs "$EP" video "$FPS" "$WORKERS"
echo "4/5 sound";   "$PY" engine/mix.py "$EP"
echo "5/5 master";  mkdir -p videos; sh engine/master.sh "episodes/$EP/out/video.mp4" "episodes/$EP/out/mix.wav" "videos/$EP.mp4"; python3 engine/finish.py "$EP"
echo "done → reels/videos/$EP.mp4"
