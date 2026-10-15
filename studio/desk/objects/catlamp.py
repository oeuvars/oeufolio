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
W, H = 27.0, 16.5
ORIGIN = (2.6, 5.5)
STEP = 0.09

# The porcelain, and the underglaze colours: the cat's ginger, light and deep, the pink of its nose and the
# insides of its ears, and the brown of the lines of its eyes and mouth.
WHITE = "#f7ecdc"
GINGER = "#d9823a"
DEEP = "#a8521f"
PINK = "#e8a7a0"
LINE = "#2a1d16"
AMBER = "#c98a2a"
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

# The tail rises from the rump and arches up and out over the cat's left side, so the lamp hangs beside it and lights
# its flank and the desk, and the markings on its back are left in sight.
TAIL = ((19.0, 0.0, 7.4), (23.0, -0.8, 13.6), (21.0, -6.0, 19.6), (15.5, -7.6, 17.6))
TAIL_R = (1.55, 1.05)
HEAD = (15.5, -7.6, 17.6)


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


def fur(p, amount, size, seed):
    """Long hair, as the figurine sculpts it: soft clumps raised over the surface."""
    rng = np.random.default_rng(seed)
    out = np.zeros(p.shape[:-1])
    for _ in range(7):
        k = rng.normal(size=3) / size
        out += np.sin(p @ k + rng.uniform(0, 6.3))
    return amount * out / 7


def body(p):
    """The ceramic: the cat, without the lamp's head. It bows, as the figurine does: a big round head low over
    its outstretched forepaws, a plump body, its haunches high. It is the household's cat, long haired: a full
    ruff round its cheeks and neck, big upright ears, and a big plume of a tail."""
    x = p[..., 0]
    head = ellipsoid(p, (4.2, 0, 3.7), (2.9, 3.2, 2.7))
    head = smin(head, mirrored(p, lambda q: ellipsoid(q, (3.6, 1.7, 2.9), (2.0, 1.8, 1.55))), 0.6)
    head = smin(head, ellipsoid(p, (1.5, 0, 2.8), (0.9, 1.25, 0.8)), 0.45)

    def ear(q):
        # A cup: a cone with its front hollowed, big and upright, set at the back corners of the crown.
        outer = cone(q, (4.6, 1.75, 5.1), (5.2, 2.75, 8.7), 1.6, 0.1)
        inner = cone(q, (4.3, 1.75, 5.5), (4.95, 2.72, 8.5), 1.15, 0.04)
        return np.maximum(outer, -inner)

    head = smin(head, mirrored(p, ear), 0.35)
    # The ruff: clumps of long hair round the cheeks, under the chin and down the chest.
    ruff = mirrored(
        p,
        lambda q: np.minimum.reduce(
            [
                ellipsoid(q, (4.7, 3.2, 3.1), (1.4, 1.2, 1.7)),
                ellipsoid(q, (5.5, 3.0, 2.0), (1.4, 1.3, 1.4)),
                ellipsoid(q, (3.8, 2.8, 1.6), (1.3, 1.2, 1.1)),
                ellipsoid(q, (4.5, 1.3, 1.0), (1.5, 1.4, 1.1)),
            ]
        ),
    )
    head = smin(head, ruff, 0.7)
    trunk = cone(p, (6.8, 0, 3.0), (10.0, 0, 4.0), 3.1, 3.4)
    trunk = smin(trunk, cone(p, (10.0, 0, 4.0), (13.0, 0, 5.4), 3.4, 3.3), 1.0)
    trunk = smin(trunk, ellipsoid(p, (16.0, 0, 6.0), (3.7, 3.7, 3.5)), 1.4)
    fore = mirrored(
        p,
        lambda q: smin(cone(q, (7.5, 2.1, 2.3), (0.4, 2.7, 0.75), 1.45, 1.15), ellipsoid(q, (-0.5, 2.8, 0.7), (1.55, 1.3, 0.7)), 0.6),
    )
    hind = mirrored(
        p,
        lambda q: smin(
            smin(ellipsoid(q, (16.4, 2.6, 4.5), (2.7, 1.7, 2.9)), cone(q, (17.3, 2.7, 3.0), (16.8, 2.8, 0.9), 1.3, 1.05), 0.7),
            ellipsoid(q, (16.4, 2.8, 0.65), (1.55, 1.1, 0.65)),
            0.5,
        ),
    )
    points, along = tail_curve()
    tail = tube(p, points, along, 0, along[-1])
    d = smin(trunk, head, 1.3)
    d = smin(d, fore, 0.9)
    d = smin(d, hind, 1.0)
    # Long hair everywhere but the face and the paws, deepest on the tail.
    hairy = soft(x - 3.4, 0, 1.0) * soft(p[..., 2] - 1.2, 0, 0.8)
    d = d - fur(p, 0.2, 1.1, 11) * hairy - 0.08 * hairy
    tail = tail - fur(p, 0.15, 1.2, 12) - 0.25
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
    """Where each colour goes, as the household's cat is marked, from its photographs: how much ginger, pink, dark
    and amber. The colours themselves are laid in the shader."""
    p = verts
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    front = soft(-normals[:, 0] - 0.2, 0, 0.3)
    # The cap: ginger over the crown, the backs and bases of the ears and the back of the head, coming down at
    # the temples to about the eyes.
    # The cap: the whole top and back of the head and the ears, ginger down to a line across the nape; in front it
    # comes down to just above the eyes, and the cheeks, muzzle, chin and ruff are white.
    nape = soft(6.7 - x + wobble(p, 7, 0.15), 0, 0.4)
    brow = soft(z - (4.2 + 0.08 * np.abs(y)) + wobble(p, 1, 0.12), 0, 0.3)
    crown = soft(x - 4.3, 0, 0.9) * soft(z - 2.9 + wobble(p, 8, 0.15), 0, 0.5)
    cap = nape * np.maximum(brow, crown) * soft(np.abs(y) - 0.0 + 3.6, 0, 0.1) * soft(3.4 - np.abs(y), 0, 0.4)
    # The blaze: white up the face from the nose, as wide as between the eyes at the eyes, narrowing to a point
    # a little off the middle at the top of the forehead.
    up = np.clip((z - 3.6) / 2.2, 0, 1)
    blaze_half = 0.75 * (1 - up) ** 1.3
    blaze = soft(blaze_half - np.abs(y - 0.12 * up), 0, 0.22) * soft(3.6 - x + 0.6 * (1 - up), 0, 0.5)
    ginger = cap * (1 - blaze)
    # The moustache: ginger on the cat's left upper lip, a smaller fleck on its right.
    ginger = np.maximum(ginger, front * soft(0.62 - np.linalg.norm((p - (0.85, -0.7, 2.55)) / (0.9, 1.0, 0.75), axis=1) + wobble(p, 3, 0.12), 0, 0.2))
    ginger = np.maximum(ginger, front * soft(0.3 - np.linalg.norm((p - (0.85, 0.55, 2.65)) / (0.9, 1.0, 0.8), axis=1), 0, 0.15))
    # The back, seen from above: four spots in two mirrored pairs either side of the spine. A small pair sits close
    # together just behind the shoulders; a larger pair behind it splays outward like wings, each spot narrowing
    # toward the spine and the head. Long fur feathers their edges.
    top = soft(normals[:, 2] - 0.15, 0, 0.3)
    for (cx, cy, rx, ry, lean), seed in (((8.5, 0.95, 0.95, 0.8, 0.3), 4), ((11.2, 1.85, 1.6, 1.3, 0.55), 5)):
        for side in (1, -1):
            dx, dy = x - cx, y - side * cy
            c, s_ = np.cos(side * lean), np.sin(side * lean)
            u, v = (c * dx + s_ * dy) / rx, (-s_ * dx + c * dy) / ry
            # Narrower at the front and toward the spine: a teardrop.
            u = u * (1 + 0.25 * np.clip(-u, 0, 1))
            spot = soft(1 - np.hypot(u, v) + wobble(p, seed + (side > 0), 0.15, 0.7), 0.1, 0.2)
            ginger = np.maximum(ginger, top * spot)
    # The tail, all of it, from its root.
    points, along = tail_curve(200)
    nearest = np.concatenate([np.argmin(((chunk[:, None, :] - points[None]) ** 2).sum(-1), axis=1) for chunk in np.array_split(p, max(1, len(p) // 20000))])
    tail = (np.linalg.norm(p - points[nearest], axis=1) < 2.2) * soft(along[nearest] - 0.2, 0, 0.9)
    ginger = np.maximum(ginger, tail)
    # The ears: white round their edges and pale pink in the cup.
    ear = soft(z - 5.4, 0, 0.3) * soft(np.abs(y) - 1.0, 0, 0.3) * soft(6.6 - x, 0, 0.3)
    cup = ear * soft(-normals[:, 0] - 0.15, 0, 0.3)
    ginger *= 1 - cup
    pink = 0.85 * cup * soft(0.7 - np.abs(np.abs(y) - (1.85 + 0.3 * (z - 5.2))), 0, 0.3)
    # The nose.
    pink = np.maximum(pink, front * soft(0.34 - np.linalg.norm((p - (0.6, 0, 3.2)) / (1, 1.25, 0.75), axis=1), 0, 0.08))
    # The eyes, open: amber, a dark pupil and a dark rim.
    amber = np.zeros(len(p))
    dark = np.zeros(len(p))
    for side in (1, -1):
        c = np.array([0.0, side * 1.35, 3.95])
        q = (p - c)[:, 1:] / np.array([0.62, 0.47])
        r = np.linalg.norm(q, axis=1)
        eye = front * (x > 0.6) * (x < 2.4) * (np.abs(y) < 2.3)
        amber = np.maximum(amber, eye * soft(1.0 - r, 0, 0.12))
        dark = np.maximum(dark, 0.45 * eye * soft(0.05 - np.abs(r - 1.0), 0, 0.08))
        pupil = np.linalg.norm((p - c)[:, 1:] / np.array([0.17, 0.36]), axis=1)
        dark = np.maximum(dark, eye * soft(1.0 - pupil, 0, 0.2))
    ginger *= 1 - amber
    return np.column_stack((np.clip(ginger, 0, 1), np.clip(pink, 0, 1), np.clip(dark, 0, 1), np.clip(amber, 0, 1)))


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
    colour = mix(nodes, links, marks.outputs["Alpha"], colour, rgb(nodes, AMBER))
    colour = mix(nodes, links, split.outputs["Blue"], colour, rgb(nodes, LINE))
    links.new(colour, shader.inputs["Base Color"])
    # The hair is drawn into the clay in fine strokes under the glaze: they shade the colour, not the glaze.
    coord = nodes.new("ShaderNodeTexCoord")
    along = nodes.new("ShaderNodeMapping")
    along.inputs["Scale"].default_value = (1.2, 14.0, 6.0)
    links.new(coord.outputs["Object"], along.inputs["Vector"])
    strands = nodes.new("ShaderNodeTexNoise")
    strands.inputs["Scale"].default_value = 1.0
    strands.inputs["Detail"].default_value = 6.0
    links.new(along.outputs["Vector"], strands.inputs["Vector"])
    combed = nodes.new("ShaderNodeBump")
    combed.inputs["Strength"].default_value = 0.45
    combed.inputs["Distance"].default_value = 0.05
    links.new(strands.outputs["Fac"], combed.inputs["Height"])
    links.new(combed.outputs["Normal"], shader.inputs["Normal"])
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
    lo, hi = (-2.4, -10.0, -0.2), (25.5, 4.8, 22.6)
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
