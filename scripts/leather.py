"""Render the leather background from a PBR texture set.

Run: blender -b -P scripts/leather.py -- <output.png> [width height samples [color|height [set]]]

color  lit leather colour map (public/leather.jpg)
height grayscale relief map (public/leather-height.jpg), used by the browser
       to light the surface from the cursor
set    Leather030 (dark brown hide, default) or Leather037 (red-brown fine grain)

The texture sets live in scripts/assets and were made by ambientCG (CC0).
"""

import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
out_path = argv[0] if argv else "/tmp/leather.png"
res_x = int(argv[1]) if len(argv) > 1 else 2560
res_y = int(argv[2]) if len(argv) > 2 else 1600
samples = int(argv[3]) if len(argv) > 3 else 96
mode = argv[4] if len(argv) > 4 else "color"
set_name = argv[5] if len(argv) > 5 else "Leather030"

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets", set_name)

PAGE_W = 3.2
PAGE_H = PAGE_W * res_y / res_x
TILES_X = 2.4  # how many times the texture repeats across the page
NORMAL_STRENGTH = 0.85  # keep the grain shallow so text stays readable
DISPLACE = 0.0035
CAM_Z = 4.2

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- geometry
if mode == "height":
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=2, y_subdivisions=2, size=1)
else:
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=1400, y_subdivisions=int(1400 * res_y / res_x), size=1)
page = bpy.context.active_object
page.scale = (PAGE_W, PAGE_H, 1)
bpy.ops.object.transform_apply(scale=True)
bpy.ops.object.shade_smooth()

# ---------------------------------------------------------------- material
mat = bpy.data.materials.new("Leather")
try:
    mat.use_nodes = True
except Exception:
    pass
try:
    mat.displacement_method = "BOTH"
except Exception:
    pass
nt = mat.node_tree
nt.nodes.clear()
N, L = nt.nodes, nt.links


def node(kind, x, y, **props):
    n = N.new(kind)
    n.location = (x, y)
    for key, value in props.items():
        setattr(n, key, value)
    return n


def link(a, a_out, b, b_in):
    L.new(a.outputs[a_out], b.inputs[b_in])


def texture(kind, x, y, mapping):
    path = os.path.join(ASSETS, f"{set_name}_1K-JPG_{kind}.jpg")
    img = bpy.data.images.load(path)
    if kind != "Color":
        img.colorspace_settings.name = "Non-Color"
    tex = node("ShaderNodeTexImage", x, y)
    tex.image = img
    tex.interpolation = "Cubic"
    tex.extension = "REPEAT"
    link(mapping, "Vector", tex, "Vector")
    return tex


coord = node("ShaderNodeTexCoord", -1200, 0)
mapping = node("ShaderNodeMapping", -1000, 0)
k = TILES_X / PAGE_W
mapping.inputs["Scale"].default_value = (k, k, 1)
link(coord, "Object", mapping, "Vector")

color = texture("Color", -700, 300, mapping)
rough = texture("Roughness", -700, 0, mapping)
normal_tex = texture("NormalGL", -700, -300, mapping)
disp_tex = texture("Displacement", -700, -600, mapping)

out = node("ShaderNodeOutputMaterial", 1000, 0)
bsdf = node("ShaderNodeBsdfPrincipled", 700, 0)
link(bsdf, "BSDF", out, "Surface")

# darken the edges of the hide a little, like a vignette
sep = node("ShaderNodeSeparateXYZ", -1000, 600)
link(coord, "Object", sep, "Vector")
ax = node("ShaderNodeMath", -800, 600, operation="ABSOLUTE")
link(sep, "X", ax, 0)
ay = node("ShaderNodeMath", -800, 700, operation="ABSOLUTE")
link(sep, "Y", ay, 0)
nx = node("ShaderNodeMath", -600, 600, operation="DIVIDE")
nx.inputs[1].default_value = PAGE_W / 2
link(ax, "Value", nx, 0)
ny = node("ShaderNodeMath", -600, 700, operation="DIVIDE")
ny.inputs[1].default_value = PAGE_H / 2
link(ay, "Value", ny, 0)
dist = node("ShaderNodeMath", -400, 650, operation="MAXIMUM")
link(nx, "Value", dist, 0)
link(ny, "Value", dist, 1)
edge = node("ShaderNodeMapRange", -200, 650)
edge.clamp = True
edge.inputs["From Min"].default_value = 0.78
edge.inputs["From Max"].default_value = 1.2
edge.inputs["To Min"].default_value = 1.0
edge.inputs["To Max"].default_value = 0.45
link(dist, "Value", edge, "Value")
shade = node("ShaderNodeMixRGB", 200, 300, blend_type="MULTIPLY")
shade.inputs["Fac"].default_value = 1.0
link(color, "Color", shade, "Color1")
edge_rgb = node("ShaderNodeCombineColor", 0, 600)
for ch in ("Red", "Green", "Blue"):
    link(edge, "Result", edge_rgb, ch)
link(edge_rgb, "Color", shade, "Color2")
link(shade, "Color", bsdf, "Base Color")

link(rough, "Color", bsdf, "Roughness")
nm = node("ShaderNodeNormalMap", 300, -300)
nm.inputs["Strength"].default_value = NORMAL_STRENGTH
link(normal_tex, "Color", nm, "Color")
link(nm, "Normal", bsdf, "Normal")
try:
    bsdf.inputs["Specular IOR Level"].default_value = 0.5
except KeyError:
    pass

if mode == "height":
    em = node("ShaderNodeEmission", 700, 400)
    link(disp_tex, "Color", em, "Color")
    for existing in list(out.inputs["Surface"].links):
        L.remove(existing)
    link(em, "Emission", out, "Surface")
else:
    disp = node("ShaderNodeDisplacement", 700, -400)
    disp.inputs["Midlevel"].default_value = 0.5
    disp.inputs["Scale"].default_value = DISPLACE
    link(disp_tex, "Color", disp, "Height")
    link(disp, "Displacement", out, "Displacement")

page.data.materials.append(mat)

# ---------------------------------------------------------------- camera + light
cam_data = bpy.data.cameras.new("Cam")
cam_data.sensor_fit = "HORIZONTAL"
cam_data.angle = 2 * math.atan((PAGE_W / 2) / CAM_Z)
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = (0, 0, CAM_Z)
scene.collection.objects.link(cam)
scene.camera = cam


def aim(obj, target=Vector((0, 0, 0))):
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


key_data = bpy.data.lights.new("Softbox", "AREA")
key_data.shape = "RECTANGLE"
key_data.size = 5.0
key_data.size_y = 3.2
key_data.energy = 260
key_data.color = (1.0, 0.9, 0.78)
key = bpy.data.objects.new("Softbox", key_data)
key.location = (-3.0, 2.2, 2.6)
scene.collection.objects.link(key)
aim(key)

fill_data = bpy.data.lights.new("Fill", "AREA")
fill_data.size = 4.0
fill_data.energy = 90
fill = bpy.data.objects.new("Fill", fill_data)
fill.location = (3.0, -1.6, 2.6)
scene.collection.objects.link(fill)
aim(fill)

world = bpy.data.worlds.new("World")
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.95, 0.8, 0.65, 1)
    bg.inputs["Strength"].default_value = 0.25

# ---------------------------------------------------------------- render
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = samples if mode != "height" else 4
scene.cycles.use_denoising = mode != "height"
scene.cycles.max_bounces = 6
scene.render.resolution_x = res_x
scene.render.resolution_y = res_y
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.filepath = out_path
bpy.ops.render.render(write_still=True)
print("WROTE", out_path)
