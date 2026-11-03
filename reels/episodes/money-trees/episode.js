// What if money grew on trees?  — a 9:16 low-poly reel.
// The world is built once; update(t) poses everything; cam(t) returns the shot.
// Times come from the voice (T.at(lineId, fraction)), so re-recording the voice re-times the film.
import * as THREE from "three";

export default {
  intro: 0, outro: 3.6,
  sky: ["#8fcaff", "#fdf1dc"], fog: [45, 130],
  light: { sunI: 2.6, hemi: 1.45, sun: "#ffe9c9" }, sunDir: [7, 11, 8],

  build({ kit, scene, T, key, poseTrack, camTrack, seg, lerp, ease, drift, ev, ...ctx }) {
    const { person, tree, bill, coin, apple, iceCream, house, fence, sign, stand, squirrel, cow, cloud, bush, rock, ground, rake, rng, PAL, POSES, mixPose, walk, mesh } = kit;
    const at = T.at, L = T.line;
    const D = Math.PI / 180;
    const R = rng(42);

    /* ── places ── */
    const HOME = [1.3, 0, 1.4], TREE_A = [0, 0, 0], STAND = [9, 0, 1.0], SPOT = [9, 0, 3.0];
    const SQ = [-7, 0, 1.6], COW = [-11, 0, 4.4], APPLE_T = [4.6, 0, -1.2], SIT = [4.6, 0, -.35];

    scene.add(ground({ flatAt: [0, -4], flat: 22, hills: 1.6 }));
    // a dirt path between home and the stand
    for (let i = 0; i < 12; i++) scene.add(mesh(new THREE.CylinderGeometry(.42, .46, .04, 7), PAL.dirt, { pos: [1.5 + i * .72, .02, 2.6 + Math.sin(i * .8) * .25], cast: false }));

    // home
    const home = house({ w: 3.4, d: 2.8, h: 2.3, roof: "#e5735f" }); home.position.set(-4.2, 0, -4.5); home.rotation.y = .25; scene.add(home);
    const f1 = fence(9, .72); f1.position.set(-6.5, 0, 3.6); scene.add(f1);
    // tree A: autumn → money. Own materials so only this tree changes colour.
    const treeA = tree({ h: 2.3, seed: 5 }); treeA.position.set(...TREE_A); scene.add(treeA);
    const canopyMats = treeA.rig.canopy.children.map((m, i) => (m.material = new THREE.MeshStandardMaterial({ color: PAL.autumn[i % 4], flatShading: true, roughness: .85 })));
    const autumnC = PAL.autumn.map(c => new THREE.Color(c)), moneyC = [new THREE.Color("#6cc070"), new THREE.Color("#58b062"), new THREE.Color("#7dcf7d")];
    // bills that sprout on the canopy
    const sprout = [];
    treeA.rig.canopy.children.forEach((blob, bi) => {
      const r = blob.geometry.parameters.radius;
      for (let k = 0; k < 7; k++) {
        const b = bill(); const u = R() * Math.PI * 2, v = R() * Math.PI * .7;
        const p = new THREE.Vector3(Math.cos(u) * Math.sin(v), Math.cos(v), Math.sin(u) * Math.sin(v)).multiplyScalar(r * 1.02);
        b.position.copy(blob.position).add(p); b.lookAt(blob.position.clone().add(p.clone().multiplyScalar(2))); b.rotateX(Math.PI / 2);
        b.userData.t = at("wonder", .74) + (bi * 7 + k) * .018; b.scale.setScalar(0);
        treeA.rig.canopy.add(b); sprout.push(b);
      }
    });
    // leaves on the ground + the rake
    const leaves = [];
    for (let i = 0; i < 26; i++) { const l = kit.leaf(PAL.autumn[i % 4]); l.position.set(HOME[0] - 1.6 + R() * 3.4, .03, HOME[2] - .4 + R() * 2.2); l.rotation.y = R() * 6; scene.add(l); leaves.push(l); }
    const hookLeaf = kit.leaf(PAL.autumn[1]); hookLeaf.scale.setScalar(1.6); scene.add(hookLeaf);

    // other trees, bushes, rocks, clouds
    const appleTree = tree({ h: 2.0, seed: 8, colors: ["#56b35a", "#4ea653"] }); appleTree.position.set(...APPLE_T); scene.add(appleTree);
    const apples = [];
    [[-.5, .2, .9], [.6, .4, .7], [.2, -.1, 1.0], [-.8, .6, .4], [.9, -.05, .3]].forEach(p => { const a = apple(); a.position.set(...p); appleTree.rig.canopy.add(a); apples.push(a); });
    const treeB = tree({ h: 2.0, seed: 11 }); treeB.position.set(SQ[0] - .6, 0, SQ[2] - 1.0); scene.add(treeB);
    [[-2.6, 2.4], [3.0, 3.6], [6.5, -2.5], [-8.5, -1.5], [12.5, -1.0], [-13, 7]].forEach(([x, z], i) => { const b = bush(i % 2 ? PAL.grassDark : "#8fcf6a", .45 + (i % 3) * .1); b.position.set(x, 0, z); scene.add(b); });
    [[2.8, 4.2], [-3.5, 4.8], [11.5, 3.6]].forEach(([x, z]) => { const r = rock(.3); r.position.set(x, 0, z); scene.add(r); });
    const clouds = [[-12, 14, -30, 2.2], [10, 17, -34, 2.8], [26, 13, -26, 1.8], [-28, 16, -20, 2.4]].map(([x, y, z, s]) => { const c = cloud(s); c.position.set(x, y, z); scene.add(c); return c; });

    // ice-cream stand + seller + price sign
    const st = stand({ w: 2.6, stripe: "#ff7a9c" }); st.position.set(...STAND); scene.add(st);
    const seller = person({ shirt: "#ffffff", pants: "#3a4a6b", skin: PAL.skin[1], hair: PAL.hair[3], hat: "#ff7a9c" }); seller.position.set(STAND[0] + .3, 0, STAND[2] - .5); scene.add(seller);
    const price = sign(1.3, .8, { post: true, frame: "#ff7a9c" }); price.position.set(STAND[0] + 2.0, 0, STAND[2] + .9); price.rotation.y = -.25; scene.add(price);
    const priceFace = price.children[0];
    const standCone = iceCream(3); standCone.position.set(STAND[0] - .8, 1.25, STAND[2] + .1); standCone.scale.setScalar(1.6); scene.add(standCone);

    // squirrel corner
    const sq = squirrel(); sq.position.set(...SQ); scene.add(sq);
    const sqBill = bill(); sqBill.scale.setScalar(.6); sq.rig.head.add(sqBill); sqBill.position.set(0, -.06, .2);
    const acorn = new THREE.Group(); acorn.add(mesh(new THREE.IcosahedronGeometry(.07, 0), "#a86b3c", { scale: [1, 1.2, 1] })); acorn.add(mesh(new THREE.CylinderGeometry(.075, .07, .05, 6), "#6b4a2b", { pos: [0, .07, 0] })); scene.add(acorn);
    const hole = mesh(new THREE.CylinderGeometry(.2, .2, .02, 8), "#5a3d2b", { pos: [SQ[0] + .5, .015, SQ[2] - .2], cast: false }); scene.add(hole);
    const dirtPile = mesh(new THREE.IcosahedronGeometry(.16, 0), PAL.dirt, { pos: [SQ[0] + .8, .06, SQ[2] - .3], scale: [1.2, .5, 1] }); scene.add(dirtPile);

    // cow corner
    const cw = cow(); cw.position.set(...COW); cw.rotation.y = -Math.PI / 2 + .35; scene.add(cw);
    const f2 = fence(7, .72); f2.position.set(COW[0] - 2.6, 0, COW[2] - 1.6); scene.add(f2);
    const pile = []; for (let i = 0; i < 14; i++) { const b = bill(); b.position.set(COW[0] + .55 + (R() - .5) * .8, .02 + i * .012, COW[2] + 1.35 + (R() - .5) * .6); b.rotation.y = R() * 6; scene.add(b); pile.push(b); }
    const bowl = mesh(new THREE.CylinderGeometry(.6, .45, .22, 8), "#d9e6f2", { pos: [COW[0] + .55, .11, COW[2] + 1.35] }); scene.add(bowl);
    pile.forEach(b => (b.position.y += .2));
    const mouthBill = bill(); mouthBill.scale.setScalar(.8); cw.rig.head.add(mouthBill); mouthBill.position.set(.62, -.28, .05); mouthBill.rotation.set(0, .5, .2);

    // the town: neighbours with their own money trees
    const town = [], neighbours = [];
    for (let gx = -3; gx <= 3; gx++) for (let gz = 0; gz < 3; gz++) {
      const x = gx * 9.5 + (gz % 2) * 4.5, z = -14 - gz * 10;
      if (Math.abs(x) < 6 && gz === 0) continue;
      const h = house({ w: 3 + R(), d: 2.6, h: 2 + R() * .6, roof: ["#e5735f", "#5aa9e6", "#f2b84b", "#9b7fd1"][(gx + gz + 4) % 4], wall: ["#f6efe0", "#fff7e8", "#eaf3ff"][(gx + 9) % 3] });
      h.position.set(x, 0, z); h.rotation.y = (R() - .5) * .4; scene.add(h);
      const t = tree({ h: 2.1, seed: 20 + town.length, colors: ["#6cc070", "#58b062", "#7dcf7d"] }); t.position.set(x + 3.2, 0, z + 2.6); scene.add(t);
      t.rig.canopy.children.slice(0, 3).forEach(blob => { for (let k = 0; k < 4; k++) { const b = bill(); const a = R() * 6; b.position.set(blob.position.x + Math.cos(a) * .8, blob.position.y + .3 + R() * .4, blob.position.z + Math.sin(a) * .8); b.rotation.set(R(), R() * 6, R()); t.rig.canopy.add(b); } });
      town.push(t);
      const n = person({ shirt: PAL.shirt[town.length % 7], pants: PAL.pants[town.length % 4], skin: PAL.skin[town.length % 4], hair: PAL.hair[town.length % 5], kid: town.length % 3 === 0, longHair: town.length % 2 === 0 });
      n.position.set(x + 2.3, 0, z + 3.5); n.rotation.y = .5; scene.add(n); neighbours.push(n);
    }
    // the queue at the stand, everyone holding a brick of cash
    const queue = [0, 1, 2, 3].map(i => {
      const n = person({ shirt: PAL.shirt[(i * 2 + 1) % 7], pants: PAL.pants[i % 4], skin: PAL.skin[(i + 1) % 4], hair: PAL.hair[(i + 2) % 5], longHair: i % 2 === 1 });
      n.position.set(STAND[0] - 2.2 - i * 1.1, 0, STAND[2] + 2.2 + i * .35); n.rotation.y = .9; scene.add(n);
      const brick = mesh(new THREE.BoxGeometry(.45, .3, .22), PAL.money); brick.add(mesh(new THREE.BoxGeometry(.47, .08, .24), "#f6efe0"));
      n.rig.armR.add(brick); brick.position.set(0, -.62, .18); n.brick = brick; return n;
    });

    // the kid (our narrator: no name)
    const kid = person({ kid: true, shirt: "#ffcf4a", pants: "#4f6ba8", skin: PAL.skin[1], hair: "#3a2a1e" }); scene.add(kid);
    const kidRake = rake(); kid.rig.armR.add(kidRake); kidRake.position.set(0, -.45, .12); kidRake.rotation.set(-1.0, 0, 0);
    const cone = iceCream(0); kid.rig.armR.add(cone); cone.position.set(0, -.52, .1); cone.scale.setScalar(.85);
    const kidCoin = coin(); kidCoin.scale.setScalar(.75); kid.rig.armR.add(kidCoin); kidCoin.position.set(0, -.55, .12);
    const kidApple = apple(); kid.rig.armR.add(kidApple); kidApple.position.set(0, -.52, .12);
    const biteMark = mesh(new THREE.BoxGeometry(.1, .12, .06), "#fff7e0", { pos: [.05, .02, .1] }); kidApple.add(biteMark);
    const fallingApple = apple(); scene.add(fallingApple);
    const handBills = [0, 1, 2].map(i => { const b = bill(); kid.rig.armR.add(b); b.position.set(0, -.6 + i * .01, .1 + i * .02); b.rotation.set(Math.PI / 2, i * .3, 0); return b; });

    // money falling from tree A, and money rain over town
    const fall = [];
    for (let i = 0; i < 26; i++) {
      const b = bill(); scene.add(b);
      const a = R() * 6.28, r = .3 + R() * 1.6;
      fall.push({ b, ts: at("wonder", .8) + R() * 2.2, x: TREE_A[0] + Math.cos(a) * r, z: TREE_A[2] + .4 + Math.sin(a) * r, y0: 2.6 + R() * 1.4, v: .7 + R() * .5, ph: R() * 6, sp: 2 + R() * 2, ry: R() * 6 });
    }
    const rain = [];
    town.forEach((tr, i) => { for (let k = 0; k < 4; k++) { const b = bill(); scene.add(b); rain.push({ b, x: tr.position.x + (R() - .5) * 3, z: tr.position.z + (R() - .5) * 3, ph: R(), v: .8 + R() * .4, sp: 2 + R() * 2 }); } });
    // the last bill that drifts past the camera at the end
    const lastBill = bill(); lastBill.scale.setScalar(1.3); scene.add(lastBill);

    /* ── sound events ── */
    const W = L("wonder"), Dr = L("dream"), An = L("animals"), Ev = L("everyone"), Pr = L("price"), In = L("insight"), Ap = L("apple"), As = L("ask");
    const stopRake = at("wonder", .42);
    for (let t = .25; t < stopRake; t += .72) ev(t, "rake");
    ev(.1, "whoosh", { dur: 1.6, soft: 1 });
    ev(at("wonder", .74), "sparkle"); ev(at("wonder", .82), "rustle", { dur: 2.4 });
    ev(Dr.t0, "whoosh", { dur: .5 }); ev(at("dream", .12), "boing"); ev(at("dream", .25), "rustle", { dur: .6 });
    const conePop = at("dream", .62); for (let k = 0; k < 6; k++) ev(conePop + k * .22, "pop", { n: k });
    ev(conePop - .35, "whoosh", { dur: .5 });
    ev(An.t0, "whoosh", { dur: .5 }); ev(at("animals", .05), "chitter"); ev(at("animals", .3), "dig", { dur: .9 }); ev(at("animals", .5), "toss");
    const cowCut = at("animals", .58); ev(cowCut - .2, "whoosh", { dur: .5 }); ev(cowCut + .1, "moo");
    for (let k = 0; k < 4; k++) ev(at("animals", .8) + k * .32, "munch");
    ev(Ev.t0, "whoosh", { dur: 4.2, soft: 1 });
    ev(Pr.t0, "whoosh", { dur: .5 });
    const flip = at("price", .74); ev(flip - .25, "whoosh", { dur: .4 }); ev(flip, "kaching");
    ev(flip + .55, "plop"); ev(flip + .8, "plop"); ev(flip + 1.05, "plop");
    ev(In.t0 + .2, "whoosh", { dur: .8, soft: 1 }); ev(at("insight", .45), "coin");
    const bonk = Ap.t0 + .75; ev(bonk - .5, "whistle", { dur: .5 }); ev(bonk, "bonk"); ev(at("apple", .86), "crunch");
    ev(As.t0 + .2, "pop", { n: 3 });
    // music plan for mix.py
    const music = { bpm: 112, start: at("wonder", .74), stops: [[In.t0 + .1, bonk]], end: As.v0 + As.vd + .6, finalAt: As.v0 + As.vd + .6 };

    /* ── animation ── */
    const rakeKeys = []; for (let t = 0; t < stopRake; t += .36) rakeKeys.push([t, rakeKeys.length % 2 ? "rake2" : "rake", .3]);
    const kidPoses = [
      ...rakeKeys, [stopRake, "idle"], [at("wonder", .5), "lookUp", .4],
      [Dr.t0, "lookUp", .01], [at("dream", .1), "reach", .25], [at("dream", .35), "holdOut", .25],
      [conePop - .3, "holdUp", .2], [conePop + 1.2, "cheer", .25],
      [Ev.t0, "cheer", .01],
      [Pr.t0, "holdUp", .01], [flip + .05, "shock", .15],
      [In.t0, "sit", .01], [at("insight", .3), "sitLook", .5],
      [Ap.t0, "sitLook", .01], [bonk + .02, "sit", .08], [bonk + .5, "sitLook", .3], [at("apple", .78), "bite", .25], [at("apple", .95), "sitLook", .3],
      [As.t0, "sitLook", .01], [As.t0 + .3, { ...POSES.sitLook, head: [-4 * D, 0, 0], armR: [-40 * D, 0, 10 * D] }, .4], [As.v0 + .4, { ...POSES.sitLook, head: [-6 * D, 0, 8 * D], armR: [-30 * D, 0, 10 * D], mouth: 1 }, .5],
    ];

    function fallBill(f, t) {
      const dt = t - f.ts; f.b.visible = dt > 0; if (dt <= 0) return;
      const y = f.y0 - f.v * dt;
      if (y > .02) { f.b.position.set(f.x + Math.sin(dt * f.sp + f.ph) * .35, y, f.z + Math.cos(dt * f.sp * .7 + f.ph) * .2); f.b.rotation.set(Math.sin(dt * f.sp + f.ph) * .7, f.ry + dt, Math.cos(dt * f.sp * 1.3) * .5); }
      else { const tl = (f.y0 - .02) / f.v; f.b.position.set(f.x + Math.sin(tl * f.sp + f.ph) * .35, .02, f.z + Math.cos(tl * f.sp * .7 + f.ph) * .2); f.b.rotation.set(0, f.ry, 0); }
    }

    function update(t) {
      // clouds drift
      clouds.forEach((c, i) => { c.position.x = [-12, 10, 26, -28][i] + t * .15; });
      // the hook leaf
      const hl = seg(t, 0, 2.3);
      hookLeaf.visible = t < 6;
      hookLeaf.position.set(HOME[0] + .5 + Math.sin(hl * 7) * .35, lerp(3.4, .04, ease.o(hl) * .3 + hl * .7), HOME[2] + .9);
      hookLeaf.rotation.set(Math.sin(hl * 9) * .8 * (1 - hl), hl * 4, Math.cos(hl * 8) * .6 * (1 - hl));
      // tree A turns to money
      const mk = ease.io(seg(t, at("wonder", .7), at("wonder", .9)));
      canopyMats.forEach((m, i) => m.color.copy(autumnC[i % 4]).lerp(moneyC[i % 3], mk));
      treeA.rig.canopy.scale.setScalar(1 + .06 * Math.sin(seg(t, at("wonder", .72), at("wonder", .95)) * Math.PI));
      sprout.forEach(b => b.scale.setScalar(ease.back(seg(t, b.userData.t, b.userData.t + .35))));
      fall.forEach(f => fallBill(f, t));
      // apples stay on the tree except the one that falls
      apples[0].visible = t < Ap.t0 + .2;
      const fa = seg(t, Ap.t0 + .2, bonk);
      fallingApple.visible = t >= Ap.t0 + .2 && t < bonk + .55;
      if (fallingApple.visible) {
        const top = new THREE.Vector3(); apples[0].getWorldPosition(top);
        if (t < bonk) fallingApple.position.set(top.x, lerp(top.y, 1.05, ease.i(fa)), lerp(top.z, SIT[2] + .05, fa));
        else { const b = seg(t, bonk, bonk + .55); fallingApple.position.set(SIT[0] + .25 * b, 1.05 + Math.sin(b * Math.PI) * .45 - b * .25, SIT[2] + .2 + .25 * b); }
        fallingApple.rotation.set(t * 6, t * 3, 0);
      }

      // the kid: where, which way, what pose
      let kp = HOME, ky = 0;
      if (t >= at("dream", .58) && t < Ev.t0) { kp = SPOT; ky = -.15; }
      if (t >= Ev.t0 && t < Pr.t0) { kp = HOME; ky = .2; }
      if (t >= Pr.t0 && t < In.t0) { kp = SPOT; ky = -.15; }
      if (t >= In.t0) { kp = SIT; ky = 0; }
      kid.position.set(...kp); kid.rotation.y = ky;
      let P = poseTrack(t, kidPoses);
      if (t >= Ev.t0 && t < Pr.t0) P = mixPose(P, POSES.reach, .5 + .5 * Math.sin(t * 7));   // picking with everyone
      if (t > at("dream", .55) && t < In.t0) P = { ...P, bob: Math.abs(Math.sin(t * 5)) * .04 };
      kid.pose(P);
      kidRake.visible = t < stopRake + .5;
      handBills.forEach((b, i) => (b.visible = t > at("dream", .3) + i * .1 && t < at("dream", .58)));
      // ice-cream tower grows, then the top scoops fall off at the price shock
      cone.visible = (t >= at("dream", .58) && t < Ev.t0) || (t >= Pr.t0 && t < In.t0);
      cone.scoops.forEach((s, k) => {
        const tp = conePop + k * .22; s.visible = t >= tp;
        s.scale.setScalar(ease.back(seg(t, tp, tp + .25)));
        const drop = k >= 3 ? seg(t, flip + .3 + (k - 3) * .25, flip + .55 + (k - 3) * .25) : 0;
        const wob = Math.sin(t * 9 + k) * .025 * k * (t > flip ? 2 : 1);
        s.position.set(wob + drop * (k - 3.5) * .5, .07 + k * .2 - drop * (.07 + k * .2 + .9) , drop * .3);
        if (drop >= 1) s.visible = false;
      });
      const armRx = kid.rig.armR.rotation.x;
      cone.rotation.x = -armRx; kidCoin.rotation.set(-armRx + Math.PI / 2, t * 2, 0);
      kidCoin.visible = t >= at("insight", .4) && t < Ap.t0 + .5;
      kidCoin.scale.setScalar(.75 * ease.back(seg(t, at("insight", .4), at("insight", .4) + .3)));
      kidApple.visible = t >= bonk + .55; kidApple.rotation.x = -armRx;
      biteMark.visible = t >= at("apple", .86);
      kidApple.scale.setScalar(t >= at("apple", .86) ? .95 : 1);

      // seller and price sign
      seller.pose(poseTrack(t, [[0, "idle"], [conePop - .2, "wave", .3], [conePop + 1.4, "idle", .4], [flip - .4, "point", .3]]));
      const sf = seg(t, flip - .25, flip + .2);
      price.rotation.y = -.25 + ease.io(sf) * Math.PI * 2;
      price.setText(t < flip - .03 ? "$2" : "$1,000", t < flip ? PAL.ink : "#e5484d");
      priceFace.scale.setScalar(1 + .15 * Math.sin(seg(t, flip, flip + .4) * Math.PI));

      // squirrel: hop to the hole, bury the bill, toss the acorn
      const sh = seg(t, An.v0, at("animals", .3));
      sq.position.set(SQ[0] + .45 * ease.io(sh), Math.abs(Math.sin(sh * Math.PI * 3)) * .25 * (sh < 1 ? 1 : 0), SQ[2] - .15 * sh);
      sq.rotation.y = .35 + sh * .3;
      const dig = seg(t, at("animals", .3), at("animals", .48));
      sq.rig.head.rotation.x = dig > 0 && dig < 1 ? .5 + Math.sin(t * 30) * .25 : -.1;
      sq.rig.tail.rotation.x = Math.sin(t * 6) * .15 + (dig > 0 && dig < 1 ? .3 : 0);
      sqBill.visible = dig < .6;
      dirtPile.scale.set(1.2, .5 + dig * .5, 1);
      const ta = seg(t, at("animals", .5), at("animals", .5) + .7);
      acorn.position.set(SQ[0] + .3 - ta * 1.4, .07 + Math.sin(ta * Math.PI) * .9, SQ[2] + .3 + ta * .5); acorn.rotation.z = ta * 8;
      // cow chews cash salad
      const chew = t > at("animals", .78) ? Math.sin(t * 14) : 0;
      cw.rig.jaw.position.y = -.3 - Math.max(0, chew) * .06; cw.rig.head.rotation.z = -.15 + chew * .03;
      mouthBill.visible = t > at("animals", .78); mouthBill.rotation.z = .2 + chew * .2;
      pile.forEach((b, i) => (b.visible = !(t > at("animals", .8) + i * .08 && i > 8)));

      // town
      neighbours.forEach((n, i) => { n.pose(mixPose(POSES.reach, POSES.cheer, .5 + .5 * Math.sin(t * 4 + i))); });
      rain.forEach(r => {
        const show = t >= Ev.t0 - .3 && t < Pr.t0 + 6; r.b.visible = show; if (!show) return;
        const cyc = ((t * r.v * .25 + r.ph) % 1), y = 4.2 - cyc * 4.2;
        r.b.position.set(r.x + Math.sin(t * r.sp) * .3, y, r.z + Math.cos(t * r.sp) * .2); r.b.rotation.set(Math.sin(t * r.sp) * .6, t + r.ph * 6, 0);
      });
      queue.forEach((n, i) => {
        n.visible = t >= Pr.t0 && t < In.t0;
        const P = t < flip ? mixPose(POSES.holdOut, { armR: [-70 * D, 0, 0] }, .5 + .5 * Math.sin(t * 3 + i)) : POSES.shock;
        n.pose({ ...P, bob: Math.abs(Math.sin(t * 4 + i)) * .03 });
        n.brick.rotation.x = -n.rig.armR.rotation.x;
      });
      // the last bill drifting past the lens
      const lb = seg(t, As.v0 + .9, T.dur);
      lastBill.visible = lb > 0;
      lastBill.position.set(lerp(3.6, 5.6, lb) + Math.sin(lb * 9) * .2, lerp(2.4, .5, lb), lerp(1.2, 1.6, lb));
      lastBill.rotation.set(Math.sin(lb * 10) * .8, lb * 3, Math.cos(lb * 8) * .5);
    }

    /* ── camera ── */
    const C = (pos, look, fov = 40) => ({ pos, look, fov });
    const shots = [
      // hook: follow a falling leaf down to the kid raking
      [0, C([3.6, 3.0, 8.0], [1.8, 2.6, 2.3], 40)],
      [2.3, C([2.8, 1.4, 5.8], [1.4, 1.0, 1.6], 42)],
      [at("wonder", .5), C([2.8, 1.3, 5.2], [1.2, 1.2, 1.4], 42)],
      // tilt up with the kid to the tree as it turns to money (low angle = wonder)
      [at("wonder", .78), C([3.4, .9, 5.6], [.2, 2.8, 0], 50)],
      [W.t1, C([3.0, 1.0, 5.2], [.2, 2.4, .2], 52)],
      // dream: reaching for bills, then the ice-cream tower, orbiting
      [Dr.t0, C([1.9, 1.0, 4.2], [1.2, 1.8, 1.0], 44), "io", true],
      [conePop - .35, C([7.4, 1.2, 6.6], [9.0, 1.6, 2.6], 40), "io", true],
      [Dr.t1, C([10.6, 1.0, 6.4], [9.0, 1.7, 2.6], 40)],
      // animals: low and close on the squirrel, then dolly on the cow
      [An.t0, C([-6.1, .55, 3.5], [-6.8, .35, 1.4], 36), "io", true],
      [cowCut, C([-6.0, .45, 3.0], [-6.6, .3, 1.3], 34)],
      [cowCut + .001, C([-8.2, 1.5, 9.0], [-10.5, 1.1, 4.8], 40), "io", true],
      [An.t1, C([-9.6, 1.3, 8.4], [-10.6, 1.1, 4.8], 38)],
      // everyone: crane up and away to reveal the whole money town
      [Ev.t0, C([2.8, 1.4, 5.4], [1.0, 1.6, .6], 44), "io", true],
      [Ev.t1 - .3, C([16, 20, 30], [0, 0, -10], 46), "io"],
      [Ev.t1, C([16.3, 20.2, 30.2], [0, 0, -10], 46)],
      // price: the queue, push to the sign, whip to the kid's face
      [Pr.t0, C([4.6, 2.6, 11.5], [8.6, 1.4, 2.0], 44), "io", true],
      [flip - .5, C([9.5, 2.0, 6.4], [10.75, 1.7, 2.4], 34), "io"],
      [flip + .5, C([9.8, 1.9, 5.6], [10.85, 1.7, 2.4], 32)],
      [flip + .52, C([9.1, 1.25, 4.9], [9.0, 1.05, 3.0], 38), "io", true],
      [Pr.t1, C([9.05, 1.2, 4.6], [9.0, 1.05, 3.0], 36)],
      // insight: a quiet push-in under the apple tree
      [In.t0, C([6.2, 1.3, 4.6], [4.6, .75, -.35], 40), "io", true],
      [In.t1, C([5.3, .95, 2.4], [4.6, .8, -.35], 38), "lin"],
      // apple: bonk, catch, bite
      [Ap.t0, C([5.5, 1.15, 2.6], [4.6, 1.0, -.35], 40), "io", true],
      [Ap.t1, C([5.2, 1.0, 2.0], [4.6, .8, -.35], 38), "lin"],
      // ask: look into the lens, push in and hold
      [As.t0, C([4.62, 1.0, 3.0], [4.6, .85, -.3], 38), "io", true],
      [As.v0 + 1.6, C([4.62, .98, 2.15], [4.6, .85, -.3], 36), "io"],
      [T.dur, C([4.62, .98, 2.05], [4.6, .85, -.3], 36), "lin"],
    ];
    function cam(t) {
      const c = camTrack(t, shots), d = drift(t, .02);
      c.pos = c.pos.map((v, i) => v + d[i]);
      // aim the shadow map at what matters in each shot
      c.shadowSize = t >= Ev.t0 && t < Pr.t0 ? 34 : 9;
      if (t >= Ev.t0 && t < Pr.t0) c.shadowAt = [0, 0, -10];
      return c;
    }

    ctx.setMusic?.(music);
    return { update, cam, music };
  },
};
