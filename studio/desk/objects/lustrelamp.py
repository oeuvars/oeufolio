"""The desk lamp: a wall light of hand-blown smoked glass under a gold lustre, with an opal lens in the middle.

It is the lamp in the user's photograph, square on to its face. The glass is one blown piece, a hollow cushion with
a soft, squarish outline, a little out of true, as blown glass is. From the rim the face rises to a low crest, then
falls into a short tube through the middle, which a bronze housing fills: an opal lens sunk in its top, held by a thin brass
ring and five clips, gives the light. The outside of the glass is coated with a thin gold lustre, a film of metal
so thin it throws back much of the room in gold and lets the rest through, and colours its reflections where it is
thinnest. Lit, the light the lens throws sideways through the tube's wall glows amber in the glass round it; the
shoulder, seen edge on, is a bright band of gold.

The lamp lies on the desk on its back, its face up, the photograph's top up the page.

Light that passes the glass's thin wall reaches the desk in its colour, as the shadow rays are let through it
(SHADOW): the lamp lights the desk round it amber through its own glass.

Built in its own coordinates, in em: standing on z = 0, its middle at the middle of its box. Its lens is marked
"bulb", at no power until desk.py turns it up, its "share" of the lamp's power spread over its "area"."""

import math

import bmesh
import bpy
import numpy as np

from objects.flutelamp import corner, glowing, node, painted, spline, turned, weigh
from paint import linear

# The glass across, on average, and its radius. The outline is this round one pushed out and in by these harmonics
# of the angle round the middle (cos, sin), fitted to the outline in the photograph.
D = 12.0
R = D / 2
HARMONICS = [(-0.0042, 0.0014), (-0.01, 0.0023), (-0.0025, -0.0119), (-0.0156, -0.0044), (-0.007, -0.0116), (0.0032, -0.0009), (0.0, 0.0017), (-0.0012, 0.0008)]
# The outline shapes the glass from this far out to this far, in shares of R; the middle stays round.
SHAPED = (0.45, 0.85)
# The glass's section, its middle surface: radius and height in em from the open end of the tube, up over the lip,
# the crest and the shoulder, round the rim and in under it to where it meets the back. The glass is this thick.
SECTION = [
    (2.35, 1.2),
    (2.35, 1.8),
    (2.38, 2.25),
    (2.5, 2.55),
    (2.72, 2.72),
    (3.05, 2.88),
    (3.4, 2.95),
    (4.0, 2.86),
    (4.5, 2.62),
    (4.95, 2.3),
    (5.35, 1.88),
    (5.7, 1.35),
    (5.92, 0.9),
    (5.88, 0.6),
    (5.6, 0.42),
    (5.3, 0.36),
]
THICK = 0.1
# Blown glass is out of true: its surface waves by up to this much, in em, slowly round it and along it.
WOBBLE = 0.015
# The back it is mounted on, inside it: steel painted dark bronze, its radius and height.
BACK_R = 5.3
BACK_H = 0.36
# The bronze housing in the tube: its radius, and the height of its top, where the brass ring is; the opal lens is
# sunk in it, doming up this much to the ring. A collar round its top reaches out to the glass. The clips stand at these angles round it, as the photograph shows them.
CAN_R = 2.12
COLLAR = 2.27
CAN_TOP = 1.95
DOME = 0.32
CLIPS = (48, 176, 206, 290, 318)
BRASS = "#b08a4a"
BRONZE = "#2a1d14"
OPAL = "#f4efe4"
# The glass, the share of each colour its smoke lets through at each face; the lustre, the colour it throws back and
# how much of the light it throws back rather than lets through; the film it is, this many nanometres thick on
# most, and none at all over most of the glass.
SMOKE = (0.94, 0.68, 0.4)
GOLD = (1.0, 0.7, 0.35)
COAT = 0.62
# The lustre was sprayed at the face: it is thickest there, nearly a mirror, and thinner over the funnel and the
# shoulder, where the light inside shows through it. Its share by the distance out, in shares of R.
COATS = [(0.0, 0.9), (0.4, 0.9), (0.45, 0.85), (0.58, 0.85), (0.66, 0.995), (0.82, 0.995)]
# Past the face it went on by how squarely the glass faced the spray: by the height of the surface's normal, the
# shoulder half coated, the side, seen edge on, thinnest, so the light inside gets out there across the desk, and
# the curl under it, which the spray caught at its back edge on the turning table, a little more.
FACING = [(-0.6, 0.5), (-0.2, 0.35), (0.0, 0.2), (0.3, 0.6), (0.75, 0.995)]
FILM = 350.0
# The lens gives warm white light, this share of the lamp's power in desk.py. Inside the glass, a frosted strip of
# LEDs on the back lights the glass from within, at this share: a ring round the housing this far out, in em, lit
# over the top and fading toward the sides by this power of the sine of the angle, where the photograph shows its
# glow through the funnel.
BULB = (1.0, 0.86, 0.66)
SHARE = 0.0004
LED_SHARE = 0.0012
LED_SPREAD = 3.0
# A band of LEDs on a riser round the edge of the back, this far out, this high and this wide, lights the shoulder
# from inside at this share; it is what lights the desk round the lamp, through the thin lustre on the side.
BAND_R = 5.0
BAND_Z = 0.85
BAND_W = 0.25
BAND_SHARE = 0.07
LED_R = (2.55, 3.7)
# Glass that bends light lets a shadow ray through in a render only if told: what each face lets through, in its
# own colour, and on the outside less what the lustre there throws back.
SHADOW = SMOKE
# The box the lamp stands in, in em.
W = H = D + 2.0
TOP = max(z for _, z in SECTION) + THICK

# The page shows the lamp from a camera of its own (desk.py PORTRAITS), straight over it as far off as the plate's
# camera, as its face was photographed. Its middle, and the point on the desk under it.
DISTANCE = 100.0
MIDDLE = (0.0, 0.0, TOP / 2)
STANDS = (0.0, 0.0, 0.0)
BODY = "lustre-glass"


def photograph():
    """The camera over the lamp: where it stands, looking straight down, and its axes."""
    return np.array(MIDDLE) + np.array([0.0, 0.0, DISTANCE]), np.eye(3), None


def outline(angle):
    """How far out the outline is at an angle round the middle, as a share of R."""
    return 1 + sum(a * np.cos(k * angle) + b * np.sin(k * angle) for k, (a, b) in enumerate(HARMONICS, 1))


def wobble(angle, along):
    """How far the blown surface stands off true at an angle round and a distance along the section, in em."""
    waves = ((2, 0.7, 0.3), (3, 1.3, 1.9), (5, 0.4, 4.1), (7, 2.1, 2.6))
    return WOBBLE * sum(np.sin(k * angle + p) * np.cos(f * along + p * 1.7) for k, f, p in waves) / len(waves) * 2


def section(step=0.02):
    """The glass's section as a closed loop round its thickness: radius and height; whether each point is on the
    coated outside; how far along the surface it is; and how high its normal points, on the outside."""
    middle, _ = spline([(r, 0.0, z) for r, z in SECTION], step)
    r, z = middle[:, 0], middle[:, 2]
    tr, tz = np.gradient(r), np.gradient(z)
    length = np.hypot(tr, tz)
    # The outward normal: to the right of the way along, which runs up the tube and out over the face.
    nr, nz = tz / length, -tr / length
    half = THICK / 2
    outside = np.column_stack((r + nr * half, z + nz * half))
    inside = np.column_stack((r - nr * half, z - nz * half))[::-1]
    # Round ends where the glass stops, at the open end of the tube and where it meets the back.
    def cap(at, normal, ahead):
        steps = np.linspace(0, math.pi, 9)[1:-1]
        return [at + half * (math.cos(a) * normal + math.sin(a) * ahead) for a in steps]

    end = cap(middle[-1, [0, 2]], np.array([nr[-1], nz[-1]]), np.array([tr[-1], tz[-1]]) / length[-1])
    start = cap(middle[0, [0, 2]], -np.array([nr[0], nz[0]]), -np.array([tr[0], tz[0]]) / length[0])
    loop = np.vstack((outside, end, inside, start))
    coated = np.concatenate((np.ones(len(outside)), np.zeros(len(end) + len(inside) + len(start))))
    facing = np.concatenate((nz, np.zeros(len(end) + len(inside) + len(start))))
    along = np.concatenate((np.cumsum(np.r_[0, np.hypot(*np.diff(outside, axis=0).T)]), np.zeros(len(end)), np.cumsum(np.r_[0, np.hypot(*np.diff(inside, axis=0).T)])[::-1], np.zeros(len(start))))
    return loop, coated, along, facing


def glass_mesh(name, around=720):
    """The glass as one closed solid: its section turned round the axis, pushed out to the outline past the middle,
    and waved a little, as blown glass is."""
    loop, coated, along, facing = section()
    count = len(loop)
    u = np.linspace(0, 2 * math.pi, around, endpoint=False)[:, None]
    r = loop[None, :, 0]
    shaped = np.clip((r / R - SHAPED[0]) / (SHAPED[1] - SHAPED[0]), 0, 1)
    shaped = shaped * shaped * (3 - 2 * shaped)
    r = r * (1 + (outline(u) - 1) * shaped) + wobble(u, along[None, :]) * shaped
    z = np.broadcast_to(loop[None, :, 1], r.shape) + wobble(u + 1.1, along[None, :] + 0.6) * shaped * 0.5
    verts = np.column_stack(((r * np.cos(u)).ravel(), (r * np.sin(u)).ravel(), z.ravel()))
    i = np.arange(around)[:, None]
    j = np.arange(count)[None, :]
    a0 = (i * count + j).ravel()
    a1 = (((i + 1) % around) * count + j).ravel()
    a2 = (((i + 1) % around) * count + (j + 1) % count).ravel()
    a3 = (i * count + (j + 1) % count).ravel()
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts.tolist(), [], np.column_stack((a0, a1, a2, a3)).tolist())
    faces = (1 - np.broadcast_to(np.minimum(coated, np.roll(coated, -1))[None, :], (around, count))).astype(np.int32)
    mesh.polygons.foreach_set("material_index", faces.ravel())
    out = np.hypot(verts[:, 0], verts[:, 1]) / R
    up = np.broadcast_to(facing[None, :], (around, count)).ravel()
    share = np.where(out < COATS[-1][0], np.interp(out, *zip(*COATS)), np.interp(up, *zip(*FACING)))
    attribute = mesh.attributes.new("coat", "FLOAT", "POINT")
    attribute.data.foreach_set("value", share.astype(np.float32))
    made = bmesh.new()
    made.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(made, faces=made.faces)
    made.to_mesh(mesh)
    made.free()
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    return mesh


def lustre(name, coat):
    """Smoked glass, under the gold lustre if coat, as much of it as the mesh's "coat" says: a film of metal so thin
    it colours what it throws back where it thins. A shadow ray passes it in its colour (SHADOW), less the lustre."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.remove(nodes["Principled BSDF"])
    glass = node(nodes, "ShaderNodeBsdfGlass", Color=(*SMOKE, 1), Roughness=0.0, IOR=1.5)
    glass.distribution = "MULTI_GGX"
    surface = glass
    if coat:
        coord = nodes.new("ShaderNodeTexCoord")
        # The film runs thinner and thicker in broad swirls, as it was sprayed on the turning glass, and the metal
        # is smudged here and there.
        swirl = node(nodes, "ShaderNodeTexNoise", Scale=0.18, Detail=3.0, Roughness=0.5)
        links.new(coord.outputs["Object"], swirl.inputs["Vector"])
        film = nodes.new("ShaderNodeMapRange")
        film.inputs["From Min"].default_value = 0.55
        film.inputs["From Max"].default_value = 0.75
        film.inputs["To Max"].default_value = FILM
        links.new(swirl.outputs["Fac"], film.inputs["Value"])
        smudge = node(nodes, "ShaderNodeTexNoise", Scale=0.5, Detail=6.0, Roughness=0.6)
        links.new(coord.outputs["Object"], smudge.inputs["Vector"])
        dull = nodes.new("ShaderNodeMapRange")
        dull.inputs["From Min"].default_value = 0.5
        dull.inputs["From Max"].default_value = 0.75
        dull.inputs["To Min"].default_value = 0.01
        dull.inputs["To Max"].default_value = 0.05
        links.new(smudge.outputs["Fac"], dull.inputs["Value"])
        metal = nodes.new("ShaderNodeBsdfPrincipled")
        metal.inputs["Base Color"].default_value = (*GOLD, 1)
        metal.inputs["Metallic"].default_value = 1.0
        metal.inputs["Thin Film IOR"].default_value = 1.45
        links.new(film.outputs[0], metal.inputs["Thin Film Thickness"])
        links.new(dull.outputs[0], metal.inputs["Roughness"])
        share = nodes.new("ShaderNodeAttribute")
        share.attribute_name = "coat"
        coated = nodes.new("ShaderNodeMixShader")
        links.new(share.outputs["Fac"], coated.inputs[0])
        links.new(glass.outputs[0], coated.inputs[1])
        links.new(metal.outputs[0], coated.inputs[2])
        surface = coated
    shade = nodes.new("ShaderNodeLightPath")
    through = node(nodes, "ShaderNodeBsdfTransparent", Color=(*SHADOW, 1))
    if coat:
        left = nodes.new("ShaderNodeMath")
        left.operation = "SUBTRACT"
        left.inputs[0].default_value = 1.0
        links.new(share.outputs["Fac"], left.inputs[1])
        tint = nodes.new("ShaderNodeVectorMath")
        tint.operation = "SCALE"
        tint.inputs[0].default_value = SHADOW
        links.new(left.outputs[0], tint.inputs["Scale"])
        links.new(tint.outputs[0], through.inputs["Color"])
    out = nodes.new("ShaderNodeMixShader")
    links.new(shade.outputs["Is Shadow Ray"], out.inputs[0])
    links.new(surface.outputs[0], out.inputs[1])
    links.new(through.outputs[0], out.inputs[2])
    links.new(out.outputs[0], nodes["Material Output"].inputs["Surface"])
    return material


def metal(name, colour, rough):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*linear(colour), 1)
    shader.inputs["Metallic"].default_value = 1.0
    shader.inputs["Roughness"].default_value = rough
    return material


def glass(stage):
    mesh = glass_mesh("lustre-glass")
    mesh.materials.append(lustre("lustre-coated", True))
    mesh.materials.append(lustre("lustre-inside", False))
    return stage.add("lustre-glass", mesh)


def back(stage):
    """The steel back the glass is mounted on, painted dark bronze."""
    outline_ = [(0.0, 0.0)] + corner(BACK_R - 0.12, 0.12, 0.12, start=-math.pi / 2, end=0.0) + corner(BACK_R - 0.12, BACK_H - 0.12, 0.12, end=math.pi / 2) + [(0.0, BACK_H)]
    mesh = turned("lustre-back", outline_)
    mesh.materials.append(painted("lustre-back", BRONZE, 0.5))
    return stage.add("lustre-back", mesh)


def ring(stage):
    """The thin brass ring round the top of the housing that holds the lens."""
    section_ = [(CAN_R - 0.03 + 0.04 * math.cos(a), CAN_TOP - 0.02 + 0.04 * math.sin(a)) for a in np.linspace(-math.pi, math.pi, 17)]
    mesh = turned("lustre-ring", section_, around=256)
    mesh.materials.append(metal("lustre-brass", BRASS, 0.22))
    return stage.add("lustre-ring", mesh)


def clips(stage):
    """The five brass clips over the lens's edge: thin strips up over the ring and bent in and down onto it."""
    made = []
    material = metal("lustre-clip", BRASS, 0.25)
    for k, angle in enumerate(CLIPS):
        a = math.radians(angle)
        out = np.array([math.cos(a), math.sin(a), 0.0])
        hook = [tuple(out * (CAN_R + 0.01) + (0, 0, CAN_TOP - 0.1)), tuple(out * (CAN_R + 0.01) + (0, 0, CAN_TOP + 0.03)), tuple(out * (CAN_R - 0.16) + (0, 0, CAN_TOP - 0.03))]
        path = spline(hook, 0.01)
        mesh = bpy.data.meshes.new(f"lustre-clip-{k}")
        centres = path[0]
        side = np.cross(out, (0, 0, 1)) * 0.05
        verts = []
        for c in centres:
            verts += [tuple(c - side), tuple(c + side)]
        faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(len(centres) - 1)]
        mesh.from_pydata(verts, [], faces)
        mesh.materials.append(material)
        obj = stage.add(f"lustre-clip-{k}", mesh)
        modifier = obj.modifiers.new("thick", "SOLIDIFY")
        modifier.thickness = 0.015
        made.append(obj)
    return made


def housing(stage):
    """The bronze housing in the tube, from the back up to the ring, its collar out to the glass: the lens is sunk
    in it, so it gives its light up out of the tube and not into the glass round it, and the light inside the glass
    does not get out up the tube."""
    outline_ = [(0.0, BACK_H), (CAN_R - 0.05, BACK_H), (CAN_R - 0.05, CAN_TOP - 0.2), (COLLAR, CAN_TOP - 0.2), (COLLAR, CAN_TOP - 0.06)]
    outline_ += [(CAN_R - 0.1, CAN_TOP - 0.04), (CAN_R - 0.1, CAN_TOP - DOME - 0.12), (0.0, CAN_TOP - DOME - 0.12)]
    mesh = turned("lustre-housing", outline_, around=192)
    mesh.materials.append(metal("lustre-bronze", BRONZE, 0.35))
    return stage.add("lustre-housing", mesh)


def lens(stage):
    """The opal lens, domed, in the ring: it gives the light."""
    top = CAN_R - 0.06
    base = CAN_TOP - DOME - 0.04
    outline_ = [(0.0, base - 0.08), (top, base - 0.08)] + [(r, base + DOME * (1 - (r / top) ** 2) ** 0.5) for r in np.linspace(top, 0, 40)]
    mesh = turned("lustre-lens", outline_, around=192)
    co = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    weigh(mesh, (co[:, 2] > base - 0.03) * 1.0)
    area = math.pi * top**2
    mesh.materials.append(glowing("lustre-opal", BULB, SHARE, area, diffuse=OPAL))
    obj = stage.add("lustre-lens", mesh)
    obj["bulb"] = True
    obj["share"] = SHARE
    obj["area"] = area
    return obj


def leds(stage):
    """The strip of LEDs on the back under the funnel, behind a frosted cover, facing up into the glass: a ring round
    the housing, lit over the top, brightest straight up and fading out toward the sides and across its width."""
    angle = np.linspace(0, 2 * math.pi, 361)
    radius = np.linspace(LED_R[0], LED_R[1], 12)
    verts = [(r * math.cos(a), r * math.sin(a), BACK_H + 0.004) for a in angle for r in radius]
    n = len(radius)
    faces = [(i * n + j, i * n + j + 1, (i + 1) * n + j + 1, (i + 1) * n + j) for i in range(len(angle) - 1) for j in range(n - 1)]
    mesh = bpy.data.meshes.new("lustre-leds")
    mesh.from_pydata(verts, [], faces)
    co = np.array(verts)
    up = np.clip(co[:, 1] / np.hypot(co[:, 0], co[:, 1]), 0, 1)
    across = (np.hypot(co[:, 0], co[:, 1]) - LED_R[0]) / (LED_R[1] - LED_R[0])
    weight = up**LED_SPREAD * np.exp(-(((across - 0.4) / 0.3) ** 2))
    weigh(mesh, weight / weight.mean())
    area = math.pi * (LED_R[1] ** 2 - LED_R[0] ** 2)
    mesh.materials.append(glowing("lustre-leds", BULB, LED_SHARE, area, diffuse=BRONZE))
    obj = stage.add("lustre-leds", mesh)
    obj["bulb"] = True
    obj["share"] = LED_SHARE
    obj["area"] = area
    return obj


def band(stage):
    """The band of LEDs on a bronze riser round the edge of the back, at the height of the glass's side, facing
    out: it lights the shoulder from inside, and through the thin lustre on the side what is round the lamp."""
    mesh = turned("lustre-band", [(BAND_R, BAND_Z), (BAND_R, BAND_Z + BAND_W)], around=256)
    weigh(mesh, np.ones(len(mesh.vertices)))
    riser = turned("lustre-riser", [(BAND_R - 0.06, BACK_H), (BAND_R - 0.01, BACK_H), (BAND_R - 0.01, BAND_Z), (BAND_R - 0.06, BAND_Z)], around=256)
    riser.materials.append(metal("lustre-riser", BRONZE, 0.4))
    area = 2 * math.pi * BAND_R * BAND_W
    mesh.materials.append(glowing("lustre-band", BULB, BAND_SHARE, area))
    obj = stage.add("lustre-band", mesh)
    obj["bulb"] = True
    obj["share"] = BAND_SHARE
    obj["area"] = area
    return [obj, stage.add("lustre-riser", riser)]


def parts(stage):
    """Every part of the lamp, standing on z = 0 about its axis."""
    return [glass(stage), back(stage), housing(stage), ring(stage), *clips(stage), lens(stage), leds(stage), *band(stage)]


def build(stage):
    for part in parts(stage):
        part.location = (part.location.x + W / 2, part.location.y - H / 2, part.location.z)
    stage.shoot("lustrelamp", (0, 0, W, H), lens=False)


SHOTS = {"lustrelamp": build}
