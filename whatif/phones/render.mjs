// Frame-by-frame capture of index.html (window.render(t)).
//   node render.mjs stills <t> <t> …        → stills/t_<t>.jpg
//   node render.mjs sheet a:b:step out.jpg  → contact sheet
//   node render.mjs events                  → events.json  {dur, ev}
//   node render.mjs video [fps=24]          → out/video.mp4 (silent)
import { createRequire } from "node:module";
import { spawn, execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
const { chromium } = createRequire(import.meta.url)("playwright");
const HERE = path.dirname(fileURLToPath(import.meta.url));
const [mode, ...args] = process.argv.slice(2);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
const errors = []; page.on("pageerror", e => errors.push(e.message));
await page.goto(pathToFileURL(path.join(HERE, "index.html")).href + "?render=1");
await page.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
if (errors.length) { console.error(errors); process.exit(1); }
const canvas = await page.$("canvas");
const shot = async t => { await page.evaluate(t => window.render(t), t); return canvas.screenshot({ type: "jpeg", quality: 92 }); };
const DUR = await page.evaluate(() => window.DUR);

if (mode === "stills" || mode === "sheet") {
  mkdirSync(path.join(HERE, "stills"), { recursive: true });
  let ts = args;
  if (mode === "sheet") { const [a, b, st] = args[0].split(":").map(Number); ts = []; for (let t = a; t <= Math.min(b, DUR); t += st) ts.push(t.toFixed(2)); }
  const files = [];
  for (const t of ts) { const f = path.join(HERE, "stills", `t_${(+t).toFixed(2)}.jpg`); writeFileSync(f, await shot(+t)); files.push(f); }
  if (mode === "sheet") {
    const cols = 4, out = args[1] || path.join(HERE, "stills", "sheet.jpg");
    execFileSync("ffmpeg", ["-y", "-loglevel", "error", ...files.flatMap(f => ["-i", f]), "-filter_complex",
      files.map((_, i) => `[${i}]scale=480:270,drawtext=text='${ts[i]}s':x=8:y=8:fontsize=22:fontcolor=red[v${i}]`).join(";") + ";" +
      files.map((_, i) => `[v${i}]`).join("") + `xstack=inputs=${files.length}:layout=` +
      files.map((_, i) => `${(i % cols) * 480}_${Math.floor(i / cols) * 270}`).join("|") + `:fill=black`, out]);
    console.log(out);
  } else console.log(files.join("\n"));
} else if (mode === "events") {
  const ev = await page.evaluate(() => ({ dur: window.DUR, ev: window.EV, ...window.TIMELINE }));
  writeFileSync(path.join(HERE, "events.json"), JSON.stringify(ev, null, 1)); console.log("events.json", ev.ev.length, "events,", ev.dur, "s");
} else if (mode === "video") {
  const fps = +(args[0] || 24), frames = Math.round(DUR * fps);
  mkdirSync(path.join(HERE, "out"), { recursive: true });
  const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(fps), "-i", "-",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", path.join(HERE, "out", "video.mp4")], { stdio: ["pipe", "inherit", "inherit"] });
  for (let f = 0; f < frames; f++) {
    const buf = await shot(f / fps);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
    if (f % (fps * 5) === 0) console.log(`  ${(f / fps).toFixed(0)}s / ${DUR}s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on("close", r));
  console.log("out/video.mp4", frames, "frames");
}
if (errors.length) { console.error(errors); process.exit(1); }
await browser.close();
