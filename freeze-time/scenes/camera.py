"""Camera paths from timeline.json segments: dolly, orbit, hold. No shake, ever."""
import math

import bpy

import geo


def ease(k, mode):
    k = geo.clamp(k)
    if mode == "in":
        return k * k
    if mode == "out":
        return 1 - (1 - k) * (1 - k)
    if mode == "inout":
        return geo.smooth(k)
    return k


def _pair(v, default):
    if v is None:
        return default, default
    return float(v[0]), float(v[1])


def build_sampler(segments, default_lens=28.0):
    """Returns f(t) -> (pos, look, lens). Each segment starts where the previous ended
    unless it gives an explicit 'from'."""
    plan = []
    state = None  # (pos, look, lens)
    for s in segments:
        typ = s["type"]
        if typ == "dolly":
            a = s.get("from")
            p0 = tuple(a["pos"]) if a else state[0]
            l0 = tuple(a["look"]) if a else state[1]
            lens = _pair(s.get("lens"), state[2] if state else default_lens)
            p1, l1 = tuple(s["to"]["pos"]), tuple(s["to"]["look"])
            plan.append(("dolly", s, (p0, l0), (p1, l1), lens))
            state = (p1, l1, lens[1])
        elif typ == "orbit":
            lens = _pair(s.get("lens"), state[2] if state else default_lens)
            cx, cy = s["center"]
            r1, h1, d1 = s["radius"][1], s["height"][1], math.radians(s["deg"][1])
            end = (cx + r1 * math.cos(d1), cy + r1 * math.sin(d1), h1)
            plan.append(("orbit", s, None, None, lens))
            state = (end, tuple(s["look"]), lens[1])
        elif typ == "hold":
            plan.append(("hold", s, state, None, (state[2], state[2])))
        else:
            raise ValueError(f"unknown camera segment type {typ}")

    def sample(t):
        seg = plan[-1]
        for p in plan:
            if p[1]["t0"] <= t < p[1]["t1"]:
                seg = p
                break
        if t < plan[0][1]["t0"]:
            seg = plan[0]
        kind, s, a, b, lens = seg
        k = (t - s["t0"]) / max(1e-6, s["t1"] - s["t0"])
        k = ease(k, s.get("ease", "inout"))
        L = geo.lerp(lens[0], lens[1], k)
        if kind == "dolly":
            return geo.lerp3(a[0], b[0], k), geo.lerp3(a[1], b[1], k), L
        if kind == "orbit":
            cx, cy = s["center"]
            r = geo.lerp(s["radius"][0], s["radius"][1], k)
            h = geo.lerp(s["height"][0], s["height"][1], k)
            d = math.radians(geo.lerp(s["deg"][0], s["deg"][1], k))
            return (cx + r * math.cos(d), cy + r * math.sin(d), h), tuple(s["look"]), L
        return a[0], a[1], L

    return sample


def make_camera(name, col, rec):
    data = bpy.data.cameras.new(name)
    data.sensor_fit = "VERTICAL"
    data.sensor_height = 36.0
    data.clip_start = 0.05
    data.clip_end = 600.0
    cam = bpy.data.objects.new(name, data)
    col.objects.link(cam)
    cam.rotation_mode = "QUATERNION"
    rec.add(cam, "location", "rotation_quaternion")
    rec.add(data, "lens")
    return cam


def pose_camera(cam, sampler, t):
    from mathutils import Vector
    pos, look, lens = sampler(t)
    cam.location = pos
    cam.rotation_quaternion = geo.look_quat(Vector(look) - Vector(pos))
    cam.data.lens = lens
