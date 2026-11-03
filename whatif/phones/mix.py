"""Score + foley + voice → out/mix.wav, all driven by events.json (exported from the page).

Instruments are synthesised here (no samples): a Karplus–Strong ukulele and bass,
a glockenspiel from inharmonic partials, a soft shaker. Foley follows the page:
marker squeaks while lines draw, pops, paper flips, knocks, a pigeon.
Usage: python mix.py
"""
import json, pathlib
import numpy as np, soundfile as sf
from scipy.signal import lfilter, butter, sosfilt

HERE = pathlib.Path(__file__).parent
SR = 48000
E = json.loads((HERE / "events.json").read_text())
DUR = E["dur"]; N = int(DUR * SR) + SR
SEC = {s["id"]: s for s in E["secs"]}; OUT = E["out"]
rng = np.random.default_rng(7)

music = np.zeros((N, 2)); sfx = np.zeros((N, 2)); voice = np.zeros((N, 2))

def add(buf, x, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or len(x) == 0: return
    x = x[: N - i] * gain
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * l * 1.414; buf[i:i + len(x), 1] += x * r * 1.414

def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)
def lp(x, f): return sosfilt(butter(2, f, btype="low", fs=SR, output="sos"), x)
def hp(x, f): return sosfilt(butter(2, f, btype="high", fs=SR, output="sos"), x)
def env(n, a=.005, rel=.05):
    e = np.ones(n); na, nr = max(1, int(a * SR)), max(1, int(rel * SR))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
def midi(m): return 440.0 * 2 ** ((m - 69) / 12)

# ── instruments ──
def pluck(f, dur=1.6, bright=.6, decay=.996):
    n = int(dur * SR); D = SR / f; Ni = int(D); frac = D - Ni
    exc = lp(rng.uniform(-1, 1, Ni + 2), 1500 + 6000 * bright)
    x = np.zeros(n); x[:len(exc)] = exc
    a = np.zeros(Ni + 2); a[0] = 1; a[Ni] -= decay * (1 - frac) * .5 + decay * .25; a[Ni + 1] -= decay * frac * .5 + decay * .25
    y = lfilter([1.0], a, x)
    y = lp(y, 5000) * env(n, .002, .08)
    return y / (np.max(np.abs(y)) + 1e-9)

def glock(f, dur=1.8):
    n = int(dur * SR); t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f * t) * np.exp(-t * 3.2) + .45 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 7)
         + .2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 14))
    return y * env(n, .001, .1) * .7

def shaker(dur=.09):
    n = int(dur * SR); return hp(rng.uniform(-1, 1, n), 5000) * np.exp(-np.arange(n) / SR * 40)

# ── foley ──
def marker(dur, loud=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    x = bp(rng.uniform(-1, 1, n), 1800, 5200)
    am = .55 + .45 * np.sin(2 * np.pi * (7 + 3 * np.sin(t * 2.3)) * t) ** 2     # stroke rhythm
    return x * am * env(n, .02, .06) * .35 * loud

def popsnd(hi=0):
    n = int(.09 * SR); t = np.arange(n) / SR
    f = (900 if hi else 620) * np.exp(-t * 18) + (300 if hi else 200)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38) * .8

def whoosh(dur, soft=0):
    n = int(dur * SR); t = np.linspace(0, 1, n)
    x = rng.uniform(-1, 1, n); out = np.zeros(n); blk = 2048
    for i in range(0, n, blk):   # sweeping band
        c = 400 + 2600 * np.sin(np.pi * t[i]) ** 2
        out[i:i + blk] = bp(x[i:i + blk], c * .6, c * 1.5)[: len(out[i:i + blk])]
    return out * np.sin(np.pi * t) ** 2 * (.25 if soft else .4)

def poof():
    n = int(.35 * SR); return lp(rng.uniform(-1, 1, n), 900) * np.exp(-np.arange(n) / SR * 12) * .9

def flip():
    n = int(.11 * SR); t = np.arange(n) / SR
    return hp(rng.uniform(-1, 1, n), 1500) * np.exp(-t * 30) * (1 - np.exp(-t * 400)) * .6

def knock():
    n = int(.14 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 170 * t) * np.exp(-t * 45) + lp(rng.uniform(-1, 1, n), 2000) * np.exp(-t * 120) * .6) * .9

def coo():
    out = np.zeros(int(.9 * SR))
    for k, (f0, f1, st, d) in enumerate([(520, 430, 0, .28), (560, 420, .38, .42)]):
        n = int(d * SR); t = np.arange(n) / SR; f = np.linspace(f0, f1, n)
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 + .4 * np.sin(2 * np.pi * 28 * t)) * np.sin(np.pi * t / d)
        y += .3 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR) * np.sin(np.pi * t / d)
        out[int(st * SR):int(st * SR) + n] += lp(y, 1800)
    return out * .35

def flutter(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    return bp(rng.uniform(-1, 1, n), 700, 3000) * (np.sin(2 * np.pi * 11 * t) ** 8) * env(n, .1, .3) * .35

def click():
    n = int(.12 * SR); y = np.zeros(n); t = np.arange(int(.012 * SR)) / SR
    for st in (0, .06):
        i = int(st * SR); y[i:i + len(t)] += hp(rng.uniform(-1, 1, len(t)), 2500) * np.exp(-t * 400)
    return y * .8

PENTA = [72, 74, 76, 79, 81, 84, 86]   # C major pentatonic, upper register

for e in E["ev"]:
    t, ty = e["t"], e["type"]
    pan = float(rng.uniform(-.35, .35))
    if ty == "draw": add(sfx, marker(e.get("dur", .6)), t, .9, pan)
    elif ty == "pop": add(sfx, popsnd(e.get("hi", 0)), t, .55, pan)
    elif ty == "scribble": add(sfx, marker(e["dur"], 1.8), t, 1.0, .2)
    elif ty == "poof": add(sfx, poof(), t, .6, .2)
    elif ty == "whoosh": add(sfx, whoosh(e["dur"], e.get("soft", 0)), t, .7, 0)
    elif ty == "flip": add(sfx, flip(), t, .7, .5)
    elif ty == "knock": add(sfx, knock(), t, .9, .4)
    elif ty == "coo": add(sfx, coo(), t, .8, -.4)
    elif ty == "flutter": add(sfx, flutter(e["dur"]), t, .6, -.3)
    elif ty == "click": add(sfx, click(), t, .6, .5)
    elif ty == "ding":
        if e.get("logo"): add(music, glock(midi([72, 76, 79, 81, 84][e["step"]])), t, .55, -.4 + .2 * e["step"])
        elif e["step"] == 9: add(music, glock(midi(84)), t, .6, 0); add(music, glock(midi(91)), t + .02, .25, 0)
        else: add(music, glock(midi(PENTA[e["step"] % len(PENTA)])), t, .45, .3)
    elif ty == "voice":
        v, sr = sf.read(HERE / "voice" / f"{e['id']}.wav")
        assert sr == SR, sr
        add(voice, v, t, 1.0, 0)

# ── score: 100 bpm, I–V–vi–IV ukulele with bass and shaker ──
BPM = 100; B = 60 / BPM
CHORDS = [[60, 64, 67, 72], [59, 62, 67, 71], [57, 60, 64, 69], [57, 60, 65, 69]]   # C G Am F (uke voicings)
BASS = [36, 43, 45, 41]
A = SEC["wonder"]; er = A["v0"] + A["vd"] + .35
music_in = er + .45                     # silence until the phone goes "poof"
E_ = SEC["find"]; gap = (E_["t0"] + .4, E_["v0"] + .42 * E_["vd"])   # a held breath before "1876"
end_at = OUT["card"] + 0.4 + 4 * .26
STRUM = [(0, .9, 1), (1.5, .55, -1), (2, .8, 1), (3, .6, -1), (3.5, .5, 1)]   # beat, vel, direction
t = music_in; bar = 0
while t < end_at - .01:
    ch, bass = CHORDS[bar % 4], BASS[bar % 4]
    for beat, vel, d in STRUM:
        tt = t + beat * B
        if gap[0] <= tt < gap[1] or tt >= end_at: continue
        notes = ch if d > 0 else ch[::-1]
        for k, m in enumerate(notes):
            add(music, pluck(midi(m), 1.4, .45 + .2 * vel), tt + k * .012, .16 * vel, -.25 + .15 * k)
        add(music, shaker(), tt + B / 2, .05, .45)
    for beat in (0, 2):
        tt = t + beat * B
        if not (gap[0] <= tt < gap[1]): add(music, pluck(midi(bass), 1.2, .2, .993), tt, .32, 0)
    t += 4 * B; bar += 1
# final chord on the last logo letter
for k, m in enumerate([48, 60, 64, 67, 72, 76]):
    add(music, pluck(midi(m), 3.5, .5, .998), end_at + k * .02, .2, -.3 + .12 * k)
add(music, glock(midi(84), 3.0), end_at + .05, .35, 0)
# a recorder-like tune on the reveal: sine + soft 3rd harmonic
def recorder(f, dur):
    n = int(dur * SR); tt = np.arange(n) / SR; vib = 1 + .004 * np.sin(2 * np.pi * 5.5 * tt) * np.minimum(1, tt * 3)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    return (np.sin(ph) + .18 * np.sin(3 * ph) + .02 * rng.uniform(-1, 1, n)) * env(n, .04, .12) * .5
tune = [(76, 1), (79, 1), (81, 2), (79, 1), (76, 1), (72, 2)]
tt = OUT["t0"] + .3
for m, beats in tune:
    add(music, recorder(midi(m), beats * B * .95), tt, .22, .1); tt += beats * B

# ── ambience: quiet room tone ──
room = lp(rng.uniform(-1, 1, N), 600) * .012
music[:, 0] += room; music[:, 1] += room

# ── mix: compress voice, duck music under it ──
def compress(x, thr=.25, ratio=3.0):
    a = np.abs(x).max(axis=1); envl = lfilter([.002], [1, -.998], a)
    gain = np.where(envl > thr, (thr + (envl - thr) / ratio) / np.maximum(envl, 1e-9), 1.0)
    return x * gain[:, None]
voice = voice / (np.abs(voice).max() + 1e-9) * .9
voice = compress(voice)
vact = lfilter([.0005], [1, -.9995], (np.abs(voice).max(axis=1) > .02).astype(float))
duck = 1 - .55 * np.clip(vact * 1.6, 0, 1)
mix = music * duck[:, None] * .9 + sfx * .8 + voice * 1.25
mix = np.tanh(mix * .9) / .9 * .7      # gentle safety limit; loudnorm happens in ffmpeg
(HERE / "out").mkdir(exist_ok=True)
sf.write(HERE / "out" / "mix.wav", mix[: int(DUR * SR)], SR, subtype="PCM_24")

def rms_db(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
vm = (np.abs(voice).max(axis=1) > .02)
print("voice RMS (where speaking) %.1f dB, music RMS there %.1f dB" % (rms_db(voice[vm] * 1.25), rms_db(music[vm] * duck[vm, None] * .9)))
print("wrote out/mix.wav", round(DUR, 2), "s")
