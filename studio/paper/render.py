"""Lights paper.py's maps as a sheet of paper, for paper.py, which runs it:

    blender -b --factory-startup -P studio/paper/render.py -- WORK OUT SIZE SAMPLES

WORK holds albedo.png and height.png, one tile each, wrapping at their edges. The sheet is one tile and a margin
each side, its surface displaced by the height and bumped by it below the mesh's grain, under a low lamp from the
top left and a soft sky. The camera looks straight down at the middle tile, at SIZE pixels square, into OUT.
"""

import sys

import bpy
import numpy as np

work, out, size, samples = sys.argv[sys.argv.index("--") + 1 :]
size, samples = int(size), int(samples)
MARGIN = 0.08  # of a tile, each side: enough for the longest shadow to come in from the next tile
RELIEF = 0.0011  # the height map's full range, in tiles (about a quarter of a millimetre on a 230 mm tile)

scene = bpy.context.scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj)

prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "METAL"
prefs.get_devices()
for device in prefs.devices:
    device.use = True
scene.render.engine = "CYCLES"
scene.cycles.device = "GPU"
scene.cycles.samples = samples
scene.cycles.use_denoising = True
scene.render.resolution_x = scene.render.resolution_y = size
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_depth = "8"

albedo = bpy.data.images.load(f"{work}/albedo.png")
height = bpy.data.images.load(f"{work}/height.png")
height.colorspace_settings.name = "Non-Color"

# The sheet: a fine grid, its UVs in tiles so the maps repeat across the margin.
span = 1 + 2 * MARGIN
cuts = int(size * span * 0.75)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=cuts, y_subdivisions=cuts, size=span)
sheet = bpy.context.object
uv = sheet.data.uv_layers.new(name="UV")
mesh = sheet.data
co = np.empty(len(mesh.vertices) * 3, np.float32)
mesh.vertices.foreach_get("co", co)
index = np.empty(len(mesh.loops), np.int32)
mesh.loops.foreach_get("vertex_index", index)
uv.data.foreach_set("uv", (co.reshape(-1, 3)[index, :2] + 0.5).ravel())

texture = bpy.data.textures.new("height", "IMAGE")
texture.image = height
texture.extension = "REPEAT"
displace = sheet.modifiers.new("relief", "DISPLACE")
displace.texture = texture
displace.texture_coords = "UV"
displace.uv_layer = "UV"
displace.strength = RELIEF
displace.mid_level = 0.5

material = bpy.data.materials.new("paper")
material.use_nodes = True
nodes, links = material.node_tree.nodes, material.node_tree.links
bsdf = nodes["Principled BSDF"]
bsdf.inputs["Roughness"].default_value = 0.92
bsdf.inputs["Specular IOR Level"].default_value = 0.25
bsdf.inputs["Sheen Weight"].default_value = 0.3
bsdf.inputs["Sheen Roughness"].default_value = 0.6
coords = nodes.new("ShaderNodeUVMap")
coords.uv_map = "UV"
colour = nodes.new("ShaderNodeTexImage")
colour.image = albedo
colour.extension = "REPEAT"
relief = nodes.new("ShaderNodeTexImage")
relief.image = height
relief.extension = "REPEAT"
relief.interpolation = "Cubic"
bump = nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.35
bump.inputs["Distance"].default_value = RELIEF
links.new(coords.outputs["UV"], colour.inputs["Vector"])
links.new(coords.outputs["UV"], relief.inputs["Vector"])
links.new(colour.outputs["Color"], bsdf.inputs["Base Color"])
links.new(relief.outputs["Color"], bump.inputs["Height"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
sheet.data.materials.append(material)

# A low lamp from the top left, and a dim even sky to fill the shadows.
bpy.ops.object.light_add(type="SUN", rotation=(1.2, 0, 2.3))
sun = bpy.context.object
sun.data.energy = 3.2
sun.data.angle = 0.06
world = bpy.data.worlds.new("sky")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45

bpy.ops.object.camera_add(location=(0, 0, 2), rotation=(0, 0, 0))
camera = bpy.context.object
camera.data.type = "ORTHO"
camera.data.ortho_scale = 1
scene.camera = camera

scene.render.filepath = out
bpy.ops.render.render(write_still=True)
