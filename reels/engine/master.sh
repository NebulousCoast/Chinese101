#!/bin/sh
# Mux picture + mix; two-pass loudnorm to -14 LUFS (Reels/Shorts level), limiter at -1 dBFS.
set -e
V=$1; A=$2; OUTF=$3
J=$(ffmpeg -hide_banner -nostats -i "$A" -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$J" | sed -n "s/.*\"$1\" : \"\([^\"]*\)\".*/\1/p"; }
ffmpeg -y -loglevel error -i "$V" -i "$A" -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000,alimiter=limit=0.84:level=false" \
  -c:a aac -b:a 192k -shortest -movflags +faststart "$OUTF"
ffmpeg -hide_banner -nostats -i "$OUTF" -map 0:a -af ebur128=peak=true -f null - 2>&1 | grep -E '^\s+(I:|Peak:)' | tail -2
