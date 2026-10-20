"""The user's coffee mug, full: a straight stoneware cylinder in a dark reactive glaze, with a square strap handle,
from their photographs of it (art/mug-*.jpg), and coffee in it from their photograph of a cup of coffee
(art/coffee-photo.jpg, unwarped by art/coffeephoto.py).

The glaze is a slate blue black, glossy, salted with fine grains lighter and darker than it where it ran thin, on the
handle and the rim, and clear and darker in the well where it pooled. It gathers darker along the handle's edges and
breaks to a thin amber line round the shoulders of the lip. The body stands on a narrow foot, a step in from its
side. The handle is a flat strap bent to a rounded square loop, set just under the rim and reaching half the way
down; its outer side leans in a little toward its foot.

The coffee stands a little under the rim, crema marbled with milk and ringed with bubbles at the wall, which it climbs
in a thin meniscus. The bulb catches on it as a sharp highlight; the crema itself is matt.

The page shows it from straight over it (desk.py PORTRAITS), as the user photographed it. Built in its own
coordinates, in em: standing on z = 0, its axis through the middle of its box, the handle out along x."""

import math
import os

import bmesh
import bpy
import numpy as np

from objects.flutelamp import node, turned
from paint import linear

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art")

# The body, in em, as built; the desk draws it at 0.85 of this (its k in desk.PROPS). Its height, the wall's
# thickness, the floor's, and the foot's step, are the photographs' proportions of its width.
D = 11.0
R = D / 2
TALL = 0.85 * D
WALL = 0.05 * D
FLOOR = 0.07 * D
FOOT = (0.2, 0.06 * D)
# The handle: a strap this thick and wide, its loop reaching this far out from the side and this far down from just
# under the rim, its outer side leaning in by LEAN at its foot, its corners rounded inside and out.
STRAP = (0.068 * D, 0.18 * D)
REACH = 0.3 * D
DROP = 0.5 * TALL
UNDER = 0.035 * D
LEAN = 0.02 * D
BEND = 0.06 * D
# The coffee stands this far under the rim and climbs the wall by MENISCUS over the last SPREAD of its radius.
LEVEL = TALL - 0.11 * D
MENISCUS = (0.012 * D, 0.03 * D)

# The glaze, measured off the overhead photograph against the white card it stands on, then lightened so it reads
# under the desk's dim light: a slate blue black, salted with fine grains lighter and darker than it, every GRAIN em
# or so; greener and darker in the well, where it pooled; darker again along the handle's edges, where it gathered;
# and a thin amber line round the shoulders of the lip, where it ran thin.
GLAZE = "#343c43"
POOL = "#1f2521"
SALT = "#62717d"
PEPPER = "#131619"
GATHERED = "#1e1a17"
AMBER = "#6a3414"
GRAIN = 0.045
GLOSS = 0.07
# The crema is matt; the coffee under it barely shines.
CREMA_ROUGH = 0.32

W = H = D + 2 * REACH + 2.0
DISTANCE = 100.0
MIDDLE = (0.0, 0.0, TALL / 2)
STANDS = (0.0, 0.0, 0.0)
BODY = "mug-body"
# Its camera keeps to the page's axes, not the mug's, so the handle points where desk.json turns it.
SQUARE = True


def photograph():
    """The camera over the mug: where it stands, looking straight down, and its axes."""
    return np.array(MIDDLE) + np.array([0.0, 0.0, DISTANCE]), np.eye(3), None


def arc(cx, cz, radius, start, end, steps=12):
    return [(cx + radius * math.cos(a), cz + radius * math.sin(a)) for a in np.linspace(math.radians(start), math.radians(end), steps)]


def profile():
    """The body's section, radius and height, from the middle of its foot out and up its side, over the rim, down
    the inside and across the floor of the well to the axis."""
    step, foot = FOOT
    inner = R - WALL
    lip = WALL / 2
    outline = [(0.0, 0.0)]
    outline += arc(R - step - 0.25, 0.25, 0.25, -90, 0, 8)
    outline += [(R - step, foot - 0.12)]
    outline += arc(R - step + 0.12, foot - 0.12, 0.12, 180, 90, 6)
    outline += arc(R - 0.08, foot + 0.04, 0.08, -90, 0, 6)
    outline += [(R, TALL * t) for t in np.linspace((foot + 0.12) / TALL, (TALL - lip) / TALL, 24)]
    outline += arc(R - lip, TALL - lip, lip, 0, 180, 24)
    outline += [(inner, TALL * t) for t in np.linspace((TALL - lip) / TALL, (FLOOR + 1.0) / TALL, 24)][1:]
    outline += arc(inner - 1.0, FLOOR + 1.0, 1.0, 0, -90, 14)
    outline += [(0.0, FLOOR)]
    return outline


def glaze(name, gathers=False):
    """The reactive glaze: slate blue black salted with fine light and dark grains, pooled darker in the well, glossy,
    with an amber line round the lip's shoulders. On the handle (gathers) it lies darker along the edges, where the
    mesh is sharpest."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    coord = nodes.new("ShaderNodeTexCoord")
    geometry = nodes.new("ShaderNodeNewGeometry")

    def mix(factor, a, b):
        made = nodes.new("ShaderNodeMix")
        made.data_type = "RGBA"
        links.new(factor, made.inputs[0])
        for socket, value in ((6, a), (7, b)):
            if isinstance(value, str):
                made.inputs[socket].default_value = (*linear(value), 1)
            else:
                links.new(value, made.inputs[socket])
        return made.outputs[2]

    def band(value, lo, hi):
        made = nodes.new("ShaderNodeMapRange")
        made.interpolation_type = "SMOOTHSTEP"
        made.inputs["From Min"].default_value = lo
        made.inputs["From Max"].default_value = hi
        links.new(value, made.inputs["Value"])
        return made.outputs[0]

    def times(a, b):
        made = nodes.new("ShaderNodeMath")
        made.operation = "MULTIPLY"
        links.new(a, made.inputs[0])
        if isinstance(b, float):
            made.inputs[1].default_value = b
        else:
            links.new(b, made.inputs[1])
        return made.outputs[0]

    split = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coord.outputs["Object"], split.inputs[0])
    deep = band(split.outputs["Z"], FLOOR + 0.5, TALL * 0.7)
    colour = mix(deep, POOL, GLAZE)
    # The grains: each a cell of its own, some lighter and some darker than the glaze, more of the light where the
    # glaze ran thin, in broad drifts.
    cells = nodes.new("ShaderNodeTexVoronoi")
    cells.inputs["Scale"].default_value = 1 / GRAIN
    cells.inputs["Randomness"].default_value = 1.0
    links.new(coord.outputs["Object"], cells.inputs["Vector"])
    luck = nodes.new("ShaderNodeSeparateColor")
    links.new(cells.outputs["Color"], luck.inputs[0])
    drift = node(nodes, "ShaderNodeTexNoise", Scale=0.9, Detail=6.0, Roughness=0.6)
    links.new(coord.outputs["Object"], drift.inputs["Vector"])
    thin = band(drift.outputs["Fac"], 0.35, 0.65)
    salt = nodes.new("ShaderNodeMath")
    salt.operation = "MULTIPLY_ADD"
    links.new(thin, salt.inputs[0])
    salt.inputs[1].default_value = -0.12
    salt.inputs[2].default_value = 0.94
    light = nodes.new("ShaderNodeMath")
    light.operation = "GREATER_THAN"
    links.new(luck.outputs[0], light.inputs[0])
    links.new(salt.outputs[0], light.inputs[1])
    dark = band(luck.outputs[1], 0.2, 0.12)
    # The well, where the glaze lies thick, is all but clear of them.
    clear = band(split.outputs["Z"], TALL * 0.55, TALL * 0.85)
    colour = mix(times(times(light.outputs[0], band(luck.outputs[2], -0.5, 1.0)), times(clear, 0.6)), colour, SALT)
    colour = mix(times(dark, 0.5), colour, PEPPER)
    if gathers:
        colour = mix(times(band(geometry.outputs["Pointiness"], 0.52, 0.58), 0.85), colour, GATHERED)
    # The amber line round the lip, on its shoulders: up near the rim, where the surface faces half up.
    up = nodes.new("ShaderNodeSeparateXYZ")
    links.new(geometry.outputs["Normal"], up.inputs[0])
    shoulder = nodes.new("ShaderNodeMath")
    shoulder.operation = "MULTIPLY"
    links.new(band(up.outputs["Z"], 0.25, 0.45), shoulder.inputs[0])
    links.new(band(up.outputs["Z"], 0.85, 0.65), shoulder.inputs[1])
    lip = times(shoulder.outputs[0], band(split.outputs["Z"], TALL - WALL * 0.6, TALL - WALL * 0.4))
    links.new(mix(lip, colour, AMBER), shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = GLOSS
    shader.inputs["IOR"].default_value = 1.52
    # The glaze flowed as it fired: a faint orange peel over the whole of it.
    peel = node(nodes, "ShaderNodeTexNoise", Scale=1.6, Detail=3.0, Roughness=0.5)
    links.new(coord.outputs["Object"], peel.inputs["Vector"])
    bump = node(nodes, "ShaderNodeBump", Strength=0.08, Distance=0.05)
    links.new(peel.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return material


def body(stage, material):
    mesh = turned(BODY, profile(), around=384)
    mesh.materials.append(material)
    return stage.add(BODY, mesh)


def loop():
    """The handle's centre line, in the plane through the axis, x out from the axis and z up: in through the wall at
    the top, out, round the top corner, down the outer side, round the foot corner and back in through the wall."""
    half = STRAP[0] / 2
    top = TALL - UNDER - half
    foot = TALL - UNDER - DROP + half
    out = R + REACH - half
    root = R - WALL * 0.6
    bend = BEND + half
    points = [(root, top), (out - bend, top)]
    points += arc(out - bend, top - bend, bend, 90, 0, 16)
    points += arc(out - LEAN - bend, foot + bend, bend, 0, -90, 16)
    points += [(root, foot)]
    path = np.array(points)
    # Even steps along it, close enough for the round corners.
    along = np.concatenate(([0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))))
    s = np.arange(0, along[-1], 0.04)
    return np.column_stack((np.interp(s, along, path[:, 0]), np.interp(s, along, path[:, 1])))


def handle(stage, material):
    """The strap: a rounded oblong section, thick in the plane of the loop and wide across it, swept along the
    loop and capped where it goes into the wall."""
    path = loop()
    ahead = np.gradient(path, axis=0)
    ahead /= np.linalg.norm(ahead, axis=1)[:, None]
    # Out of the loop, toward its inside, in the plane: the tangent turned a quarter.
    inward = np.column_stack((ahead[:, 1], -ahead[:, 0]))
    a, b = STRAP[0] / 2, STRAP[1] / 2
    around = 64
    t = np.linspace(0, 2 * math.pi, around, endpoint=False)
    power = 2 / 3
    u = a * np.sign(np.cos(t)) * np.abs(np.cos(t)) ** power
    v = b * np.sign(np.sin(t)) * np.abs(np.sin(t)) ** power
    rings = np.zeros((len(path), around, 3))
    rings[..., 0] = path[:, None, 0] + inward[:, None, 0] * u[None, :]
    rings[..., 2] = path[:, None, 1] + inward[:, None, 1] * u[None, :]
    rings[..., 1] = v[None, :]
    count = len(path)
    verts = np.vstack((rings.reshape(-1, 3), [path[0][0], 0, path[0][1]], [path[-1][0], 0, path[-1][1]]))
    i = np.arange(count - 1)[:, None]
    j = np.arange(around)[None, :]
    faces = np.column_stack(((i * around + j).ravel(), ((i + 1) * around + j).ravel(), ((i + 1) * around + (j + 1) % around).ravel(), (i * around + (j + 1) % around).ravel())).tolist()
    first, last = count * around, count * around + 1
    faces += [(first, (k + 1) % around, k) for k in range(around)]
    faces += [(last, (count - 1) * around + k, (count - 1) * around + (k + 1) % around) for k in range(around)]
    mesh = bpy.data.meshes.new("mug-handle")
    mesh.from_pydata(verts.tolist(), [], faces)
    mesh.validate()
    made = bmesh.new()
    made.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(made, faces=made.faces)
    made.to_mesh(mesh)
    made.free()
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.materials.append(material)
    return stage.add("mug-handle", mesh)


def crema(name):
    """The coffee's surface: the photograph of it, laid flat across the well, matt but for a faint wet sheen, the
    bubbles a little sunk into it."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    coord = nodes.new("ShaderNodeTexCoord")
    place = nodes.new("ShaderNodeMapping")
    reach = R - WALL
    place.inputs["Location"].default_value = (0.5, 0.5, 0)
    place.inputs["Scale"].default_value = (1 / (2 * reach), -1 / (2 * reach), 1)
    links.new(coord.outputs["Object"], place.inputs["Vector"])
    photo = nodes.new("ShaderNodeTexImage")
    photo.image = bpy.data.images.load(os.path.join(ART, "coffee-surface.png"))
    photo.extension = "EXTEND"
    photo.interpolation = "Cubic"
    links.new(place.outputs["Vector"], photo.inputs["Vector"])
    links.new(photo.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = CREMA_ROUGH
    shader.inputs["IOR"].default_value = 1.34
    # The bubbles are its darkest spots: the dark sinks.
    bump = node(nodes, "ShaderNodeBump", Strength=0.25, Distance=0.04)
    links.new(photo.outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return material


def coffee(stage):
    """The surface of the coffee, flat across the well and climbing the wall at its edge, a little into it so no
    gap shows."""
    reach = R - WALL
    rise, spread = MENISCUS
    outline = [(0.0, LEVEL)]
    outline += [(r, LEVEL + rise * max(1 - (reach - r) / spread, 0) ** 2.5) for r in np.linspace(reach - spread, reach + 0.03, 10)]
    mesh = turned("mug-coffee", outline, around=256)
    # An open surface has no inside to face away from: turn it up, to the camera.
    if sum(face.normal.z for face in mesh.polygons) < 0:
        mesh.flip_normals()
    mesh.materials.append(crema("mug-crema"))
    return stage.add("mug-coffee", mesh)


def parts(stage):
    return [body(stage, glaze("mug-glaze")), handle(stage, glaze("mug-handle-glaze", gathers=True)), coffee(stage)]


def build(stage):
    for part in parts(stage):
        part.location = (part.location.x + W / 2, part.location.y - H / 2, part.location.z)
    stage.shoot("mug", (0, 0, W, H), lens=False)


SHOTS = {"mug": build}
