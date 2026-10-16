"""Renders one folder tab's cut paper, for tabcut.py, which runs it:

    blender -b --factory-startup -P studio/tabcut/render.py -- SPEC.json OUT_DIR

SPEC gives the tab's measures in rem (band, protrude, height, as SiteShell's TabShape), the frame to render in the
tab's own coordinates (x from where the band starts, y down from the tab's top), the pixels to a rem and the samples.

The paper is a sheet THICK thick, cut to the strip's edge and the tab's outline exactly as SiteShell draws it, its
cut a little ragged with fibres, lying on the page below. The tab stands off the folder, lifting a little towards its
tip, as a folder's tab does once it has been handled. Everything is white, under the copy stand's own studio light
(studio/desk's stage, its room and octabox), so what is rendered is only light and shadow. Writes OUT_DIR/cut.exr, that
render, and OUT_DIR/bare.exr, the same frame with nothing on the page, for tabcut.py to divide one by the other.
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

spec_path, out_dir = sys.argv[sys.argv.index("--") + 1 :]
spec = json.load(open(spec_path))
band, protrude, height = spec["band"], spec["protrude"], spec["height"]
x0, y0, w, h = spec["frame"]
THICK = 0.035  # rem
LIFT = 0.07  # rem, at the tab's tip
RAGGED = 0.012  # rem, how far the cut wanders
rng = np.random.default_rng(spec.get("seed", 5))


def outline():
    """The cut edge, top to bottom, as SiteShell's tabOutline draws it: down the strip's edge, out along the tab's
    eased corners and back, in rem, y down."""
    rise, ease = protrude * 0.33, protrude * 0.2
    corners = [(band, y0), (band, 0), (band + protrude, rise), (band + protrude, height - rise), (band, height), (band, y0 + h)]

    def toward(a, b):
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        return (a[0] + (b[0] - a[0]) / length * ease, a[1] + (b[1] - a[1]) / length * ease)

    points = [corners[0]]
    for i in range(1, 5):
        before, after = toward(corners[i], corners[i - 1]), toward(corners[i], corners[i + 1])
        points.append(before)
        for t in np.linspace(0, 1, 24)[1:-1]:
            # The quadratic from before to after with the corner as its control point.
            points.append(tuple((1 - t) ** 2 * np.array(before) + 2 * (1 - t) * t * np.array(corners[i]) + t**2 * np.array(after)))
        points.append(after)
    points.append(corners[-1])
    # Even steps along it, fine enough for its fibres.
    path = np.array(points)
    run = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(path, axis=0).T))])
    s = np.arange(0, run[-1], 0.004)
    path = np.stack([np.interp(s, run, path[:, 0]), np.interp(s, run, path[:, 1])], -1)
    # Ragged: wandering slowly and at fibre scale, outward and in, along its normal.
    tangent = np.gradient(path, axis=0)
    normal = np.stack([tangent[:, 1], -tangent[:, 0]], -1)
    normal /= np.linalg.norm(normal, axis=1, keepdims=True)
    wander = np.convolve(rng.standard_normal(len(s)), np.hanning(40) / np.hanning(40).sum(), "same")
    fibre = np.convolve(rng.standard_normal(len(s)), np.hanning(6) / np.hanning(6).sum(), "same")
    offset = RAGGED * (wander / wander.std() * 0.6 + fibre / fibre.std() * 0.4)
    return path + normal * offset[:, None]


def sheet():
    cut = outline()
    left = x0 - 0.2
    ring = [(left, y0 - 0.2), (cut[0, 0], y0 - 0.2), *map(tuple, cut), (cut[-1, 0], y0 + h + 0.2), (left, y0 + h + 0.2)]
    mesh = bpy.data.meshes.new("paper")
    bm = bmesh.new()
    verts = [bm.verts.new((x, -y, 0)) for x, y in ring]
    face = bm.faces.new(verts)
    grown = bmesh.ops.extrude_face_region(bm, geom=[face])
    for v in grown["geom"]:
        if isinstance(v, bmesh.types.BMVert):
            v.co.z = THICK
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("paper", mesh)
    bpy.context.scene.collection.objects.link(obj)
    # Even voxels through it, which round its cut a little as a real cut is, and give it the vertices to bend by.
    remesh = obj.modifiers.new("even", "REMESH")
    remesh.mode = "VOXEL"
    remesh.voxel_size = THICK / 4
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="even")
    co = np.empty(len(obj.data.vertices) * 3, np.float32)
    obj.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    # The tab lifts from the strip's edge to its tip.
    out = np.clip((co[:, 0] - band) / protrude, 0, 1)
    co[:, 2] += LIFT * out**2
    obj.data.vertices.foreach_set("co", co.ravel())
    obj.data.update()
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def white(name):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1)
    shader.inputs["Roughness"].default_value = 0.9
    shader.inputs["Specular IOR Level"].default_value = 0.2
    return material


scene = bpy.context.scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj)
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "METAL"
prefs.get_devices()
for device in prefs.devices:
    device.use = device.type == "METAL"
scene.render.engine = "CYCLES"
scene.cycles.device = "GPU"
scene.cycles.samples = spec["samples"]
scene.cycles.use_denoising = True
scene.view_settings.view_transform = "Standard"
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
scene.render.resolution_x = round(w * spec["density"])
scene.render.resolution_y = round(h * spec["density"])
scene.render.resolution_percentage = 100

# The copy stand's room: its studio, turned so the octabox is up and to the top left of the page.
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

ground = bpy.data.meshes.new("page")
ground.from_pydata([(-90, -90, 0), (90, -90, 0), (90, 90, 0), (-90, 90, 0)], [], [(0, 1, 2, 3)])
page = bpy.data.objects.new("page", ground)
scene.collection.objects.link(page)
ground.materials.append(white("page"))

camera_data = bpy.data.cameras.new("overhead")
camera_data.type = "ORTHO"
camera_data.ortho_scale = max(w, h)
camera = bpy.data.objects.new("overhead", camera_data)
camera.location = (x0 + w / 2, -(y0 + h / 2), 50)
scene.collection.objects.link(camera)
scene.camera = camera

for name, with_paper in (("bare", False), ("cut", True)):
    if with_paper:
        paper = sheet()
        paper.data.materials.append(white("paper"))
    scene.render.filepath = os.path.join(out_dir, f"{name}.exr")
    bpy.ops.render.render(write_still=True)
