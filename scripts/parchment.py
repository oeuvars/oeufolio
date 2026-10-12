"""Render the parchment page textures used by the site.

Run: blender -b -P scripts/parchment.py -- <output.png> [width height samples [color|height]]

color  lit parchment colour map (public/parchment.jpg)
height grayscale relief map of the paper fibres (public/paper-height.jpg),
       used by the browser to light the paper from the cursor
"""

import math
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
out_path = argv[0] if argv else "/tmp/parchment.png"
res_x = int(argv[1]) if len(argv) > 1 else 2560
res_y = int(argv[2]) if len(argv) > 2 else 1600
samples = int(argv[3]) if len(argv) > 3 else 96
mode = argv[4] if len(argv) > 4 else "color"

PAGE_W = 3.2
PAGE_H = PAGE_W * res_y / res_x

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- geometry
bpy.ops.mesh.primitive_plane_add(size=1)
page = bpy.context.active_object
page.scale = (PAGE_W, PAGE_H, 1)
bpy.ops.object.transform_apply(scale=True)

# ---------------------------------------------------------------- material
mat = bpy.data.materials.new("Parchment")
try:
    mat.use_nodes = True
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


def math_node(x, y, op, a=None, b=None, clamp=False):
    m = node("ShaderNodeMath", x, y, operation=op, use_clamp=clamp)
    if a is not None:
        m.inputs[0].default_value = a
    if b is not None:
        m.inputs[1].default_value = b
    return m


coord = node("ShaderNodeTexCoord", -2400, 0)
out = node("ShaderNodeOutputMaterial", 1800, 0)
bsdf = node("ShaderNodeBsdfPrincipled", 1500, 0)
bsdf.inputs["Roughness"].default_value = 0.82
try:
    bsdf.inputs["Specular IOR Level"].default_value = 0.18
except KeyError:
    pass
link(bsdf, "BSDF", out, "Surface")

# object-space coordinates, centred on the page
sep = node("ShaderNodeSeparateXYZ", -2200, 0)
link(coord, "Object", sep, "Vector")

# --- paper body: low-frequency tonal variation
tone_noise = node("ShaderNodeTexNoise", -1900, 600)
tone_noise.inputs["Scale"].default_value = 1.3
tone_noise.inputs["Detail"].default_value = 9
tone_noise.inputs["Roughness"].default_value = 0.62
link(coord, "Object", tone_noise, "Vector")
tone = ramp(
    -1650,
    600,
    [
        (0.0, (0.74, 0.66, 0.5, 1)),
        (0.45, (0.87, 0.81, 0.66, 1)),
        (1.0, (0.94, 0.9, 0.78, 1)),
    ],
)
link(tone_noise, "Fac", tone, "Fac")

# --- mottled blotches (darker patches)
blot_noise = node("ShaderNodeTexNoise", -1900, 250)
blot_noise.inputs["Scale"].default_value = 3.4
blot_noise.inputs["Detail"].default_value = 6
blot_noise.inputs["Roughness"].default_value = 0.7
blot_noise.inputs["Distortion"].default_value = 0.6
link(coord, "Object", blot_noise, "Vector")
blot_mask = ramp(-1650, 250, [(0.46, (1, 1, 1, 1)), (0.72, (0.8, 0.72, 0.58, 1))])
link(blot_noise, "Fac", blot_mask, "Fac")
base_mix = mix(-1400, 450, "MULTIPLY", 0.35)
link(tone, "Color", base_mix, "Color1")
link(blot_mask, "Color", base_mix, "Color2")

# --- water ring stains
ring_map = node("ShaderNodeMapping", -2000, -150)
ring_map.inputs["Location"].default_value = (0.65, -0.1, 0)
link(coord, "Object", ring_map, "Vector")
rings = node("ShaderNodeTexWave", -1800, -150, wave_type="RINGS", rings_direction="SPHERICAL")
rings.inputs["Scale"].default_value = 1.15
rings.inputs["Distortion"].default_value = 9
rings.inputs["Detail"].default_value = 4
rings.inputs["Detail Scale"].default_value = 1.4
link(ring_map, "Vector", rings, "Vector")
ring_ramp = ramp(
    -1550,
    -150,
    [(0.0, (1, 1, 1, 1)), (0.72, (1, 1, 1, 1)), (0.78, (0.7, 0.58, 0.4, 1)), (0.84, (1, 1, 1, 1))],
)
link(rings, "Color", ring_ramp, "Fac")
ring_mix = mix(-1250, 300, "MULTIPLY", 0.0)
link(base_mix, "Color", ring_mix, "Color1")
link(ring_ramp, "Color", ring_mix, "Color2")

# --- foxing: small brown flecks clustered by a mask
fox_vor = node("ShaderNodeTexVoronoi", -1900, -550)
fox_vor.inputs["Scale"].default_value = 55
fox_vor.inputs["Randomness"].default_value = 1.0
link(coord, "Object", fox_vor, "Vector")
fox_cluster = node("ShaderNodeTexNoise", -1900, -800)
fox_cluster.inputs["Scale"].default_value = 2.2
fox_cluster.inputs["Detail"].default_value = 3
link(coord, "Object", fox_cluster, "Vector")
fox_cluster_ramp = ramp(-1650, -800, [(0.5, (0, 0, 0, 1)), (0.68, (1, 1, 1, 1))])
link(fox_cluster, "Fac", fox_cluster_ramp, "Fac")
fox_spots = ramp(-1650, -550, [(0.0, (0.35, 0.18, 0.06, 1)), (0.11, (0.35, 0.18, 0.06, 1)), (0.2, (1, 1, 1, 1))])
link(fox_vor, "Distance", fox_spots, "Fac")
fox_gate = mix(-1400, -650, "ADD", 1.0)
link(fox_spots, "Color", fox_gate, "Color1")
fox_gate.inputs["Color2"].default_value = (0, 0, 0, 1)
fox_fac = node("ShaderNodeMath", -1400, -820, operation="MULTIPLY")
link(fox_cluster_ramp, "Color", fox_fac, 0)
fox_fac.inputs[1].default_value = 0.45
fox_mix = mix(-1000, 250, "MULTIPLY", 1.0)
link(fox_fac, "Value", fox_mix, "Fac")
link(ring_mix, "Color", fox_mix, "Color1")
link(fox_spots, "Color", fox_mix, "Color2")

# --- folds / creases: distorted bands
crease_map = node("ShaderNodeMapping", -2000, -1100)
crease_map.inputs["Rotation"].default_value = (0, 0, math.radians(24))
link(coord, "Object", crease_map, "Vector")
creases = node("ShaderNodeTexWave", -1800, -1100, wave_type="BANDS")
creases.inputs["Scale"].default_value = 0.3
creases.inputs["Distortion"].default_value = 0.9
creases.inputs["Detail"].default_value = 2
creases.inputs["Detail Scale"].default_value = 1.8
link(crease_map, "Vector", creases, "Vector")
crease_line = ramp(-1550, -1100, [(0.0, (0, 0, 0, 1)), (0.485, (0, 0, 0, 1)), (0.5, (1, 1, 1, 1)), (0.515, (0, 0, 0, 1)), (1.0, (0, 0, 0, 1))])
link(creases, "Fac", crease_line, "Fac")
crease_dark = ramp(-1250, -1100, [(0.0, (1, 1, 1, 1)), (1.0, (0.78, 0.66, 0.46, 1))])
link(crease_line, "Color", crease_dark, "Fac")
crease_mix = mix(-700, 250, "MULTIPLY", 0.0)
link(fox_mix, "Color", crease_mix, "Color1")
link(crease_dark, "Color", crease_mix, "Color2")

# --- darkened, burnt edges (irregular)
ax = math_node(-2000, 1100, "ABSOLUTE")
link(sep, "X", ax, 0)
ay = math_node(-2000, 1000, "ABSOLUTE")
link(sep, "Y", ay, 0)
nx = math_node(-1800, 1100, "DIVIDE", b=PAGE_W / 2)
link(ax, "Value", nx, 0)
ny = math_node(-1800, 1000, "DIVIDE", b=PAGE_H / 2)
link(ay, "Value", ny, 0)
dist = math_node(-1600, 1050, "MAXIMUM")
link(nx, "Value", dist, 0)
link(ny, "Value", dist, 1)
edge_noise = node("ShaderNodeTexNoise", -1800, 900)
edge_noise.inputs["Scale"].default_value = 5.5
edge_noise.inputs["Detail"].default_value = 8
edge_noise.inputs["Roughness"].default_value = 0.7
link(coord, "Object", edge_noise, "Vector")
edge_jit = math_node(-1400, 1000, "MULTIPLY_ADD")
link(edge_noise, "Fac", edge_jit, 0)
edge_jit.inputs[1].default_value = 0.22
link(dist, "Value", edge_jit, 2)
edge_range = node("ShaderNodeMapRange", -1200, 1000)
edge_range.inputs["From Min"].default_value = 0.8
edge_range.inputs["From Max"].default_value = 1.12
edge_range.inputs["To Min"].default_value = 0.0
edge_range.inputs["To Max"].default_value = 1.0
edge_range.clamp = True
link(edge_jit, "Value", edge_range, "Value")
edge_color = ramp(-1000, 1000, [(0.0, (1, 1, 1, 1)), (0.55, (0.88, 0.8, 0.64, 1)), (1.0, (0.55, 0.42, 0.26, 1))])
link(edge_range, "Result", edge_color, "Fac")
edge_mix = mix(-400, 250, "MULTIPLY", 1.0)
link(crease_mix, "Color", edge_mix, "Color1")
link(edge_color, "Color", edge_mix, "Color2")

# --- fibres: two stretched noise layers feed bump + faint colour variation
mapping_a = node("ShaderNodeMapping", -2000, -1500)
mapping_a.inputs["Scale"].default_value = (140, 14, 1)
link(coord, "Object", mapping_a, "Vector")
fibre_a = node("ShaderNodeTexNoise", -1800, -1500)
fibre_a.inputs["Scale"].default_value = 3.0
fibre_a.inputs["Detail"].default_value = 12
fibre_a.inputs["Roughness"].default_value = 0.65
link(mapping_a, "Vector", fibre_a, "Vector")
mapping_b = node("ShaderNodeMapping", -2000, -1800)
mapping_b.inputs["Rotation"].default_value = (0, 0, math.radians(63))
mapping_b.inputs["Scale"].default_value = (110, 12, 1)
link(coord, "Object", mapping_b, "Vector")
fibre_b = node("ShaderNodeTexNoise", -1800, -1800)
fibre_b.inputs["Scale"].default_value = 3.0
fibre_b.inputs["Detail"].default_value = 12
link(mapping_b, "Vector", fibre_b, "Vector")
grain = node("ShaderNodeTexNoise", -1800, -2100)
grain.inputs["Scale"].default_value = 900
grain.inputs["Detail"].default_value = 4
link(coord, "Object", grain, "Vector")

fibre_sum = mix(-1450, -1650, "ADD", 0.5)
link(fibre_a, "Fac", fibre_sum, "Color1")
link(fibre_b, "Fac", fibre_sum, "Color2")
bump_height = mix(-1200, -1750, "ADD", 0.35)
link(fibre_sum, "Color", bump_height, "Color1")
link(grain, "Fac", bump_height, "Color2")
crease_height = mix(-950, -1650, "ADD", 0.0)
link(bump_height, "Color", crease_height, "Color1")
link(crease_line, "Color", crease_height, "Color2")

bump = node("ShaderNodeBump", 1000, -300)
bump.inputs["Strength"].default_value = 0.9
bump.inputs["Distance"].default_value = 0.02
link(crease_height, "Color", bump, "Height")
link(bump, "Normal", bsdf, "Normal")

fibre_tint = ramp(-1000, -1450, [(0.3, (0.9, 0.86, 0.78, 1)), (0.7, (1, 1, 1, 1))])
link(fibre_sum, "Color", fibre_tint, "Fac")
final_mix = mix(300, 200, "MULTIPLY", 1.0)
link(edge_mix, "Color", final_mix, "Color1")
link(fibre_tint, "Color", final_mix, "Color2")
link(final_mix, "Color", bsdf, "Base Color")

# subtle translucency so light bleeds through thin patches
for name in ("Subsurface Weight",):
    if name in bsdf.inputs:
        bsdf.inputs[name].default_value = 0.08

if mode == "height":
    def remap(src, x, y):
        m = node("ShaderNodeMapRange", x, y)
        m.inputs["From Min"].default_value = 0.3
        m.inputs["From Max"].default_value = 0.7
        m.clamp = True
        link(src, "Fac", m, "Value")
        return m

    a = remap(fibre_a, -800, -2400)
    b = remap(fibre_b, -800, -2600)
    g = remap(grain, -800, -2800)
    wa = math_node(-600, -2400, "MULTIPLY", b=0.45)
    link(a, "Result", wa, 0)
    wb = math_node(-600, -2600, "MULTIPLY", b=0.35)
    link(b, "Result", wb, 0)
    wg = math_node(-600, -2800, "MULTIPLY", b=0.2)
    link(g, "Result", wg, 0)
    s1 = math_node(-400, -2500, "ADD")
    link(wa, "Value", s1, 0)
    link(wb, "Value", s1, 1)
    s2 = math_node(-200, -2600, "ADD")
    link(s1, "Value", s2, 0)
    link(wg, "Value", s2, 1)
    em = node("ShaderNodeEmission", 1000, 400)
    link(s2, "Value", em, "Color")
    for existing in list(out.inputs["Surface"].links):
        L.remove(existing)
    link(em, "Emission", out, "Surface")

page.data.materials.append(mat)

# ---------------------------------------------------------------- light + camera
cam_data = bpy.data.cameras.new("Cam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = PAGE_W
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = (0, 0, 4)
scene.collection.objects.link(cam)
scene.camera = cam

sun_data = bpy.data.lights.new("Raking", "SUN")
sun_data.energy = 2.6
sun_data.angle = math.radians(6)
sun_data.color = (1.0, 0.93, 0.8)
sun = bpy.data.objects.new("Raking", sun_data)
sun.rotation_euler = (math.radians(68), math.radians(8), math.radians(-38))
scene.collection.objects.link(sun)

fill_data = bpy.data.lights.new("Fill", "AREA")
fill_data.energy = 220
fill_data.size = 6
fill = bpy.data.objects.new("Fill", fill_data)
fill.location = (0, 0, 3.4)
scene.collection.objects.link(fill)

world = bpy.data.worlds.new("World")
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.9, 0.82, 0.68, 1)
    bg.inputs["Strength"].default_value = 0.35

# ---------------------------------------------------------------- render
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = samples
scene.cycles.use_denoising = mode != "height"
scene.render.resolution_x = res_x
scene.render.resolution_y = res_y
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.3
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.filepath = out_path
bpy.ops.render.render(write_still=True)
print("WROTE", out_path)
