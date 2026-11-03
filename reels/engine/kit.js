// Low-poly kit: blocky people, animals, props and environments.
// Everything is flat-shaded primitives with flat colours, so any episode can be
// assembled from code. All builders return a THREE.Group positioned at its feet / base.
import * as THREE from "three";

export const PAL = {
  skin: ["#f2c9a0", "#d9a273", "#a8714a", "#7a4e2d"],
  hair: ["#2b2018", "#5a3a22", "#c98b3c", "#1c1c24", "#d9d4cc"],
  shirt: ["#ff7a59", "#4f9dff", "#ffcf4a", "#59c27a", "#b388ff", "#ff9ec4", "#3fc1c9"],
  pants: ["#3a4a6b", "#5b4a3a", "#2f3640", "#6d7b8c"],
  grass: "#9fd67a", grassDark: "#7cbf5e", dirt: "#d9b48a", trunk: "#8a5a3b",
  leaf: "#5fb85a", autumn: ["#f2a541", "#e8743b", "#f6c453", "#d9542b"],
  money: "#7cc47f", moneyDark: "#3f8f53", gold: "#f7c948", sky: "#bfe3ff",
  white: "#fbfaf5", ink: "#22252b", red: "#e5484d", pink: "#ff9ec4",
};

const matCache = new Map();
export function mat(color, o = {}) {
  const key = color + JSON.stringify(o);
  if (!matCache.has(key)) matCache.set(key, new THREE.MeshStandardMaterial({ color, flatShading: true, roughness: .85, metalness: 0, ...o }));
  return matCache.get(key);
}
export function mesh(geo, color, o = {}) {
  const m = new THREE.Mesh(geo, color instanceof THREE.Material ? color : mat(color, o.mat));
  m.castShadow = o.cast ?? true; m.receiveShadow = o.receive ?? true;
  if (o.pos) m.position.set(...o.pos);
  if (o.rot) m.rotation.set(...o.rot);
  if (o.scale) Array.isArray(o.scale) ? m.scale.set(...o.scale) : m.scale.setScalar(o.scale);
  return m;
}
const box = (w, h, d, c, o) => mesh(new THREE.BoxGeometry(w, h, d), c, o);
// a pivot: a group placed at a joint, with its child hanging below it
function pivot(parent, at, child) { const g = new THREE.Group(); g.position.set(...at); g.add(child); parent.add(g); return g; }

// seeded random so every frame / every render is identical
export function rng(seed = 1) { let s = seed >>> 0; return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

/* ── people ── */
// person({kid, shirt, pants, skin, hair, hat}) → group with .rig joints and .pose(p)
export function person(o = {}) {
  const s = o.kid ? .72 : 1, root = new THREE.Group(), body = new THREE.Group();
  root.add(body);
  const skin = o.skin || PAL.skin[0], shirt = o.shirt || PAL.shirt[0], pants = o.pants || PAL.pants[0], hairC = o.hair || PAL.hair[0];
  const hips = new THREE.Group(); hips.position.y = .88 * s; body.add(hips);
  const legGeo = [.22 * s, .86 * s, .26 * s];
  const leg = x => pivot(hips, [x * s, 0, 0], (() => { const g = new THREE.Group(); g.add(box(...legGeo, pants, { pos: [0, -.43 * s, 0] })); g.add(box(.24 * s, .12 * s, .34 * s, "#3b3b44", { pos: [0, -.82 * s, .04 * s] })); return g; })());
  const legL = leg(-.15), legR = leg(.15);
  const torso = new THREE.Group(); hips.add(torso);
  torso.add(box(.62 * s, .72 * s, .36 * s, shirt, { pos: [0, .36 * s, 0] }));
  const arm = x => pivot(torso, [x * s, .66 * s, 0], (() => { const g = new THREE.Group(); g.add(box(.18 * s, .58 * s, .2 * s, shirt, { pos: [0, -.27 * s, 0] })); g.add(box(.17 * s, .18 * s, .19 * s, skin, { pos: [0, -.62 * s, 0] })); return g; })());
  const armL = arm(-.41), armR = arm(.41);
  const neck = new THREE.Group(); neck.position.y = .74 * s; torso.add(neck);
  const headS = (o.kid ? .56 : .46) * s / (o.kid ? .72 : 1) * (o.kid ? .72 : 1);
  const head = new THREE.Group(); neck.add(head);
  head.add(box(headS, headS, headS, skin, { pos: [0, headS / 2, 0] }));
  head.add(box(headS * 1.06, headS * .26, headS * 1.06, hairC, { pos: [0, headS * .95, -.01] }));
  head.add(box(headS * 1.06, headS * .6, headS * .2, hairC, { pos: [0, headS * .62, -headS * .46] }));
  if (o.longHair) head.add(box(headS * 1.08, headS * .9, headS * .26, hairC, { pos: [0, headS * .35, -headS * .45] }));
  if (o.hat) { head.add(box(headS * 1.3, headS * .08, headS * 1.3, o.hat, { pos: [0, headS * 1.08, 0] })); head.add(box(headS * .9, headS * .4, headS * .9, o.hat, { pos: [0, headS * 1.3, 0] })); }
  const eyes = [];
  for (const x of [-.22, .22]) { const e = box(headS * .12, headS * .16, .02, PAL.ink, { pos: [x * headS, headS * .55, headS / 2 + .005], cast: false }); head.add(e); eyes.push(e); }
  const mouth = box(headS * .26, headS * .07, .02, "#8a3b3b", { pos: [0, headS * .28, headS / 2 + .005], cast: false }); head.add(mouth);
  for (const x of [-.34, .34]) head.add(box(headS * .14, headS * .08, .02, "#f29b8f", { pos: [x * headS, headS * .38, headS / 2 + .004], cast: false }));
  root.rig = { body, hips, torso, legL, legR, armL, armR, neck, head, mouth, eyes, s, headS };
  root.pose = p => applyPose(root, p);
  return root;
}
// a pose is a plain object of joint rotations (radians); missing = 0
export function applyPose(fig, p = {}) {
  const r = fig.rig, z = (j, v) => { j.rotation.set(...(Array.isArray(v) ? v : [v || 0, 0, 0])); };
  z(r.armL, p.armL); z(r.armR, p.armR); z(r.legL, p.legL); z(r.legR, p.legR);
  z(r.torso, p.torso); z(r.neck, p.head);
  r.body.position.y = (p.bob || 0) * (r.s < 1 ? .72 : 1);
  r.mouth.scale.y = p.mouth ?? 1;                 // 1 = closed line, 3 = open
  r.eyes.forEach(e => (e.scale.y = p.blink ? .15 : 1));
}
const lerp = (a, b, k) => a + (b - a) * k;
export function mixPose(a, b, k) {
  const o = {};
  for (const key of new Set([...Object.keys(a), ...Object.keys(b)])) {
    const va = a[key] ?? (Array.isArray(b[key]) ? [0, 0, 0] : 0), vb = b[key] ?? (Array.isArray(va) ? [0, 0, 0] : 0);
    const A = Array.isArray(va) ? va : [va, 0, 0], B = Array.isArray(vb) ? vb : [vb, 0, 0];
    o[key] = (Array.isArray(va) || Array.isArray(vb)) ? A.map((x, i) => lerp(x, B[i], k)) : lerp(va, vb, k);
  }
  return o;
}
const D = Math.PI / 180;
export const POSES = {
  idle: {},
  rake: { armL: [-40 * D, 0, 0], armR: [-55 * D, 0, 0], torso: [12 * D, 0, 0], head: [10 * D, 0, 0] },
  rake2: { armL: [-10 * D, 0, 0], armR: [-25 * D, 0, 0], torso: [22 * D, 0, 0], head: [8 * D, 0, 0] },
  lookUp: { armL: [-20 * D, 0, -10 * D], armR: [-20 * D, 0, 10 * D], head: [-38 * D, 0, 0], torso: [-6 * D, 0, 0], mouth: 3 },
  reach: { armR: [-170 * D, 0, 8 * D], armL: [-20 * D, 0, -15 * D], head: [-30 * D, 0, 0], torso: [-4 * D, 0, 0] },
  cheer: { armL: [-160 * D, 0, -25 * D], armR: [-160 * D, 0, 25 * D], head: [-10 * D, 0, 0], mouth: 3 },
  holdOut: { armR: [-80 * D, 0, 0], armL: [-15 * D, 0, -8 * D] },
  holdUp: { armR: [-100 * D, 0, 0], armL: [-20 * D, 0, -10 * D], head: [-15 * D, 0, 0], mouth: 3 },
  shock: { armL: [-30 * D, 0, -50 * D], armR: [-30 * D, 0, 50 * D], head: [8 * D, 0, 0], torso: [-8 * D, 0, 0], mouth: 4 },
  think: { armR: [-130 * D, 0, 40 * D], armL: [-35 * D, 0, -40 * D], head: [-12 * D, 18 * D, 8 * D] },
  sit: { legL: [-90 * D, 0, 0], legR: [-90 * D, 0, 0], armL: [-30 * D, 0, 0], armR: [-50 * D, 0, 0], head: [12 * D, 0, 0], bob: -.7 },
  sitLook: { legL: [-90 * D, 0, 0], legR: [-90 * D, 0, 0], armL: [-30 * D, 0, 0], armR: [-70 * D, 0, 0], head: [-6 * D, 0, 0], bob: -.7 },
  bite: { armR: [-120 * D, 0, 25 * D], armL: [-15 * D, 0, -8 * D], head: [6 * D, 0, 0], mouth: 3 },
  shrug: { armL: [-40 * D, 0, -70 * D], armR: [-40 * D, 0, 70 * D], head: [0, 0, 10 * D], mouth: 1 },
  wave: { armR: [-150 * D, 0, 30 * D], armL: [-10 * D, 0, -8 * D], mouth: 3 },
  point: { armR: [-90 * D, 0, 20 * D], armL: [-10 * D, 0, -8 * D], mouth: 3 },
};
// walking / running cycle (phase in cycles)
export function walk(phase, amt = 1) {
  const a = Math.sin(phase * Math.PI * 2) * 35 * D * amt;
  return { legL: [a, 0, 0], legR: [-a, 0, 0], armL: [-a * .8, 0, 0], armR: [a * .8, 0, 0], bob: Math.abs(Math.cos(phase * Math.PI * 2)) * .05 * amt };
}

/* ── animals ── */
export function squirrel() {
  const g = new THREE.Group(), c = "#c8763a", belly = "#f2d3a8";
  g.add(mesh(new THREE.IcosahedronGeometry(.22, 0), c, { pos: [0, .24, 0], scale: [1, 1.15, 1.25] }));
  g.add(mesh(new THREE.IcosahedronGeometry(.14, 0), belly, { pos: [0, .22, .12], scale: [1, 1.2, .8] }));
  const head = new THREE.Group(); head.position.set(0, .48, .12); g.add(head);
  head.add(box(.24, .22, .24, c, { pos: [0, 0, 0] }));
  head.add(box(.1, .08, .06, belly, { pos: [0, -.04, .13] }));
  for (const x of [-.07, .07]) { head.add(box(.04, .05, .02, PAL.ink, { pos: [x, .03, .125], cast: false })); head.add(mesh(new THREE.ConeGeometry(.05, .12, 4), c, { pos: [x * 1.2, .16, -.02] })); }
  const tail = new THREE.Group(); tail.position.set(0, .2, -.22); g.add(tail);
  [[0, .1, -.08, 1], [0, .3, -.16, 1.15], [0, .52, -.12, 1.2], [0, .68, .0, 1]].forEach(([x, y, z, sc], i) =>
    tail.add(mesh(new THREE.IcosahedronGeometry(.13, 0), i % 2 ? "#d98a4a" : c, { pos: [x, y, z], scale: sc })));
  for (const x of [-.1, .1]) g.add(box(.07, .1, .12, c, { pos: [x, .04, .1] }));
  g.rig = { head, tail }; return g;
}
export function cow() {
  const g = new THREE.Group(), W = PAL.white, B = "#2d2d33";
  g.add(box(1.5, .8, .8, W, { pos: [0, 1.0, 0] }));
  [[.3, 1.25, .41, .4, .3], [-.4, .95, .41, .35, .35], [.1, 1.0, -.41, .5, .3], [-.5, 1.3, -.41, .3, .2]].forEach(([x, y, z, w, h]) => g.add(box(w, h, .02, B, { pos: [x, y, z] })));
  for (const [x, z] of [[.55, .28], [.55, -.28], [-.55, .28], [-.55, -.28]]) g.add(box(.18, .62, .18, W, { pos: [x, .31, z] }));
  const head = new THREE.Group(); head.position.set(.85, 1.25, 0); g.add(head);
  head.add(box(.5, .5, .5, W, { pos: [.15, 0, 0] }));
  head.add(box(.2, .28, .46, "#f2a7a7", { pos: [.45, -.12, 0] }));
  for (const z of [-.14, .14]) { head.add(box(.02, .07, .07, B, { pos: [.41, .1, z], cast: false })); head.add(mesh(new THREE.ConeGeometry(.05, .2, 4), "#efe2c4", { pos: [.1, .32, z * 1.6], rot: [z > 0 ? .5 : -.5, 0, 0] })); }
  const jaw = box(.18, .08, .4, "#f2a7a7", { pos: [.45, -.3, 0] }); head.add(jaw);
  g.rig = { head, jaw }; return g;
}
export function bird(color = "#ffffff") {
  const g = new THREE.Group();
  g.add(mesh(new THREE.IcosahedronGeometry(.12, 0), color, { scale: [1.4, 1, 1] }));
  g.add(mesh(new THREE.ConeGeometry(.03, .08, 4), "#f2a541", { pos: [.18, .02, 0], rot: [0, 0, -Math.PI / 2] }));
  const wL = box(.14, .02, .2, color, { pos: [0, .05, .12] }), wR = box(.14, .02, .2, color, { pos: [0, .05, -.12] });
  g.add(wL, wR); g.rig = { wL, wR }; return g;
}

/* ── nature ── */
export function tree(o = {}) {
  const g = new THREE.Group(), h = o.h || 2.2, r = rng(o.seed || 3);
  g.add(mesh(new THREE.CylinderGeometry(.16, .24, h, 6), PAL.trunk, { pos: [0, h / 2, 0] }));
  const canopy = new THREE.Group(); canopy.position.y = h; g.add(canopy);
  const blobs = o.blobs || [[0, .5, 0, 1.15], [-.7, .15, .2, .8], [.7, .2, -.1, .85], [0, .1, .6, .7], [.1, 1.1, -.1, .75]];
  const cols = o.colors || [PAL.leaf];
  blobs.forEach(([x, y, z, s], i) => canopy.add(mesh(new THREE.IcosahedronGeometry(s, 0), cols[i % cols.length], { pos: [x, y, z], rot: [r() * 3, r() * 3, 0] })));
  g.rig = { canopy };
  return g;
}
export function bush(c = PAL.grassDark, s = .5) { const g = new THREE.Group(); [[0, s * .7, 0, s], [s * .8, s * .5, .1, s * .7], [-s * .7, s * .45, 0, s * .65]].forEach(([x, y, z, r]) => g.add(mesh(new THREE.IcosahedronGeometry(r, 0), c, { pos: [x, y, z] }))); return g; }
export function rock(s = .4, c = "#b8b2a7") { return mesh(new THREE.DodecahedronGeometry(s, 0), c, { pos: [0, s * .6, 0], scale: [1.2, .8, 1] }); }
export function cloud(s = 1) { const g = new THREE.Group(); [[0, 0, 0, 1], [1, -.2, 0, .75], [-1, -.25, 0, .7], [.4, .45, 0, .7]].forEach(([x, y, z, r]) => g.add(mesh(new THREE.IcosahedronGeometry(r * s, 0), PAL.white, { pos: [x * s, y * s, z * s], cast: false }))); return g; }
// a big ground with low-poly bumps (flat area near the origin)
export function ground(o = {}) {
  const size = o.size || 120, seg = o.seg || 60;
  const geo = new THREE.PlaneGeometry(size, size, seg, seg); geo.rotateX(-Math.PI / 2);
  const p = geo.attributes.position, r = rng(o.seed || 9);
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), z = p.getZ(i), d = Math.hypot(x - (o.flatAt?.[0] || 0), z - (o.flatAt?.[1] || 0));
    const hill = Math.max(0, d - (o.flat || 14)) * .06;
    p.setY(i, (r() - .5) * .18 + hill * (1 + Math.sin(x * .15) * Math.cos(z * .12)) * (o.hills ?? 1.4));
  }
  geo.computeVertexNormals();
  return mesh(geo, o.color || PAL.grass, { cast: false });
}

/* ── props ── */
const texCache = new Map();
export function canvasTex(w, h, draw, key) {
  if (key && texCache.has(key)) return texCache.get(key);
  const c = document.createElement("canvas"); c.width = w; c.height = h; draw(c.getContext("2d"), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  if (key) texCache.set(key, t); return t;
}
export function bill() {
  const tex = canvasTex(256, 120, (g, w, h) => {
    g.fillStyle = PAL.money; g.fillRect(0, 0, w, h);
    g.strokeStyle = PAL.moneyDark; g.lineWidth = 8; g.strokeRect(8, 8, w - 16, h - 16);
    g.fillStyle = "#b9e3b5"; g.beginPath(); g.ellipse(w / 2, h / 2, 34, 40, 0, 0, 7); g.fill();
    g.fillStyle = PAL.moneyDark; g.font = "bold 64px sans-serif"; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("$", w / 2, h / 2 + 4);
  }, "bill");
  const m = new THREE.Mesh(new THREE.BoxGeometry(.42, .008, .2), [mat(PAL.moneyDark), mat(PAL.moneyDark), new THREE.MeshStandardMaterial({ map: tex, roughness: .9 }), new THREE.MeshStandardMaterial({ map: tex, roughness: .9 }), mat(PAL.moneyDark), mat(PAL.moneyDark)]);
  m.castShadow = true; return m;
}
export function coin() { return mesh(new THREE.CylinderGeometry(.12, .12, .03, 12), PAL.gold, { rot: [Math.PI / 2, 0, 0], mat: { metalness: .3, roughness: .4 } }); }
export function leaf(c) { const m = mesh(new THREE.TetrahedronGeometry(.11, 0), c, { scale: [1.3, .25, 1] }); return m; }
export function apple() { const g = new THREE.Group(); g.add(mesh(new THREE.IcosahedronGeometry(.13, 1), PAL.red)); g.add(box(.02, .08, .02, PAL.trunk, { pos: [0, .14, 0] })); g.add(box(.08, .01, .04, PAL.leaf, { pos: [.05, .15, 0], rot: [0, 0, .4] })); return g; }
export function rake() {
  const g = new THREE.Group();
  g.add(mesh(new THREE.CylinderGeometry(.025, .025, 1.5, 6), "#c79a5b", { pos: [0, .75, 0] }));
  g.add(box(.5, .05, .06, "#8a8f99", { pos: [0, .02, 0] }));
  for (let i = 0; i < 6; i++) g.add(box(.02, .1, .02, "#8a8f99", { pos: [-.22 + i * .088, -.05, 0] }));
  return g;
}
export function iceCream(scoops = 1) {
  const g = new THREE.Group();
  g.add(mesh(new THREE.ConeGeometry(.11, .3, 6), "#e0a85c", { pos: [0, -.15, 0], rot: [Math.PI, 0, 0] }));
  const cols = ["#ff9ec4", "#fff1c9", "#8a5a3b", "#a7e0a5", "#ffcf4a", "#b9a7ff"];
  g.scoops = [];
  for (let i = 0; i < 6; i++) { const s = mesh(new THREE.IcosahedronGeometry(.13, 1), cols[i], { pos: [0, .07 + i * .2, 0] }); s.visible = i < scoops; g.add(s); g.scoops.push(s); }
  return g;
}
export function house(o = {}) {
  const g = new THREE.Group(), w = o.w || 3, d = o.d || 2.6, h = o.h || 2.2;
  g.add(box(w, h, d, o.wall || "#f6efe0", { pos: [0, h / 2, 0] }));
  const roof = new THREE.Mesh(new THREE.CylinderGeometry(.01, w * .74, 1.4, 4, 1), mat(o.roof || "#e5735f"));
  roof.rotation.y = Math.PI / 4; roof.scale.set(1, 1, d / w); roof.position.y = h + .7; roof.castShadow = true; g.add(roof);
  g.add(box(.6, 1.1, .05, "#8a5a3b", { pos: [0, .55, d / 2 + .02] }));
  for (const x of [-w * .3, w * .3]) g.add(box(.55, .55, .05, "#9fd3ff", { pos: [x, h * .62, d / 2 + .02] }));
  return g;
}
export function fence(n = 6, gap = .7) {
  const g = new THREE.Group();
  for (let i = 0; i < n; i++) g.add(box(.12, .8, .08, "#fbfaf5", { pos: [i * gap, .4, 0] }));
  g.add(box(n * gap, .1, .06, "#fbfaf5", { pos: [(n - 1) * gap / 2, .55, 0] }));
  g.add(box(n * gap, .1, .06, "#fbfaf5", { pos: [(n - 1) * gap / 2, .25, 0] }));
  return g;
}
// a sign whose text can change: sign.setText("$2")
export function sign(w = 1.4, h = .8, o = {}) {
  const g = new THREE.Group();
  const c = document.createElement("canvas"); c.width = 512; c.height = Math.round(512 * h / w);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const face = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({ map: tex, roughness: .9 }));
  face.position.set(0, o.post ? 1.6 : 0, .045); g.add(face);
  g.add(box(w + .08, h + .08, .08, o.frame || "#8a5a3b", { pos: [0, o.post ? 1.6 : 0, 0] }));
  if (o.post) g.add(box(.1, 1.6, .1, "#8a5a3b", { pos: [0, .8, -.05] }));
  let last = null;
  g.setText = (txt, color = PAL.ink, bg = PAL.white) => {
    if (txt === last) return; last = txt;
    const x = c.getContext("2d"); x.fillStyle = bg; x.fillRect(0, 0, c.width, c.height);
    x.fillStyle = color; x.textAlign = "center"; x.textBaseline = "middle";
    let size = c.height * .62; x.font = `700 ${size}px Fredoka, sans-serif`;
    while (x.measureText(txt).width > c.width * .86) { size *= .92; x.font = `700 ${size}px Fredoka, sans-serif`; }
    x.fillText(txt, c.width / 2, c.height / 2 + size * .04); tex.needsUpdate = true;
  };
  return g;
}
export function stand(o = {}) {   // a little market stall with a striped awning
  const g = new THREE.Group(), w = o.w || 2.4;
  g.add(box(w, 1.0, .9, o.counter || "#fbfaf5", { pos: [0, .5, 0] }));
  g.add(box(w + .1, .08, 1.0, "#e9d8b4", { pos: [0, 1.04, 0] }));
  for (const x of [-w / 2 + .06, w / 2 - .06]) g.add(box(.08, 2.4, .08, "#8a5a3b", { pos: [x, 1.2, -.4] }));
  const n = 8;
  for (let i = 0; i < n; i++) g.add(box(w / n + .01, .08, 1.3, i % 2 ? PAL.white : (o.stripe || "#ff7a9c"), { pos: [-w / 2 + (i + .5) * w / n, 2.45, .05], rot: [-.25, 0, 0] }));
  return g;
}
