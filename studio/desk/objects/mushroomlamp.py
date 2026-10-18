"""The desk lamp: a mushroom lamp in deep oxblood lacquer, a wide domed shade over a tapering stem.

It is the lamp in the user's photograph, seen on the desk from straight over it. The stem stands on a
rounded foot, swells a little above it and tapers up to a rounded shoulder, where a short neck carries the
shade. The shade is a squashed dome with straight sides and a rounded rim that curls in under it. Both are
lacquered deep red under a frosted coat, which gives a soft sheen where the moon through the window over its top left
lights it. Lit or not, the lamp looks the same from over it: its light is under the
shade.

Under the shade, an opal ring gives a soft yellow light down onto the shoulder of the stem and the
desk round the lamp. The shade, opaque, keeps it off the ceiling: from over it, the lamp is its red dome in a ring
of its own light on the desk. A braided cord the red of the lacquer leaves the foot at the back and lies across the
desk to the right, off its edge.

The lamp stands upright on the desk. Built in its own coordinates, in em: standing on z = 0, its axis through the
middle of its box. Its ring is marked "bulb", at no power until desk.py turns it up, its "share" of the lamp's
power spread over its "area"."""

import math

import bpy
import numpy as np

from objects.flutelamp import glowing, node, spline, tube, turned, weigh
from paint import linear

# The stem's outline, radius and height in em, from the middle of its foot round the rounded edge, up the swell and
# the taper to its shoulder, measured off the photograph (595 pixels to 13.5 em). The neck stands up into the shade.
STEM = [
    (0.0, 0.0),
    (1.2, 0.0),
    (1.75, 0.03),
    (2.1, 0.12),
    (2.35, 0.27),
    (2.53, 0.45),
    (2.65, 0.7),
    (2.73, 1.0),
    (2.77, 1.35),
    (2.76, 1.85),
    (2.7, 2.4),
    (2.64, 2.95),
    (2.58, 3.5),
    (2.51, 4.05),
    (2.43, 4.6),
    (2.36, 5.13),
    (2.27, 5.67),
    (2.17, 6.22),
    (2.05, 6.76),
    (1.92, 7.3),
    (1.77, 7.85),
    (1.67, 8.22),
    (1.53, 8.52),
    (1.4, 8.72),
    (1.25, 8.78),
]
NECK = 1.2
# The shade's outline, from the middle of its top out over the dome, down its side and round the rim, and in under
# it, flat, to the neck. The opal ring lies just under that, out toward the rim, so it throws its light out over
# the desk more than down onto the shoulder of the stem right under it.
SHADE = [
    (0.0, 13.5),
    (1.0, 13.47),
    (1.9, 13.4),
    (2.61, 13.3),
    (3.2, 13.16),
    (3.62, 13.0),
    (4.04, 12.75),
    (4.33, 12.48),
    (4.55, 12.21),
    (4.72, 11.94),
    (4.86, 11.66),
    (4.97, 11.36),
    (5.06, 10.98),
    (5.11, 10.55),
    (5.13, 10.1),
    (5.12, 9.65),
    (5.07, 9.32),
    (4.97, 9.08),
    (4.82, 8.93),
    (4.62, 8.85),
    (4.4, 8.83),
]
# The shade is drawn this much larger than the photograph's, about the bottom of its rim, so it holds its own on the
# desk seen from over it.
HEAD = 1.15
RIM = SHADE[-1][1]
SHADE = [(r * HEAD, RIM + (z - RIM) * HEAD) for r, z in SHADE]
RING = (2.1, 4.3 * HEAD)
RING_Z = 8.845
UNDER = 8.86
TOP = SHADE[0][1]
# The finish: the red under it, how rough the paint is, and over it a clear coat etched to a frost, which spreads
# what it throws back into a soft sheen instead of a picture of the room.
LACQUER = (0.09, 0.003, 0.005)
PAINT_ROUGH = 0.5
COAT_ROUGH = 0.4
# An etched frost is not perfectly even: its roughness wanders by this much either way, in patches about this many
# to the em.
FROST = (0.05, 6.0)
# The ring gives soft yellow light, this share of the lamp's power in desk.py. Seen edge on under the shade it is a
# thin line, which a camera exposing for the desk it lights would draw as a smear of glare across the shade: it is
# drawn at this share of its brightness, as the photograph shows it, a bright line and no more.
BULB = (1.0, 0.8, 0.42)
SHARE = 1.0
SEEN = 0.15
OPAL = "#f6efe2"
# The box the lamp stands in, in em.
D = 2 * max(r for r, _ in SHADE)
W = H = D + 2.0

# The cord: braided textile dyed the lacquer's red, this thick (a 6 mm lamp cord on a lamp about 30 cm tall), its
# braid two sets of strands, this many each way round it, crossing one over one under every this many em along it,
# each strand a few yarns side by side. It leaves the foot low at its back, through a notch, and lies through these
# points on the desk, x along to the right and y across, out past the desk's edge.
CORD_R = 0.2
STRANDS = 8
LAY = 0.2
YARNS = 3
BRAID = 0.03
CORD_RED = "#2c0709"
CORD_LIES = [(1.5, 0.0), (3.0, 0.0), (5.5, 0.35), (8.5, 1.1), (11.5, 1.2), (15.0, 0.4), (19.0, -0.6), (24.0, -1.0), (30.0, -0.4), (38.0, 0.3), (46.0, 0.5)]

# The page shows the lamp from a camera of its own (desk.py PORTRAITS), straight over it as far off as the plate's
# camera: the plate's camera, off to one side of it, would draw it leaning away. Its middle, and the point on the
# desk under it.
DISTANCE = 100.0
MIDDLE = (0.0, 0.0, TOP / 2)
STANDS = (0.0, 0.0, 0.0)
BODY = "mushroom-stem"


def photograph():
    """The camera over the lamp: where it stands, looking straight down, and its axes."""
    return np.array(MIDDLE) + np.array([0.0, 0.0, DISTANCE]), np.eye(3), None


def smooth(points):
    """A smooth outline through points, radius and height."""
    path, _ = spline([(r, 0.0, z) for r, z in points], 0.02)
    return [(r, z) for r, _, z in path]


def lacquer(name):
    """Deep red paint under a clear coat etched to a frost: a soft sheen, a little uneven, and no sharp reflection."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*LACQUER, 1)
    shader.inputs["Roughness"].default_value = PAINT_ROUGH
    # The paint shines only through the coat over it.
    shader.inputs["Specular IOR Level"].default_value = 0.0
    shader.inputs["Coat Weight"].default_value = 1.0
    shader.inputs["Coat IOR"].default_value = 1.5
    coord = nodes.new("ShaderNodeTexCoord")
    patches = node(nodes, "ShaderNodeTexNoise", Scale=FROST[1], Detail=3.0, Roughness=0.5)
    links.new(coord.outputs["Object"], patches.inputs["Vector"])
    rough = nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = COAT_ROUGH - FROST[0]
    rough.inputs["To Max"].default_value = COAT_ROUGH + FROST[0]
    links.new(patches.outputs["Fac"], rough.inputs["Value"])
    links.new(rough.outputs[0], shader.inputs["Coat Roughness"])
    return material


def stem(stage, material):
    outline = smooth(STEM) + [(NECK, 8.78), (NECK, UNDER + 0.02), (0.0, UNDER + 0.02)]
    mesh = turned("mushroom-stem", outline, around=384)
    mesh.materials.append(material)
    return stage.add("mushroom-stem", mesh)


def shade(stage, material):
    """The shade as one closed solid: its outside, the rim curled in under it, and its flat underside."""
    outline = smooth(SHADE) + [(0.0, UNDER)]
    mesh = turned("mushroom-shade", outline, around=384)
    mesh.materials.append(material)
    return stage.add("mushroom-shade", mesh)


def ring(stage):
    """The opal ring under the shade round the neck, facing down: it gives the light."""
    mesh = turned("mushroom-ring", [(RING[1], RING_Z), (RING[0], RING_Z)], around=256)
    weigh(mesh, np.ones(len(mesh.vertices)))
    area = math.pi * (RING[1] ** 2 - RING[0] ** 2)
    material = glowing("mushroom-opal", BULB, SHARE, area, diffuse=OPAL)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    emit = next(n for n in nodes if n.type == "EMISSION")
    strength = emit.inputs["Strength"].links[0].from_socket
    path = nodes.new("ShaderNodeLightPath")
    seen = nodes.new("ShaderNodeMapRange")
    seen.inputs["To Min"].default_value = 1.0
    seen.inputs["To Max"].default_value = SEEN
    links.new(path.outputs["Is Camera Ray"], seen.inputs["Value"])
    dimmed = nodes.new("ShaderNodeMath")
    dimmed.operation = "MULTIPLY"
    links.new(strength, dimmed.inputs[0])
    links.new(seen.outputs[0], dimmed.inputs[1])
    links.new(dimmed.outputs[0], emit.inputs["Strength"])
    mesh.materials.append(material)
    obj = stage.add("mushroom-ring", mesh)
    obj["bulb"] = True
    obj["share"] = SHARE
    obj["area"] = area
    return obj


def braid(s, angle):
    """The braid's relief: two sets of strands round the cord, one each way, each passing over one of the other
    and under the next; each strand a few yarns, each a round ridge. Height over the cord's radius, in em."""
    turn = STRANDS * angle / (2 * math.pi)
    a, b = turn + s / LAY, turn - s / LAY
    ua, ub = np.mod(a, 1.0), np.mod(b, 1.0)
    over = (np.floor(a) + np.floor(b)) % 2 == 0
    lift_a = np.sin(math.pi * ub) ** 0.6
    lift_b = np.sin(math.pi * ua) ** 0.6
    top_a = lift_a * (0.75 + 0.25 * np.abs(np.sin(math.pi * YARNS * ua)) ** 0.5)
    top_b = lift_b * (0.75 + 0.25 * np.abs(np.sin(math.pi * YARNS * ub)) ** 0.5)
    return BRAID * (np.where(over, np.maximum(top_a, 0.55 * top_b), np.maximum(top_b, 0.55 * top_a)) - 0.5)


def textile():
    """Dyed braided cotton: matte, with the soft sheen of fibres along the strands, darker in the hollows the braid's
    relief leaves (the mesh's "hollow")."""
    material = bpy.data.materials.new("mushroom-cord")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Roughness"].default_value = 0.65
    shader.inputs["Specular IOR Level"].default_value = 0.2
    shader.inputs["Sheen Weight"].default_value = 0.25
    shader.inputs["Sheen Roughness"].default_value = 0.4
    shader.inputs["Sheen Tint"].default_value = (0.6, 0.35, 0.33, 1)
    hollow = nodes.new("ShaderNodeAttribute")
    hollow.attribute_name = "hollow"
    shade_ = nodes.new("ShaderNodeMix")
    shade_.data_type = "RGBA"
    shade_.inputs["A"].default_value = (*linear(CORD_RED), 1)
    shade_.inputs["B"].default_value = (*[0.35 * c for c in linear(CORD_RED)], 1)
    links.new(hollow.outputs["Fac"], shade_.inputs["Factor"])
    links.new(shade_.outputs["Result"], shader.inputs["Base Color"])
    return material


def cord(stage):
    """The cord, out of the foot and across the desk. It lies on the desk and is drawn in the plate, not in the lamp's
    own picture ("plated"): its picture covers where it leaves the foot, under the shade."""
    path = spline([(x, y, CORD_R + BRAID / 2) for x, y in CORD_LIES], 0.012)
    mesh = tube("mushroom-cord", path, CORD_R, 96, braid)
    angle = np.linspace(0, 2 * math.pi, 96, endpoint=False)
    relief = braid(path[1][:, None], angle[None, :]).ravel() / BRAID + 0.5
    hollow = np.concatenate((np.clip(0.9 - relief, 0, 1) ** 1.5, [0, 0]))
    attribute = mesh.attributes.new("hollow", "FLOAT", "POINT")
    attribute.data.foreach_set("value", hollow.astype(np.float32))
    mesh.materials.append(textile())
    wire = stage.add("mushroom-cord", mesh)
    wire["plated"] = True
    return wire


def parts(stage):
    """Every part of the lamp, standing on z = 0 about its axis."""
    paint = lacquer("mushroom-lacquer")
    return [stem(stage, paint), shade(stage, paint), ring(stage), cord(stage)]


def build(stage):
    for part in parts(stage):
        part.location = (part.location.x + W / 2, part.location.y - H / 2, part.location.z)
    stage.shoot("mushroomlamp", (0, 0, W, H), lens=False)


SHOTS = {"mushroomlamp": build}
