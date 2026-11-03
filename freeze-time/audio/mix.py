#!/usr/bin/env python3
"""Builds the final audio track from timeline.json and style.json.

Layers: voiceover (one file per beat), lo-fi music (looped, ducked under VO, cut during
freezes/holds, slowed from beat 5, soft return in beat 8), vinyl crackle (only during
freezes/holds, plus one crackle at each freeze start), wind (outdoor beats, rising in beat 7).
Missing assets become generated placeholders (music/vinyl/wind) or silence (VO).
The mix is loudness-normalized to style.audio.target_lufs with a two-pass ffmpeg loudnorm.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config"))
import timeline_lib as tl_lib  # noqa: E402

SR = 48000
WARN = []


def db(x):
    return 10 ** (x / 20.0)


def load(path):
    """Decode any audio file to float32 stereo at 48 kHz, shape (n, 2)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()


def save_wav(path, x):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def loop_to(x, n):
    reps = int(np.ceil(n / len(x)))
    return np.tile(x, (reps, 1))[:n]


def moving_avg(x, width):
    """Centred moving average via cumulative sums (O(n) for any width)."""
    width = max(1, int(width))
    c = np.cumsum(np.concatenate([np.zeros(1), x.astype(np.float64)]))
    half = width // 2
    i = np.arange(len(x))
    lo = np.clip(i - half, 0, len(x))
    hi = np.clip(i - half + width, 0, len(x))
    return ((c[hi] - c[lo]) / width).astype(np.float32)


def window_mask(n, windows, ramp_s):
    """1 inside windows, 0 outside, with linear ramps of ramp_s centred on each edge."""
    m = np.zeros(n, dtype=np.float32)
    for s, e in windows:
        m[int(s * SR):int(e * SR)] = 1.0
    return moving_avg(m, ramp_s * SR)


# ------------------------------------------------------------------ placeholders


def fast_lowpass(x, width):
    return np.stack([moving_avg(x[:, c], width) for c in range(x.shape[1])], axis=1)


def gen_music(rng):
    bpm = 82
    beat = 60 / bpm
    bars = 4
    n = int(bars * 4 * beat * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    chords = [[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 64]]  # Am7 Fmaj7 Cmaj7 G6
    bar_n = int(4 * beat * SR)
    for b, ch in enumerate(chords):
        seg = slice(b * bar_n, (b + 1) * bar_n)
        tt = t[seg] - t[seg][0]
        env = np.minimum(tt / 0.25, 1.0) * np.exp(-tt * 0.35)
        for i, note in enumerate(ch):
            f = 440 * 2 ** ((note - 69) / 12)
            for det, pan in ((-0.6, 0.35), (0.6, 0.65)):
                tone = np.sin(2 * np.pi * (f + det) * tt) + 0.25 * np.sin(2 * np.pi * 2 * (f + det) * tt)
                out[seg, 0] += 0.05 * env * tone * (1 - pan)
                out[seg, 1] += 0.05 * env * tone * pan
        # bass
        fb = 440 * 2 ** ((ch[0] - 12 - 69) / 12)
        out[seg] += (0.16 * np.sin(2 * np.pi * fb * tt) * np.exp(-tt * 0.6))[:, None]
    # drums
    for i in range(bars * 4):
        s = int(i * beat * SR)
        L = int(0.35 * SR)
        tt = np.arange(L) / SR
        if i % 2 == 0:  # kick
            kick = np.sin(2 * np.pi * (45 + 60 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
            out[s:s + L] += (0.45 * kick)[:, None][: len(out[s:s + L])]
        else:  # soft snare
            sn = rng.standard_normal(L) * np.exp(-tt * 18)
            sn = np.diff(sn, prepend=0)
            out[s:s + L] += (0.08 * sn)[:, None][: len(out[s:s + L])]
        for h in (0.0, 0.5):  # hats
            hs = s + int(h * beat * SR)
            HL = int(0.05 * SR)
            hat = np.diff(rng.standard_normal(HL), prepend=0) * np.exp(-np.arange(HL) / SR * 80)
            out[hs:hs + HL] += (0.03 * hat)[:, None][: len(out[hs:hs + HL])]
    return (out / np.max(np.abs(out)) * 0.7).astype(np.float32)


def gen_vinyl(rng, seconds=6.0):
    n = int(seconds * SR)
    hiss = fast_lowpass(rng.standard_normal((n, 2)) * 0.05, 6)
    pops = np.zeros((n, 2))
    for _ in range(int(seconds * 9)):
        p = rng.integers(0, n - 200)
        L = rng.integers(20, 160)
        amp = rng.uniform(0.15, 0.6) * rng.choice([-1, 1])
        pops[p:p + L] += (amp * np.exp(-np.arange(L) / (L / 4)))[:, None] * rng.uniform(0.6, 1.0, 2)
    return (hiss + pops).astype(np.float32) * 0.6


def gen_wind(rng, seconds=10.0):
    n = int(seconds * SR)
    white = rng.standard_normal((n, 2))
    brown = np.cumsum(white, axis=0)
    brown -= fast_lowpass(brown, 4000)  # remove drift
    brown /= np.max(np.abs(brown))
    t = np.arange(n) / SR
    lfo = 0.55 + 0.45 * np.sin(2 * np.pi * t[:, None] / seconds * 2 + np.array([[0, 1.3]]))
    w = brown * lfo
    fade = int(0.5 * SR)
    w[:fade] *= np.linspace(0, 1, fade)[:, None]
    w[-fade:] *= np.linspace(1, 0, fade)[:, None]
    w[:fade] += w[-fade:][::-1] * 0  # (fades already make the seam silent-free at low level)
    return (w * 0.8).astype(np.float32)


def asset_or_placeholder(rel, gen, rng, name):
    p = tl_lib.path(rel)
    if os.path.exists(p):
        return load(p), False
    ph = tl_lib.path("build", "audio", "placeholders", f"{name}.wav")
    if not os.path.exists(ph):
        save_wav(ph, gen(rng))
    WARN.append(f"{rel} missing: using generated placeholder {os.path.relpath(ph, tl_lib.ROOT)}")
    return load(ph), True


# ------------------------------------------------------------------ mix
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    tl = tl_lib.Timeline()
    A = tl_lib.style()["audio"]
    rng = np.random.default_rng(42)
    N = int(round(tl.duration * SR))
    t = np.arange(N) / SR
    stops = tl.stopped
    edge = A["edge_fade_s"]
    report = {"placeholders": [], "missing_vo": []}

    # Voiceover.
    vo = np.zeros((N, 2), dtype=np.float32)
    for v in tl.d["vo"]:
        p = tl_lib.path(v["file"])
        beat = tl.beat(v["beat"])
        if not os.path.exists(p):
            if v["line"]:
                WARN.append(f"{v['file']} missing: inserted {beat['end'] - beat['start']:.1f}s of silence "
                            f"(line: “{v['line']}”)")
                report["missing_vo"].append(v["file"])
            continue
        x = load(p) * db(A["vo_db"])
        s = int(v["start"] * SR)
        if s + len(x) > int(beat["end"] * SR):
            WARN.append(f"{v['file']} runs {(s + len(x)) / SR - beat['end']:.2f}s past the end of beat {v['beat']}")
        x = x[: max(0, N - s)]
        vo[s:s + len(x)] += x

    # Music: looped, time-warped (slower + lower) from slow_from.
    mus_src, ph = asset_or_placeholder(tl.d["music"]["file"], gen_music, rng, "music")
    if ph:
        report["placeholders"].append("music")
    rate = A["music_slow_rate"]
    slow_from = tl.d["music"]["slow_from"]
    src_t = np.where(t < slow_from, t, slow_from + (t - slow_from) * rate)
    looped = loop_to(mus_src, int(src_t[-1] * SR) + 2)
    idx = src_t * SR
    music = np.stack([np.interp(idx, np.arange(len(looped)), looped[:, c]) for c in range(2)], axis=1)
    g = np.full(N, db(A["music_db"]), dtype=np.float32)
    mutes = []
    if tl.d["music"].get("mute_during_freezes", True):
        mutes += tl.freezes
    if tl.d["music"].get("mute_during_holds", True):
        mutes += tl.holds
    mutes += [tuple(m) for m in tl.d["music"].get("extra_mutes", [])]
    g *= 1 - window_mask(N, mutes, edge)
    for sw in tl.d["music"].get("soft", []):
        fin = np.clip((t - sw["start"]) / sw["fade_in"], 0, 1)
        inside = (t >= sw["start"]) & (t < sw["end"])
        g = np.where(inside, g * db(A["music_soft_db"]) * fin, g)
    # Duck under voiceover.
    act = (np.abs(vo).max(axis=1) > 0.01).astype(np.float32)
    act = moving_avg(act, 0.3 * SR)
    act = np.clip(act * 4, 0, 1)
    g *= 1 - act * (1 - db(A["duck_db"]))
    music *= g[:, None]
    in_mute = window_mask(N, mutes, 0.001) > 0.5
    edge_n = int(0.1 * SR)
    core = in_mute & (moving_avg(in_mute.astype(np.float32), edge_n * 2) > 0.999)  # ignore the fade edges
    report["music_rms_db_in_freezes"] = float(20 * np.log10(np.sqrt(np.mean(music[core] ** 2)) + 1e-12))
    report["music_rms_db_outside"] = float(20 * np.log10(np.sqrt(np.mean(music[~in_mute] ** 2)) + 1e-12))

    # Vinyl crackle: freezes and holds only, plus a single crackle at each freeze start.
    vin_src, ph = asset_or_placeholder(tl.d["sfx"]["vinyl"]["file"], gen_vinyl, rng, "vinyl")
    if ph:
        report["placeholders"].append("vinyl")
    vinyl = loop_to(vin_src, N) * window_mask(N, stops, edge)[:, None] * db(A["vinyl_db"])
    for s, _ in tl.freezes:
        p = int(s * SR)
        L = int(0.012 * SR)
        click = np.exp(-np.arange(L) / (L / 5)) * 0.5
        vinyl[p:p + L] += np.stack([click, click * 0.8], axis=1)[: len(vinyl[p:p + L])]

    # Wind under outdoor beats; rises through the rise beat.
    wind_src, ph = asset_or_placeholder(tl.d["sfx"]["wind"]["file"], gen_wind, rng, "wind")
    if ph:
        report["placeholders"].append("wind")
    wb = [tl.beat(b) for b in tl.d["sfx"]["wind"]["beats"]]
    wmask = window_mask(N, [(b["start"], b["end"]) for b in wb], 0.5)
    wg = np.full(N, db(A["wind_db"]))
    rb = tl.d["sfx"]["wind"].get("rise_beat")
    if rb:
        b = tl.beat(rb)
        rise = np.clip((t - b["start"]) / (b["end"] - b["start"]), 0, 1)
        rise = np.where(t >= b["end"], 1.0, rise)
        wg *= db(A["wind_rise_db"] * rise)
    wind = loop_to(wind_src, N) * (wmask * wg)[:, None]

    mix = vo + music + vinyl + wind
    peak = float(np.max(np.abs(mix)))
    if peak > 0.99:
        mix *= 0.99 / peak
    raw = os.path.splitext(a.out)[0] + "_raw.wav"
    save_wav(raw, mix)

    # Loudness: gain toward the target, brick-wall limit for true-peak headroom, re-measure, correct once.
    tgt, tp = A["target_lufs"], A["true_peak_db"]
    lim = 10 ** ((tp - 0.5) / 20)  # extra 0.5 dB margin for AAC overshoot

    def measure(path):
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true",
                            "-f", "null", "-"], capture_output=True, text=True)
        return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])

    def render(gain_db, dst):
        af = (f"volume={gain_db:.3f}dB,alimiter=limit={lim:.4f}:attack=3:release=60:level=false,"
              f"aresample={SR * 4},alimiter=limit={lim:.4f}:attack=1:release=40:level=false,aresample={SR}")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", af, "-ac", "2",
                        "-c:a", "pcm_s16le", dst], check=True)

    m_in = measure(raw)
    gain = tgt - m_in
    for _ in range(3):
        render(gain, a.out)
        got = measure(a.out)
        if abs(got - tgt) <= 0.3:
            break
        gain += tgt - got
    m = {"input_i": m_in, "output_i": got, "gain_db": gain}
    report["loudness"] = m
    report["warnings"] = WARN
    with open(os.path.splitext(a.out)[0] + "_report.json", "w") as fh:
        json.dump(report, fh, indent=1)
    for w in WARN:
        print("WARN  " + w)
    print(f"[audio] {tl.duration:.1f}s mix: {m_in:.1f} LUFS -> {got:.1f} LUFS (gain {gain:+.1f} dB, "
          f"limit {tp - 0.5:.1f} dBFS) -> {a.out}")


if __name__ == "__main__":
    main()
