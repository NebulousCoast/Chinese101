"""Sets: ground, town, props. Each set is one collection, shared by every beat that uses it.

A set returns a dict:
  col        the collection
  ground_z   f(x, y) -> ground height, for placing characters
  ambient    list of f(t, w) updaters for set-level motion on the world clock (rain, swings, ...)
"""
import math
import random

import bpy

import characters as ch
import geo
from geo import box, cone, ico, plane, poly, roof

RAD = math.radians


def new_collection(name, parent=None):
    col = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(col)
    return col


# ---------------------------------------------------------------- shared props
def rain(name, col, rec, center, size, top=14.0, count=260, speed=9.0, seed=1):
    """Three stacked identical tiles that scroll down; the wrap is seamless."""
    rng = random.Random(seed)
    h = top / 2.0
    verts, faces = [], []
    drops = [(rng.uniform(-size[0] / 2, size[0] / 2), rng.uniform(-size[1] / 2, size[1] / 2), rng.uniform(0, h))
             for _ in range(count)]
    for tile in range(3):
        for x, y, z in drops:
            z += tile * h
            b = len(verts)
            s, L = 0.012, 0.32
            verts += [(x - s, y, z), (x + s, y, z), (x + s, y, z + L), (x - s, y, z + L),
                      (x, y - s, z), (x, y + s, z), (x, y + s, z + L), (x, y - s, z + L)]
            faces += [(b, b + 1, b + 2, b + 3), (b + 4, b + 5, b + 6, b + 7)]
    ob = poly(name, col, "rain", verts, faces, (center[0], center[1], -h))
    rec.add(ob, "location")

    def upd(t, w):
        ob.location = (center[0], center[1], -((w * speed) % h) - 0.0)
    return ob, upd


def tree(name, col, loc, rng, scale=1.0, foliage="ground"):
    s = scale * rng.uniform(0.8, 1.25)
    box(f"{name}.trunk", col, "dark", (0.22 * s, 0.22 * s, 0.9 * s), loc, origin="bottom")
    cone(f"{name}.crown", col, foliage, 0.9 * s, 0.0, 2.2 * s, (loc[0], loc[1], loc[2] + 0.7 * s), seg=6)
    cone(f"{name}.crown2", col, foliage, 0.7 * s, 0.0, 1.6 * s, (loc[0], loc[1], loc[2] + 1.7 * s), seg=6)


def house(name, col, loc, rng, w=None, d=None, h=None, facing=-1, rot=0.0, windows=True):
    w = w or rng.uniform(2.6, 4.4)
    d = d or rng.uniform(2.6, 3.8)
    h = h or rng.uniform(2.2, 4.4)
    root = geo.empty(name, col, loc)
    root.rotation_euler = (0, 0, rot)
    box(f"{name}.body", col, "stone", (w, d, h), (0, 0, 0), origin="bottom", parent=root)
    roof(f"{name}.roof", col, "dark", w + 0.3, d + 0.3, rng.uniform(0.9, 1.6), (0, 0, h), parent=root)
    if windows:
        floors = max(1, int(h // 1.6))
        cols = max(1, int(w // 1.3))
        for fy in range(floors):
            for cx in range(cols):
                if rng.random() < 0.65:
                    x = -w / 2 + (cx + 0.5) * w / cols
                    z = 0.9 + fy * 1.5
                    box(f"{name}.win{fy}{cx}", col, "glow" if rng.random() < 0.7 else "dark",
                        (0.42, 0.06, 0.55), (x, facing * d / 2, z), parent=root)
        box(f"{name}.door", col, "dark", (0.6, 0.06, 1.1), (rng.uniform(-w / 4, w / 4), facing * d / 2, 0),
            origin="bottom", parent=root)
    return root


def lamp(name, col, loc):
    box(f"{name}.post", col, "dark", (0.08, 0.08, 2.6), loc, origin="bottom")
    box(f"{name}.head", col, "glow", (0.26, 0.26, 0.26), (loc[0], loc[1], loc[2] + 2.7))


def ground_plane(col, material="ground", size=400):
    return plane("ground", col, material, size, size, (0, 0, -0.01))


# ---------------------------------------------------------------- hill (beats 1, 2, 8)
def hill_height(x, y):
    return 3.0 * math.exp(-(x * x + y * y) / (2 * 6.5 ** 2))


def build_hill(rec):
    col = new_collection("Set_Hill")
    rng = random.Random(42)
    ground_plane(col)

    def hfn(x, y):
        r = math.hypot(x, y)
        n = 0.0 if r < 3.0 else rng.uniform(-0.12, 0.12)
        return hill_height(x, y) + n
    geo.grid_terrain("hill", col, "ground", 44, 1.6, hfn, rng)
    # Rocks and grass tufts on the hill.
    for i in range(14):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(3.5, 14)
        x, y = r * math.cos(a), r * math.sin(a)
        ico(f"rock{i}", col, "stone", rng.uniform(0.15, 0.4), (x, y, hill_height(x, y)), subdiv=0)
    # Town below, toward +Y.
    k = 0
    for gx in range(-5, 6):
        for gy in range(3, 11):
            if rng.random() < 0.62:
                x = gx * 6.5 + rng.uniform(-1, 1)
                y = gy * 6.5 + rng.uniform(-1, 1)
                house(f"h{k}", col, (x, y, 0), rng)
                k += 1
            elif rng.random() < 0.5:
                tree(f"ht{k}", col, (gx * 6.5 + rng.uniform(-2, 2), gy * 6.5, 0), rng)
                k += 1
    for i in range(10):
        lamp(f"hl{i}", col, (-30 + i * 6.5, 17.0, 0))
    for i in range(12):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(9, 16)
        x, y = r * math.cos(a), r * math.sin(a)
        if y < 6:
            tree(f"hillt{i}", col, (x, y, hill_height(x, y) - 0.1), rng, 0.9)

    _, rain_upd = rain("Hill.rain", col, rec, (0, 4), (26, 26), top=16.0, count=420, seed=7)
    kite = ch.Kite("Hill.kite", col, rec, anchor=(-18, 38, 0))
    birds = [ch.Bird(f"Hill.bird{i}", col, rec) for i in range(2)]

    def ambient(t, w):
        kite.pose((-5 + 0.6 * math.sin(0.5 * w), 12 + 0.4 * math.sin(0.37 * w), 9.5 + 0.5 * math.sin(0.8 * w)), w)
        for i, b in enumerate(birds):
            # Passes across the frame; at w=3.0 (the first freeze) bird 0 is near the kite.
            x = -15 + ((3.2 * (w - 3.0) + 13 + i * 11) % 30)
            y = 7 + 2.5 * i
            z = 6.5 + 0.4 * math.sin(w * 1.7 + i) + i * 0.8
            b.pose((x, y, z), ch.RAD(-90), w * 14 + i)
    return dict(col=col, ground_z=hill_height, ambient=[rain_upd, ambient])


# ---------------------------------------------------------------- street (beat 3)
def build_street(rec):
    col = new_collection("Set_Street")
    rng = random.Random(43)
    ground_plane(col)
    box("road", col, "dark", (60, 5.0, 0.02), (0, -4.0, 0), origin="bottom")
    for i in range(-6, 7):
        box(f"stripe{i}", col, "light", (1.2, 0.12, 0.03), (i * 3.0, -4.0, 0), origin="bottom")
    box("sidewalk", col, "stone", (60, 6.1, 0.03), (0, 1.55, 0), origin="bottom")
    # Bakery front: wall with a window opening, awning, outside shelf with the cookie jar.
    bx, by = 0.0, 5.2
    box("bak.wall_l", col, "light", (1.6, 1.2, 3.6), (bx - 1.9, by, 0), origin="bottom")
    box("bak.wall_r", col, "light", (1.6, 1.2, 3.6), (bx + 1.9, by, 0), origin="bottom")
    box("bak.wall_b", col, "light", (2.2, 1.2, 0.8), (bx, by, 0), origin="bottom")
    box("bak.wall_t", col, "light", (2.2, 1.2, 1.2), (bx, by, 2.4), origin="bottom")
    box("bak.back", col, "warm", (5.4, 0.2, 3.6), (bx, by + 1.6, 0), origin="bottom")
    box("bak.inside_floor", col, "stone", (5.4, 2.4, 0.02), (bx, by + 0.6, 0), origin="bottom")
    box("bak.lamp", col, "glow", (0.5, 0.5, 0.2), (bx, by + 1.0, 2.9))
    roof("bak.roof", col, "dark", 5.8, 3.4, 1.2, (bx, by + 0.4, 3.6))
    for i in range(6):
        box(f"bak.awning{i}", col, "warm" if i % 2 == 0 else "light", (0.6, 1.1, 0.06),
            (bx - 1.5 + i * 0.6, by - 1.05, 2.55)).rotation_euler = (RAD(-18), 0, 0)
    box("bak.counter", col, "warm", (2.0, 0.5, 1.0), (bx, by + 0.3, 0), origin="bottom")
    box("shelf", col, "warm", (1.8, 0.46, 0.07), (bx, 4.3, 0.95))
    for sx in (-1, 1):
        box(f"shelf.leg{sx}", col, "dark", (0.06, 0.06, 0.95), (bx + 0.8 * sx, 4.3, 0), origin="bottom")
    geo.cone("jar", col, "light", 0.15, 0.15, 0.28, (bx + 0.3, 4.3, 0.985), seg=8)
    geo.cone("jar.rim", col, "stone", 0.12, 0.12, 0.03, (bx + 0.3, 4.3, 1.26), seg=8)
    for i, (dx, dz) in enumerate([(-0.04, 1.24), (0.05, 1.22)]):
        geo.cone(f"jar.cookie{i}", col, "warm", 0.07, 0.07, 0.025, (bx + 0.3 + dx, 4.3, dz), seg=7).rotation_euler = (RAD(70), 0, 0)
    box("bread1", col, "warm", (0.35, 0.2, 0.15), (bx - 0.5, 4.3, 0.99), origin="bottom")
    box("bread2", col, "light", (0.3, 0.2, 0.12), (bx - 0.15, 4.3, 0.99), origin="bottom")
    # Neighbours.
    for i, x in enumerate([-11, -7, 6.5, 10.5, 14.5, -15]):
        house(f"st{i}", col, (x, 6.4, 0), rng, w=3.6, d=3.2, h=rng.uniform(3.0, 5.0))
    for i, x in enumerate([-9.0, 4.5, 12.0]):
        lamp(f"sl{i}", col, (x, -1.4, 0))
    for i, x in enumerate([-18, 18, -9, 9]):
        tree(f"stt{i}", col, (x, -8.5, 0), rng)
    _, rain_upd = rain("Street.rain", col, rec, (0, 0.5), (26, 18), top=14.0, count=380, seed=8)
    return dict(col=col, ground_z=lambda x, y: 0.0, ambient=[rain_upd])


# ---------------------------------------------------------------- classroom (beat 4)
def build_classroom(rec):
    col = new_collection("Set_Classroom")
    rng = random.Random(44)
    box("floor", col, "stone", (13, 13, 0.1), (0, 0, -0.1), origin="bottom")
    box("wall_back", col, "light", (13, 0.3, 4.0), (0, 6.15, 0), origin="bottom")
    box("wall_left", col, "light", (0.3, 13, 4.0), (-6.5, 0, 0), origin="bottom")
    box("wall_right", col, "light", (0.3, 13, 4.0), (6.5, 0, 0), origin="bottom")
    box("ceiling", col, "light", (13, 13, 0.1), (0, 0, 4.0), origin="bottom")
    for i in range(3):
        box(f"ceiling.lamp{i}", col, "glow", (2.4, 0.3, 0.05), (0, -2 + i * 3.2, 3.97))
    box("board", col, "dark", (6.4, 0.06, 1.6), (0, 5.97, 1.0), origin="bottom")
    box("board.ledge", col, "stone", (6.4, 0.16, 0.05), (0, 5.92, 0.98))
    for i in range(7):  # chalk writing
        box(f"chalk{i}", col, "light", (rng.uniform(0.4, 1.5), 0.02, 0.05),
            (-2.4 + rng.uniform(0, 3.0), 5.93, 2.3 - i * 0.18))
    box("eq", col, "light", (0.7, 0.02, 0.05), (1.9, 5.93, 1.95))
    for i in range(3):
        box(f"window{i}", col, "sky", (0.05, 1.6, 1.4), (-6.33, -3.5 + i * 3.4, 1.2), origin="bottom")
        box(f"window{i}.frame", col, "dark", (0.06, 0.06, 1.4), (-6.31, -3.5 + i * 3.4, 1.2), origin="bottom")
    # Wall clock: the second hand runs on the world clock, so it stops during the freeze.
    geo.cone("clock", col, "light", 0.32, 0.32, 0.05, (4.6, 5.98, 2.9), seg=12, origin="center").rotation_euler = (RAD(90), 0, 0)
    hand = box("clock.hand", col, "dark", (0.03, 0.02, 0.26), (4.6, 5.93, 2.9), origin="bottom")
    rec.add(hand, "rotation_euler")
    box("clock.hand2", col, "dark", (0.04, 0.02, 0.18), (4.6, 5.935, 2.9), origin="bottom").rotation_euler = (0, RAD(-60), 0)
    # Teacher's desk with the answer sheet.
    box("tdesk", col, "warm", (1.6, 0.8, 0.08), (-4.3, 4.5, 0.78))
    box("tdesk.front", col, "warm", (1.6, 0.05, 0.7), (-4.3, 4.12, 0.05), origin="bottom")
    plane("answers", col, "light", 0.32, 0.42, (-4.2, 4.4, 0.83))
    for i in range(4):
        box(f"answers.line{i}", col, "dark", (0.22, 0.03, 0.005), (-4.2, 4.55 - i * 0.08, 0.835))
    desks = []
    for gy in (0.0, 1.6, 3.2):
        for gx in (-2.4, 0.0, 2.4):
            box(f"desk{gx}{gy}", col, "warm", (1.0, 0.6, 0.06), (gx, gy, 0.72))
            for sx in (-1, 1):
                box(f"desk{gx}{gy}.leg{sx}", col, "dark", (0.05, 0.05, 0.69), (gx + 0.45 * sx, gy, 0), origin="bottom")
            box(f"chair{gx}{gy}", col, "dark", (0.42, 0.42, 0.05), (gx, gy - 0.6, 0.44))
            box(f"chair{gx}{gy}.back", col, "dark", (0.42, 0.05, 0.45), (gx, gy - 0.82, 0.44), origin="bottom")
            plane(f"desk{gx}{gy}.paper", col, "light", 0.3, 0.38, (gx + 0.1, gy, 0.755))
            desks.append((gx, gy))

    def ambient(t, w):
        hand.rotation_euler = (0, RAD(w * 6.0), 0)
    return dict(col=col, ground_z=lambda x, y: 0.0, ambient=[ambient], desks=desks)


# ---------------------------------------------------------------- pond (beat 5)
def build_pond(rec):
    col = new_collection("Set_Pond")
    rng = random.Random(45)
    ground_plane(col)
    n = 14
    pts = [(5.0 * math.cos(2 * math.pi * i / n) * rng.uniform(0.9, 1.08),
            6.0 + 4.2 * math.sin(2 * math.pi * i / n) * rng.uniform(0.9, 1.08), 0.03) for i in range(n)]
    poly("pond", col, "water", [(0, 6, 0.03)] + pts, [(0, i + 1, (i + 1) % n + 1) for i in range(n)])
    for i, (x, y, _) in enumerate(pts):
        ico(f"shore{i}", col, "stone", rng.uniform(0.18, 0.35), (x, y, 0.05), subdiv=0)
    for i in range(16):
        a = rng.uniform(0.3, 2.6)
        x, y = 5.3 * math.cos(a) + rng.uniform(-0.4, 0.4), 6 + 4.4 * math.sin(a)
        cone(f"reed{i}", col, "ground", 0.05, 0.0, rng.uniform(0.6, 1.2), (x, y, 0), seg=4)
    for i in range(5):
        geo.cone(f"pad{i}", col, "ground", 0.35, 0.35, 0.02, (rng.uniform(-3, 3), rng.uniform(4.5, 8.5), 0.04), seg=7)
    for i in range(14):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(11, 22)
        tree(f"pt{i}", col, (r * math.cos(a), 6 + r * math.sin(a), 0), rng)
    box("bench", col, "warm", (1.6, 0.45, 0.08), (-5.5, -2.5, 0.45))
    for sx in (-1, 1):
        box(f"bench.leg{sx}", col, "dark", (0.08, 0.4, 0.45), (-5.5 + 0.7 * sx, -2.5, 0), origin="bottom")
    return dict(col=col, ground_z=lambda x, y: 0.0, ambient=[])


# ---------------------------------------------------------------- playground (beat 6)
def build_playground(rec):
    col = new_collection("Set_Playground")
    rng = random.Random(46)
    ground_plane(col)
    box("pg.mat", col, "stone", (16, 12, 0.02), (0, 2, 0), origin="bottom")
    # Swings.
    for sx in (-1, 1):
        for dy in (-0.7, 0.7):
            b = box(f"sw.frame{sx}{dy}", col, "dark", (0.1, 0.1, 2.8), (4.0 + 1.6 * sx, 4.0 + dy, 0), origin="bottom")
            b.rotation_euler = (RAD(14 * (1 if dy > 0 else -1)), 0, 0)
    box("sw.bar", col, "dark", (3.4, 0.12, 0.12), (4.0, 4.0, 2.72))
    sw = [ch.swing(f"swing{i}", col, rec, (3.4 + 1.2 * i, 4.0, 2.66), seat_color=("warm", "sky")[i]) for i in range(2)]
    # Slide.
    box("slide.tower", col, "warm", (1.2, 1.2, 1.6), (-4.5, 4.5, 0), origin="bottom")
    box("slide.roof", col, "sky", (1.4, 1.4, 0.1), (-4.5, 4.5, 2.6))
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"slide.post{sx}{sy}", col, "dark", (0.08, 0.08, 1.0), (-4.5 + 0.6 * sx, 4.5 + 0.6 * sy, 1.6), origin="bottom")
    s = box("slide.chute", col, "light", (0.8, 3.0, 0.08), (-4.5, 2.6, 0.85))
    s.rotation_euler = (RAD(-30), 0, 0)
    for i in range(4):
        box(f"slide.step{i}", col, "dark", (0.6, 0.12, 0.06), (-4.5, 5.2, 0.35 + i * 0.4))
    # Sandbox.
    box("sand", col, "light", (2.6, 2.0, 0.12), (-4.0, -2.5, 0), origin="bottom")
    for i, (dx, dy, w, d) in enumerate([(0, -1.0, 2.8, 0.15), (0, 1.0, 2.8, 0.15), (-1.35, 0, 0.15, 2.0), (1.35, 0, 0.15, 2.0)]):
        box(f"sand.edge{i}", col, "warm", (w, d, 0.25), (-4.0 + dx, -2.5 + dy, 0), origin="bottom")
    ico("bucket", col, "sky", 0.14, (-3.6, -2.3, 0.2), subdiv=0)
    # Fence.
    for i in range(-10, 11):
        box(f"fence{i}", col, "light", (0.1, 0.1, 0.9), (i * 1.0, 8.5, 0), origin="bottom")
    box("fence.rail", col, "light", (21, 0.06, 0.08), (0, 8.5, 0.75))
    for i in range(10):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(12, 22)
        tree(f"pgt{i}", col, (r * math.cos(a), 2 + r * math.sin(a), 0), rng)
    house("pg.house1", col, (-12, 16, 0), rng, w=5, d=4, h=4)
    house("pg.house2", col, (12, 16, 0), rng, w=4.5, d=4, h=3.5)

    def ambient(t, w):
        for i, p in enumerate(sw):
            p.rotation_euler = (RAD(32 * math.sin(w * 2.1 + i * 1.9)), 0, 0)
    return dict(col=col, ground_z=lambda x, y: 0.0, ambient=[ambient])


# ---------------------------------------------------------------- town square (beat 7)
def build_town(rec):
    col = new_collection("Set_Town")
    rng = random.Random(47)
    ground_plane(col)
    n = 16
    poly("plaza", col, "stone", [(0, 0, 0.01)] + [(11 * math.cos(2 * math.pi * i / n), 11 * math.sin(2 * math.pi * i / n), 0.01) for i in range(n)],
         [(0, i + 1, (i + 1) % n + 1) for i in range(n)])
    # Fountain with water jets (they freeze with everything else).
    geo.cone("fountain.base", col, "light", 1.8, 1.8, 0.45, (0, 6, 0), seg=10)
    geo.cone("fountain.pool", col, "water", 1.6, 1.6, 0.05, (0, 6, 0.42), seg=10)
    geo.cone("fountain.col", col, "light", 0.25, 0.2, 1.3, (0, 6, 0.45), seg=6)
    jets = []
    for i in range(6):
        j = ico(f"fountain.drop{i}", col, "water", 0.09, (0, 6, 1.8), subdiv=0)
        rec.add(j, "location")
        jets.append(j)
    # Ring of houses facing the plaza.
    k = 0
    for ring, r in enumerate([15.0, 22.0, 30.0]):
        m = 10 + ring * 5
        for i in range(m):
            a = 2 * math.pi * i / m + ring * 0.3
            if rng.random() < 0.85:
                x, y = r * math.cos(a), r * math.sin(a)
                house(f"tw{k}", col, (x, y, 0), rng, rot=a - math.pi / 2, h=rng.uniform(2.8, 5.2), facing=-1)
                k += 1
    for i in range(10):
        a = 2 * math.pi * i / 10
        lamp(f"twl{i}", col, (10.5 * math.cos(a), 10.5 * math.sin(a), 0))
    for i in range(8):
        a = 2 * math.pi * i / 8 + 0.2
        tree(f"twt{i}", col, (12.5 * math.cos(a), 12.5 * math.sin(a), 0), rng)
    _, rain_upd = rain("Town.rain", col, rec, (0, 0), (30, 30), top=16.0, count=520, seed=9)

    def ambient(t, w):
        for i, j in enumerate(jets):
            ph = (w * 0.9 + i / 6) % 1.0
            a = 2 * math.pi * i / 6
            j.location = (0.9 * ph * math.cos(a), 6 + 0.9 * ph * math.sin(a), 1.8 + 1.6 * ph - 3.2 * ph * ph)
    return dict(col=col, ground_z=lambda x, y: 0.0, ambient=[rain_upd, ambient])


SETS = {
    "hill": build_hill,
    "street": build_street,
    "classroom": build_classroom,
    "pond": build_pond,
    "playground": build_playground,
    "town": build_town,
}
