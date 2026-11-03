"""Blender headless scene builder and renderer.

  blender -b --factory-startup -P scenes/build_scene.py -- --beat 3 --out build/preview/frames/beat_3/ --mode preview

One .blend: each beat is a collection (Beat_01 ... Beat_08) holding its actors, lights and
camera; the sets (Set_Hill, Set_Street, ...) are child collections shared by the beats that use them.

Clocks: the kid always runs on real time t. Everything else runs on the world clock, which stops
inside freeze and hold windows from timeline.json. Motion is baked to keyframes (one per frame).
"""
import argparse
import math
import os
import random
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "config"))

import timeline_lib as tl_lib  # noqa: E402
import geo  # noqa: E402
import characters as ch  # noqa: E402
import environment as env  # noqa: E402
import camera as camlib  # noqa: E402
from characters import Human, RAD  # noqa: E402
from geo import Path, ramp, lerp, heading_to, angle_lerp  # noqa: E402

random.seed(42)


# ======================================================================= helpers
def snap_arm(t, ts):
    """Right-arm finger-snap gesture peaking at ts. Returns (forward, out) degrees."""
    up = ramp(t, ts - 0.4, ts - 0.08)
    down = ramp(t, ts + 0.25, ts + 0.7)
    k = up * (1 - down)
    return (105 * k, 22 * k)


def locomote(h, path, t, gz, run=False, stride=None, turn=0.3, face=None, **over):
    x, y = path.at(t)
    vx, vy = path.velocity(t)
    sp = math.hypot(vx, vy)
    target = face if face is not None else (heading_to(vx, vy) if sp > 0.05 else h.heading)
    hd = angle_lerp(h.heading, target, turn)
    stride = stride or (1.15 if run else 0.7) * h.scale
    phase = path.dist(t) / stride * math.pi
    amp = geo.clamp(sp / (2.6 if run else 1.0))
    p = Human.walk(phase, amp, run)
    p.update(over)
    h.pose((x, y, gz(x, y)), hd, **p)


class Ctx:
    def __init__(self, tl, rec, beat, col, set_d):
        self.tl, self.rec, self.beat, self.col, self.set = tl, rec, beat, col, set_d
        self.b0 = beat["start"]
        self.off = self.b0 - tl.world(self.b0)

    def wt(self, t):
        """World clock expressed in real seconds: equals t until this beat's first stop, then lags."""
        return self.tl.world(t) + self.off


# ======================================================================= beats
def beat_hook(c):
    """Beat 1: kid on the hill, rain falling, slow push-in."""
    kid = Human("Kid_b1", c.col, c.rec)
    gz = c.set["ground_z"]

    def upd(t, w):
        kid.pose((0, 0, gz(0, 0)), 0.0, head=(-8, 6 * math.sin(t * 0.8)), **Human.idle(t))
    return [upd]


def beat_first_freeze(c):
    kid = Human("Kid_b2", c.col, c.rec)
    gz = c.set["ground_z"]

    def upd(t, w):
        p = Human.idle(t)
        p["arm_r"] = snap_arm(t, 3.0)
        look = 0.0
        if 3.3 < t < 5.0:  # looks around at the frozen world
            look = 45 * math.sin((t - 3.3) / 1.7 * math.pi * 1.5)
        pitch = -8 - 12 * ramp(t, 5.2, 6.0)
        kid.pose((0, 0, gz(0, 0)), RAD(10 * ramp(t, 3.4, 4.2)), head=(pitch, look), **p)
    return [upd]


def beat_cookies(c):
    gz = c.set["ground_z"]
    kid = Human("Kid_b3", c.col, c.rec)
    kid.heading = heading_to(1, 1)
    path = Path([(8.0, -4.5, 0.5), (9.05, -4.5, 0.5), (10.9, -0.2, 3.62), (12.3, -0.2, 3.62), (14.7, 0.9, 1.0)])
    cookie = geo.cone("cookie", c.col, "warm", 0.075, 0.075, 0.026, (0.26, 4.3, 1.27), seg=7)
    c.rec.add(cookie, "location", "rotation_euler")
    keeper = Human("Shopkeeper", c.col, c.rec, scale=1.3, shirt="stone", pants="dark", hair="dark")
    walker = Human("Walker", c.col, c.rec, scale=1.3, shirt="sky", pants="dark", hair="dark", hair_style="long")
    umb = geo.empty("Walker.umbrella", c.col, (0.18, 0.15, 1.12), parent=walker.root)
    geo.cone("Walker.umbrella.top", c.col, "warm", 0.62, 0.0, 0.3, (0, 0, 0.62), seg=8, parent=umb)
    geo.box("Walker.umbrella.stick", c.col, "dark", (0.03, 0.03, 0.66), (0, 0, 0), origin="bottom", parent=umb)
    wpath_y = 2.5

    def upd(t, w):
        wt = c.wt(t)
        over = {}
        if t < 9.05:
            over["arm_r"] = snap_arm(t, 8.95)
        reach = ramp(t, 10.9, 11.25) * (1 - ramp(t, 11.5, 11.9))
        to_mouth = max(ramp(t, 12.4, 12.7) * (1 - ramp(t, 13.1, 13.4)), ramp(t, 13.9, 14.2) * (1 - ramp(t, 14.6, 14.9)))
        if t >= 9.05:
            over["arm_r"] = (75 * reach + 125 * to_mouth + 20 * ramp(t, 11.5, 11.9) * (1 - to_mouth), 8)
        face = 0.0 if 10.8 < t < 12.3 else None
        locomote(kid, path, t, gz, face=face, turn=0.25, **over)
        if t < 11.25:
            cookie.location = (0.26, 4.3, 1.27)
            cookie.rotation_euler = (RAD(70), 0, 0)
        else:
            hp = kid.hand_world("r")
            cookie.location = (hp.x, hp.y, hp.z - 0.02)
            cookie.rotation_euler = (RAD(70), 0, kid.heading)
        # Shopkeeper wipes the counter (world clock).
        keeper.pose((0.5, 5.65, 0), math.pi, arm_r=(70, 10 + 18 * math.sin(wt * 5.0)), arm_l=(20, 5),
                    head=(15, 0), lean=8)
        # Walker with umbrella crosses the street (world clock).
        x = 6.0 - 1.1 * (wt - 8.0)
        p = Human.walk((6.0 - x) / 0.9 * math.pi, 1.0)
        p["arm_r"] = (65, 10)
        walker.pose((x, wpath_y, 0), heading_to(-1, 0), **p)
    return [upd]


def beat_test(c):
    gz = c.set["ground_z"]
    tl = c.tl
    fs, fe = tl.freeze_in_beat(4)
    teacher = Human("Teacher", c.col, c.rec, scale=1.35, shirt="stone", pants="dark", hair="dark", hair_style="long")
    marker = geo.box("marker", c.col, "warm", (0.04, 0.04, 0.17), (0, 0, 0))
    c.rec.add(marker, "location", "rotation_euler")
    students = []
    for i, (gx, gy) in enumerate(c.set["desks"]):
        if (gx, gy) == (-2.4, 1.6):
            continue
        s = Human(f"Student{i}", c.col, c.rec, scale=1.0, shirt=("sky", "stone", "warm", "light")[i % 4],
                  pants="dark", hair="dark", hair_style=("short", "long")[i % 2])
        students.append((s, gx, gy, i))
    kid = Human("Kid_b4", c.col, c.rec)
    kid.heading = 0.0
    seat = (-2.4, 1.0)
    path = Path([(16.35, -2.4, 1.0), (16.75, -3.6, 1.2), (17.35, -4.0, 3.2), (17.55, -4.0, 3.72),
                 (18.55, -4.0, 3.72), (18.75, -4.0, 3.2), (19.35, -3.6, 1.2), (19.7, -2.4, 1.0)])

    def seated(h, x, y, **kw):
        h.pose((x, y, -0.16), kw.pop("heading", 0.0), leg_l=88, leg_r=88, **kw)

    toss_period, toss_len = 3.0, 0.8

    def upd(t, w):
        wt = c.wt(t)
        # Teacher: writes, then tosses the marker. At the freeze the marker is at the top of a toss.
        ph = (wt - fs + 0.4) % toss_period
        if ph < toss_len:
            teacher.pose((1.6, 5.45, 0), 0.0, arm_r=(70, 12), arm_l=(10, 6), head=(-12, -20), twist=-10)
            hp = teacher.hand_world("r")
            k = ph / toss_len
            marker.location = (hp.x, hp.y, hp.z + 0.05 + 2.8 * k * (1 - k))
            marker.rotation_euler = (RAD(720 * k), RAD(30), 0)
        else:
            teacher.pose((1.6, 5.45, 0), 0.0, arm_r=(140 + 7 * math.sin(wt * 9), 10 + 9 * math.sin(wt * 4.3)),
                         arm_l=(10, 6), head=(-10, 0))
            hp = teacher.hand_world("r")
            marker.location = (hp.x, hp.y + 0.05, hp.z + 0.05)
            marker.rotation_euler = (RAD(-60), 0, 0)
        for s, gx, gy, i in students:
            seated(s, gx, gy - 0.6, arm_l=(62, 4), arm_r=(62 + 6 * math.sin(wt * 6 + i), 4),
                   head=(18 + 6 * math.sin(wt * 1.3 + i), 4 * math.sin(wt * 0.7 + i)))
        # Kid: snap at 15.95 while seated, sneak to the teacher's desk, copy, sneak back.
        if t < 16.1:
            seated(kid, *seat, arm_r=snap_arm(t, 15.95), arm_l=(60, 4), head=(10, 0))
        elif t < 16.35:
            k = ramp(t, 16.1, 16.35)
            kid.pose((seat[0], seat[1], lerp(-0.16, 0, k)), 0.0, leg_l=88 * (1 - k), leg_r=88 * (1 - k),
                     head=(5, 25 * k))
        elif t < 19.7:
            copying = ramp(t, 17.6, 17.8) * (1 - ramp(t, 18.35, 18.5))
            over = dict(head=(35 * copying, 0), lean=18 * copying)
            if copying > 0.01:
                over["arm_r"] = (55 * copying, 6)
                over["arm_l"] = (45 * copying, 4)
            locomote(kid, path, t, gz, run=True, face=0.0 if 17.5 < t < 18.6 else None, turn=0.35, **over)
        else:
            k = ramp(t, 19.7, 19.98)
            kid.heading = angle_lerp(kid.heading, 0.0, 0.5)
            wr = 6 * math.sin(t * 7) if t > 20.2 else 0
            kid.pose((seat[0], seat[1], lerp(0, -0.16, k)), kid.heading, leg_l=88 * k, leg_r=88 * k,
                     arm_l=(60 * k, 4), arm_r=(60 * k + wr, 4), head=(20 * k, 0))
    return [upd]


def beat_animals(c):
    gz = c.set["ground_z"]
    kid = Human("Kid_b5", c.col, c.rec)
    kid.heading = 0.2
    dog = ch.Dog("Dog", c.col, c.rec)
    ball = geo.ico("ball", c.col, "light", 0.12, (0, 0, 0), subdiv=1)
    c.rec.add(ball, "location")
    birds = [ch.Bird(f"PondBird{i}", c.col, c.rec) for i in range(2)]
    kpath = Path([(22.0, -3.0, -0.5), (25.3, -3.0, -0.5), (28.8, -9.5, -4.0)])
    dpath = Path([(22.0, -1.8, 0.0), (22.9, -1.8, 0.0), (23.5, -1.0, 1.9)])
    p_rel, p_land, t_rel, t_land = None, (1.0, 7.2, 0.05), 22.75, 24.9

    def upd(t, w):
        nonlocal p_rel
        wt = c.wt(t)
        # Kid: throw, snap, watch, then forget and walk away.
        over = {}
        wind = ramp(t, 22.3, 22.55) * (1 - ramp(t, 22.55, 22.75))
        fling = ramp(t, 22.55, 22.75) * (1 - ramp(t, 23.0, 23.4))
        over["arm_r"] = (-55 * wind + 130 * fling, 8)
        if t > 23.4:
            over["arm_r"] = snap_arm(t, 23.9)
        if t > 24.2:
            over["head"] = (-10, 0) if t < 25.0 else (5, 0)
        locomote(kid, kpath, t, gz, face=0.2 if t < 25.2 else None, turn=0.2, **over)
        if p_rel is None and t >= t_rel - 1e-6:
            hp = kid.hand_world("r")
            p_rel = (hp.x, hp.y, hp.z)
        # Ball on the world clock.
        if wt < t_rel or p_rel is None:
            hp = kid.hand_world("r")
            ball.location = (hp.x, hp.y, hp.z)
        else:
            k = geo.clamp((wt - t_rel) / (t_land - t_rel))
            x, y, z = geo.lerp3(p_rel, p_land, k)
            ball.location = (x, y, z + 3.2 * 4 * k * (1 - k))
        # Dog: idle, run, leap (peak exactly at the freeze), splash into the pond.
        if wt < 23.5:
            vx, vy = dpath.velocity(wt)
            run = math.hypot(vx, vy) > 0.1
            x, y = dpath.at(wt)
            dog.pose((x, y, 0), heading_to(0.8, 1.9) if run else 0.0, gait=wt * 16, amp=1.0 if run else 0.0,
                     tail=30 * math.sin(wt * 12))
        elif wt < 24.5:
            k = (wt - 23.5) / 1.0
            x, y = lerp(-1.0, 0.6, k), lerp(1.9, 5.0, k)
            dog.pose((x, y, 0), heading_to(1.6, 3.1), pitch=lerp(25, -25, k), stretch=1.0,
                     height=1.3 * 4 * k * (1 - k), tail=10)
        else:
            k = geo.clamp((wt - 24.5) / 0.4)
            dog.pose((0.6 + 0.3 * (wt - 24.5), 5.0 + 0.4 * (wt - 24.5), 0), heading_to(1.6, 3.1),
                     pitch=-25 * (1 - k), height=-0.38 * k, gait=wt * 10, amp=0.8, tail=0)
        for i, b in enumerate(birds):
            a = wt * (0.9 if i == 0 else -0.7) + i * 2.0
            r, z = (3.2, 4.2) if i == 0 else (4.0, 5.4)
            b.pose((r * math.cos(a), 6.5 + r * math.sin(a), z), a + (0 if i == 0 else math.pi), wt * 15 + i, bank=-20 if i == 0 else 20)
    return [upd]


def beat_friend(c):
    gz = c.set["ground_z"]
    kid = Human("Kid_b6", c.col, c.rec)
    bully = Human("Bully", c.col, c.rec, scale=1.2, shirt="dark", pants="stone", hair="dark")
    friend = Human("Friend", c.col, c.rec, scale=0.97, shirt="sky", pants="dark", hair="warm",
                   hair_style="long", mouth_open=True)
    kid.heading = 0.0
    kpath = Path([(30.0, 0.0, 0.0), (31.45, 0.0, 0.0), (31.9, 0.0, -0.45), (33.4, 0.0, -0.45), (38.6, 14.0, -4.0)])
    bpath = Path([(30.0, 0.0, 2.6), (31.2, 0.0, 1.3)])
    fpath = Path([(30.0, -1.25, -0.3), (32.2, -1.25, -0.3), (32.9, -0.95, -0.35), (39.0, -0.95, -0.35), (39.5, -0.6, -0.4)])

    def upd(t, w):
        wt = c.wt(t)
        # Kid (real time).
        over = {}
        if t < 31.9:
            stumble = ramp(t, 31.45, 31.7) * (1 - ramp(t, 31.8, 32.2))
            over.update(lean=-15 * stumble, arm_l=(40 * stumble, 25), arm_r=(40 * stumble, 25))
        elif t < 33.4:
            over["arm_r"] = snap_arm(t, 32.95)
            over["head"] = (0, -40 * ramp(t, 33.05, 33.3))
        face = 0.0 if t < 33.4 else None
        locomote(kid, kpath, t, gz, run=t > 33.3, face=face, turn=0.25,
                 **({} if t > 33.4 else over))
        if t > 33.4:
            kid.pose(tuple(kid.root.location), kid.heading,
                     **{**Human.walk(kpath.dist(t) / 1.15 * math.pi, 1.0, True), "head": (0, 20 * ramp(t, 34.5, 35.0))})
        # Bully (world clock): walk in, shove, raise a fist.
        shove = ramp(wt, 31.3, 31.45) * (1 - ramp(wt, 31.6, 31.9))
        fist = ramp(wt, 32.3, 32.9)
        bover = dict(arm_l=(80 * shove + 30 * fist, 6), arm_r=(80 * shove + 115 * fist, 6), lean=10 * shove + 6 * fist)
        locomote(bully, bpath, wt, gz, face=math.pi, **bover)
        # Friend (world clock): reaches toward the kid; frozen mid-reach at the freeze.
        reach = ramp(wt, 32.2, 32.95)
        stumble = ramp(wt, 33.0, 33.5)
        locomote(friend, fpath, wt, gz, face=heading_to(1, 0.05),
                 arm_r=(88 * reach, 4), arm_l=(30 * reach, 15), lean=10 * reach + 18 * stumble,
                 head=(-5 * reach, 0))
    return [upd]


def beat_lock(c):
    gz = c.set["ground_z"]
    rng = random.Random(7)
    kid = Human("Kid_b7", c.col, c.rec)
    kid.heading = 0.0
    people = []
    for i in range(9):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(3.0, 9.0)
        d = rng.uniform(0, 2 * math.pi)
        adult = i % 3 != 0
        h = Human(f"Townsfolk{i}", c.col, c.rec, scale=1.3 if adult else 1.0,
                  shirt=("stone", "sky", "warm", "light", "dark")[i % 5], pants=("dark", "stone")[i % 2],
                  hair=("dark", "warm", "stone")[i % 3], hair_style=("short", "long")[(i // 2) % 2])
        if i in (1, 5):
            u = geo.empty(f"Townsfolk{i}.umb", c.col, (0.18, 0.15, 1.12), parent=h.root)
            geo.cone(f"Townsfolk{i}.umb.top", c.col, ("warm", "sky")[i % 2], 0.62, 0.0, 0.3, (0, 0, 0.62), seg=8, parent=u)
            geo.box(f"Townsfolk{i}.umb.stick", c.col, "dark", (0.03, 0.03, 0.66), (0, 0, 0), origin="bottom", parent=u)
        people.append((h, (r * math.cos(a), r * math.sin(a)), (math.cos(d), math.sin(d)), rng.uniform(0.8, 1.3), i in (1, 5)))
    birds = [ch.Bird(f"TownBird{i}", c.col, c.rec) for i in range(3)]
    kpath = Path([(40.0, 0.0, -0.8), (40.6, 0.0, 0.0)])

    def upd(t, w):
        wt = c.wt(t)
        over = {}
        if t < 41.3:
            over["arm_r"] = snap_arm(t, 40.95)
        else:
            a = max(snap_arm(t, 42.2)[0], snap_arm(t, 43.3)[0], snap_arm(t, 44.4)[0])
            over["arm_r"] = (a, 22 * a / 105)
            over["arm_l"] = (0.6 * snap_arm(t, 43.85)[0], 20)
        slump = ramp(t, 45.8, 46.8)
        if slump > 0:
            over.update(lean=22 * slump, head=(30 * slump, 0), arm_l=(5, 4), arm_r=(5, 4))
        spin = 0.0
        if t > 41.3:
            spin = RAD(35) * math.sin((t - 41.3) * 1.4) * (1 - slump) + RAD(200) * ramp(t, 44.8, 45.7)
        locomote(kid, kpath, t, gz, face=spin, turn=0.3, **over)
        for h, p0, d, sp, umb in people:
            x, y = p0[0] + d[0] * sp * (wt - 40.0), p0[1] + d[1] * sp * (wt - 40.0)
            p = Human.walk(sp * (wt - 40.0) / 0.9 * math.pi + p0[0], 1.0)
            if umb:
                p["arm_r"] = (65, 10)
            h.pose((x, y, 0), heading_to(*d), **p)
        for i, b in enumerate(birds):
            a = wt * 0.6 + i * 2.1
            b.pose((7 * math.cos(a), 7 * math.sin(a), 8 + i), a, wt * 13 + i, bank=-18)
    return [upd]


def beat_ending(c):
    gz = c.set["ground_z"]
    kid = Human("Kid_b8", c.col, c.rec)
    kid.heading = 0.0
    path = Path([(48.0, 0.0, 0.0), (50.8, 0.0, 0.0), (57.0, 0.5, 2.5)])

    def upd(t, w):
        over = dict(head=(18 * ramp(t, 50.3, 51.0), 0))
        locomote(kid, path, t, gz, stride=0.55, turn=0.2, **over)
    return [upd]


BEATS = {1: beat_hook, 2: beat_first_freeze, 3: beat_cookies, 4: beat_test,
         5: beat_animals, 6: beat_friend, 7: beat_lock, 8: beat_ending}

# Per-beat lighting: one key area light, one fill. Positions relative to the set origin.
LIGHTS = {
    1: dict(world="sky", world_str=0.9, key=(-14, 22, 15), key_col=(1.0, 0.82, 0.66), key_size=10, fill=(9, -12, 7), fill_col=(0.7, 0.76, 1.0)),
    2: dict(world="sky", world_str=0.9, key=(-14, 22, 15), key_col=(1.0, 0.82, 0.66), key_size=10, fill=(9, -12, 7), fill_col=(0.7, 0.76, 1.0)),
    3: dict(gain=0.45, world="sky", world_str=0.5, key=(-9, -8, 13), key_col=(1.0, 0.86, 0.72), key_size=8, fill=(10, -7, 5), fill_col=(0.72, 0.78, 1.0)),
    4: dict(gain=0.35, world="sky", world_str=0.35, key=(-5.5, -1.5, 3.7), key_col=(1.0, 0.9, 0.78), key_size=4, fill=(4.0, -5.0, 3.6), fill_col=(0.8, 0.84, 1.0), aim=(0, 3, 0.8)),
    5: dict(world="sky", world_str=0.9, key=(-12, 18, 14), key_col=(1.0, 0.82, 0.66), key_size=10, fill=(8, -10, 6), fill_col=(0.7, 0.76, 1.0)),
    6: dict(gain=0.5, world="sky", world_str=0.6, key=(12, 16, 14), key_col=(1.0, 0.82, 0.66), key_size=10, fill=(-8, -10, 6), fill_col=(0.7, 0.76, 1.0)),
    7: dict(gain=0.45, world="sky", world_str=0.55, key=(-20, -14, 26), key_col=(1.0, 0.84, 0.7), key_size=16, fill=(16, 10, 10), fill_col=(0.7, 0.76, 1.0)),
    8: dict(world="warm", world_str=0.06, key=(0, 30, 7), key_col=(1.0, 0.75, 0.55), key_size=12, fill=(0, -10, 6), fill_col=(0.55, 0.6, 0.9), fill_mult=0.02),
}


def add_lights(bid, col):
    cfg = LIGHTS[bid]
    aim = cfg.get("aim", (0, 2, 1))
    from mathutils import Vector
    for role, posk, colk, mult, size, shadow in (
            ("key", "key", "key_col", 1.0, cfg["key_size"], True),
            ("fill", "fill", "fill_col", cfg.get("fill_mult", 0.3), cfg["key_size"] * 1.5, False)):
        pos = Vector(cfg[posk])
        d = (pos - Vector(aim)).length
        ld = bpy.data.lights.new(f"B{bid}.{role}", "AREA")
        ld.shape = "DISK"
        ld.size = size
        ld.color = cfg[colk]
        ld.energy = 900.0 * (d / 4.5) ** 2 * mult * cfg.get("gain", 1.0)
        ld.use_shadow = shadow
        ob = bpy.data.objects.new(f"B{bid}.{role}", ld)
        col.objects.link(ob)
        ob.location = pos
        ob.rotation_mode = "QUATERNION"
        ob.rotation_quaternion = geo.look_quat(Vector(aim) - pos)


def make_world(bid, style):
    cfg = LIGHTS[bid]
    w = bpy.data.worlds.new(f"World_B{bid}")
    w.use_nodes = True
    nt = w.node_tree
    out = nt.nodes["World Output"]
    light_bg = nt.nodes["Background"]
    rgb = tuple(tl_lib.srgb_to_linear(c) for c in tl_lib.hex_rgb(style["palette"][cfg["world"]])) + (1.0,)
    light_bg.inputs["Color"].default_value = rgb
    light_bg.inputs["Strength"].default_value = cfg["world_str"]
    cam_bg = nt.nodes.new("ShaderNodeBackground")  # what the camera sees: the flat palette color
    cam_bg.inputs["Color"].default_value = rgb
    cam_bg.inputs["Strength"].default_value = 1.0
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(light_bg.outputs[0], mix.inputs[1])
    nt.links.new(cam_bg.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return w


# ======================================================================= main
def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--beat", required=True, help="beat id, or 'all' (with --save-blend)")
    ap.add_argument("--out", default=None, help="output directory for the PNG sequence")
    ap.add_argument("--mode", default="preview", choices=["preview", "final"])
    ap.add_argument("--engine", default=None, choices=["eevee", "cycles"])
    ap.add_argument("--samples", type=int, default=None)
    ap.add_argument("--width", type=int, default=None)
    ap.add_argument("--height", type=int, default=None)
    ap.add_argument("--frames", default=None, help="subset, e.g. 61-90 or a single time like t=3.5")
    ap.add_argument("--save-blend", default=None)
    ap.add_argument("--force", action="store_true", help="re-render frames that already exist")
    return ap.parse_args(argv)


def main():
    a = parse()
    t_start = time.time()
    tl = tl_lib.Timeline()
    style = tl_lib.style()
    rcfg = dict(style["render"][a.mode])
    for k in ("engine", "samples", "width", "height"):
        if getattr(a, k) is not None:
            rcfg[k] = getattr(a, k)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = tl.fps
    geo.make_materials(style)
    rec = geo.Recorder()

    wanted = [int(b["id"]) for b in tl.beats] if a.beat == "all" else [int(a.beat)]
    sets, beat_cols, updaters, cams, worlds = {}, {}, {}, {}, {}
    for b in tl.beats:
        bid = int(b["id"])
        col = env.new_collection(f"Beat_{bid:02d}")
        beat_cols[bid] = col
        if b["set"] not in sets:
            s = env.SETS[b["set"]](rec)
            scene.collection.children.unlink(s["col"])
            sets[b["set"]] = s
        s = sets[b["set"]]
        col.children.link(s["col"])
        if bid not in wanted:
            continue
        c = Ctx(tl, rec, b, col, s)
        updaters[bid] = BEATS[bid](c)
        add_lights(bid, col)
        cams[bid] = (camlib.make_camera(f"Cam_B{bid}", col, rec),
                     camlib.build_sampler(tl.d["camera"][str(bid)]))
        worlds[bid] = make_world(bid, style)

    # Bake: walk every frame of each wanted beat once, in order.
    for bid in wanted:
        b = tl.beat(bid)
        f0, f1 = tl.frame_range(bid)
        s = sets[b["set"]]
        cam, sampler = cams[bid]
        for f in range(f0, f1 + 1):
            t = tl.t_of(f)
            w = tl.world(t)
            for u in s["ambient"]:
                u(t, w)
            for u in updaters[bid]:
                u(t, w)
            camlib.pose_camera(cam, sampler, t)
            rec.capture(f)
    rec.flush()
    print(f"[build_scene] built and baked in {time.time() - t_start:.1f}s")

    # Render settings.
    r = scene.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = rcfg["width"], rcfg["height"], 100
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGB"
    r.image_settings.compression = 15
    r.use_overwrite = a.force
    r.use_placeholder = False
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    if rcfg["engine"] == "eevee":
        r.engine = "BLENDER_EEVEE"
        e = scene.eevee
        e.taa_render_samples = rcfg["samples"]
        e.use_soft_shadows = True
        e.shadow_cube_size = "1024"
        e.shadow_cascade_size = "2048"
        e.use_gtao = True
        e.gtao_distance = 1.2
        e.gtao_factor = 1.0
    else:
        r.engine = "CYCLES"
        cy = scene.cycles
        cy.device = "CPU"
        cy.samples = rcfg["samples"]
        cy.use_denoising = False  # this Blender build has no OpenImageDenoise
        cy.use_adaptive_sampling = True
        cy.max_bounces = 4
        cy.diffuse_bounces = 2
        cy.glossy_bounces = 1
        cy.transmission_bounces = 1
        cy.transparent_max_bounces = 4
        cy.blur_glossy = 1.0
        cy.sample_clamp_indirect = 3.0

    if a.save_blend:
        os.makedirs(os.path.dirname(os.path.abspath(a.save_blend)), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save_blend))
        print(f"[build_scene] saved {a.save_blend}")
    if a.beat == "all" or not a.out:
        return

    bid = int(a.beat)
    for k, col in beat_cols.items():
        bpy.context.view_layer.layer_collection.children[col.name].exclude = (k != bid)
    scene.camera = cams[bid][0]
    scene.world = worlds[bid]
    f0, f1 = tl.frame_range(bid)
    ranges = [(f0, f1)]
    if a.frames:
        if a.frames.startswith("t="):
            ranges = [(int(round(float(x) * tl.fps)) + 1,) * 2 for x in a.frames[2:].split(",")]
        else:
            lo, hi = a.frames.split("-")
            ranges = [(max(f0, int(lo)), min(f1, int(hi)))]
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    r.filepath = os.path.join(out, "######")
    print(f"[build_scene] rendering beat {bid} frames {ranges} at {rcfg['width']}x{rcfg['height']} "
          f"{rcfg['engine']} {rcfg['samples']} samples -> {out}")
    t0 = time.time()
    n = 0
    for lo, hi in ranges:
        scene.frame_start, scene.frame_end = lo, hi
        bpy.ops.render.render(animation=True)
        n += hi - lo + 1
    print(f"[build_scene] beat {bid}: {n} frames in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
