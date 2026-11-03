"""Blocky humans and low-poly animals. Each rig is a small hierarchy of boxes.

Animation is baked by build_scene.py: every frame it calls .pose(...) and the
Recorder captures transforms into keyframes.
"""
import math

from mathutils import Euler, Matrix, Vector

import geo
from geo import box, cone, empty, ico, poly, plane

RAD = math.radians


class Human:
    """Kid at scale 1.0 is about 1.45 units tall. Local forward is +Y."""

    SHOULDER = (0.28, 0.0, 0.44)  # relative to torso origin (hip height)
    ARM_LEN = 0.50

    def __init__(self, name, col, rec, scale=1.0, shirt="warm", pants="dark", skin="light",
                 hair="dark", hair_style="short", mouth_open=False):
        self.name = name
        self.scale = scale
        self.root = empty(f"{name}", col)
        self.root.scale = (scale,) * 3
        self.legs = {}
        for side, sx in (("l", -1), ("r", 1)):
            self.legs[side] = box(f"{name}.leg_{side}", col, pants, (0.16, 0.18, 0.62),
                                  (0.11 * sx, 0, 0.62), origin="top", parent=self.root)
            box(f"{name}.shoe_{side}", col, "dark", (0.17, 0.26, 0.08), (0, 0.04, -0.58),
                origin="center", parent=self.legs[side])
        self.torso = box(f"{name}.torso", col, shirt, (0.44, 0.26, 0.5), (0, 0, 0.6),
                         origin="bottom", parent=self.root)
        self.head = box(f"{name}.head", col, skin, (0.34, 0.32, 0.34), (0, 0, 0.52),
                        origin="bottom", parent=self.torso)
        box(f"{name}.hair", col, hair, (0.36, 0.34, 0.1), (0, -0.01, 0.33), origin="bottom",
            parent=self.head)
        if hair_style == "long":
            box(f"{name}.hair_back", col, hair, (0.36, 0.08, 0.32), (0, -0.16, 0.06), origin="bottom",
                parent=self.head)
        for sx in (-1, 1):
            box(f"{name}.eye{sx}", col, "dark", (0.05, 0.02, 0.06), (0.075 * sx, 0.165, 0.2),
                parent=self.head)
        if mouth_open:
            box(f"{name}.mouth", col, "dark", (0.08, 0.02, 0.07), (0, 0.165, 0.08), parent=self.head)
        self.arms = {}
        for side, sx in (("l", -1), ("r", 1)):
            sh = (self.SHOULDER[0] * sx, self.SHOULDER[1], self.SHOULDER[2])
            self.arms[side] = box(f"{name}.arm_{side}", col, shirt, (0.13, 0.15, 0.5), sh,
                                  origin="top", parent=self.torso)
            box(f"{name}.hand_{side}", col, skin, (0.12, 0.13, 0.1), (0, 0, -0.5), origin="center",
                parent=self.arms[side])
        self.parts = [self.torso, self.head, self.arms["l"], self.arms["r"], self.legs["l"], self.legs["r"]]
        rec.add(self.root, "location", "rotation_euler")
        for p in self.parts:
            rec.add(p, "rotation_euler")
        self.heading = 0.0
        self.pose((0, 0, 0), 0.0)

    def pose(self, loc, heading, arm_l=(0, 0), arm_r=(0, 0), leg_l=0.0, leg_r=0.0,
             head=(0, 0), lean=0.0, twist=0.0, bob=0.0, lean_side=0.0):
        """Angles in degrees. arm=(forward swing, sideways out)."""
        self.heading = heading
        self.root.location = (loc[0], loc[1], loc[2] + bob)
        self.root.rotation_euler = (0, 0, heading)
        self.torso.rotation_euler = (RAD(-lean), RAD(lean_side), RAD(twist))
        self.head.rotation_euler = (RAD(-head[0]), 0, RAD(head[1]))
        self.arms["l"].rotation_euler = (RAD(arm_l[0]), RAD(arm_l[1]), 0)
        self.arms["r"].rotation_euler = (RAD(arm_r[0]), RAD(-arm_r[1]), 0)
        self.legs["l"].rotation_euler = (RAD(leg_l), 0, 0)
        self.legs["r"].rotation_euler = (RAD(leg_r), 0, 0)

    def hand_world(self, side):
        """World position of a hand, computed from the current pose (no depsgraph needed)."""
        sx = -1 if side == "l" else 1
        m = (Matrix.Translation(self.root.location) @ Euler(self.root.rotation_euler).to_matrix().to_4x4()
             @ Matrix.Scale(self.scale, 4)
             @ Matrix.Translation(self.torso.location) @ Euler(self.torso.rotation_euler).to_matrix().to_4x4()
             @ Matrix.Translation(self.arms[side].location)
             @ Euler(self.arms[side].rotation_euler).to_matrix().to_4x4())
        return m @ Vector((0, 0, -self.ARM_LEN))

    # Convenience pose builders -------------------------------------------
    @staticmethod
    def walk(phase, amp=1.0, run=False):
        a = (28 if not run else 50) * amp
        s = math.sin(phase)
        return dict(arm_l=(a * s, 6), arm_r=(-a * s, 6), leg_l=-a * s, leg_r=a * s,
                    bob=abs(math.cos(phase)) * (0.03 if not run else 0.07) * amp,
                    lean=(4 if not run else 14) * amp)

    @staticmethod
    def idle(t):
        b = math.sin(t * 2.0)
        return dict(arm_l=(2 * b, 5), arm_r=(-2 * b, 5), bob=0.006 * b)


class Dog:
    """Low-poly dog. Local forward is +Y. Origin on the ground."""

    def __init__(self, name, col, rec, color="warm"):
        self.root = empty(name, col)
        self.body = box(f"{name}.body", col, color, (0.3, 0.72, 0.3), (0, 0, 0.5), parent=self.root)
        self.head = box(f"{name}.head", col, color, (0.26, 0.28, 0.26), (0, 0.42, 0.16), parent=self.body)
        box(f"{name}.snout", col, "light", (0.16, 0.16, 0.12), (0, 0.2, -0.05), parent=self.head)
        box(f"{name}.nose", col, "dark", (0.07, 0.04, 0.05), (0, 0.29, -0.01), parent=self.head)
        for sx in (-1, 1):
            box(f"{name}.ear{sx}", col, "dark", (0.07, 0.06, 0.14), (0.1 * sx, -0.04, 0.16), parent=self.head)
            box(f"{name}.eye{sx}", col, "dark", (0.04, 0.02, 0.04), (0.07 * sx, 0.14, 0.05), parent=self.head)
        self.tail = box(f"{name}.tail", col, color, (0.06, 0.06, 0.26), (0, -0.36, 0.1), origin="bottom",
                        parent=self.body)
        self.legs = []
        for i, (lx, ly) in enumerate([(-0.1, 0.25), (0.1, 0.25), (-0.1, -0.25), (0.1, -0.25)]):
            lg = box(f"{name}.leg{i}", col, color, (0.08, 0.08, 0.36), (lx, ly, -0.12), origin="top",
                     parent=self.body)
            self.legs.append(lg)
        rec.add(self.root, "location", "rotation_euler")
        for p in [self.body, self.tail, self.head] + self.legs:
            rec.add(p, "rotation_euler")
        rec.add(self.body, "location")

    def pose(self, loc, heading, pitch=0.0, gait=0.0, amp=0.0, stretch=0.0, tail=0.0, height=0.0):
        self.root.location = loc
        self.root.rotation_euler = (0, 0, heading)
        self.body.location = (0, 0, 0.5 + height)
        self.body.rotation_euler = (RAD(pitch), 0, 0)
        self.tail.rotation_euler = (RAD(-35), RAD(tail), 0)
        self.head.rotation_euler = (RAD(-pitch * 0.4), 0, 0)
        s = math.sin(gait)
        swings = [s, -s, -s, s]
        for i, lg in enumerate(self.legs):
            front = i < 2
            ext = (55 if front else -55) * stretch
            lg.rotation_euler = (RAD(35 * amp * swings[i] + ext), 0, 0)


class Bird:
    def __init__(self, name, col, rec, color="dark"):
        self.root = empty(name, col)
        ico(f"{name}.body", col, color, 0.14, (0, 0, 0), subdiv=1, scale=(0.8, 1.5, 0.8), parent=self.root)
        cone(f"{name}.beak", col, "warm", 0.04, 0.0, 0.1, (0, 0.24, 0), seg=4, origin="bottom",
             parent=self.root).rotation_euler = (RAD(-90), 0, 0)
        self.wings = []
        for sx in (-1, 1):
            w = poly(f"{name}.wing{sx}", col, color,
                     [(0, -0.1, 0), (0, 0.12, 0), (0.42 * sx, -0.05, 0)], [(0, 1, 2)],
                     (0.08 * sx, 0, 0.02), parent=self.root)
            self.wings.append((w, sx))
        rec.add(self.root, "location", "rotation_euler")
        for w, _ in self.wings:
            rec.add(w, "rotation_euler")

    def pose(self, loc, heading, flap_phase, bank=0.0):
        self.root.location = loc
        self.root.rotation_euler = (0, RAD(bank), heading)
        a = 35 * math.sin(flap_phase)
        for w, sx in self.wings:
            w.rotation_euler = (0, RAD(-a * sx), 0)


class Kite:
    def __init__(self, name, col, rec, anchor):
        self.anchor = Vector(anchor)
        self.root = empty(name, col)
        poly(f"{name}.sail_a", col, "warm", [(0, 0, 0.75), (-0.5, 0, 0.1), (0, 0, -0.65)], [(0, 1, 2)],
             parent=self.root)
        poly(f"{name}.sail_b", col, "light", [(0, 0, 0.75), (0.5, 0, 0.1), (0, 0, -0.65)], [(0, 1, 2)],
             parent=self.root)
        self.tail = []
        for i in range(4):
            b = box(f"{name}.bow{i}", col, "light" if i % 2 else "warm", (0.16, 0.03, 0.08),
                    (0, 0, -0.85 - 0.32 * i), parent=self.root)
            self.tail.append(b)
            rec.add(b, "location")
        self.string = box(f"{name}.string", col, "light", (0.02, 0.02, 1.0), (0, 0, 0), origin="bottom")
        self.string.rotation_mode = "QUATERNION"
        rec.add(self.root, "location", "rotation_euler")
        rec.add(self.string, "location", "rotation_quaternion", "scale")

    def pose(self, loc, w):
        self.root.location = loc
        d = Vector(loc) - self.anchor
        self.root.rotation_euler = (RAD(8 * math.sin(w * 1.3)), 0, math.atan2(-d.x, d.y) + RAD(6 * math.sin(w * 0.9)))
        for i, b in enumerate(self.tail):
            b.location = (0.12 * math.sin(w * 3.0 - i * 0.9) * (i + 1) / 2, 0, -0.85 - 0.32 * i)
        self.string.location = self.anchor
        self.string.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
        self.string.scale = (1, 1, d.length - 0.6)


def swing(name, col, rec, loc, chain=1.7, seat_color="warm"):
    """Pivot empty at the top bar; rotate its X to swing."""
    pivot = empty(name, col, loc)
    for sx in (-1, 1):
        box(f"{name}.chain{sx}", col, "stone", (0.03, 0.03, chain), (0.22 * sx, 0, 0), origin="top", parent=pivot)
    box(f"{name}.seat", col, seat_color, (0.56, 0.24, 0.05), (0, 0, -chain), parent=pivot)
    rec.add(pivot, "rotation_euler")
    return pivot
