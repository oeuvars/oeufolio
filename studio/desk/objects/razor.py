"""Safety razor: a Merkur 23C, the long-handled three-piece one, measured off the maker's photographs
(104 mm long, the head 43 by 25 mm) at 6 mm to the em. Bright chrome on brass and die-cast zinc: the curved
cap, a blade under it, the base plate with a straight scalloped guard bar down each side, the flared neck,
a long grip cut with a diamond knurl, the band rolled with MERKUR and SOLINGEN and a knurled end knob broken
by two turned grooves. It lies as a razor does, on one edge of its head and on the knob, so the handle slopes.
The head is plated all over, inside and out, as the maker's photographs show it: the base plate one casting, its
ends shaped as they are. It has been used: fine scratches, a few water spots, and dried soap in the knurl and the
scallops. Its chrome throws back the room round the desk, its walls and ceiling lit by the pendant."""

import math
import os

import bmesh
import bpy
import numpy as np

from paint import cloud, linear
from solids import finish, principled, strip_light, worn

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art")

# Every measure below is in millimetres. Along the razor from the crown of the cap, across the blade's
# length, and across the head from one guard bar to the other.
MM = 1 / 6
W, H = 17.5, 7.3

# The base plate, along the razor: the floor of the channels inside the bars, its back, the notch inside each bar
# block, and the back of the blocks.
BASE = (7.0, 7.9, 7.4, 8.4)
# The window through each end of the base plate: this far either side of the middle across the head, from this far
# along the razor to this far, and this deep into the end.
WINDOW = (7.5, 4.9, 7.0, 5.0)
# What the chrome throws back besides the lamp: the room round the desk, its walls this far off and as high as the
# ceiling, which closes them; as bright as the pendant's light thrown back off the desk leaves them, and this warm,
# the walls dark at the floor and brighter up toward the ceiling, which is brightest.
WALLS = (300.0, 400.0, (0.13, 0.108, 0.083))
CEILING = (0.2, 0.165, 0.13)
# A room is never even: its walls and ceiling lighter and darker in broad patches (shelves, a door, the shade's
# shadow), between these shares of their brightness, this many patches round.
PATCHES = (0.35, 1.6, 2.2)

# The cap is nearly flat across its crown and rolls over tightly to its two edges: the radius of the crown,
# how far out the roll begins, the angle the roll ends at and the half depth of the cap.
CROWN, ROLL, LIP, CAP_EDGE = 19.0, 8.5, math.radians(60), 11.3
BAR = (10.5, 12.5, 5.9, 8.4)
SCALLOPS, SCALLOP_PITCH = 13, 2.75
NECK = ((8.4, 4.3), (9.6, 4.25), (11.0, 4.1), (13.0, 3.95), (15.0, 4.0), (17.0, 4.2), (19.0, 4.6), (20.6, 5.1), (21.2, 5.25), (21.45, 5.25), (21.6, 4.9))
GRIP = (27.0, 84.2, 4.65)
BAND = (84.0, 90.4)
KNOB = (90.4, 104.0, 5.4)
GROOVES = ((93.5, 94.4), (97.5, 98.4))
STARTS, KNURL, CUT = 32, 0.95, 0.3

CHROME = (0.84, 0.85, 0.87)
SOAP = "#e9e7df"


def chrome(name, rough=0.05, spots=0.0, band=False):
    """Bright chrome plate that has been used: hairline scratches and finger marks, soap dried white wherever
    the mesh says it has gathered (its `scum` attribute), and water spots, each a pale ring with a faint
    middle. band rolls the maker's name into it, by the mesh's UV map."""
    material = principled(name, CHROME, rough=rough, metal=1.0)
    worn(material, "Scratches003", 2.2, 0.1)
    worn(material, "Fingerprints009", 4.0, 0.07)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]

    def maths(op, a, b=None, c=None):
        node = nodes.new("ShaderNodeMath")
        node.operation = op
        for socket, value in zip(node.inputs, (a, b, c)):
            if value is None:
                continue
            if isinstance(value, (int, float)):
                socket.default_value = value
            else:
                links.new(value, socket)
        return node.outputs[0]

    def step(lo, hi, value):
        node = nodes.new("ShaderNodeMapRange")
        node.interpolation_type = "SMOOTHSTEP"
        node.inputs["From Min"].default_value, node.inputs["From Max"].default_value = lo, hi
        links.new(value, node.inputs["Value"])
        return node.outputs[0]

    stored = nodes.new("ShaderNodeAttribute")
    stored.attribute_name = "scum"
    soap = stored.outputs["Fac"]
    dull = soap
    if spots:
        coord = nodes.new("ShaderNodeTexCoord")
        cells = nodes.new("ShaderNodeTexVoronoi")
        cells.inputs["Scale"].default_value = 2.8
        # No drop dries round: the cells are pushed about before they are measured.
        wobble = nodes.new("ShaderNodeTexNoise")
        wobble.inputs["Scale"].default_value = 7.0
        links.new(coord.outputs["Object"], wobble.inputs["Vector"])
        push = nodes.new("ShaderNodeVectorMath")
        push.operation = "MULTIPLY_ADD"
        push.inputs[1].default_value = (0.14, 0.14, 0.14)
        links.new(wobble.outputs["Color"], push.inputs[0])
        links.new(coord.outputs["Object"], push.inputs[2])
        links.new(push.outputs[0], cells.inputs["Vector"])
        each = nodes.new("ShaderNodeSeparateColor")
        links.new(cells.outputs["Color"], each.inputs["Color"])
        radius = maths("MULTIPLY_ADD", each.outputs["Red"], 0.1, 0.05)
        inside = maths("SUBTRACT", 1.0, step(-0.012, 0.0, maths("SUBTRACT", cells.outputs["Distance"], radius)))
        rim = maths("MULTIPLY", inside, step(-0.035, -0.012, maths("SUBTRACT", cells.outputs["Distance"], radius)))
        spot = maths("MULTIPLY", maths("MULTIPLY_ADD", rim, 0.55, maths("MULTIPLY", inside, 0.3)), step(1 - spots, 1 - spots + 0.05, each.outputs["Green"]))
        dull = maths("MAXIMUM", soap, maths("MULTIPLY", spot, 0.7))
    engraved = None
    if band:
        roll = nodes.new("ShaderNodeTexImage")
        roll.image = bpy.data.images.load(os.path.join(ART, "merkur-band.png"))
        roll.image.colorspace_settings.name = "Non-Color"
        roll.extension = "REPEAT"
        engraved = roll.outputs["Alpha"]
        cut = nodes.new("ShaderNodeBump")
        cut.invert = True
        cut.inputs["Distance"].default_value = 0.035
        links.new(engraved, cut.inputs["Height"])
        links.new(cut.outputs["Normal"], shader.inputs["Normal"])
        dull = maths("MAXIMUM", dull, maths("MULTIPLY", engraved, 0.3))

    tint = nodes.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.inputs[6].default_value = (*CHROME, 1)
    tint.inputs[7].default_value = (*linear(SOAP), 1)
    links.new(dull, tint.inputs[0])
    links.new(tint.outputs[2], shader.inputs["Base Color"])
    links.new(maths("SUBTRACT", 1.0, maths("MULTIPLY", dull, 0.9)), shader.inputs["Metallic"])
    under = shader.inputs["Roughness"].links[0].from_socket
    links.new(maths("ADD", under, maths("MULTIPLY", dull, 0.7)), shader.inputs["Roughness"])
    return material


def lathed(stage, name, profile, material, steps=128, relief=None, scum=None, start=0.0, ends=(True, True), span=None):
    """Turn a profile of (distance along the razor, radius) about the razor's axis, which is the object's x.
    relief(along, angle) is added to the radius and scum(along, angle, relief) is how much soap lies at
    each point. The UV map runs once round the part across and along `span` down."""
    along, radius = (np.array(v, dtype=float) for v in zip(*profile))
    angle = start + np.arange(steps) * 2 * np.pi / steps
    A, T = np.meshgrid(along, angle, indexing="ij")
    cut = relief(A, T) if relief else np.zeros_like(A)
    R = radius[:, None] + cut
    verts = np.column_stack((A.ravel(), (R * np.cos(T)).ravel(), (R * np.sin(T)).ravel())) * MM
    rows = len(along)
    i, j = (v.ravel() for v in np.meshgrid(np.arange(rows - 1), np.arange(steps), indexing="ij"))
    k = (j + 1) % steps
    faces = np.column_stack((i * steps + j, i * steps + k, (i + 1) * steps + k, (i + 1) * steps + j)).tolist()
    lids = [list(range(steps))[::-1]] * ends[0] + [[(rows - 1) * steps + n for n in range(steps)]] * ends[1]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts.tolist(), [], faces + lids)
    lo, hi = span or (along[0], along[-1])
    v0, v1 = 1 - (along[i] - lo) / (hi - lo), 1 - (along[i + 1] - lo) / (hi - lo)
    uv = np.dstack((1 - np.column_stack((j, j + 1, j + 1, j)) / steps, np.column_stack((v0, v0, v1, v1)))).ravel()
    mesh.uv_layers.new().data.foreach_set("uv", np.concatenate((uv, np.zeros(2 * steps * len(lids)))))
    soap = np.clip(scum(A, T, cut), 0, 1).ravel() if scum else np.zeros(rows * steps)
    mesh.color_attributes.new("scum", "FLOAT_COLOR", "POINT").data.foreach_set("color", np.repeat(soap, 4))
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.set_sharp_from_angle(angle=math.radians(38))
    mesh.materials.append(material)
    return stage.add(name, mesh)


def knurl(along, angle):
    """A diamond knurl: two sets of grooves crossing, leaving rows of blunt pyramids. 0 at their tips."""
    round_, down = angle / (2 * np.pi) * STARTS, along / KNURL
    one, two = (1 - np.abs(2 * ((round_ + s * down) % 1) - 1) for s in (1, -1))
    return -CUT * (1 - np.minimum(np.minimum(one, two) / 0.82, 1))


def gathered(seed, heavy):
    """Where soap has dried in a knurl: down in the grooves, in patches, heaviest toward `heavy` mm along."""
    patches = {}

    def scum(along, angle, cut):
        if "map" not in patches:
            patches["map"] = np.clip(cloud(along.shape, seed, falloff=1.7) * 0.7 + 0.15, 0, 1)
        deep = np.clip(-cut / CUT, 0, 1) ** 1.5
        return deep * patches["map"] * (0.25 + 0.75 * np.exp(-(((along - heavy) / 14) ** 2)))

    return scum


def extruded(stage, name, section, u0, u1, material, bevel=0.3, soft=math.radians(28)):
    """Push a section of (across the head, along the razor) points along the blade from u0 to u1, and
    take the sharpness off every edge as casting and plating do."""
    bm = bmesh.new()
    near = [bm.verts.new((a * MM, u0 * MM, w * MM)) for w, a in section]
    far = [bm.verts.new((a * MM, u1 * MM, w * MM)) for w, a in section]
    count = len(section)
    bm.faces.new(near)
    bm.faces.new(far[::-1])
    for i in range(count):
        j = (i + 1) % count
        bm.faces.new((near[j], near[i], far[i], far[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    hard = [edge for edge in bm.edges if len(edge.link_faces) == 2 and edge.calc_face_angle() > soft]
    if bevel:
        bmesh.ops.bevel(bm, geom=hard, offset=bevel * MM, segments=3, profile=0.5, affect="EDGES", clamp_overlap=True)
    return finish(stage, name, bm, material)


def bar(stage, name, side, material):
    """One guard bar: straight, with slanted scallops cut across its outer corner for the lather to leave by."""
    w0, w1, a0, a1 = BAR
    u = np.linspace(-20.8, 20.8, 417)
    inside = np.clip((18.2 - np.abs(u)) / 0.8, 0, 1)

    def cuts(shift):
        """Each cut runs across the corner on a slant: it deepens slowly and ends short."""
        t = ((u + shift) / SCALLOP_PITCH) % 1
        return np.where(t < 0.72, (t / 0.72) ** 1.7, ((1 - t) / 0.28) ** 0.8) * inside

    top, face = 0.22 + 1.0 * cuts(0.5), 0.22 + 1.15 * cuts(-0.4)
    rings = np.stack(
        (
            np.column_stack((np.full_like(u, w0), np.full_like(u, a1))),
            np.column_stack((np.full_like(u, w0), np.full_like(u, a0))),
            np.column_stack((w1 - top, np.full_like(u, a0))),
            np.column_stack((w1 - 0.35 * top, a0 + 0.3 * face)),
            np.column_stack((np.full_like(u, w1), a0 + face)),
            np.column_stack((np.full_like(u, w1), np.full_like(u, a1 - 0.2))),
            np.column_stack((np.full_like(u, w1 - 0.2), np.full_like(u, a1))),
        ),
        axis=1,
    )
    around = rings.shape[1]
    bm = bmesh.new()
    held = bm.verts.layers.float_color.new("scum")
    soap = np.clip(cloud((len(u), 8), 5 + (side > 0), falloff=1.4)[:, 0] * 0.6 + 0.2, 0, 1) * cuts(0.0) ** 0.5
    loops = []
    for n in range(len(u)):
        loop = [bm.verts.new((a * MM, u[n] * MM, side * w * MM)) for w, a in rings[n]]
        for at in (2, 3, 4):
            loop[at][held] = (soap[n],) * 4
        loops.append(loop)
    for lower, upper in zip(loops, loops[1:]):
        for k in range(around):
            bm.faces.new((lower[k], lower[(k + 1) % around], upper[(k + 1) % around], upper[k]))
    bm.faces.new(loops[0])
    bm.faces.new(loops[-1])
    return finish(stage, name, bm, material)


def head(stage, plate, steel):
    """The three pieces of the head with a blade between them."""
    turn = math.asin(ROLL / CROWN)
    tight = (CAP_EDGE - ROLL) / (math.sin(LIP) - math.sin(turn))

    def top(w):
        """The outside of the cap."""
        if abs(w) <= ROLL:
            return CROWN - math.sqrt(CROWN**2 - w**2)
        at = math.asin(min(1.0, (abs(w) - ROLL) / tight + math.sin(turn)))
        return CROWN * (1 - math.cos(turn)) + tight * (math.cos(turn) - math.cos(at))

    def bed(w, lift=0.0):
        return 2.9 + lift + 2.2 * (w / 11.9) ** 2

    across = np.linspace(-1, 1, 41)
    # More points where the roll is tight, so it shines as a curve and not as flats.
    spread = np.linspace(-1, 1, 97)
    rolled = np.sign(spread) * (1 - (1 - np.abs(spread)) ** 1.8)
    edge = top(CAP_EDGE)
    cap = [(w, top(w)) for w in rolled * CAP_EDGE] + [(CAP_EDGE - 0.12, edge + 0.18)] + [(w, bed(w, -0.35)) for w in across[::-1] * 10.7] + [(-CAP_EDGE + 0.12, edge + 0.18)]
    parts = [extruded(stage, "cap", cap, -21.5, 21.5, plate, bevel=0.45, soft=math.radians(14))]
    blade = [(w, bed(w, -0.12)) for w in across * 11.95] + [(w, bed(w)) for w in across[::-1] * 11.95]
    parts.append(extruded(stage, "blade", blade, -21.4, 21.4, steel, bevel=0.0))
    # The base plate is one casting, plated all over: seen from its end (the maker's photographs), a block under
    # each guard bar, a notch inside it and a straight back between, where the neck is screwed on; a channel runs
    # between the blade's seat and each bar, its floor the plate, for the lather to leave by.
    floor, back, notch, block = BASE
    seat = [(w, bed(w, 0.02)) for w in across * 9.6]
    outline = seat + [(9.6, floor), (12.5, floor), (12.5, block), (10.4, block + 0.2), (9.3, notch), (8.0, back)]
    outline += [(-w, a) for w, a in outline[len(seat) :][::-1]]
    base = extruded(stage, "base", outline, -20.8, 20.8, plate, bevel=0.3)
    # Through each end, a tall window between the blade's seat and the back.
    w, a0, a1, deep = WINDOW
    for end in (1, -1):
        cutter = bmesh.new()
        bmesh.ops.create_cube(cutter, size=1.0)
        bmesh.ops.scale(cutter, vec=((a1 - a0) * MM, (2 * deep) * MM, 2 * w * MM), verts=cutter.verts)
        bmesh.ops.translate(cutter, vec=((a0 + a1) / 2 * MM, end * 20.8 * MM, 0.0), verts=cutter.verts)
        box = bpy.data.meshes.new("window")
        cutter.to_mesh(box)
        cutter.free()
        punch = stage.add("window", box)
        cut = base.modifiers.new("window", "BOOLEAN")
        cut.operation = "DIFFERENCE"
        cut.solver = "EXACT"
        cut.object = punch
        bpy.context.view_layer.update()
        graph = bpy.context.evaluated_depsgraph_get()
        done = bpy.data.meshes.new_from_object(base.evaluated_get(graph), depsgraph=graph)
        base.modifiers.remove(cut)
        base.data = done
        bpy.data.objects.remove(punch)
    parts.append(base)
    for side in (1, -1):
        parts.append(bar(stage, f"bar-{side}", side, plate))
    # The cap's two pegs come through the plate and show as domes under it.
    for end in (1, -1):
        dome = lathed(stage, f"peg-{end}", [(8.3 + 1.9 * math.sin(t), 1.65 * math.cos(t)) for t in np.linspace(0, math.pi / 2 - 0.02, 14)], plate, steps=40, ends=(True, True))
        dome.location = (0, end * 14.6 * MM, 0)
        parts.append(dome)
    return parts


def handle(stage, plate, turned, rolled):
    """Neck, collar, grip, band and knob, each turned about the razor's axis."""
    first, last, grip = GRIP
    parts = [lathed(stage, "neck", [(a, r) for a, r in zip(*smooth(NECK))], plate, steps=96)]
    parts.append(lathed(stage, "collar", [(21.6, 4.5), (21.85, 4.7), (26.75, 4.7), (27.0, 4.55)], plate, steps=96))

    def bite(lo, hi, run=0.7):
        """The knurl runs out to nothing at both ends of the stock it is cut in."""
        return lambda along, angle: knurl(along, angle) * np.clip((along - lo) / run, 0, 1) * np.clip((hi - along) / run, 0, 1)

    rows = np.arange(first, last + 1e-6, KNURL / 8)
    parts.append(lathed(stage, "grip", [(a, grip) for a in rows], turned, steps=STARTS * 8, relief=bite(first, last), scum=gathered(3, 34.0), ends=(False, False)))
    lo, hi = BAND
    parts.append(lathed(stage, "band", [(a, grip) for a in np.linspace(lo, hi, 9)], rolled, steps=128, start=math.radians(-75), ends=(False, False), span=BAND))

    start, end, fat = KNOB
    rows = np.arange(start, end + 1e-6, KNURL / 8)
    stock = np.full_like(rows, fat)
    stock -= 0.5 * (1 - np.clip((rows - start) / 0.45, 0, 1)) + 0.4 * (1 - np.clip((end - rows) / 0.4, 0, 1))
    lands = np.ones_like(rows)
    for a, b in GROOVES:
        inside = np.clip((rows - a) / 0.15, 0, 1) * np.clip((b - rows) / 0.15, 0, 1)
        stock -= 0.36 * inside
        lands *= 1 - np.clip((rows - a + 0.35) / 0.3, 0, 1) * np.clip((b + 0.35 - rows) / 0.3, 0, 1)
    lands *= np.clip((rows - start - 0.5) / 0.4, 0, 1) * np.clip((end - 0.45 - rows) / 0.4, 0, 1)

    def cut(along, angle):
        return knurl(along, angle) * np.interp(along, rows, lands)

    def soap(along, angle, relief):
        ring = sum(np.exp(-(((along - (a + b) / 2) / 0.4) ** 2)) for a, b in GROOVES)
        return gathered(4, 96.0)(along, angle, relief) + 0.8 * ring * np.clip(cloud(along.shape, 9, falloff=1.5) * 0.6 + 0.3, 0, 1)

    parts.append(lathed(stage, "knob", list(zip(rows, stock)), turned, steps=STARTS * 8, relief=cut, scum=soap, ends=(True, False)))
    # The handle is a tube, open at the end of the knob.
    parts.append(lathed(stage, "bore", [(end, stock[-1]), (end, 2.7), (end - 5.0, 2.6), (end - 5.0, 0.01)], plate, steps=64, ends=(False, False)))
    return parts


def room(stage):
    """The room's walls and ceiling round the desk, seen only in the chrome: without them it throws back only the
    dark, and reads as black glass. A ring and a disc, the same whichever way the razor is turned."""
    radius, high, warm = WALLS
    around = np.linspace(0, 2 * math.pi, 96, endpoint=False)
    walls = bpy.data.meshes.new("razor-walls")
    walls.from_pydata([(radius * math.cos(a), radius * math.sin(a), z) for a in around for z in (0.0, high)], [], [(2 * k, 2 * ((k + 1) % 96), 2 * ((k + 1) % 96) + 1, 2 * k + 1) for k in range(96)])
    ceiling = bpy.data.meshes.new("razor-ceiling")
    ceiling.from_pydata([(radius * math.cos(a), radius * math.sin(a), high) for a in around], [], [list(range(96))[::-1]])
    for mesh, light, rising in ((walls, warm, True), (ceiling, CEILING, False)):
        material = bpy.data.materials.new(mesh.name)
        material.use_nodes = True
        nodes, links = material.node_tree.nodes, material.node_tree.links
        nodes.remove(nodes["Principled BSDF"])
        emit = nodes.new("ShaderNodeEmission")
        low, high_, count = PATCHES
        where = nodes.new("ShaderNodeTexCoord")
        patches = nodes.new("ShaderNodeTexNoise")
        patches.inputs["Scale"].default_value = count
        patches.inputs["Detail"].default_value = 1.0
        links.new(where.outputs["Generated"], patches.inputs["Vector"])
        spread = nodes.new("ShaderNodeMapRange")
        spread.inputs["From Min"].default_value, spread.inputs["From Max"].default_value = 0.35, 0.65
        spread.inputs["To Min"].default_value, spread.inputs["To Max"].default_value = low, high_
        links.new(patches.outputs["Fac"], spread.inputs["Value"])
        tint = nodes.new("ShaderNodeMix")
        tint.data_type = "RGBA"
        tint.blend_type = "MULTIPLY"
        tint.inputs["Factor"].default_value = 1.0
        tint.inputs["A"].default_value = (*light, 1)
        links.new(spread.outputs[0], tint.inputs["B"])
        links.new(tint.outputs["Result"], emit.inputs["Color"])
        if rising:
            height = nodes.new("ShaderNodeSeparateXYZ")
            links.new(where.outputs["Generated"], height.inputs[0])
            ramp = nodes.new("ShaderNodeMapRange")
            ramp.inputs["To Min"].default_value = 0.15
            links.new(height.outputs["Z"], ramp.inputs["Value"])
            links.new(ramp.outputs[0], emit.inputs["Strength"])
        links.new(emit.outputs[0], nodes["Material Output"].inputs["Surface"])
        mesh.materials.append(material)
        obj = stage.add(mesh.name, mesh)
        obj.location = (W / 2, -H / 2, 0)
        for flag in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission", "visible_volume_scatter"):
            setattr(obj, flag, False)
        # desk.py keeps it, as it keeps no other shot's studio cards.
        obj["kept"] = True


def smooth(points, step=0.2):
    """A turned profile drawn through a few measured points."""
    along, radius = zip(*points)
    fine = np.arange(along[0], along[-1] + 1e-6, step)
    eased = np.interp(fine, along, radius)
    kernel = np.exp(-(np.linspace(-2, 2, 9) ** 2))
    eased = np.convolve(np.pad(eased, 4, mode="edge"), kernel / kernel.sum(), mode="valid")
    eased[0], eased[-1] = radius[0], radius[-1]
    return fine, eased


def razor(stage):
    plate = chrome("chrome", rough=0.085, spots=0.12)
    turned = chrome("knurled", rough=0.1)
    rolled = chrome("rolled", rough=0.05, band=True)
    steel = worn(principled("blade", (0.62, 0.63, 0.65), rough=0.22, metal=1.0), "Scratches003", 1.5, 0.15)

    # It rests on the lower guard bar and on the knob, which is narrower, so the handle runs downhill.
    low, foot = BAR[1], BAR[3]
    slope = math.atan2(low - KNOB[2], KNOB[1] - 0.4 - foot)
    root = stage.add("razor", None)
    root.rotation_euler = (0, slope, 0)
    root.location = (0.05, -H / 2, (low * math.cos(slope) + foot * math.sin(slope)) * MM)
    for part in (*head(stage, plate, steel), *handle(stage, plate, turned, rolled)):
        part.parent = root
    room(stage)

    strip_light(stage, "strip", (W / 2, -H / 2 + 5.0, 30.0), 70.0, 9.0, 3.0)
    stage.shoot("razor", (0, 0, W, H), bleed=1.0, shadow=1.3, card=1.4, sharp=1.5)


SHOTS = {"razor": razor}
