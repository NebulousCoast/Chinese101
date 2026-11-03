#!/usr/bin/env python3
"""HUD PNG sequence: one small RGBA image per frame, values from timeline hud_keyframes.

Writes build/<mode>/overlays/hud/%06d.png and hud.json (position for compose).
"""
import argparse
import json
import math
import os
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config"))
import timeline_lib as tl_lib  # noqa: E402


def display_value(v):
    """Count-down display: round up to the tenth, so 0.0 shows only when the bank is empty."""
    return max(0.0, math.ceil(v * 10 - 1e-6) / 10)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="preview")
    a = ap.parse_args()
    tl = tl_lib.Timeline()
    st = tl_lib.style()
    W = st["render"][a.mode]["width"]
    L = st["layout_1080"]
    k = W / L["width"]
    hud = L["hud"]
    bw, bh = round(hud["width"] * k), round(hud["height"] * k)
    x = (W - bw) // 2
    y = round(hud["y"] * k)
    assert y >= L["safe_top"] * k, "HUD is above the top safe zone"

    f_label = ImageFont.truetype(tl_lib.font_path(st, "hud_label")[0], round(hud["label_px"] * k))
    f_value = ImageFont.truetype(tl_lib.font_path(st, "hud_value")[0], round(hud["value_px"] * k))
    dark = tl_lib.hex_rgb(st["palette"]["dark"])
    light = tl_lib.hex_rgb(st["palette"]["light"])
    accent = tl_lib.hex_rgb(st["hud_accent"])
    warn = tl_lib.hex_rgb(st["hud_warning"])
    below = st["hud_warning_below"]

    out = tl_lib.path("build", a.mode, "overlays", "hud")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    cache = {}
    label = "TIME BANK"
    track = 0.2 * hud["label_px"] * k

    def draw(text, color, alpha, draining):
        im = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=round(hud["radius"] * k), fill=dark + (hud["bg_alpha"],))
        # Letter-spaced label.
        widths = [d.textlength(ch, font=f_label) for ch in label]
        total = sum(widths) + track * (len(label) - 1)
        cx = (bw - total) / 2
        ly = round(22 * k)
        for ch, w in zip(label, widths):
            d.text((cx, ly), ch, font=f_label, fill=light + (215,))
            cx += w + track
        # Value.
        tw = d.textlength(text, font=f_value)
        vy = round(bh * 0.36)
        d.text(((bw - tw) / 2, vy), text, font=f_value, fill=color + (alpha,))
        if draining:  # thin bar under the value marks "time is being spent"
            d.rounded_rectangle((bw * 0.3, bh - round(16 * k), bw * 0.7, bh - round(10 * k)),
                                radius=round(3 * k), fill=color + (alpha,))
        return im

    n = tl.total_frames
    for f in range(1, n + 1):
        t = tl.t_of(f)
        v = display_value(tl.hud(t))
        draining = tl.is_draining(t)
        red = v < below
        color = warn if red else accent
        alpha = 255
        if red and draining and int(t * 4) % 2 == 1:
            alpha = 110  # flashes while it drains below the warning line
        key = (v, color, alpha, draining)
        if key not in cache:
            p = os.path.join(out, f"_{len(cache)}.png")
            draw(f"{v:04.1f}s", color, alpha, draining).save(p, compress_level=3)
            cache[key] = p
        os.link(cache[key], os.path.join(out, f"{f:06d}.png"))
    with open(tl_lib.path("build", a.mode, "overlays", "hud.json"), "w") as fh:
        json.dump({"x": x, "y": y, "w": bw, "h": bh}, fh)
    print(f"[hud] {n} frames ({len(cache)} unique) at {bw}x{bh}, position {x},{y} -> {out}")
    print(f"[hud] start {display_value(tl.hud(0)):04.1f}s, end {display_value(tl.hud(tl.duration)):04.1f}s")


if __name__ == "__main__":
    main()
