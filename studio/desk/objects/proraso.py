"""Shaving soap in a tube: Proraso's white Pelli Sensibili, with oatmeal and green tea, 150 ml, as the user's own,
used and crumpled, photographed from above (art/proraso-own.jpg). An aluminium tube lacquered white and printed,
under a clear gloss varnish, lying on its back with the crimped end to the left: flattened and flared toward the
crimp, narrowing to the shoulder. Its outline is the photograph's, followed down both edges (art/prorasophoto.py).
Its print is Proraso's own artwork with the green and gold drawn, laid where the photograph has them; its crumples
are real folds, from a scan of creased paper, so the light on them is the scene's. A few chips and finger marks
show it has been used. The white shoulder and the ribbed white cap screwed on its thread are clean."""

import json
import math
import os

import bmesh
import bpy
import numpy as np

from paint import disc, linear, ramp
from solids import finish, grain, principled, worn
from stage import ASSETS
from stock import Sheet, fit, pixels_of

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art")

# The tube's outline from the photograph: every 0.05 em from the crimped edge, its half width, its depth and how far
# its middle wanders off its axis, in em. Drawn WIDE times as broad and deep as the photograph measures it, the
# length kept, and its width and middle smoothed over STRAIGHT em: the photograph's small waves in the outline read
# as bends. Its depth is smoothed over SOFT em, so the pinch behind the crimp is a soft fold and not a ruled line.
WIDE = 1.125
STRAIGHT = 1.5
SOFT = 0.4
with open(os.path.join(ART, "proraso-shape.json")) as _file:
    SHAPE = json.load(_file)
for _key, _over in (("half", STRAIGHT), ("deep", SOFT), ("off", STRAIGHT)):
    _reach = int(3 * _over / 0.05)
    _kernel = np.exp(-0.5 * (np.arange(-_reach, _reach + 1) * 0.05 / _over) ** 2)
    _line = np.convolve(np.pad(SHAPE[_key], _reach, mode="edge"), _kernel / _kernel.sum(), mode="valid")
    SHAPE[_key] = list(WIDE * _line)
# The print's width once round, the length from the crimped edge to the shoulder, and the diameter at the shoulder,
# where the tube is round.
FRONT = math.pi * 5.0 / 2
LENGTH = 22.31
D = 2 * SHAPE["half"][-1]
# The crumples are a scan of creased paper (ambientCG Paper003, fetched by fetch.py): broad facets between folds,
# as squeezed aluminium takes them. The scan is laid TILE em to a repeat, once round the tube, and softened over
# ROUND em, for aluminium folds round over where paper creases sharp and the paper's own crinkle is not in metal.
# Its heights are spread DENT em about their middle (one deviation), and none goes more than REACH deviations in or
# out. They give way where the flattened tube folds over at its edges (FOLD em, see body()), and the crimped end is
# pressed flat for its first CRIMP em.
TILE = 2 * FRONT
ROUND = 0.035
DENT = 0.09
REACH = 2.5
FOLD = 0.3
CRIMP = 0.5

# The tube's white lacquer, and Proraso's inks: a deep green, a red, and a gold that is a metallic ink.
WHITE = "#d2d1cc"
LEAF = "#14583a"
RED = "#7a2620"
GOLD = "#c09a5b"
PLASTIC = "#e6e5e0"
# Where the print lies, in em round from the middle of the face up and down from the crimped edge, as the photograph
# has it. The gold bands, BAND_W wide, are BAND em out at FEET em down and run SLOPE em further out for each em up,
# to the crimp; outside them the green runs round the sides to SIDE em, down to GREEN em, and under it, behind the
# logo's panel, a band of red and a line of gold. The logo's panel, the lettering and the signature are boxes
# (left, top, right, bottom) round the front's middle.
BAND, FEET, SLOPE, BAND_W = 1.37, 4.82, 0.723, 0.15
SIDE, GREEN = 5.03, 4.56
FLAG = ((5.32, 6.30, RED), (6.30, 6.40, GOLD))
LOGO = (-3.55, 3.45, 3.75, 8.05)
LETTERING = (-3.02, 9.8, 3.17, 12.27)
SIGNATURE = (-3.2, 18.07, 3.7, 19.74)

# The shoulder domes in from the wall to the neck, and the cap covers the neck from where the dome is this wide.
DOME = 0.62
NECK = 0.72
CAP_R, CAP_H = 0.345 * D, 0.53 * D
RIBS = 100
WELL = 0.6
W, H = 25.5, 8.95


def crumples(round_, along):
    """The crumples' height, in em about their middle, at points so far round the tube and so far along it from the
    crimped edge, in em: a row for each along. Pressed flat in the crimp and dying out at the shoulder's rim."""
    image = bpy.data.images.load(os.path.join(ASSETS, "Paper003", "Paper003_2K-PNG_Displacement.png"))
    image.colorspace_settings.name = "Non-Color"
    size = image.size[0]
    data = np.empty(size * size * 4, dtype=np.float32)
    image.pixels.foreach_get(data)
    bpy.data.images.remove(image)
    scan = data.reshape(size, size, 4)[::-1, :, 0].astype(np.float64)
    # Softened over ROUND em by a blur that wraps round the tile as the tile wraps round the tube.
    sigma, f = ROUND / TILE * size, np.fft.fftfreq(size)
    scan = np.real(np.fft.ifft2(np.fft.fft2(scan) * np.exp(-2 * (np.pi * sigma) ** 2 * (f[:, None] ** 2 + f[None, :] ** 2))))

    xs, ys = np.meshgrid(round_ / TILE * size, along / TILE * size)
    x0, y0 = np.floor(xs).astype(int), np.floor(ys).astype(int)
    fx, fy = xs - x0, ys - y0
    x0, y0 = x0 % size, y0 % size
    x1, y1 = (x0 + 1) % size, (y0 + 1) % size
    top = scan[y0, x0] * (1 - fx) + scan[y0, x1] * fx
    bottom = scan[y1, x0] * (1 - fx) + scan[y1, x1] * fx
    height = DENT * np.clip(((top * (1 - fy) + bottom * fy) - scan.mean()) / scan.std(), -REACH, REACH)
    return height * (ramp(CRIMP, CRIMP + 0.4, along) * (1 - ramp(LENGTH - 0.35, LENGTH - 0.05, along)))[:, None]


def printed(sheet, name, left, top, right, bottom):
    """Print one of Proraso's artworks in a box given in em round the front's middle. Its white is the tube's own
    white lacquer and covers whatever is printed under it; its inks go over that."""
    r0, r1, c0, c1 = (round(v * sheet.ppe) for v in (top, bottom, FRONT + left, FRONT + right))
    image = fit(pixels_of(os.path.join(ART, f"proraso-{name}.png")).astype(np.float64), r1 - r0, c1 - c0)
    srgb, alpha = image[..., :3], image[..., 3]
    own = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
    ink = alpha * (1 - ramp(0.8, 0.95, srgb.min(axis=-1)))
    patch = sheet.rgb[r0:r1, c0:c1]
    patch += alpha[..., None] * (linear(WHITE) - patch)
    patch += ink[..., None] * (own - patch)


def label():
    """The print, once round the tube across and crimp to shoulder down: ink and lacquer only, for the light on the
    crumples is the geometry's."""
    sheet = Sheet(2 * FRONT, LENGTH, WHITE, rough=0.3, density=3)
    X, Y = sheet.X, sheet.Y
    out = np.abs(X - FRONT)

    # The green outside the gold bands and round the sides, and the red and gold under it at the sides.
    spread = BAND + (FEET - Y) * SLOPE
    outside = sheet.mask(spread - out) * sheet.mask(out - SIDE)
    sheet.paint(outside * sheet.mask(Y - GREEN), LEAF)
    for top, foot, colour in FLAG:
        sheet.paint(outside * sheet.mask(top - Y) * sheet.mask(Y - foot), colour)
    band = sheet.mask(np.abs(out - spread) / math.hypot(1, SLOPE) - BAND_W / 2) * sheet.mask(Y - FEET - 0.15)
    sheet.paint(band, GOLD)

    printed(sheet, "white-logo", *LOGO)
    printed(sheet, "white-lettering", *LETTERING)
    printed(sheet, "signature", *SIGNATURE)

    # The gold is a metallic ink, found by its colour: warm, and yellow rather than red.
    r, g, b = sheet.rgb[..., 0], sheet.rgb[..., 1], sheet.rgb[..., 2]
    warm, yellow = (r - b) / np.maximum(r, 1e-3), g / np.maximum(r, 1e-3)
    gilt = ramp(0.45, 0.6, warm) * ramp(0.3, 0.4, yellow) * (1 - ramp(0.85, 0.95, yellow)) * ramp(0.06, 0.12, r)
    sheet.finish(gilt, rough=0.25, metal=0.7)

    # Used: the lacquer is chipped in a few small specks down to the bare aluminium, most of them round the
    # shoulder's rim and the crimp, where the tube is knocked and pressed.
    rng = np.random.default_rng(8799)
    chips = np.zeros(sheet.height.shape)
    for _ in range(40):
        y = rng.choice((rng.uniform(LENGTH - 0.5, LENGTH - 0.05), rng.uniform(0.05, 1.2), rng.uniform(1.2, LENGTH - 0.5)), p=(0.3, 0.2, 0.5))
        x = FRONT + rng.uniform(-4.2, 4.2)
        rows, cols = sheet.window(x - 0.05, y - 0.05, x + 0.05, y + 0.05)
        chips[rows, cols] = np.maximum(chips[rows, cols], sheet.mask(disc(X[rows, cols], Y[rows, cols], x, y, rng.uniform(0.008, 0.025))))
    sheet.paint(chips, "#d6d8da")
    sheet.finish(chips, rough=0.35, metal=1.0)

    # The whole print is under one clear, hard varnish, except where it is chipped.
    sheet.coat[:] = 1 - chips
    return sheet


def lacquer(sheet, name, wear=()):
    """A material from a painted sheet, to wrap on a mesh by its UV map."""
    rows, cols = sheet.height.shape

    def image(kind, channels):
        img = bpy.data.images.new(f"{name}-{kind}", cols, rows, alpha=True, float_buffer=True)
        img.colorspace_settings.name = "Non-Color"
        img.alpha_mode = "CHANNEL_PACKED"
        img.pixels.foreach_set(np.dstack(channels)[::-1].astype(np.float32).ravel())
        img.pack()
        node = nodes.new("ShaderNodeTexImage")
        node.image = img
        node.interpolation = "Cubic"
        return node

    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    inked = image("colour", (sheet.rgb[..., 0], sheet.rgb[..., 1], sheet.rgb[..., 2], np.ones((rows, cols))))
    packed = image("data", (sheet.height, sheet.rough, sheet.metal, sheet.coat))
    split = nodes.new("ShaderNodeSeparateColor")
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 1.0
    links.new(packed.outputs["Color"], split.inputs["Color"])
    links.new(split.outputs["Red"], bump.inputs["Height"])
    links.new(inked.outputs["Color"], shader.inputs["Base Color"])
    links.new(split.outputs["Green"], shader.inputs["Roughness"])
    links.new(split.outputs["Blue"], shader.inputs["Metallic"])
    links.new(packed.outputs["Alpha"], shader.inputs["Coat Weight"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(bump.outputs["Normal"], shader.inputs["Coat Normal"])
    # The shine is the varnish's alone: a hard gloss, which finger marks dull a little.
    shader.inputs["Specular IOR Level"].default_value = 0.1
    for asset, size, dull in wear:
        worn(material, asset, size, dull)
    varnish = nodes.new("ShaderNodeMath")
    varnish.operation = "MULTIPLY"
    varnish.inputs[1].default_value = 0.12
    links.new(shader.inputs["Roughness"].links[0].from_socket, varnish.inputs[0])
    links.new(varnish.outputs[0], shader.inputs["Coat Roughness"])
    return material


def body(stage, material):
    """The wall of the tube: every section an oval as wide as the photograph shows the tube there and as deep as
    the shape has it, its middle where the photograph's is."""
    rings, steps = 1440, 720
    along = np.linspace(0, LENGTH, rings)
    a = np.interp(along, SHAPE["along"], SHAPE["half"])
    b = np.maximum(np.interp(along, SHAPE["along"], SHAPE["deep"]), 0.11)
    # Held round by the shoulder over its last em, to meet the shoulder's rim all the way round.
    b = b + (a - b) * ramp(LENGTH - 1.0, LENGTH, along)
    off = np.interp(along, SHAPE["along"], SHAPE["off"])

    # Points evenly spaced round each oval, as the print was unrolled.
    phi = np.linspace(-np.pi, np.pi, 4097)
    turn = np.empty((rings, steps))
    share = np.arange(steps) / steps
    for i in range(rings):
        ds = np.hypot(a[i] * np.cos(phi), b[i] * np.sin(phi))
        s = np.concatenate(([0], np.cumsum((ds[1:] + ds[:-1]) / 2)))
        turn[i] = np.interp(share * s[-1], s, phi)
    y, z = a[:, None] * np.sin(turn), b[:, None] * np.cos(turn)
    # The crumples pushed out along each point's normal on the oval, all the way round.
    ny, nz = b[:, None] * np.sin(turn), a[:, None] * np.cos(turn)
    length = np.hypot(ny, nz)
    push = crumples(share * 2 * FRONT, along)
    # Where the flattened tube folds over at its edges the wall curves tighter than any crumple and stays a fold: the
    # crumples die away as the radius it curves on falls below FOLD em. Pushed in no further than under half the gap
    # to the wall facing it, which may be pushed in as far, eased in toward that: the gap closes toward the edges.
    curve = (a[:, None] ** 2 * np.cos(turn) ** 2 + b[:, None] ** 2 * np.sin(turn) ** 2) ** 1.5 / (a * b)[:, None]
    push = push * curve / (curve + FOLD)
    give = 0.45 * b[:, None] * np.abs(np.cos(turn)) + 1e-4
    push = np.where(push < 0, -give * np.tanh(-push / give), push)
    y, z = y + push * ny / length + off[:, None], z + push * nz / length

    # It lies on the mat. The crimped end has a wave in it, and its edge is not cut quite straight.
    x = np.broadcast_to(along[:, None], (rings, steps))
    round_ = (share[None, :] - 0.5) * 2 * FRONT
    z = np.maximum(z + b[:, None], 0.0) + 0.045 * (1 + np.sin(0.8 + 1.25 * round_)) * (1 - ramp(0, 3.0, x))
    x = x + 0.05 * np.sin(0.6 + 0.9 * round_) * (1 - ramp(0, 1.4, x))

    verts = np.column_stack((x.ravel(), y.ravel(), z.ravel()))
    i, k = np.meshgrid(np.arange(rings - 1), np.arange(steps), indexing="ij")
    i, k = i.ravel(), k.ravel()
    near, far = k, (k + 1) % steps
    faces = np.column_stack((i * steps + near, (i + 1) * steps + near, (i + 1) * steps + far, i * steps + far))
    mesh = bpy.data.meshes.new("tube")
    mesh.from_pydata(verts.tolist(), [], faces.tolist() + [list(range(steps))])
    u = np.column_stack((k, k, k + 1, k + 1)) / steps
    v = 1 - np.column_stack((i, i + 1, i + 1, i)) / (rings - 1)
    uv = np.concatenate((np.dstack((u, v)).ravel(), np.tile((0.5, 1.0), steps)))
    mesh.uv_layers.new().data.foreach_set("uv", uv)
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.materials.append(material)
    return stage.add("tube", mesh)


def turned(stage, name, rings, material, steps, wave=None):
    """Spin rings of (height, radius, part) about the object's z axis. wave(part, height, angles) is added to
    the radius of the rings that name a part, for ribs and threads. A ring of no radius closes to a point."""
    bm = bmesh.new()
    angles = np.arange(steps) * 2 * np.pi / steps
    loops = []
    for height, radius, part in rings:
        if radius <= 1e-6:
            loops.append([bm.verts.new((0, 0, height))])
            continue
        r = radius + (wave(part, height, angles) if part else np.zeros(steps))
        loops.append([bm.verts.new((r[j] * math.cos(angles[j]), r[j] * math.sin(angles[j]), height)) for j in range(steps)])
    for lower, upper in zip(loops, loops[1:]):
        for j in range(steps):
            n = (j + 1) % steps
            if len(lower) == 1 and len(upper) == 1:
                continue
            if len(lower) == 1:
                bm.faces.new((lower[0], upper[j], upper[n]))
            elif len(upper) == 1:
                bm.faces.new((lower[j], upper[0], lower[n]))
            else:
                bm.faces.new((lower[j], upper[j], upper[n], lower[n]))
    return finish(stage, name, bm, material)


def shoulder(stage, enamel):
    """The stiff end of the tube: a dome in white enamel from the wall's rim in to the neck. It starts just inside
    the wall, so nothing of it shows past the rim."""
    r = D / 2
    k = r - CAP_R
    dome = [(-0.05, r - 0.02), (0.0, r - 0.006 * k), (0.05, r - 0.03 * k), (0.14, r - 0.11 * k), (0.3, r - 0.38 * k), (0.45, r - 0.7 * k), (DOME, CAP_R + 0.02), (DOME + 0.12, CAP_R - 0.3), (DOME + 0.2, NECK), (DOME + 0.5, NECK)]
    part = turned(stage, "shoulder", [(h, radius, None) for h, radius in dome], enamel, 160)
    part.rotation_euler = (0, math.radians(90), 0)
    part.location = (LENGTH, 0, r)
    return part


def cap(stage, plastic):
    """The screw cap on its thread, as the photographs have it: a straight wall finely ribbed the whole way up, a
    hair narrower toward its closed end, and that end a flat ring round a round well WELL across and 0.3 em deep.
    It turns about its own z axis, open end down."""
    def wall(h):
        return CAP_R * (1 - 0.03 * h / CAP_H)

    well = WELL * CAP_R
    rings = [(0.0, CAP_R - 0.22, None), (0.0, CAP_R - 0.07, None), (0.03, CAP_R - 0.02, None), (0.07, CAP_R, "ribs")]
    rings += [(h, wall(h), "ribs") for h in np.linspace(0.12, CAP_H - 0.12, 14)]
    rings += [(CAP_H - 0.05, wall(CAP_H) - 0.02, "ribs"), (CAP_H - 0.015, wall(CAP_H) - 0.05, None), (CAP_H, wall(CAP_H) - 0.1, None)]
    rings += [(CAP_H, well + 0.04, None), (CAP_H - 0.015, well, None), (CAP_H - 0.3, well - 0.01, None), (CAP_H - 0.3, 0, None)]

    def ribs(part, height, angles):
        return -0.035 * (0.5 - 0.5 * np.cos(RIBS * angles)) * ramp(0.05, 0.12, height)

    return turned(stage, "cap", rings, plastic, RIBS * 6, ribs)


def proraso(stage):
    # Finger marks dull the varnish where the tube is held and squeezed.
    paint = lacquer(label(), "lacquer", wear=(("Fingerprints009", 6, 0.12),))
    enamel = worn(principled("enamel", WHITE, rough=0.2, coat_weight=1.0, coat_roughness=0.04), "SurfaceImperfections003", 3, 0.15)
    # Moulded polypropylene: a satin white that lets a little light into it.
    plastic = principled("cap", PLASTIC, rough=0.32, subsurface_weight=0.2, subsurface_scale=0.03)
    plastic = worn(grain(plastic, 320, 0.0015), "SurfaceImperfections003", 3, 0.12)

    root = stage.add("proraso", None)
    root.location = (0.04, -H / 2, 0)
    lid = cap(stage, plastic)
    lid.rotation_mode = "ZYX"
    lid.rotation_euler = (0, math.radians(90), math.radians(23))
    lid.location = (LENGTH + DOME - 0.03, SHAPE["off"][-1], D / 2)
    tube_end = shoulder(stage, enamel)
    tube_end.location.y = SHAPE["off"][-1]
    for part in (body(stage, paint), tube_end, lid):
        part.parent = root

    stage.shoot("proraso", (0, 0, W, H), bleed=1.0, shadow=1.2)


SHOTS = {"proraso": proraso}
