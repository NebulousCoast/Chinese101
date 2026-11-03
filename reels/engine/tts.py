"""Kid narrator for an episode: Kokoro (offline) + a light pitch-up.
Usage: python engine/tts.py <episode> <kokoro model dir> [voice=af_sky] [speed=0.92]
Writes episodes/<ep>/voice/<id>.wav (48 kHz mono) and voice/dur.json."""
import json, subprocess, sys, pathlib
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

ROOT = pathlib.Path(__file__).resolve().parent.parent
ep, models = sys.argv[1], pathlib.Path(sys.argv[2])
voice = sys.argv[3] if len(sys.argv) > 3 else "af_sky"; speed = float(sys.argv[4]) if len(sys.argv) > 4 else .92
EP = ROOT / "episodes" / ep; out = EP / "voice"; out.mkdir(exist_ok=True)
k = Kokoro(str(models / "kokoro-v1.0.onnx"), str(models / "voices-v1.0.bin"))
durs = {}
for ln in json.loads((EP / "lines.json").read_text()):
    audio, sr = k.create(ln.get("say", ln["en"]).replace("…", "..."), voice=ln.get("voice", voice), speed=ln.get("speed", speed), lang="en-us")
    nz = np.flatnonzero(np.abs(audio) > .01); audio = audio[max(0, nz[0] - 600): nz[-1] + 1500]
    raw = out / f"{ln['id']}.raw.wav"; sf.write(raw, audio, sr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", f"asetrate={sr}*1.15,aresample=48000,atempo={1/1.15:.5f}", "-ac", "1", out / f"{ln['id']}.wav"], check=True)
    raw.unlink(); durs[ln["id"]] = round(sf.info(out / f"{ln['id']}.wav").duration, 3)
    print(f"  {ln['id']:10s} {durs[ln['id']]:5.2f}s  {ln['en']}")
(out / "dur.json").write_text(json.dumps(durs, indent=1))
print("  total voice", round(sum(durs.values()), 2), "s")
