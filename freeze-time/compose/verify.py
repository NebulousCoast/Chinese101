#!/usr/bin/env python3
"""Checks the rendered MP4 against the acceptance checklist and prints the run report."""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config"))
import timeline_lib as tl_lib  # noqa: E402


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", path],
                       check=True, capture_output=True, text=True)
    return json.loads(r.stdout)


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-map", "0:a", "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True)
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    return float(i[-1]), float(tp[-1]) if tp else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="preview")
    a = ap.parse_args()
    tl = tl_lib.Timeline()
    st = tl_lib.style()
    W, H = st["render"][a.mode]["width"], st["render"][a.mode]["height"]
    out = tl_lib.path("out", f"{a.mode}_9x16.mp4")
    build = tl_lib.path("build", a.mode)
    if not os.path.exists(out):
        sys.exit(f"verify: {out} does not exist")
    p = probe(out)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    au = next(s for s in p["streams"] if s["codec_type"] == "audio")
    dur = float(p["format"]["duration"])
    fps = eval(v["r_frame_rate"])
    nframes = int(v["nb_read_frames"])
    want_frames = round(tl.duration * 30)
    I, TP = lufs(out)
    caps = json.load(open(os.path.join(build, "overlays", "captions.json")))
    k = W / 1080
    safe_top, safe_bot = st["layout_1080"]["safe_top"] * k, H - st["layout_1080"]["safe_bottom"] * k
    caps_ok = all(c["box"][1] >= safe_top and c["box"][3] <= safe_bot for c in caps)
    caps_match = [c["text"] for c in tl.d["captions"]] == [" ".join(c["lines"]) for c in caps]
    q = [c for c in caps if c["id"] == "question"][0]
    arep_p = os.path.join(build, "audio", "mix_report.json")
    arep = json.load(open(arep_p)) if os.path.exists(arep_p) else {}
    hud0, hud1 = tl.hud(0.0), tl.hud(tl.duration)
    drains = all(tl.hud(e) < tl.hud(s) for s, e in tl.freezes)

    checks = [
        (f"ffprobe: {v['width']}x{v['height']} (want {W}x{H}), {fps:g} fps, {dur:.2f}s (45.0–60.0)",
         v["width"] == W and v["height"] == H and abs(fps - 30) < 1e-6 and 45.0 <= dur <= 60.0),
        (f"codec {v['codec_name']}/{v['pix_fmt']}, audio {au['codec_name']} {au['sample_rate']} Hz "
         f"{au['channels']}ch {int(au.get('bit_rate', 0)) // 1000} kb/s",
         v["codec_name"] == "h264" and v["pix_fmt"] == "yuv420p" and au["codec_name"] == "aac"
         and au["sample_rate"] == "48000" and au["channels"] == 2),
        (f"question visible {q['start']:.1f}–{q['end']:.1f}s", q["start"] == 0.0 and q["end"] >= 2.0),
        (f"HUD starts {hud0:.1f}s, drains in all {len(tl.freezes)} freezes, ends {hud1:.1f}s",
         abs(hud0 - tl.d["bank_start"]) < 1e-6 and drains and abs(hud1) < 1e-6),
        (f"captions inside safe zone ({safe_top:.0f}–{safe_bot:.0f}px) and match timeline.json", caps_ok and caps_match),
        (f"music in freezes {arep.get('music_rms_db_in_freezes', float('nan')):.0f} dBFS vs "
         f"{arep.get('music_rms_db_outside', float('nan')):.0f} dBFS outside; VO files present: "
         f"{sum(os.path.exists(tl_lib.path(x['file'])) for x in tl.d['vo'])}/8 (4 beats have lines)",
         arep.get("music_rms_db_in_freezes", 0) < -80),
        (f"loudness {I:.1f} LUFS (target {st['audio']['target_lufs']} ±1), true peak {TP} dBFS",
         abs(I - st["audio"]["target_lufs"]) <= 1.0),
        (f"frames {nframes} = {tl.duration:g}s x 30 = {want_frames}", nframes == want_frames),
    ]
    print(f"\n=== {a.mode.upper()} REPORT ===")
    print(f"1. Built: {os.path.relpath(out, tl_lib.ROOT)}  ({os.path.getsize(out) / 1e6:.1f} MB)")
    print("2. Checklist:")
    ok = True
    for text, good in checks:
        ok &= good
        print(f"   [{'x' if good else ' '}] {text}")
    print("3. Missing user assets / placeholders:")
    for w in arep.get("warnings", []):
        print("   - " + w)
    for role in st["fonts"]:
        pth, fb = tl_lib.font_path(st, role)
        if fb:
            print(f"   - {st['fonts'][role]['file']} missing: using {pth}")
    if not ok:
        sys.exit("verify: one or more checks failed")


if __name__ == "__main__":
    main()
