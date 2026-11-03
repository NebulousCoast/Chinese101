// Render a "What If?" episode from whatif.html as a 9:16 reel, timed to a recorded voice.
// Voice + lines live in reels/episodes/whatif-<id>/ (lines.json, voice/dur.json from reels/engine/tts.py).
// Usage: node scripts/render-whatif-reel.mjs <id=phones> [events|stills t…|video] [fps=30]
// Writes reels/episodes/whatif-<id>/out/{events.json, video.mp4, stills/}; then reels/engine/mix.py,
// master.sh and finish.py finish it exactly like the 3D reels.
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
const { chromium } = createRequire(import.meta.url)("playwright");

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const [id = "phones", mode = "video", ...rest] = process.argv.slice(2);
const EP = path.join(root, "reels", "episodes", `whatif-${id}`), OUT = path.join(EP, "out");
mkdirSync(path.join(OUT, "stills"), { recursive: true });
const dur = JSON.parse(readFileSync(path.join(EP, "voice", "dur.json"), "utf8"));
const REEL = { lines: JSON.parse(readFileSync(path.join(EP, "lines.json"), "utf8")).map(l => ({ ...l, vd: dur[l.id] })) };

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
const errors = []; page.on("pageerror", e => errors.push(e.message));
await page.addInitScript(r => { window.REEL = r; }, REEL);
await page.goto(pathToFileURL(path.join(root, "whatif.html")).href + `?render=${id}&reel=1`);
await page.evaluate(() => document.fonts.ready);
if (errors.length) { console.error(errors.join("\n")); process.exit(1); }
const X = await page.evaluate(() => window.EXPORT);
writeFileSync(path.join(OUT, "events.json"), JSON.stringify(X, null, 1));
const shot = async t => { await page.evaluate(t => window.seek(t), t); return page.screenshot({ type: "jpeg", quality: 92 }); };

if (mode === "events") console.log(`events.json: ${X.ev.length} events, ${X.dur}s`);
else if (mode === "stills") for (const t of rest) { const f = path.join(OUT, "stills", `t_${(+t).toFixed(2)}.jpg`); writeFileSync(f, await shot(+t)); console.log(f); }
else if (mode === "video") {
  const fps = +(rest[0] || 30), frames = Math.round(X.dur * fps);
  const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(fps), "-i", "-",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-movflags", "+faststart", path.join(OUT, "video.mp4")], { stdio: ["pipe", "inherit", "inherit"] });
  for (let f = 0; f < frames; f++) {
    const buf = await shot(f / fps);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
    if (f % (fps * 10) === 0) console.log(`  ${Math.round(f / fps)}s / ${X.dur}s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on("close", r));
  console.log(`video.mp4: ${frames} frames, ${X.dur}s`);
}
if (errors.length) { console.error(errors.join("\n")); process.exit(1); }
await browser.close();
