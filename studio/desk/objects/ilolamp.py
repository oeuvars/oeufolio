"""The desk lamp: the ILO Light by Arieto Studio, a ring of glossy cream opal glass resting on an oxblood dock.

It is the lamp in the user's Pinterest pin and every view of it there: eight photographs and two films. The ring
is a fat cushion, as tall as its tube is wide, flat-topped and flat-bottomed with round sides, so from the side it
is a pill and from above a broad ring round a hole a little over a third of it across. Its glass is milky and
mirror-glossy: off, it is cream and shows the room in crisp reflections; on, it glows a warm white all round, from
light-emitting diodes inside it, a little brighter round the hole. It is a portable light that charges where it
rests: on a dock of painted metal, a wide drum with a flat ledge round its top, from which a cone tapers up to a
narrow top with a charging pad set into it. The ring sits on the rim of that top, the cone showing under it, and
lit, the ring's light makes the cone glow red.

The ring's glass is a thin shell. Its own light fills the tube and lights the glass from behind, which is what
shows of it, and reaches the dock under it through the glass. The lit glass is then the lamp: a surface just inside
it gives out its light onto everything round it, most where it glows most, and the glass, which that light has
already come through, holds none of it back (light linking).

Built in its own coordinates, in em: standing on z = 0, its middle at the middle of its box. Its lights are marked
"bulb", at no power until desk.py turns them up, each its "share" of the lamp's power; the glowing surface's power
is spread over its "area"."""

import math

import bmesh
import bpy
import numpy as np

from paint import linear

# The ring: how wide it is across, the radius its tube runs round at, and the tube's half-width and half-height.
# The tube's cross-section is a rounded square, a superellipse of this power: flat on top and underneath, round at
# the sides. The hole at its narrowest is the ring's radius less the tube's half-width, 0.37 of the ring across.
D = 10.5
HOLE = 0.185 * D
OUTER = 0.5 * D
RING = (HOLE + OUTER) / 2
TUBE = ((OUTER - HOLE) / 2, 0.155 * D)
SQUARE = 2.6
# The dock, turned on a lathe: its outline, radius and height in em from the middle of its foot, round its corners
# by the radius beside each. A wide drum, a flat ledge round its top, a cone up from the ledge to the narrow top, and
# in the top a shallow round pad for the ring to charge on.
DRUM = 0.355 * D
LEDGE = 0.32 * D
NECK = 0.30 * D
TOP = 0.21 * D
CROWN = LEDGE + 0.137 * D
PAD = 0.165 * D
DOCK = [
    (0.0, 0.0, 0.0),
    (DRUM - 0.12, 0.0, 0.0),
    (DRUM - 0.06, 0.07, 0.04),
    (DRUM, 0.22, 0.14),
    (DRUM, LEDGE, 0.12),
    (NECK + 0.06, LEDGE, 0.05),
    (NECK, LEDGE + 0.04, 0.06),
    (TOP + 0.05, CROWN - 0.14, 0.18),
    (TOP, CROWN, 0.08),
    (PAD + 0.08, CROWN, 0.03),
    (PAD, CROWN - 0.05, 0.02),
    (0.0, CROWN - 0.05, 0.0),
]
# The ring sits on the rim of the dock's top: its underside, curving up into the hole, rests there. How far over
# its flattest the underside stands at the top's radius, for the superellipse, sets how low the ring comes down.
_x = (RING - TOP) / TUBE[0]
SEATED = TUBE[1] * (1 - (1 - _x**SQUARE) ** (1 / SQUARE))
FOOT = CROWN - SEATED
MIDDLE_Z = FOOT + TUBE[1]
# The box the lamp stands in, in em.
W = H = D + 2.0

# The glass: its cream when the light falls on it from outside, as it does when the lamp is off; how much of the
# light reaching it from inside it lets through, and in what colour, warm white seen square on.
GLASS = "#efe7da"
THROUGH = (1.0, 0.9, 0.78)
TRANSLUCENT = 0.55
INSIDE = 0.2
# The glass is milky: the slanter the eye looks through it, the more glass the light crosses on its way out, and
# the warmer and dimmer it comes (Beer and Lambert). The path is taken as this power of the slant, and no longer
# than at this slant.
PATH = 0.8
GRAZING = 0.3
# What comes out of the lamp onto the desk: the yellow orange light of the desk's lamp before it, a glass donut.
# The diodes' own light, which lights the glass from inside, so that the glass glows the amber that lamp did, and
# how bright it is there against the lamp's light outside.
BULB_COLOUR = (1.0, 0.55, 0.1)
BULB_WHITE = (1.0, 0.35, 0.041)
GLASS_SHARE = 0.034
# The diodes inside the ring light the glass all round from inside it. What they fill the tube with stands for as
# this many lights round the ring, each this wide, at the middle of the tube, this high over its foot (as a share
# of its half-height): up toward its top, so the crest glows brightest and the glass falls off toward the hole and
# the rim, as a lit cushion does. What comes out of the glass lies round all of it alike, this much more on the side toward
# the hole and on top, and is, all told, this many times the lamp's power in desk.py.
BULBS = 16
FILL_R = 0.6
BULB_HIGH = 1.5
INNER = 0.25
POWER = 0.8
# How much of its light the underside of the ring gives, facing the dock and the desk, against the rest of it.
UNDER = 0.45
# Opal glass is not opaque: what light it lets through it colours, so its shadow is warm and not black.
SHADOW = (0.42, 0.36, 0.28)
# A blown shell is not quite true: it swells and dips this much, in em, over a few hand-widths.
WOBBLE = 0.025
# The dock's paint: a deep oxblood, a satin coat under a clear glossy one, the clear coat's faint orange peel.
OXBLOOD = "#6a1219"

# The page shows the lamp from a camera of its own (desk.py PORTRAITS), straight over it as far off as the plate's
# camera: round, as it is, the dock hidden under the ring but for its pad through the hole. Its middle, and the
# point on the desk under it, in the coordinates of the dock, which the camera is placed by.
DISTANCE = 100.0
MIDDLE = (0.0, 0.0, (MIDDLE_Z + TUBE[1]) / 2)
STANDS = (0.0, 0.0, 0.0)
BODY = "ilo-dock"


def photograph():
    """The camera over the lamp: where it stands, looking straight down, and its axes."""
    return np.array(MIDDLE) + np.array([0.0, 0.0, DISTANCE]), np.eye(3), None


def shell(stage, material, name="ilo-glass", inset=0.0, around=320, tube=192):
    """The ring: a torus whose cross-section is a rounded square, a little uneven as blown glass is, drawn in by
    inset em."""
    a, b = TUBE[0] - inset, TUBE[1] - inset
    u = np.linspace(0, 2 * math.pi, around, endpoint=False)
    v = np.linspace(0, 2 * math.pi, tube, endpoint=False)
    U, V = np.meshgrid(u, v, indexing="ij")
    rng = np.random.default_rng(11)
    swell = np.zeros_like(U)
    for k in range(1, 4):
        for j in range(0, 3):
            phase = rng.uniform(0, 2 * math.pi, 2)
            swell += rng.normal(0, 1) / (k + j) * np.cos(k * U + phase[0]) * np.cos(j * V + phase[1])
    swell *= WOBBLE / np.abs(swell).max()
    c, s = np.cos(V), np.sin(V)
    power = 2 / SQUARE
    across = np.sign(c) * np.abs(c) ** power
    high = np.sign(s) * np.abs(s) ** power
    r = RING + (a + swell) * across
    x, y = r * np.cos(U), r * np.sin(U)
    z = MIDDLE_Z + (b + swell) * high
    verts = np.column_stack((x.ravel(), y.ravel(), z.ravel()))
    i = np.arange(around)[:, None]
    j = np.arange(tube)[None, :]
    a0 = (i * tube + j).ravel()
    a1 = (((i + 1) % around) * tube + j).ravel()
    a2 = (((i + 1) % around) * tube + (j + 1) % tube).ravel()
    a3 = (i * tube + (j + 1) % tube).ravel()
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts.tolist(), [], np.column_stack((a0, a1, a2, a3)).tolist())
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.materials.append(material)
    return stage.add(name, mesh)


def rounded(outline, steps=8):
    """An outline of (radius, height, round) corners, each corner rounded off by its round."""
    points = []
    for k, (r, z, round_) in enumerate(outline):
        here = np.array([r, z])
        if round_ <= 0 or k == 0 or k == len(outline) - 1:
            points.append(here)
            continue
        before = np.array(outline[k - 1][:2])
        after = np.array(outline[k + 1][:2])
        into = (before - here) / np.linalg.norm(before - here)
        out = (after - here) / np.linalg.norm(after - here)
        reach = min(round_, np.linalg.norm(before - here) / 2, np.linalg.norm(after - here) / 2)
        start, end = here + into * reach, here + out * reach
        for t in np.linspace(0, 1, steps):
            points.append((1 - t) ** 2 * start + 2 * (1 - t) * t * here + t**2 * end)
    return np.array(points)


def lathe(stage, name, outline, material, around=256):
    """Turn an outline of radius and height round the upright axis."""
    profile = rounded(outline)
    u = np.linspace(0, 2 * math.pi, around, endpoint=False)
    count = len(profile)
    verts = np.column_stack(
        (
            (profile[None, :, 0] * np.cos(u)[:, None]).ravel(),
            (profile[None, :, 0] * np.sin(u)[:, None]).ravel(),
            np.broadcast_to(profile[None, :, 1], (around, count)).ravel(),
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
    # The outline starts and ends on the axis, where its turns all meet: weld them, and face everything outward.
    made = bmesh.new()
    made.from_mesh(mesh)
    bmesh.ops.remove_doubles(made, verts=made.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(made, edges=made.edges, dist=1e-6)
    bmesh.ops.recalc_face_normals(made, faces=made.faces)
    made.to_mesh(mesh)
    made.free()
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.materials.append(material)
    return stage.add(name, mesh)


def node(nodes, kind, **inputs):
    made = nodes.new(kind)
    for name, value in inputs.items():
        made.inputs[name.replace("_", " ")].default_value = value
    return made


def glass():
    """Milky cream glass under a clear polished skin. What lights it from outside it scatters back cream; what
    lights it from inside it lets through, diffused, warmer and dimmer the slanter it is seen. Over both lies the
    skin's own reflection, as strong as glass reflects at that angle, smooth but for faint smudges and a fine
    ripple from the blowing."""
    material = bpy.data.materials.new("ilo-glass")
    material.use_nodes = True
    tree = material.node_tree
    nodes, links = tree.nodes, tree.links
    nodes.remove(nodes["Principled BSDF"])
    out = nodes["Material Output"]
    coord = nodes.new("ShaderNodeTexCoord")
    smudge = node(nodes, "ShaderNodeTexNoise", Scale=0.5, Detail=6.0, Roughness=0.62)
    links.new(coord.outputs["Object"], smudge.inputs["Vector"])
    patches = nodes.new("ShaderNodeMapRange")
    patches.inputs["From Min"].default_value = 0.55
    patches.inputs["From Max"].default_value = 0.75
    patches.inputs["To Min"].default_value = 0.01
    patches.inputs["To Max"].default_value = 0.09
    links.new(smudge.outputs["Fac"], patches.inputs["Value"])
    ripple = node(nodes, "ShaderNodeTexNoise", Scale=2.2, Detail=2.0)
    links.new(coord.outputs["Object"], ripple.inputs["Vector"])
    bump = node(nodes, "ShaderNodeBump", Strength=1.0, Distance=0.002)
    links.new(ripple.outputs["Fac"], bump.inputs["Height"])
    scatter = node(nodes, "ShaderNodeBsdfDiffuse", Color=(*linear(GLASS), 1), Roughness=0.3)
    # The glow the glass lets through is what reflections of it show. What it throws on matte things round it is
    # the glowing surface inside it (luminaire), so light bounced off them sees no glow in it, or it would count twice.
    through = nodes.new("ShaderNodeBsdfTranslucent")
    light_path = nodes.new("ShaderNodeLightPath")
    glowing = nodes.new("ShaderNodeMix")
    glowing.data_type = "RGBA"
    glowing.inputs["B"].default_value = (0, 0, 0, 1)
    links.new(light_path.outputs["Is Diffuse Ray"], glowing.inputs["Factor"])
    # How much glass the light leaving toward the eye crosses, against square on, and what colour that leaves it.
    view = nodes.new("ShaderNodeNewGeometry")
    square = nodes.new("ShaderNodeVectorMath")
    square.operation = "DOT_PRODUCT"
    links.new(view.outputs["Normal"], square.inputs[0])
    links.new(view.outputs["Incoming"], square.inputs[1])
    slant = nodes.new("ShaderNodeMath")
    slant.operation = "ABSOLUTE"
    links.new(square.outputs["Value"], slant.inputs[0])
    held = nodes.new("ShaderNodeMath")
    held.operation = "MAXIMUM"
    held.inputs[1].default_value = GRAZING
    links.new(slant.outputs[0], held.inputs[0])
    crossed = nodes.new("ShaderNodeMath")
    crossed.operation = "POWER"
    crossed.inputs[1].default_value = -PATH
    links.new(held.outputs[0], crossed.inputs[0])
    passed = nodes.new("ShaderNodeCombineColor")
    for channel, face_on in zip(("Red", "Green", "Blue"), THROUGH):
        taken = nodes.new("ShaderNodeMath")
        taken.operation = "POWER"
        taken.inputs[0].default_value = face_on
        links.new(crossed.outputs[0], taken.inputs[1])
        links.new(taken.outputs[0], passed.inputs[channel])
    links.new(passed.outputs["Color"], glowing.inputs["A"])
    links.new(glowing.outputs["Result"], through.inputs["Color"])
    outside = node(nodes, "ShaderNodeMixShader", Fac=TRANSLUCENT)
    links.new(scatter.outputs[0], outside.inputs[1])
    links.new(through.outputs[0], outside.inputs[2])
    # Inside the tube the glass is dark: what of the diodes' light it does not let through it mostly takes in, so
    # the tube does not fill with light bounced round it.
    dim = node(nodes, "ShaderNodeBsdfDiffuse", Color=(*[c * INSIDE for c in linear(GLASS)], 1))
    inside = node(nodes, "ShaderNodeMixShader", Fac=TRANSLUCENT)
    links.new(dim.outputs[0], inside.inputs[1])
    links.new(through.outputs[0], inside.inputs[2])
    facing = nodes.new("ShaderNodeNewGeometry")
    body = nodes.new("ShaderNodeMixShader")
    links.new(facing.outputs["Backfacing"], body.inputs[0])
    links.new(outside.outputs[0], body.inputs[1])
    links.new(inside.outputs[0], body.inputs[2])
    skin = node(nodes, "ShaderNodeBsdfGlossy", Color=(1, 1, 1, 1))
    skin.distribution = "MULTI_GGX"
    links.new(patches.outputs[0], skin.inputs["Roughness"])
    links.new(bump.outputs[0], skin.inputs["Normal"])
    fresnel = node(nodes, "ShaderNodeFresnel", IOR=1.5)
    links.new(bump.outputs[0], fresnel.inputs["Normal"])
    layered = nodes.new("ShaderNodeMixShader")
    links.new(fresnel.outputs[0], layered.inputs[0])
    links.new(body.outputs[0], layered.inputs[1])
    links.new(skin.outputs[0], layered.inputs[2])
    shade = nodes.new("ShaderNodeLightPath")
    let_through = node(nodes, "ShaderNodeBsdfTransparent", Color=(*SHADOW, 1))
    surface = nodes.new("ShaderNodeMixShader")
    links.new(shade.outputs["Is Shadow Ray"], surface.inputs[0])
    links.new(layered.outputs[0], surface.inputs[1])
    links.new(let_through.outputs[0], surface.inputs[2])
    links.new(surface.outputs[0], out.inputs["Surface"])
    return material


def paint():
    """Oxblood paint on metal: a satin colour coat under a clear glossy coat with a faint orange peel."""
    material = bpy.data.materials.new("ilo-dock")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*linear(OXBLOOD), 1)
    shader.inputs["Roughness"].default_value = 0.38
    shader.inputs["Coat Weight"].default_value = 1.0
    shader.inputs["Coat Roughness"].default_value = 0.06
    shader.inputs["Coat IOR"].default_value = 1.5
    coord = nodes.new("ShaderNodeTexCoord")
    peel = node(nodes, "ShaderNodeTexNoise", Scale=9.0, Detail=3.0, Roughness=0.5)
    links.new(coord.outputs["Object"], peel.inputs["Vector"])
    bump = node(nodes, "ShaderNodeBump", Strength=0.25, Distance=0.004)
    links.new(peel.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs[0], shader.inputs["Coat Normal"])
    return material


def dock(stage):
    return lathe(stage, "ilo-dock", DOCK, paint())


def bulbs(stage, glass_obj, dock_obj):
    """The light the diodes fill the tube with, as it shows on the glass: lights round the ring at the middle of
    the tube, alike all round. They light the glass from behind, and the dock under it, through the glass, and
    nothing else."""
    only = bpy.data.collections.new("ilo-only")
    only.objects.link(glass_obj)
    only.objects.link(dock_obj)
    lights = []
    for k in range(BULBS):
        turn = 2 * math.pi * (k + 0.5) / BULBS
        source = bpy.data.lights.new(f"ilo-glow-{k}", "POINT")
        source.color = BULB_WHITE
        source.energy = 0.0
        source.shadow_soft_size = FILL_R
        obj = stage.add(f"ilo-glow-{k}", source)
        obj.location = (RING * math.cos(turn), RING * math.sin(turn), FOOT + BULB_HIGH * TUBE[1])
        obj.visible_camera = False
        obj.visible_glossy = False
        obj["bulb"] = True
        obj["share"] = GLASS_SHARE / BULBS
        obj.light_linking.receiver_collection = only
        lights.append(obj)
    return lights


def luminaire(stage, glass_obj, dock_obj):
    """The lamp's light on everything round it, which comes from the whole of the glowing glass: a surface just
    inside the glass, as large, giving out light where the glass glows, all round it and a little more toward the
    hole and on top. The glass neither takes its light nor stands in its way. The dock does not take it either: its
    pad shows only at the bottom of the hole, walled in by the glass a hair away, and lit by the lamp's whole power
    from there it would outshine the glass that lights it. It is lit as the glass is, from inside the ring (bulbs),
    and stands in the light's way, so the desk under the ring is in its shade."""
    clear = bpy.data.collections.new("ilo-clear")
    clear.objects.link(glass_obj)
    clear.collection_objects[0].light_linking.link_state = "EXCLUDE"
    unlit = bpy.data.collections.new("ilo-unlit")
    for part in (glass_obj, dock_obj):
        unlit.objects.link(part)
    for linked in unlit.collection_objects:
        linked.light_linking.link_state = "EXCLUDE"
    material = bpy.data.materials.new("ilo-light")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.remove(nodes["Principled BSDF"])
    glow = nodes.new("ShaderNodeAttribute")
    glow.attribute_name = "glow"
    power = nodes.new("ShaderNodeValue")
    power.name = "power"
    power.outputs[0].default_value = 0.0
    strength = nodes.new("ShaderNodeMath")
    strength.operation = "MULTIPLY"
    links.new(glow.outputs["Fac"], strength.inputs[0])
    links.new(power.outputs[0], strength.inputs[1])
    emit = node(nodes, "ShaderNodeEmission", Color=(*BULB_COLOUR, 1))
    links.new(strength.outputs[0], emit.inputs["Strength"])
    links.new(emit.outputs[0], nodes["Material Output"].inputs["Surface"])
    obj = shell(stage, material, "ilo-light", inset=0.06, around=192, tube=96)
    mesh = obj.data
    co = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    weight = 1 + INNER * (RING - np.hypot(co[:, 0], co[:, 1])) / TUBE[0]
    facing = (co[:, 2] - MIDDLE_Z) / TUBE[1]
    weight *= UNDER + (1 - UNDER) * np.clip((facing + 0.6) / 1.2, 0, 1)
    weight /= weight.mean()
    attribute = mesh.attributes.new("glow", "FLOAT", "POINT")
    attribute.data.foreach_set("value", weight.astype(np.float32))
    area = sum(polygon.area for polygon in mesh.polygons)
    for flag in ("visible_camera", "visible_glossy", "visible_transmission", "visible_shadow", "visible_volume_scatter"):
        setattr(obj, flag, False)
    obj["bulb"] = True
    obj["share"] = POWER
    obj["area"] = area
    obj.light_linking.receiver_collection = unlit
    obj.light_linking.blocker_collection = clear
    return obj


def build(stage):
    ring = shell(stage, glass())
    stand = dock(stage)
    parts = [ring, stand] + bulbs(stage, ring, stand) + [luminaire(stage, ring, stand)]
    for part in parts:
        part.location = (part.location.x + W / 2, part.location.y - H / 2, part.location.z)
    stage.shoot("ilolamp", (0, 0, W, H), lens=False)


SHOTS = {"ilolamp": build}
