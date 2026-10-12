"""Render crocodile-embossed leather used as the site background.

Run: blender -b -P scripts/leather.py -- <output.png> [width height samples [color|height [palette]]]

color  lit leather colour map (public/leather.jpg), true displaced geometry
height grayscale relief map (public/leather-height.jpg), used by the browser
       to light the surface from the cursor
palette: green (default), yellow, oxblood
"""

import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
out_path = argv[0] if argv else "/tmp/leather.png"
res_x = int(argv[1]) if len(argv) > 1 else 2560
res_y = int(argv[2]) if len(argv) > 2 else 1600
samples = int(argv[3]) if len(argv) > 3 else 96
mode = argv[4] if len(argv) > 4 else "color"
palette_name = argv[5] if len(argv) > 5 else "green"

# Colours are linear RGB.
PALETTES = {
    "green": {
        "tone": [(0.0, (0.004, 0.07, 0.034, 1)), (0.5, (0.008, 0.12, 0.058, 1)), (1.0, (0.018, 0.19, 0.095, 1))],
        "seam": (0.0008, 0.016, 0.008, 1),
        "edge": (0.42, 0.48, 0.42, 1),
        "pit": (0.2, 0.3, 0.22, 1),
    },
    "yellow": {
        "tone": [(0.0, (0.86, 0.6, 0.03, 1)), (0.5, (0.96, 0.75, 0.07, 1)), (1.0, (1.0, 0.88, 0.2, 1))],
        "seam": (0.3, 0.17, 0.01, 1),
        "edge": (0.55, 0.4, 0.14, 1),
        "pit": (0.5, 0.35, 0.05, 1),
    },
    "oxblood": {
        "tone": [(0.0, (0.07, 0.006, 0.008, 1)), (0.5, (0.12, 0.01, 0.012, 1)), (1.0, (0.2, 0.018, 0.02, 1))],
        "seam": (0.012, 0.001, 0.001, 1),
        "edge": (0.4, 0.34, 0.34, 1),
        "pit": (0.4, 0.2, 0.2, 1),
    },
}
PALETTE = PALETTES[palette_name]

PAGE_W = 3.2
PAGE_H = PAGE_W * res_y / res_x
SCALE_X = 4.1  # scales per unit, horizontal (wider than tall, like belly scales)
SCALE_Y = 5.5
CAM_Z = 4.2

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- geometry
if mode == "height":
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=2, y_subdivisions=2, size=1)
else:
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=1500, y_subdivisions=int(1500 * res_y / res_x), size=1)
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
N = nt.nodes
L = nt.links


def node(kind, x, y, **props):
    n = N.new(kind)
    n.location = (x, y)
    for key, value in props.items():
        setattr(n, key, value)
    return n


def link(a, a_out, b, b_in):
    L.new(a.outputs[a_out], b.inputs[b_in])


def math_node(x, y, op, a=None, b=None, clamp=False):
    m = node("ShaderNodeMath", x, y, operation=op, use_clamp=clamp)
    if a is not None:
        m.inputs[0].default_value = a
    if b is not None:
        m.inputs[1].default_value = b
    return m


def map_range(x, y, src, out_name, lo, hi, to_lo, to_hi, smooth=False):
    m = node("ShaderNodeMapRange", x, y)
    m.clamp = True
    if smooth:
        m.interpolation_type = "SMOOTHSTEP"
    m.inputs["From Min"].default_value = lo
    m.inputs["From Max"].default_value = hi
    m.inputs["To Min"].default_value = to_lo
    m.inputs["To Max"].default_value = to_hi
    link(src, out_name, m, "Value")
    return m


def ramp(x, y, stops):
    r = node("ShaderNodeValToRGB", x, y)
    r.color_ramp.elements[0].position = stops[0][0]
    r.color_ramp.elements[0].color = stops[0][1]
    r.color_ramp.elements[1].position = stops[-1][0]
    r.color_ramp.elements[1].color = stops[-1][1]
    for pos, col in stops[1:-1]:
        e = r.color_ramp.elements.new(pos)
        e.color = col
    return r


def mix(x, y, blend, fac=1.0):
    m = node("ShaderNodeMixRGB", x, y, blend_type=blend)
    m.inputs["Fac"].default_value = fac
    return m


def vmath(x, y, op):
    return node("ShaderNodeVectorMath", x, y, operation=op)


coord = node("ShaderNodeTexCoord", -3000, 0)
out = node("ShaderNodeOutputMaterial", 2600, 0)
bsdf = node("ShaderNodeBsdfPrincipled", 2300, 0)
link(bsdf, "BSDF", out, "Surface")

# --- scale grid: voronoi cells wobbled by a low-frequency warp
mapping = node("ShaderNodeMapping", -2800, 0)
mapping.inputs["Scale"].default_value = (SCALE_X, SCALE_Y, 1)
link(coord, "Object", mapping, "Vector")

warp = node("ShaderNodeTexNoise", -2800, -300)
warp.inputs["Scale"].default_value = 1.3
warp.inputs["Detail"].default_value = 2
link(coord, "Object", warp, "Vector")
warp_offset = vmath(-2600, -300, "MULTIPLY_ADD")
warp_offset.inputs[1].default_value = (0.32, 0.4, 0.0)
warp_offset.inputs[2].default_value = (-0.16, -0.2, 0.0)
link(warp, "Color", warp_offset, 0)
warped = vmath(-2400, -100, "ADD")
link(mapping, "Vector", warped, 0)
link(warp_offset, "Vector", warped, 1)

cells = node("ShaderNodeTexVoronoi", -2200, 300, feature="F1")
cells.inputs["Scale"].default_value = 1.0
cells.inputs["Randomness"].default_value = 0.26
link(warped, "Vector", cells, "Vector")
edges = node("ShaderNodeTexVoronoi", -2200, -50, feature="DISTANCE_TO_EDGE")
edges.inputs["Scale"].default_value = 1.0
edges.inputs["Randomness"].default_value = 0.26
link(warped, "Vector", edges, "Vector")

rand = node("ShaderNodeSeparateXYZ", -2000, 500)  # per-scale random values
link(cells, "Color", rand, "Vector")

# vector from the fragment to its scale centre, used to tilt each scale a little
to_center = vmath(-2000, 250, "SUBTRACT")
link(warped, "Vector", to_center, 0)
link(cells, "Position", to_center, 1)
tc = node("ShaderNodeSeparateXYZ", -1800, 250)
link(to_center, "Vector", tc, "Vector")
rx = math_node(-1800, 450, "SUBTRACT", b=0.5)
link(rand, "X", rx, 0)
ry = math_node(-1800, 550, "SUBTRACT", b=0.5)
link(rand, "Y", ry, 0)
tx = math_node(-1600, 350, "MULTIPLY")
link(tc, "X", tx, 0)
link(rx, "Value", tx, 1)
ty = math_node(-1600, 250, "MULTIPLY")
link(tc, "Y", ty, 0)
link(ry, "Value", ty, 1)
tilt_sum = math_node(-1400, 300, "ADD")
link(tx, "Value", tilt_sum, 0)
link(ty, "Value", tilt_sum, 1)
tilt = math_node(-1200, 300, "MULTIPLY", b=0.22, clamp=False)
link(tilt_sum, "Value", tilt, 0)

# rounded shoulders on every scale: flat plateau, soft drop into the seam
shoulder_lin = map_range(-1800, -50, edges, "Distance", 0.0, 0.07, 0.0, 1.0)
shoulder_pi = math_node(-1700, -50, "MULTIPLY", b=math.pi / 2)
link(shoulder_lin, "Result", shoulder_pi, 0)
shoulder = math_node(-1600, -50, "SINE", clamp=True)
link(shoulder_pi, "Value", shoulder, 0)
seam_mask = map_range(-1800, -250, edges, "Distance", 0.0, 0.035, 0.0, 1.0, smooth=True)
dome = map_range(-1800, 700, cells, "Distance", 0.0, 0.62, 1.0, 0.0, smooth=True)

# per-scale height: base + random + gentle dome + tilt
h_rand = math_node(-1400, 600, "MULTIPLY", b=0.14)
link(rand, "Z", h_rand, 0)
h_dome = math_node(-1400, 700, "MULTIPLY", b=0.55)
link(dome, "Result", h_dome, 0)
h1 = math_node(-1200, 650, "ADD")
link(h_rand, "Value", h1, 0)
link(h_dome, "Value", h1, 1)
h2 = math_node(-1000, 600, "ADD", b=0.3)
link(h1, "Value", h2, 0)
h3 = math_node(-800, 500, "ADD")
link(h2, "Value", h3, 0)
link(tilt, "Value", h3, 1)
plateau = math_node(-600, 400, "MULTIPLY")
link(h3, "Value", plateau, 0)
link(shoulder, "Value", plateau, 1)

# dimples (pores) on the scales
pits = node("ShaderNodeTexVoronoi", -2200, -700, feature="F1")
pits.inputs["Scale"].default_value = 30
pits.inputs["Randomness"].default_value = 1.0
link(coord, "Object", pits, "Vector")
pit_shape = map_range(-1800, -700, pits, "Distance", 0.0, 0.11, 1.0, 0.0, smooth=True)
pit_gate = math_node(-1500, -700, "GREATER_THAN", b=0.28)
link(rand, "Z", pit_gate, 0)
pit_on = math_node(-1300, -700, "MULTIPLY")
link(pit_shape, "Result", pit_on, 0)
link(pit_gate, "Value", pit_on, 1)
pit_on_scale = math_node(-1100, -700, "MULTIPLY")
link(pit_on, "Value", pit_on_scale, 0)
link(shoulder, "Value", pit_on_scale, 1)
pit_depth = math_node(-900, -700, "MULTIPLY", b=0.16)
link(pit_on_scale, "Value", pit_depth, 0)

macro_base = math_node(-450, 100, "SUBTRACT")
link(plateau, "Value", macro_base, 0)
link(pit_depth, "Value", macro_base, 1)
wave = node("ShaderNodeTexNoise", -900, 300)
wave.inputs["Scale"].default_value = 0.85
wave.inputs["Detail"].default_value = 3
link(coord, "Object", wave, "Vector")
wave_amp = math_node(-700, 300, "MULTIPLY", b=0.55)
link(wave, "Fac", wave_amp, 0)
macro = math_node(-300, 100, "ADD", clamp=False)
link(macro_base, "Value", macro, 0)
link(wave_amp, "Value", macro, 1)

# hairline wrinkles inside each scale
wrinkles = node("ShaderNodeTexVoronoi", -2200, -1650, feature="DISTANCE_TO_EDGE")
wrinkles.inputs["Scale"].default_value = 95
wrinkles.inputs["Randomness"].default_value = 1.0
link(coord, "Object", wrinkles, "Vector")
wrinkle_lines = map_range(-1800, -1650, wrinkles, "Distance", 0.0, 0.07, 0.0, 1.0, smooth=True)

# fine grain and fine creases, handled by bump (finer than the mesh)
grain = node("ShaderNodeTexNoise", -2200, -1100)
grain.inputs["Scale"].default_value = 420
grain.inputs["Detail"].default_value = 8
grain.inputs["Roughness"].default_value = 0.6
link(coord, "Object", grain, "Vector")
creases = node("ShaderNodeTexNoise", -2200, -1350)
creases.inputs["Scale"].default_value = 70
creases.inputs["Detail"].default_value = 5
creases.inputs["Distortion"].default_value = 1.6
link(coord, "Object", creases, "Vector")
micro_a = math_node(-1800, -1100, "MULTIPLY", b=0.6)
link(grain, "Fac", micro_a, 0)
micro_b = math_node(-1800, -1350, "MULTIPLY", b=0.4)
link(creases, "Fac", micro_b, 0)
micro_ab = math_node(-1650, -1250, "ADD")
link(micro_a, "Value", micro_ab, 0)
link(micro_b, "Value", micro_ab, 1)
micro_w = math_node(-1650, -1650, "MULTIPLY", b=0.45)
link(wrinkle_lines, "Result", micro_w, 0)
micro = math_node(-1500, -1300, "ADD")
link(micro_ab, "Value", micro, 0)
link(micro_w, "Value", micro, 1)
micro_on_scales = math_node(-1300, -1200, "MULTIPLY")
link(micro, "Value", micro_on_scales, 0)
link(shoulder, "Value", micro_on_scales, 1)

# --- colour
mottle = node("ShaderNodeTexNoise", -1800, 1250)
mottle.inputs["Scale"].default_value = 1.6
mottle.inputs["Detail"].default_value = 5
link(coord, "Object", mottle, "Vector")
mottle_tint = ramp(-1500, 1250, [(0.3, (0.6, 0.7, 0.62, 1)), (0.7, (1.2, 1.25, 1.2, 1))])
link(mottle, "Fac", mottle_tint, "Fac")
tone = ramp(-1800, 1000, PALETTE["tone"])
link(rand, "X", tone, "Fac")
seam_color = mix(-1000, 1000, "MIX")
seam_color.inputs["Color1"].default_value = PALETTE["seam"]
link(seam_mask, "Result", seam_color, "Fac")
link(tone, "Color", seam_color, "Color2")

top_wear = ramp(-1500, 850, [(0.0, (0.55, 0.55, 0.55, 1)), (0.55, (0.95, 0.95, 0.95, 1)), (1.0, (1.35, 1.35, 1.35, 1))])
link(dome, "Result", top_wear, "Fac")
worn = mix(-700, 1000, "MULTIPLY", 1.0)
link(seam_color, "Color", worn, "Color1")
link(top_wear, "Color", worn, "Color2")

pit_tint = ramp(-1300, -500, [(0.0, (1, 1, 1, 1)), (1.0, PALETTE["pit"])])
link(pit_on_scale, "Value", pit_tint, "Fac")
pitted = mix(-400, 1000, "MULTIPLY", 1.0)
link(worn, "Color", pitted, "Color1")
link(pit_tint, "Color", pitted, "Color2")

grain_tint = ramp(-1500, -1450, [(0.3, (0.88, 0.88, 0.88, 1)), (0.7, (1, 1, 1, 1))])
link(grain, "Fac", grain_tint, "Fac")
grained = mix(-100, 1000, "MULTIPLY", 1.0)
link(pitted, "Color", grained, "Color1")
link(grain_tint, "Color", grained, "Color2")

sep = node("ShaderNodeSeparateXYZ", -2800, 1400)
link(coord, "Object", sep, "Vector")
ax = math_node(-2600, 1400, "ABSOLUTE")
link(sep, "X", ax, 0)
ay = math_node(-2600, 1500, "ABSOLUTE")
link(sep, "Y", ay, 0)
nx = math_node(-2400, 1400, "DIVIDE", b=PAGE_W / 2)
link(ax, "Value", nx, 0)
ny = math_node(-2400, 1500, "DIVIDE", b=PAGE_H / 2)
link(ay, "Value", ny, 0)
dist = math_node(-2200, 1450, "MAXIMUM")
link(nx, "Value", dist, 0)
link(ny, "Value", dist, 1)
edge_range = map_range(-2000, 1450, dist, "Value", 0.8, 1.18, 0.0, 1.0)
edge_color = ramp(-1800, 1450, [(0.0, (1, 1, 1, 1)), (1.0, PALETTE["edge"])])
link(edge_range, "Result", edge_color, "Fac")
mottled = mix(0, 1250, "MULTIPLY", 1.0)
link(grained, "Color", mottled, "Color1")
link(mottle_tint, "Color", mottled, "Color2")
vignette = mix(200, 1000, "MULTIPLY", 1.0)
link(mottled, "Color", vignette, "Color1")
link(edge_color, "Color", vignette, "Color2")
link(vignette, "Color", bsdf, "Base Color")

# --- finish: semi-gloss varnish, duller in the seams
rough_scale = map_range(1400, -300, seam_mask, "Result", 0.0, 1.0, 0.55, 0.36)
rough_noise = node("ShaderNodeTexNoise", 1400, -600)
rough_noise.inputs["Scale"].default_value = 24
rough_noise.inputs["Detail"].default_value = 4
link(coord, "Object", rough_noise, "Vector")
rough_var = math_node(1650, -450, "MULTIPLY_ADD", b=0.2)
link(rough_noise, "Fac", rough_var, 0)
rough_var.inputs[2].default_value = -0.1
rough_sum = math_node(1900, -400, "ADD", clamp=True)
link(rough_scale, "Result", rough_sum, 0)
link(rough_var, "Value", rough_sum, 1)
link(rough_sum, "Value", bsdf, "Roughness")
try:
    bsdf.inputs["Specular IOR Level"].default_value = 0.4
except KeyError:
    pass
for name, value in (("Coat Weight", 0.34), ("Coat Roughness", 0.17), ("Sheen Weight", 0.08)):
    if name in bsdf.inputs:
        bsdf.inputs[name].default_value = value

height_total = math_node(-100, -200, "ADD")
link(macro, "Value", height_total, 0)
micro_small = math_node(-300, -1100, "MULTIPLY", b=0.05)
link(micro_on_scales, "Value", micro_small, 0)
link(micro_small, "Value", height_total, 1)

bump = node("ShaderNodeBump", 1900, -900)
bump.inputs["Strength"].default_value = 1.5
bump.inputs["Distance"].default_value = 0.004
link(micro_on_scales, "Value", bump, "Height")

if mode == "height":
    em = node("ShaderNodeEmission", 2300, 600)
    link(height_total, "Value", em, "Color")
    for existing in list(out.inputs["Surface"].links):
        L.remove(existing)
    link(em, "Emission", out, "Surface")
else:
    disp = node("ShaderNodeDisplacement", 2300, -500)
    disp.inputs["Midlevel"].default_value = 0.3
    disp.inputs["Scale"].default_value = 0.022
    link(macro, "Value", disp, "Height")
    link(disp, "Displacement", out, "Displacement")
    link(bump, "Normal", bsdf, "Normal")

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
key_data.color = (1.0, 0.96, 0.9)
key = bpy.data.objects.new("Softbox", key_data)
key.location = (-3.0, 2.2, 2.6)
scene.collection.objects.link(key)
aim(key)

rim_data = bpy.data.lights.new("Rim", "AREA")
rim_data.size = 3.0
rim_data.energy = 50
rim_data.color = (0.9, 0.95, 1.0)
rim = bpy.data.objects.new("Rim", rim_data)
rim.location = (3.2, -1.8, 2.2)
scene.collection.objects.link(rim)
aim(rim)

strip_data = bpy.data.lights.new("Strip", "AREA")
strip_data.shape = "RECTANGLE"
strip_data.size = 0.5
strip_data.size_y = 3.4
strip_data.energy = 90
strip = bpy.data.objects.new("Strip", strip_data)
strip.location = (-1.2, -2.9, 2.2)
scene.collection.objects.link(strip)
aim(strip)

top_data = bpy.data.lights.new("Top", "AREA")
top_data.size = 1.6
top_data.energy = 70
top = bpy.data.objects.new("Top", top_data)
top.location = (0.4, 0.8, 3.0)
scene.collection.objects.link(top)
aim(top)

world = bpy.data.worlds.new("World")
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.8, 0.82, 0.8, 1)
    bg.inputs["Strength"].default_value = 0.18

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
