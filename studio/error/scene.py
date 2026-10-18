"""Lays book.py's maps on a book and photographs it, for book.py, which runs it:

    blender -b --factory-startup -P studio/error/scene.py -- WORK

WORK holds layout.json and each page's maps. The wide plate is the book lying open on a dark cloth: boards covered in
indigo silk, and on them the two halves of the text block, each page rising out of the gutter and easing down at its
fore-edge, the edges of the leaves under it showing. The tall plate is one loose page of it on the same cloth. A
cherry petal or two has fallen on the pages. The light is a big window to the top left, a soft box high over the camera for
the gold to catch, and the room.

The camera is a long lens straight overhead. Writes render.npy (linear RGBA, top row first) and boxes.json: where each
of the page's words lands in the frame, as fractions of it, and the box the pages cover.
"""

import json
import math
import os
import sys

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

work = sys.argv[sys.argv.index("--") + 1]
layout = json.load(open(os.path.join(work, "layout.json")))
MM = 0.001
ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "desk", "assets")
BOARD = 3.2  # mm, the boards' thickness
OVERHANG = 6.0  # mm the boards stand out past the leaves
HEIGHT = 2.6  # m, the camera over the cloth
rng = np.random.default_rng(5)

bpy.ops.wm.read_factory_settings(use_empty=True)
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "METAL"
prefs.get_devices()
for device in prefs.devices:
    device.use = device.type == "METAL"
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "GPU"
scene.cycles.samples = layout["samples"]
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.006
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 8
scene.render.resolution_x, scene.render.resolution_y = layout["px"]
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.color_depth = "32"


def mesh(name, verts, faces, uvs=None, material=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    if uvs is not None:
        layer = me.uv_layers.new(name="UV")
        index = np.empty(len(me.loops), np.int32)
        me.loops.foreach_get("vertex_index", index)
        layer.data.foreach_set("uv", np.asarray(uvs, np.float32)[index].ravel())
    if smooth:
        me.shade_smooth()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    if material:
        me.materials.append(material)
    return obj


def grid_faces(nx, ny):
    i = np.arange(nx * ny).reshape(ny, nx)
    a, b, c, d = i[:-1, :-1], i[:-1, 1:], i[1:, 1:], i[1:, :-1]
    return np.stack([a, b, c, d], -1).reshape(-1, 4)


def node(tree, kind, **inputs):
    n = tree.nodes.new(kind)
    for key, value in inputs.items():
        n.inputs[key].default_value = value
    return n


# ---------------------------------------------------------------- materials


def paper(name, page):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    t = m.node_tree
    bsdf = t.nodes["Principled BSDF"]
    bsdf.inputs["Sheen Weight"].default_value = 0.25
    bsdf.inputs["Sheen Roughness"].default_value = 0.5
    bsdf.inputs["Specular IOR Level"].default_value = 0.4
    bsdf.inputs["Coat Roughness"].default_value = 0.22
    bsdf.inputs["Subsurface Weight"].default_value = 0.08
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.9, 0.8)
    bsdf.inputs["Subsurface Scale"].default_value = 0.0015

    def image(kind, colour=False):
        img = bpy.data.images.load(os.path.join(work, f"{name}-{kind}.png"))
        if not colour:
            img.colorspace_settings.name = "Non-Color"
        n = t.nodes.new("ShaderNodeTexImage")
        n.image = img
        n.interpolation = "Cubic"
        n.extension = "EXTEND"
        return n

    t.links.new(image("albedo", True).outputs["Color"], bsdf.inputs["Base Color"])
    t.links.new(image("metal").outputs["Color"], bsdf.inputs["Metallic"])
    t.links.new(image("rough").outputs["Color"], bsdf.inputs["Roughness"])
    coat = image("coat")
    scale = t.nodes.new("ShaderNodeMath")
    scale.operation = "MULTIPLY"
    scale.inputs[1].default_value = 0.7
    t.links.new(coat.outputs["Color"], scale.inputs[0])
    t.links.new(scale.outputs[0], bsdf.inputs["Coat Weight"])
    bump = node(t, "ShaderNodeBump", Strength=0.6, Distance=page["relief"] * MM)
    t.links.new(image("height").outputs["Color"], bump.inputs["Height"])
    t.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def silk(name, colour, rough=0.32, weave=900.0, sheen=0.7):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    t = m.node_tree
    bsdf = t.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*colour, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Anisotropic"].default_value = 0.65
    bsdf.inputs["Sheen Weight"].default_value = sheen
    bsdf.inputs["Sheen Roughness"].default_value = 0.35
    bsdf.inputs["Specular IOR Level"].default_value = 0.55
    coords = t.nodes.new("ShaderNodeTexCoord")
    # The weave: warp threads one way, weft the other.
    warp = node(t, "ShaderNodeTexWave", Scale=weave, Distortion=0.6, Detail=1.0)
    warp.wave_profile = "SIN"
    weft = node(t, "ShaderNodeTexWave", Scale=weave * 1.3, Distortion=0.4)
    weft.bands_direction = "Y"
    mix = node(t, "ShaderNodeMath")
    mix.operation = "MAXIMUM"
    t.links.new(coords.outputs["Object"], warp.inputs["Vector"])
    t.links.new(coords.outputs["Object"], weft.inputs["Vector"])
    t.links.new(warp.outputs["Fac"], mix.inputs[0])
    t.links.new(weft.outputs["Fac"], mix.inputs[1])
    bump = node(t, "ShaderNodeBump", Strength=0.12, Distance=0.00015)
    t.links.new(mix.outputs[0], bump.inputs["Height"])
    t.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def leaves_edge():
    """The edges of the stacked leaves: fine lines, some a shade darker, none quite straight."""
    m = bpy.data.materials.new("edges")
    m.use_nodes = True
    t = m.node_tree
    bsdf = t.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.9
    coords = t.nodes.new("ShaderNodeTexCoord")
    lines = node(t, "ShaderNodeTexWave", Scale=2400.0, Distortion=3.0, Detail=2.0, **{"Detail Scale": 2.0})
    lines.bands_direction = "Z"
    t.links.new(coords.outputs["Object"], lines.inputs["Vector"])
    ramp = t.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.62, 0.58, 0.51, 1)
    ramp.color_ramp.elements[1].color = (0.80, 0.77, 0.70, 1)
    t.links.new(lines.outputs["Fac"], ramp.inputs["Fac"])
    t.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def petal_material():
    m = bpy.data.materials.new("petal")
    m.use_nodes = True
    t = m.node_tree
    bsdf = t.nodes["Principled BSDF"]
    coords = t.nodes.new("ShaderNodeTexCoord")
    sep = t.nodes.new("ShaderNodeSeparateXYZ")
    t.links.new(coords.outputs["Generated"], sep.inputs["Vector"])
    ramp = t.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.95, 0.60, 0.68, 1)  # deeper pink at the claw
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[1].color = (0.99, 0.90, 0.91, 1)
    ramp.color_ramp.elements[1].position = 0.45
    t.links.new(sep.outputs["Y"], ramp.inputs["Fac"])
    t.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.42
    bsdf.inputs["Subsurface Weight"].default_value = 0.25
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.6, 0.65)
    bsdf.inputs["Subsurface Scale"].default_value = 0.0005
    bsdf.inputs["Sheen Weight"].default_value = 0.4
    veins = node(t, "ShaderNodeTexWave", Scale=60.0, Distortion=2.0)
    veins.bands_direction = "X"
    t.links.new(coords.outputs["Generated"], veins.inputs["Vector"])
    bump = node(t, "ShaderNodeBump", Strength=0.15, Distance=0.0001)
    t.links.new(veins.outputs["Fac"], bump.inputs["Height"])
    t.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


# ---------------------------------------------------------------- shapes


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def lift(s, w):
    """How high a leaf stands, in mm over the boards, s mm out from the gutter on a page w mm wide: down in the
    gutter, rising steeply out of it, a slow arch, and easing down over the fore-edge."""
    return 0.6 + 11.5 * (1 - np.exp(-s / 19)) + 2.0 * np.sin(np.pi * np.clip(s / w, 0, 1)) - 2.6 * smoothstep(w - 10, w, s) ** 1.6


class Surface:
    """A page laid on the set: where a point x, y mm on the page (from its top left) lies in the world."""

    def __init__(self, w, h, left, top, gutter, base):
        self.w, self.h, self.left, self.top, self.gutter, self.base = w, h, left, top, gutter, base

    def z(self, x, y):
        if self.gutter is None:  # a loose sheet: flat, its corners curling up a little
            cx = np.abs(x - self.w / 2) / (self.w / 2)
            cy = np.abs(y - self.h / 2) / (self.h / 2)
            return self.base + 0.25 + 2.2 * smoothstep(0.82, 1, np.maximum(cx, cy)) ** 2 * smoothstep(0.7, 1, np.minimum(cx, cy) + 0.3)
        s = x if self.gutter == "left" else self.w - x
        cockle = 0.25 * np.sin(y / 23 + x / 41) * smoothstep(10, 50, s)
        return self.base + lift(s, self.w) + cockle

    def world(self, x, y):
        x, y = np.asarray(x, np.float32), np.asarray(y, np.float32)
        return np.stack([(self.left + x) * MM, (self.top - y) * MM, self.z(x, y) * MM], -1)

    def build(self, name, material, step=1.0):
        nx, ny = int(self.w / step) + 1, int(self.h / step) + 1
        xs, ys = np.meshgrid(np.linspace(0, self.w, nx), np.linspace(0, self.h, ny))
        verts = self.world(xs, ys).reshape(-1, 3)
        uvs = np.stack([xs / self.w, 1 - ys / self.h], -1).reshape(-1, 2)
        return mesh(name, verts, grid_faces(nx, ny), uvs, material)

    def walls(self, name, material, floor):
        """The edges of the leaves under the page, down to floor (mm): along its head, its tail and its fore-edge."""
        objs = []
        edges = []
        n = 240
        if self.gutter is not None:
            far = self.w if self.gutter == "left" else 0.0
            edges.append([(far, y) for y in np.linspace(0, self.h, n)])
        edges.append([(x, 0.0) for x in np.linspace(0, self.w, n)])
        edges.append([(x, self.h) for x in np.linspace(0, self.w, n)])
        for i, edge in enumerate(edges):
            xs, ys = np.array(edge).T
            top = self.world(xs, ys)
            bottom = top.copy()
            bottom[:, 2] = floor * MM
            verts = np.concatenate([top, bottom])
            faces = [(j, j + 1, n + j + 1, n + j) for j in range(n - 1)]
            objs.append(mesh(f"{name}-wall-{i}", verts, faces, None, material, smooth=False))
        return objs


def box(name, x0, y0, x1, y1, z0, z1, material, bevel=0.6):
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    obj.name = name
    obj.scale = ((x1 - x0) / 2 * MM, (y1 - y0) / 2 * MM, (z1 - z0) / 2 * MM)
    obj.location = ((x0 + x1) / 2 * MM, (y0 + y1) / 2 * MM, (z0 + z1) / 2 * MM)
    bpy.ops.object.transform_apply(scale=True)
    mod = obj.modifiers.new("bevel", "BEVEL")
    mod.width = bevel * MM
    mod.segments = 3
    obj.data.materials.append(material)
    return obj


def cloth(frame):
    """The dark cloth the book lies on: a matte black weave, flat, reaching well past the frame."""
    m = silk("cloth", (0.010, 0.010, 0.012), rough=0.8, weave=700, sheen=0.25)
    w, h = frame[0] * 1.6 * MM, frame[1] * 1.6 * MM
    return mesh("cloth", [(-w / 2, -h / 2, -0.4 * MM), (w / 2, -h / 2, -0.4 * MM), (w / 2, h / 2, -0.4 * MM), (-w / 2, h / 2, -0.4 * MM)], [(0, 1, 2, 3)], None, m)


def petal(material, at, turn, size, cup, base):
    """A cherry petal: a rounded fan narrowing to its claw, notched at its tip, cupped and a little curled."""
    rings, spokes = 7, 48
    verts = [(0.0, -0.5, 0.0)]
    for r in range(1, rings + 1):
        k = r / rings
        for i in range(spokes):
            t = 2 * math.pi * i / spokes
            x, y = 0.48 * math.cos(t), 0.5 * math.sin(t)
            x *= 0.45 + 0.55 * (y + 0.5)  # narrower toward the claw
            notch = 0.16 * math.exp(-((t - math.pi / 2) / 0.22) ** 2)
            y -= notch
            px, py = x * k, -0.5 + (y + 0.5) * k
            verts.append((px, py, 0.0))
    faces = [(0, 1 + i, 1 + (i + 1) % spokes) for i in range(spokes)]
    for r in range(rings - 1):
        a, b = 1 + r * spokes, 1 + (r + 1) * spokes
        faces += [(a + i, a + (i + 1) % spokes, b + (i + 1) % spokes, b + i) for i in range(spokes)]
    v = np.array(verts)
    v[:, 2] = cup * (v[:, 0] ** 2) * 2.2 + 0.18 * cup * (v[:, 1] + 0.5) ** 2
    c, s = math.cos(turn), math.sin(turn)
    xy = v[:, :2] * size
    v[:, 0], v[:, 1] = at[0] + xy[:, 0] * c - xy[:, 1] * s, at[1] + xy[:, 0] * s + xy[:, 1] * c
    v[:, 2] = base + v[:, 2] * size
    obj = mesh("petal", v * MM, faces, None, material)
    mod = obj.modifiers.new("solid", "SOLIDIFY")
    mod.thickness = 0.12 * MM
    return obj


# ---------------------------------------------------------------- the set

plate = layout["plate"]
frame = layout["frame"]
pages = layout["pages"]
surfaces = {}
edges = leaves_edge()
if plate == "wide":
    w, h = pages["right"]["size"]
    lift_base = BOARD + 0.6
    surfaces["right"] = Surface(w, h, 0.0, h / 2, "left", lift_base)
    surfaces["left"] = Surface(w, h, -w, h / 2, "right", lift_base)
    board = silk("board", (0.018, 0.03, 0.075), rough=0.4, weave=1400, sheen=0.5)
    box("boards", -w - OVERHANG, -h / 2 - OVERHANG, w + OVERHANG, h / 2 + OVERHANG, 0, BOARD, board)
    for name, surface in surfaces.items():
        surface.build(name, paper(name, pages[name]))
        surface.walls(name, edges, BOARD)
    petals = [((176, -100), 2.1, 15.5, 0.9, "right"), ((-176, -60), -0.6, 14.0, 1.1, "left")]
else:
    w, h = pages["loose"]["size"]
    surfaces["loose"] = Surface(w, h, -w / 2, h / 2, None, 0.0)
    surfaces["loose"].build("loose", paper("loose", pages["loose"]))
    petals = [((58, 6), 2.0, 12.0, 1.0, "loose")]

cloth(frame)
petal_mat = petal_material()
for at, turn, size, cup, on in petals:
    s = surfaces[on]
    base = float(s.z(np.array(at[0] - s.left), np.array(s.top - at[1]))) + 0.15
    petal(petal_mat, at, turn, size, cup, base)

# ---------------------------------------------------------------- light

world = bpy.data.worlds.new("room")
scene.world = world
world.use_nodes = True
wt = world.node_tree
env = wt.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(os.path.join(ASSETS, "studio_small_08.hdr"))
mapping = wt.nodes.new("ShaderNodeMapping")
mapping.inputs["Rotation"].default_value = (0, 0, math.radians(130))
coord = wt.nodes.new("ShaderNodeTexCoord")
wt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
wt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
wt.links.new(env.outputs["Color"], wt.nodes["Background"].inputs["Color"])
wt.nodes["Background"].inputs["Strength"].default_value = 0.35


def area(name, location, size, energy, colour, target=(0, 0, 0)):
    data = bpy.data.lights.new(name, "AREA")
    data.shape = "DISK"
    data.size = size
    data.energy = energy
    data.color = colour
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    direction = Vector(target) - Vector(location)
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return obj


# A tall window to the top left, the day white with a little warmth in it.
area("window", (-1.5, 1.1, 1.5), 1.6, 2600, (1.0, 0.95, 0.88))
# A big soft box high over the camera, for the gold and the mica to catch.
area("soft box", (0.35, -0.25, HEIGHT + 0.6), 3.0, 520, (1.0, 0.98, 0.95))
# Light thrown back off a wall to the right, a little cooler.
area("bounce", (1.8, -0.6, 0.7), 2.2, 380, (0.92, 0.95, 1.0))

cam_data = bpy.data.cameras.new("lens")
cam_data.sensor_width = 36
if plate == "wide":
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.lens = 36 * HEIGHT / (frame[0] * MM)
else:
    cam_data.sensor_fit = "VERTICAL"
    cam_data.sensor_height = 36
    cam_data.lens = 36 * HEIGHT / (frame[1] * MM)
camera = bpy.data.objects.new("camera", cam_data)
bpy.context.collection.objects.link(camera)
camera.location = (0, 0, HEIGHT)
scene.camera = camera

# ---------------------------------------------------------------- shoot

exr = os.path.join(work, "render.exr")
scene.render.filepath = exr
bpy.ops.render.render(write_still=True)
img = bpy.data.images.load(exr)
W, H = img.size
pixels = np.empty(W * H * 4, np.float32)
img.pixels.foreach_get(pixels)
np.save(os.path.join(work, "render.npy"), pixels.reshape(H, W, 4)[::-1])


def project(points):
    out = []
    for p in points:
        v = world_to_camera_view(scene, camera, Vector(p))
        out.append((v.x, 1 - v.y))
    return np.array(out)


boxes = {}
for name, page in pages.items():
    s = surfaces[name]
    for anchor in page["anchors"]:
        x0, y0, x1, y1 = anchor["box"]
        xs = np.linspace(x0, x1, 5)
        ys = np.linspace(y0, y1, 5)
        gx, gy = np.meshgrid(xs, ys)
        pts = project(s.world(gx.ravel(), gy.ravel()))
        (fx0, fy0), (fx1, fy1) = pts.min(0), pts.max(0)
        boxes[anchor["id"]] = {"text": anchor["text"], "box": [round(float(v), 5) for v in (fx0, fy0, fx1 - fx0, fy1 - fy0)], "vertical": anchor.get("vertical", False)}
    corners = project(s.world(np.array([0, s.w, s.w, 0]), np.array([0, 0, s.h, s.h])))
    boxes.setdefault("_pages", []).append([round(float(v), 5) for v in (*corners.min(0), *corners.max(0))])
json.dump(boxes, open(os.path.join(work, "boxes.json"), "w"), ensure_ascii=False)
