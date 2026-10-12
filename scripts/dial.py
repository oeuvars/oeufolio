"""Render the brass rotary dial used for navigation.

Run: blender -b -P scripts/dial.py -- <output.png> [size samples]

Transparent PNG, top-down, so the browser can rotate it and overlay the labels.
"""

import math
import sys

import bmesh
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
out_path = argv[0] if argv else "/tmp/dial.png"
size = int(argv[1]) if len(argv) > 1 else 1024
samples = int(argv[2]) if len(argv) > 2 else 96

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def make_material(name):
    mat = bpy.data.materials.new(name)
    try:
        mat.use_nodes = True
    except Exception:
        pass
    mat.node_tree.nodes.clear()
    return mat


def node(nt, kind, x, y, **props):
    n = nt.nodes.new(kind)
    n.location = (x, y)
    for key, value in props.items():
        setattr(n, key, value)
    return n


def link(nt, a, a_out, b, b_in):
    nt.links.new(a.outputs[a_out], b.inputs[b_in])


def brass_material(name, rough=0.3, ticks=False, brushed=True):
    mat = make_material(name)
    nt = mat.node_tree
    out = node(nt, "ShaderNodeOutputMaterial", 1400, 0)
    bsdf = node(nt, "ShaderNodeBsdfPrincipled", 1100, 0)
    link(nt, bsdf, "BSDF", out, "Surface")
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = rough
    for key, value in (("Anisotropic", 0.45),):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = value

    coord = node(nt, "ShaderNodeTexCoord", -1400, 0)
    radial = node(nt, "ShaderNodeVectorMath", -1200, 200, operation="LENGTH")
    link(nt, coord, "Object", radial, 0)

    base = node(nt, "ShaderNodeMixRGB", 600, 200, blend_type="MULTIPLY")
    base.inputs["Fac"].default_value = 1.0
    base.inputs["Color1"].default_value = (0.78, 0.53, 0.13, 1)

    height_sources = []

    if brushed:
        grooves = node(nt, "ShaderNodeTexWave", -900, -200, wave_type="RINGS", rings_direction="SPHERICAL")
        grooves.inputs["Scale"].default_value = 70
        grooves.inputs["Distortion"].default_value = 1.4
        grooves.inputs["Detail"].default_value = 3
        link(nt, coord, "Object", grooves, "Vector")
        noise = node(nt, "ShaderNodeTexNoise", -900, -500)
        noise.inputs["Scale"].default_value = 220
        noise.inputs["Detail"].default_value = 6
        link(nt, coord, "Object", noise, "Vector")
        brush = node(nt, "ShaderNodeMath", -600, -300, operation="ADD")
        scaled_g = node(nt, "ShaderNodeMath", -750, -200, operation="MULTIPLY")
        scaled_g.inputs[1].default_value = 0.35
        link(nt, grooves, "Fac", scaled_g, 0)
        scaled_n = node(nt, "ShaderNodeMath", -750, -500, operation="MULTIPLY")
        scaled_n.inputs[1].default_value = 0.5
        link(nt, noise, "Fac", scaled_n, 0)
        link(nt, scaled_g, "Value", brush, 0)
        link(nt, scaled_n, "Value", brush, 1)
        height_sources.append(brush)

        tint = node(nt, "ShaderNodeValToRGB", -300, 350)
        tint.color_ramp.elements[0].color = (0.8, 0.8, 0.8, 1)
        tint.color_ramp.elements[1].color = (1.1, 1.05, 1.0, 1)
        link(nt, noise, "Fac", tint, "Fac")
        link(nt, tint, "Color", base, "Color2")
    else:
        base.inputs["Color2"].default_value = (1, 1, 1, 1)

    height = None
    if ticks:
        angle = node(nt, "ShaderNodeTexGradient", -1200, -800, gradient_type="RADIAL")
        link(nt, coord, "Object", angle, "Vector")

        def tick_mask(count, width, r_lo, r_hi, y):
            scaled = node(nt, "ShaderNodeMath", -950, y, operation="MULTIPLY")
            scaled.inputs[1].default_value = count
            link(nt, angle, "Fac", scaled, 0)
            fract = node(nt, "ShaderNodeMath", -750, y, operation="FRACT")
            link(nt, scaled, "Value", fract, 0)
            near = node(nt, "ShaderNodeMath", -550, y, operation="SUBTRACT", use_clamp=True)
            near.inputs[0].default_value = 1.0
            # distance to nearest tick (0 at a tick)
            fract2 = node(nt, "ShaderNodeMath", -550, y - 120, operation="SUBTRACT")
            fract2.inputs[0].default_value = 1.0
            link(nt, fract, "Value", fract2, 1)
            nearest = node(nt, "ShaderNodeMath", -350, y, operation="MINIMUM")
            link(nt, fract, "Value", nearest, 0)
            link(nt, fract2, "Value", nearest, 1)
            line = node(nt, "ShaderNodeMapRange", -150, y)
            line.clamp = True
            line.inputs["From Min"].default_value = 0.0
            line.inputs["From Max"].default_value = width
            line.inputs["To Min"].default_value = 1.0
            line.inputs["To Max"].default_value = 0.0
            link(nt, nearest, "Value", line, "Value")
            band = node(nt, "ShaderNodeMapRange", -150, y - 220)
            band.clamp = True
            band.interpolation_type = "STEPPED"
            band.inputs["Steps"].default_value = 1
            band.inputs["From Min"].default_value = r_lo
            band.inputs["From Max"].default_value = r_hi
            link(nt, radial, "Value", band, "Value")
            # band is 0..1 across the radius range; keep only inside using a window
            inside_lo = node(nt, "ShaderNodeMath", 50, y - 220, operation="GREATER_THAN")
            inside_lo.inputs[1].default_value = r_lo
            link(nt, radial, "Value", inside_lo, 0)
            inside_hi = node(nt, "ShaderNodeMath", 50, y - 340, operation="LESS_THAN")
            inside_hi.inputs[1].default_value = r_hi
            link(nt, radial, "Value", inside_hi, 0)
            window = node(nt, "ShaderNodeMath", 250, y - 280, operation="MULTIPLY")
            link(nt, inside_lo, "Value", window, 0)
            link(nt, inside_hi, "Value", window, 1)
            final = node(nt, "ShaderNodeMath", 450, y - 100, operation="MULTIPLY")
            link(nt, line, "Result", final, 0)
            link(nt, window, "Value", final, 1)
            return final

        minor = tick_mask(48, 0.08, 0.80, 0.9, -1000)
        major = tick_mask(4, 0.02, 0.7, 0.9, -1700)
        both = node(nt, "ShaderNodeMath", 700, -1200, operation="MAXIMUM")
        link(nt, minor, "Value", both, 0)
        link(nt, major, "Value", both, 1)

        dark = node(nt, "ShaderNodeValToRGB", 850, -1200)
        dark.color_ramp.elements[0].color = (1, 1, 1, 1)
        dark.color_ramp.elements[1].color = (0.07, 0.045, 0.02, 1)
        link(nt, both, "Value", dark, "Fac")
        engraved = node(nt, "ShaderNodeMixRGB", 900, 200, blend_type="MULTIPLY")
        engraved.inputs["Fac"].default_value = 1.0
        link(nt, base, "Color", engraved, "Color1")
        link(nt, dark, "Color", engraved, "Color2")
        link(nt, engraved, "Color", bsdf, "Base Color")

        neg = node(nt, "ShaderNodeMath", 900, -1000, operation="MULTIPLY")
        neg.inputs[1].default_value = -1.0
        link(nt, both, "Value", neg, 0)
        height_sources.append(neg)
    else:
        link(nt, base, "Color", bsdf, "Base Color")

    if height_sources:
        total = height_sources[0]
        for extra in height_sources[1:]:
            add = node(nt, "ShaderNodeMath", 1000, -400, operation="ADD")
            link(nt, total, "Value", add, 0)
            link(nt, extra, "Value", add, 1)
            total = add
        bump = node(nt, "ShaderNodeBump", 1000, -150)
        bump.inputs["Strength"].default_value = 0.6
        bump.inputs["Distance"].default_value = 0.01
        link(nt, total, "Value", bump, "Height")
        link(nt, bump, "Normal", bsdf, "Normal")
    return mat


# --------------------------------------------------------------- geometry
HEIGHT = 0.16

# knurled outer ring: a gear-like profile, extruded
bm = bmesh.new()
teeth = 120
profile = []
for i in range(teeth * 2):
    a = i * math.pi / teeth
    r = 1.0 if i % 2 == 0 else 0.968
    profile.append(bm.verts.new((r * math.cos(a), r * math.sin(a), 0.0)))
face = bm.faces.new(profile)
res = bmesh.ops.extrude_face_region(bm, geom=[face])
moved = [v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)]
bmesh.ops.translate(bm, verts=moved, vec=Vector((0, 0, HEIGHT)))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
mesh = bpy.data.meshes.new("Knurl")
bm.to_mesh(mesh)
bm.free()
ring = bpy.data.objects.new("Knurl", mesh)
scene.collection.objects.link(ring)
bevel = ring.modifiers.new("Bevel", "BEVEL")
bevel.width = 0.008
bevel.segments = 2
ring.data.materials.append(brass_material("BrassRing", rough=0.26, brushed=False))
bpy.context.view_layer.objects.active = ring
ring.select_set(True)
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))

# a stepped lip inside the ring
bpy.ops.mesh.primitive_cylinder_add(radius=0.93, depth=0.03, vertices=180, location=(0, 0, HEIGHT - 0.025))
lip = bpy.context.active_object
lip.data.materials.append(brass_material("BrassLip", rough=0.22, brushed=False))
lip.modifiers.new("Bevel", "BEVEL").width = 0.012
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))

# engraved face plate
bpy.ops.mesh.primitive_cylinder_add(radius=0.885, depth=0.04, vertices=180, location=(0, 0, HEIGHT - 0.025))
face_obj = bpy.context.active_object
face_obj.data.materials.append(brass_material("BrassFace", rough=0.34, ticks=True))
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))

# centre boss with a screw slot
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.1, vertices=96, location=(0, 0, HEIGHT + 0.01))
boss = bpy.context.active_object
boss.data.materials.append(brass_material("BrassBoss", rough=0.2, brushed=False))
boss.modifiers.new("Bevel", "BEVEL").width = 0.02
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))

slot_mat = make_material("Slot")
snt = slot_mat.node_tree
sout = node(snt, "ShaderNodeOutputMaterial", 300, 0)
sbsdf = node(snt, "ShaderNodeBsdfPrincipled", 0, 0)
sbsdf.inputs["Base Color"].default_value = (0.02, 0.012, 0.005, 1)
sbsdf.inputs["Roughness"].default_value = 0.7
link(snt, sbsdf, "BSDF", sout, "Surface")
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, HEIGHT + 0.066))
slot = bpy.context.active_object
slot.scale = (0.3, 0.032, 0.012)
slot.rotation_euler = (0, 0, math.radians(32))
slot.data.materials.append(slot_mat)

# enamel-filled tick marks and fine rings, built as real geometry
FACE_TOP = HEIGHT - 0.025 + 0.02
for i in range(48):
    a = i * 2 * math.pi / 48
    major = i % 12 == 0
    length = 0.15 if major else 0.065
    width = 0.022 if major else 0.01
    radius = 0.825 if major else 0.845
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(radius * math.cos(a), radius * math.sin(a), FACE_TOP + 0.002),
    )
    tick = bpy.context.active_object
    tick.scale = (length, width, 0.006)
    tick.rotation_euler = (0, 0, a)
    tick.data.materials.append(slot_mat)

for ring_radius, ring_width in ((0.76, 0.006), (0.9, 0.008), (0.32, 0.006)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=ring_radius,
        minor_radius=ring_width,
        major_segments=180,
        minor_segments=10,
        location=(0, 0, FACE_TOP + 0.001),
    )
    groove = bpy.context.active_object
    groove.scale = (1, 1, 0.5)
    groove.data.materials.append(slot_mat)

# --------------------------------------------------------------- camera, light
cam_data = bpy.data.cameras.new("Cam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 2.12
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = (0, 0, 4)
scene.collection.objects.link(cam)
scene.camera = cam


def aim(obj, target=Vector((0, 0, 0))):
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


key_data = bpy.data.lights.new("Key", "AREA")
key_data.size = 3.0
key_data.energy = 200
key_data.color = (1.0, 0.95, 0.85)
key = bpy.data.objects.new("Key", key_data)
key.location = (-1.8, 1.7, 2.6)
scene.collection.objects.link(key)
aim(key)

fill_data = bpy.data.lights.new("Fill", "AREA")
fill_data.size = 2.2
fill_data.energy = 60
fill = bpy.data.objects.new("Fill", fill_data)
fill.location = (2.2, -1.5, 2.0)
scene.collection.objects.link(fill)
aim(fill)

# studio-like environment so the metal has something to reflect
world = bpy.data.worlds.new("World")
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
wnt = world.node_tree
wnt.nodes.clear()
wout = node(wnt, "ShaderNodeOutputWorld", 800, 0)
wbg = node(wnt, "ShaderNodeBackground", 600, 0)
wcoord = node(wnt, "ShaderNodeTexCoord", -600, 0)
wsep = node(wnt, "ShaderNodeSeparateXYZ", -400, 0)
link(wnt, wcoord, "Generated", wsep, "Vector")
wrange = node(wnt, "ShaderNodeMapRange", -200, 0)
wrange.inputs["From Min"].default_value = -0.2
wrange.inputs["From Max"].default_value = 1.0
link(wnt, wsep, "Z", wrange, "Value")
wramp = node(wnt, "ShaderNodeValToRGB", 100, 0)
wramp.color_ramp.elements[0].position = 0.0
wramp.color_ramp.elements[0].color = (0.02, 0.018, 0.015, 1)
wramp.color_ramp.elements[1].position = 1.0
wramp.color_ramp.elements[1].color = (0.5, 0.48, 0.44, 1)
mid = wramp.color_ramp.elements.new(0.42)
mid.color = (0.16, 0.12, 0.08, 1)
link(wnt, wrange, "Result", wramp, "Fac")
wx = node(wnt, "ShaderNodeMapRange", -200, -300)
wx.clamp = True
wx.inputs["From Min"].default_value = -0.8
wx.inputs["From Max"].default_value = 0.8
wx.inputs["To Min"].default_value = 0.35
wx.inputs["To Max"].default_value = 1.8
link(wnt, wsep, "X", wx, "Value")
wmul = node(wnt, "ShaderNodeMixRGB", 350, 0, blend_type="MULTIPLY")
wmul.inputs["Fac"].default_value = 1.0
link(wnt, wramp, "Color", wmul, "Color1")
wxc = node(wnt, "ShaderNodeCombineColor", 100, -300)
link(wnt, wx, "Result", wxc, "Red")
link(wnt, wx, "Result", wxc, "Green")
link(wnt, wx, "Result", wxc, "Blue")
link(wnt, wxc, "Color", wmul, "Color2")
link(wnt, wmul, "Color", wbg, "Color")
wbg.inputs["Strength"].default_value = 1.0
link(wnt, wbg, "Background", wout, "Surface")

# --------------------------------------------------------------- render
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = samples
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 8
scene.render.film_transparent = True
scene.render.resolution_x = size
scene.render.resolution_y = size
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.filepath = out_path
bpy.ops.render.render(write_still=True)
print("WROTE", out_path)
