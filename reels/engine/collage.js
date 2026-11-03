// Collage B-roll: turn one voice-over line into a paper-cutout clip that assembles itself.
//
// In lines.json, give a line  "broll": {}  (or {"from": 0, "to": .7, "pieces": [...], "words": [...], "paper": "#f2c14e"})
// and the engine covers that part of the line with a collage:
//   • pieces are picked from the words spoken in the window (KEYWORDS below) unless you list them;
//   • each piece slaps down when its word is spoken (word times estimated from the line);
//   • one or two key words are cut out as ransom-note letters (CAPS words in the line, or "words");
//   • torn white paper edges, grain, drop shadows, 12 fps stop-motion with a little boil;
//   • a torn sheet wipes in and out; "tear" and "slap" sound events are emitted for the mix.
import { rng } from "./kit.js";

export const W = 1080, H = 1920;
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const seg = (t, a, b) => clamp((t - a) / (b - a));
const back = k => 1 + 2.4 * Math.pow(k - 1, 3) + 1.4 * Math.pow(k - 1, 2);
const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
const step12 = t => Math.floor(t * 12) / 12;                // stop-motion timing

/* ── paper ── */
let GRAIN = null;
function grain() {
  if (GRAIN) return GRAIN;
  const c = document.createElement("canvas"); c.width = c.height = 256; const g = c.getContext("2d"), r = rng(77);
  const img = g.createImageData(256, 256);
  for (let i = 0; i < 256 * 256; i++) { const v = 215 + r() * 40 - (r() < .02 ? 40 : 0); img.data.set([v, v, v * .97, 255], i * 4); }
  g.putImageData(img, 0, 0);
  // a few fibres
  g.strokeStyle = "rgba(120,100,80,.12)"; g.lineWidth = 1;
  for (let i = 0; i < 60; i++) { const x = r() * 256, y = r() * 256; g.beginPath(); g.moveTo(x, y); g.lineTo(x + (r() - .5) * 30, y + (r() - .5) * 8); g.stroke(); }
  return (GRAIN = c);
}
function grainOver(g, w, h, alpha = .55) {
  g.save(); g.globalCompositeOperation = "multiply"; g.globalAlpha = alpha;
  g.fillStyle = g.createPattern(grain(), "repeat"); g.fillRect(0, 0, w, h); g.restore();
}
// cut a shape out of paper: draw(g, s) paints the shape centred at (0,0) at unit size s
function cutout(draw, s, seed, o = {}) {
  const pad = Math.round(s * .18) + 24, size = Math.ceil(s * (o.w || 1) + pad * 2), hgt = Math.ceil(s * (o.h || 1) + pad * 2);
  const A = document.createElement("canvas"); A.width = size; A.height = hgt;
  const a = A.getContext("2d"); a.translate(size / 2, hgt / 2); draw(a, s); a.setTransform(1, 0, 0, 1, 0, 0);
  grainInto(A, .35);
  // white torn border: dilate the silhouette with jittered offsets
  const Wt = document.createElement("canvas"); Wt.width = size; Wt.height = hgt; const wt = Wt.getContext("2d");
  wt.drawImage(A, 0, 0); wt.globalCompositeOperation = "source-in"; wt.fillStyle = o.edge || "#fbf8f1"; wt.fillRect(0, 0, size, hgt);
  const B = document.createElement("canvas"); B.width = size; B.height = hgt; const b = B.getContext("2d"), r = rng(seed);
  const rad = o.border ?? Math.max(7, s * .035);
  for (let k = 0; k < 28; k++) { const ang = k / 28 * Math.PI * 2, rr = rad * (.75 + r() * .6); b.drawImage(Wt, Math.cos(ang) * rr, Math.sin(ang) * rr); }
  grainInto(B, .25);
  b.drawImage(A, 0, 0);
  return B;
}
// multiply paper grain into a canvas, only where it is already painted
function grainInto(c, alpha = .4) {
  const G = document.createElement("canvas"); G.width = c.width; G.height = c.height; const g = G.getContext("2d");
  g.fillStyle = g.createPattern(grain(), "repeat"); g.fillRect(0, 0, c.width, c.height);
  g.globalCompositeOperation = "destination-in"; g.drawImage(c, 0, 0);
  const x = c.getContext("2d"); x.save(); x.globalCompositeOperation = "multiply"; x.globalAlpha = alpha; x.drawImage(G, 0, 0); x.restore();
}

/* ── the piece library (flat paper shapes) ── */
const T = (g, txt, x, y, size, col, font = "Fredoka") => { g.fillStyle = col; g.font = `700 ${size}px ${font}, sans-serif`; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(txt, x, y); };
const rr = (g, x, y, w, h, r) => { g.beginPath(); g.roundRect(x, y, w, h, r); };
const LIB = {
  bill: { w: 2, h: .95, draw(g, s) { g.fillStyle = "#7cc47f"; g.fillRect(-s, -s * .47, s * 2, s * .94); g.strokeStyle = "#3f8f53"; g.lineWidth = s * .05; g.strokeRect(-s * .9, -s * .38, s * 1.8, s * .76); g.fillStyle = "#c4e8bf"; g.beginPath(); g.ellipse(0, 0, s * .26, s * .32, 0, 0, 7); g.fill(); T(g, "$", 0, s * .02, s * .48, "#3f8f53"); } },
  coin: { draw(g, s) { g.fillStyle = "#f7c948"; g.beginPath(); g.arc(0, 0, s * .5, 0, 7); g.fill(); g.strokeStyle = "#d39e1c"; g.lineWidth = s * .05; g.beginPath(); g.arc(0, 0, s * .4, 0, 7); g.stroke(); T(g, "$", 0, s * .02, s * .5, "#c48a12"); } },
  bag: { h: 1.15, draw(g, s) { g.fillStyle = "#cfa86a"; g.beginPath(); g.moveTo(-s * .18, -s * .38); g.bezierCurveTo(-s * .62, -s * .1, -s * .62, s * .55, 0, s * .55); g.bezierCurveTo(s * .62, s * .55, s * .62, -s * .1, s * .18, -s * .38); g.closePath(); g.fill(); g.fillStyle = "#b58b4c"; g.fillRect(-s * .22, -s * .45, s * .44, s * .1); g.beginPath(); g.moveTo(-s * .14, -s * .45); g.lineTo(-s * .3, -s * .6); g.lineTo(s * .3, -s * .6); g.lineTo(s * .14, -s * .45); g.fill(); T(g, "$", 0, s * .15, s * .5, "#3f8f53"); } },
  icecream: { w: .7, h: 1.2, draw(g, s) { g.fillStyle = "#e0a85c"; g.beginPath(); g.moveTo(-s * .26, -s * .05); g.lineTo(s * .26, -s * .05); g.lineTo(0, s * .58); g.fill(); g.strokeStyle = "#b9803a"; g.lineWidth = s * .02; for (let i = -2; i <= 2; i++) { g.beginPath(); g.moveTo(i * s * .1 - s * .1, -s * .05); g.lineTo(i * s * .1 + s * .15, s * .3); g.stroke(); } g.fillStyle = "#ff9ec4"; g.beginPath(); g.arc(0, -s * .15, s * .27, 0, 7); g.fill(); g.fillStyle = "#fff1c9"; g.beginPath(); g.arc(0, -s * .42, s * .22, 0, 7); g.fill(); g.fillStyle = "#e5484d"; g.beginPath(); g.arc(s * .02, -s * .64, s * .07, 0, 7); g.fill(); } },
  tree: { h: 1.2, draw(g, s) { g.fillStyle = "#8a5a3b"; g.fillRect(-s * .08, 0, s * .16, s * .55); g.fillStyle = "#59b05f"; for (const [x, y, r] of [[0, -s * .22, s * .32], [-s * .26, 0, s * .22], [s * .26, -s * .02, s * .24]]) { g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); } g.fillStyle = "#c4e8bf"; for (const [x, y] of [[-.1, -.3], [.15, -.1], [-.25, .02], [.05, -.45]]) g.fillRect(x * s, y * s, s * .12, s * .06); } },
  house: { draw(g, s) { g.fillStyle = "#f6efe0"; g.fillRect(-s * .38, -s * .05, s * .76, s * .5); g.fillStyle = "#e5735f"; g.beginPath(); g.moveTo(-s * .48, -s * .03); g.lineTo(0, -s * .45); g.lineTo(s * .48, -s * .03); g.fill(); g.fillStyle = "#8a5a3b"; g.fillRect(-s * .08, s * .17, s * .16, s * .28); g.fillStyle = "#9fd3ff"; g.fillRect(-s * .3, s * .05, s * .14, s * .14); g.fillRect(s * .16, s * .05, s * .14, s * .14); } },
  person: { w: .6, h: 1.1, draw(g, s, v = 0) { const cols = ["#ff7a59", "#4f9dff", "#ffcf4a", "#59c27a", "#b388ff", "#ff9ec4"]; g.fillStyle = cols[v % 6]; rr(g, -s * .2, -s * .1, s * .4, s * .45, s * .08); g.fill(); g.fillStyle = "#3a4a6b"; g.fillRect(-s * .17, s * .33, s * .14, s * .2); g.fillRect(s * .03, s * .33, s * .14, s * .2); g.fillStyle = ["#f2c9a0", "#d9a273", "#a8714a"][v % 3]; g.beginPath(); g.arc(0, -s * .3, s * .17, 0, 7); g.fill(); g.fillStyle = "#2b2018"; g.fillRect(-s * .07, -s * .33, s * .03, s * .05); g.fillRect(s * .04, -s * .33, s * .03, s * .05); } },
  crowd: { w: 1.8, h: 1.1, draw(g, s) { for (let i = 0; i < 5; i++) { g.save(); g.translate((i - 2) * s * .36, (i % 2) * s * .06); g.scale(.9, .9); LIB.person.draw(g, s, i); g.restore(); } } },
  mountain: { w: 1.6, h: 1.2, draw(g, s) { g.fillStyle = "#7a8fb8"; g.beginPath(); g.moveTo(-s * .8, s * .55); g.lineTo(0, -s * .55); g.lineTo(s * .8, s * .55); g.fill(); g.fillStyle = "#fbfaf5"; g.beginPath(); g.moveTo(-s * .22, -s * .25); g.lineTo(0, -s * .55); g.lineTo(s * .22, -s * .25); g.lineTo(s * .1, -s * .3); g.lineTo(0, -s * .2); g.lineTo(-s * .1, -s * .3); g.fill(); g.fillStyle = "#f7c948"; g.beginPath(); g.arc(0, -s * .62, s * .1, 0, 7); g.fill(); } },
  gem: { draw(g, s) { g.fillStyle = "#5fd0e6"; g.beginPath(); g.moveTo(-s * .45, -s * .1); g.lineTo(-s * .25, -s * .38); g.lineTo(s * .25, -s * .38); g.lineTo(s * .45, -s * .1); g.lineTo(0, s * .45); g.fill(); g.strokeStyle = "#2f9fb8"; g.lineWidth = s * .025; g.beginPath(); g.moveTo(-s * .45, -s * .1); g.lineTo(s * .45, -s * .1); g.moveTo(-s * .12, -s * .38); g.lineTo(-s * .2, -s * .1); g.lineTo(0, s * .45); g.lineTo(s * .2, -s * .1); g.lineTo(s * .12, -s * .38); g.stroke(); } },
  lock: { h: 1.1, draw(g, s) { g.strokeStyle = "#8a8f99"; g.lineWidth = s * .09; g.beginPath(); g.arc(0, -s * .12, s * .22, Math.PI, 0); g.lineTo(s * .22, s * .02); g.moveTo(-s * .22, -s * .12); g.lineTo(-s * .22, s * .02); g.stroke(); g.fillStyle = "#f2b705"; rr(g, -s * .36, 0, s * .72, s * .5, s * .06); g.fill(); g.fillStyle = "#5a3d2b"; g.beginPath(); g.arc(0, s * .2, s * .06, 0, 7); g.fill(); g.fillRect(-s * .025, s * .2, s * .05, s * .14); } },
  burst: { draw(g, s) { g.fillStyle = "#ffcf4a"; g.beginPath(); for (let i = 0; i < 24; i++) { const a = i / 24 * Math.PI * 2, r = i % 2 ? s * .32 : s * .5; g.lineTo(Math.cos(a) * r, Math.sin(a) * r); } g.fill(); } },
  apple: { draw(g, s) { g.fillStyle = "#e5484d"; g.beginPath(); g.arc(-s * .14, s * .04, s * .3, 0, 7); g.arc(s * .14, s * .04, s * .3, 0, 7); g.fill(); g.fillStyle = "#8a5a3b"; g.fillRect(-s * .025, -s * .4, s * .05, s * .16); g.fillStyle = "#59b05f"; g.beginPath(); g.ellipse(s * .12, -s * .33, s * .12, s * .05, -.5, 0, 7); g.fill(); } },
  question: { w: .7, h: 1.1, draw(g, s) { T(g, "?", 0, s * .05, s * 1.0, "#4f9dff"); } },
  cloud: { w: 1.4, h: .8, draw(g, s) { g.fillStyle = "#ffffff"; for (const [x, y, r] of [[0, 0, .3], [-.35, .08, .22], [.35, .08, .24], [.15, -.15, .22]]) { g.beginPath(); g.arc(x * s, y * s, r * s, 0, 7); g.fill(); } } },
  heart: { draw(g, s) { g.fillStyle = "#ff6b8a"; g.beginPath(); g.moveTo(0, s * .4); g.bezierCurveTo(-s * .6, 0, -s * .35, -s * .5, 0, -s * .18); g.bezierCurveTo(s * .35, -s * .5, s * .6, 0, 0, s * .4); g.fill(); } },
  cow: { w: 1.5, draw(g, s) { g.fillStyle = "#fbfaf5"; rr(g, -s * .55, -s * .15, s * .9, s * .45, s * .1); g.fill(); g.fillStyle = "#2d2d33"; g.beginPath(); g.ellipse(-s * .2, 0, s * .14, s * .1, .3, 0, 7); g.fill(); g.fillStyle = "#fbfaf5"; g.fillRect(-s * .45, s * .25, s * .1, s * .25); g.fillRect(s * .15, s * .25, s * .1, s * .25); rr(g, s * .28, -s * .4, s * .34, s * .34, s * .06); g.fill(); g.fillStyle = "#f2a7a7"; rr(g, s * .4, -s * .2, s * .24, s * .16, s * .05); g.fill(); g.fillStyle = "#2d2d33"; g.fillRect(s * .36, -s * .32, s * .04, s * .05); } },
  squirrel: { draw(g, s) { g.fillStyle = "#c8763a"; g.beginPath(); g.ellipse(-s * .25, -s * .1, s * .2, s * .42, -.3, 0, 7); g.fill(); g.beginPath(); g.ellipse(s * .08, s * .12, s * .22, s * .28, 0, 0, 7); g.fill(); g.beginPath(); g.arc(s * .15, -s * .22, s * .15, 0, 7); g.fill(); g.fillStyle = "#2b2018"; g.beginPath(); g.arc(s * .2, -s * .24, s * .025, 0, 7); g.fill(); } },
};
// words → pieces (first match wins per word)
const KEYWORDS = [
  [/^(money|dollars?|bills?|cash)$/, ["bill", "coin"]], [/^coins?$/, ["coin"]], [/^(tons|rich|lots|loads)$/, ["bag", "bill"]],
  [/^(everyone|everybody|people|neighbou?rs)$/, ["crowd"]], [/^(ice|cream)$/, ["icecream"]], [/^trees?$/, ["tree"]],
  [/^(houses?|town|home)$/, ["house"]], [/^(hard|difficult|climb)$/, ["mountain"]], [/^(special|valuable|precious|rare|treasure)$/, ["gem"]],
  [/^(safe|keep|hide|locked)$/, ["lock"]], [/^apples?$/, ["apple"]], [/^(think|wonder|why|what)$/, ["question"]], [/^(love|happy)$/, ["heart"]],
  [/^(cows?)$/, ["cow"]], [/^squirrels?$/, ["squirrel"]], [/^(costs?|price|expensive)$/, ["burst"]],
];
const PAPERS = ["#f2c14e", "#8ecae6", "#b8e0b0", "#ffb4a2", "#cdb4db", "#ffd6a5"];
const LETTER_PAPERS = ["#fbf8f1", "#fff3b0", "#ffd6e0", "#d6f0ff", "#e8e8e8", "#1f2430"];
const LETTER_FONTS = ["700 {s}px Fredoka, sans-serif", "900 {s}px Georgia, serif", "700 {s}px 'Courier New', monospace", "800 {s}px Impact, 'Arial Black', sans-serif", "700 italic {s}px serif"];

// a word as ransom-note letters: each letter on its own scrap
function wordPiece(text, size, seed) {
  const r = rng(seed), scraps = [];
  for (const ch of text) {
    if (ch === " ") { scraps.push({ space: true }); continue; }
    const paper = LETTER_PAPERS[Math.floor(r() * LETTER_PAPERS.length)], dark = paper === "#1f2430";
    const font = LETTER_FONTS[Math.floor(r() * LETTER_FONTS.length)].replace("{s}", Math.round(size * (.85 + r() * .3)));
    const c = document.createElement("canvas"), g = c.getContext("2d"); g.font = font;
    const w = Math.ceil(g.measureText(ch).width + size * .3), h = Math.ceil(size * 1.25);
    c.width = w; c.height = h; g.fillStyle = paper; g.fillRect(0, 0, w, h); grainOver(g, w, h, .3);
    g.font = font; g.textAlign = "center"; g.textBaseline = "middle"; g.fillStyle = dark ? "#fbf8f1" : ["#1f2430", "#e5484d", "#2f6fd6", "#1f2430"][Math.floor(r() * 4)];
    g.fillText(ch, w / 2, h / 2 + size * .04);
    scraps.push({ c, w, h, rot: (r() - .5) * .22, dy: (r() - .5) * size * .15 });
  }
  const total = scraps.reduce((a, s) => a + (s.space ? size * .35 : s.w * .92), 0);
  const C = document.createElement("canvas"); C.width = Math.ceil(total + size * .6); C.height = Math.ceil(size * 1.8);
  const g = C.getContext("2d"); let x = size * .3;
  for (const s of scraps) {
    if (s.space) { x += size * .35; continue; }
    g.save(); g.translate(x + s.w / 2, C.height / 2 + s.dy); g.rotate(s.rot);
    g.shadowColor = "rgba(0,0,0,.25)"; g.shadowBlur = 6; g.shadowOffsetY = 3; g.drawImage(s.c, -s.w / 2, -s.h / 2); g.restore();
    x += s.w * .92;
  }
  return C;
}

// estimate when each word is spoken, from character counts (pauses for … , . ?)
function wordTimes(text, v0, vd) {
  const toks = text.split(/\s+/).filter(Boolean);
  const weight = w => w.replace(/[^\p{L}\p{N}$]/gu, "").length + 1 + (/[…]|\.\.\./.test(w) ? 6 : /[,.?!:]$/.test(w) ? 3 : 0);
  const total = toks.reduce((a, w) => a + weight(w), 0); let acc = 0;
  return toks.map(w => { const t = v0 + acc / total * vd; acc += weight(w); return { word: w, clean: w.toLowerCase().replace(/[^a-z0-9$,]/g, "").replace(/,$/, ""), t }; });
}

const SLOTS = {   // centres as fractions of the frame; the band y .17–.52 stays clear of captions (y≈.69)
  1: [[.5, .34]], 2: [[.34, .27], [.66, .45]], 3: [[.5, .25], [.27, .44], [.73, .46]],
  4: [[.3, .22], [.72, .25], [.3, .45], [.7, .47]], 5: [[.5, .34], [.24, .2], [.78, .21], [.25, .48], [.76, .49]],
  6: [[.27, .2], [.73, .2], [.5, .34], [.25, .48], [.75, .48], [.5, .52]],
};

export function makeCollage(line, opt = {}, seed = 1) {
  const r = rng(seed * 991 + 7);
  const from = opt.from ?? 0, to = opt.to ?? 1;
  const tIn = line.v0 + from * line.vd - .25, tOut = line.v0 + to * line.vd + .2;
  const words = wordTimes(line.en, line.v0, line.vd).filter(w => w.t >= tIn - .05 && w.t <= tOut);
  // pieces: listed, or picked from the spoken words
  let picks = [];
  if (opt.pieces) picks = opt.pieces.map((p, i) => ({ kind: p, t: tIn + .35 + i * Math.max(.3, (tOut - tIn - .8) / opt.pieces.length) }));
  else for (const w of words) for (const [re, kinds] of KEYWORDS) if (re.test(w.clean)) { kinds.forEach((k, j) => picks.push({ kind: k, t: w.t + j * .18 })); break; }
  picks = picks.filter((p, i) => LIB[p.kind] && picks.findIndex(q => q.kind === p.kind) === i).slice(0, 5);
  if (!picks.length) picks.push({ kind: "question", t: tIn + .4 });
  // the cut-out words: listed, CAPS in the line, or the longest spoken word
  let wt = opt.words || words.filter(w => /^[A-Z$][A-Z0-9$,!?]+$/.test(w.word.replace(/[…."]/g, "")) && w.word.length > 1).map(w => w.word.replace(/[….,"]/g, ""));
  if (!wt.length && words.length) wt = [words.slice().sort((a, b) => b.clean.length - a.clean.length)[0].word.replace(/[…."?!,]/g, "").toUpperCase()];
  const wordAt = (txt) => (words.find(w => w.clean.startsWith(txt.toLowerCase().split(" ")[0].replace(/[^a-z0-9$]/g, ""))) || { t: tIn + .5 }).t;
  // build images
  const slots = SLOTS[Math.min(6, picks.length)];
  const items = picks.map((p, i) => {
    const def = LIB[p.kind], hero = i === 0, s = (hero ? 440 : 330) * (picks.length > 3 ? .82 : 1);
    const img = cutout((g, sz) => def.draw(g, sz, i), s, seed * 31 + i, { w: def.w || 1, h: def.h || 1 });
    const [sx, sy] = slots[i];
    return { img, x: sx * W + (r() - .5) * 60, y: sy * H + (r() - .5) * 50, rot: (r() - .5) * .35, t: Math.max(tIn + .3, p.t), tape: r() < .45 };
  });
  wt.slice(0, 2).forEach((txt, i) => {
    const img = wordPiece(txt, 120, seed * 13 + i);
    items.push({ img, x: W / 2 + (r() - .5) * 80, y: (i ? .1 : .6) * H, rot: (r() - .5) * .12, t: Math.max(tIn + .35, wordAt(txt)), word: true, scale: Math.min(1, 960 / img.width) });
  });
  items.sort((a, b) => a.t - b.t);
  // background sheet with a torn top edge and a couple of decorative scraps
  const paper = opt.paper || PAPERS[seed % PAPERS.length];
  const sheet = document.createElement("canvas"); sheet.width = W; sheet.height = H + 120;
  { const g = sheet.getContext("2d"), rr2 = rng(seed + 5); g.fillStyle = paper; g.beginPath(); g.moveTo(0, 60);
    for (let x = 0; x <= W; x += 18) g.lineTo(x, 40 + rr2() * 40); g.lineTo(W, H + 120); g.lineTo(0, H + 120); g.fill();
    grainInto(sheet, .5);
    g.save(); g.globalCompositeOperation = "source-atop";
    g.fillStyle = "rgba(255,255,255,.55)"; g.fillRect(0, 50, W, 26);   // white torn rim
    // newsprint scraps
    for (const [x, y, w, h, a] of [[-40, 1520, 420, 260, -.12], [760, 180, 380, 220, .18]]) {
      g.save(); g.translate(x + w / 2, y + h / 2); g.rotate(a); g.fillStyle = "#ece6d8"; g.fillRect(-w / 2, -h / 2, w, h);
      g.fillStyle = "rgba(60,60,60,.35)"; for (let ly = -h / 2 + 24; ly < h / 2 - 10; ly += 22) g.fillRect(-w / 2 + 20, ly, w - 40 - (ly % 3) * 30, 8); g.restore();
    }
    g.restore(); }

  const events = [{ t: tIn, type: "tear", dur: .45 }, { t: tOut - .05, type: "tear", dur: .35, soft: 1 }, ...items.map((it, i) => ({ t: it.t, type: "slap", n: i }))];

  return {
    tIn, tOut, events,
    covers: t => t >= tIn + .35 && t <= tOut - .05,
    draw(g, t) {
      if (t < tIn || t > tOut + .35) return false;
      const tq = step12(t);
      const enter = 1 - back(seg(tq, tIn, tIn + .35)), exit = seg(tq, tOut, tOut + .35);
      const oy = enter * (H + 140) + Math.pow(exit, 2) * (H + 140);
      const push = 1 + .05 * seg(t, tIn, tOut);                 // slow push so the held collage breathes
      g.save(); g.translate(0, oy);
      g.shadowColor = "rgba(0,0,0,.3)"; g.shadowBlur = 30; g.shadowOffsetY = -6;
      g.drawImage(sheet, 0, -60); g.shadowColor = "transparent";
      g.translate(W / 2, H * .42); g.scale(push, push); g.translate(-W / 2, -H * .42);
      items.forEach((it, i) => {
        const k = seg(tq, it.t, it.t + .25); if (k <= 0) return;
        const lift = 1 - back(k), boil = (hash(Math.floor(t * 12) * 7 + i) - .5) * .02;
        const sc = (it.scale || 1) * (1 + .35 * lift);
        g.save(); g.translate(it.x, it.y - 40 * lift); g.rotate(it.rot + lift * .3 + boil); g.scale(sc, sc);
        g.shadowColor = "rgba(0,0,0,.28)"; g.shadowBlur = 14 + 30 * lift; g.shadowOffsetY = 8 + 30 * lift; g.shadowOffsetX = 4;
        g.drawImage(it.img, -it.img.width / 2, -it.img.height / 2);
        g.shadowColor = "transparent";
        if (it.tape && !it.word) { g.fillStyle = "rgba(245,235,200,.75)"; g.rotate(-.5); g.fillRect(-60, -it.img.height / 2 - 6, 120, 34); }
        g.restore();
      });
      g.restore();
      return true;
    },
  };
}
