"""A Leica M3 with its 50 mm Summicron, lying on its back on the leather beside the ticket, photographed on the copy
stand under the same light, so its shadow falls as the ticket's does. Run from the repository root:

    blender -b --factory-startup -P studio/ticket/leica.py -- [--scale 0.5] [--samples 64] [--proofs DIR]

It is modelled in millimetres from the camera itself, as a photograph straight on to an M3's front shows it
(leica_face.py), and that photograph is laid on the front of the model, so its chrome, vulcanite, engraving and glass
are the real camera's: the body a slab 138 by 75 by 33.5 mm with its two ends rounded, the lower part wrapped in black vulcanite with its fine
pebbled grain, the top cover and bottom plate satin chrome; on the front of the top cover the three windows, the
big viewfinder window and the frosted one that lights the framelines close together at one end and the small
rangefinder window further along; the bayonet flange with the lens on it, and below the windows the self-timer
lever and the frame selector. Along the top the rewind knob, the accessory shoe, the speed dial, the release and
the advance lever stand up off the cover, seen from above in profile. The lens is turned chrome, ring above ring,
the focusing ring knurled, the black front ring engraved and filled white, and in the middle the front element,
coated, so it throws back the studio in violet and amber. A leather strap is on the lug at the far end, with its
keeper, and runs off the leather.

The model is scaled to the props' scale (PROP, em to the millimetre), turned and laid at AT, in the em of the scene
it is put down in (scene.py, which photographs it with everything else on the leather). Run on its own, it writes
public/objects/ticket-camera.avif, the camera alone on the stand, for a look at it. Set OEUSUME if that checkout is
not in ~/Documents/oeusume.
"""

import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OEUSUME = os.environ.get("OEUSUME", os.path.expanduser("~/Documents/oeusume"))
sys.path.insert(0, os.path.join(OEUSUME, "studio"))
sys.path.insert(0, HERE)

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import key  # noqa: E402
import stage as stage_module  # noqa: E402
from solids import finish, lathe, principled, prism, rect, spun, torus, worn  # noqa: E402
from stage import Stage  # noqa: E402

OUT = os.path.join(ROOT, "public", "objects")
PANEL = "#651415"
PROP = 0.068  # em to the millimetre: the props' scale
AT = (3.7, 1.7)  # where the middle of the body lies, in the spread's em
TURN = 80  # degrees, anticlockwise from lying level: the top cover to the left, as the photograph has it
EXPOSURE = -2.0

L, H, D = 138.0, 75.0, 33.5  # the body: long, high, deep
END = 15.0  # the radius its two ends are rounded to, seen from above
TOP = 55.0  # where the top cover starts, up from the bottom
LENS = (78.7, 33.5)  # the lens's axis on the front
FRONT = D  # the front face, up off the leather as the camera lies


# Materials.


def chrome(name="chrome", rough=0.2):
    """Leica's satin chrome: bright, but not a mirror, its finish a fine matte that blurs what it reflects, a little
    uneven across a surface, polished brighter on the edges where hands have rubbed it for decades, and marked with
    fingerprints and hairline scratches."""
    m = principled(name, (0.9, 0.89, 0.86), rough=rough, metal=1.0)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    shader = nodes["Principled BSDF"]
    coord = nodes.new("ShaderNodeTexCoord")
    speckle = nodes.new("ShaderNodeTexNoise")
    speckle.inputs["Scale"].default_value = 6.0
    speckle.inputs["Detail"].default_value = 8.0
    links.new(coord.outputs["Object"], speckle.inputs["Vector"])
    uneven = nodes.new("ShaderNodeMapRange")
    uneven.inputs["To Min"].default_value = rough - 0.05
    uneven.inputs["To Max"].default_value = rough + 0.07
    links.new(speckle.outputs["Fac"], uneven.inputs["Value"])
    # Rubbed bright on the edges: where the surface turns most sharply it is smoother.
    geometry = nodes.new("ShaderNodeNewGeometry")
    edge = nodes.new("ShaderNodeMapRange")
    edge.inputs["From Min"].default_value = 0.5
    edge.inputs["From Max"].default_value = 0.56
    edge.inputs["To Min"].default_value = 0.0
    edge.inputs["To Max"].default_value = 0.12
    links.new(geometry.outputs["Pointiness"], edge.inputs["Value"])
    polished = nodes.new("ShaderNodeMath")
    polished.operation = "SUBTRACT"
    polished.use_clamp = True
    links.new(uneven.outputs["Result"], polished.inputs[0])
    links.new(edge.outputs["Result"], polished.inputs[1])
    links.new(polished.outputs[0], shader.inputs["Roughness"])
    # The satin's own grain, as a faint bump.
    grit = nodes.new("ShaderNodeTexNoise")
    grit.inputs["Scale"].default_value = 140.0
    links.new(coord.outputs["Object"], grit.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.004
    links.new(grit.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    worn(m, "Fingerprints009", 30, 0.06)
    worn(m, "Scratches003", 25, 0.07)
    return m


def turned(name="turned", rough=0.16):
    return spun(chrome(name, rough), 0.6)


def vulcanite():
    """Black vulcanite: hard rubber moulded with a fine leathery grain. On the front its grain is the photograph's
    own; here it is only the black, matte, a shade shinier on the worn tops."""
    return principled("vulcanite", (0.012, 0.0115, 0.011), rough=0.7, specular_ior_level=0.25)


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






# The face: the photograph straightened to the front (leica_face.py), PX_PER_MM, with its margins.
FACE = os.path.join(HERE, "art", "leica-front.png")
FACE_MARGIN, FACE_TOP = 12.0, 14.0  # as leica_face.py has them
# The photograph is taken straight on to the front, from far off, so the face is laid on straight down; SLANT would
# lean it, for a photograph that looked down at the camera.
SLANT = 0.0
PIVOT = None  # the empty all of the camera hangs from, in whose space the face is laid on


def faced(material, metal=None, rough=None, relief=0.012, image="leica-front.png"):
    """Lay the photograph on a material, on the faces that look out of the front as the photograph did: the colour
    there is the photograph's, its fine detail a faint relief; where a face turns away, to the sides, the material's
    own colour takes over. metal and rough are what the photographed surface is, where it is shown."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    coord = nodes.new("ShaderNodeTexCoord")
    coord.object = PIVOT
    split = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coord.outputs["Object"], split.inputs["Vector"])
    u = nodes.new("ShaderNodeMath")
    u.operation = "MULTIPLY_ADD"
    u.inputs[1].default_value = 1 / (L + 2 * FACE_MARGIN)
    u.inputs[2].default_value = FACE_MARGIN / (L + 2 * FACE_MARGIN)
    links.new(split.outputs["X"], u.inputs[0])
    lift = nodes.new("ShaderNodeMath")
    lift.operation = "MULTIPLY_ADD"
    lift.inputs[1].default_value = -SLANT
    lift.inputs[2].default_value = SLANT * FRONT
    links.new(split.outputs["Z"], lift.inputs[0])
    y = nodes.new("ShaderNodeMath")
    y.operation = "ADD"
    links.new(split.outputs["Y"], y.inputs[0])
    links.new(lift.outputs[0], y.inputs[1])
    v = nodes.new("ShaderNodeMath")
    v.operation = "MULTIPLY_ADD"
    tall = H + FACE_MARGIN + FACE_TOP
    v.inputs[1].default_value = 1 / tall
    v.inputs[2].default_value = FACE_MARGIN / tall
    links.new(y.outputs[0], v.inputs[0])
    uv = nodes.new("ShaderNodeCombineXYZ")
    links.new(u.outputs[0], uv.inputs["X"])
    links.new(v.outputs[0], uv.inputs["Y"])
    photo = nodes.new("ShaderNodeTexImage")
    photo.image = bpy.data.images.get(image) or bpy.data.images.load(os.path.join(os.path.dirname(FACE), image))
    photo.interpolation = "Cubic"
    photo.extension = "EXTEND"
    links.new(uv.outputs[0], photo.inputs["Vector"])
    # How squarely a face looks out of the front, which is up as the camera lies.
    geometry = nodes.new("ShaderNodeNewGeometry")
    up = nodes.new("ShaderNodeSeparateXYZ")
    links.new(geometry.outputs["Normal"], up.inputs["Vector"])
    front = nodes.new("ShaderNodeMapRange")
    front.interpolation_type = "SMOOTHSTEP"
    front.inputs["From Min"].default_value = 0.35
    front.inputs["From Max"].default_value = 0.8
    links.new(up.outputs["Z"], front.inputs["Value"])

    def blend(socket, value, kind="RGBA"):
        mix = nodes.new("ShaderNodeMix")
        mix.data_type = kind
        a, b = (6, 7) if kind == "RGBA" else (2, 3)
        if socket.is_linked:
            links.new(socket.links[0].from_socket, mix.inputs[a])
        elif kind == "RGBA":
            mix.inputs[a].default_value = socket.default_value
        else:
            mix.inputs[a].default_value = socket.default_value
        if isinstance(value, (int, float)):
            mix.inputs[b].default_value = value
        else:
            links.new(value, mix.inputs[b])
        links.new(front.outputs["Result"], mix.inputs[0])
        links.new(mix.outputs[2 if kind == "RGBA" else 0], socket)

    blend(shader.inputs["Base Color"], photo.outputs["Color"])
    if metal is not None:
        blend(shader.inputs["Metallic"], metal, "FLOAT")
    if rough is not None:
        blend(shader.inputs["Roughness"], rough, "FLOAT")
    # The photograph's fine detail as relief: the vulcanite's grain, the engraving, the knurls.
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = relief
    links.new(photo.outputs["Color"], bump.inputs["Height"])
    links.new(front.outputs["Result"], bump.inputs["Strength"])
    normal = shader.inputs["Normal"]
    if normal.is_linked:
        links.new(normal.links[0].from_socket, bump.inputs["Normal"])
    links.new(bump.outputs["Normal"], normal)
    return material


def lens_glass():
    """The front element. Glass is not lit as a surface is: what shows in it is what lies behind it, down in the lens,
    the black of the barrel and the coloured reflections of the coated elements, which is what the photograph shows
    there; so that is given out as it was photographed, and over it only the glass's own thin, sharp reflection of
    the studio, curved with its surface."""
    material = principled("lens-glass", (0, 0, 0), rough=0.03, specular_ior_level=0.05)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    faced(material, relief=0.0)
    shader = nodes["Principled BSDF"]
    photo = next(n for n in nodes if n.type == "TEX_IMAGE")
    shader.inputs["Base Color"].links and links.remove(shader.inputs["Base Color"].links[0])
    shader.inputs["Base Color"].default_value = (0, 0, 0, 1)
    # Given out at the strength that develops back to the photograph's own tones.
    strength = 1 / (float(stage_module.GAIN.mean()) * 2.0**EXPOSURE)
    links.new(photo.outputs["Color"], shader.inputs["Emission Color"])
    shader.inputs["Emission Strength"].default_value = strength
    return material


def camera():
    global PIVOT
    PIVOT = bpy.data.objects.new("leica", None)
    bpy.context.scene.collection.objects.link(PIVOT)
    parts_before = set(bpy.data.objects)
    satin = faced(chrome(), metal=0.75, rough=0.3, image="leica-body.png")
    bright = faced(turned(), metal=0.75, rough=0.28)
    skin = faced(vulcanite(), metal=0.0, rough=0.72, relief=0.008, image="leica-body.png")
    black = faced(principled("black", (0.012, 0.012, 0.012), rough=0.35), metal=0.0, rough=0.4)
    glass = faced(principled("glass", (0.01, 0.01, 0.01), rough=0.05, coat_weight=0.35, coat_roughness=0.02), metal=0.0, rough=0.08, relief=0.0)

    # The body, measured off the photograph: the vulcanite between the plates, a hair inside them, then the chrome
    # top cover and bottom plate.
    slab("body", 5.5, TOP, 0.35, skin, bevel=0)
    slab("top", TOP, H, 0.0, satin, bevel=1.6)
    slab("bottom", 0.0, 5.5, 0.0, satin, bevel=0.8)

    # The three windows on the front of the top cover, each in its chrome bezel, where the photograph has them.
    for name, (x, y, w, h) in (("finder", (116.7, 68.5, 19.7, 13.0)), ("frames", (89.3, 68.4, 15.5, 11.2)), ("range", (44.9, 69.1, 8.7, 6.2))):
        frontal(f"{name}-bezel", rect(x - w / 2 - 1.4, y - h / 2 - 1.4, x + w / 2 + 1.4, y + h / 2 + 1.4, r=1.6), FRONT - 0.2, FRONT + 0.9, bright, bevel=0.45)
        frontal(f"{name}-glass", rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, r=0.8), FRONT - 0.2, FRONT + 0.6, glass)

    # The lens, ring above ring off the bayonet flange: the scale ring, the focusing ring, the aperture ring, the
    # barrel, the black front ring round the glass, and the glass, curved, in its throat. Seen from straight above,
    # only the front ring, the barrel's lip and the flange round it show, as they do on a Summicron. Each ring is
    # open in the middle, so nothing lies over the glass but the glass. The engraving, the scales and what the
    # glass reflects are the photograph's.
    cx, cy = LENS
    disc("flange", cx, cy, [(0, 0), (0, 26.4), (1.2, 26.4), (1.6, 25.8), (1.6, 0)], bright)
    disc("scale", cx, cy, [(1.6, 20.5), (1.6, 24.8), (7.0, 24.8), (7.4, 24.6), (7.4, 20.5)], bright, caps=False)
    disc("focus", cx, cy, [(7.4, 20.5), (7.4, 24.6), (16.0, 24.6), (16.4, 24.4), (16.4, 20.5)], bright, steps=180, caps=False)
    disc("aperture", cx, cy, [(16.4, 20.5), (16.4, 24.4), (21.5, 24.4), (21.9, 24.3), (21.9, 20.5)], bright, steps=120, caps=False)
    disc("barrel", cx, cy, [(21.9, 20.5), (21.9, 25.2), (27.6, 25.2), (28.2, 24.6), (28.2, 21.4)], bright, caps=False)
    disc("bezel", cx, cy, [(28.2, 17.4), (28.6, 17.4), (28.6, 21.4), (28.2, 21.4)], black, caps=False)
    disc("throat", cx, cy, [(28.6, 17.4), (26.0, 17.2), (24.0, 17.0)], black, caps=False)
    disc("element", cx, cy, [(24.0, 0), (24.0, 17.0), (25.0, 17.0), (26.6, 12.8), (27.6, 6.9), (27.95, 0)], lens_glass(), steps=128)

    # Along the top, seen from above in profile: the advance lever and the release, the speed dial, the shoe, the
    # rewind knob.
    upright("release", 24.5, [(0, 0), (0, 8.0), (3.5, 8.0), (4.0, 7.5), (4.0, 2.0), (6.0, 2.0), (6.0, 0)], bright)
    frontal("lever", rect(26.0, H + 3.0, 50.0, H + 5.0, r=1.0), D / 2 - 1.2, D / 2 + 1.2, satin, bevel=0.5)
    upright("dial", 51.0, [(0, 0), (0, 8.5), (4.5, 8.5), (5.0, 8.0), (5.0, 0)], knurled("dial", 60))
    frontal("shoe", rect(62.0, H, 84.0, H + 1.5), 7.0, D - 7.0, satin, bevel=0.3)
    upright("rewind", 134.2, [(0, 0), (0, 3.8), (7.0, 3.8), (7.5, 3.4), (7.5, 0)], knurled("rewind", 40))

    # The lugs at either end, and on the far one the strap: its split ring, the leather keeper, the cord.
    for x in (-1.8, L + 1.8):
        lug = torus(STAGE, f"lug-{x:.0f}", 2.6, 0.9, bright, steps=48, around=12)
        lug.location = (x, 59.0, D / 2)
        lug.rotation_euler = (0, math.radians(90), 0)
    ring_ = torus(STAGE, "split-ring", 5.0, 0.7, bright, steps=64, around=12)
    ring_.location = (L + 6.5, 59.0, 2.0)
    strap = principled("strap", (0.02, 0.018, 0.016), rough=0.55)
    keeper = lathe(STAGE, "keeper", [(0, 0), (0, 3.4), (15.0, 3.4), (15.0, 0)], strap, steps=32, axis="X")
    keeper.location = (L + 12.0, 59.0, 3.4)
    cord = bpy.data.curves.new("cord", "CURVE")
    cord.dimensions = "3D"
    cord.bevel_depth = 2.0
    cord.bevel_resolution = 4
    spline = cord.splines.new("BEZIER")
    path = [(L + 27.0, 59.0, 2.0), (L + 55.0, 54.0, 2.0), (L + 95.0, 67.0, 2.0), (L + 130.0, 63.0, 2.0)]
    spline.bezier_points.add(len(path) - 1)
    for point, co in zip(spline.bezier_points, path):
        point.co = co
        point.handle_left_type = point.handle_right_type = "AUTO"
    cord.materials.append(strap)
    STAGE.add("cord", cord)

    # Gather it all, and lay it where the page wants it, at the props' scale.
    pivot = PIVOT
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


def softbox(holder):
    """Over the camera hangs a ring softbox round the stand's lens, as a camera is lit for its photograph: chrome and
    glass show only what is round them, and here that is one broad even light all round, with the dark of the stand's
    lens in its middle, right over the lens below, so the lens looks back at it as a dark eye ringed with light. Only
    the camera sees it, and only in what it reflects: it lights nothing else, and casts nothing."""
    parts = bpy.data.collections.new("leica-parts")
    stack = [holder]
    while stack:
        obj = stack.pop()
        stack.extend(obj.children)
        if obj.type in ("MESH", "CURVE", "FONT"):
            parts.objects.link(obj)
    lens_at = bpy.data.objects["element"].matrix_world.translation
    cast = 1 / stage_module.GAIN
    for name, inner, outer, z, glow in (("softbox", 9.0, 34.0, 40.0, 0.45), ("stand-lens", 0.0, 9.0, 40.05, 0.0)):
        panel_mesh = bpy.data.meshes.new(name)
        bm = bmesh.new()
        angles = np.linspace(0, 2 * math.pi, 96, endpoint=False)
        if inner > 0:
            near = [bm.verts.new((lens_at.x + inner * math.cos(t), lens_at.y + inner * math.sin(t), z)) for t in angles]
            far = [bm.verts.new((lens_at.x + outer * math.cos(t), lens_at.y + outer * math.sin(t), z)) for t in angles]
            for i in range(96):
                j = (i + 1) % 96
                bm.faces.new((near[i], far[i], far[j], near[j]))
        else:
            bm.faces.new([bm.verts.new((lens_at.x + outer * math.cos(t), lens_at.y + outer * math.sin(t), z)) for t in angles])
        bm.to_mesh(panel_mesh)
        bm.free()
        light = bpy.data.materials.new(name)
        light.use_nodes = True
        nodes = light.node_tree.nodes
        nodes.clear()
        emit = nodes.new("ShaderNodeEmission")
        emit.inputs["Color"].default_value = (*(cast / cast.max()), 1.0)
        emit.inputs["Strength"].default_value = glow
        out = nodes.new("ShaderNodeOutputMaterial")
        light.node_tree.links.new(emit.outputs[0], out.inputs["Surface"])
        panel_mesh.materials.append(light)
        panel = STAGE.add(name, panel_mesh)
        panel["stand"] = "shadowless"
        panel.visible_camera = False
        panel.visible_shadow = False
        panel.visible_diffuse = False
        panel.visible_volume_scatter = False
        panel.light_linking.receiver_collection = parts
        panel.light_linking.blocker_collection = parts


def main():
    """The camera on its own, on the stand, for a look at it."""
    global STAGE
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
    holder = camera()
    x0, y0, x1, y1 = bounds()
    softbox(holder)
    key.add(((x0 + x1) / 2, -(y0 + y1) / 2))
    STAGE.shoot("ticket-camera", (x0, y0, x1 - x0, y1 - y0), bleed=4.0, shadow=0.9, exposure=EXPOSURE, lens=False, sharp=2.0)


STAGE = None  # the stage the camera is built on: main's, or a scene's (scene.py)

if __name__ == "__main__":
    main()
