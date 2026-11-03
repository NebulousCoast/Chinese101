"""Soundtrack for an episode: score + foley + voice → episodes/<ep>/out/mix.wav.
Everything is synthesised (no samples) and placed by events.json, which the page exports.

Score: a playful marimba + plucked bass + soft kick/shaker groove (I–vi–IV–V), with the
gaps the episode asks for (music.stops) and a final chord (music.finalAt).
Usage: python engine/mix.py <ep>
"""
import json, sys, pathlib
import numpy as np, soundfile as sf
from scipy.signal import lfilter, butter, sosfilt

ROOT = pathlib.Path(__file__).resolve().parent.parent
EP = ROOT / "episodes" / sys.argv[1]
E = json.loads((EP / "out" / "events.json").read_text())
SR = 48000; DUR = E["dur"]; N = int((DUR + 1) * SR)
M = E.get("music") or {}
if (EP / "music.json").exists(): M = {**M, **json.loads((EP / "music.json").read_text())}   # per-episode music choice, e.g. {"style": "lofi"}
rng = np.random.default_rng(11)
music, sfx, voice = (np.zeros((N, 2)) for _ in range(3))

def add(buf, x, t, gain=1., pan=0.):
    i = int(max(0, t) * SR)
    if i >= N or len(x) == 0: return
    x = x[: N - i] * gain; l, r = np.cos((pan + 1) * np.pi / 4) * 1.414, np.sin((pan + 1) * np.pi / 4) * 1.414
    buf[i:i + len(x), 0] += x * l; buf[i:i + len(x), 1] += x * r
def filt(x, kind, f, order=2): return sosfilt(butter(order, f, btype=kind, fs=SR, output="sos"), x)
def noise(d): return rng.uniform(-1, 1, int(d * SR))
def tt(d): return np.arange(int(d * SR)) / SR
def env(n, a=.005, r=.05):
    e = np.ones(n); na, nr = max(1, int(a * SR)), max(1, int(r * SR)); e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
def midi(m): return 440. * 2 ** ((m - 69) / 12)
def sweep(f0, f1, d, shape=np.sin):
    f = np.geomspace(f0, f1, int(d * SR)); return shape(2 * np.pi * np.cumsum(f) / SR)

# ── instruments ──
def marimba(f, d=1.0):
    t = tt(d); return (np.sin(2 * np.pi * f * t) * np.exp(-t * 6) + .35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 22) + .1 * np.sin(2 * np.pi * f * 9.9 * t) * np.exp(-t * 60)) * env(len(t), .002, .05)
def pluck(f, d=1.0, decay=.994):
    n = int(d * SR); Ni = int(SR / f); exc = filt(rng.uniform(-1, 1, Ni + 2), "low", 2500)
    x = np.zeros(n); x[:len(exc)] = exc; a = np.zeros(Ni + 2); a[0] = 1; a[Ni] = a[Ni + 1] = -decay / 2
    y = lfilter([1.], a, x); return filt(y / (np.abs(y).max() + 1e-9), "low", 3000) * env(n, .002, .06)
def kick(): t = tt(.25); return sweep(140, 45, .25) * np.exp(-t * 16) * .9
def shaker(): t = tt(.07); return filt(noise(.07), "high", 6000) * np.exp(-t * 50)
def glock(f, d=1.5):
    t = tt(d); return (np.sin(2 * np.pi * f * t) * np.exp(-t * 3.5) + .4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 8)) * env(len(t), .001, .1) * .6

# ── foley ──
def rake():
    d = .45; t = tt(d); x = filt(noise(d), "band", [1500, 6000]); return x * np.sin(np.pi * t / d) ** 2 * (.6 + .4 * np.sin(2 * np.pi * 34 * t)) * .5
def whoosh(d, soft=0):
    n = int(d * SR); k = np.linspace(0, 1, n); x = noise(d); out = np.zeros(n)
    for i in range(0, n, 2048):
        c = 300 + 2400 * np.sin(np.pi * k[i]) ** 2; out[i:i + 2048] = filt(x[i:i + 2048], "band", [c * .6, c * 1.5])[: len(out[i:i + 2048])]
    return out * np.sin(np.pi * k) ** 2 * (.22 if soft else .38)
def rustle(d):
    t = tt(d); return filt(noise(d), "band", [2000, 7000]) * (np.abs(np.sin(2 * np.pi * 9 * t + np.sin(t * 13))) ** 6) * env(len(t), .05, .3) * .35
def sparkle():
    out = np.zeros(int(1.6 * SR))
    for i, m in enumerate([84, 88, 91, 96, 100]): s = glock(midi(m), 1.2); j = int(i * .07 * SR); out[j:j + len(s)] += s * .6
    return out
def popsnd(n=0): t = tt(.12); return sweep(500 + 80 * n, 1100 + 120 * n, .12) * np.exp(-t * 30) * .7
def boing(): t = tt(.5); return sweep(180, 520, .5, lambda p: np.sin(p + 3 * np.sin(p * .02))) * np.exp(-t * 5) * (1 + .5 * np.sin(2 * np.pi * 14 * t)) * .45
def chitter():
    out = np.zeros(int(.6 * SR))
    for i in range(6): s = sweep(2600, 3600, .05) * np.hanning(int(.05 * SR)); j = int(i * .08 * SR); out[j:j + len(s)] += s
    return out * .25
def dig(d):
    t = tt(d); return filt(noise(d), "band", [300, 2500]) * (np.abs(np.sin(2 * np.pi * 7 * t)) ** 4) * env(len(t), .02, .1) * .5
def toss(): return popsnd(4) * .6
def moo():
    t = tt(1.1); f = 120 + 25 * np.sin(np.pi * t / 1.1); ph = 2 * np.pi * np.cumsum(f) / SR
    y = sum(np.sin(k * ph) / k for k in range(1, 9)); return filt(y, "low", 900) * np.sin(np.pi * t / 1.1) ** .7 * .5
def munch(): t = tt(.18); return filt(noise(.18), "band", [400, 3000]) * np.exp(-t * 25) * .8
def kaching():
    out = np.zeros(int(1.4 * SR)); t = tt(.06); out[:len(t)] += filt(noise(.06), "high", 2000) * np.exp(-t * 60)
    for m, st in [(96, .08), (100, .12), (103, .16)]: s = glock(midi(m), 1.1); j = int(st * SR); out[j:j + len(s)] += s * .8
    return out
def plop(): t = tt(.2); return sweep(420, 160, .2) * np.exp(-t * 18) * .7 + filt(noise(.2), "low", 800) * np.exp(-t * 30) * .3
def coinsnd(): return glock(midi(100), 1.6) * .8 + glock(midi(107), 1.6) * .3
def whistle(d): t = tt(d); return sweep(1800, 700, d) * np.sin(np.pi * t / d) * .25
def bonk(): t = tt(.35); return (sweep(300, 120, .35) * np.exp(-t * 14) + filt(noise(.35), "low", 1500) * np.exp(-t * 60) * .5) * .9
def crunch(): t = tt(.25); return filt(noise(.25), "band", [800, 6000]) * (np.abs(np.sin(2 * np.pi * 30 * t)) ** 3) * np.exp(-t * 9) * .9

def tear(d, soft=0):
    t = tt(d); x = filt(noise(d), "band", [900, 7000]); crackle = (rng.uniform(0, 1, len(t)) < .02) * rng.uniform(.5, 1, len(t))
    return (x * (.5 + .5 * np.sin(np.pi * t / d)) * (.4 + .6 * filt(crackle, "low", 300) * 8) * env(len(t), .01, .08)) * (.3 if soft else .45)
def slap(n=0):
    t = tt(.16); return (filt(noise(.16), "band", [200, 2500]) * np.exp(-t * 45) + sweep(180 + 15 * n, 90, .16) * np.exp(-t * 30) * .6) * .8
FX = {"tear": lambda e: tear(e.get("dur", .4), e.get("soft", 0)), "slap": lambda e: slap(e.get("n", 0)), "rake": lambda e: rake(), "whoosh": lambda e: whoosh(e.get("dur", .5), e.get("soft", 0)), "rustle": lambda e: rustle(e.get("dur", 1)),
      "sparkle": lambda e: sparkle(), "pop": lambda e: popsnd(e.get("n", 0)), "boing": lambda e: boing(), "chitter": lambda e: chitter(),
      "dig": lambda e: dig(e.get("dur", .8)), "toss": lambda e: toss(), "moo": lambda e: moo(), "munch": lambda e: munch(), "kaching": lambda e: kaching(),
      "plop": lambda e: plop(), "coin": lambda e: coinsnd(), "whistle": lambda e: whistle(e.get("dur", .5)), "bonk": lambda e: bonk(), "crunch": lambda e: crunch()}
GAIN = {"whoosh": .8, "rake": .9, "sparkle": .55, "rustle": .8, "moo": .9, "kaching": .7, "coin": .5}
missing = set()
for e in E["ev"]:
    if e["type"] == "voice":
        v, sr = sf.read(EP / "voice" / f"{e['id']}.wav"); assert sr == SR; add(voice, v, e["t"])
    elif e["type"] in FX: add(sfx, FX[e["type"]](e), e["t"], GAIN.get(e["type"], .75), float(rng.uniform(-.3, .3)))
    else: missing.add(e["type"])
if missing: print("  (no sound for:", ", ".join(sorted(missing)) + ")")

# ── lo-fi chill: jazzy chords, relaxed swung groove, vinyl crackle, cozy late-night ──
def rhodes(f, d=2.5, vel=1.):
    t = tt(d); trem = 1 + .12 * np.sin(2 * np.pi * 4.6 * t)
    body = np.sin(2 * np.pi * f * t + .8 * np.exp(-t * 6) * np.sin(2 * np.pi * f * t)) * np.exp(-t * 1.1)   # soft FM bark
    bell = .25 * np.sin(2 * np.pi * f * 7.02 * t) * np.exp(-t * 18) * vel
    return (body + bell + .15 * np.sin(4 * np.pi * f * t) * np.exp(-t * 2.5)) * trem * env(len(t), .006, .25) * (.6 + .4 * vel)
def lofi_bass(f, d):
    t = tt(d); y = np.tanh(1.6 * (np.sin(2 * np.pi * f * t) + .25 * np.sin(4 * np.pi * f * t))) * np.exp(-t * 1.4)
    return filt(y, "low", 420) * env(len(t), .01, .12)
def lofi_kick(): t = tt(.35); return sweep(110, 42, .35) * np.exp(-t * 11) * .95
def lofi_snare():
    t = tt(.28); return filt(filt(noise(.28), "band", [900, 4500]) * np.exp(-t * 16) + .5 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 28), "low", 5000) * .55
def lofi_hat(open_=False):
    d = .22 if open_ else .05; t = tt(d); return filt(noise(d), "high", 6500) * np.exp(-t * (12 if open_ else 70)) * .4
def vinyl(n):
    crackle = np.zeros(n); k = rng.integers(0, n, int(n / SR * 9)); crackle[k] = rng.uniform(-1, 1, len(k)) * rng.uniform(.2, 1, len(k)) ** 3
    pops = np.zeros(n); k2 = rng.integers(0, n, int(n / SR * .6)); pops[k2] = rng.choice([-1, 1], len(k2))
    hiss = filt(rng.uniform(-1, 1, n), "band", [2000, 9000]) * .02
    rumble = filt(rng.uniform(-1, 1, n), "low", 60) * .08
    return filt(crackle, "high", 1200) * .35 + filt(pops, "low", 2500) * .5 + hiss + rumble
def lofi_score():
    bpm = M.get("bpm", 76); B = 60 / bpm; sw = .62                  # swing: the off-8th lands late
    # ii–V–I–vi in F, rootless jazzy voicings (min9, 13, maj9, min9)
    PROG = [(43, [58, 62, 65, 69]), (36, [52, 58, 62, 69]), (41, [57, 60, 64, 67]), (38, [53, 57, 60, 64])]
    MEL = [[None, 77, None, 74], [76, None, 72, None], [None, 72, 74, 69], [None, None, 67, None]]
    stops = M.get("stops", []); quiet = lambda x: any(a <= x < b for a, b in stops)
    t, bar, end = M.get("start", 0), 0, M["end"]
    while t < end - .01:
        root, ch = PROG[bar % 4]
        if not quiet(t):
            for k, m in enumerate(ch): add(music, rhodes(midi(m), B * 4 + .5, .7), t + k * .018, .085, -.25 + .17 * k)
            push = t + B * (1 + sw)                                          # chord anticipation on the "and" of 2
            if bar % 2: [add(music, rhodes(midi(m), B * 2, .5), push + k * .015, .05, .2) for k, m in enumerate(ch[1:])]
            add(music, lofi_bass(midi(root), B * 1.8), t, .55)
            add(music, lofi_bass(midi(root + (7 if bar % 2 else 12)), B * 1.2), t + B * (2 + sw), .4)
        for beat in range(4):
            for half in (0, 1):
                x = t + B * (beat + (sw if half else 0))
                if x >= end or quiet(x): continue
                vel = .8 + .2 * rng.random()
                add(music, lofi_hat(open_=(beat == 3 and half == 1 and bar % 2 == 1)), x, .16 * vel * (1 if half == 0 else .7), .35)
                if half == 0 and beat in (0,) or (beat == 2 and half == 1 and bar % 2 == 0): add(music, lofi_kick(), x, .6)
                if half == 0 and beat in (1, 3): add(music, lofi_snare(), x + .012, .38 * vel, -.1)
        if bar % 8 >= 4 and not quiet(t):                                   # a lazy melody every other phrase
            for i, m in enumerate(MEL[bar % 4]):
                if m: add(music, rhodes(midi(m), B * 1.6, 1.0), t + B * i + (B * (sw - .5) if i % 2 else 0), .06, .3)
        t += 4 * B; bar += 1
    fa = M.get("finalAt", end)
    for k, m in enumerate([41, 57, 60, 64, 67, 72]): add(music, rhodes(midi(m), 4.0, .8), fa + k * .05, .09, -.3 + .12 * k)
    # cozy tape tone: roll off the top, a touch of saturation
    for ch_ in (0, 1): music[:, ch_] = np.tanh(filt(music[:, ch_], "low", 5200) * 1.2) / 1.2
    vin = vinyl(N) * .55; music[:, 0] += vin; music[:, 1] += np.roll(vin, 37)

# ── score ──
if M.get("style") == "lofi":
    lofi_score()
elif M:
    B = 60 / M.get("bpm", 112)
    PROG = [(65, [65, 69, 72]), (62, [62, 65, 69]), (58, [58, 62, 65]), (60, [60, 64, 67])]   # F Dm Bb C
    MEL = [[77, None, 76, 74, 72, None, 74, None], [74, None, 72, 69, 72, None, None, None], [70, None, 72, 74, 77, None, 76, None], [76, 74, 72, None, 79, None, None, None]]
    stops = M.get("stops", []); quiet = lambda x: any(a <= x < b for a, b in stops)
    t, bar = M.get("start", 0), 0
    while t < M["end"] - .01:
        root, ch = PROG[bar % 4]
        for i in range(8):                       # eighth notes
            x = t + i * B / 2
            if x >= M["end"] or quiet(x): continue
            if i in (0, 3, 4, 6): add(music, marimba(midi(ch[(i // 2) % 3] + 12), .8), x, .22, -.3)
            m = MEL[bar % 4][i]
            if m and bar % 8 >= 4: add(music, marimba(midi(m), 1.0), x, .2, .3)    # tune every other phrase
            if i % 2 == 1: add(music, shaker(), x, .06, .4)
            if i in (0, 4): add(music, kick(), x, .35); add(music, pluck(midi(root - 24), .9), x, .45, 0)
            if i == 6: add(music, pluck(midi(root - 17), .6), x, .3, 0)
        t += 8 * B / 2; bar += 1
    fa = M.get("finalAt", M["end"])
    for k, m in enumerate([53, 65, 69, 72, 77]): add(music, marimba(midi(m), 2.5), fa + k * .03, .25, -.3 + .15 * k)
    add(music, glock(midi(89), 2.5), fa + .1, .25)
music += filt(noise(N / SR), "low", 500)[:N, None] * .01         # room tone

def compress(x, thr=.25, ratio=3.):
    a = np.abs(x).max(axis=1); e = lfilter([.002], [1, -.998], a)
    return x * np.where(e > thr, (thr + (e - thr) / ratio) / np.maximum(e, 1e-9), 1.)[:, None]
voice = compress(voice / (np.abs(voice).max() + 1e-9) * .9)
active = lfilter([.0006], [1, -.9994], (np.abs(voice).max(axis=1) > .02).astype(float))
duck = 1 - .5 * np.clip(active * 1.6, 0, 1)
mix = np.tanh((music * duck[:, None] * .7 + sfx * .8 + voice * 1.2) * .9) / .9 * .7
(EP / "out").mkdir(exist_ok=True); sf.write(EP / "out" / "mix.wav", mix[: int(DUR * SR)], SR, subtype="PCM_24")
rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9); sp = np.abs(voice).max(axis=1) > .02
print(f"  mix.wav {DUR}s · voice {rms(voice[sp] * 1.2):.1f} dB vs music {rms(music[sp] * duck[sp, None]):.1f} dB while speaking")
