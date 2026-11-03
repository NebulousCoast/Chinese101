// Capture an episode frame by frame.
//   node engine/render.mjs <ep> events               → episodes/<ep>/out/events.json
//   node engine/render.mjs <ep> stills 1.5 12 …      → episodes/<ep>/out/stills/t_<t>.jpg
//   node engine/render.mjs <ep> sheet 0:60:3         → episodes/<ep>/out/sheet.jpg (contact sheet)
//   node engine/render.mjs <ep> video [fps] [workers]→ episodes/<ep>/out/video.mp4 (silent)
//   node engine/render.mjs <ep> serve                → http://localhost:8123/engine/stage.html?ep=<ep> (live preview)
import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import { createServer } from "node:http";
import { mkdirSync, writeFileSync, readFileSync, existsSync, rmSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
const { chromium } = createRequire(import.meta.url)("playwright");

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const [ep, mode = "video", ...args] = process.argv.slice(2);
if (!ep || !existsSync(path.join(ROOT, "episodes", ep, "episode.js"))) { console.error("usage: node engine/render.mjs <episode> events|stills|sheet|video|serve"); process.exit(2); }
const OUT = path.join(ROOT, "episodes", ep, "out"); mkdirSync(OUT, { recursive: true });

const TYPES = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json", ".woff2": "font/woff2", ".png": "image/png", ".jpg": "image/jpeg" };
const server = createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(new URL(req.url, "http://x").pathname));
  if (!p.startsWith(ROOT) || !existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "content-type": TYPES[path.extname(p)] || "application/octet-stream" }); res.end(readFileSync(p));
});
await new Promise(r => server.listen(mode === "serve" ? 8123 : 0, "127.0.0.1", r));
const URL0 = `http://127.0.0.1:${server.address().port}/engine/stage.html?ep=${ep}`;
if (mode === "serve") { console.log("preview:", URL0); await new Promise(() => {}); }

const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
async function openPage() {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  const errors = []; page.on("pageerror", e => errors.push(e.message)); page.on("console", m => m.type() === "error" && errors.push(m.text()));
  await page.goto(URL0 + "&render=1");
  try { await page.waitForFunction(() => window.READY === true, null, { timeout: 120000 }); }
  catch { console.error(errors.join("\n") || "page never became READY"); process.exit(1); }
  if (errors.length) { console.error(errors.join("\n")); process.exit(1); }
  const frame = await page.$("#frame");
  return { page, shot: async t => { await page.evaluate(t => window.render(t), t); return frame.screenshot({ type: "jpeg", quality: 92 }); } };
}
const { page, shot } = await openPage();
const DUR = await page.evaluate(() => window.DUR);

if (mode === "events") {
  const tl = await page.evaluate(() => ({ ev: window.EV, ...window.TIMELINE }));
  writeFileSync(path.join(OUT, "events.json"), JSON.stringify(tl, null, 1));
  console.log(`events.json: ${tl.ev.length} events, ${tl.dur}s`);
} else if (mode === "stills" || mode === "sheet") {
  const dir = path.join(OUT, "stills"); mkdirSync(dir, { recursive: true });
  let ts = args.map(Number);
  if (mode === "sheet") { const [a, b, s] = (args[0] || `0:${DUR}:3`).split(":").map(Number); ts = []; for (let t = a; t <= Math.min(b, DUR) + 1e-6; t += s) ts.push(+t.toFixed(2)); }
  const files = [];
  for (const t of ts) { const f = path.join(dir, `t_${t.toFixed(2)}.jpg`); writeFileSync(f, await shot(t)); files.push(f); }
  if (mode === "sheet") {
    const cols = 6, w = 270, h = 480;
    const r = spawnSync("ffmpeg", ["-y", "-loglevel", "error", ...files.flatMap(f => ["-i", f]), "-filter_complex",
      files.map((_, i) => `[${i}]scale=${w}:${h},drawtext=text='${ts[i]}':x=6:y=6:fontsize=26:fontcolor=red[v${i}]`).join(";") + ";" +
      files.map((_, i) => `[v${i}]`).join("") + `xstack=inputs=${files.length}:fill=black:layout=` + files.map((_, i) => `${(i % cols) * w}_${Math.floor(i / cols) * h}`).join("|"),
      path.join(OUT, "sheet.jpg")], { stdio: "inherit" });
    console.log(r.status ? "sheet failed" : path.join(OUT, "sheet.jpg"));
  } else console.log(files.join("\n"));
} else if (mode === "video") {
  const fps = +(args[0] || 30), workers = +(args[1] || 3), frames = Math.round(DUR * fps);
  const fdir = path.join(OUT, "frames"); rmSync(fdir, { recursive: true, force: true }); mkdirSync(fdir, { recursive: true });
  const pages = [{ shot }]; for (let i = 1; i < workers; i++) pages.push(await openPage());
  let next = 0, done = 0; const t0 = Date.now();
  await Promise.all(pages.map(async p => {
    while (next < frames) {
      const f = next++;
      writeFileSync(path.join(fdir, `${String(f).padStart(5, "0")}.jpg`), await p.shot(f / fps));
      if (++done % (fps * 5) === 0) console.log(`  ${done}/${frames} frames  ${((Date.now() - t0) / done).toFixed(0)} ms/frame`);
    }
  }));
  const r = spawnSync("ffmpeg", ["-y", "-loglevel", "error", "-framerate", String(fps), "-i", path.join(fdir, "%05d.jpg"),
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium", "-movflags", "+faststart", path.join(OUT, "video.mp4")], { stdio: "inherit" });
  if (r.status) process.exit(1);
  rmSync(fdir, { recursive: true, force: true });
  console.log(`video.mp4: ${frames} frames @ ${fps} fps`);
}
await browser.close(); server.close();
