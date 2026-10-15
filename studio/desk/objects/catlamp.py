"""The desk lamp: a glazed porcelain cat, stretched in a play bow, its tail curled up and over its back. The end
of the tail is not porcelain but opal glass, rounded off, with the lamp inside it: switched on, the tail's tip
glows and lights the desk, and switched off it is milky white glass.

The cat is the household's own, a Turkish Van: white, with an orange cap over the head and ears parted by a
white blaze up the forehead, pink inside the ears and on the nose, a ginger patch at one side of the mouth,
two ginger patches on the back and ginger round the root of a ginger tail, brushed on in underglaze under a
thick clear glaze.

The body is one smooth solid, modelled as a signed distance field: the head, cheeks, muzzle and ears, the chest
and back, the legs and paws, and the tail along a curve, blended into each other as a figurine is modelled in
clay, and cut flat underneath where it stands. The field is turned into a mesh by surface nets, its vertices
drawn onto the surface itself, and where each colour goes is laid on the vertices.

Built in its own coordinates, in em: the head toward -x, the tail toward +x, standing on z = 0. The lamp is
the lights marked "bulb" inside the glass, at no power until desk.py turns them up."""

import math

import bmesh
import bpy
import numpy as np

from paint import linear

# The box the cat stands in, in em, and where the cat's own origin lies in it. The tail curls up and out to the
# cat's left, so from overhead the lit tip hangs clear beside the rump.
W, H = 26.0, 15.0
ORIGIN = (2.6, 9.6)
STEP = 0.09

# The porcelain, and the underglaze colours: the cat's ginger, light and deep, the pink of its nose and the
# insides of its ears, and the brown of the lines of its eyes and mouth.
WHITE = "#f6f1e9"
GINGER = "#e09048"
DEEP = "#b8622a"
PINK = "#e8a7a0"
LINE = "#5a3b2c"
# The clear glaze where it pools in hollows, with the faint green of glaze run thick.
POOL = "#dfe5dc"
# The lamp: the same warm bulb as the pendant it replaces, and where along the glass its filaments lie.
BULB_COLOUR = (1.0, 0.74, 0.46)
BULBS = (0.3, 0.55, 0.8)

# The tail runs along this curve from the rump. Its last GLASS em are the lamp.
TAIL = ((19.0, 0.0, 7.4), (22.4, 0.6, 11.4), (22.4, 5.4, 14.2), (18.8, 7.2, 13.4))
TAIL_R = (1.2, 0.95)
GLASS = 2.7


def ellipsoid(p, centre, radii):
    q = (p - np.asarray(centre)) / np.asarray(radii)
    k0 = np.linalg.norm(q, axis=-1)
    k1 = np.linalg.norm(q / np.asarray(radii), axis=-1)
    return k0 * (k0 - 1) / np.maximum(k1, 1e-9)


def cone(p, a, b, ra, rb):
    """A rod from a to b whose radius runs from ra to rb, rounded at both ends."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(p - a - t[..., None] * ab, axis=-1) - (ra + (rb - ra) * t)


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


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
    tail = tube(p, points, along, 0, along[-1] - GLASS + 0.2)
    d = smin(trunk, head, 1.3)
    d = smin(d, fore, 0.9)
    d = smin(d, hind, 1.0)
    d = smin(d, tail, 0.7)
    # It stands on a flat foot.
    return np.maximum(d, -p[..., 2])


def glass(p):
    points, along = tail_curve()
    # A hair fuller than the porcelain, so it seats over the end of it.
    return tube(p, points, along, along[-1] - GLASS, along[-1]) - 0.04


def nets(field, lo, hi, step):
    """Surface nets: a vertex in every cell the surface passes through, drawn onto the surface, and a quad
    across every edge of the grid the surface cuts."""
    axes = [np.arange(a, b + step, step) for a, b in zip(lo, hi)]
    X, Y, Z = np.meshgrid(*axes, indexing="ij")
    grid = np.stack((X, Y, Z), axis=-1).reshape(-1, 3).astype(np.float32)
    values = np.concatenate([field(chunk) for chunk in np.array_split(grid, max(1, len(grid) // 2_000_000))]).reshape(X.shape)
    del grid
    inside = values < 0
    corners = [inside[i : inside.shape[0] - 1 + i, j : inside.shape[1] - 1 + j, k : inside.shape[2] - 1 + k] for i in (0, 1) for j in (0, 1) for k in (0, 1)]
    some = np.logical_or.reduce(corners)
    every = np.logical_and.reduce(corners)
    active = some & ~every
    index = np.full(active.shape, -1, dtype=np.int64)
    cells = np.argwhere(active)
    index[active] = np.arange(len(cells))
    origin = np.asarray(lo, dtype=float)
    verts = origin + (cells + 0.5) * step
    # Newton's method, kept inside each vertex's cell.
    for _ in range(4):
        f = field(verts)
        grad = np.stack([(field(verts + e) - field(verts - e)) / (2 * 0.01) for e in np.eye(3) * 0.01], axis=-1)
        verts = verts - (f / np.maximum((grad**2).sum(-1), 1e-9))[:, None] * grad
        verts = np.clip(verts, origin + cells * step, origin + (cells + 1) * step)
    quads = []
    nx, ny, nz = inside.shape
    # Edges along x, y and z, and the four cells round each, in turn.
    for axis, around in (
        (0, ((0, -1, -1), (0, 0, -1), (0, 0, 0), (0, -1, 0))),
        (1, ((-1, 0, -1), (-1, 0, 0), (0, 0, 0), (0, 0, -1))),
        (2, ((-1, -1, 0), (0, -1, 0), (0, 0, 0), (-1, 0, 0))),
    ):
        step_ = np.eye(3, dtype=int)[axis]
        a = inside[: nx - step_[0], : ny - step_[1], : nz - step_[2]]
        b = inside[step_[0] :, step_[1] :, step_[2] :]
        cut = np.argwhere(a != b)
        keep = np.all(cut >= 1, axis=1) & (cut[:, 0] < nx - 1) & (cut[:, 1] < ny - 1) & (cut[:, 2] < nz - 1)
        cut = cut[keep]
        flip = a[tuple(cut.T)]
        corners_ = np.stack([index[tuple((cut + np.asarray(o)).T)] for o in around], axis=1)
        corners_[flip] = corners_[flip][:, ::-1]
        quads.append(corners_[np.all(corners_ >= 0, axis=1)])
    return verts, np.concatenate(quads)


def mesh(stage, name, field, lo, hi, step, material):
    verts, quads = nets(field, lo, hi, step)
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts.tolist(), [], quads.tolist())
    data.validate()
    bm = bmesh.new()
    bm.from_mesh(data)
    # Surface nets leave a faint grain of the grid in the surface; a fired glaze has none.
    for _ in range(4):
        bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(data)
    bm.free()
    data.polygons.foreach_set("use_smooth", [True] * len(data.polygons))
    data.materials.append(material)
    return stage.add(name, data), verts


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
    """Hard-paste porcelain painted in underglaze under a thick clear glaze, as such figurines are made.

    The ginger is brushwork: laid in strokes that run with the fur, lighter and deeper where the brush was
    loaded, and its edges break into the white as a dry brush leaves them. The glaze over it runs thick in the
    hollows, where the ginger looks deeper and the white takes the faint green of thick glaze, and thin over
    the crests. The glaze is glass: very glossy, with the slow ripple of a fired glaze and the odd pinhole. The
    porcelain under it lets a little light in."""
    material = bpy.data.materials.new("porcelain")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    marks = nodes.new("ShaderNodeVertexColor")
    marks.layer_name = "paint"
    split = nodes.new("ShaderNodeSeparateColor")
    links.new(marks.outputs["Color"], split.inputs[0])
    tail = marks.outputs["Alpha"]
    coord = nodes.new("ShaderNodeTexCoord")
    # Strokes running with the fur: along the body, finer and every way on the tail.
    along = nodes.new("ShaderNodeMapping")
    along.inputs["Scale"].default_value = (0.7, 7.0, 7.0)
    links.new(coord.outputs["Object"], along.inputs["Vector"])
    strokes = nodes.new("ShaderNodeTexNoise")
    strokes.inputs["Scale"].default_value = 1.2
    strokes.inputs["Detail"].default_value = 6.0
    strokes.inputs["Roughness"].default_value = 0.6
    links.new(along.outputs["Vector"], strokes.inputs["Vector"])
    tail_strokes = nodes.new("ShaderNodeTexNoise")
    tail_strokes.inputs["Scale"].default_value = 3.0
    tail_strokes.inputs["Detail"].default_value = 6.0
    links.new(coord.outputs["Object"], tail_strokes.inputs["Vector"])
    brush = mix(nodes, links, tail, strokes.outputs["Fac"], tail_strokes.outputs["Fac"])
    brush_value = nodes.new("ShaderNodeRGBToBW")
    links.new(brush, brush_value.inputs[0])
    brush = brush_value.outputs[0]
    # The edge of each colour is feathered with fine strokes running with the fur, as the painter flicked the
    # brush outward to paint fur, so ginger and white comb into each other.
    fine_along = nodes.new("ShaderNodeMapping")
    fine_along.inputs["Scale"].default_value = (1.5, 26.0, 26.0)
    links.new(coord.outputs["Object"], fine_along.inputs["Vector"])
    fine = nodes.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 1.0
    fine.inputs["Detail"].default_value = 4.0
    links.new(fine_along.outputs["Vector"], fine.inputs["Vector"])
    combed = math_node(nodes, links, "ADD", math_node(nodes, links, "MULTIPLY", brush, value=0.5), math_node(nodes, links, "MULTIPLY", fine.outputs["Fac"], value=0.5))

    def broken(mask, width):
        shifted = math_node(nodes, links, "ADD", mask, math_node(nodes, links, "MULTIPLY", math_node(nodes, links, "SUBTRACT", combed, value=0.5), value=width))
        ramp = nodes.new("ShaderNodeMapRange")
        ramp.interpolation_type = "SMOOTHSTEP"
        ramp.inputs["From Min"].default_value = 0.3
        ramp.inputs["From Max"].default_value = 0.7
        links.new(shifted, ramp.inputs["Value"])
        return ramp.outputs[0]

    ginger = broken(split.outputs["Red"], 1.4)
    pink = broken(split.outputs["Green"], 0.4)
    line = split.outputs["Blue"]
    # Hollows, where the glaze pools.
    hollow = nodes.new("ShaderNodeAmbientOcclusion")
    hollow.inputs["Distance"].default_value = 0.8
    hollow.only_local = True
    pooled = nodes.new("ShaderNodeMapRange")
    pooled.inputs["From Min"].default_value = 1.0
    pooled.inputs["From Max"].default_value = 0.55
    links.new(hollow.outputs["AO"], pooled.inputs["Value"])
    loaded = nodes.new("ShaderNodeMapRange")
    loaded.inputs["From Min"].default_value = 0.3
    loaded.inputs["From Max"].default_value = 0.75
    links.new(brush, loaded.inputs["Value"])
    deep = math_node(nodes, links, "MAXIMUM", loaded.outputs[0], pooled.outputs[0])
    paint = mix(nodes, links, deep, rgb(nodes, GINGER), rgb(nodes, DEEP))
    white = mix(nodes, links, math_node(nodes, links, "MULTIPLY", pooled.outputs[0], value=0.8), rgb(nodes, WHITE), rgb(nodes, POOL))
    colour = mix(nodes, links, ginger, white, paint)
    colour = mix(nodes, links, pink, colour, rgb(nodes, PINK))
    colour = mix(nodes, links, line, colour, rgb(nodes, LINE))
    links.new(colour, shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = 0.5
    shader.inputs["Subsurface Weight"].default_value = 0.15
    shader.inputs["Subsurface Radius"].default_value = (1.0, 0.85, 0.7)
    shader.inputs["Subsurface Scale"].default_value = 0.1
    # The glaze.
    shader.inputs["Coat Weight"].default_value = 1.0
    shader.inputs["Coat IOR"].default_value = 1.52
    shader.inputs["Coat Roughness"].default_value = 0.02
    ripple = nodes.new("ShaderNodeTexNoise")
    ripple.inputs["Scale"].default_value = 0.35
    ripple.inputs["Detail"].default_value = 3.0
    links.new(coord.outputs["Object"], ripple.inputs["Vector"])
    pins = nodes.new("ShaderNodeTexVoronoi")
    pins.inputs["Scale"].default_value = 4.0
    links.new(coord.outputs["Object"], pins.inputs["Vector"])
    pinhole = nodes.new("ShaderNodeMapRange")
    pinhole.inputs["From Min"].default_value = 0.012
    pinhole.inputs["From Max"].default_value = 0.0
    pinhole.inputs["To Max"].default_value = -1.0
    links.new(pins.outputs["Distance"], pinhole.inputs["Value"])
    surface = math_node(nodes, links, "ADD", ripple.outputs["Fac"], math_node(nodes, links, "MULTIPLY", pinhole.outputs[0], value=0.3))
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.03
    bump.inputs["Distance"].default_value = 0.03
    links.new(surface, bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Coat Normal"])
    return material


def opal():
    """Opal glass: milky white, glossy outside. The bulb inside lights it from within, the light coming through
    the glass scattered, brightest nearest the filament and dimming toward the rounded end. Unlit, it is plain
    milky glass in the room's light."""
    material = bpy.data.materials.new("opal")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0.92, 0.9, 0.87, 1)
    shader.inputs["Roughness"].default_value = 0.45
    shader.inputs["Coat Weight"].default_value = 1.0
    shader.inputs["Coat Roughness"].default_value = 0.03
    through = nodes.new("ShaderNodeBsdfTranslucent")
    through.inputs["Color"].default_value = (0.9, 0.88, 0.85, 1)
    both = nodes.new("ShaderNodeMixShader")
    both.inputs[0].default_value = 0.6
    links.new(shader.outputs[0], both.inputs[1])
    links.new(through.outputs[0], both.inputs[2])
    links.new(both.outputs[0], nodes["Material Output"].inputs["Surface"])
    return material


def bulbs(stage, ox, oy):
    """The lamp in the glass: small warm lights along the inside of the tip, off until desk.py switches them."""
    points, along = tail_curve(400)
    lights = []
    for i, share in enumerate(BULBS):
        target = along[-1] - GLASS * (1 - share)
        at = points[np.argmin(np.abs(along - target))]
        source = bpy.data.lights.new(f"catlamp-bulb-{i}", "POINT")
        source.color = BULB_COLOUR
        source.energy = 0.0
        source.shadow_soft_size = 0.35
        light = stage.add(f"catlamp-bulb-{i}", source)
        light.location = (at[0] + ox, at[1] - oy, at[2])
        light["bulb"] = True
        lights.append(light)
    return lights


def build(stage):
    ox, oy = ORIGIN
    lo, hi = (-2.4, -4.6, -0.2), (24.5, 9.0, 15.5)
    cat, verts = mesh(stage, "cat", body, lo, hi, STEP, porcelain())
    normals = np.zeros_like(verts)
    for e, column in zip(np.eye(3) * 0.01, range(3)):
        normals[:, column] = body(verts + e) - body(verts - e)
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-9)
    layer = cat.data.color_attributes.new("paint", "FLOAT_COLOR", "POINT")
    layer.data.foreach_set("color", painted(verts, normals).ravel())
    points, _ = tail_curve()
    tlo = points.min(axis=0) - 1.5
    thi = points.max(axis=0) + 1.5
    tip, _ = mesh(stage, "tip", glass, tuple(tlo), tuple(thi), 0.04, opal())
    for obj in (cat, tip):
        obj.location = (ox, -oy, 0)
    # The glass lets the bulb's light through to the room, scattered: the room is lit by the bulb itself.
    tip.visible_shadow = False
    bulbs(stage, ox, oy)
    stage.shoot("catlamp", (0, 0, W, H), lens=False)


SHOTS = {"catlamp": build}
