"""The watch: a Seiko Prospex Alpinist, the SPB119, as in the user's photograph, lying face up on the desk with its
strap undone.

A 39.5 mm stainless steel case, polished all over: a wide sloping bezel round a domed sapphire crystal, flanks that
round under to the back, and four lugs that fall away toward their tips. Two crowns, at 2 and at 4 o'clock: the one
at 2 turns the compass ring inside the crystal. Under the crystal, the cream dial and its sloping compass ring carry
the photograph itself, unwarped to square on (art/watch-dial.png, by art/watchphoto.py): its numerals, indices,
SEIKO, hands and date are the real ones, in the photograph's own light.

The strap is brown leather, cream stitched at the lug ends. Worn, it has taken the curve of the wrist, so undone and
put down face up the watch stands on its two halves: each bows down from the lugs to the desk, holding the case's
back a little off it, and from there lies flat, the tip of the long half lifting a little where it was cut.

Built in millimetres, 12 o'clock up the page, the middle of the dial over the origin, and drawn MM em to the
millimetre."""

import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

from objects.flutelamp import spline, turned, tube
from paint import linear
from solids import worn

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
# Oiled, pulled-up leather, as in the photograph: a brown that goes darker where the oil has gathered and paler,
# toward tan, where the leather has been stretched over the wrist.
LEATHER = "#5e2e20"
LEATHER_DARK = "#311610"
LEATHER_WORN = "#97603f"
STITCH = "#e3d6b8"
# The strap: this wide at the lugs, narrowing to this at the buckle and the tip, this thick. The short half, this long
# from the lug, ends in the buckle; the long half, this long, carries holes this far from its lug, this far apart,
# this round. Each half leaves its spring bar, this far out and this high, the case standing this much off the desk on
# them, heading down at this slope as the lugs aim it, and bows down to the desk over this length; on the desk it
# wanders a little to one side, this much a millimetre, as it was dropped; and from this far along, its tip lifts off
# the desk, curled round this radius.
STRAP_W = (20.0, 18.0)
STRAP_T = 3.6
SHORT = 72.0
LONG = 118.0
HOLES = (72.0, 6.5, 7, 0.85)
BAR = (20.8, 5.2)
RAISE = 2.5
AIM = 0.47
FALL = 24.0
DRIFT = (1 / 320.0, -1 / 380.0)
LIFT = ((64.0, 200.0), (102.0, 90.0))
BUCKLE = (22.0, 17.0, 1.1)

# What the polished steel throws back: the pendant over the top right of the desk (desk.json's "lamp"), the bright
# mouth of its shade this far off in this direction, this wide, this bright; and the room's walls round the watch,
# this far off and this high, dim and warm. They light the watch alone and show only in it ("kept": desk.py keeps
# them, as it does no other shot's studio cards): without them its steel throws back only the dark room, and reads
# as black.
LAMP_FROM = (0.1, 0.68, 0.72)
LAMP_AT = (700.0, 110.0, (1.1, 0.8, 0.5))
WALLS = (450.0, 300.0, (0.09, 0.075, 0.058))

W = H = 2 * (LONG + 20.0) * MM


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


def leather(name):
    """Brown leather: the scan's grain and gloss over a brown that darkens toward the painted edges and wears paler
    on top, the cream stitching and the holes (the mesh's "edge", "stitch", "hole" and "wear")."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Sheen Weight"].default_value = 0.35
    shader.inputs["Sheen Roughness"].default_value = 0.45
    shader.inputs["Sheen Tint"].default_value = (1.0, 0.85, 0.7, 1)
    shader.inputs["Specular IOR Level"].default_value = 0.3

    def attribute(name):
        node = nodes.new("ShaderNodeAttribute")
        node.attribute_name = name
        return node.outputs["Fac"]

    def mix(factor, a, b):
        node = nodes.new("ShaderNodeMix")
        node.data_type = "RGBA"
        links.new(factor, node.inputs["Factor"])
        for socket, value in ((node.inputs["A"], a), (node.inputs["B"], b)):
            if isinstance(value, tuple):
                socket.default_value = value
            else:
                links.new(value, socket)
        return node.outputs["Result"]

    coord = nodes.new("ShaderNodeTexCoord")
    # The pull-up: broad clouds of dark and pale, and through them fine streaks along the strap, where the fibres
    # were stretched.
    mottle = nodes.new("ShaderNodeTexNoise")
    mottle.inputs["Scale"].default_value = 0.06
    mottle.inputs["Detail"].default_value = 6.0
    mottle.inputs["Roughness"].default_value = 0.6
    links.new(coord.outputs["Object"], mottle.inputs["Vector"])
    stretched = nodes.new("ShaderNodeMapping")
    stretched.inputs["Scale"].default_value = (2.2, 0.25, 2.2)
    links.new(coord.outputs["Object"], stretched.inputs["Vector"])
    streaks = nodes.new("ShaderNodeTexNoise")
    streaks.inputs["Scale"].default_value = 0.9
    streaks.inputs["Detail"].default_value = 8.0
    streaks.inputs["Roughness"].default_value = 0.7
    links.new(stretched.outputs["Vector"], streaks.inputs["Vector"])
    blend = nodes.new("ShaderNodeMath")
    blend.operation = "MULTIPLY_ADD"
    blend.inputs[1].default_value = 0.55
    links.new(mottle.outputs["Fac"], blend.inputs[0])
    links.new(streaks.outputs["Fac"], blend.inputs[2])
    contrast = nodes.new("ShaderNodeMapRange")
    contrast.inputs["From Min"].default_value = 0.65
    contrast.inputs["From Max"].default_value = 1.05
    links.new(blend.outputs[0], contrast.inputs["Value"])
    colour = mix(contrast.outputs[0], (*linear(LEATHER_DARK), 1), (*linear(LEATHER_WORN), 1))
    colour = mix(attribute("wear"), (*linear(LEATHER), 1), colour)
    colour = mix(attribute("edge"), colour, (*linear(LEATHER_DARK), 1))
    colour = mix(attribute("hole"), colour, (0.01, 0.006, 0.004, 1))
    colour = mix(attribute("stitch"), colour, (*linear(STITCH), 1))
    links.new(colour, shader.inputs["Base Color"])
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1 / 18.0, 1 / 18.0, 1 / 18.0)
    links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    for kind, socket in (("Roughness", shader.inputs["Roughness"]), ("Displacement", None)):
        scan = nodes.new("ShaderNodeTexImage")
        scan.image = bpy.data.images.load(os.path.join(os.path.dirname(ART), "assets", "Leather030", f"Leather030_1K-JPG_{kind}.jpg"))
        scan.image.colorspace_settings.name = "Non-Color"
        scan.projection = "BOX"
        scan.projection_blend = 0.3
        links.new(mapping.outputs["Vector"], scan.inputs["Vector"])
        if socket is not None:
            rough = nodes.new("ShaderNodeMapRange")
            rough.inputs["To Min"].default_value = 0.5
            rough.inputs["To Max"].default_value = 0.8
            links.new(scan.outputs["Color"], rough.inputs["Value"])
            links.new(rough.outputs[0], socket)
        else:
            bump = nodes.new("ShaderNodeBump")
            bump.inputs["Distance"].default_value = 0.035
            links.new(scan.outputs["Color"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], shader.inputs["Normal"])
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
    """The centre line of a strap half: out of its spring bar heading down (AIM) and bowed down to the desk, along the
    desk with a little drift to one side, and its tip curled up off it (lift: from how far along, round what
    radius)."""
    y0, z0 = BAR
    z0 += RAISE
    s = np.arange(0.0, length + 0.2, 0.2)
    heading = np.cumsum(np.where(s > FALL, drift, 0.0)) * 0.2
    x = np.cumsum(np.sin(heading)) * 0.2
    y = side * (y0 + np.cumsum(np.cos(heading)) * 0.2)
    # Down from the bar to the desk as a stiff band bends: leaving at the lugs' slope, meeting the desk flat.
    t = np.clip(s / FALL, 0, 1)
    z = (2 * t**3 - 3 * t**2 + 1) * z0 - (t**3 - 2 * t**2 + t) * FALL * AIM + (3 * t**2 - 2 * t**3) * STRAP_T / 2
    start, radius = lift
    z = z + np.maximum(s - start, 0) ** 2 / (2 * radius)
    return np.column_stack((x, y, z)), s


def strap(stage, name, length, side, drift, lift, material, holes=False):
    """A strap half: a band along its centre line, rounded at the edges, narrowing toward its end, with the
    attributes the leather reads, and its end rounded off on the long half."""
    centres, s = strap_path(length, side, drift, lift)
    ahead = np.gradient(centres, axis=0)
    ahead /= np.linalg.norm(ahead, axis=1)[:, None]
    across = np.cross(ahead, (0.0, 0.0, 1.0))
    across /= np.linalg.norm(across, axis=1)[:, None]
    up = np.cross(across, ahead)
    width = STRAP_W[0] + (STRAP_W[1] - STRAP_W[0]) * np.clip(s / length, 0, 1)
    if holes:
        # The tip rounds off over its last half width.
        end = np.clip((length - s) / (width / 2), 0, 1)
        width = width * np.sqrt(1 - (1 - end) ** 2)
        width = np.maximum(width, 0.6)
    # The section: a rectangle with rounded edges, its corners evenly spaced round it, so the top, where the holes
    # and the stitches are, is as finely made across as along. In shares of the half width and the half thickness.
    edge_r = 1.1
    corner = np.linspace(0, math.pi / 2, 7)
    section = []
    for cx, cy, start in ((1, 1, 0.0), (-1, 1, math.pi / 2), (-1, -1, math.pi), (1, -1, 1.5 * math.pi)):
        for k, a in enumerate(corner):
            section.append((cx, cy, math.cos(start + a), math.sin(start + a)))
        if cy > 0 and cx > 0:
            for t in np.linspace(1, -1, 61)[1:-1]:
                section.append((t, 1, 0.0, 1.0))
        elif cy < 0 and cx < 0:
            for t in np.linspace(-1, 1, 61)[1:-1]:
                section.append((t, -1, 0.0, -1.0))
    section = np.array(section)
    count = len(section)
    # Each point is a corner's centre, pulled in by the round from the edge, plus the round in its own direction.
    inset_x = width[:, None] / 2 - edge_r
    inset_z = STRAP_T / 2 - edge_r
    straight = section[:, 2] == 0
    cross = np.where(straight[None, :], section[None, :, 0] * inset_x, np.sign(section[None, :, 0]) * inset_x + edge_r * section[None, :, 2])
    height = np.broadcast_to(section[None, :, 1] * inset_z + edge_r * section[None, :, 3], cross.shape)
    sz = section[:, 3]
    verts = centres[:, None, :] + cross[..., None] * across[:, None, :] + height[..., None] * up[:, None, :]
    rings = len(s)
    faces = []
    for i in range(rings - 1):
        for j in range(count):
            a, b = i * count + j, i * count + (j + 1) % count
            faces.append((a, b, b + count, a + count))
    verts = verts.reshape(-1, 3)
    first, last = len(verts), len(verts) + 1
    verts = np.vstack((verts, centres[0], centres[-1]))
    faces += [(first, (j + 1) % count, j) for j in range(count)]
    faces += [(last, (rings - 1) * count + j, (rings - 1) * count + (j + 1) % count) for j in range(count)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts.tolist(), [], faces)
    # What the leather reads, at each corner of the mesh: along it and across it in mm, and whether on top.
    along = np.concatenate((np.repeat(s, count), [0.0, length]))
    over = np.concatenate((cross.ravel(), [0.0, 0.0]))
    top = np.concatenate((np.tile(sz > 0.7, rings), [False, False]))
    wide = np.concatenate((np.repeat(width / 2, count), [10.0, 10.0]))
    edge = np.clip((np.abs(over) - (wide - 0.9)) / 0.9, 0, 1) + (~top) * 0.6
    stitch = np.zeros_like(along)
    # The stitches at the lug end, two short rows down each side.
    for column in (-1, 1):
        lane = np.abs(over - column * (wide - 1.6)) < 0.32
        dash = ((along - 2.0) % 2.4) < 1.5
        stitch += lane & dash & (along > 2.0) & (along < 15.0) & top
    hole = np.zeros_like(along)
    if holes:
        start, pitch, count_, radius = HOLES
        for k in range(count_):
            d = np.hypot(along - (start + k * pitch), over)
            hole = np.maximum(hole, np.clip((radius - d) / 0.15, 0, 1) * top)
    wear = np.clip(1 - along / 40.0, 0, 1) * top
    for key, values in (("edge", np.clip(edge, 0, 1)), ("stitch", np.clip(stitch, 0, 1)), ("hole", hole), ("wear", wear)):
        attribute = mesh.attributes.new(key, "FLOAT", "POINT")
        attribute.data.foreach_set("value", values.astype(np.float32))
    # The holes are pressed through, their middles sunk; the stitches stand a little proud of the leather.
    co = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    normal_up = np.concatenate((np.repeat(up, count, axis=0), [up[0], up[-1]]))
    co += normal_up * (np.clip(stitch, 0, 1) * 0.12 - hole * STRAP_T * 0.8)[:, None]
    mesh.vertices.foreach_set("co", co.ravel())
    made = bmesh.new()
    made.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(made, faces=made.faces)
    made.to_mesh(mesh)
    made.free()
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.materials.append(material)
    return stage.add(name, mesh), centres, ahead, across, width


def plain(s, angle):
    """No relief on a tube."""
    return np.zeros(np.broadcast(s, angle).shape)


def buckle(stage, centres, ahead, across, width, metal):
    """The tang buckle at the short half's end: a rounded frame of steel wire lying flat, the strap folded round its
    bar, and its tongue lying on the frame."""
    end = centres[-1]
    forward, side = ahead[-1], across[-1]
    w, d, r = BUCKLE
    corners = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, d), (-w / 2, d)]
    path = []
    for (ax, ay), (bx, by) in zip(corners, corners[1:] + corners[:1]):
        for t in np.linspace(0, 1, 30, endpoint=False):
            path.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    path = np.array(path)
    # Round the frame's corners by smoothing the outline.
    for _ in range(40):
        path = (np.roll(path, 1, axis=0) + 2 * path + np.roll(path, -1, axis=0)) / 4
    points = [end + side * x + forward * (y - 1.5) + np.array([0, 0, r - STRAP_T / 2]) for x, y in path]
    points.append(points[0])
    frame = tube("watch-buckle", spline(points, 0.1), r, 24, plain)
    frame.materials.append(metal)
    tongue_points = [end + forward * (-1.5) + np.array([0, 0, r * 1.6 - STRAP_T / 2]), end + forward * (d * 0.55) + np.array([0, 0, r * 2.2 - STRAP_T / 2]), end + forward * (d - 1.5) + np.array([0, 0, r * 2.0 - STRAP_T / 2])]
    tongue = tube("watch-tongue", spline(tongue_points, 0.1), r * 0.7, 16, plain)
    tongue.materials.append(metal)
    return [stage.add("watch-buckle", frame), stage.add("watch-tongue", tongue)]


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
    hide = leather("watch-leather")
    made = case(stage, polish) + dial(stage, paper) + [crystal(stage)]
    for part in made:
        part.location.z += RAISE
    short, centres, ahead, across, width = strap(stage, "watch-strap-short", SHORT, 1, DRIFT[0], LIFT[0], hide)
    made += [short, *buckle(stage, centres, ahead, across, width, steel("watch-buckle-steel", 0.18))]
    long, *_ = strap(stage, "watch-strap-long", LONG, -1, DRIFT[1], LIFT[1], hide, holes=True)
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
