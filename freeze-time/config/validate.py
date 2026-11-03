#!/usr/bin/env python3
"""make validate: schema, storyboard/timeline consistency, tools and assets.

Exit code 1 on any mismatch between the source-of-truth files (the pipeline must
stop rather than guess). Missing user assets are warnings: the build uses
placeholders and lists them in the final report.
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_lib as tl_lib  # noqa: E402

ERR, WARN = [], []


def err(m):
    ERR.append(m)


def warn(m):
    WARN.append(m)


def check_schema(d, s):
    for k in ["fps", "duration", "bank_start", "beats", "freezes", "hud_keyframes", "captions", "vo", "camera", "music", "sfx"]:
        if k not in d:
            err(f"timeline.json: missing key '{k}'")
    for k in ["palette", "hud_accent", "hud_warning", "fonts", "layout_1080", "render", "audio"]:
        if k not in s:
            err(f"style.json: missing key '{k}'")
    if ERR:
        return False
    if len(s["palette"]) > 6:
        err(f"style.json: {len(s['palette'])} base colors; the limit is 6")
    for name, h in list(s["palette"].items()) + [("hud_accent", s["hud_accent"]), ("hud_warning", s["hud_warning"])]:
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", h):
            err(f"style.json: color {name}={h} is not #RRGGBB")
    return True


def check_timeline(tl):
    d = tl.d
    if d["fps"] != 30:
        err(f"timeline.json: fps is {d['fps']}, spec requires 30")
    if not (45.0 <= tl.duration <= 60.0):
        err(f"timeline.json: duration {tl.duration}s is outside 45–60s")

    # Beats: contiguous from 0 to duration.
    t = 0.0
    for b in sorted(tl.beats, key=lambda b: b["start"]):
        if abs(b["start"] - t) > 1e-6:
            err(f"Beat {b['id']} starts at {b['start']}s; expected {t}s (beats must be contiguous)")
        t = b["end"]
    if abs(t - tl.duration) > 1e-6:
        err(f"Last beat ends at {t}s but duration is {tl.duration}s")

    # Freezes: inside their beat, non-overlapping, 1:1 drain.
    rate = float(d.get("drain_rate", 1.0))
    windows = sorted(tl.freezes + tl.holds)
    for (s0, e0), (s1, e1) in zip(windows, windows[1:]):
        if s1 < e0 - 1e-6:
            err(f"Freeze/hold windows overlap: {s0}–{e0}s and {s1}–{e1}s")
    for f in d["freezes"]:
        b = tl.beat(f["beat"])
        if not (b["start"] <= f["start"] < f["end"] <= b["end"]):
            err(f"Freeze {f['start']}–{f['end']}s is outside beat {f['beat']} ({b['start']}–{b['end']}s)")
        want = round((f["end"] - f["start"]) * rate, 6)
        if abs(f["bank_drain"] - want) > 1e-6:
            err(f"Freeze {f['start']}–{f['end']}s: bank_drain {f['bank_drain']} but 1:1 drain gives {want}")

    # HUD keyframes must equal what the freezes imply.
    exp = tl.expected_hud_keyframes()
    got = tl.hud_keys
    if len(exp) != len(got) or any(abs(a[0] - b[0]) > 1e-6 or abs(a[1] - b[1]) > 1e-6 for a, b in zip(exp, got)):
        err("hud_keyframes do not match the freeze windows.\n"
            f"    expected: {exp}\n    got:      {got}")
    if abs(tl.hud(0.0) - d["bank_start"]) > 1e-6:
        err(f"HUD starts at {tl.hud(0.0)}, bank_start is {d['bank_start']}")
    if abs(tl.hud(tl.duration)) > 1e-6:
        err(f"HUD ends at {tl.hud(tl.duration)}s; it must end at 0.0s")

    # Captions.
    s = tl_lib.style()["layout_1080"]
    q = [c for c in d["captions"] if c["style"] == "question"]
    if not q or q[0]["start"] != 0.0 or q[0]["end"] < 2.0:
        err("The question caption must run from 0.0s to at least 2.0s")
    for c in d["captions"]:
        if not (0 <= c["start"] < c["end"] <= tl.duration):
            err(f"Caption '{c['id']}' time {c['start']}–{c['end']}s is out of range")
        if tl_lib.wrap_lines(c["text"], s["caption_max_chars"], s["caption_max_lines"]) is None:
            err(f"Caption '{c['id']}' cannot fit in {s['caption_max_lines']} lines of {s['caption_max_chars']} chars")

    # Camera: every beat covered, segments contiguous.
    for b in tl.beats:
        segs = d["camera"].get(str(b["id"]))
        if not segs:
            err(f"No camera segments for beat {b['id']}")
            continue
        t = b["start"]
        for sgm in segs:
            if abs(sgm["t0"] - t) > 1e-6:
                err(f"Beat {b['id']} camera: segment starts at {sgm['t0']}s, expected {t}s")
            t = sgm["t1"]
        if abs(t - b["end"]) > 1e-6:
            err(f"Beat {b['id']} camera ends at {t}s, beat ends at {b['end']}s")
        if segs[0]["type"] != "dolly" or "from" not in segs[0]:
            err(f"Beat {b['id']} camera: first segment must be a dolly with 'from'")


def check_storyboard(tl):
    p = tl_lib.path("storyboard", "storyboard.md")
    if not os.path.exists(p):
        err("storyboard/storyboard.md is missing")
        return
    md = open(p, encoding="utf-8").read()
    heads = list(re.finditer(r"^## Beat (\d+) · ([\d.]+)–([\d.]+)s · (.+)$", md, re.M))
    if len(heads) != len(tl.beats):
        err(f"Storyboard has {len(heads)} beats, timeline has {len(tl.beats)}")
    for i, h in enumerate(heads):
        bid, s, e = int(h.group(1)), float(h.group(2)), float(h.group(3))
        body = md[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(md)]
        try:
            b = tl.beat(bid)
        except KeyError:
            err(f"Storyboard beat {bid} is not in the timeline")
            continue
        if abs(b["start"] - s) > 1e-6 or abs(b["end"] - e) > 1e-6:
            err(f"Beat {bid}: storyboard says {s}–{e}s, timeline says {b['start']}–{b['end']}s")
        hud = re.search(r"^\* HUD:(.*)$", body, re.M)
        if hud:
            nums = re.findall(r"(\d+(?:\.\d+)?)s", hud.group(1))
            if nums and abs(float(nums[-1]) - tl.hud(b["end"])) > 0.05:
                err(f"Beat {bid}: storyboard HUD ends at {nums[-1]}s, timeline HUD at beat end is {tl.hud(b['end']):.1f}s")
        cap = re.search(r"^\* Caption(?: \(final card\))?: (.+)$", body, re.M)
        if cap:
            text = cap.group(1).strip()
            if not any(c["text"] == text for c in tl.d["captions"]):
                err(f"Beat {bid}: storyboard caption “{text}” is not in timeline.json")
        vo = re.search(r"^\* VO: “(.+)”$", body, re.M)
        tvo = [v for v in tl.d["vo"] if int(v["beat"]) == bid]
        tline = tvo[0]["line"] if tvo else None
        if (vo.group(1) if vo else None) != tline:
            err(f"Beat {bid}: storyboard VO {vo.group(1) if vo else None!r} != timeline VO {tline!r}")
    for f in tl.d["freezes"]:
        if f"{f['start']:.1f}–{f['end']:.1f}s" not in md:
            err(f"Freeze {f['start']:.1f}–{f['end']:.1f}s is not in the storyboard freeze table")


def check_tools():
    for tool in ["blender", "ffmpeg", "ffprobe"]:
        if not shutil.which(tool):
            err(f"'{tool}' not found. Ubuntu/Debian: apt-get install {tool if tool != 'ffprobe' else 'ffmpeg'}. "
                "macOS: brew install --cask blender / brew install ffmpeg.")
    try:
        import PIL  # noqa: F401
        import numpy  # noqa: F401
    except ImportError as e:
        err(f"Python package missing ({e.name}). Install: pip install --break-system-packages pillow numpy")


def check_assets(tl):
    s = tl_lib.style()
    missing = []
    for v in tl.d["vo"]:
        if not os.path.exists(tl_lib.path(v["file"])):
            missing.append(v["file"] + ("" if v["line"] else "  (no line in storyboard; silence is fine)"))
    for f in [tl.d["music"]["file"], tl.d["sfx"]["vinyl"]["file"], tl.d["sfx"]["wind"]["file"]]:
        if not os.path.exists(tl_lib.path(f)):
            missing.append(f + "  (generated placeholder will be used)")
    for role in s["fonts"]:
        p, fb = tl_lib.font_path(s, role)
        if fb:
            missing.append(f"{s['fonts'][role]['file']}  (using {p})")
        if not os.path.exists(p):
            err(f"Font for '{role}' not found at {p}")
    sat = tl_lib.path("assets", "satellite")
    if os.path.isdir(sat) and [f for f in os.listdir(sat) if not f.startswith(".")]:
        warn("assets/satellite/ has files, but satellite ground is not wired in yet; using procedural ground")
    for m in missing:
        warn("Missing asset: " + m)


def main():
    d = tl_lib.load_json("timeline.json")
    s = tl_lib.style()
    if check_schema(d, s):
        tl = tl_lib.Timeline(d)
        check_timeline(tl)
        check_storyboard(tl)
        check_assets(tl)
    check_tools()
    for w in WARN:
        print("WARN  " + w)
    for e in ERR:
        print("ERROR " + e)
    if ERR:
        print(f"\nvalidate: {len(ERR)} error(s). Fix the mismatch before building.")
        sys.exit(1)
    print(f"validate: OK ({len(WARN)} warning(s))")


if __name__ == "__main__":
    main()
