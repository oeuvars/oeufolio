"""The desk lamp: a glazed porcelain cat, stretched in a play bow, its tail rising from the rump and arching
forward over its back. From the tail's tip hangs the lamp's head, after an arched floor lamp's: an orange enamelled
dome gilded inside, on a brass neck, with the bulb up inside it, lighting the cat and the desk below.

The cat is the household's own, a Turkish Van: white, with a ginger cap over the head and ears parted by a white
blaze up the forehead, pink inside the ears and on the nose, a ginger patch at one side of the mouth, two ginger
patches on the back and ginger round the root of a ginger tail, airbrushed on under a thick glossy glaze.

The body is one smooth solid, modelled as a signed distance field (sdf.py): the head, cheeks, muzzle and ears, the
chest and back, the legs and paws, and the tail along a curve, blended into each other as a figurine is modelled
in clay, and cut flat underneath where it stands. Where each colour goes is laid on the vertices.

Built in its own coordinates, in em: the head toward -x, the tail toward +x, standing on z = 0. The lamp is the
light marked "bulb", at no power until desk.py turns it up."""

import math

import bmesh
import bpy
import numpy as np

from paint import linear
from sdf import cone, ellipsoid, mesh, smin
from solids import lathe

# The box the cat stands in, in em, and where the cat's own origin lies in it.
W, H = 27.0, 10.0
ORIGIN = (2.6, 5.0)
STEP = 0.09

# The porcelain, and the underglaze colours: the cat's ginger, light and deep, the pink of its nose and the
# insides of its ears, and the brown of the lines of its eyes and mouth.
WHITE = "#f7ecdc"
GINGER = "#e8994a"
DEEP = "#c06a26"
PINK = "#e8a7a0"
LINE = "#5a3b2c"
# The clear glaze where it pools in hollows, with the faint green of glaze run thick.
POOL = "#dfe5dc"
# The lamp: the same warm bulb as the pendant it replaces.
BULB_COLOUR = (1.0, 0.74, 0.46)
BULB_R = 0.8
# The head: where the tail's tip holds it, the brass neck's length, and the dome's radius and thickness.
ENAMEL = "#e5591a"
NECK = 0.9
SHADE_R = 3.0
SHADE_T = 0.1

# The tail rises from the rump and arches forward over the back, its tip over the cat's shoulders.
TAIL = ((19.0, 0.0, 7.4), (23.6, 0.0, 13.6), (20.6, 0.0, 21.6), (14.5, 0.0, 20.0))
TAIL_R = (1.2, 0.9)
HEAD = (14.5, 0.0, 20.0)


def tail_curve(samples=60):
    p0, p1, p2, p3 = (np.asarray(c, dtype=float) for c in TAIL)
    t = np.linspace(0, 1, samples)[:, None]
    points = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t**2 * p2 + t**3 * p3
    along = np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))))
    return points, along


def tube(p, points, along, start, end):
    """The tail between two lengths along it, as a chain of tapering rods."""
    total = along[-1]
    d = np.full(p.shape[:-1], 1e3)
    for i in range(len(points) - 1):
        if along[i + 1] < start or along[i] > end:
            continue
        ra = TAIL_R[0] + (TAIL_R[1] - TAIL_R[0]) * along[i] / total
        rb = TAIL_R[0] + (TAIL_R[1] - TAIL_R[0]) * along[i + 1] / total
        d = np.minimum(d, cone(p, points[i], points[i + 1], ra, rb))
    return d


def mirrored(p, part):
    """A part that the cat has on both sides, given for the left one."""
    flipped = p * np.array([1, -1, 1])
    return np.minimum(part(p), part(flipped))


def body(p):
    """The porcelain: everything but the glass. The cat bows, as the figurine does: a big round head low over
    its outstretched forepaws, a short plump body, its haunches high."""
    head = ellipsoid(p, (4.2, 0, 3.7), (3.0, 3.4, 2.8))
    head = smin(head, mirrored(p, lambda q: ellipsoid(q, (3.6, 1.8, 2.9), (2.1, 1.9, 1.6))), 0.6)
    head = smin(head, ellipsoid(p, (1.5, 0, 2.8), (0.9, 1.3, 0.8)), 0.45)
    ears = mirrored(p, lambda q: cone(q, (4.9, 2.0, 5.6), (5.4, 2.9, 7.9), 1.3, 0.15))
    head = smin(head, ears, 0.4)
    trunk = cone(p, (6.8, 0, 3.0), (10.0, 0, 4.0), 3.0, 3.3)
    trunk = smin(trunk, cone(p, (10.0, 0, 4.0), (13.0, 0, 5.4), 3.3, 3.2), 1.0)
    trunk = smin(trunk, ellipsoid(p, (16.0, 0, 6.0), (3.6, 3.6, 3.4)), 1.4)
    fore = mirrored(
        p,
        lambda q: smin(cone(q, (7.5, 2.1, 2.3), (0.4, 2.7, 0.75), 1.45, 1.15), ellipsoid(q, (-0.5, 2.8, 0.7), (1.55, 1.3, 0.7)), 0.6),
    )
    hind = mirrored(
        p,
        lambda q: smin(
            smin(ellipsoid(q, (16.4, 2.5, 4.5), (2.6, 1.6, 2.8)), cone(q, (17.3, 2.6, 3.0), (16.8, 2.7, 0.9), 1.2, 1.0), 0.7),
            ellipsoid(q, (16.4, 2.7, 0.65), (1.55, 1.1, 0.65)),
            0.5,
        ),
    )
    points, along = tail_curve()
    tail = tube(p, points, along, 0, along[-1])
    d = smin(trunk, head, 1.3)
    d = smin(d, fore, 0.9)
    d = smin(d, hind, 1.0)
    d = smin(d, tail, 0.7)
    # It stands on a flat foot.
    return np.maximum(d, -p[..., 2])


def soft(x, edge, width):
    return np.clip((x - edge) / width + 0.5, 0, 1) ** 2 * (3 - 2 * np.clip((x - edge) / width + 0.5, 0, 1))


def wobble(p, seed, scale=0.6, size=1.8):
    """A slow irregular wander, for the edges of brushed underglaze."""
    rng = np.random.default_rng(seed)
    out = np.zeros(len(p))
    for _ in range(5):
        k = rng.normal(size=3) / size
        out += np.sin(p @ k + rng.uniform(0, 6.3))
    return scale * out / 5


def painted(verts, normals):
    """Where each underglaze goes, as the household's cat is marked: how much ginger, pink and line, and whether
    it is on the tail, for the brushwork. The colours themselves are laid in the shader."""
    p = verts
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    ginger = np.zeros(len(p))
    # The cap: the crown, the back of the head and the ears, down to about the eyes at the sides, and lower
    # toward the back of the head.
    near_head = soft(-np.linalg.norm((p - (4.2, 0, 4.2)) / (3.9, 4.0, 4.6), axis=1) + wobble(p, 7, 0.12), -1.0, 0.18)
    cap = near_head * soft(z - (3.5 + 0.42 * (4.8 - x)) + wobble(p, 1, 0.3), 0, 0.35)
    # The blaze: white up the middle of the face from the nose, narrowing to a point on the crown.
    blaze_half = np.clip(0.95 - 0.27 * (x - 1.2), 0.0, 1.0)
    blaze = soft(blaze_half - np.abs(y + 0.25 * wobble(p, 2, 1.0)), 0, 0.3) * soft(5.6 - x, 0, 0.6)
    ginger = np.maximum(ginger, cap * (1 - blaze))
    # The ginger at the cat's left upper lip.
    ginger = np.maximum(ginger, soft(0.75 - np.linalg.norm((p - (0.75, -0.85, 2.55)) / (0.8, 1.0, 0.7), axis=1) + wobble(p, 3, 0.2), 0, 0.3))
    # On the back, as seen from above: a large patch on the left side behind the shoulders, a smaller one beside
    # it, and ginger on the rump round the root of the tail.
    for centre, radii, seed in (((10.6, 1.9, 6.6), (2.3, 1.7, 1.6), 4), ((13.6, 1.1, 7.6), (1.5, 1.1, 1.2), 5)):
        ginger = np.maximum(ginger, soft(1 - np.linalg.norm((p - centre) / radii, axis=1) + wobble(p, seed, 0.35), 0, 0.7))
    ginger = np.maximum(ginger, soft(1 - np.linalg.norm((p - (18.6, 0, 8.0)) / (2.0, 1.8, 1.6), axis=1) + wobble(p, 6, 0.3), 0, 0.35))
    # The tail, all of it.
    points, along = tail_curve(200)
    nearest = np.concatenate([np.argmin(((chunk[:, None, :] - points[None]) ** 2).sum(-1), axis=1) for chunk in np.array_split(p, max(1, len(p) // 20000))])
    tail = (np.linalg.norm(p - points[nearest], axis=1) < 1.6) * soft(along[nearest] - 0.4, 0, 0.8)
    ginger = np.maximum(ginger, tail)
    # Pink: the nose, and the insides of the ears.
    pink = soft(0.36 - np.linalg.norm((p - (0.6, 0, 3.25)) / (1, 1.3, 0.8), axis=1), 0, 0.1)
    ear = soft(z - 5.8, 0, 0.3) * soft(np.abs(y) - 1.2, 0, 0.3) * soft(7.0 - x, 0, 0.3)
    inside = ear * soft(-normals[:, 0] - 0.3, 0, 0.3) * soft(0.6 - np.abs(np.abs(y) - (2.0 + 0.39 * (z - 5.6))), 0, 0.3)
    pink = np.maximum(pink, inside)
    ginger *= 1 - inside
    # The eyes, shut in a smile, and the line of the mouth.
    line = np.zeros(len(p))
    for side in (1, -1):
        centre = np.array([1.75, side * 1.3, 4.05])
        r = np.linalg.norm((p - centre)[:, 1:], axis=1)
        line = np.maximum(line, soft(0.07 - np.abs(r - 0.5), 0, 0.05) * (p[:, 2] < centre[2]) * (x < 2.8))
    return np.column_stack((np.clip(ginger, 0, 1), np.clip(pink, 0, 1), np.clip(line, 0, 1), tail))


def rgb(nodes, hex_):
    node = nodes.new("ShaderNodeRGB")
    node.outputs[0].default_value = (*linear(hex_), 1)
    return node.outputs[0]


def mix(nodes, links, factor, a, b):
    node = nodes.new("ShaderNodeMix")
    node.data_type = "RGBA"
    links.new(factor, node.inputs["Factor"])
    links.new(a, node.inputs["A"])
    links.new(b, node.inputs["B"])
    return node.outputs["Result"]


def math_node(nodes, links, operation, a, b=None, value=None):
    node = nodes.new("ShaderNodeMath")
    node.operation = operation
    links.new(a, node.inputs[0])
    if b is not None:
        links.new(b, node.inputs[1])
    elif value is not None:
        node.inputs[1].default_value = value
    return node.outputs[0]


def porcelain():
    """Glazed ceramic as the figurine is: a creamy white body under a thick, smooth, very glossy glaze, the ginger
    airbrushed on, deep in the middle of each patch and fading softly into the white at its edge. A little light
    goes into the ceramic and comes out warm."""
    material = bpy.data.materials.new("ceramic")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    marks = nodes.new("ShaderNodeVertexColor")
    marks.layer_name = "paint"
    split = nodes.new("ShaderNodeSeparateColor")
    links.new(marks.outputs["Color"], split.inputs[0])
    ginger = split.outputs["Red"]
    # Airbrushed: the colour builds up toward the middle of a patch, lighter where the spray thinned.
    depth = math_node(nodes, links, "POWER", ginger, value=2.5)
    paint = mix(nodes, links, depth, rgb(nodes, GINGER), rgb(nodes, DEEP))
    colour = mix(nodes, links, math_node(nodes, links, "POWER", ginger, value=0.7), rgb(nodes, WHITE), paint)
    colour = mix(nodes, links, split.outputs["Green"], colour, rgb(nodes, PINK))
    colour = mix(nodes, links, split.outputs["Blue"], colour, rgb(nodes, LINE))
    links.new(colour, shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = 0.4
    shader.inputs["Subsurface Weight"].default_value = 0.25
    shader.inputs["Subsurface Radius"].default_value = (1.0, 0.7, 0.45)
    shader.inputs["Subsurface Scale"].default_value = 0.15
    shader.inputs["Coat Weight"].default_value = 1.0
    shader.inputs["Coat IOR"].default_value = 1.52
    shader.inputs["Coat Roughness"].default_value = 0.04
    return material


def lathed(stage, name, profile, material):
    """A solid turned about the upright through the lamp's head, from (height, radius) pairs."""
    obj = lathe(stage, name, profile, material, steps=96, axis="Z", caps=False)
    obj.data.polygons.foreach_set("use_smooth", [True] * len(obj.data.polygons))
    return obj


def shade(stage):
    """The lamp's head, after the arched floor lamp's: a dome of spun steel enamelled a glossy orange, gilded
    inside, on a short brass neck from the tail's tip, with a frosted bulb up inside it. Its light falls out of
    the open bottom onto the cat and the desk; the dome holds back all that goes up."""
    x, y, tip = HEAD
    rim = tip - NECK - SHADE_R
    orange = bpy.data.materials.new("enamel")
    orange.use_nodes = True
    o = orange.node_tree.nodes["Principled BSDF"]
    o.inputs["Base Color"].default_value = (*linear(ENAMEL), 1)
    o.inputs["Roughness"].default_value = 0.3
    o.inputs["Coat Weight"].default_value = 1.0
    o.inputs["Coat Roughness"].default_value = 0.03
    gold = bpy.data.materials.new("gilt")
    gold.use_nodes = True
    g = gold.node_tree.nodes["Principled BSDF"]
    g.inputs["Base Color"].default_value = (1.0, 0.78, 0.38, 1)
    g.inputs["Metallic"].default_value = 1.0
    g.inputs["Roughness"].default_value = 0.3
    brass = bpy.data.materials.new("brass")
    brass.use_nodes = True
    b = brass.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.86, 0.64, 0.3, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.22
    frosted = bpy.data.materials.new("frosted")
    frosted.use_nodes = True
    f = frosted.node_tree.nodes["Principled BSDF"]
    f.inputs["Base Color"].default_value = (1, 1, 1, 1)
    f.inputs["Transmission Weight"].default_value = 1.0
    f.inputs["Roughness"].default_value = 0.6
    t = SHADE_T
    arc = np.linspace(0, math.pi / 2, 40)
    outer = [(rim + SHADE_R * math.sin(a), SHADE_R * math.cos(a)) for a in arc[::-1]]
    inner = [(rim + (SHADE_R - t) * math.sin(a), (SHADE_R - t) * math.cos(a)) for a in arc]
    parts = [
        # The enamelled dome: its outside down to the rim, and the rim's edge.
        lathed(stage, "shade", [(rim + SHADE_R, 0.0)] + outer[1:] + [(rim, SHADE_R - t)] + [(rim + 0.001, SHADE_R - t)], orange),
        # The gilded inside.
        lathed(stage, "shade-inside", [(rim + 0.001, SHADE_R - t)] + inner[1:-1] + [(rim + SHADE_R - t, 0.0)], gold),
        # The neck: a collar on the dome, a knurled nut and a short stem up into the tail.
        lathed(stage, "neck", [(rim + SHADE_R - 0.05, 0.0), (rim + SHADE_R - 0.05, 0.55), (rim + SHADE_R + 0.15, 0.55), (rim + SHADE_R + 0.2, 0.36), (rim + SHADE_R + 0.45, 0.36), (rim + SHADE_R + 0.5, 0.42), (rim + SHADE_R + 0.7, 0.42), (rim + SHADE_R + 0.75, 0.24), (tip + 0.4, 0.24), (tip + 0.4, 0.0)], brass),
    ]
    bulb = bmesh.new()
    bmesh.ops.create_uvsphere(bulb, u_segments=48, v_segments=24, radius=BULB_R)
    data = bpy.data.meshes.new("bulb")
    bulb.to_mesh(data)
    bulb.free()
    data.polygons.foreach_set("use_smooth", [True] * len(data.polygons))
    data.materials.append(frosted)
    glass = stage.add("bulb-glass", data)
    glass.location = (x, y, rim + 0.25 * SHADE_R)
    # The bulb's own light is the lamp's; its glass lets it out.
    glass.visible_shadow = False
    parts.append(glass)
    source = bpy.data.lights.new("bulb", "POINT")
    source.color = BULB_COLOUR
    source.energy = 0.0
    source.shadow_soft_size = BULB_R * 0.8
    light = stage.add("bulb", source)
    light.location = (x, y, rim + 0.25 * SHADE_R)
    light["bulb"] = True
    parts.append(light)
    for part in parts[:3]:
        part.location = (x, y, 0)
    return parts


def build(stage):
    ox, oy = ORIGIN
    lo, hi = (-2.4, -4.8, -0.2), (25.5, 4.8, 22.6)
    cat, verts = mesh(stage, "cat", body, lo, hi, STEP, porcelain())
    normals = np.zeros_like(verts)
    for e, column in zip(np.eye(3) * 0.01, range(3)):
        normals[:, column] = body(verts + e) - body(verts - e)
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-9)
    layer = cat.data.color_attributes.new("paint", "FLOAT_COLOR", "POINT")
    layer.data.foreach_set("color", painted(verts, normals).ravel())
    for part in [cat] + shade(stage):
        part.location = (part.location.x + ox, part.location.y - oy, part.location.z)
    stage.shoot("catlamp", (0, 0, W, H), lens=False)


SHOTS = {"catlamp": build}
