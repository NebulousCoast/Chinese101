"""Shared timeline helpers. Pure Python (no numpy) so Blender's Python can import it too.

Every script reads timing from config/timeline.json through this module.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path(*parts):
    return os.path.join(ROOT, *parts)


def load_json(name):
    with open(path("config", name), encoding="utf-8") as f:
        return json.load(f)


class Timeline:
    def __init__(self, data=None):
        self.d = data if data is not None else load_json("timeline.json")
        self.fps = int(self.d["fps"])
        self.duration = float(self.d["duration"])
        self.beats = self.d["beats"]
        self.freezes = [(float(f["start"]), float(f["end"])) for f in self.d["freezes"]]
        self.holds = [(float(h["start"]), float(h["end"])) for h in self.d.get("holds", [])]
        # Windows where the world clock is stopped and the frozen look applies.
        self.stopped = sorted(self.freezes + self.holds)
        self.hud_keys = [(float(t), float(v)) for t, v in self.d["hud_keyframes"]]

    # ---- frames -------------------------------------------------------
    @property
    def total_frames(self):
        return int(round(self.duration * self.fps))

    def t_of(self, frame):
        """Blender/global frames start at 1. Frame 1 is t=0."""
        return (frame - 1) / self.fps

    def frame_range(self, beat_id):
        b = self.beat(beat_id)
        return int(round(b["start"] * self.fps)) + 1, int(round(b["end"] * self.fps))

    def beat(self, beat_id):
        for b in self.beats:
            if int(b["id"]) == int(beat_id):
                return b
        raise KeyError(beat_id)

    def beat_at(self, t):
        for b in self.beats:
            if b["start"] <= t < b["end"]:
                return b
        return self.beats[-1]

    # ---- clocks -------------------------------------------------------
    def is_stopped(self, t):
        return any(s <= t < e for s, e in self.stopped)

    def in_freeze(self, t):
        return any(s <= t < e for s, e in self.freezes)

    def world(self, t):
        """World clock: real time minus all time spent stopped before t."""
        w = t
        for s, e in self.stopped:
            if t > s:
                w -= min(t, e) - s
        return w

    # ---- HUD ----------------------------------------------------------
    def hud(self, t):
        k = self.hud_keys
        if t <= k[0][0]:
            return k[0][1]
        for (t0, v0), (t1, v1) in zip(k, k[1:]):
            if t0 <= t <= t1:
                if t1 == t0:
                    return v1
                return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
        return k[-1][1]

    def expected_hud_keyframes(self):
        """HUD keyframes implied by bank_start, drain_rate and the freeze windows."""
        rate = float(self.d.get("drain_rate", 1.0))
        bank = float(self.d["bank_start"])
        keys = [(0.0, bank)]
        for f in sorted(self.d["freezes"], key=lambda f: f["start"]):
            keys.append((float(f["start"]), bank))
            bank -= (float(f["end"]) - float(f["start"])) * rate
            keys.append((float(f["end"]), round(bank, 6)))
        keys.append((self.duration, round(bank, 6)))
        return keys

    def is_draining(self, t):
        return self.in_freeze(t)

    # ---- helpers for scene building -------------------------------------
    def freeze_in_beat(self, beat_id):
        for f in self.d["freezes"]:
            if int(f["beat"]) == int(beat_id):
                return float(f["start"]), float(f["end"])
        return None


def wrap_lines(text, max_chars, max_lines):
    """Same balanced wrap the caption renderer uses. Returns None if it cannot fit."""
    words = text.split()
    if len(text) <= max_chars:
        return [text]
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if len(a) <= max_chars and len(b) <= max_chars:
            score = max(len(a), len(b))
            if best is None or score < best[0]:
                best = (score, [a, b])
    if best and max_lines >= 2:
        return best[1]
    return None


def style():
    return load_json("style.json")


def font_path(style_d, role):
    f = style_d["fonts"][role]
    p = path(f["file"])
    if os.path.exists(p):
        return p, False
    return f["fallback"], True


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
