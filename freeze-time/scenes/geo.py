"""Low-poly mesh helpers, shared flat materials, and a fast keyframe recorder."""
import math

import bmesh
import bpy
from mathutils import Vector

import timeline_lib as tl_lib

MATS = {}


# ---------------------------------------------------------------- materials
def _principled(name, hex_color, rough=0.85, spec=0.15, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    rgb = tuple(tl_lib.srgb_to_linear(c) for c in tl_lib.hex_rgb(hex_color)) + (1.0,)
    bsdf.inputs["Base Color"].default_value = rgb
    bsdf.inputs["Roughness"].default_value = rough
    for key in ("Specular IOR Level", "Specular"):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = spec
            break
    if emit > 0:
        for key in ("Emission Color", "Emission"):
            if key in bsdf.inputs:
                bsdf.inputs[key].default_value = rgb
                break
        bsdf.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = rgb
    return m


def make_materials(style):
    """One shared material per palette color, plus emissive and water variants of the same colors."""
    MATS.clear()
    pal = style["palette"]
    for name, hx in pal.items():
        MATS[name] = _principled(name, hx)
    MATS["glow"] = _principled("glow", pal["warm"], emit=4.0)
    MATS["rain"] = _principled("rain", pal["light"], emit=0.6)
    MATS["water"] = _principled("water", pal["sky"], rough=0.95, spec=0.03)
    return MATS


def mat(name):
    return MATS[name]


# ---------------------------------------------------------------- objects
def link(obj, col):
    col.objects.link(obj)
    return obj


def _finish(name, bm, col, material, loc, parent):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False  # flat shading everywhere
    if material is not None:
        me.materials.append(mat(material) if isinstance(material, str) else material)
    ob = bpy.data.objects.new(name, me)
    link(ob, col)
    if parent is not None:
        ob.parent = parent
    ob.location = loc
    return ob


def empty(name, col, loc=(0, 0, 0), parent=None):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_size = 0.2
    link(ob, col)
    if parent is not None:
        ob.parent = parent
    ob.location = loc
    return ob


def box(name, col, material, size, loc=(0, 0, 0), origin="center", parent=None):
    sx, sy, sz = size
    z0 = {"center": -sz / 2, "top": -sz, "bottom": 0.0}[origin]
    bm = bmesh.new()
    v = [bm.verts.new((x * sx / 2, y * sy / 2, z0 + zz * sz))
         for x in (-1, 1) for y in (-1, 1) for zz in (0, 1)]
    # v index = (xi*2 + yi)*2 + zi
    def q(a, b, c, d):
        bm.faces.new((v[a], v[b], v[c], v[d]))
    q(0, 2, 6, 4)  # bottom
    q(1, 5, 7, 3)  # top
    q(0, 1, 3, 2)  # -x
    q(4, 6, 7, 5)  # +x
    q(0, 4, 5, 1)  # -y
    q(2, 3, 7, 6)  # +y
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish(name, bm, col, material, loc, parent)


def cone(name, col, material, r1, r2, h, loc=(0, 0, 0), seg=7, origin="bottom", parent=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=r1, radius2=r2, depth=h)
    dz = {"bottom": h / 2, "center": 0.0, "top": -h / 2}[origin]
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, dz))
    return _finish(name, bm, col, material, loc, parent)


def ico(name, col, material, r, loc=(0, 0, 0), subdiv=1, scale=(1, 1, 1), parent=None):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    return _finish(name, bm, col, material, loc, parent)


def poly(name, col, material, verts, faces, loc=(0, 0, 0), parent=None):
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in verts]
    for f in faces:
        bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish(name, bm, col, material, loc, parent)


def roof(name, col, material, w, d, h, loc, parent=None):
    """Triangular prism, ridge along x. loc is the eave center."""
    verts = [(-w / 2, -d / 2, 0), (w / 2, -d / 2, 0), (w / 2, d / 2, 0), (-w / 2, d / 2, 0),
             (-w / 2, 0, h), (w / 2, 0, h)]
    faces = [(0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)]
    return poly(name, col, material, verts, faces, loc, parent)


def plane(name, col, material, sx, sy, loc=(0, 0, 0), parent=None):
    verts = [(-sx / 2, -sy / 2, 0), (sx / 2, -sy / 2, 0), (sx / 2, sy / 2, 0), (-sx / 2, sy / 2, 0)]
    return poly(name, col, material, verts, [(0, 1, 2, 3)], loc, parent)


def grid_terrain(name, col, material, size, step, height_fn, rng, jitter=0.25, loc=(0, 0, 0)):
    """Faceted terrain: a jittered triangle grid displaced by height_fn(x, y)."""
    n = int(size / step)
    bm = bmesh.new()
    vs = {}
    for i in range(n + 1):
        for j in range(n + 1):
            x = -size / 2 + i * step
            y = -size / 2 + j * step
            if 0 < i < n and 0 < j < n:
                x += rng.uniform(-jitter, jitter) * step
                y += rng.uniform(-jitter, jitter) * step
            vs[i, j] = bm.verts.new((x, y, height_fn(x, y)))
    for i in range(n):
        for j in range(n):
            a, b, c, d = vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]
            if (i + j) % 2:
                bm.faces.new((a, b, c)); bm.faces.new((a, c, d))
            else:
                bm.faces.new((a, b, d)); bm.faces.new((b, c, d))
    return _finish(name, bm, col, material, loc, None)


def look_quat(direction):
    return Vector(direction).to_track_quat("-Z", "Y")


# ---------------------------------------------------------------- math
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ramp(t, t0, t1):
    """0 before t0, smooth to 1 at t1."""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return smooth((t - t0) / (t1 - t0))


def lerp(a, b, k):
    return a + (b - a) * k


def lerp3(a, b, k):
    return tuple(lerp(x, y, k) for x, y in zip(a, b))


def heading_to(dx, dy):
    """Rotation about Z that turns local +Y toward (dx, dy)."""
    return math.atan2(-dx, dy)


def angle_lerp(a, b, k):
    d = (b - a + math.pi) % (2 * math.pi) - math.pi
    return a + d * k


class Path:
    """Piecewise-linear 2D path with waypoint times: [(t, x, y), ...]."""

    def __init__(self, pts):
        self.pts = sorted(pts)

    def at(self, t):
        p = self.pts
        if t <= p[0][0]:
            return p[0][1], p[0][2]
        for (t0, x0, y0), (t1, x1, y1) in zip(p, p[1:]):
            if t0 <= t <= t1:
                k = 0 if t1 == t0 else (t - t0) / (t1 - t0)
                return lerp(x0, x1, k), lerp(y0, y1, k)
        return p[-1][1], p[-1][2]

    def dist(self, t):
        d = 0.0
        p = self.pts
        for (t0, x0, y0), (t1, x1, y1) in zip(p, p[1:]):
            seg = math.hypot(x1 - x0, y1 - y0)
            if t >= t1:
                d += seg
            elif t > t0:
                d += seg * (t - t0) / (t1 - t0)
        return d

    def velocity(self, t, h=1 / 30):
        x0, y0 = self.at(t - h)
        x1, y1 = self.at(t + h)
        return (x1 - x0) / (2 * h), (y1 - y0) / (2 * h)


# ---------------------------------------------------------------- keyframes
class Recorder:
    """Collects per-frame transforms in Python, then writes F-curves in one pass.

    Much faster than keyframe_insert for hundreds of objects x hundreds of frames.
    """

    def __init__(self):
        self.tracks = {}  # key -> {path: [(frame, values)]}
        self.objs = {}

    def add(self, obj, *paths):
        key = (type(obj).__name__, obj.name)
        self.objs[key] = obj
        t = self.tracks.setdefault(key, {})
        for p in paths:
            t.setdefault(p, [])

    def capture(self, frame):
        for name, paths in self.tracks.items():
            ob = self.objs[name]
            for p, rows in paths.items():
                v = getattr(ob, p)
                rows.append((frame, (v,) if isinstance(v, (int, float)) else tuple(v)))

    def flush(self):
        for name, paths in self.tracks.items():
            ob = self.objs[name]
            ad = ob.animation_data_create()
            act = bpy.data.actions.new(name[1] + "_act")
            ad.action = act
            for p, rows in paths.items():
                if not rows:
                    continue
                dims = len(rows[0][1])
                for i in range(dims):
                    fc = act.fcurves.new(p, index=i)
                    fc.keyframe_points.add(len(rows))
                    co = []
                    for f, vals in rows:
                        co += [f, vals[i]]
                    fc.keyframe_points.foreach_set("co", co)
                    fc.keyframe_points.foreach_set("interpolation", [1] * len(rows))  # LINEAR
                    fc.update()
