"""The desk lamp: a donut of blown orange opal glass, resting on a flat round white base, lit by a bulb in its hole.

It is the lamp in the user's Pinterest pin (a glass donut table lamp, glowing orange on a book by a bed) and the
pins beside it: a fat ring whose tube is nearly as thick as the ring is wide, so the hole through the middle is
only a small hole from above, the glass a deep glossy orange when it is off, and when it is on glowing all round,
hottest and yellow round the hole, deeper toward the rim. The glass rests on a flat round base, and the bulb stands in
the base's middle, up into the hole, its mirrored crown showing through it (the user's photograph of it lit).

The glass is a thin shell. Seen from outside it is a clear, polished skin over milky orange glass: a mirror-smooth
reflection, faintly smudged where it is handled, over a surface that scatters what lights it from outside, and lets
through, diffused, what lights it from inside. The bulb's light fills the tube and lights the glass from behind,
which is what shows of it. The lit glass is then the lamp: a surface just inside it gives out its light onto everything round it, most
where it glows most, in the colour it passes, and the glass, which that light has already come through, holds none
of it back (light linking).

Built in its own coordinates, in em: lying on z = 0, its middle at the middle of its box. Its lights are marked
"bulb", at no power until desk.py turns them up, each its "share" of the lamp's power; the glowing surface's power
is spread over its "area"."""

import math

import bpy
import numpy as np

from paint import linear

# The donut: how wide it is across, how far its tube's middle runs from the middle of the ring, and the tube's
# half-width and half-height. The hole at its narrowest is the ring's radius less the tube's half-width.
D = 10.5
RING = 0.58 * D / 2
TUBE = (0.42 * D / 2, 0.42 * D / 2)
# It sits on a flat round base of white plastic, this wide across and this tall, its edge rounded this much, the
# glass resting on it this far down into its top. The bulb stands in the middle of the base, up into the hole: a
# frosted globe this wide with a mirrored crown over it down past its middle, which is all that shows of it through
# the hole: a dark mirror, round it the lit glass of the hole, and none of the frosted globe's own glow.
BASE = (0.78 * D, 0.45, 0.15)
SEAT = 0.03
LIFT = BASE[1] - SEAT
GLOBE = 0.06 * D
# The box the lamp stands in, in em.
W = H = D + 2.0

# The glass: its orange when the light falls on it from outside, as it does when the lamp is off; how much of the
# light reaching it from inside it lets through, and in what colour, the warm white of the bulb turned a yellow orange by it.
GLASS = "#f06a0a"
THROUGH = (1.0, 0.45, 0.08)
# How much of what lights the glass it lets through, against what it scatters back, and how much of the
# glass's orange it scatters back inside the tube.
TRANSLUCENT = 0.6
# The orange is in the glass, so the slanter the eye looks through it, the more glass the light crosses on its way
# out and the more of its green and blue the glass takes (Beer and Lambert): THROUGH is its colour seen square on,
# and it deepens toward red where the glass turns away, to the rim and round the hole. The path is taken as this
# power of the slant, and no longer than at this slant, past which the light leaves by a shorter way.
PATH = 1.6
GRAZING = 0.15
INSIDE = 0.15
# What comes out of the lamp onto the desk: the bulb's warm light as the orange glass passes it. The bulb's own
# warm white, which lights the glass from inside, and how bright it is there against the lamp's light outside.
BULB_COLOUR = (1.0, 0.55, 0.1)
BULB_WHITE = (1.0, 0.7, 0.4)
GLASS_SHARE = 0.034
# The bulb in the hole lights the glass all round from inside it, most on the side toward the hole. What it fills
# the tube with stands for as this many lights round the ring, each this wide, this far in toward the hole from the
# middle of the tube (as a share of the tube's half-width), this high over the glass's foot. What comes out of the
# glass lies round all of it alike, this much more on the side toward the hole, and is, all told, this many times
# the lamp's power in desk.py. The bulb's own globe gives this share of it.
BULBS = 12
FILL_R = 0.053 * D
INWARD = 0.4
BULB_HIGH = 0.16 * D
INNER = 0.4
POWER = 0.8
# How much of its light the underside of the tube, facing the desk, gives against the rest of it.
UNDER = 0.15
GLOBE_SHARE = 0.0001
# Opal glass is not opaque: what light it lets through it colours, so its shadow is orange and not black.
SHADOW = (0.5, 0.22, 0.05)
# The page shows the lamp from a camera of its own (desk.py PORTRAITS), straight over it at this height, the
# plate's camera's: round, as it is, wherever it stands on the desk. Its middle, and the point on the desk under it,
# in the coordinates of the glass, which the camera is placed by.
OVERHEAD = 100.0
MIDDLE = (0.0, 0.0, LIFT + TUBE[1])
STANDS = (0.0, 0.0, 0.0)
BODY = "donut-glass"
# A hand-blown shell is not quite true: it swells and dips this much, in em, over a few hand-widths.
WOBBLE = 0.05


def photograph():
    """The camera over the lamp: where it stands, looking straight down, and its axes."""
    return np.array([0.0, 0.0, OVERHEAD]), np.eye(3), None


def shell(stage, material, name="donut-glass", inset=0.0, around=288, tube=128):
    """The torus, its cross-section an ellipse, a little uneven as blown glass is, drawn in by inset em."""
    a, b = TUBE
    u = np.linspace(0, 2 * math.pi, around, endpoint=False)
    v = np.linspace(0, 2 * math.pi, tube, endpoint=False)
    U, V = np.meshgrid(u, v, indexing="ij")
    rng = np.random.default_rng(7)
    swell = np.zeros_like(U)
    for k in range(1, 4):
        for j in range(0, 3):
            phase = rng.uniform(0, 2 * math.pi, 2)
            swell += rng.normal(0, 1) / (k + j) * np.cos(k * U + phase[0]) * np.cos(j * V + phase[1])
    swell *= WOBBLE / np.abs(swell).max()
    rx = a + swell - inset
    rz = b + swell - inset
    r = RING + rx * np.cos(V)
    x, y = r * np.cos(U), r * np.sin(U)
    z = LIFT + b + rz * np.sin(V)
    verts = np.column_stack((x.ravel(), y.ravel(), z.ravel()))
    i = np.arange(around)[:, None]
    j = np.arange(tube)[None, :]
    a0 = (i * tube + j).ravel()
    a1 = (((i + 1) % around) * tube + j).ravel()
    a2 = (((i + 1) % around) * tube + (j + 1) % tube).ravel()
    a3 = (i * tube + (j + 1) % tube).ravel()
    faces = np.column_stack((a0, a1, a2, a3))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts.tolist(), [], faces.tolist())
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.materials.append(material)
    return stage.add(name, mesh)


def node(nodes, kind, **inputs):
    made = nodes.new(kind)
    for name, value in inputs.items():
        made.inputs[name.replace("_", " ")].default_value = value
    return made


def glass():
    """Milky orange glass under a clear polished skin. What lights it from outside it scatters back orange; what
    lights it from inside it lets through, diffused. Over both lies the skin's own reflection, as strong as glass
    reflects at that angle, smooth but for faint smudges and a fine ripple from the blowing."""
    material = bpy.data.materials.new("donut-glass")
    material.use_nodes = True
    tree = material.node_tree
    nodes, links = tree.nodes, tree.links
    nodes.remove(nodes["Principled BSDF"])
    out = nodes["Material Output"]
    coord = nodes.new("ShaderNodeTexCoord")
    # Smudges: where hands have held it, the skin's polish is dulled a little.
    smudge = node(nodes, "ShaderNodeTexNoise", Scale=0.35, Detail=6.0, Roughness=0.62)
    links.new(coord.outputs["Object"], smudge.inputs["Vector"])
    patches = nodes.new("ShaderNodeMapRange")
    patches.inputs["From Min"].default_value = 0.52
    patches.inputs["From Max"].default_value = 0.72
    patches.inputs["To Min"].default_value = 0.015
    patches.inputs["To Max"].default_value = 0.16
    links.new(smudge.outputs["Fac"], patches.inputs["Value"])
    # The faint ripple a blown surface keeps, too slight to see but in the reflection.
    ripple = node(nodes, "ShaderNodeTexNoise", Scale=1.6, Detail=2.0)
    links.new(coord.outputs["Object"], ripple.inputs["Vector"])
    bump = node(nodes, "ShaderNodeBump", Strength=1.0, Distance=0.004)
    links.new(ripple.outputs["Fac"], bump.inputs["Height"])
    scatter = node(nodes, "ShaderNodeBsdfDiffuse", Color=(*linear(GLASS), 1), Roughness=0.0)
    # The glow the glass lets through is what reflections of it show. What it throws on matte things round it is
    # the glowing surface inside it (luminaire), so light bounced off them sees no glow in it, or it would count twice.
    through = nodes.new("ShaderNodeBsdfTranslucent")
    path = nodes.new("ShaderNodeLightPath")
    glowing = nodes.new("ShaderNodeMix")
    glowing.data_type = "RGBA"
    # How much glass the light leaving toward the eye crosses, against square on, and what colour that leaves it.
    view = nodes.new("ShaderNodeNewGeometry")
    square = nodes.new("ShaderNodeVectorMath")
    square.operation = "DOT_PRODUCT"
    links.new(view.outputs["Normal"], square.inputs[0])
    links.new(view.outputs["Incoming"], square.inputs[1])
    slant = node(nodes, "ShaderNodeMath")
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
    glowing.inputs["B"].default_value = (0, 0, 0, 1)
    links.new(path.outputs["Is Diffuse Ray"], glowing.inputs["Factor"])
    links.new(glowing.outputs["Result"], through.inputs["Color"])
    outside = node(nodes, "ShaderNodeMixShader", Fac=TRANSLUCENT)
    links.new(scatter.outputs[0], outside.inputs[1])
    links.new(through.outputs[0], outside.inputs[2])
    # Inside the tube the glass is dark: what of the bulbs' light it does not let through it mostly takes in, so
    # the tube does not fill with light bounced round it, and the glass is brightest nearest the bulbs.
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
    passed = node(nodes, "ShaderNodeBsdfTransparent", Color=(*SHADOW, 1))
    surface = nodes.new("ShaderNodeMixShader")
    links.new(shade.outputs["Is Shadow Ray"], surface.inputs[0])
    links.new(layered.outputs[0], surface.inputs[1])
    links.new(passed.outputs[0], surface.inputs[2])
    links.new(surface.outputs[0], out.inputs["Surface"])
    return material


def plastic():
    material = bpy.data.materials.new("donut-base")
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*linear("#ecebe6"), 1)
    shader.inputs["Roughness"].default_value = 0.42
    shader.inputs["Subsurface Weight"].default_value = 0.3
    shader.inputs["Subsurface Radius"].default_value = (0.2, 0.2, 0.2)
    return material


def base(stage):
    """The flat round base the glass rests on, its edge rounded, flat on the desk."""
    wide, tall, round_ = BASE
    bpy.ops.mesh.primitive_cylinder_add(vertices=192, radius=wide / 2, depth=tall, location=(0, 0, tall / 2))
    plinth = bpy.context.active_object
    plinth.name = "donut-base"
    bevel = plinth.modifiers.new("round", "BEVEL")
    bevel.width = round_
    bevel.segments = 6
    plinth.modifiers.new("smooth", "WEIGHTED_NORMAL")
    plinth.data.materials.append(plastic())
    plinth.data.polygons.foreach_set("use_smooth", [True] * len(plinth.data.polygons))
    return plinth


def globe(stage):
    """The bulb in the hole: a frosted globe on the base that glows when the lamp is on, under a mirrored crown."""
    frosted = bpy.data.materials.new("donut-globe")
    frosted.use_nodes = True
    nodes, links = frosted.node_tree.nodes, frosted.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (1, 1, 1, 1)
    shader.inputs["Roughness"].default_value = 0.5
    shader.inputs["Emission Color"].default_value = (*BULB_WHITE, 1)
    power = nodes.new("ShaderNodeValue")
    power.name = "power"
    power.outputs[0].default_value = 0.0
    links.new(power.outputs[0], shader.inputs["Emission Strength"])
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=GLOBE, location=(0, 0, BASE[1] + GLOBE))
    bulb = bpy.context.active_object
    bulb.name = "donut-globe"
    bulb.data.materials.append(frosted)
    bulb.data.polygons.foreach_set("use_smooth", [True] * len(bulb.data.polygons))
    bulb["bulb"] = True
    bulb["share"] = GLOBE_SHARE
    bulb["area"] = 4 * math.pi * GLOBE**2
    mirror = bpy.data.materials.new("donut-crown")
    mirror.use_nodes = True
    chrome = mirror.node_tree.nodes["Principled BSDF"]
    chrome.inputs["Base Color"].default_value = (0.92, 0.92, 0.92, 1)
    chrome.inputs["Metallic"].default_value = 1.0
    chrome.inputs["Roughness"].default_value = 0.05
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=GLOBE * 1.01, location=(0, 0, BASE[1] + GLOBE))
    crown = bpy.context.active_object
    crown.name = "donut-crown"
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for vertex in crown.data.vertices:
        vertex.select = vertex.co.z < -0.3 * GLOBE
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")
    crown.data.materials.append(mirror)
    crown.data.polygons.foreach_set("use_smooth", [True] * len(crown.data.polygons))
    return [bulb, crown]


def bulbs(stage, glass_obj, plinth):
    """The light the bulb in the hole fills the tube with, as it shows on the glass: lights round the ring, in toward
    the hole, alike all round. They light the glass from behind, and the base under it, through the glass, and
    nothing else."""
    only = bpy.data.collections.new("donut-only")
    only.objects.link(glass_obj)
    only.objects.link(plinth)
    lights = []
    for k in range(BULBS):
        turn = 2 * math.pi * (k + 0.5) / BULBS
        reach = RING - INWARD * TUBE[0]
        source = bpy.data.lights.new(f"glow-{k}", "POINT")
        source.color = BULB_WHITE
        source.energy = 0.0
        source.shadow_soft_size = FILL_R
        obj = stage.add(f"glow-{k}", source)
        obj.location = (reach * math.cos(turn), reach * math.sin(turn), LIFT + BULB_HIGH)
        obj.visible_camera = False
        obj.visible_glossy = False
        obj["bulb"] = True
        obj["share"] = GLASS_SHARE / BULBS
        obj.light_linking.receiver_collection = only
        lights.append(obj)
    return lights


def luminaire(stage, glass_obj, plinth):
    """The lamp's light on everything round it, which comes from the whole of the glowing glass: a surface just
    inside the glass, as large, giving out light where the glass glows, all round it and most toward the hole, in
    the colour the glass passes. The glass neither takes its light nor stands in its way, and nothing sees it but the light it gives."""
    clear = bpy.data.collections.new("donut-clear")
    clear.objects.link(glass_obj)
    clear.collection_objects[0].light_linking.link_state = "EXCLUDE"
    material = bpy.data.materials.new("donut-light")
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
    obj = shell(stage, material, "donut-light", inset=0.08)
    mesh = obj.data
    co = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    weight = 1 + INNER * (RING - np.hypot(co[:, 0], co[:, 1])) / TUBE[0]
    # The bulb stands over the base, so the underside of the tube, facing the desk, is in the base's shade and gives
    # little light: the desk at the lamp's foot is dark, as under anything that sits on it.
    facing = (co[:, 2] - LIFT - TUBE[1]) / TUBE[1]
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
    # Nor does it light the base, which shows only at the bottom of the hole, walled in by the glass a hair away:
    # lit by the lamp's whole power from there it would outshine the glass that lights it. It is lit as the glass
    # is, from inside the tube (bulbs).
    unlit = bpy.data.collections.new("donut-unlit")
    for part in (glass_obj, plinth):
        unlit.objects.link(part)
    for linked in unlit.collection_objects:
        linked.light_linking.link_state = "EXCLUDE"
    obj.light_linking.receiver_collection = unlit
    obj.light_linking.blocker_collection = clear
    return obj


def build(stage):
    body = shell(stage, glass())
    plinth = base(stage)
    parts = [body, plinth] + globe(stage) + bulbs(stage, body, plinth) + [luminaire(stage, body, plinth)]
    for part in parts:
        part.location = (part.location.x + W / 2, part.location.y - H / 2, part.location.z)
    stage.shoot("donutlamp", (0, 0, W, H), lens=False)


SHOTS = {"donutlamp": build}
