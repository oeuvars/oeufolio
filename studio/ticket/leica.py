"""A Leica M3 with its 50 mm Summicron, lying on its back on the leather beside the ticket, photographed on the copy
stand under the same light, so its shadow falls as the ticket's does. Run from the repository root:

    blender -b --factory-startup -P studio/ticket/leica.py -- [--scale 0.5] [--samples 64] [--proofs DIR]

It is modelled in millimetres from the camera itself, as the photograph the page was given shows it: the body a
slab 138 by 77 by 33.5 mm with its two ends rounded, the lower part wrapped in black vulcanite with its fine
pebbled grain, the top cover and bottom plate satin chrome; on the front of the top cover the three windows, the
big viewfinder window and the frosted one that lights the framelines close together at one end and the small
rangefinder window further along; the bayonet flange with the lens on it, and below the windows the self-timer
lever and the frame selector. Along the top the rewind knob, the accessory shoe, the speed dial, the release and
the advance lever stand up off the cover, seen from above in profile. The lens is turned chrome, ring above ring,
the focusing ring knurled, the black front ring engraved and filled white, and in the middle the front element,
coated, so it throws back the studio in violet and amber. A leather strap is on the lug at the far end, with its
keeper, and runs off the leather.

The model is scaled to the props' scale (PROP, em to the millimetre, shared with film.py), turned and laid where
the page wants it in the spread's em, and the box the photograph covers is written to src/components/ticket/
camera.json for the page to place it by. Writes public/objects/ticket-camera.avif. Set OEUSUME if that checkout is
not in ~/Documents/oeusume.
"""

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OEUSUME = os.environ.get("OEUSUME", os.path.expanduser("~/Documents/oeusume"))
sys.path.insert(0, os.path.join(OEUSUME, "studio"))

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import stage as stage_module  # noqa: E402
from solids import finish, lathe, principled, prism, rect, spun, torus, worn  # noqa: E402
from stage import Stage  # noqa: E402

OUT = os.path.join(ROOT, "public", "objects")
PLACE = os.path.join(ROOT, "src", "components", "ticket", "camera.json")
PANEL = "#651415"
PROP = 0.095  # em to the millimetre: the props' scale, film.py's too
AT = (3.9, 1.4)  # where the middle of the body lies, in the spread's em
TURN = 80  # degrees, anticlockwise from lying level: the top cover to the left, as the photograph has it
EXPOSURE = 0.1

L, H, D = 138.0, 77.0, 33.5  # the body: long, high, deep
END = 15.0  # the radius its two ends are rounded to, seen from above
TOP = 50.5  # where the top cover starts, up from the bottom
LENS = (66.0, 34.0)  # the lens's axis on the front
FRONT = D  # the front face, up off the leather as the camera lies


# Materials.


def chrome(name="chrome", rough=0.17):
    m = principled(name, (0.8, 0.79, 0.77), rough=rough, metal=1.0)
    worn(m, "Fingerprints009", 30, 0.12)
    worn(m, "Scratches003", 45, 0.06)
    return m


def turned(name="turned", rough=0.14):
    return spun(chrome(name, rough), 0.6)


def vulcanite():
    """Black vulcanite, its grain a close field of small rounded pebbles, matte with a little sheen on their tops."""
    m = principled("vulcanite", (0.016, 0.015, 0.014), rough=0.62)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    coord = nodes.new("ShaderNodeTexCoord")
    cells = nodes.new("ShaderNodeTexVoronoi")
    cells.feature = "DISTANCE_TO_EDGE"
    cells.inputs["Scale"].default_value = 1.4
    cells.inputs["Randomness"].default_value = 1.0
    links.new(coord.outputs["Object"], cells.inputs["Vector"])
    shoulder = nodes.new("ShaderNodeMapRange")
    shoulder.inputs["From Max"].default_value = 0.18
    links.new(cells.outputs["Distance"], shoulder.inputs["Value"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.08
    bump.inputs["Strength"].default_value = 0.8
    links.new(shoulder.outputs["Result"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], nodes["Principled BSDF"].inputs["Normal"])
    rough = nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = 0.72
    rough.inputs["To Max"].default_value = 0.5
    links.new(shoulder.outputs["Result"], rough.inputs["Value"])
    links.new(rough.outputs["Result"], nodes["Principled BSDF"].inputs["Roughness"])
    return m


def knurled(name, count):
    """Turned chrome cut with fine grooves along the axis, all the way round: a focusing ring's grip. The ring is
    built along its own x axis, so the angle round it is taken in y and z."""
    m = turned(name)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    coord = nodes.new("ShaderNodeTexCoord")
    split = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coord.outputs["Object"], split.inputs["Vector"])
    angle = nodes.new("ShaderNodeMath")
    angle.operation = "ARCTAN2"
    links.new(split.outputs["Z"], angle.inputs[0])
    links.new(split.outputs["Y"], angle.inputs[1])
    times = nodes.new("ShaderNodeMath")
    times.operation = "MULTIPLY"
    times.inputs[1].default_value = count
    links.new(angle.outputs[0], times.inputs[0])
    wave = nodes.new("ShaderNodeMath")
    wave.operation = "SINE"
    links.new(times.outputs[0], wave.inputs[0])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.06
    links.new(wave.outputs[0], bump.inputs["Height"])
    # Only round the ring's side: the flat step on top of it is turned smooth.
    normal = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coord.outputs["Normal"], normal.inputs["Vector"])
    flat = nodes.new("ShaderNodeMath")
    flat.operation = "ABSOLUTE"
    links.new(normal.outputs["X"], flat.inputs[0])
    side = nodes.new("ShaderNodeMath")
    side.operation = "SUBTRACT"
    side.inputs[0].default_value = 1.0
    side.use_clamp = True
    links.new(flat.outputs[0], side.inputs[1])
    links.new(side.outputs[0], bump.inputs["Strength"])
    links.new(bump.outputs["Normal"], nodes["Principled BSDF"].inputs["Normal"])
    return m


def dark_glass(name="window"):
    """A window into the dark of the finder: black, and as glossy as glass, so it shows only what it reflects."""
    return principled(name, (0.004, 0.004, 0.005), rough=0.02, specular_ior_level=0.6, coat_weight=1.0, coat_roughness=0.0)


def frosted():
    """The frosted window that lights the framelines: milky, ribbed, catching the light through it."""
    m = principled("frosted", (0.62, 0.63, 0.6), rough=0.42, subsurface_weight=0.3)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    coord = nodes.new("ShaderNodeTexCoord")
    wave = nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 1.2
    links.new(coord.outputs["Object"], wave.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.05
    links.new(wave.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], nodes["Principled BSDF"].inputs["Normal"])
    return m


def coated():
    """The front element: clear glass with an anti-reflection coat, which colours what it reflects."""
    m = principled("coated", (1, 1, 1), rough=0.0, transmission_weight=1.0, ior=1.62)
    shader = m.node_tree.nodes["Principled BSDF"]
    shader.inputs["Thin Film Thickness"].default_value = 330
    shader.inputs["Thin Film IOR"].default_value = 1.38
    return m


# Geometry, in the camera's own millimetres: x along the body, y up it from the bottom, z out of its front.


def slab(name, y0, y1, inset, material, bevel=1.2):
    """A length of the body between heights y0 and y1: its outline from above, a rectangle with rounded ends,
    stood up from y0 to y1, its edges eased."""
    outline = rect(inset, inset, L - inset, D - inset, r=min(END, D / 2) - inset, steps=12)
    bm = bmesh.new()
    lower = [bm.verts.new((x, y0, z)) for x, z in outline]
    upper = [bm.verts.new((x, y1, z)) for x, z in outline]
    bm.faces.new(lower[::-1])
    bm.faces.new(upper)
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lower[i], lower[j], upper[j], upper[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    if bevel:
        caps = [e for e in bm.edges if all(abs(v.co.y - y0) < 1e-6 for v in e.verts) or all(abs(v.co.y - y1) < 1e-6 for v in e.verts)]
        bmesh.ops.bevel(bm, geom=caps, offset=bevel, segments=4, profile=0.5, affect="EDGES", clamp_overlap=True)
    return finish(STAGE, name, bm, material)


def frontal(name, outline, z0, z1, material, bevel=0.0, segments=3):
    """A part standing out of the front: an outline in front coordinates (x along, y up), from z0 to z1."""
    obj = prism(STAGE, name, [(x, -y) for x, y in outline], z0, z1, material, bevel=bevel, segments=segments)
    return obj


def disc(name, cx, cy, profile, material, steps=96, caps=True):
    """A turned part on the front, its axis out of the front at cx, cy: profile is (height off the front, radius).
    A ring, open in the middle, is turned without caps."""
    obj = lathe(STAGE, name, [(FRONT + z, r) for z, r in profile], material, steps=steps, axis="Z", caps=caps)
    obj.location = (cx, cy, 0)
    return obj


def upright(name, cx, profile, material, steps=64):
    """A turned part standing up off the top cover, its axis along y at cx, halfway through the body's depth."""
    obj = lathe(STAGE, name, [(H + y, r) for y, r in profile], material, steps=steps, axis="X")
    obj.rotation_euler = (0, 0, math.radians(90))
    obj.location = (cx, 0, D / 2)
    return obj


def engrave(text, cx, cy, radius, start, size, z, material, sweep=None):
    """Letters round a ring on the front, reading clockwise from the angle start (degrees, from the top), each
    upright to the ring, as a lens's maker's ring is engraved."""
    letters = []
    step = size * 0.78 / radius
    for i, char in enumerate(text):
        if char == " ":
            continue
        curve = bpy.data.curves.new(f"letter-{len(letters)}", "FONT")
        curve.body = char
        curve.size = size
        curve.align_x = "CENTER"
        curve.align_y = "CENTER"
        obj = STAGE.add(f"letter-{len(letters)}", curve)
        obj.data.materials.append(material)
        a = math.radians(90 - start) - i * step
        obj.location = (cx + radius * math.cos(a), cy + radius * math.sin(a), z)
        obj.rotation_euler = (0, 0, a - math.radians(90))
        letters.append(obj)
    return letters


def camera():
    parts_before = set(bpy.data.objects)
    satin, bright = chrome(), turned()
    skin = vulcanite()
    black = principled("black", (0.012, 0.012, 0.012), rough=0.35)
    paint = principled("fill", (0.86, 0.86, 0.82), rough=0.55)
    glass = dark_glass()

    # The body: the vulcanite between the plates, a hair inside them, then the chrome top cover and bottom plate.
    slab("body", 2.5, TOP, 0.35, skin, bevel=0)
    slab("top", TOP, H, 0.0, satin, bevel=1.6)
    slab("bottom", 0.0, 2.5, 0.0, satin, bevel=0.8)

    # The windows on the front of the top cover, each in a chrome bezel, and the line engraved under them.
    for name, (x, y, w, h), material in (
        ("finder", (115.0, 64.0, 16.5, 13.0), glass),
        ("frames", (90.0, 64.5, 14.0, 11.0), frosted()),
        ("range", (42.0, 64.0, 9.5, 9.5), glass),
    ):
        frontal(f"{name}-bezel", rect(x - w / 2 - 1.2, y - h / 2 - 1.2, x + w / 2 + 1.2, y + h / 2 + 1.2, r=1.6), FRONT - 0.2, FRONT + 0.7, bright, bevel=0.4)
        frontal(f"{name}-glass", rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, r=0.8), FRONT - 0.2, FRONT + 0.75, material)

    # The bayonet flange and the lens release, the self-timer lever and the frame selector below the windows.
    cx, cy = LENS
    disc("flange", cx, cy, [(0, 0), (0, 25.0), (1.2, 25.0), (1.6, 24.4), (1.6, 0)], bright)
    disc("release", cx + 26.5, cy + 15.0, [(0, 0), (0, 3.4), (2.6, 3.4), (3.0, 3.0), (3.0, 0)], bright, steps=48)
    disc("selector-hub", 38.0, 46.0, [(0, 0), (0, 5.0), (1.6, 5.0), (2.0, 4.6), (2.0, 0)], bright, steps=48)
    frontal("selector", rect(36.6, 46.0, 39.4, 58.0, r=1.2), FRONT + 1.2, FRONT + 2.4, bright, bevel=0.5)
    disc("timer-hub", 21.0, 34.0, [(0, 0), (0, 4.2), (1.4, 4.2), (1.8, 3.8), (1.8, 0)], bright, steps=48)
    frontal("timer", rect(19.8, 18.0, 22.2, 34.0, r=1.2), FRONT + 1.0, FRONT + 2.2, bright, bevel=0.5)
    disc("timer-tip", 21.0, 18.5, [(0, 0), (0, 3.0), (2.8, 3.0), (3.2, 2.6), (3.2, 0)], bright, steps=48)

    # The lens, ring above ring off the flange: the scale ring, the knurled focusing ring, the aperture ring, the
    # barrel, and the black front ring round the glass.
    disc("scale", cx, cy, [(1.6, 0), (1.6, 23.2), (7.0, 23.2), (7.4, 22.9), (7.4, 0)], bright)
    disc("focus", cx, cy, [(7.4, 0), (7.4, 25.6), (16.0, 25.6), (16.4, 25.2), (16.4, 0)], knurled("focus", 90), steps=180)
    disc("aperture", cx, cy, [(16.4, 0), (16.4, 24.4), (21.5, 24.4), (21.9, 24.0), (21.9, 0)], knurled("aperture", 30), steps=120)
    disc("barrel", cx, cy, [(21.9, 0), (21.9, 22.6), (27.6, 22.6), (28.2, 22.0), (28.2, 0)], bright)
    disc("bezel", cx, cy, [(28.2, 16.2), (28.6, 16.2), (28.6, 21.6), (28.2, 22.0)], black, caps=False)
    # Inside the bezel: a black throat going down into the lens, the elements behind the front one and the iris
    # between them, and the front element bulging in the throat.
    disc("throat", cx, cy, [(28.6, 16.2), (25.0, 15.6), (12.0, 13.0), (12.0, 0)], black, caps=False)
    disc("iris", cx, cy, [(17.0, 6.5), (17.0, 13.5), (17.3, 13.5), (17.3, 6.5), (17.0, 6.5)], black, caps=False)
    disc("rear", cx, cy, [(18.5, 0), (18.5, 12.6), (19.2, 12.6), (20.4, 9.0), (20.8, 0)], coated(), steps=96)
    disc("middle", cx, cy, [(21.5, 0), (21.5, 13.8), (22.2, 13.8), (22.6, 10.0), (22.0, 0)], coated(), steps=96)
    disc("element", cx, cy, [(24.6, 0), (24.6, 15.4), (25.6, 15.4), (26.9, 11.5), (27.8, 6.5), (28.1, 0)], coated(), steps=128)
    engrave("SUMMICRON f=5cm 1:2  No 1234567", cx, cy, 18.9, -20, 1.55, FRONT + 28.62, paint)
    engrave("ERNST LEITZ GMBH WETZLAR", cx, cy, 18.9, 162, 1.55, FRONT + 28.62, paint)
    # Distance and aperture marks on the step of each ring, filled black.
    for k in range(-4, 5):
        a = math.radians(90 + k * 9)
        r0 = 23.6
        x, y = cx + r0 * math.cos(a), cy + r0 * math.sin(a)
        frontal(f"tick-{k}", rect(x - 0.18, y - 0.9, x + 0.18, y + 0.9), FRONT + 7.4, FRONT + 7.45, black)

    # Along the top, seen from above in profile: the rewind knob, the shoe, the speed dial, the release, the lever.
    upright("rewind", 22.0, [(0, 0), (0, 8.0), (2.0, 8.0), (2.0, 9.5), (8.0, 9.5), (8.5, 9.0), (8.5, 0)], knurled("rewind", 40))
    frontal("shoe", rect(60.0, H, 80.0, H + 1.5), 7.0, D - 7.0, satin, bevel=0.3)
    upright("dial", 104.0, [(0, 0), (0, 11.0), (4.5, 11.0), (5.0, 10.5), (5.0, 0)], knurled("dial", 60))
    upright("release", 118.0, [(0, 0), (0, 4.5), (5.5, 4.5), (6.0, 3.6), (6.0, 0)], bright)
    frontal("lever", rect(121.0, H + 2.0, 139.0, H + 5.5, r=1.6), D / 2 - 1.2, D / 2 + 1.2, satin, bevel=0.6)

    # The lugs at either end, and on the far one the strap: its split ring, the leather keeper, the cord.
    for x in (-1.8, L + 1.8):
        lug = torus(STAGE, f"lug-{x:.0f}", 2.6, 0.9, bright, steps=48, around=12)
        lug.location = (x, 62.0, D / 2)
        lug.rotation_euler = (0, math.radians(90), 0)
    ring_ = torus(STAGE, "split-ring", 5.0, 0.7, bright, steps=64, around=12)
    ring_.location = (L + 6.5, 62.0, 2.0)
    strap = principled("strap", (0.02, 0.018, 0.016), rough=0.55)
    keeper = lathe(STAGE, "keeper", [(0, 0), (0, 3.4), (15.0, 3.4), (15.0, 0)], strap, steps=32, axis="X")
    keeper.location = (L + 12.0, 62.0, 3.4)
    cord = bpy.data.curves.new("cord", "CURVE")
    cord.dimensions = "3D"
    cord.bevel_depth = 2.0
    cord.bevel_resolution = 4
    spline = cord.splines.new("BEZIER")
    path = [(L + 27.0, 62.0, 2.0), (L + 55.0, 57.0, 2.0), (L + 95.0, 70.0, 2.0), (L + 130.0, 66.0, 2.0)]
    spline.bezier_points.add(len(path) - 1)
    for point, co in zip(spline.bezier_points, path):
        point.co = co
        point.handle_left_type = point.handle_right_type = "AUTO"
    cord.materials.append(strap)
    STAGE.add("cord", cord)

    # Gather it all, and lay it where the page wants it, at the props' scale.
    pivot = bpy.data.objects.new("leica", None)
    bpy.context.scene.collection.objects.link(pivot)
    for obj in set(bpy.data.objects) - parts_before - {pivot}:
        if obj.parent is None:
            obj.parent = pivot
    pivot.location = (-L / 2, -H / 2, 0)
    bpy.context.view_layer.update()
    holder = bpy.data.objects.new("leica-placed", None)
    bpy.context.scene.collection.objects.link(holder)
    pivot.parent = holder
    holder.scale = (PROP, PROP, PROP)
    holder.rotation_euler = (0, 0, math.radians(TURN))
    holder.location = (AT[0], -AT[1], 0)
    bpy.context.view_layer.update()
    return holder


def bounds():
    """The box everything lies in, in the spread's em (x right, y down)."""
    xs, ys = [], []
    for obj in bpy.context.scene.objects:
        if obj.type not in ("MESH", "FONT", "CURVE") or obj.get("stand"):
            continue
        for corner in obj.bound_box:
            p = obj.matrix_world @ Vector(corner)
            xs.append(p.x)
            ys.append(-p.y)
    return min(xs), min(ys), max(xs), max(ys)


parser = argparse.ArgumentParser()
parser.add_argument("--scale", type=float, default=1.0)
parser.add_argument("--samples", type=int, default=160)
parser.add_argument("--proofs")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
if args.proofs:
    os.makedirs(args.proofs, exist_ok=True)
stage_module.MAT = PANEL
STAGE = Stage(OUT, args.proofs, scale=args.scale, samples=args.samples)
STAGE.clear()
camera()
x0, y0, x1, y1 = bounds()
BLEED = 2.0
json.dump({"box": [round(v, 4) for v in (x0 - BLEED, y0 - BLEED, x1 - x0 + 2 * BLEED, y1 - y0 + 2 * BLEED)]}, open(PLACE, "w"))
# The stand's own camera hangs over it, dark, and the front element and the finder windows face straight up at it:
# what they show is that dark, ringed with the room. It is seen only in reflections, and casts nothing.
over = bpy.data.meshes.new("stand-camera")
bm = bmesh.new()
bmesh.ops.create_circle(bm, cap_ends=True, radius=9.0, segments=64)
bm.to_mesh(over)
bm.free()
over.materials.append(principled("stand-camera", (0.003, 0.003, 0.003), rough=0.6))
above = STAGE.add("stand-camera", over)
above.location = ((x0 + x1) / 2, -(y0 + y1) / 2, 60.0)
above["stand"] = "shadowless"
above.visible_camera = False
above.visible_shadow = False
above.visible_diffuse = False
STAGE.shoot("ticket-camera", (x0, y0, x1 - x0, y1 - y0), bleed=BLEED, shadow=0.8, exposure=EXPOSURE, lens=False, sharp=2.0)
