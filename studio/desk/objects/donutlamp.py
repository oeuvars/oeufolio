"""The desk lamp: a donut of blown orange opal glass, lying flat on the desk on three small white feet, lit from inside.

It is the lamp in the user's Pinterest pin (a glass donut table lamp, glowing orange on a book by a bed) and the
pins beside it: a fat ring whose tube is nearly as thick as the ring is wide, so the hole through the middle is
only a small hole from above, the glass a deep glossy orange when it is off, and when it is on a hot yellow over
the bulb, low in the tube, deepening to orange over the far side.

The glass is a thin shell. Seen from outside it is a clear, polished skin over milky orange glass: a mirror-smooth
reflection, faintly smudged where it is handled, over a surface that scatters what lights it from outside, and lets
through, diffused, what lights it from inside. The bulb inside lights the glass from behind, which is what shows of
it. The lit glass is then the lamp: a surface just inside it gives out its light onto everything round it, most
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
D = 15.0
RING = 0.58 * D / 2
TUBE = (0.42 * D / 2, 0.42 * D / 2)
# It stands on three small white plastic feet under the tube, this tall and this wide.
FOOT = (0.32, 0.75)
LIFT = FOOT[0]
# The box the lamp stands in, in em.
W = H = D + 2.0

# The glass: its orange when the light falls on it from outside, as it does when the lamp is off; how much of the
# light reaching it from inside it lets through, and in what colour, the warm white of the bulb deepened by it.
GLASS = "#f06a0a"
THROUGH = (1.0, 0.3, 0.04)
# How much of what lights the glass it lets through, against what it scatters back, and how much of the
# glass's orange it scatters back inside the tube.
TRANSLUCENT = 0.6
INSIDE = 0.15
# What comes out of the lamp onto the desk: the bulb's warm light as the orange glass passes it. The bulb's own
# warm white, which lights the glass from inside, and how bright it is there against the lamp's light outside.
BULB_COLOUR = (1.0, 0.22, 0.03)
BULB_WHITE = (1.0, 0.7, 0.4)
GLASS_SHARE = 0.15
# The bulb: low in the tube, this high over the glass's foot and this wide, under the side toward the near edge of
# the desk, this many degrees round from the right. Of the light on the glass, this share is the bulb's own; the
# rest it fills the tube with, bounced round it, which this many lights round the ring stand for, each this wide.
# What comes out of the glass lies round the ring as it glows, the far side this much darker than the near one, and
# is, all told, this many times the lamp's power in desk.py.
BULB_HIGH = 1.1
BULB_R = 1.0
BULB_AT = -75
BULB_SHARE = 0.75
BULBS = 12
FILL_R = 0.6
BULB_SIDE = 0.6
POWER = 0.55
# Opal glass is not opaque: what light it lets through it colours, so its shadow is orange and not black.
SHADOW = (0.5, 0.22, 0.05)
# A hand-blown shell is not quite true: it swells and dips this much, in em, over a few hand-widths.
WOBBLE = 0.05


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
    glowing.inputs["A"].default_value = (*THROUGH, 1)
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
    material = bpy.data.materials.new("donut-foot")
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*linear("#ecebe6"), 1)
    shader.inputs["Roughness"].default_value = 0.42
    shader.inputs["Subsurface Weight"].default_value = 0.3
    shader.inputs["Subsurface Radius"].default_value = (0.2, 0.2, 0.2)
    return material


def feet(stage):
    """Three short rounded white feet under the middle of the tube."""
    tall, wide = FOOT
    material = plastic()
    parts = []
    for k in range(3):
        turn = math.radians(90 + 120 * k)
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=wide / 2, depth=tall + 0.2, location=(RING * math.cos(turn), RING * math.sin(turn), (tall + 0.2) / 2))
        foot = bpy.context.active_object
        foot.name = "donut-foot"
        bevel = foot.modifiers.new("round", "BEVEL")
        bevel.width = 0.08
        bevel.segments = 4
        foot.data.materials.append(material)
        foot.data.polygons.foreach_set("use_smooth", [True] * len(foot.data.polygons))
        parts.append(foot)
    return parts


def bulbs(stage, glass_obj):
    """The light inside the tube, as it shows on the glass: one bulb, low in it, under the side toward the near edge
    of the desk, and the light it fills the tube with, round all of it. These light the glass from behind and
    nothing else."""
    only = bpy.data.collections.new("donut-only")
    only.objects.link(glass_obj)
    lights = []

    def light(k, turn, share, size):
        source = bpy.data.lights.new(f"glow-{k}", "POINT")
        source.color = BULB_WHITE
        source.energy = 0.0
        source.shadow_soft_size = size
        obj = stage.add(f"glow-{k}", source)
        obj.location = (RING * math.cos(turn), RING * math.sin(turn), LIFT + BULB_HIGH)
        obj.visible_camera = False
        obj.visible_glossy = False
        obj["bulb"] = True
        obj["share"] = share
        obj.light_linking.receiver_collection = only
        lights.append(obj)

    light("bulb", math.radians(BULB_AT), GLASS_SHARE * BULB_SHARE, BULB_R)
    for k in range(BULBS):
        light(k, 2 * math.pi * (k + 0.5) / BULBS, GLASS_SHARE * (1 - BULB_SHARE) / BULBS, FILL_R)
    return lights


def luminaire(stage, glass_obj):
    """The lamp's light on everything round it, which comes from the whole of the glowing glass: a surface just
    inside the glass, as large, giving out light where the glass glows, most over the bulb, in the colour the glass
    passes. The glass neither takes its light nor stands in its way, and nothing sees it but the light it gives."""
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
    turn = np.arctan2(co[:, 1], co[:, 0])
    weight = 1 - BULB_SIDE + BULB_SIDE * (1 + np.cos(turn - math.radians(BULB_AT))) / 2
    weight /= weight.mean()
    attribute = mesh.attributes.new("glow", "FLOAT", "POINT")
    attribute.data.foreach_set("value", weight.astype(np.float32))
    area = sum(polygon.area for polygon in mesh.polygons)
    for flag in ("visible_camera", "visible_glossy", "visible_transmission", "visible_shadow", "visible_volume_scatter"):
        setattr(obj, flag, False)
    obj["bulb"] = True
    obj["share"] = POWER
    obj["area"] = area
    obj.light_linking.receiver_collection = clear
    obj.light_linking.blocker_collection = clear
    return obj


def build(stage):
    body = shell(stage, glass())
    parts = [body] + feet(stage) + bulbs(stage, body) + [luminaire(stage, body)]
    for part in parts:
        part.location = (part.location.x + W / 2, part.location.y - H / 2, part.location.z)
    stage.shoot("donutlamp", (0, 0, W, H), lens=False)


SHOTS = {"donutlamp": build}
