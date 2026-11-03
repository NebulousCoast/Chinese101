"""Subtitles (.srt with English + Chinese) and caption text for posting.
Usage: python3 engine/finish.py <ep>"""
import json, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent; EP = ROOT / "episodes" / sys.argv[1]
E = json.loads((EP / "out" / "events.json").read_text())
ts = lambda t: "%02d:%02d:%02d,%03d" % (t // 3600, t % 3600 // 60, int(t % 60), round(t % 1 * 1000) % 1000)
srt = [f"{i}\n{ts(l['v0'])} --> {ts(max(l['v0'] + l['vd'] + .5, l['v0'] + 1.8))}\n{l['en']}\n" + (f"{l['zh']}\n" if l.get("zh") else "") for i, l in enumerate(E["lines"], 1)]
(EP / "out" / "subtitles.srt").write_text("\n".join(srt), encoding="utf-8")
print("  out/subtitles.srt")
