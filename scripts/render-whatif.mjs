// Render a "What If?" episode from whatif.html to a silent MP4 with burned-in captions.
// Usage: node scripts/render-whatif.mjs [episodeId=phones] [cap=both|zh|en] [fps=24]
// Needs Playwright (Chromium) and ffmpeg on PATH. Output: videos/whatif-<id>[-cap].mp4
import { createRequire } from "node:module";
const { chromium } = createRequire(import.meta.url)("playwright");
import { spawn } from "node:child_process";
import { mkdirSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const [id = "phones", cap = "both", fpsArg = "24"] = process.argv.slice(2);
const fps = Number(fpsArg);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
mkdirSync(path.join(root, "videos"), { recursive: true });
const out = path.join(root, "videos", `whatif-${id}${cap === "both" ? "" : "-" + cap}.mp4`);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
const url = pathToFileURL(path.join(root, "whatif.html")).href + `?render=${id}&cap=${cap}`;
await page.goto(url);
await page.evaluate(() => document.fonts.ready);
const total = (await page.evaluate(() => window.timeline())).reduce((a, b) => a + b, 0);
const frames = Math.round(total * fps);

const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(fps),
  "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-movflags", "+faststart", out],
  { stdio: ["pipe", "inherit", "inherit"] });

for (let f = 0; f < frames; f++) {
  await page.evaluate(t => window.seek(t), f / fps);
  const buf = await page.screenshot({ type: "jpeg", quality: 90 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
  if (f % (fps * 10) === 0) process.stdout.write(`  ${Math.round(f / fps)}s / ${total}s\n`);
}
ff.stdin.end();
await new Promise((res, rej) => ff.on("close", c => (c === 0 ? res() : rej(new Error("ffmpeg exit " + c)))));
await browser.close();
console.log("wrote", out);
