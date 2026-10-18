"""The watch: a Seiko Prospex Alpinist, the SPB119, as in the user's photograph, lying face up on the desk with its
strap undone.

A 39.5 mm stainless steel case, polished all over: a wide sloping bezel round a domed sapphire crystal, flanks that
round under to the back, and four lugs that fall away toward their tips. Two crowns, at 2 and at 4 o'clock: the one
at 2 turns the compass ring inside the crystal. Under the crystal, the cream dial and its sloping compass ring carry
the photograph itself, unwarped to square on (art/watch-dial.png, by art/watchphoto.py): its numerals, indices,
SEIKO, hands and date are the real ones, in the photograph's own light.

The strap is the user's: a vintage strap of oiled, pulled-up brown leather, in their photograph of it
(art/watch-strap-photo.jpg), and its top is that photograph, unwarped flat (art/watch-strap-*.png, by
art/strapphoto.py): its creases, its stitches at the lugs, by the buckle and at the tip, its four punched holes and
the photograph's own light on them are the real ones. Its shape is measured off the same photograph: straight and as
wide as the lugs all down, thick, its edges burnished near black, the long half drawn to a rounded point, the short
half folded round the bar of a heavy bead-blasted buckle under one wide keeper. Worn, it has taken the curve of the
wrist, so undone and put down face up the watch stands on its two halves: each bows down from the lugs to the desk,
holding the case's back a little off it, and from there lies flat, the tip of the long half lifting a little.

Built in millimetres, 12 o'clock up the page, the middle of the dial over the origin, and drawn MM em to the
millimetre."""

import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

from objects.flutelamp import spline, turned
from paint import linear
from solids import worn
from stage import ASSETS

ART = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "art")
DIAL_ART = os.path.join(ART, "watch-dial.png")
DIAL_ART_SIZE = 36.0

# Em to the millimetre: the case 39.5 mm across draws 4.1 em, so the watch, strap and all, fits where it lies.
MM = 4.1 / 39.5

# The case's section, radius and height in mm: up from the back round the flank, over the sloping bezel to its
# inner lip, and down inside to below the dial.
CASE = [
    (0.0, 0.4),
    (12.0, 0.4),
    (15.0, 0.7),
    (17.2, 1.5),
    (18.7, 2.7),
    (19.5, 4.0),
    (19.75, 5.8),
    (19.7, 7.8),
    (19.5, 8.8),
    (19.1, 9.4),
    (18.5, 9.9),
    (17.8, 10.35),
    (17.2, 10.65),
    (16.75, 10.8),
    (16.55, 10.7),
    (16.55, 7.3),
    (0.0, 7.3),
]
CRYSTAL_R = 16.6
CRYSTAL = (0.9, 10.85, 11.75)
DIAL_R = 13.3
DIAL_Z = 7.8
RING_Z = (7.9, 9.4)
# The lugs: each this far out from the middle across, this wide, reaching out to this far along the watch, their
# tops falling from this height at the case to this at their tips.
LUG_X = 10.15
LUG_W = 3.4
LUG_FROM = 14.0
LUG_TO = 23.2
LUG_TOP = (8.9, 6.9)
LUG_BOTTOM = 3.4
# The crowns: at these hours, this round, standing out this far from the flank, at this height, their knurl this
# many teeth.
CROWNS = ((2, 3.1, 3.6), (4, 3.4, 3.9))
CROWN_Z = 5.4
TEETH = 36
STEEL = (0.8, 0.8, 0.82)
CREAM_ROUGH = 0.5
# The strap's top, from the photograph: each half's picture runs from its end at the lugs to its far end, the strap's
# width across, dimmed this much (the pendant is brighter than the photograph's light); beside it, its creases' relief,
# which stands this many mm proud at most. Under the picture, the leather's grain (a scan, repeating every this many
# mm, its relief this strong), and its shine, this rough, duller in grain and handled patches. The leather's cut edges,
# sides and underneath, burnished this dark brown and this glossy.
STRAP_ART = os.path.join(ART, "watch-strap-{}.png")
RELIEF_ART = os.path.join(ART, "watch-strap-{}-relief.png")
TRIM = (0.02, 0.035)
DIM = 0.85
CREASE = 0.1
GRAIN = ("Leather030", 60.0, 1.4)
SHINE = 0.5
EDGE = "#2b170d"
EDGE_SHINE = 0.3
# A strap cut and worn by hand is never true: along it, over about this many mm, its width wanders this much either
# side, its thickness this much, and it twists this many degrees either way.
WANDER = (22.0, 0.14, 0.18, 1.6)
# The strap, its sizes measured off the photograph at 7.05 of its pixels to the mm, the lugs' 20 mm across: this wide,
# this thick at the lugs and this at its ends, its top crowned this much over its width, its edges rounded this much.
# Its end is tucked this far in under the case, round the spring bar. The short half runs this long from the bar to
# its fold round the buckle's bar; the long half runs this long, drawn to its point over the last of it as this half
# width, in mm, at these distances from the tip; its holes are this far from its bar, this far across from its middle,
# this round. Each half leaves its spring bar, this far out and this high, the case standing this much off the desk on
# them, heading down at this slope as the lugs aim it, and bows down to the desk over this length; on the desk it
# wanders a little to one side, this much a millimetre, as it was dropped; and from this far along, its tip lifts off
# the desk, curled round this radius.
STRAP_W = 20.0
STRAP_T = (4.2, 3.5)
CROWN = 0.35
EDGE_R = 1.1
TUCK = 3.0
SHORT = 64.1
LONG = 106.0
POINT = [(0.0, 0.0), (0.6, 2.6), (1.7, 4.1), (4.0, 6.3), (6.2, 8.0), (8.5, 9.25), (10.8, 9.9), (13.0, 10.0)]
HOLES = ((47.8, 54.5, 60.8, 67.3), -1.6, 1.75)
BAR = (20.8, 5.2)
RAISE = 2.7
AIM = 0.47
FALL = 24.0
DRIFT = (1 / 320.0, -1 / 380.0)
LIFT = ((90.0, 200.0), (92.0, 90.0))
# The keeper, a wide leather loop round the short half: from this far along it to this far, standing this far proud
# of it all round.
KEEPER = (40.1, 55.0, 1.2)
# The buckle, measured off the photograph too: a heavy frame round the short half's fold, its bar inside the fold this
# far along the strap; this wide outside and this wide inside (the strap's own width); its near side this far along
# the strap, its far side's outside this far and its inside this far; this thick, its far corners rounded this much.
# Bead-blasted: steel this grey and this rough. Its tongue, this wide and this thick, comes out of a slot this far
# along the strap, over the fold, and lies on the frame's far side to this far along.
BUCKLE_BAR = 62.4
BUCKLE = (24.0, 20.0, 59.3, 79.1, 72.6, 3.0, 3.0)
BLASTED = ((0.6, 0.6, 0.61), 0.52)
TONGUE = (3.8, 2.0, 59.6, 76.5)

# What the polished steel throws back: the pendant over the top right of the desk (desk.json's "lamp"), the bright
# mouth of its shade this far off in this direction, this wide, this bright; and the room's walls round the watch,
# this far off and this high, dim and warm. They light the watch alone and show only in it ("kept": desk.py keeps
# them, as it does no other shot's studio cards): without them its steel throws back only the dark room, and reads
# as black.
LAMP_FROM = (0.1, 0.68, 0.72)
LAMP_AT = (700.0, 110.0, (1.1, 0.8, 0.5))
WALLS = (450.0, 300.0, (0.09, 0.075, 0.058))

# The box the desk lays the watch out in, as wide as a longer strap once made it.
W = H = 2 * (118.0 + 20.0) * MM


def steel(name, rough=0.06):
    """Polished stainless steel, a little handled."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*STEEL, 1)
    shader.inputs["Metallic"].default_value = 1.0
    shader.inputs["Roughness"].default_value = rough
    worn(material, "Scratches003", 30.0, 0.05)
    return material


def printed(name):
    """The dial and its ring as photographed (DIAL_ART), laid on from straight over it, a satin finish."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Roughness"].default_value = CREAM_ROUGH
    coord = nodes.new("ShaderNodeTexCoord")
    place = nodes.new("ShaderNodeMapping")
    place.inputs["Scale"].default_value = (1 / DIAL_ART_SIZE, 1 / DIAL_ART_SIZE, 1)
    place.inputs["Location"].default_value = (0.5, 0.5, 0)
    links.new(coord.outputs["Object"], place.inputs["Vector"])
    art = nodes.new("ShaderNodeTexImage")
    art.image = bpy.data.images.load(DIAL_ART)
    art.interpolation = "Cubic"
    links.new(place.outputs["Vector"], art.inputs["Vector"])
    links.new(art.outputs["Color"], shader.inputs["Base Color"])
    return material


def sapphire(name):
    """The crystal: clear sapphire with an anti-reflective coat inside, which takes the edge off its reflections."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (1, 1, 1, 1)
    shader.inputs["Transmission Weight"].default_value = 1.0
    shader.inputs["Roughness"].default_value = 0.0
    # Sapphire's own index is 1.77; coated on both faces it throws back about as little as glass of this index.
    shader.inputs["IOR"].default_value = 1.2
    shader.inputs["Thin Film Thickness"].default_value = 140.0
    shader.inputs["Thin Film IOR"].default_value = 1.38
    # Glass lets a shadow ray through in a render only if told: the dial under it is lit by the lamp, not only by
    # what the room throws back.
    nodes, links = material.node_tree.nodes, material.node_tree.links
    path = nodes.new("ShaderNodeLightPath")
    through = nodes.new("ShaderNodeBsdfTransparent")
    either = nodes.new("ShaderNodeMixShader")
    links.new(path.outputs["Is Shadow Ray"], either.inputs[0])
    links.new(shader.outputs[0], either.inputs[1])
    links.new(through.outputs[0], either.inputs[2])
    links.new(either.outputs[0], nodes["Material Output"].inputs["Surface"])
    return material


def leather(name, art):
    """The strap's leather: on top the photograph of it (art, laid on by the mesh's UV) over the scanned grain of
    leather, so the pendant's light breaks into glints on it as it does on the wallet, its creases standing up from it;
    oiled, its shine soft and duller where handled; its cut edges, sides and underneath burnished dark and glossy (the
    mesh's "edge")."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Specular IOR Level"].default_value = 0.5
    shader.inputs["Sheen Weight"].default_value = 0.2
    shader.inputs["Sheen Roughness"].default_value = 0.5
    shader.inputs["Sheen Tint"].default_value = (1.0, 0.82, 0.66, 1)

    def image(path, colour=True):
        node = nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(path)
        if not colour:
            node.image.colorspace_settings.name = "Non-Color"
        node.interpolation = "Cubic"
        node.extension = "EXTEND"
        return node

    def mix(factor, a, b, blend="MIX"):
        node = nodes.new("ShaderNodeMix")
        node.data_type = "RGBA"
        node.blend_type = blend
        for socket, value in ((node.inputs["Factor"], factor), (node.inputs["A"], a), (node.inputs["B"], b)):
            if isinstance(value, (int, float)):
                socket.default_value = value
            elif isinstance(value, tuple):
                socket.default_value = value
            else:
                links.new(value, socket)
        return node.outputs["Result"]

    picture = image(STRAP_ART.format(art))
    relief = image(RELIEF_ART.format(art), colour=False)
    edge = nodes.new("ShaderNodeAttribute")
    edge.attribute_name = "edge"
    # The photograph's light was dimmer than the pendant's: its leather as dark here as there.
    dimmed = mix(1.0, picture.outputs["Color"], (DIM, DIM, DIM, 1), "MULTIPLY")
    links.new(mix(edge.outputs["Fac"], dimmed, (*linear(EDGE), 1)), shader.inputs["Base Color"])
    # The grain, from the scan, under the creases from the photograph.
    asset, size, strength = GRAIN
    coord = nodes.new("ShaderNodeTexCoord")
    place = nodes.new("ShaderNodeMapping")
    place.inputs["Scale"].default_value = (1 / size, 1 / size, 1 / size)
    links.new(coord.outputs["Object"], place.inputs["Vector"])
    scans = {}
    for kind in ("NormalGL", "Roughness"):
        scan = image(os.path.join(ASSETS, asset, f"{asset}_1K-JPG_{kind}.jpg"), colour=False)
        scan.extension = "REPEAT"
        links.new(place.outputs["Vector"], scan.inputs["Vector"])
        scans[kind] = scan
    grain = nodes.new("ShaderNodeNormalMap")
    grain.inputs["Strength"].default_value = strength
    links.new(scans["NormalGL"].outputs["Color"], grain.inputs["Color"])
    creases = nodes.new("ShaderNodeBump")
    creases.inputs["Strength"].default_value = 0.6
    creases.inputs["Distance"].default_value = CREASE
    links.new(relief.outputs["Color"], creases.inputs["Height"])
    links.new(grain.outputs["Normal"], creases.inputs["Normal"])
    links.new(creases.outputs["Normal"], shader.inputs["Normal"])
    # The shine: the scan's own unevenness about SHINE; the burnished edge glossier.
    shine = nodes.new("ShaderNodeMapRange")
    shine.inputs["To Min"].default_value = SHINE - 0.12
    shine.inputs["To Max"].default_value = SHINE + 0.12
    links.new(scans["Roughness"].outputs["Color"], shine.inputs["Value"])
    rough = nodes.new("ShaderNodeMix")
    rough.data_type = "FLOAT"
    links.new(edge.outputs["Fac"], rough.inputs["Factor"])
    links.new(shine.outputs[0], rough.inputs["A"])
    rough.inputs["B"].default_value = EDGE_SHINE
    links.new(rough.outputs["Result"], shader.inputs["Roughness"])
    worn(material, "SurfaceImperfections003", 40.0, 0.15)
    worn(material, "Scratches003", 50.0, 0.08)
    return material


def blasted(name):
    """Bead-blasted steel: grey, and matte from the fine pits the blasting leaves."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    grey, rough = BLASTED
    shader.inputs["Base Color"].default_value = (*grey, 1)
    shader.inputs["Metallic"].default_value = 1.0
    shader.inputs["Roughness"].default_value = rough
    pits = nodes.new("ShaderNodeTexNoise")
    pits.inputs["Scale"].default_value = 9.0
    pits.inputs["Detail"].default_value = 2.0
    coord = nodes.new("ShaderNodeTexCoord")
    links.new(coord.outputs["Object"], pits.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.02
    links.new(pits.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    worn(material, "Scratches003", 30.0, 0.04)
    return material


def polygon_prism(name, outline, z0, z1, material, top=None, bevel=0.0):
    """An outline (x, y in mm, y up) stood up from z0 to z1, its top edge rounded by bevel; top, if given, is the
    material of its top face."""
    bm = bmesh.new()
    bottom = [bm.verts.new((x, y, z0)) for x, y in outline]
    lid = [bm.verts.new((x, y, z1)) for x, y in outline]
    bm.faces.new(bottom[::-1])
    cap = bm.faces.new(lid)
    count = len(outline)
    for i in range(count):
        j = (i + 1) % count
        bm.faces.new((bottom[i], bottom[j], lid[j], lid[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bevel > 0:
        bm.normal_update()
        bmesh.ops.bevel(bm, geom=list(cap.edges), offset=bevel, segments=3, profile=0.5, affect="EDGES", clamp_overlap=True)
    if top is not None:
        for face in bm.faces:
            face.material_index = 1 if face.normal.z > 0.97 else 0
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    if top is not None:
        mesh.materials.append(top)
    return mesh


def case(stage, polish):
    made = [stage.add("watch-case", turned("watch-case", CASE, around=360))]
    made[0].data.materials.append(polish)
    # The lugs, each its outline stood up, its top falling toward the tip.
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, x1 = sx * LUG_X, sx * (LUG_X + LUG_W)
            outline = [(x0, sy * LUG_FROM), (x1, sy * LUG_FROM), (x1, sy * (LUG_TO - 1.2)), (sx * (LUG_X + LUG_W - 0.4), sy * LUG_TO), (sx * (LUG_X + 0.4), sy * LUG_TO), (x0, sy * (LUG_TO - 1.2))]
            if sx * sy < 0:
                outline = outline[::-1]
            mesh = polygon_prism(f"watch-lug-{sx}{sy}", outline, LUG_BOTTOM, LUG_TOP[0], polish, bevel=1.1)
            co = np.empty(len(mesh.vertices) * 3)
            mesh.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            along = np.clip((np.abs(co[:, 1]) - LUG_FROM) / (LUG_TO - LUG_FROM), 0, 1)
            top = co[:, 2] > LUG_BOTTOM + 0.5
            fall = (LUG_TOP[0] - LUG_TOP[1]) * along**1.4
            co[:, 2] = np.where(top, co[:, 2] - fall, co[:, 2])
            mesh.vertices.foreach_set("co", co.ravel())
            mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
            obj = stage.add(mesh.name, mesh)
            obj.modifiers.new("normals", "WEIGHTED_NORMAL").keep_sharp = True
            made.append(obj)
    # The crowns, knurled, on short necks out of the flank.
    for hour, radius, reach in CROWNS:
        angle = math.radians(90 - hour * 30)
        teeth = []
        for k in range(TEETH * 4):
            a = 2 * math.pi * k / (TEETH * 4)
            r = radius - (0.18 if (k // 2) % 2 else 0.0)
            teeth.append((r * math.cos(a), r * math.sin(a)))
        crown = polygon_prism(f"watch-crown-{hour}", teeth, 0.0, reach - 0.4, polish, bevel=0.35)
        cap = turned(f"watch-crown-cap-{hour}", [(0.0, reach - 0.2), (radius - 0.5, reach - 0.35), (radius - 0.3, reach - 0.55)], around=96)
        neck = turned(f"watch-crown-neck-{hour}", [(0.0, -1.8), (1.7, -1.8), (1.7, 0.2), (0.0, 0.2)], around=64)
        for mesh in (crown, cap, neck):
            if not mesh.materials:
                mesh.materials.append(polish)
            obj = stage.add(mesh.name, mesh)
            # Stood on its axis, then laid along the radius out of the flank.
            obj.matrix_world = Matrix.Translation((19.4 * math.cos(angle), 19.4 * math.sin(angle), CROWN_Z)) @ Matrix.Rotation(angle, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y")
            made.append(obj)
    return made


def dial(stage, paper):
    made = []
    disc = turned("watch-dial", [(0.0, DIAL_Z), (DIAL_R + 0.1, DIAL_Z), (DIAL_R + 0.1, DIAL_Z - 0.3), (0.0, DIAL_Z - 0.3)], around=256)
    disc.materials.append(paper)
    made.append(stage.add("watch-dial", disc))
    # The compass ring, sloping up from the dial's edge to the crystal's.
    ring = turned("watch-ring", [(DIAL_R, RING_Z[0]), (CRYSTAL_R - 0.05, RING_Z[1]), (CRYSTAL_R - 0.05, RING_Z[0] - 0.3)], around=360)
    ring.materials.append(paper)
    made.append(stage.add("watch-ring", ring))
    return made


def crystal(stage):
    """The domed crystal: a shell of even thickness, so it bends what is under it hardly at all."""
    thick, edge, top = CRYSTAL
    dome = [(r, edge + (top - edge) * (1 - (r / CRYSTAL_R) ** 2)) for r in np.linspace(0, CRYSTAL_R, 48)]
    profile = dome + [(r, z - thick) for r, z in dome[::-1]]
    mesh = turned("watch-crystal", profile, around=256)
    mesh.materials.append(sapphire("watch-sapphire"))
    return stage.add("watch-crystal", mesh)


def strap_path(length, side, drift, lift):
    """The centre line of a strap half, from its end tucked round the spring bar under the case: out of the bar
    heading down (AIM) and bowed down to the desk, along the desk with a little drift to one side, and its tip curled up
    off it (lift: from how far along, round what radius). The heights are of the strap's middle, which lies half its
    thickness off the desk."""
    y0, z0 = BAR
    z0 += RAISE
    s = np.arange(-TUCK, length + 0.1, 0.2)
    s[-1] = length
    heading = np.cumsum(np.where(s > FALL, drift, 0.0)) * 0.2
    x = np.cumsum(np.sin(heading)) * 0.2
    x -= x[0]
    y = side * (y0 - TUCK + np.concatenate(([0.0], np.cumsum(np.cos(heading[1:]) * np.diff(s)))))
    thick = thickness(s, length)
    # Down from the bar to the desk as a stiff band bends: leaving at the lugs' slope, meeting the desk flat.
    t = np.clip(s / FALL, 0, 1)
    z = (2 * t**3 - 3 * t**2 + 1) * z0 - (t**3 - 2 * t**2 + t) * FALL * AIM + (3 * t**2 - 2 * t**3) * thick / 2
    start, radius = lift
    z = z + np.maximum(s - start, 0) ** 2 / (2 * radius)
    centres = np.column_stack((x, y, z))
    ahead = np.gradient(centres, axis=0)
    ahead /= np.linalg.norm(ahead, axis=1)[:, None]
    across = np.cross(ahead, (0.0, 0.0, 1.0))
    across /= np.linalg.norm(across, axis=1)[:, None]
    up = np.cross(across, ahead)
    return centres, s, ahead, across, up


def thickness(s, length):
    """The strap's thickness along it: full at the lugs, thinning toward its end."""
    return STRAP_T[0] + (STRAP_T[1] - STRAP_T[0]) * np.clip(s / length, 0, 1)


def section():
    """A strap's section, round from its top middle: a rectangle with rounded corners, its points evenly spread, so
    the top, where the holes and the stitches are, is as finely made across as along. Each point is (x, z) in shares of
    the straight part of the half width and of the half thickness, and the direction (nx, nz) of its round, (0, 0) on
    the straight runs."""
    corner = np.linspace(0, math.pi / 2, 7)
    points = []
    for cx, cz, start in ((1, 1, 0.0), (-1, 1, math.pi / 2), (-1, -1, math.pi), (1, -1, 1.5 * math.pi)):
        for a in corner:
            points.append((cx, cz, math.cos(start + a), math.sin(start + a)))
        if cz > 0 and cx > 0:
            points += [(t, 1, 0.0, 0.0) for t in np.linspace(1, -1, 81)[1:-1]]
        elif cz < 0 and cx < 0:
            points += [(t, -1, 0.0, 0.0) for t in np.linspace(-1, 1, 21)[1:-1]]
    return np.array(points)


def sweep(name, frame, half, thick, crown, edge_r, rolled=0.0):
    """A band of leather (or steel) along a path: at each of its rings (frame: centres, ahead, across, up) this half
    width and thickness, its top crowned, its edges rounded; rolled, the last that many mm round off in its thickness,
    as leather does folded round a bar. Returns the mesh, and what each corner is: across it in mm, and whether on top
    (with the two ends' middles last)."""
    centres, ahead, across, up = frame
    shape = section()
    count = len(shape)
    round_ = np.minimum(edge_r, np.minimum(half * 0.95, thick / 2 * 0.95))
    straight = (shape[:, 2] == 0) & (shape[:, 3] == 0)
    inset_x = (half - round_)[:, None]
    inset_z = (thick / 2 - round_)[:, None]
    x = np.where(straight[None, :], shape[None, :, 0] * inset_x, shape[None, :, 0] * inset_x + round_[:, None] * shape[None, :, 2])
    z = np.where(straight[None, :], shape[None, :, 1] * inset_z + np.sign(shape[None, :, 1]) * round_[:, None], shape[None, :, 1] * inset_z + round_[:, None] * shape[None, :, 3])
    top = (shape[:, 1] > 0) & (straight | (shape[:, 3] > 0.7))
    z = z + np.where(top[None, :], crown * np.clip(1 - (x / half[:, None]) ** 2, 0, 1), 0.0)
    if rolled > 0:
        along = np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(centres, axis=0), axis=1))))
        u = np.clip((along - (along[-1] - rolled)) / rolled, 0, 1)
        z = z * np.sqrt(1 - u**2 * 0.97)[:, None]
    verts = centres[:, None, :] + x[..., None] * across[:, None, :] + z[..., None] * up[:, None, :]
    rings = len(centres)
    i = np.arange(rings - 1)[:, None]
    j = np.arange(count)[None, :]
    a, b = (i * count + j).ravel(), (i * count + (j + 1) % count).ravel()
    faces = np.column_stack((a, b, b + count, a + count)).tolist()
    verts = verts.reshape(-1, 3)
    first, last = len(verts), len(verts) + 1
    verts = np.vstack((verts, centres[0], centres[-1]))
    faces += [(first, (k + 1) % count, k) for k in range(count)]
    faces += [(last, (rings - 1) * count + k, (rings - 1) * count + (k + 1) % count) for k in range(count)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts.tolist(), [], faces)
    made = bmesh.new()
    made.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(made, faces=made.faces)
    made.to_mesh(mesh)
    made.free()
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    over = np.concatenate((x.ravel(), [0.0, 0.0]))
    on_top = np.concatenate((np.tile(top, rings), [False, False]))
    return mesh, over, on_top, count


def mapped(mesh, along, over, length, wide):
    """A UV layer laying the half's picture on: across it edge to edge over wide (the half width), the picture's own
    margins (TRIM, its share at either side, where the photograph's edge highlight falls just inside) left over the
    rounded edges; down it from its end at the lugs (at the picture's top) to length."""
    u = np.clip(TRIM[0] + (1 - TRIM[0] - TRIM[1]) * (over / (2 * wide) + 0.5), 0, 1)
    v = np.clip(1 - along / length, 0, 1)
    layer = mesh.uv_layers.new(name="UVMap")
    corners = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", corners)
    layer.data.foreach_set("uv", np.column_stack((u[corners], v[corners])).astype(np.float32).ravel())


def wander(seed, s, scale, amount):
    """A smooth, uneven wander along a strap, s in mm: a few sines of random phase, the widest scale longest."""
    rng = np.random.default_rng(seed)
    out = np.zeros_like(s)
    for k in range(4):
        out += np.sin(2 * math.pi * s / (scale / 1.7**k) + rng.uniform(0, 2 * math.pi)) / 1.7**k
    return amount * out / 2.2


def twisted(frame, seed, s):
    """A strap's frame twisted a little about its centre line, by a wander of up to WANDER's degrees."""
    centres, ahead, across, up = frame
    scale, _, _, degrees = WANDER
    turn = np.radians(wander(seed, s, scale * 1.6, degrees))[:, None]
    return centres, ahead, across * np.cos(turn) + up * np.sin(turn), up * np.cos(turn) - across * np.sin(turn)


def sample(path, u, v):
    """A grey image's values at u, v (0 to 1, v up), between its pixels."""
    picture = bpy.data.images.load(path, check_existing=True)
    cols, rows = picture.size
    pixels = np.empty(cols * rows * 4, dtype=np.float32)
    picture.pixels.foreach_get(pixels)
    grey = pixels.reshape(rows, cols, 4)[..., 0]
    x, y = np.clip(u, 0, 1) * (cols - 1), np.clip(v, 0, 1) * (rows - 1)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, cols - 1), np.minimum(y0 + 1, rows - 1)
    fx, fy = x - x0, y - y0
    return (grey[y0, x0] * (1 - fx) + grey[y0, x1] * fx) * (1 - fy) + (grey[y1, x0] * (1 - fx) + grey[y1, x1] * fx) * fy


def creased(mesh, frame, count, along, over, top, half, wide, length, art):
    """Its top pushed up and down by the photograph's creases (art's relief), less toward the edges (half, its half
    width at each ring), and its attributes and UV (the picture wide either side of the middle): "edge" for the
    burnished edges, sides and underneath."""
    centres, ahead, across, up = frame
    u = np.clip(TRIM[0] + (1 - TRIM[0] - TRIM[1]) * (over / (2 * wide) + 0.5), 0, 1)
    v = np.clip(1 - along / length, 0, 1)
    rise = (sample(RELIEF_ART.format(art), u, v) - 0.5) * 2 * CREASE
    half = np.concatenate((np.repeat(half, count), [half[0], half[-1]]))
    inward = np.clip((half - np.abs(over)) / 1.5, 0, 1)
    co = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    normal_up = np.concatenate((np.repeat(up, count, axis=0), [up[0], up[-1]]))
    co += normal_up * (rise * inward * top)[:, None]
    mesh.vertices.foreach_set("co", co.ravel())
    edge = np.clip((np.abs(over) - (half - 0.3)) / 0.3, 0, 1) + (~top)
    attribute = mesh.attributes.new("edge", "FLOAT", "POINT")
    attribute.data.foreach_set("value", np.clip(edge, 0, 1).astype(np.float32))
    mapped(mesh, along, over, length, wide)


def punched(stage, obj, frame, s, thick, material):
    """The long half's holes, punched clean through it, their walls burnished like its edges."""
    centres, ahead, across, up = frame
    middles, off, radius = HOLES
    verts, faces = [], []
    around = 40
    for middle in middles:
        k = int(np.searchsorted(s, middle))
        base = len(verts)
        for z in (-thick[k], thick[k]):
            for a in np.linspace(0, 2 * math.pi, around, endpoint=False):
                verts.append(tuple(centres[k] + off * across[k] + radius * (math.cos(a) * across[k] + math.sin(a) * ahead[k]) + z * up[k]))
        faces += [(base + i, base + (i + 1) % around, base + around + (i + 1) % around, base + around + i) for i in range(around)]
        faces += [tuple(base + i for i in range(around))[::-1], tuple(base + around + i for i in range(around))]
    mesh = bpy.data.meshes.new(f"{obj.name}-punch")
    mesh.from_pydata(verts, [], faces)
    mesh.attributes.new("edge", "FLOAT", "POINT").data.foreach_set("value", np.ones(len(verts), dtype=np.float32))
    mesh.uv_layers.new(name="UVMap")
    mesh.materials.append(material)
    punch = stage.add(mesh.name, mesh)
    cut = obj.modifiers.new("punch", "BOOLEAN")
    cut.operation = "DIFFERENCE"
    cut.solver = "EXACT"
    cut.object = punch
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    done = bpy.data.meshes.new_from_object(obj.evaluated_get(graph), preserve_all_data_layers=True, depsgraph=graph)
    obj.modifiers.remove(cut)
    obj.data = done
    bpy.data.objects.remove(punch)


def strap(stage, name, length, side, drift, lift, material, art, long=False):
    """A strap half: leather along its centre line, crowned and rounded at the edges, as wide as the lugs all down
    but wandering a little in width, thickness and twist as a hand-cut, worn strap does; its top carries the photograph
    (by UV) and is pushed up by its creases; the long half is drawn to its point and its holes punched through, the
    short one rolled round the buckle's bar."""
    centres, s, ahead, across, up = strap_path(length, side, drift, lift)
    scale, width, depth, _ = WANDER
    seed = 7 if long else 3
    half = STRAP_W / 2 + wander(seed, s, scale, width)
    if long:
        back, wide = np.array(POINT).T
        half = np.minimum(half, np.maximum(np.interp(length - s, back, wide), 0.3))
    thick = thickness(s, length) + wander(seed + 1, s, scale, depth)
    frame = twisted((centres, ahead, across, up), seed + 2, s)
    mesh, over, top, count = sweep(name, frame, half, thick, CROWN, EDGE_R, 0.0 if long else thick[-1] / 2)
    along = np.concatenate((np.repeat(s, count), [s[0], s[-1]]))
    creased(mesh, frame, count, along, over, top, half, STRAP_W / 2, length, art)
    mesh.materials.append(material)
    obj = stage.add(name, mesh)
    if long:
        punched(stage, obj, frame, s, thick, material)
    return obj, (centres, s, ahead, across, up), half, thick


def keeper(stage, path, half, thick, material):
    """The keeper, a wide leather loop round the short half, standing proud of it all round and softly rounded, as
    leather folded round on itself is; its top is the keeper in the photograph, its bottom hidden under the strap, on
    the desk."""
    centres, s, ahead, across, up = path
    start, end, proud = KEEPER
    pick = (s >= start) & (s <= end)
    lifted = centres[pick] + up[pick] * proud * 0.5
    frame = twisted((lifted, ahead[pick], across[pick], up[pick]), 11, s[pick])
    # Swelling a little in the middle, where the strap inside pushes it out.
    swell = 0.25 * np.sin(np.clip((s[pick] - start) / (end - start), 0, 1) * math.pi)
    wide = half[pick] + proud + swell * 0.4
    mesh, over, top, count = sweep("watch-keeper", frame, wide, thick[pick] + proud + swell, 0.45, 1.9)
    along = np.concatenate((np.repeat(s[pick], count), [start, end]))
    creased(mesh, frame, count, along, over, top, wide, STRAP_W / 2 + proud, SHORT, "short")
    mesh.materials.append(material)
    return stage.add(mesh.name, mesh)


def rounded(x0, x1, y0, y1, near, far, n=24):
    """A rectangle's outline, counter-clockwise, its near corners (at y0) rounded by near and its far ones by far."""
    points = []
    for cx, cy, r, a0 in ((x1 - far, y1 - far, far, 0.0), (x0 + far, y1 - far, far, 90.0), (x0 + near, y0 + near, near, 180.0), (x1 - near, y0 + near, near, 270.0)):
        for a in np.radians(np.linspace(a0, a0 + 90, n)):
            points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return points


def buckle(stage, path, metal):
    """The buckle at the short half's end: a heavy frame lying on the desk round the strap's fold, its bar inside the
    fold, its sides slim and its far side broad, all of it rounded over like a cushion; and its tongue, a flat bar out
    of the strap's slot, over the fold and lying on the frame's far side."""
    centres, s, ahead, across, up = path
    at = int(np.searchsorted(s, BUCKLE_BAR))
    forward = np.array([ahead[at][0], ahead[at][1], 0.0])
    forward /= np.linalg.norm(forward)
    side = np.array([-forward[1], forward[0], 0.0])
    outside, inside, near, far, far_in, thick, corner = BUCKLE
    # In the buckle's own frame: x across, y forward from the bar's middle. The frame is a band swept round the
    # middle of its wire: as wide as the gap between outside and inside, the far side's broad, the near side's under
    # the fold; its corners rounded.
    x = (outside + inside) / 4
    # The near side, the bar, runs inside the fold, its corners with it.
    y0 = near - BUCKLE_BAR + 0.6
    y1 = (far + far_in) / 2 - BUCKLE_BAR
    round_ = min(corner + 0.5, (y1 - y0) / 2)
    loop = np.array(rounded(-x, x, y0, y1, 2.0, round_, n=40) + rounded(-x, x, y0, y1, 2.0, round_, n=40)[:1])
    # Evenly along the outline, which runs straight between its rounded corners.
    run = np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(loop, axis=0), axis=1))))
    along = np.arange(0.0, run[-1], 0.1)
    along = np.append(along, run[-1])
    line = np.column_stack((np.interp(along, run, loop[:, 0]), np.interp(along, run, loop[:, 1]), np.full_like(along, thick / 2)))
    ahead_f = np.gradient(line, axis=0)
    ahead_f[0] = ahead_f[-1] = line[1] - line[-2]
    ahead_f /= np.linalg.norm(ahead_f, axis=1)[:, None]
    across_f = np.cross(ahead_f, (0.0, 0.0, 1.0))
    across_f /= np.linalg.norm(across_f, axis=1)[:, None]
    up_f = np.cross(across_f, ahead_f)
    side_wire = (outside - inside) / 4
    far_wire = (far - far_in) / 2
    # Broadening smoothly from the sides into the far side round its corners.
    t = np.clip((line[:, 1] - (y1 - round_ - 3.0)) / (round_ + 3.0), 0, 1)
    t = t * t * (3 - 2 * t)
    half = side_wire + (far_wire - side_wire) * t
    # The sides slimmer in height too, under the fold's leather where they meet the bar.
    high = thick * (0.78 + 0.22 * t)
    line[:, 2] = high / 2
    mesh, *_ = sweep("watch-buckle", (line, ahead_f, across_f, up_f), half, high, 0.5, 1.1)
    mesh.materials.append(metal)
    frame = mesh
    bar = centres[at]
    placed = Matrix(((*side, 0.0), (*forward, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0))).transposed()
    placed.translation = Vector((bar[0], bar[1], 0.0))
    made = [stage.add("watch-buckle", frame)]
    made[0].matrix_world = placed
    # The tongue: out of the slot, over the fold, down onto the frame's far side.
    wide, deep, slot, tip = TONGUE
    top = thickness(np.array([SHORT]), SHORT)[0]
    points = [(slot - 1.0, top * 0.45), (BUCKLE_BAR, top + deep / 2 + 0.1), (BUCKLE_BAR + 4.0, top + deep / 2 - 0.2), (far_in - 0.5, thick + 0.5 + deep / 2), (tip, thick + 0.4 + deep / 2)]
    points = np.array([bar * np.array([1, 1, 0]) + (y - BUCKLE_BAR) * forward + np.array([0.0, 0.0, z]) for y, z in points])
    line, along = spline(points, 0.1)
    ahead_t = np.gradient(line, axis=0)
    ahead_t /= np.linalg.norm(ahead_t, axis=1)[:, None]
    across_t = np.repeat(side[None, :], len(line), axis=0)
    up_t = np.cross(across_t, ahead_t)
    tongue, *_ = sweep("watch-tongue", (line, ahead_t, across_t, up_t), np.full_like(along, wide / 2), np.full_like(along, deep), 0.1, 0.45)
    tongue.materials.append(metal)
    made.append(stage.add("watch-tongue", tongue))
    return made


def room(stage):
    """The lamp's face and the room's walls, seen only in the watch's steel and glass."""
    made = []
    distance, size, glow = LAMP_AT
    towards = np.array(LAMP_FROM) / np.linalg.norm(LAMP_FROM)
    centre = towards * distance
    across = np.cross(-towards, (0.0, 0.0, 1.0))
    across /= np.linalg.norm(across)
    up = np.cross(across, -towards)
    lamp = bpy.data.meshes.new("watch-lamp")
    lamp.from_pydata([tuple(centre + size / 2 * (i * across + j * up)) for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))], [], [(0, 1, 2, 3)])
    radius, high, warm = WALLS
    around = np.linspace(0, 2 * math.pi, 96, endpoint=False)
    walls = bpy.data.meshes.new("watch-walls")
    walls.from_pydata([(radius * math.cos(a), radius * math.sin(a), z) for a in around for z in (0.0, high)], [], [(2 * k, 2 * ((k + 1) % 96), 2 * ((k + 1) % 96) + 1, 2 * k + 1) for k in range(96)])
    for mesh, light in ((lamp, glow), (walls, warm)):
        material = bpy.data.materials.new(mesh.name)
        material.use_nodes = True
        nodes = material.node_tree.nodes
        nodes.remove(nodes["Principled BSDF"])
        emit = nodes.new("ShaderNodeEmission")
        emit.inputs["Color"].default_value = (*light, 1)
        material.node_tree.links.new(emit.outputs[0], nodes["Material Output"].inputs["Surface"])
        mesh.materials.append(material)
        obj = stage.add(mesh.name, mesh)
        for flag in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission", "visible_volume_scatter"):
            setattr(obj, flag, False)
        obj["kept"] = True
        made.append(obj)
    return made


def parts(stage):
    polish = steel("watch-steel")
    paper = printed("watch-paper")
    made = case(stage, polish) + dial(stage, paper) + [crystal(stage)]
    for part in made:
        part.location.z += RAISE
    short_hide = leather("watch-leather-short", "short")
    short, path, half, thick = strap(stage, "watch-strap-short", SHORT, 1, DRIFT[0], LIFT[0], short_hide, "short")
    made += [short, keeper(stage, path, half, thick, short_hide), *buckle(stage, path, blasted("watch-buckle-steel"))]
    long, *_ = strap(stage, "watch-strap-long", LONG, -1, DRIFT[1], LIFT[1], leather("watch-leather-long", "long"), "long", long=True)
    made.append(long)
    return made + room(stage)


def build(stage):
    made = parts(stage)
    # Parts placed by their rotation and location have their matrices only once the scene is updated.
    bpy.context.view_layer.update()
    for part in made:
        part.matrix_world = Matrix.Translation((W / 2, -H / 2, 0)) @ Matrix.Scale(MM, 4) @ part.matrix_world
    stage.shoot("watch", (0, 0, W, H), lens=False)


SHOTS = {"watch": build}
