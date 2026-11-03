// Reel engine: one vertical 1080×1920 three.js stage, driven by time.
// An episode (episodes/<id>/episode.js) builds its world with the kit and returns
// update(t) + cam(t). The engine owns lights, sky, subtitles, the timeline from the
// voice durations, and the capture contract used by render.mjs:
//   window.DUR, window.render(t), window.EV, window.TIMELINE, window.READY
import * as THREE from "three";
import * as kit from "./kit.js";

export const W = 1080, H = 1920;
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const ease = {
  io: k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2,
  o: k => 1 - Math.pow(1 - k, 3),
  i: k => k * k * k,
  back: k => 1 + 2.7 * Math.pow(k - 1, 3) + 1.7 * Math.pow(k - 1, 2),
  lin: k => k,
};
export const seg = (t, a, b) => clamp((t - a) / (b - a));
export const lerp = (a, b, k) => a + (b - a) * k;
const lerp3 = (a, b, k) => a.map((v, i) => lerp(v, b[i], k));

// keyframes: [[t, value, easeName?], ...] → value at t (numbers or arrays)
export function key(t, keys, def = "io") {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    const [t1, v1, e] = keys[i], [t0, v0] = keys[i - 1];
    if (t < t1) { const k = ease[e || def](seg(t, t0, t1)); return Array.isArray(v0) ? lerp3(v0, v1, k) : lerp(v0, v1, k); }
  }
  return keys[keys.length - 1][1];
}
// pose keyframes: [[t, poseOrName], ...] with eased blends of `blend` seconds
export function poseTrack(t, keys, blend = .3) {
  const P = v => typeof v === "string" ? kit.POSES[v] : v;
  let p = P(keys[0][1]);
  for (let i = 1; i < keys.length; i++) if (t >= keys[i][0]) p = kit.mixPose(p, P(keys[i][1]), ease.io(seg(t, keys[i][0], keys[i][0] + (keys[i][2] ?? blend))));
  return p;
}
// camera shots: [[t, {pos, look, fov}, ease?, cut?], ...]; `cut: true` jumps instead of blending
export function camTrack(t, keys) {
  let i = 0; while (i < keys.length - 1 && t >= keys[i + 1][0]) i++;
  const [t0, a] = keys[i], nxt = keys[i + 1];
  if (!nxt || nxt[3]) return { ...a };
  const k = ease[nxt[2] || "io"](seg(t, t0, nxt[0])), b = nxt[1];
  return { pos: lerp3(a.pos, b.pos, k), look: lerp3(a.look, b.look, k), fov: lerp(a.fov ?? 40, b.fov ?? 40, k), roll: lerp(a.roll || 0, b.roll || 0, k) };
}
// handheld-ish drift so held shots breathe (deterministic)
export const drift = (t, amt = .03) => [Math.sin(t * .7) * amt, Math.sin(t * .53 + 1) * amt * .6, Math.cos(t * .61) * amt];

export async function boot(epId) {
  const base = `../episodes/${epId}/`;
  const [lines, dur, mod] = await Promise.all([
    fetch(base + "lines.json").then(r => r.json()),
    fetch(base + "voice/dur.json").then(r => r.json()),
    import(base + "episode.js"),
  ]);
  const ep = mod.default;

  /* timeline from the voice */
  let T0 = ep.intro ?? 0;
  const L = {};
  for (const ln of lines) {
    const lead = ln.lead ?? .5, tail = ln.tail ?? .8, vd = dur[ln.id];
    L[ln.id] = { ...ln, t0: T0, v0: T0 + lead, vd, t1: T0 + lead + vd + tail };
    T0 = L[ln.id].t1;
  }
  const DUR = +(T0 + (ep.outro ?? 2.5)).toFixed(2);
  const T = {
    line: id => L[id],
    at: (id, f = 0) => L[id].v0 + f * L[id].vd,     // a moment inside a spoken line (0..1)
    start: id => L[id].t0, end: id => L[id].t1, dur: DUR, lines: L,
  };

  /* stage */
  const canvas = document.getElementById("c");
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
  renderer.setSize(W, H, false); renderer.setPixelRatio(1);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = ep.exposure ?? 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  const sky = ep.sky || ["#9fd2ff", "#e9f6ff"];
  scene.background = kit.canvasTex(4, 512, (g, w, h) => { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, sky[0]); gr.addColorStop(1, sky[1]); g.fillStyle = gr; g.fillRect(0, 0, w, h); });
  scene.fog = new THREE.Fog(sky[1], ep.fog?.[0] ?? 30, ep.fog?.[1] ?? 90);
  const hemi = new THREE.HemisphereLight(ep.light?.sky || "#dff1ff", ep.light?.ground || "#d9c9a0", ep.light?.hemi ?? 1.5); scene.add(hemi);
  const sun = new THREE.DirectionalLight(ep.light?.sun || "#fff0d8", ep.light?.sunI ?? 2.4);
  sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -.0004; sun.shadow.normalBias = .02;
  const sc = sun.shadow.camera; sc.left = sc.bottom = -14; sc.right = sc.top = 14; sc.near = 1; sc.far = 80;
  scene.add(sun, sun.target);
  const sunDir = new THREE.Vector3(...(ep.sunDir || [6, 12, 7])).normalize();
  const camera = new THREE.PerspectiveCamera(40, W / H, .1, 300);

  /* sound events + music plan: episodes push to these while building */
  const EV = [];
  const ctx = {
    THREE, kit, scene, T, key, poseTrack, camTrack, seg, lerp, ease, drift,
    ev: (t, type, x = {}) => EV.push({ t: +(+t).toFixed(3), type, ...x }),
    music: null,
  };
  const world = await ep.build(ctx);
  for (const id in L) ctx.ev(L[id].v0, "voice", { id });

  /* subtitles */
  const sub = document.getElementById("sub"), subEn = sub.querySelector(".en"), subZh = sub.querySelector(".zh");
  let shown = null;
  function subtitles(t) {
    const cur = Object.values(L).find(l => t >= l.v0 - .05 && t < Math.max(l.v0 + l.vd + .5, l.v0 + 1.8));
    if (!cur) { sub.style.opacity = 0; shown = null; return; }
    if (shown !== cur.id) { subEn.textContent = cur.en; subZh.textContent = cur.zh; shown = cur.id; }
    const k = ease.back(seg(t, cur.v0 - .05, cur.v0 + .25));
    sub.style.opacity = clamp(seg(t, cur.v0 - .05, cur.v0 + .15));
    sub.style.transform = `translate(-50%, 0) scale(${.85 + .15 * k})`;
  }

  window.render = t => {
    t = clamp(t, 0, DUR);
    world.update(t);
    const c = world.cam(t);
    camera.position.set(...c.pos); camera.lookAt(...c.look); camera.fov = c.fov ?? 40;
    if (c.roll) camera.rotateZ(c.roll);
    camera.updateProjectionMatrix();
    // keep the shadow map centred on what the camera looks at
    const f = new THREE.Vector3(...(c.shadowAt || c.look));
    sun.target.position.copy(f); sun.position.copy(f).addScaledVector(sunDir, 30);
    if (c.shadowSize) { sc.left = sc.bottom = -c.shadowSize; sc.right = sc.top = c.shadowSize; sc.updateProjectionMatrix(); }
    renderer.render(scene, camera);
    subtitles(t);
  };
  window.DUR = DUR; window.EV = EV;
  window.TIMELINE = { lines: Object.values(L).map(({ id, en, zh, t0, v0, vd, t1 }) => ({ id, en, zh, t0, v0, vd, t1 })), music: world.music || null, dur: DUR };
  await document.fonts.ready;
  window.render(0);
  window.READY = true;
  return { ep, T };
}
