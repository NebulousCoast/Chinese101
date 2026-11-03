#!/usr/bin/env bash
# Final FFmpeg assembly: frames + freeze look (desaturate + grain) + HUD + captions + audio.
#   bash compose/compose.sh preview|final
set -euo pipefail
MODE="${1:-preview}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build/$MODE"
OUT="$ROOT/out/${MODE}_9x16.mp4"
mkdir -p "$ROOT/out" "$BUILD"

# 1. Gather the per-beat PNG sequences into one global sequence (symlinks, no copies).
SEQ="$BUILD/seq"
rm -rf "$SEQ" && mkdir -p "$SEQ"
for d in "$BUILD"/frames/beat_*/; do
  for f in "$d"*.png; do [ -e "$f" ] && ln -sf "$f" "$SEQ/$(basename "$f")"; done
done

# 2. Build the filter graph and input list from timeline.json, style.json and the overlay manifests.
ROOT="$ROOT" python3 - "$MODE" "$BUILD" <<'PY'
import json, os, sys
root = os.environ["ROOT"]
sys.path.insert(0, os.path.join(root, "config"))
import timeline_lib as tl_lib
mode, build = sys.argv[1], sys.argv[2]
tl = tl_lib.Timeline()
st = tl_lib.style()
n = tl.total_frames
missing = [f for f in range(1, n + 1) if not os.path.exists(f"{build}/seq/{f:06d}.png")]
if missing:
    sys.exit(f"compose: {len(missing)} of {n} frames are missing (first: {missing[0]}, last: {missing[-1]}). "
             f"Run `make scenes MODE={mode}`.")
hud = json.load(open(f"{build}/overlays/hud.json"))
caps = json.load(open(f"{build}/overlays/captions.json"))
look = st["freeze_look"]
win = "+".join(f"between(t,{s:.3f},{e - 1e-3:.3f})" for s, e in tl.stopped)
dur = tl.duration
inputs = ["-framerate", "30", "-start_number", "1", "-i", f"{build}/seq/%06d.png",
          "-framerate", "30", "-start_number", "1", "-i", f"{build}/overlays/hud/%06d.png"]
g = [f"[0:v]format=yuv444p,hue=s={look['saturation']}:enable='{win}',"
     f"noise=alls={look['grain_strength']}:allf=t+u:enable='{win}'[base]",
     f"[base][1:v]overlay=x={hud['x']}:y={hud['y']}:format=auto[v0]"]
prev = "v0"
for i, c in enumerate(caps):
    idx = 2 + i
    inputs += ["-loop", "1", "-framerate", "30", "-t", f"{dur}", "-i", c["png"]]
    fo = c["fade_out"]
    g.append(f"[{idx}:v]format=rgba,fade=t=out:st={c['end'] - fo:.3f}:d={fo}:alpha=1[c{i}]")
    g.append(f"[{prev}][c{i}]overlay=0:0:format=auto:enable='between(t,{c['start']:.3f},{c['end']:.3f})'[v{i + 1}]")
    prev = f"v{i + 1}"
g.append(f"[{prev}]format=yuv420p[vout]")
inputs += ["-i", f"{build}/audio/mix.wav"]
open(f"{build}/compose_filter.txt", "w").write(";\n".join(g))
open(f"{build}/compose_inputs.txt", "w").write("\n".join(inputs))
open(f"{build}/compose_audio_index.txt", "w").write(str(2 + len(caps)))
print(f"[compose] {n} frames, {len(caps)} captions, freeze look on {len(tl.stopped)} windows")
PY

mapfile -t INPUTS < "$BUILD/compose_inputs.txt"
AIDX="$(cat "$BUILD/compose_audio_index.txt")"
DUR="$(python3 -c "import json;print(json.load(open('$ROOT/config/timeline.json'))['duration'])")"
if [ "$MODE" = "final" ]; then X264=(-preset slow -crf 17); else X264=(-preset veryfast -crf 22); fi

ffmpeg -hide_banner -loglevel error -nostats -y "${INPUTS[@]}" \
  -filter_complex_script "$BUILD/compose_filter.txt" \
  -map "[vout]" -map "${AIDX}:a" \
  -c:v libx264 "${X264[@]}" -pix_fmt yuv420p -r 30 \
  -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -t "$DUR" -movflags +faststart "$OUT"
echo "[compose] wrote $OUT"
