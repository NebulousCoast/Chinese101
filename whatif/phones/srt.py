"""events.json + lines.json → phones.srt (English line, Chinese line under it)."""
import json, pathlib
HERE = pathlib.Path(__file__).parent
E = json.loads((HERE / "events.json").read_text()); L = {l["id"]: l for l in json.loads((HERE / "lines.json").read_text())}
ts = lambda t: "%02d:%02d:%02d,%03d" % (t // 3600, t % 3600 // 60, t % 60, round(t % 1 * 1000) % 1000)
out = []
for i, s in enumerate(E["secs"], 1):
    t0, t1 = s["v0"], max(s["v0"] + s["vd"] + .6, s["v0"] + 1.8)
    out.append(f"{i}\n{ts(t0)} --> {ts(t1)}\n{L[s['id']]['en']}\n{L[s['id']]['zh']}\n")
(HERE / "phones.srt").write_text("\n".join(out), encoding="utf-8"); print("phones.srt")
