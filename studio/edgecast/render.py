"""Renders one strip's edge lying on the strip after it, for edgecast.py, which runs it:

    blender -b --factory-startup -P studio/edgecast/render.py -- SPEC.json OUT_DIR

SPEC gives what the strip is made of ("mat" or "poster"), how thick it is, the frame to render across the edge (x in CSS
px from the strip's edge, out positive), how long a length of it runs and how far past either end to render, the pixels
to a CSS px and the samples. A poster also gives its tear, the edge's x at each CSS px down one length, and how far
the torn paper curls up off the mat at each.

The mat is leather THICK thick, cut straight, its cut burnished round at the top and a little at the foot, lying flat
on the page. The poster is a sheet of paper cut along its tear, its torn edge curling a little up off the page where
it was pulled. Each is its own colour (SPEC colour, roughness) and so is the page (under), under the copy stand's own
studio light (studio/desk's stage, its room and octabox). Writes OUT_DIR/cast.exr, that render, OUT_DIR/bare.exr,
the same frame with nothing on the page, and OUT_DIR/flat.exr, the strip's own flat top far from its edge, for
edgecast.py to divide the first by the others.
"""

import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Quaternion

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "desk"))
import stage  # noqa: E402

# The factory scene's cube, lamp and camera out of the way first.
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj)

spec_path, out_dir = sys.argv[sys.argv.index("--") + 1 :]
spec = json.load(open(spec_path))
kind, thick = spec["kind"], spec["thick"]
x0, x1 = spec["frame"]
length, past = spec["length"], spec["past"]
y0, y1 = -past, length + past
# How far in from the edge the strip runs on in the render, and past the frame's ends, well past where it could shade.
BACK = 400.0
BEYOND = 200.0


def mesh(name, verts, faces):
    data = bpy.data.meshes.new(name)
    data.vertices.add(len(verts))
    data.vertices.foreach_set("co", np.asarray(verts, np.float32).ravel())
    faces = np.asarray(faces, np.int32)
    data.loops.add(faces.size)
    data.loops.foreach_set("vertex_index", faces.ravel())
    data.polygons.add(len(faces))
    data.polygons.foreach_set("loop_start", np.arange(0, faces.size, 4, dtype=np.int32))
    data.update()
    data.validate()
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def strip(section, edge, lift, line):
    """A solid swept down the edge: section is its outline across, (x in from the edge, z up) closed round from the
    top far in, out to the edge and back under; edge and lift give, for each row down, how far out the edge lies
    and how far up its last stretch curls, and line the edge's run with its jags smoothed out, which the curl follows:
    paper curls as a whole, not at each jag. Rows are y in CSS px, down."""
    rows = len(edge)
    ys = np.linspace(y0 - BEYOND, y1 + BEYOND, rows)
    n = len(section)
    verts = []
    for y, out, up, run in zip(ys, edge, lift, line):
        for x, z in section:
            # x here is negative, in from the edge; the curl rises toward the edge's run over CURL.
            rise = up * np.clip(1 + (out + x - run) / CURL, 0, 1) ** 2 if CURL else 0.0
            verts.append((out + x, -y, z + rise))
    faces = []
    for r in range(rows - 1):
        for k in range(n):
            a, b = r * n + k, r * n + (k + 1) % n
            faces.append((a, b, b + n, a + n))
    obj = mesh(kind, verts, faces)
    # Its faces all turned outward, so its rounded cut shades smoothly.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    # Smooth round its cut, but hard at its corners, so a corner's leaning normal is not spread across a wide face.
    obj.data.shade_smooth()
    obj.data.set_sharp_from_angle(angle=math.radians(30))
    return obj


def mat_section():
    """The mat's cut, across: flat on top, rounding over at the burnished top edge, straight down its cut, rounding
    in a little at its foot."""
    top, foot = 0.32 * thick, 0.12 * thick
    # The top runs flat right up to where it rounds over, so the round's leaning normals stay on the round.
    pts = [(-BACK, thick), (-top - 0.25, thick)]
    for t in np.linspace(0, math.pi / 2, 12):
        pts.append((-top + top * math.sin(t), thick - top + top * math.cos(t)))
    for t in np.linspace(0, math.pi / 2, 6):
        pts.append((-foot + foot * math.cos(t), foot - foot * math.sin(t)))
    pts.append((-BACK, 0.0))
    # A hair off the page, so the page and the mat's underside never share a plane.
    return [(x, max(z, 0.002)) for x, z in pts]


def paper_section():
    """The paper across: its top and underside, out to a torn edge, which is soft and frays thinner at its very end."""
    xs = np.concatenate([[-BACK], -np.geomspace(60, 0.25, 40), [0.0]])
    top = [(x, thick) for x in xs]
    end = [(0.0, 0.5 * thick)]
    under = [(x, 0.002) for x in xs[::-1]]
    return top + end + under


if kind == "mat":
    CURL = 0.0
    rows = 2
    obj = strip(mat_section(), np.zeros(rows), np.zeros(rows), np.zeros(rows))
else:
    CURL = spec["curl"]
    tear = np.asarray(spec["edge"], np.float64)  # x at each CSS px down one length, length + 1 values
    up = np.asarray(spec["lift"], np.float64)
    ys = np.linspace(y0 - BEYOND, y1 + BEYOND, round((y1 - y0 + 2 * BEYOND) * 2) + 1)
    at = np.mod(ys, length)
    grid = np.arange(len(tear))
    edge = np.interp(at, grid, tear)
    # Smoothed over 30 CSS px (two rows to one), its ends held.
    window = np.hanning(121) / np.hanning(121).sum()
    line = np.convolve(np.pad(edge, 60, mode="edge"), window, "valid")
    obj = strip(paper_section(), edge, np.interp(at, grid, up), line)


def paint(name, colour, roughness):
    """A plain surface of the colour it is on the page (linear), so the light it throws back onto the page beside it
    is as much as the real one's: a dark mat's lit cut throws back far less than a white one would."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*colour, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = 0.3
    return material


obj.data.materials.append(paint(kind, spec["colour"], spec["roughness"]))

scene = bpy.context.scene
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "METAL"
prefs.get_devices()
for device in prefs.devices:
    device.use = device.type == "METAL"
scene.render.engine = "CYCLES"
scene.cycles.device = "GPU"
scene.cycles.samples = spec["samples"]
scene.cycles.use_adaptive_sampling = False
scene.cycles.use_denoising = spec.get("denoise", True)
# Each pixel sees only its own square, so it splits cleanly into strip and page where edgecast.py says the edge lies.
scene.cycles.filter_width = 0.01
# No stray bright path, which would print as a speck on the page.
scene.cycles.sample_clamp_indirect = 1.0
scene.view_settings.view_transform = "Standard"
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
scene.render.resolution_x = round((x1 - x0) * spec["density"])
scene.render.resolution_y = round((y1 - y0) * spec["density"])
scene.render.resolution_percentage = 100

# The copy stand's room: its studio, turned so the octabox is up and to the top right of the page.
world = bpy.data.worlds.new("room")
scene.world = world
world.use_nodes = True
nodes, links = world.node_tree.nodes, world.node_tree.links
coord = nodes.new("ShaderNodeTexCoord")
turn = nodes.new("ShaderNodeMapping")
aim = stage.BOX_ON_STAND.rotation_difference(stage.BOX_IN_ROOM) @ Quaternion(stage.BOX_ON_STAND, stage.ROOM_ROLL)
turn.inputs["Rotation"].default_value = aim.to_euler()
room = nodes.new("ShaderNodeTexEnvironment")
room.image = bpy.data.images.load(os.path.join(stage.ASSETS, stage.ROOM))
links.new(coord.outputs["Generated"], turn.inputs["Vector"])
links.new(turn.outputs["Vector"], room.inputs["Vector"])
links.new(room.outputs["Color"], nodes["Background"].inputs["Color"])

page = mesh("page", [(-4000, 4000, 0), (4000, 4000, 0), (4000, -4000, 0), (-4000, -4000, 0)], [(0, 1, 2, 3)])
page.data.materials.append(paint("page", spec["under"], 0.7))

camera_data = bpy.data.cameras.new("overhead")
camera_data.type = "ORTHO"
camera_data.ortho_scale = max(x1 - x0, y1 - y0)
camera_data.clip_end = 1000
camera = bpy.data.objects.new("overhead", camera_data)
camera.location = ((x0 + x1) / 2, -(y0 + y1) / 2, 300)
scene.collection.objects.link(camera)
scene.camera = camera

# The page bare, the strip on it, and the strip moved out so the frame sees only its flat top, far from either end.
for name, with_strip, out in (("bare", False, 0), ("cast", True, 0), ("flat", True, BACK / 2)):
    obj.hide_render = not with_strip
    obj.location.x = out
    scene.render.filepath = os.path.join(out_dir, f"{name}.exr")
    bpy.ops.render.render(write_still=True)
