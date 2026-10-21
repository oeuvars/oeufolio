"""Renders the letter's deckle edge, for edge.py, which runs it:

    blender -b --factory-startup -P studio/paper/deckle.py -- WORK

WORK holds spec.json and fibres.npz, which edge.py writes. The sheet is the pulp laid as it was laid: its body, a
surface at the paper's thickness wherever the pulp lies thick, and toward the line the pulp stopped on, its fibres
themselves, each a thread of cotton as long and as fine as the paper's own, lying where they settled and curling as
they do. Each fibre is cellulose, so a single one lets most of the light through and only where they cross and
pile up does the sheet turn solid. It lies on the strip after it (the poster's print) under the copy stand's light
(studio/desk's stage, as studio/edgecast lights the strips' edges).

Three renders, all looking straight down at the edge:

- mask.exr: the sheet over nothing, so its alpha is how much of each pixel the paper covers;
- cast.exr: the page with the sheet on it, the sheet unseen but still in the light's way;
- bare.exr: the page alone.

edge.py keeps the first as the mask the page cuts its sheet with, and the second over the third as its shadow.
"""

import json
import os
import sys

import bpy
import numpy as np
from mathutils import Quaternion

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "desk"))
import stage  # noqa: E402

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj)

work = sys.argv[sys.argv.index("--") + 1]
spec = json.load(open(os.path.join(work, "spec.json")))
data = np.load(os.path.join(work, "fibres.npz"))
scene = bpy.context.scene


def mesh(name, verts, faces):
    shape = bpy.data.meshes.new(name)
    shape.vertices.add(len(verts))
    shape.vertices.foreach_set("co", np.asarray(verts, np.float32).ravel())
    faces = np.asarray(faces, np.int32)
    shape.loops.add(faces.size)
    shape.loops.foreach_set("vertex_index", faces.ravel())
    shape.polygons.add(len(faces))
    shape.polygons.foreach_set("loop_start", np.arange(0, faces.size, 4, dtype=np.int32))
    shape.update()
    shape.validate()
    obj = bpy.data.objects.new(name, shape)
    scene.collection.objects.link(obj)
    return obj


def paint(name, colour, roughness, through=0.0):
    """A plain surface of the colour it shows (linear); through, how much light passes a fibre untouched."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*colour, 1)
    shader.inputs["Roughness"].default_value = roughness
    if through:
        # Cellulose: what a fibre does not let straight past it, it scatters on through as much as back.
        glow = nodes.new("ShaderNodeBsdfTranslucent")
        glow.inputs["Color"].default_value = (*colour, 1)
        half = nodes.new("ShaderNodeMixShader")
        half.inputs["Fac"].default_value = 0.5
        links.new(shader.outputs[0], half.inputs[1])
        links.new(glow.outputs[0], half.inputs[2])
        shader = half
        clear = nodes.new("ShaderNodeBsdfTransparent")
        mix = nodes.new("ShaderNodeMixShader")
        mix.inputs["Fac"].default_value = 1 - through
        links.new(clear.outputs[0], mix.inputs[1])
        links.new(shader.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], nodes["Material Output"].inputs["Surface"])
    return material


# The body: the sheet's top where the pulp lies thick, a heightfield over the grid edge.py measured it on, and on
# past the frame's left, far into the sheet, flat.
grid = data["body"]  # z at each grid point, nan off the body
gx, gy = data["body_x"], data["body_y"]
rows, cols = grid.shape
X, Y = np.meshgrid(gx, gy)
verts = np.stack([X.ravel(), -Y.ravel(), np.nan_to_num(grid).ravel()], -1)
on = ~np.isnan(grid)
quad = on[:-1, :-1] & on[1:, :-1] & on[:-1, 1:] & on[1:, 1:]
r, c = np.nonzero(quad)
a = r * cols + c
faces = np.stack([a, a + 1, a + 1 + cols, a + cols], -1)
body = mesh("body", verts, faces)
far = mesh("far", [(gx[0] - 600, -gy[0] + 600, spec["thick"]), (gx[0] + 0.01, -gy[0] + 600, spec["thick"]), (gx[0] + 0.01, -gy[-1] - 600, spec["thick"]), (gx[0] - 600, -gy[-1] - 600, spec["thick"])], [(0, 1, 2, 3)])
pulp = paint("pulp", spec["paper"], 0.9)
body.data.materials.append(pulp)
far.data.materials.append(pulp)

# The fibres: one curve each, with its points and its radius at each.
sizes = data["sizes"]
curves = bpy.data.hair_curves.new("fibres")
curves.add_curves(sizes.tolist())
curves.position_data.foreach_set("vector", data["points"].astype(np.float32).ravel())
radius = curves.attributes.get("radius") or curves.attributes.new("radius", "FLOAT", "POINT")
radius.data.foreach_set("value", data["radius"].astype(np.float32))
fibres = bpy.data.objects.new("fibres", curves)
scene.collection.objects.link(fibres)
curves.materials.append(paint("fibre", spec["paper"], 0.6, spec["through"]))

page = mesh("page", [(-4000, 4000, 0), (4000, 4000, 0), (4000, -4000, 0), (-4000, -4000, 0)], [(0, 1, 2, 3)])
page.data.materials.append(paint("page", spec["under"], 0.8))

prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "METAL"
prefs.get_devices()
for device in prefs.devices:
    device.use = device.type == "METAL"
scene.render.engine = "CYCLES"
scene.cycles.device = "GPU"
scene.cycles.use_adaptive_sampling = False
# Fibres pile many deep before the sheet turns solid: every one of them counts.
scene.cycles.transparent_max_bounces = 256
scene.cycles.max_bounces = 8
scene.cycles.sample_clamp_indirect = 1.0
scene.cycles_curves.shape = "THICK"
scene.render.film_transparent = True
scene.view_settings.view_transform = "Standard"
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
scene.render.resolution_percentage = 100

# The copy stand's room, as studio/edgecast has it.
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

y0, y1 = spec["rows"]
camera_data = bpy.data.cameras.new("overhead")
camera_data.type = "ORTHO"
camera_data.clip_end = 1000
camera = bpy.data.objects.new("overhead", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera


def shoot(name, frame, density, samples, filter_width, denoise):
    x0, x1 = frame
    camera_data.ortho_scale = max(x1 - x0, y1 - y0)
    camera.location = ((x0 + x1) / 2, -(y0 + y1) / 2, 300)
    scene.render.resolution_x = round((x1 - x0) * density)
    scene.render.resolution_y = round((y1 - y0) * density)
    scene.cycles.samples = samples
    scene.cycles.filter_width = filter_width
    scene.cycles.use_denoising = denoise
    scene.render.filepath = os.path.join(work, f"{name}.exr")
    bpy.ops.render.render(write_still=True)


sheet = (body, far, fibres)
# The mask: the sheet alone, every pixel's share of it antialiased over a pixel's own square.
page.hide_render = True
shoot("mask", spec["mask_frame"], spec["mask_density"], spec["mask_samples"], 1.0, False)
page.hide_render = False
# Its shadow: the page with the sheet in the light's way, and the page bare. Each pixel sees only its own square, so
# the shadow lies exactly where the sheet does.
for obj in sheet:
    obj.visible_camera = False
shoot("cast", spec["cast_frame"], spec["cast_density"], spec["samples"], 0.01, True)
for obj in sheet:
    obj.hide_render = True
shoot("bare", spec["cast_frame"], spec["cast_density"], spec["samples"], 0.01, True)
