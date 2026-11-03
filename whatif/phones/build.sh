#!/bin/sh
# Build the film: voice → events → picture → sound → master.
# Needs: node + playwright (Chromium), ffmpeg, and a Python with kokoro-onnx numpy scipy soundfile.
#   PY=/path/to/python KOKORO=/dir/with/kokoro-v1.0.onnx+voices-v1.0.bin sh build.sh
set -e
HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"
PY=${PY:-python3}
[ -n "$KOKORO" ] && "$PY" tts.py "$KOKORO" af_sky          # skip to reuse voice/*.wav
node render.mjs events
"$PY" srt.py
"$PY" mix.py
node render.mjs video 24
sh master.sh out/video.mp4 out/mix.wav ../../videos/whatif-phones.mp4
