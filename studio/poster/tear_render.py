"""Renders the poster's torn edge, for tear.py, which runs it:

    blender -b --factory-startup -P studio/poster/tear_render.py -- WORK

WORK holds spec.json and tear.npz, which tear.py writes: the print and the core under it as surfaces swept down the
rows, and the fibres of the bared core. They lie on the mat under the copy stand's light (studio/desk's stage, as
studio/edgecast lights the strips' edges). Four renders, all straight down at the edge:

- edge.exr: the print alone over nothing, so its alpha is how much of each pixel the print covers;
- core.exr: the bared paper and its fibres, the print unseen but still in the light's way;
- cast.exr: the mat with the strip on it, the strip unseen but still in the light's way;
- bare.exr: the mat alone;
- flat.exr: a little of the paper lying flat, for its white.
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
data = np.load(os.path.join(work, "tear.npz"))
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


def swept(name, xs, zs):
    """A surface swept down the rows: xs and zs give, for each row, its points across."""
    rows, cols = xs.shape
    ys = np.broadcast_to(data["ys"][:, None], xs.shape)
    verts = np.stack([xs, -ys, zs], -1).reshape(-1, 3)
    r, c = np.meshgrid(np.arange(rows - 1), np.arange(cols - 1), indexing="ij")
    a = (r * cols + c).ravel()
    obj = mesh(name, verts, np.stack([a, a + cols, a + cols + 1, a + 1], -1))
    obj.data.shade_smooth()
    return obj


def paint(name, colour, roughness, through=0.0):
    """A plain surface of the colour it shows (linear); through, how much light passes a fibre untouched, and what
    it does not let past it scatters on through as much as back, as cellulose does."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*colour, 1)
    shader.inputs["Roughness"].default_value = roughness
    if through:
        glow = nodes.new("ShaderNodeBsdfTranslucent")
        glow.inputs["Color"].default_value = (*colour, 1)
        half = nodes.new("ShaderNodeMixShader")
        half.inputs["Fac"].default_value = 0.5
        links.new(shader.outputs[0], half.inputs[1])
        links.new(glow.outputs[0], half.inputs[2])
        clear = nodes.new("ShaderNodeBsdfTransparent")
        mix = nodes.new("ShaderNodeMixShader")
        mix.inputs["Fac"].default_value = 1 - through
        links.new(clear.outputs[0], mix.inputs[1])
        links.new(half.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], nodes["Material Output"].inputs["Surface"])
    return material


printed = swept("print", data["print_x"], data["print_z"])
printed.data.materials.append(paint("print", spec["print"], 0.8))
core = swept("core", data["core_x"], data["core_z"])
core.data.materials.append(paint("core", spec["paper"], 0.9))

curves = bpy.data.hair_curves.new("fibres")
curves.add_curves(data["sizes"].tolist())
curves.position_data.foreach_set("vector", data["points"].astype(np.float32).ravel())
radius = curves.attributes.get("radius") or curves.attributes.new("radius", "FLOAT", "POINT")
radius.data.foreach_set("value", data["radius"].astype(np.float32))
fibres = bpy.data.objects.new("fibres", curves)
scene.collection.objects.link(fibres)
curves.materials.append(paint("fibre", spec["paper"], 0.6, spec["through"]))

page = mesh("page", [(-4000, 4000, 0), (4000, 4000, 0), (4000, -4000, 0), (-4000, -4000, 0)], [(0, 1, 2, 3)])
page.data.materials.append(paint("page", spec["under"], 0.7))

prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "METAL"
prefs.get_devices()
for device in prefs.devices:
    device.use = device.type == "METAL"
scene.render.engine = "CYCLES"
scene.cycles.device = "GPU"
scene.cycles.use_adaptive_sampling = False
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


def seen(*objs):
    for obj in (printed, core, fibres, page):
        obj.visible_camera = obj in objs


samples = spec["samples"]
seen(printed)
shoot("edge", spec["edge_frame"], spec["edge_density"], max(64, samples // 2), 1.0, False)
# The print is only ink on the core's own face, so it shades nothing of it: the bared core runs white up to it.
seen(core, fibres)
printed.visible_shadow = False
shoot("core", spec["frame"], spec["density"], samples, 1.0, True)
printed.visible_shadow = True
# Each pixel of the shadow sees only its own square, so it lies exactly where the strip does.
seen(page)
shoot("cast", spec["frame"], spec["density"], samples, 0.01, True)
for obj in (printed, core, fibres):
    obj.hide_render = True
shoot("bare", spec["frame"], spec["density"], samples, 0.01, True)
# The bared paper's own white, lying flat in the same light, far from anything, for tear.py to measure it by.
page.data.materials[0] = core.data.materials[0]
shoot("flat", (-4, 4), 2, samples, 1.0, True)
