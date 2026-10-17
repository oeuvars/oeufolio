"""The desk lamp: a round wall light of fluted amber glass under a copper mirror coat, on a white drum.

It is the lamp in the user's two photographs: one square on to its face, one from three quarters. A shallow drum of
amber glass stands on a white painted back a little narrower than it. Its face is pressed into ribs, fifteen
across, a smooth wave running straight across; they go right out to the rim, which they notch into a scalloped edge. The outside of the glass is coated with a thin copper mirror, so the ribs throw
back the room in copper and pink; lit, the light inside shows through it amber. Inside, on the back, an opal disc
gives the light. The ribs are lenses: each draws that disc out across it, so lit, the face glows in a wide oval of
bars, and the ribs past the disc show the dark copper walls of the drum, pinched into points.

The lamp lies on the desk on its back, its face up, the ribs across the page, its black braided cord out of the side
of the back and across the desk.

The glass is real glass: it bends the light through the ribs and throws back what the coat does. Light that has
passed glass that bends it does not reach the desk in a render, so the lamp's light on everything round it comes
from a surface just inside the glass, as large, giving out light where the glass glows; the glass neither takes
that light nor stands in its way (light linking).

Built in its own coordinates, in em: standing on z = 0, its middle at the middle of its box. Its lights are marked
"bulb", at no power until desk.py turns them up, each its "share" of the lamp's power; a glowing surface's power is
spread over its "area"."""

import math

import bmesh
import bpy
import numpy as np

from paint import linear

# The glass drum: across, and its radius.
D = 11.0
R = D / 2
# The white back it stands on: its height, its radius, and the round of its edge.
BACK_H = 0.12 * D
BACK_R = R - 0.12
BACK_ROUND = 0.3
# The glass: its foot on the back, the height of its rim, and the face over it, which rises by the ribs. The corner
# from face to side is rounded by RIM. The side wall is this thick, and the face, under its grooves, this thick.
FOOT = BACK_H
EDGE = FOOT + 0.36 * D
RIM = 0.35
WALL = 0.28
FACE = 0.5
# The ribs: this many across the face (15: the period of the light bands on the face in the front photograph and of
# the scallops on its rim in the three-quarter one), the face a sine wave across them, this deep from crest to trough
# (the scallops' depth in the three-quarter photograph). Each crest is a lens that draws the disc into a bright band,
# each trough one that spreads it into a dimmer band: two bands to a rib, as in the photograph.
RIBS = 15
PITCH = D / RIBS
CREST = 0.3 * PITCH
# The opal disc inside that gives the light, on a drum on the back that holds it close under the face: its radius,
# and how high it stands.
DISC_R = 0.4 * D
DISC_Z = EDGE - FACE - 1.8
# The box the lamp stands in, in em.
W = H = D + 2.0
TOP = EDGE + CREST

# The glass: amber, the share of each colour it lets through at each face it crosses; its copper coat, the colour
# copper throws back, and how much of the light it throws back rather than lets through.
AMBER = (1.0, 0.59, 0.31)
COPPER = (0.96, 0.6, 0.45)
COAT = 0.55
# The drum's wall is ground on the inside, so the side glows a satin orange and does not show the inside; its outside
# is satin too, under a thinner coat than the face's. The face's underside is lightly frosted, which softens the bars
# the ribs draw of the disc into one another.
GROUND = 0.45
SATIN = 0.22
SIDE_COAT = 0.08
FROST = 0.1
# Inside the wall stands a thin sleeve, pale orange where it faces the glass, so the side reads a satin orange in
# the light round it, and white inside, like the back.
SLEEVE = ("#e8873a", "#ecebe6")
# The floor of the drum, round the disc: the back's white paint.
FLOOR = "#ecebe6"
# The back is white paint; the opal disc a white plastic, and the light it gives white: all the colour in the lamp's
# light is what the glass makes of it.
WHITE = "#ecebe6"
OPAL = "#f3f1ec"
BULB_WHITE = (1.0, 1.0, 1.0)
DISC_SHARE = 0.0047
FALL = 0.35
# What comes out of the lamp onto the desk: the white light, through the glass's two faces, this many times the
# lamp's power in desk.py, most of it up through the face; the satin side glows too, at this share, as it does
# lit in the photograph.
BULB_COLOUR = tuple(white * c * c for white, c in zip(BULB_WHITE, AMBER))
POWER = 0.8
SIDE = 0.45
# The photograph's studio, for the glass alone to reflect: a white wall all round it this far off and this high, and
# a soft key over the top left, as the photograph's highlights and shadow show, this far up and this large. They
# light the glass and nothing else on the desk, are out of the lamp's picture, and are on with the lamp, at these
# shares of its power: lit, the copper face throws back the bright room the lamp was photographed in.
STUDIO_R = 40.0
STUDIO_H = 30.0
KEY_AT = (-30.0, 30.0, 60.0)
KEY_SIZE = 30.0
WALL_SHARE = 0.12
KEY_SHARE = 0.25
# Glass that bends light lets a shadow ray through in a render only if told: what of the light it lets through at
# each face, in its own colour, less what the coat throws back, so its shadow is amber and not black.
SHADOW = tuple(c * (1 - COAT) ** 0.5 for c in AMBER)
# The cord: black braided textile, this thick, out of the white back through a black rubber grommet, falling to the
# desk and lying across it to the right. Its braid is two sets of strands, this many each way round it, crossing
# one over one under every this many em along it, each strand a few yarns side by side.
CORD_R = 0.16
STRANDS = 8
LAY = 0.17
YARNS = 3
BRAID = 0.028
CORD_BLACK = "#121212"
# Where the cord leaves the back, how high, and the points it lies through on the desk after it: x along, y across.
CORD_Z = 0.62
LIES = [(BACK_R + 2.6, -0.2), (BACK_R + 4.2, -0.45), (12.5, -0.35), (16.0, 0.5), (20.0, 0.95), (25.0, 0.6), (31.0, 0.2)]

# The page shows the lamp from a camera of its own (desk.py PORTRAITS), straight over it as far off as the plate's
# camera: round, as its face was photographed. Its middle, and the point on the desk under it, in the coordinates
# of the glass, which the camera is placed by.
DISTANCE = 100.0
MIDDLE = (0.0, 0.0, (FOOT + TOP) / 2)
STANDS = (0.0, 0.0, 0.0)
BODY = "flute-glass"


def photograph():
    """The camera over the lamp: where it stands, looking straight down, and its axes."""
    return np.array(MIDDLE) + np.array([0.0, 0.0, DISTANCE]), np.eye(3), None


def rib(y):
    """How high the face stands over its troughs at y: a sine wave, crest to trough, across the ribs."""
    return CREST * (0.5 + 0.5 * np.cos(2 * math.pi * y / PITCH))


def profile():
    """The glass's section, from the middle of its face out over the rim, down the side, under its foot, up the
    inside and back across under the face to the middle: radius, height, how far round the rim's corner (1 on the
    face, 0 down the side), and which surface it is (0 the coated face, 1 frosted inside under the face, 2
    ground inside the wall, 3 the satin side)."""
    rows = []
    for r in np.linspace(0, R - RIM, 300):
        rows.append((r, EDGE, 1.0, 0))
    for phi in np.linspace(0, math.pi / 2, 28)[1:]:
        rows.append((R - RIM + RIM * math.sin(phi), EDGE - RIM + RIM * math.cos(phi), math.cos(phi), 0))
    for z in np.linspace(EDGE - RIM, FOOT, 30)[1:]:
        rows.append((R, z, 0.0, 3))
    inner = R - WALL
    ceiling = EDGE - FACE
    rows.append((R - WALL / 2, FOOT, 0.0, 2))
    for z in np.linspace(FOOT, ceiling - 0.2, 24):
        rows.append((inner, z, 0.0, 2))
    for phi in np.linspace(0, math.pi / 2, 8)[1:]:
        rows.append((inner - 0.2 + 0.2 * math.cos(phi), ceiling - 0.2 + 0.2 * math.sin(phi), 0.0, 1))
    for r in np.linspace(inner - 0.2, 0, 160)[1:]:
        rows.append((r, ceiling, 0.0, 1))
    return np.array(rows)


def glass_mesh(name, around=1440):
    """The glass as one closed solid: its section turned round the axis, its outside pressed into ribs across y,
    which it carries over the rim's corner along the corner's normal and loses by the time the side is straight."""
    section = profile()
    count = len(section)
    u = np.linspace(0, 2 * math.pi, around, endpoint=False)
    r = section[None, :, 0]
    x = r * np.cos(u)[:, None]
    y = r * np.sin(u)[:, None]
    z = np.broadcast_to(section[None, :, 1], x.shape).copy()
    face = section[None, :, 2]
    outside = (section[None, :, 3] == 0) | (section[None, :, 3] == 3)
    rise = np.where(outside, rib(y), 0.0)
    # Over the corner the rise goes along its normal: up on the face, outward and up round the rim.
    phi = np.arccos(np.clip(face, 0, 1))
    out = rise * face * np.sin(phi)
    x = x + out * np.cos(u)[:, None]
    y = y + out * np.sin(u)[:, None]
    z = z + rise * face * np.cos(phi)
    verts = np.column_stack((x.ravel(), y.ravel(), z.ravel()))
    i = np.arange(around)[:, None]
    j = np.arange(count - 1)[None, :]
    a0 = (i * count + j).ravel()
    a1 = (((i + 1) % around) * count + j).ravel()
    a2 = (((i + 1) % around) * count + j + 1).ravel()
    a3 = (i * count + j + 1).ravel()
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts.tolist(), [], np.column_stack((a0, a1, a2, a3)).tolist())
    surfaces = np.broadcast_to(section[None, :-1, 3], (around, count - 1)).astype(np.int32).ravel()
    mesh.polygons.foreach_set("material_index", surfaces)
    # The section starts and ends on the axis, where its turns all meet: weld them, and face everything outward.
    made = bmesh.new()
    made.from_mesh(mesh)
    bmesh.ops.remove_doubles(made, verts=made.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(made, edges=made.edges, dist=1e-6)
    bmesh.ops.recalc_face_normals(made, faces=made.faces)
    made.to_mesh(mesh)
    made.free()
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    return mesh


def turned(name, outline, around=256):
    """A solid turned from an outline of radius and height, from the axis round and back to it."""
    outline = np.asarray(outline, dtype=float)
    count = len(outline)
    u = np.linspace(0, 2 * math.pi, around, endpoint=False)
    verts = np.column_stack(
        (
            (outline[None, :, 0] * np.cos(u)[:, None]).ravel(),
            (outline[None, :, 0] * np.sin(u)[:, None]).ravel(),
            np.broadcast_to(outline[None, :, 1], (around, count)).ravel(),
        )
    )
    i = np.arange(around)[:, None]
    j = np.arange(count - 1)[None, :]
    a0 = (i * count + j).ravel()
    a1 = (((i + 1) % around) * count + j).ravel()
    a2 = (((i + 1) % around) * count + j + 1).ravel()
    a3 = (i * count + j + 1).ravel()
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts.tolist(), [], np.column_stack((a0, a1, a2, a3)).tolist())
    made = bmesh.new()
    made.from_mesh(mesh)
    bmesh.ops.remove_doubles(made, verts=made.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(made, edges=made.edges, dist=1e-6)
    bmesh.ops.recalc_face_normals(made, faces=made.faces)
    made.to_mesh(mesh)
    made.free()
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    return mesh


def corner(r, z, round_, steps=10, start=0.0, end=math.pi / 2):
    """A quarter round of radius round_ about (r, z), from angle start to end (0 straight out, pi/2 straight up)."""
    return [(r + round_ * math.cos(a), z + round_ * math.sin(a)) for a in np.linspace(start, end, steps)]


def node(nodes, kind, **inputs):
    made = nodes.new(kind)
    for name, value in inputs.items():
        made.inputs[name.replace("_", " ")].default_value = value
    return made


def amber(name, rough, coat):
    """Amber glass, polished or ground, under as much of the copper mirror coat as coat. A shadow ray passes it in
    its colour (SHADOW)."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.remove(nodes["Principled BSDF"])
    glass = node(nodes, "ShaderNodeBsdfGlass", Color=(*AMBER, 1), Roughness=rough, IOR=1.52)
    glass.distribution = "MULTI_GGX"
    surface = glass
    if coat:
        # The coat is a film of copper too thin to stop all the light: it throws back its copper share, smooth but
        # for faint smudges, and lets the rest into the glass.
        coord = nodes.new("ShaderNodeTexCoord")
        smudge = node(nodes, "ShaderNodeTexNoise", Scale=0.35, Detail=5.0, Roughness=0.6)
        links.new(coord.outputs["Object"], smudge.inputs["Vector"])
        dull = nodes.new("ShaderNodeMapRange")
        dull.inputs["From Min"].default_value = 0.5
        dull.inputs["From Max"].default_value = 0.75
        dull.inputs["To Min"].default_value = 0.015
        dull.inputs["To Max"].default_value = 0.07
        links.new(smudge.outputs["Fac"], dull.inputs["Value"])
        mirror = node(nodes, "ShaderNodeBsdfGlossy", Color=(*COPPER, 1))
        mirror.distribution = "MULTI_GGX"
        links.new(dull.outputs[0], mirror.inputs["Roughness"])
        coated = node(nodes, "ShaderNodeMixShader", Fac=coat)
        links.new(glass.outputs[0], coated.inputs[1])
        links.new(mirror.outputs[0], coated.inputs[2])
        surface = coated
    shade = nodes.new("ShaderNodeLightPath")
    through = node(nodes, "ShaderNodeBsdfTransparent", Color=(*SHADOW, 1))
    out = nodes.new("ShaderNodeMixShader")
    links.new(shade.outputs["Is Shadow Ray"], out.inputs[0])
    links.new(surface.outputs[0], out.inputs[1])
    links.new(through.outputs[0], out.inputs[2])
    links.new(out.outputs[0], nodes["Material Output"].inputs["Surface"])
    return material


def painted(name, colour, rough):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*linear(colour), 1)
    shader.inputs["Roughness"].default_value = rough
    return material


def glowing(name, colour, share, area, diffuse=None):
    """A surface that gives light of colour, at its share of the lamp's power spread over its area (its "power"
    node, which desk.py sets), over a matte colour of its own if it has one."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.remove(nodes["Principled BSDF"])
    weight = nodes.new("ShaderNodeAttribute")
    weight.attribute_name = "glow"
    power = nodes.new("ShaderNodeValue")
    power.name = "power"
    power.outputs[0].default_value = 0.0
    strength = nodes.new("ShaderNodeMath")
    strength.operation = "MULTIPLY"
    links.new(weight.outputs["Fac"], strength.inputs[0])
    links.new(power.outputs[0], strength.inputs[1])
    emit = node(nodes, "ShaderNodeEmission", Color=(*colour, 1))
    links.new(strength.outputs[0], emit.inputs["Strength"])
    surface = emit
    if diffuse is not None:
        matte = node(nodes, "ShaderNodeBsdfDiffuse", Color=(*linear(diffuse), 1))
        both = nodes.new("ShaderNodeAddShader")
        links.new(matte.outputs[0], both.inputs[0])
        links.new(emit.outputs[0], both.inputs[1])
        surface = both
    links.new(surface.outputs[0], nodes["Material Output"].inputs["Surface"])
    return material


def weigh(mesh, weight):
    attribute = mesh.attributes.new("glow", "FLOAT", "POINT")
    attribute.data.foreach_set("value", np.asarray(weight, dtype=np.float32))


def glass(stage):
    mesh = glass_mesh("flute-glass")
    for material in (amber("flute-coated", 0.0, COAT), amber("flute-inside", FROST, 0.0), amber("flute-ground", GROUND, 0.0), amber("flute-side", SATIN, SIDE_COAT)):
        mesh.materials.append(material)
    return stage.add("flute-glass", mesh)


def back(stage):
    """The white back, its top the floor of the drum."""
    outline = [(0.0, 0.0)] + corner(BACK_R - BACK_ROUND, BACK_ROUND, BACK_ROUND, start=-math.pi / 2, end=0.0)
    outline += [(BACK_R, FOOT - 0.02), (0.0, FOOT - 0.02)]
    mesh = turned("flute-back", outline)
    mesh.materials.append(painted("flute-white", WHITE, 0.55))
    mesh.materials.append(painted("flute-floor", FLOOR, 0.6))
    inside = [int(p.center.z > FOOT - 0.05 and math.hypot(p.center.x, p.center.y) < BACK_R - 0.01) for p in mesh.polygons]
    mesh.polygons.foreach_set("material_index", inside)
    return stage.add("flute-back", mesh)


def disc(stage):
    """The opal disc that gives the light, a little domed, its edge rounded, on a drum down to the back. Only its top
    gives light."""
    outline = [(0.0, FOOT), (DISC_R, FOOT)] + corner(DISC_R - 0.12, DISC_Z - 0.12, 0.12, end=math.pi / 2)
    outline += [(r, DISC_Z + 0.06 * (1 - (r / DISC_R) ** 2)) for r in np.linspace(DISC_R - 0.12, 0, 40)]
    mesh = turned("flute-disc", outline, around=192)
    co = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    out = np.hypot(co[:, 0], co[:, 1]) / DISC_R
    weigh(mesh, (co[:, 2] > DISC_Z - 0.1) * np.clip(1 - out**2, 0, 1) ** FALL / (1 + FALL) * (1 + FALL))
    area = math.pi * DISC_R**2
    mesh.materials.append(glowing("flute-opal", BULB_WHITE, DISC_SHARE, area, diffuse=OPAL))
    obj = stage.add("flute-disc", mesh)
    obj["bulb"] = True
    obj["share"] = DISC_SHARE
    obj["area"] = area
    return obj


def sleeve(stage):
    """The sleeve inside the drum's wall: pale facing out, dark facing in."""
    inner = R - WALL - 0.04
    outline = [(inner, FOOT), (inner, EDGE - FACE - 0.25), (inner - 0.03, EDGE - FACE - 0.25), (inner - 0.03, FOOT)]
    mesh = turned("flute-sleeve", outline, around=256)
    material = bpy.data.materials.new("flute-sleeve")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.remove(nodes["Principled BSDF"])
    out = node(nodes, "ShaderNodeBsdfDiffuse", Color=(*linear(SLEEVE[0]), 1))
    into = node(nodes, "ShaderNodeBsdfDiffuse", Color=(*linear(SLEEVE[1]), 1))
    facing = nodes.new("ShaderNodeNewGeometry")
    either = nodes.new("ShaderNodeMixShader")
    co = np.empty(len(mesh.polygons) * 3)
    mesh.polygons.foreach_get("center", co)
    co = co.reshape(-1, 3)
    # Faces of the sleeve's inner skin are the dark ones.
    mesh.materials.append(material)
    dark = bpy.data.materials.new("flute-sleeve-in")
    dark.use_nodes = True
    dark.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*linear(SLEEVE[1]), 1)
    dark.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
    mesh.materials.append(dark)
    mesh.polygons.foreach_set("material_index", (np.hypot(co[:, 0], co[:, 1]) < inner - 0.015).astype(np.int32))
    nodes.remove(facing)
    nodes.remove(into)
    nodes.remove(either)
    links.new(out.outputs[0], nodes["Material Output"].inputs["Surface"])
    return stage.add("flute-sleeve", mesh)


def luminaire(stage, glass_obj, back_obj, disc_obj):
    """The lamp's light on everything round it, which comes from the whole of the glowing glass: a surface just
    inside the glass, as large, giving out its light up through the face and less of it out of the side. The glass
    neither takes its light nor stands in its way; the back and the disc do not take it either, but the back, under
    it, shades the desk."""
    clear = bpy.data.collections.new("flute-clear")
    unlit = bpy.data.collections.new("flute-unlit")
    # The back, under it, stands in its way: the desk under the lamp is in its shade.
    for part in (glass_obj, disc_obj, *[obj for obj in bpy.context.scene.objects if obj.name.startswith("flute-sleeve")]):
        clear.objects.link(part)
    for part in (glass_obj, back_obj, disc_obj, *[obj for obj in bpy.context.scene.objects if obj.name.startswith("flute-sleeve")]):
        unlit.objects.link(part)
    for linked in (*clear.collection_objects, *unlit.collection_objects):
        linked.light_linking.link_state = "EXCLUDE"
    inset = 0.08
    outline = [(0.0, EDGE - inset)] + corner(R - RIM, EDGE - RIM, RIM - inset, steps=12, start=math.pi / 2, end=0.0)
    outline += [(R - inset, FOOT + 0.05), (0.0, FOOT + 0.05)]
    mesh = turned("flute-light", outline, around=192)
    co = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    on_face = co[:, 2] > EDGE - RIM
    weight = np.where(on_face, 1.0, SIDE)
    weight = np.where(co[:, 2] < FOOT + 0.1, 0.0, weight)
    weight /= weight.mean()
    weigh(mesh, weight)
    area = sum(polygon.area for polygon in mesh.polygons)
    mesh.materials.append(glowing("flute-light", BULB_COLOUR, POWER, area))
    obj = stage.add("flute-light", mesh)
    for flag in ("visible_camera", "visible_glossy", "visible_transmission", "visible_shadow", "visible_volume_scatter"):
        setattr(obj, flag, False)
    obj["bulb"] = True
    obj["unseen"] = True
    obj["share"] = POWER
    obj["area"] = area
    obj.light_linking.receiver_collection = unlit
    obj.light_linking.blocker_collection = clear
    return obj


def spline(points, step):
    """A smooth path through points (Catmull and Rom), sampled every step em along it."""
    points = np.asarray(points, dtype=float)
    padded = np.vstack((2 * points[0] - points[1], points, 2 * points[-1] - points[-2]))
    dense = []
    for k in range(1, len(padded) - 2):
        p0, p1, p2, p3 = padded[k - 1 : k + 3]
        for t in np.linspace(0, 1, 60, endpoint=False):
            dense.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t**3))
    dense.append(points[-1])
    dense = np.array(dense)
    along = np.concatenate(([0], np.cumsum(np.linalg.norm(np.diff(dense, axis=0), axis=1))))
    s = np.arange(0, along[-1], step)
    return np.column_stack([np.interp(s, along, dense[:, axis]) for axis in range(3)]), s


def tube(name, path, radius, around, height=None):
    """A tube round a path, its rings square to it, carried along without twisting; height(s, angle) pushes its
    surface out, in em. Returns the mesh."""
    centres, s = path
    ahead = np.gradient(centres, axis=0)
    ahead /= np.linalg.norm(ahead, axis=1)[:, None]
    normal = np.cross(ahead[0], (0.0, 0.0, 1.0))
    normal /= np.linalg.norm(normal)
    normals = []
    for k in range(len(centres)):
        normal = normal - ahead[k] * np.dot(normal, ahead[k])
        normal /= np.linalg.norm(normal)
        normals.append(normal)
    normals = np.array(normals)
    binormals = np.cross(ahead, normals)
    angle = np.linspace(0, 2 * math.pi, around, endpoint=False)
    out = radius + (height(s[:, None], angle[None, :]) if height else 0.0)
    rings = centres[:, None, :] + out[..., None] * (np.cos(angle)[None, :, None] * normals[:, None, :] + np.sin(angle)[None, :, None] * binormals[:, None, :])
    count = len(centres)
    verts = np.vstack((rings.reshape(-1, 3), centres[0], centres[-1]))
    i = np.arange(count - 1)[:, None]
    j = np.arange(around)[None, :]
    a0 = (i * around + j).ravel()
    a1 = ((i + 1) * around + j).ravel()
    a2 = ((i + 1) * around + (j + 1) % around).ravel()
    a3 = (i * around + (j + 1) % around).ravel()
    faces = np.column_stack((a0, a1, a2, a3)).tolist()
    first, last = count * around, count * around + 1
    faces += [(first, (k + 1) % around, k) for k in range(around)]
    faces += [(last, (count - 1) * around + k, (count - 1) * around + (k + 1) % around) for k in range(around)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts.tolist(), [], faces)
    made = bmesh.new()
    made.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(made, faces=made.faces)
    made.to_mesh(mesh)
    made.free()
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    return mesh


def braid(s, angle):
    """The braid's relief: two sets of strands round the cord, one each way, each passing over one of the other
    and under the next; each strand a few yarns, each a round ridge. Height over the cord's radius, in em."""
    turn = STRANDS * angle / (2 * math.pi)
    a, b = turn + s / LAY, turn - s / LAY
    ua, ub = np.mod(a, 1.0), np.mod(b, 1.0)
    over = (np.floor(a) + np.floor(b)) % 2 == 0
    # A strand rises to the middle of the crossing it is over and dives toward the crossings it goes under.
    lift_a = np.sin(math.pi * ub) ** 0.6
    lift_b = np.sin(math.pi * ua) ** 0.6
    yarn_a = np.abs(np.sin(math.pi * YARNS * ua)) ** 0.5
    yarn_b = np.abs(np.sin(math.pi * YARNS * ub)) ** 0.5
    top_a = lift_a * (0.75 + 0.25 * yarn_a)
    top_b = lift_b * (0.75 + 0.25 * yarn_b)
    return BRAID * (np.where(over, np.maximum(top_a, 0.55 * top_b), np.maximum(top_b, 0.55 * top_a)) - 0.5)


def textile():
    """Black braided polyester: dark, with the soft sheen of fibres along the strands, darker in the hollows the
    braid's relief leaves (from the mesh's "hollow")."""
    material = bpy.data.materials.new("flute-cord")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Roughness"].default_value = 0.6
    shader.inputs["Specular IOR Level"].default_value = 0.2
    shader.inputs["Sheen Weight"].default_value = 0.15
    shader.inputs["Sheen Roughness"].default_value = 0.4
    shader.inputs["Sheen Tint"].default_value = (0.25, 0.25, 0.25, 1)
    hollow = nodes.new("ShaderNodeAttribute")
    hollow.attribute_name = "hollow"
    shade = nodes.new("ShaderNodeMix")
    shade.data_type = "RGBA"
    shade.inputs["A"].default_value = (*linear(CORD_BLACK), 1)
    shade.inputs["B"].default_value = (*[0.35 * c for c in linear(CORD_BLACK)], 1)
    links.new(hollow.outputs["Fac"], shade.inputs["Factor"])
    links.new(shade.outputs["Result"], shader.inputs["Base Color"])
    return material


def rubber():
    material = bpy.data.materials.new("flute-grommet")
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*linear("#0e0e0e"), 1)
    shader.inputs["Roughness"].default_value = 0.42
    return material


def cord(stage):
    """The cord and the grommet it leaves the back through. Both lie on the desk and are drawn in the plate, not in
    the lamp's own picture ("plated")."""
    out = BACK_R - 0.05
    drop = [(out - 0.6, 0.0, CORD_Z), (out + 0.4, 0.0, CORD_Z), (out + 1.4, -0.05, CORD_Z - 0.14)]
    lying = [(x, y, CORD_R + BRAID / 2) for x, y in LIES]
    path = spline(drop + lying, 0.012)
    mesh = tube("flute-cord", path, CORD_R, 112, braid)
    s = path[1]
    angle = np.linspace(0, 2 * math.pi, 112, endpoint=False)
    relief = braid(s[:, None], angle[None, :]).ravel() / BRAID + 0.5
    hollow = np.concatenate((np.clip(0.9 - relief, 0, 1) ** 1.5, [0, 0]))
    attribute = mesh.attributes.new("hollow", "FLOAT", "POINT")
    attribute.data.foreach_set("value", hollow.astype(np.float32))
    mesh.materials.append(textile())
    wire = stage.add("flute-cord", mesh)
    sleeve_path = spline([(out - 0.2, 0.0, CORD_Z), (out + 0.45, 0.0, CORD_Z)], 0.02)
    grommet = tube("flute-grommet", sleeve_path, CORD_R + 0.07, 64, lambda s, a: 0.02 * np.minimum(1, s / 0.1) - 0.04 * np.clip((s - 0.55) / 0.1, 0, 1))
    grommet.materials.append(rubber())
    boot = stage.add("flute-grommet", grommet)
    for obj in (wire, boot):
        obj["plated"] = True
    return [wire, boot]


def studio(stage, glass_obj):
    """The photograph's studio round the glass: the wall and the key, white, seen by the glass's reflections alone."""
    only = bpy.data.collections.new("flute-only")
    only.objects.link(glass_obj)
    made = []
    around = np.linspace(0, 2 * math.pi, 96, endpoint=False)
    wall = bpy.data.meshes.new("flute-wall")
    verts = [(STUDIO_R * math.cos(a), STUDIO_R * math.sin(a), z) for a in around for z in (0.0, STUDIO_H)]
    faces = [(2 * k, 2 * ((k + 1) % 96), 2 * ((k + 1) % 96) + 1, 2 * k + 1) for k in range(96)]
    wall.from_pydata(verts, [], faces)
    key = bpy.data.meshes.new("flute-key")
    centre = np.array(KEY_AT)
    facing = -centre / np.linalg.norm(centre)
    across = np.cross(facing, (0.0, 0.0, 1.0))
    across /= np.linalg.norm(across)
    up = np.cross(across, facing)
    half = KEY_SIZE / 2
    key.from_pydata([tuple(centre + half * (i * across + j * up)) for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))], [], [(0, 1, 2, 3)])
    for mesh, share in ((wall, WALL_SHARE), (key, KEY_SHARE)):
        weigh(mesh, np.ones(len(mesh.vertices)))
        area = sum(polygon.area for polygon in mesh.polygons)
        mesh.materials.append(glowing(mesh.name, (1.0, 1.0, 1.0), share, area))
        obj = stage.add(mesh.name, mesh)
        for flag in ("visible_camera", "visible_diffuse", "visible_transmission", "visible_shadow", "visible_volume_scatter"):
            setattr(obj, flag, False)
        obj["bulb"] = True
        obj["unseen"] = True
        obj["share"] = share
        obj["area"] = area
        obj.light_linking.receiver_collection = only
        made.append(obj)
    return made


def parts(stage):
    """Every part of the lamp, standing on z = 0 about its axis."""
    shade = glass(stage)
    drum = back(stage)
    opal = disc(stage)
    lining = sleeve(stage)
    return [shade, drum, opal, lining, luminaire(stage, shade, drum, opal), *studio(stage, shade), *cord(stage)]


def build(stage):
    for part in parts(stage):
        part.location = (part.location.x + W / 2, part.location.y - H / 2, part.location.z)
    stage.shoot("flutelamp", (0, 0, W, H), lens=False)


SHOTS = {"flutelamp": build}
