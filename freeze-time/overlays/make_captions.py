#!/usr/bin/env python3
"""One transparent full-frame PNG per caption (Pillow). FFmpeg composites them with timing + fade.

Writes build/<mode>/overlays/captions/<id>.png and captions.json.
"""
import argparse
import json
import os
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config"))
import timeline_lib as tl_lib  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="preview")
    a = ap.parse_args()
    tl = tl_lib.Timeline()
    st = tl_lib.style()
    W, H = st["render"][a.mode]["width"], st["render"][a.mode]["height"]
    L = st["layout_1080"]
    k = W / L["width"]
    font_file = tl_lib.font_path(st, "caption")[0]
    dark = tl_lib.hex_rgb(st["palette"]["dark"])
    light = tl_lib.hex_rgb(st["palette"]["light"])
    pad_x, pad_y, gap = L["caption_pad_x"] * k, L["caption_pad_y"] * k, L["caption_line_gap"] * k
    max_w = W - 2 * L["side_margin"] * k - 2 * pad_x
    safe_top, safe_bot = L["safe_top"] * k, H - L["safe_bottom"] * k

    out = tl_lib.path("build", a.mode, "overlays", "captions")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    manifest = []
    for c in tl.d["captions"]:
        lines = tl_lib.wrap_lines(c["text"], L["caption_max_chars"], L["caption_max_lines"])
        if lines is None:
            sys.exit(f"Caption '{c['id']}' does not fit in 2 lines of 32 characters")
        sty = c["style"]
        px = L[sty]["px"] * k
        probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        while True:  # shrink until every line fits the width
            font = ImageFont.truetype(font_file, round(px))
            if max(probe.textlength(s, font=font) for s in lines) <= max_w or px < 20 * k:
                break
            px *= 0.95
        asc, desc = font.getmetrics()
        line_h = asc + desc
        text_w = max(probe.textlength(s, font=font) for s in lines)
        box_w = text_w + 2 * pad_x
        box_h = len(lines) * line_h + (len(lines) - 1) * gap + 2 * pad_y
        if sty == "question":
            top = L["question"]["y"] * k
        elif sty == "lower":
            top = L["lower"]["bottom"] * k - box_h
        else:
            top = L["card"]["center_y"] * k - box_h / 2
        left = (W - box_w) / 2
        if top < safe_top or top + box_h > safe_bot:
            sys.exit(f"Caption '{c['id']}' box {top:.0f}-{top + box_h:.0f}px leaves the safe zone "
                     f"({safe_top:.0f}-{safe_bot:.0f}px)")
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((left, top, left + box_w, top + box_h), radius=round(22 * k),
                            fill=dark + (L["caption_bg_alpha"] if sty != "card" else 200,))
        y = top + pad_y
        for s in lines:
            w = d.textlength(s, font=font)
            d.text(((W - w) / 2, y), s, font=font, fill=light + (255,))
            y += line_h + gap
        p = os.path.join(out, f"{c['id']}.png")
        im.save(p)
        manifest.append({"id": c["id"], "png": p, "start": c["start"], "end": c["end"],
                         "fade_out": L["caption_fade_out"], "lines": lines,
                         "box": [round(left), round(top), round(left + box_w), round(top + box_h)]})
        print(f"[captions] {c['id']:9s} {c['start']:5.1f}-{c['end']:5.1f}s  {' / '.join(lines)}")
    with open(tl_lib.path("build", a.mode, "overlays", "captions.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)


if __name__ == "__main__":
    main()
