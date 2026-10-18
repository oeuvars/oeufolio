"""The desk lamp: a mushroom lamp in deep oxblood lacquer, a wide domed shade over a tapering stem.

It is the lamp in the user's photograph, seen on the desk from straight over it. The stem stands on a
rounded foot, swells a little above it and tapers up to a rounded shoulder, where a short neck carries the
shade. The shade is a squashed dome with straight sides and a rounded rim that curls in under it. Both are
lacquered so deep and glossy that they show the room more than their own red: a window off to the left lies
across the shade and runs in long streaks down the stem.

Under the shade, an opal ring gives a soft yellow light down onto the shoulder of the stem and the
desk round the lamp. The shade, opaque, keeps it off the ceiling: from over it, the lamp is its red dome in a ring
of its own light on the desk.

The lamp stands upright on the desk. Built in its own coordinates, in em: standing on z = 0, its axis through the
middle of its box. Its ring is marked "bulb", at no power until desk.py turns it up, its "share" of the lamp's
power spread over its "area"."""

import math

import bpy
import numpy as np

from objects.flutelamp import glowing, node, spline, turned, weigh

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
RING = (2.1, 4.3)
RING_Z = 8.845
UNDER = 8.86
TOP = SHADE[0][1]
# The lacquer: the red under it, how rough the paint is under the clear coat, and the coat's own gloss.
LACQUER = (0.09, 0.003, 0.005)
PAINT_ROUGH = 0.35
COAT_ROUGH = 0.02
# Lacquer flows out nearly flat, but not quite: the faint orange peel a sprayed coat keeps, this deep, this fine,
# and this faint.
PEEL = (0.004, 60.0, 0.04)
# The ring gives soft yellow light, this share of the lamp's power in desk.py. Seen edge on under the shade it is a
# thin line, which a camera exposing for the desk it lights would draw as a smear of glare across the shade: it is
# drawn at this share of its brightness, as the photograph shows it, a bright line and no more.
BULB = (1.0, 0.8, 0.42)
SHARE = 0.35
SEEN = 0.15
OPAL = "#f6efe2"
# The box the lamp stands in, in em.
D = 2 * max(r for r, _ in SHADE)
W = H = D + 2.0

# The photograph's studio, which the lacquer throws back: a tall window, off over the top left of the desk as the
# desk's own window is (desk.py WINDOW_FROM), its reflection lying on the upper left of the dome, and a warm plaster
# wall round the lamp. The page shows the lamp lit as it was photographed, so its picture, lit, is taken in this
# studio (desk.py puts the parts marked "studio" in the lamp's lit portrait alone).
WINDOW_AT = (-30.0, 27.0, 26.0)
WINDOW_SIZE = (26.0, 46.0)
WINDOW_PANES = (3, 4)
WINDOW_BAR = 0.05
WINDOW_LIGHT = (4.5, 4.4, 4.2)
WALL_R = 45.0
WALL_H = 120.0
WALL_LIGHT = (0.75, 0.64, 0.54)
# The wall is lit from the window: brighter on the left, falling off round to the right, where the shade's dark side
# looks.
WALL_FALL = 0.85

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
    """Deep red paint under a thick clear coat, as glossy as glass, with the faint orange peel of a sprayed finish."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*LACQUER, 1)
    shader.inputs["Roughness"].default_value = PAINT_ROUGH
    # The paint shines only through the coat over it.
    shader.inputs["Specular IOR Level"].default_value = 0.0
    shader.inputs["Coat Weight"].default_value = 1.0
    shader.inputs["Coat Roughness"].default_value = COAT_ROUGH
    shader.inputs["Coat IOR"].default_value = 1.5
    coord = nodes.new("ShaderNodeTexCoord")
    peel = node(nodes, "ShaderNodeTexNoise", Scale=PEEL[1], Detail=2.0, Roughness=0.5)
    links.new(coord.outputs["Object"], peel.inputs["Vector"])
    bump = node(nodes, "ShaderNodeBump", Strength=PEEL[2], Distance=PEEL[0])
    links.new(peel.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Coat Normal"])
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


def studio(stage):
    """The photograph's window and wall round the lamp, which light the lacquer and show in it."""
    made = []
    centre = np.array(WINDOW_AT)
    facing = -centre / np.linalg.norm(centre)
    across = np.cross(facing, (0.0, 0.0, 1.0))
    across /= np.linalg.norm(across)
    up = np.cross(across, facing)
    window = bpy.data.meshes.new("mushroom-window")
    w, h = WINDOW_SIZE
    window.from_pydata([tuple(centre + i * w / 2 * across + j * h / 2 * up) for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))], [], [(0, 1, 2, 3)])
    window.uv_layers.new(name="UVMap")
    for loop, uv in zip(window.uv_layers[0].data, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop.uv = uv
    around = np.linspace(0, 2 * math.pi, 128, endpoint=False)
    wall = bpy.data.meshes.new("mushroom-wall")
    wall.from_pydata([(WALL_R * math.cos(a), WALL_R * math.sin(a), z) for a in around for z in (-1.0, WALL_H)], [], [(2 * k, 2 * ((k + 1) % 128), 2 * ((k + 1) % 128) + 1, 2 * k + 1) for k in range(128)])
    lit = wall.attributes.new("lit", "FLOAT", "POINT")
    # Facing the window across the room, the wall is lit full; turned away from it, less.
    towards = np.array([math.cos(a) * -centre[0] + math.sin(a) * -centre[1] for a in around]) / np.hypot(centre[0], centre[1])
    # and up it the light falls off into the dark of the room, so the dome, which throws back the wall round its
    # shoulder and the room's ceiling over its top, shades from one to the other.
    lit.data.foreach_set("value", (np.repeat(1 - WALL_FALL * (1 - towards) / 2, 2) * np.tile((1.0, 0.0), len(around))).astype(np.float32))
    for mesh, light in ((window, WINDOW_LIGHT), (wall, WALL_LIGHT)):
        material = bpy.data.materials.new(mesh.name)
        material.use_nodes = True
        nodes, links = material.node_tree.nodes, material.node_tree.links
        nodes.remove(nodes["Principled BSDF"])
        emit = node(nodes, "ShaderNodeEmission", Color=(*light, 1), Strength=1.0)
        if mesh is window:
            # The glazing bars: a grid of thin dark lines across the light.
            uv = nodes.new("ShaderNodeUVMap")
            grid = nodes.new("ShaderNodeSeparateXYZ")
            links.new(uv.outputs["UV"], grid.inputs[0])
            bars = []
            for axis, panes in zip(("X", "Y"), WINDOW_PANES):
                scaled = nodes.new("ShaderNodeMath")
                scaled.operation = "MULTIPLY"
                scaled.inputs[1].default_value = panes
                links.new(grid.outputs[axis], scaled.inputs[0])
                frac = nodes.new("ShaderNodeMath")
                frac.operation = "PINGPONG"
                frac.inputs[1].default_value = 0.5
                links.new(scaled.outputs[0], frac.inputs[0])
                edge = nodes.new("ShaderNodeMath")
                edge.operation = "GREATER_THAN"
                edge.inputs[1].default_value = WINDOW_BAR * panes / 2
                links.new(frac.outputs[0], edge.inputs[0])
                bars.append(edge)
            both = nodes.new("ShaderNodeMath")
            both.operation = "MULTIPLY"
            links.new(bars[0].outputs[0], both.inputs[0])
            links.new(bars[1].outputs[0], both.inputs[1])
            links.new(both.outputs[0], emit.inputs["Strength"])
        else:
            weight = nodes.new("ShaderNodeAttribute")
            weight.attribute_name = "lit"
            links.new(weight.outputs["Fac"], emit.inputs["Strength"])
        links.new(emit.outputs[0], nodes["Material Output"].inputs["Surface"])
        mesh.materials.append(material)
        obj = stage.add(mesh.name, mesh)
        # The lacquer's red is the paint lit by the photograph's room: the window and the wall light it, as well as
        # showing in it. Nothing else sees them: they are in the lamp's lit portrait alone.
        for flag in ("visible_camera", "visible_shadow", "visible_volume_scatter", "visible_transmission"):
            setattr(obj, flag, False)
        obj["unseen"] = True
        obj["studio"] = True
        made.append(obj)
    return made


def parts(stage):
    """Every part of the lamp, standing on z = 0 about its axis."""
    paint = lacquer("mushroom-lacquer")
    return [stem(stage, paint), shade(stage, paint), ring(stage), *studio(stage)]


def build(stage):
    for part in parts(stage):
        part.location = (part.location.x + W / 2, part.location.y - H / 2, part.location.z)
    stage.shoot("mushroomlamp", (0, 0, W, H), lens=False)


SHOTS = {"mushroomlamp": build}
