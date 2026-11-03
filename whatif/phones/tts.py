"""Kid narrator: Kokoro (offline) → light pitch-up with ffmpeg → voice/<id>.wav + voice.js timings.
Usage: python tts.py <kokoro model dir> [voice=af_sky]"""
import json, subprocess, sys, pathlib
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

HERE = pathlib.Path(__file__).parent
models = pathlib.Path(sys.argv[1]); voice = sys.argv[2] if len(sys.argv) > 2 else "af_sky"
k = Kokoro(str(models / "kokoro-v1.0.onnx"), str(models / "voices-v1.0.bin"))
out = HERE / "voice"; out.mkdir(exist_ok=True)
durs = {}
for ln in json.loads((HERE / "lines.json").read_text()):
    audio, sr = k.create(ln.get("say", ln["en"]), voice=voice, speed=0.9, lang="en-us")
    nz = np.flatnonzero(np.abs(audio) > 0.01)                      # trim silence
    audio = audio[max(0, nz[0] - 600): nz[-1] + 1200]
    raw = out / f"{ln['id']}.raw.wav"; sf.write(raw, audio, sr)
    wav = out / f"{ln['id']}.wav"
    # +~2.4 semitones, same tempo: a younger-sounding voice
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
                    f"asetrate={sr}*1.15,aresample=48000,atempo={1/1.15:.5f}", "-ac", "1", wav], check=True)
    raw.unlink()
    durs[ln["id"]] = round(sf.info(wav).duration, 3)
    print(ln["id"], durs[ln["id"]])
lines = json.loads((HERE / "lines.json").read_text())
(HERE / "voice.js").write_text("window.VOICE_DUR = " + json.dumps(durs) + ";\nwindow.LINES = " + json.dumps(lines, ensure_ascii=False) + ";\n")
