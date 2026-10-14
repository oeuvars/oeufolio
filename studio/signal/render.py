"""The spine's picture: a traffic signal on its post, with flowers where its three lamps should be. A red rose
for stop, the sunflower with an eye at its heart for wait, and a Victoria lily pad for go. Run from the repository
root, after studio/signal/cut.py:

    blender -b --factory-startup -P studio/signal/render.py -- [--scale 1] [--samples 128]

Writes studio/signal/art/signal.png, the render on clear ground, for studio/signal/print.py to screen.

Metres. x runs across the face of the signal, y away from the camera, z up. The head is a cast aluminium housing of
three sections, each with a hinged door and a cap visor open underneath, as on a 12-inch vehicle signal, painted
the dark green of the reference poster's signal. It sits on a slip fitter on top of a plain round post. The camera
is orthographic, a little to the left of the signal and a little below it, so the visors show their depth and the
post runs straight down the strip.
"""

import argparse
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "art")

WIDTH = 0.36  # across the housing
DEPTH = 0.22  # front to back
CELL = 0.40  # the height of one section
LENS = 0.15  # radius of the lamp opening
VISOR = 0.21  # how far the visor reaches at its top
POST = 0.06  # radius of the post
FRONT = -DEPTH / 2 - 0.028  # the face of the doors
MOUTH = FRONT - 0.012 - VISOR - 0.01  # just out past the visors, where the flowers stand
ASPECT = 11  # the picture's height over its width: taller than the spine ever is, so it is only cut at the foot
YAW = math.radians(24)  # the camera stands this far round to the signal's left
PITCH = math.radians(9)  # and looks up at it by this much
LEAN = math.radians(2.5)  # and is tilted, so the signal leans into the strip as the poster's does


def mesh_object(name, verts, faces, material=None):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def primitive(kind, material, **kw):
    getattr(bpy.ops.mesh, f"primitive_{kind}_add")(**kw)
    obj = bpy.context.active_object
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


def bevel(obj, width, segments=4):
    mod = obj.modifiers.new("bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    obj.modifiers.new("normals", "WEIGHTED_NORMAL").keep_sharp = True
    return obj


def box(name, size, at, material, round_=0.01):
    bpy.ops.mesh.primitive_cube_add(size=1, location=at)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(scale=True)
    obj.data.materials.append(material)
    return bevel(obj, round_)


def node_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    return mat, nodes, links, nodes["Principled BSDF"]


def paint():
    """Dark green enamel on cast aluminium, weathered: rougher and a little chalky where the weather has had it."""
    mat, nodes, links, bsdf = node_material("paint")
    coord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 18
    noise.inputs["Detail"].default_value = 8
    links.new(coord.outputs["Object"], noise.inputs["Vector"])
    tone = nodes.new("ShaderNodeValToRGB")
    tone.color_ramp.elements[0].position = 0.35
    tone.color_ramp.elements[0].color = (0.016, 0.042, 0.046, 1)
    tone.color_ramp.elements[1].position = 0.75
    tone.color_ramp.elements[1].color = (0.036, 0.075, 0.078, 1)
    links.new(noise.outputs["Fac"], tone.inputs["Fac"])
    links.new(tone.outputs["Color"], bsdf.inputs["Base Color"])
    rough = nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = 0.32
    rough.inputs["To Max"].default_value = 0.6
    links.new(noise.outputs["Fac"], rough.inputs["Value"])
    links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def dark():
    mat, _, _, bsdf = node_material("recess")
    bsdf.inputs["Base Color"].default_value = (0.01, 0.012, 0.012, 1)
    bsdf.inputs["Roughness"].default_value = 0.7
    return mat


def picture(name, file, glow, rim=None):
    """A cut-out picture, lit and glowing a little from behind as a lamp's lens does."""
    mat, nodes, links, bsdf = node_material(name)
    image = nodes.new("ShaderNodeTexImage")
    image.image = bpy.data.images.load(os.path.join(ART, file))
    image.extension = "CLIP"
    links.new(image.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(image.outputs["Alpha"], bsdf.inputs["Alpha"])
    links.new(image.outputs["Color"], bsdf.inputs["Emission Color"])
    # Brightest in the middle, as a lamp is behind its lens.
    coord = nodes.new("ShaderNodeTexCoord")
    centre = nodes.new("ShaderNodeVectorMath")
    centre.operation = "DISTANCE"
    centre.inputs[1].default_value = (0.5, 0.5, 0)
    links.new(coord.outputs["UV"], centre.inputs[0])
    fall = nodes.new("ShaderNodeMapRange")
    fall.inputs["From Min"].default_value = 0.05
    fall.inputs["From Max"].default_value = 0.5
    fall.inputs["To Min"].default_value = glow
    fall.inputs["To Max"].default_value = glow * 0.45
    links.new(centre.outputs["Value"], fall.inputs["Value"])
    links.new(fall.outputs["Result"], bsdf.inputs["Emission Strength"])
    bsdf.inputs["Roughness"].default_value = 0.55
    return mat


def rose_material():
    """Red petals with a velvet bloom on them, deepening to near black in the heart, lit through where they are thin."""
    mat, nodes, links, bsdf = node_material("rose")
    shade = nodes.new("ShaderNodeVertexColor")
    shade.layer_name = "shade"
    # The folds between the petals fall into deep shadow, the way a rose's heart goes nearly black.
    occlusion = nodes.new("ShaderNodeAmbientOcclusion")
    occlusion.inputs["Distance"].default_value = 0.03
    occlusion.samples = 16
    deepen = nodes.new("ShaderNodeMath")
    deepen.operation = "POWER"
    deepen.inputs[1].default_value = 2.5
    links.new(occlusion.outputs["AO"], deepen.inputs[0])
    folded = nodes.new("ShaderNodeVectorMath")
    folded.operation = "MULTIPLY"
    links.new(shade.outputs["Color"], folded.inputs[0])
    links.new(deepen.outputs["Value"], folded.inputs[1])
    links.new(folded.outputs["Vector"], bsdf.inputs["Base Color"])
    links.new(shade.outputs["Color"], bsdf.inputs["Subsurface Radius"])
    bsdf.inputs["Subsurface Weight"].default_value = 0.35
    bsdf.inputs["Subsurface Scale"].default_value = 0.004
    bsdf.inputs["Roughness"].default_value = 0.5
    bsdf.inputs["Sheen Weight"].default_value = 0.3
    bsdf.inputs["Sheen Roughness"].default_value = 0.35
    bsdf.inputs["Sheen Tint"].default_value = (1.0, 0.2, 0.2, 1)
    links.new(folded.outputs["Vector"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 0.08
    return mat


def smooth(edge0, edge1, x):
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3 - 2 * t)


def rose(at, across, material):
    """A rose in full bloom seen from the front: petals set round the heart one golden angle apart, the inner ones
    wrapped close and upright, the outer ones opening out wide, broad and rounded, their edges rolled back."""
    verts, faces, shades = [], [], []
    petals, nu, nv = 38, 13, 12
    for k in range(petals):
        t = k / (petals - 1)
        theta = k * math.radians(137.508)
        r0 = 0.03 + 0.25 * t**0.8  # where the petal springs from, out from the heart
        height = 0.32 + 0.62 * t**0.7
        widest = 0.32 + 0.75 * t
        open_ = math.radians(4 + 78 * t**1.5)
        roll = math.radians(14 + 64 * t)
        cup = 1 / max(0.12, r0 * 1.15) * (1 - 0.55 * t)
        er = Vector((math.cos(theta), math.sin(theta), 0))
        et = Vector((-math.sin(theta), math.cos(theta), 0))
        ez = Vector((0, 0, 1))
        # The petal's midline, walked up from its foot.
        line, r, z, steps = [], r0, 0.0, 48
        for i in range(steps + 1):
            v = i / steps
            gamma = open_ * v**0.8 + roll * smooth(0.62, 1.0, v)
            line.append((r, z, gamma))
            ds = height / steps
            r += ds * math.sin(gamma)
            z += ds * math.cos(gamma)
        base = len(verts)
        for j in range(nv + 1):
            v = j / nv
            for i in range(nu + 1):
                u = 2 * i / nu - 1
                # The corners come down, so the top is round.
                vv = v * (1 - 0.22 * u * u * v)
                r, z, gamma = line[round(vv * steps)]
                width = widest * (0.22 + 0.78 * (1 - (1 - vv) ** 2.2)) * (1 - 0.35 * vv**5)
                x = u * width / 2
                c = cup * (1 - 1.5 * t * smooth(0.45, 1.0, vv))
                if abs(c) < 1e-4:
                    side, inward = x, 0.0
                else:
                    side, inward = math.sin(x * c) / c, (1 - math.cos(x * c)) / c
                normal = er * math.cos(gamma) - ez * math.sin(gamma)
                ripple = 0.012 * math.sin(7 * u + 3 * k) * vv**2
                p = er * r + ez * z + et * side - normal * (inward - ripple)
                verts.append(tuple(p + Vector(at)))
                deep = (1 - t) ** 1.6
                edge = smooth(0.7, 1.0, vv) * 0.25
                shades.append((0.5 - 0.44 * deep - edge * 0.5 * (0.42 - 0.34 * deep), 0.012 * (1 - deep), 0.03 - 0.018 * deep))
        for j in range(nv):
            for i in range(nu):
                a = base + j * (nu + 1) + i
                faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    obj = mesh_object("rose", verts, faces, material)
    layer = obj.data.color_attributes.new("shade", "FLOAT_COLOR", "POINT")
    for i, s in enumerate(shades):
        layer.data[i].color = (*s, 1)
    solid = obj.modifiers.new("thick", "SOLIDIFY")
    solid.thickness = 0.0012
    obj.modifiers.new("smooth", "SUBSURF").levels = 1
    # Its heart toward the camera, as wide as across.
    lo = min(v.co.x for v in obj.data.vertices)
    hi = max(v.co.x for v in obj.data.vertices)
    fit = across / (hi - lo)
    pivot = Vector(at)
    obj.data.transform(Matrix.Translation(-pivot))
    obj.data.transform(Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Scale(fit, 4))
    obj.location = pivot
    return obj


def disc(name, at, size, material, sag=0.0, rings=32):
    """A square picture on a sheet facing the camera, dished toward it by sag at the edge."""
    verts, faces = [], []
    for j in range(rings + 1):
        for i in range(rings + 1):
            u, v = i / rings, j / rings
            x, z = (u - 0.5) * size, (v - 0.5) * size
            d = (x * x + z * z) / (size / 2) ** 2
            verts.append((at[0] + x, at[1] - sag * d, at[2] + z))
    for j in range(rings):
        for i in range(rings):
            a = j * (rings + 1) + i
            faces.append((a, a + 1, a + rings + 2, a + rings + 1))
    obj = mesh_object(name, verts, faces, material)
    uv = obj.data.uv_layers.new()
    for loop in obj.data.loops:
        co = obj.data.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = ((co.x - at[0]) / size + 0.5, (co.z - at[2]) / size + 0.5)
    return obj


def ring(name, at, radius, length, thickness, material, start=0.0, sweep=360.0, longer=0.0, segments=96):
    """A tube along -y from at, or a part of one; longer stretches it at its top, so a visor reaches out over its lamp."""
    bm = bmesh.new()
    arc = []
    closed = sweep >= 360
    count = segments if closed else segments + 1
    for i in range(count):
        a = math.radians(start + sweep * i / segments)
        x, z = radius * math.cos(a), radius * math.sin(a)
        reach = length * (1 - longer * (1 - math.sin(a)) / 2)
        back = bm.verts.new((at[0] + x, at[1], at[2] + z))
        front = bm.verts.new((at[0] + x, at[1] - reach, at[2] + z))
        arc.append((back, front))
    for i in range(count if closed else count - 1):
        b0, f0 = arc[i]
        b1, f1 = arc[(i + 1) % count]
        bm.faces.new((b0, b1, f1, f0))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    for poly in mesh.polygons:
        poly.use_smooth = True
    solid = obj.modifiers.new("thick", "SOLIDIFY")
    solid.thickness = thickness
    solid.offset = 1
    bevel(obj, thickness * 0.45, 3)
    return obj


def lamp_light(at, colour, power):
    light = bpy.data.lights.new("lamp", "POINT")
    light.color = colour
    light.energy = power
    light.shadow_soft_size = 0.05
    obj = bpy.data.objects.new("lamp", light)
    obj.location = at
    bpy.context.collection.objects.link(obj)


def lamps(at, colour):
    """A lamp's light: one in the visor behind its flower, filling the visor with colour, and its glow thrown back on
    the flower from the visor's mouth, so the flower is lit in the colour it stands for."""
    lamp_light((at[0], FRONT - 0.07, at[2]), colour, 6)
    lamp_light((at[0], MOUTH - 0.07, at[2] + 0.03), colour, 3)


def signal():
    green = paint()
    recess = dark()
    box("housing", (WIDTH, DEPTH, 3 * CELL), (0, 0, -1.5 * CELL), green, 0.035)
    # Top cap and its fitting.
    primitive("cylinder", green, radius=0.055, depth=0.05, location=(0, 0, 0.025), vertices=48)
    bevel(bpy.context.active_object, 0.01)
    primitive("uv_sphere", green, radius=0.04, location=(0, 0, 0.05), segments=32, ring_count=16)
    # The slip fitter that clamps the head to its post, and its bolts.
    foot = -3 * CELL
    primitive("cylinder", green, radius=0.088, depth=0.16, location=(0, 0, foot - 0.08), vertices=64)
    bevel(bpy.context.active_object, 0.012)
    primitive("cylinder", green, radius=0.1, depth=0.025, location=(0, 0, foot - 0.012), vertices=64)
    bevel(bpy.context.active_object, 0.008)
    for a in (200, 290):
        r = math.radians(a)
        bolt = primitive("cylinder", green, radius=0.012, depth=0.03, location=(0.09 * math.cos(r), 0.09 * math.sin(r), foot - 0.09), vertices=6)
        bolt.rotation_euler = (0, math.radians(90), r)
    primitive("cylinder", green, radius=POST, depth=14, location=(0, 0, foot - 7.1), vertices=96)

    for n in range(3):
        mid = -CELL * (n + 0.5)
        box(f"door{n}", (WIDTH - 0.02, 0.03, CELL - 0.025), (0, -DEPTH / 2 - 0.012, mid), green, 0.012)
        primitive("cylinder", recess, radius=LENS, depth=0.01, location=(0, FRONT + 0.002, mid), rotation=(math.radians(90), 0, 0), vertices=96)
        # The lens's bezel, then the visor bolted round it, open underneath.
        ring(f"bezel{n}", (0, FRONT + 0.002, mid), LENS + 0.012, 0.018, 0.014, green)
        ring(f"visor{n}", (0, FRONT - 0.012, mid), LENS + 0.01, VISOR, 0.005, green, start=-52, sweep=284, longer=0.3)
        for h in (mid + CELL * 0.3, mid - CELL * 0.3):
            lug = primitive("cylinder", green, radius=0.014, depth=0.055, location=(-WIDTH / 2 - 0.004, -DEPTH / 2 - 0.006, h), vertices=24)
            bevel(lug, 0.004)
        primitive("cylinder", green, radius=0.012, depth=0.03, location=(WIDTH / 2 - 0.004, -DEPTH / 2 - 0.02, mid), rotation=(math.radians(90), 0, 0), vertices=6)
        box(f"wing{n}", (0.008, 0.012, 0.05), (WIDTH / 2 - 0.004, -DEPTH / 2 - 0.04, mid), green, 0.003)

    stop = -CELL * 0.5
    rose((0, MOUTH + 0.08, stop), 0.35, rose_material())
    lamps((0, 0, stop), (1.0, 0.1, 0.06))

    wait = -CELL * 1.5
    disc("sunflower", (0, MOUTH + 0.04, wait), 0.41, picture("sunflower", "sunflower.png", 0.3), sag=0.06)
    lamps((0, 0, wait), (1.0, 0.5, 0.06))

    go = -CELL * 2.5
    pad = 0.34
    disc("lily", (0, MOUTH + 0.05, go), pad, picture("lily", "lily.png", 0.8), sag=0.012)
    # The Victoria's pad turns up a rim all round it, red on the outside.
    rim = node_material("rim")
    rim[3].inputs["Base Color"].default_value = (0.42, 0.04, 0.02, 1)
    rim[3].inputs["Roughness"].default_value = 0.45
    rim[3].inputs["Sheen Weight"].default_value = 0.4
    ring("rim", (0, MOUTH + 0.06, go), pad / 2 - 0.004, 0.032, 0.004, rim[0], segments=160)
    lamps((0, 0, go), (0.15, 1.0, 0.3))


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--out", default=os.path.join(ART, "signal.png"))
    # When the GPU is busy with another render the picture may not fit beside it; the CPU has the room.
    parser.add_argument("--cpu", action="store_true")
    args = parser.parse_args(argv)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for device in prefs.devices:
        device.use = device.type == "METAL"
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU" if args.cpu else "GPU"
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    # The picture is tall, so it is rendered a piece at a time to keep within the GPU's memory.
    scene.cycles.use_auto_tile = True
    scene.cycles.tile_size = 1024
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    width = round(480 * args.scale)
    scene.render.resolution_x = width
    scene.render.resolution_y = width * ASPECT
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "16"

    signal()

    # A clear day: blue light from the sky in every shadow, and the sun from high on the left.
    world = bpy.data.worlds.new("sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.36, 0.55, 0.95, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.85
    scene.world = world
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 4.6
    sun.color = (1.0, 0.95, 0.87)
    sun.angle = math.radians(1.5)
    sun_obj = bpy.data.objects.new("sun", sun)
    sun_obj.rotation_euler = (math.radians(50), math.radians(-28), math.radians(-30))
    bpy.context.collection.objects.link(sun_obj)

    cam = bpy.data.cameras.new("camera")
    cam.type = "ORTHO"
    camera = bpy.data.objects.new("camera", cam)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    toward = Vector((math.sin(YAW) * math.cos(PITCH), math.cos(YAW) * math.cos(PITCH), math.sin(PITCH)))
    target = Vector((0, 0, -1.5 * CELL))
    camera.location = target - toward * 30
    camera.rotation_euler = (toward.to_track_quat("-Z", "Y") @ Quaternion((0, 0, 1), LEAN)).to_euler()
    cam.clip_end = 100

    # Frame the head: its widest reach across the picture with a little room, and about as much room over its top as
    # the other strips leave over their pages.
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    points = []
    for obj in scene.objects:
        if obj.type != "MESH" or obj.dimensions.z > 5:
            continue
        evaluated = obj.evaluated_get(depsgraph)
        points += [evaluated.matrix_world @ Vector(c) for c in evaluated.bound_box]
    right = camera.matrix_world.to_3x3() @ Vector((1, 0, 0))
    up = camera.matrix_world.to_3x3() @ Vector((0, 1, 0))
    xs = [(p - camera.location).dot(right) for p in points]
    ys = [(p - camera.location).dot(up) for p in points]
    span = (max(xs) - min(xs)) / 0.84
    cam.ortho_scale = span * ASPECT
    # A little left of the middle: the strip's right edge is torn, and the tear takes the last of the picture.
    cam.shift_x = ((max(xs) + min(xs)) / 2 + 0.05 * span) / cam.ortho_scale
    cam.shift_y = (max(ys) + 0.2 * span - cam.ortho_scale / 2) / cam.ortho_scale

    scene.render.filepath = args.out
    bpy.ops.render.render(write_still=True)


main()
