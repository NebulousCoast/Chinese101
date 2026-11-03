"""Fetch the caption fonts (OFL, Google Fonts): Fredoka 600 (Latin) and Noto Sans TC 700
subset to the Chinese characters used by every episode. Usage: python3 engine/fonts.py"""
import json, pathlib, re, subprocess, urllib.parse
ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
def css(q): return subprocess.run(["curl", "-sS", "-A", UA, "https://fonts.googleapis.com/css2?" + q], capture_output=True, text=True, check=True).stdout
def get(url, name): subprocess.run(["curl", "-sS", "-o", str(ROOT / "fonts" / name), url], check=True); print("fonts/" + name)
(ROOT / "fonts").mkdir(exist_ok=True)
latin = re.search(r"/\* latin \*/.*?url\((https://[^)]+)\)", css("family=Fredoka:wght@600"), re.S).group(1)
get(latin, "fredoka-600.woff2")
chars = set("0123456789$")
for f in (ROOT / "episodes").glob("*/lines.json"):
    for l in json.loads(f.read_text()): chars |= set(l["zh"])
zh = re.search(r"url\((https://[^)]+)\)", css("family=Noto+Sans+TC:wght@700&text=" + urllib.parse.quote("".join(sorted(chars))))).group(1)
get(zh, "notosanstc-700-subset.woff2")
