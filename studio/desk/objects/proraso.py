"""Shaving soap in a tube: Proraso's white Pelli Sensibili, with oatmeal and green tea, 150 ml, after the
maker's packshot and photographs of used ones. A lacquered aluminium tube lying on its back, crimped end to the left, a few weeks into use:
pressed flat toward the crimp, with a few small creases there where the white lacquer has cracked, and the
shallow dents thumbs leave in thin aluminium further along. The white enamel shoulder and the ribbed white cap screwed on its thread are dulled with
dried soap. The crimp is bitten by the jaws that closed it and stamped with a
lot number.
The lacquer is a satin gloss, lit only by the room the rest of the desk is in. The front's print is a real tube's,
unrolled from a photograph of one; round the sides the logo's panel, the green and the flag are drawn."""

import math
import os

import bmesh
import bpy
import numpy as np

from paint import blur, cloud, linear, ramp
from solids import finish, grain, principled, worn
from stock import Sheet, fit, pixels_of

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art")

# The tube: its diameter when full, the flat width of its front (half the way round) and its length from the
# crimped edge to the shoulder. Everything printed on it is placed in shares of the flat width, as measured
# on the packshot unrolled.
D = 5.0
FRONT = math.pi * D / 2
LENGTH = 2.84 * FRONT
FOLD = 0.7
# How thick the tube is along its length: folded shut at the crimp, pressed flat for the first few em where it
# has been squeezed from, and filling out to round well before the shoulder.
THICK = ((0, 0.26), (FOLD, 0.26), (FOLD + 0.14, 0.14), (1.5, 0.35), (3.5, 0.6), (5.5, 1.2), (8.0, 2.2), (11.0, 3.4), (14.0, 4.3), (17.0, 4.8), (LENGTH, D))
# Where thumbs have pressed it over a few weeks of use: distance from the crimp and round from the middle of the
# front, the radius along and round, and the depth. Thin aluminium takes a press as a shallow dent with a flat
# floor and a defined rim, not a soft hollow.
# A thumb never presses a circle: each dent is turned (in degrees) and its rim wanders.
DIVOTS = (
    (6.4, 0.5, 1.7, 1.1, 0.1, 25),
    (9.6, -1.3, 2.1, 1.3, 0.14, -15),
    (11.9, 1.6, 1.5, 0.9, 0.11, 40),
    (14.2, -0.6, 1.8, 1.4, 0.08, 10),
    (17.1, 1.2, 1.2, 0.8, 0.06, -30),
)


def _folds(seed=7):
    """The small creases where the end has been pressed flat: thin metal folds into flat facets with sharp
    creases between them. Each
    fold is a straight crease of limited length, at (along, round) in em, turned this many radians off the
    tube's axis, half this long, its flanks sloping this much for this far either side of it and level beyond.
    A negative slope is a ridge."""
    rng = np.random.default_rng(seed)
    folds = []
    while len(folds) < 22:
        # Only where it has been pressed flat does the metal fold.
        at = rng.uniform(FOLD + 0.2, 6.0)
        flat = True
        across = rng.uniform(-FRONT * 0.7, FRONT * 0.7)
        # Mostly across the tube, the way a thumb presses, with some running along it.
        turn = np.radians(90 + rng.normal(0, 30)) if rng.random() < 0.8 else np.radians(rng.normal(0, 12))
        half = rng.uniform(0.5, 2.2)
        reach = rng.uniform(0.15, 0.5)
        slope = rng.choice((-1, 1)) * rng.uniform(0.03, 0.08)
        folds.append((at, across, turn, half, reach, slope))
    return tuple(folds)


FOLDS = _folds()
# The sharpest of them, where the lacquer has cracked along the crease: as segments, (along, round) to (along,
# round), with a width for the crack.
CREASES = tuple(
    (at - half * np.cos(turn) * 0.7, across - half * np.sin(turn) * 0.7, at + half * np.cos(turn) * 0.7, across + half * np.sin(turn) * 0.7, slope, 0.12)
    for at, across, turn, half, reach, slope in FOLDS
    if abs(slope) > 0.07
)
# The print is never quite square to the crimp.
SLIP = 0.02

BODY = "#e4e4df"
LEAF = "#1f7a3c"
WHITE = "#f2f1ea"
RED = "#a3261f"
GOLD = "#d8c08c"
ALU = "#c9cacb"
PLASTIC = "#e2e1dc"
SOAP = "#f2f0e8"
SHEEN = "#1a8f86"

# The shoulder domes in from the wall to the neck, and the cap covers the neck from where the dome is this wide.
DOME = 0.62
NECK = 0.83
CAP_R, CAP_H = 0.3 * D, 0.5 * D
RIBS = 84
W, H = 25.5, 7.95


def label():
    """The print, upright as on the packshot: once round the tube across, crimp to shoulder down."""
    sheet = Sheet(2 * FRONT, LENGTH, BODY, rough=0.34, density=3)
    X, Y = sheet.X, sheet.Y
    shape = sheet.height.shape
    F = FRONT
    mid = F * (1 + SLIP)
    out = np.abs(X - mid)

    # Two gold lines fall from the corners toward the lion. Outside them the green is lighter, and under that
    # the white and red of the flag run round the tube behind the logo.
    spread = 0.174 * F + (0.614 * F - Y) / 1.383
    # On the white tube the green runs only to just round the sides. The back is white.
    outside = sheet.mask(spread - out) * sheet.mask(out - 0.64 * F)
    sheet.paint(outside * sheet.mask(Y - 0.58 * F), LEAF)
    for top, foot, colour in ((0.58, 0.677, WHITE), (0.677, 0.802, RED), (0.802, 0.815, GOLD)):
        sheet.paint(outside * sheet.mask(top * F - Y) * sheet.mask(Y - foot * F), colour)
    sheet.paint(sheet.mask(np.abs(out - spread) * 0.81 - 0.014 * F) * sheet.mask(Y - 0.63 * F), GOLD)

    def printed(name, x0, y0, x1, y1):
        sheet.art(os.path.join(ART, f"proraso-{name}.png"), mid + x0 * F, y0 * F, mid + x1 * F, y1 * F)

    printed("white-logo", -0.4645, 0.467, 0.4645, 1.0715)
    # Over the front, a real tube's print, unrolled from a photograph of one (art/prorasophoto.py): its inks, its
    # registration and the faint unevenness of its lacquer. The drawing above is left only round the sides, where
    # the logo's panel wraps; the lettering and the signature are the photograph's alone.
    printed("print", -0.5, 0.0, 0.5, LENGTH / F)

    # Every gold on it is a pale metallic ink: warm, and yellow rather than red.
    r, g, b = sheet.rgb[..., 0], sheet.rgb[..., 1], sheet.rgb[..., 2]
    gilt = np.clip(((r - b) / np.maximum(r, 1e-3) - 0.35) / 0.15, 0, 1) * np.clip((g / np.maximum(r, 1e-3) - 0.6) / 0.1, 0, 1) * np.clip((r - 0.08) / 0.05, 0, 1)
    sheet.finish(gilt, metal=0.35)

    # The crimp: the end folded over three times and pressed, each fold a step down toward the wall, none of
    # them straight. The jaws that pressed it left their teeth in it and the lot number, and the lacquer has
    # rubbed thin along the folds.
    wavy = 0.03 * cloud((1, shape[1]), 2, falloff=1.6) + 0.012 * cloud((1, shape[1]), 12, falloff=0.9)
    folds = ((FOLD, 0.03), (FOLD * 0.68, 0.022), (FOLD * 0.33, 0.02))
    sheet.height += blur(sum(step * sheet.mask(Y - y - wavy * (1 + n)) for n, (y, step) in enumerate(folds)), 2)
    band = sheet.mask(Y - FOLD + 0.06 - wavy) * ramp(0.02, 0.1, Y)
    bitten = np.clip(0.6 + 0.5 * cloud(shape, 13, falloff=1.8), 0, 1) * band
    r0, r1, c0, c1 = (round(v * sheet.ppe) for v in (0.14, 0.14 + 0.44, mid + 0.7, mid + 0.7 + 2.2))
    lot = np.zeros(shape)
    lot[r0:r1, c0:c1] = fit(pixels_of(os.path.join(ART, "proraso-lot.png"))[..., 3:].astype(np.float64), r1 - r0, c1 - c0)[..., 0]
    stamped = np.zeros(shape)
    stamped[r0:r1, c0:c1] = 1
    sheet.press((0.5 + 0.5 * np.cos(2 * np.pi * X / 0.085)) * bitten * (1 - blur(stamped, 6)), 0.006)
    sheet.press(blur(lot, 1.5), 0.03)
    sheet.rgb *= (1 - 0.35 * blur(lot, 1.5))[..., None]
    edges = sum(gain * np.exp(-(((Y - y - wavy) / width) ** 2)) for y, width, gain in ((0, 0.05, 1.2), (FOLD * 0.33, 0.02, 0.5), (FOLD * 0.68, 0.02, 0.4), (FOLD, 0.03, 0.6)))
    bare = np.clip(edges * (0.1 + 0.7 * cloud(shape, 3, falloff=1.3)), 0, 1)
    # The rim of the shoulder chips, and the white under the print shows.
    rim = (1 - ramp(0.0, 0.06, LENGTH - Y)) * np.clip(cloud(shape, 6, falloff=1.2, stretch=3.0) * 0.8 + 0.1, 0, 1)
    sheet.paint(np.clip(rim, 0, 1), WHITE)
    bare = blur(bare, 0.8)
    sheet.paint(bare * 0.85, ALU)
    sheet.finish(bare, rough=0.4, metal=1.0)

    # Squeezing has cracked the lacquer along every crease, in broken runs, and flaked it off beside them.
    cracked = np.zeros(shape)
    for a0, r0, a1, r1, _, width in CREASES:
        apart = crease(Y, X - mid, a0, r0, a1, r1)
        broken = np.clip(cloud(shape, int(a0 * 10), falloff=0.8) * 1.5 - 0.4, 0, 1)
        flakes = np.clip(cloud(shape, int(a1 * 10), falloff=0.7) * 2 - 2.2, 0, 1)
        cracked = np.maximum(cracked, np.maximum(sheet.mask(apart - width * 0.1) * broken, sheet.mask(apart - width) * flakes))
    cracked = blur(cracked, 0.5)
    sheet.paint(cracked * 0.6, ALU)
    sheet.finish(cracked, rough=0.3, metal=1.0)
    bare = np.maximum(bare, cracked)
    # Dried soap in a crust along the rim of the shoulder, where the cap has been screwed down over a smear of it.
    smear = (1 - ramp(0.1, 0.9, LENGTH - Y)) * np.clip(cloud(shape, 71, falloff=1.0, stretch=2.0) * 1.4 - 0.2, 0, 1)
    sheet.paint(smear * 0.8, SOAP)
    sheet.finish(smear, rough=0.75, metal=0.0)
    bare = np.maximum(bare, smear)

    # The green is a translucent lacquer over the bright aluminium, so the light it throws back is green too.
    # In the photographs its lit band is a saturated blue green, never grey.
    green = np.clip(((sheet.rgb[..., 1] - np.maximum(sheet.rgb[..., 0], sheet.rgb[..., 2])) / np.maximum(sheet.rgb[..., 1], 1e-3) - 0.3) / 0.15, 0, 1) * (1 - bare)
    sheet.finish(green, metal=0.55)
    sheet.rgb += (green * (1 - outside))[..., None] * (linear(SHEEN) - sheet.rgb) * 0.45

    # The whole print is under one clear varnish, a little duller in the broad patches where it is held.
    sheet.coat[:] = (1 - bare) * 0.6
    sheet.finish(np.clip(0.5 + 0.4 * cloud(shape, 7, falloff=2.6), 0, 1) * (1 - bare), rough=0.32)
    return sheet


def crease(along, round_, a0, r0, a1, r1):
    """Distance from a crease given as a segment from (a0, r0) to (a1, r1), in em along and round the tube."""
    pa, pr, da, dr = along - a0, round_ - r0, a1 - a0, r1 - r0
    t = np.clip((pa * da + pr * dr) / (da * da + dr * dr), 0, 1)
    return np.hypot(pa - da * t, pr - dr * t)


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
    # The shine is the varnish's alone: a satin gloss, which finger marks dull a little.
    shader.inputs["Specular IOR Level"].default_value = 0.1
    for asset, size, dull in wear:
        worn(material, asset, size, dull)
    varnish = nodes.new("ShaderNodeMath")
    varnish.operation = "MULTIPLY"
    varnish.inputs[1].default_value = 0.42
    links.new(shader.inputs["Roughness"].links[0].from_socket, varnish.inputs[0])
    links.new(varnish.outputs[0], shader.inputs["Coat Roughness"])
    return material


def body(stage, material):
    """The wall of the tube: every section is an oval of the same girth, as thick as the tube is there, with
    the two hollows pushed into it and the slow unevenness of thin metal that has been handled."""
    rings, steps = 960, 480
    along = np.linspace(0, LENGTH, rings)
    thick = np.interp(along, *zip(*THICK))
    kernel = np.exp(-(np.linspace(-2, 2, 25) ** 2))
    thick = np.convolve(np.pad(thick, 12, mode="edge"), kernel / kernel.sum(), mode="valid")
    b = thick / 2
    # The crimp runs square across the tube, and the jaws leave both its corners very slightly rounded.
    rounded = 0.12 * (1 - np.sqrt(1 - np.clip(1 - along / 0.12, 0, 1) ** 2))
    wide = FRONT / 2 - rounded
    lo, hi = b.copy(), wide.copy()
    for _ in range(40):
        a = (lo + hi) / 2
        h = ((a - b) / (a + b)) ** 2
        girth = np.pi * (a + b) * (1 + 3 * h / (10 + np.sqrt(4 - 3 * h)))
        lo, hi = np.where(girth < 4 * wide, a, lo), np.where(girth < 4 * wide, hi, a)

    # Points evenly spaced round each oval, so the print keeps its width wherever the tube is flattened.
    phi = np.linspace(-np.pi, np.pi, 4097)
    turn = np.empty((rings, steps))
    share = np.arange(steps) / steps
    for i in range(rings):
        ds = np.hypot(a[i] * np.cos(phi), b[i] * np.sin(phi))
        s = np.concatenate(([0], np.cumsum((ds[1:] + ds[:-1]) / 2)))
        turn[i] = np.interp(share * s[-1], s, phi)
    y, z = a[:, None] * np.sin(turn), b[:, None] * np.cos(turn)
    ny, nz = b[:, None] * np.sin(turn), a[:, None] * np.cos(turn)
    length = np.hypot(ny, nz)

    # Dents, and the slow unevenness of thin metal that has been handled.
    x = np.broadcast_to(along[:, None], (rings, steps))
    round_ = (share[None, :] - 0.5) * 2 * FRONT
    push = np.zeros((rings, steps))
    # Each fold is a V along its crease, level beyond its reach, and dies away toward its two ends.
    for at, across, turn, half, reach, slope in FOLDS:
        along_, round_off = x - at, round_ - across
        t = along_ * np.cos(turn) + round_off * np.sin(turn)
        d = -along_ * np.sin(turn) + round_off * np.cos(turn)
        ends = np.clip(1 - (np.abs(t) / half) ** 2, 0, 1) ** 0.6
        push += slope * (reach - np.minimum(np.abs(d), reach)) * ends
    for n, (at, across, r_along, r_round, depth, turn) in enumerate(DIVOTS):
        c, s_ = np.cos(np.radians(turn)), np.sin(np.radians(turn))
        u, w = (x - at) * c + (round_ - across) * s_, -(x - at) * s_ + (round_ - across) * c
        theta = np.arctan2(w, u)
        wander = 1 + 0.18 * np.sin(3 * theta + n * 1.7) + 0.1 * np.sin(5 * theta + n * 2.9)
        q = np.sqrt((u / r_along) ** 2 + (w / r_round) ** 2) / wander
        # A floor that is not quite flat, and a rim that is sharper on one side than the other.
        floor = 1 - 0.25 * np.clip(u / r_along, -1, 1)
        push += depth * floor * (1 - ramp(0.35 + 0.15 * np.sin(theta + n), 1.0, q))
    push += 0.012 * cloud((rings, steps), 21, falloff=2.2) * ramp(0, 3, thick)[:, None]
    push *= ramp(FOLD, FOLD + 0.7, x) * (1 - ramp(LENGTH - 1.8, LENGTH - 0.35, x))
    y, z = y - push * ny / length, z - push * nz / length
    # It lies on the mat and is not quite straight. The crimped end has a wave in it, its edge is not cut
    # quite straight, and one corner has been bent a little up off the mat.
    y = y + 0.05 * np.sin(1.0 + 4.4 * x / LENGTH) * ramp(0, 5.5, x)
    z = np.maximum(z + b[:, None], 0.0) + 0.045 * (1 + np.sin(0.8 + 1.25 * round_)) * (1 - ramp(0, 3.0, x))
    z = z + 0.2 * np.clip(1 - np.hypot(x, y - FRONT / 2) / 1.5, 0, 1) ** 2
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
    """The stiff end of the tube: a dome in white enamel from the wall in to the neck."""
    r = D / 2
    dome = [(-0.3, r - 0.04), (0.0, r - 0.006), (0.05, r - 0.03), (0.14, r - 0.11), (0.3, r - 0.38), (0.45, r - 0.7), (DOME, CAP_R + 0.02), (DOME + 0.12, CAP_R - 0.3), (DOME + 0.2, NECK), (DOME + 0.5, NECK)]
    part = turned(stage, "shoulder", [(h, radius, None) for h, radius in dome], enamel, 160)
    part.rotation_euler = (0, math.radians(90), 0)
    part.location = (LENGTH, 0, r)
    return part


def cap(stage, plastic):
    """The screw cap on its thread: a straight ribbed wall, a hair narrower toward its closed end, and a
    flat end with a tight round on its edge. It turns about its own z axis, open end down."""
    def wall(h):
        return CAP_R * (1 - 0.03 * h / CAP_H)

    rings = [(0.0, CAP_R - 0.22, None), (0.0, CAP_R - 0.07, None), (0.03, CAP_R - 0.02, None), (0.07, CAP_R, "ribs")]
    rings += [(h, wall(h), "ribs") for h in np.linspace(0.12, CAP_H - 0.12, 14)]
    rings += [(CAP_H - 0.05, wall(CAP_H) - 0.02, "ribs"), (CAP_H - 0.015, wall(CAP_H) - 0.05, None), (CAP_H, wall(CAP_H) - 0.1, None), (CAP_H, 0, None)]

    def ribs(part, height, angles):
        return -0.075 * (0.5 - 0.5 * np.cos(RIBS * angles)) ** 0.7 * ramp(0.05, 0.12, height)

    return turned(stage, "cap", rings, plastic, RIBS * 6, ribs)


def soiled(material, grooves, reach, colour=SOAP, most=1.0):
    """Dried soap on a part turned about its z axis: in the grooves of its ribs if it has any, thickest at the
    foot of the part and fading out over `reach` up it, and never even. most is how far it covers at its thickest."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]

    def maths(op, a, b=None, c=None):
        node = nodes.new("ShaderNodeMath")
        node.operation = op
        for socket, value in zip(node.inputs, (a, b, c)):
            if value is None:
                continue
            if isinstance(value, (int, float)):
                socket.default_value = value
            else:
                links.new(value, socket)
        return node.outputs[0]

    def step(lo, hi, value, falling=False):
        node = nodes.new("ShaderNodeMapRange")
        node.interpolation_type = "SMOOTHSTEP"
        node.inputs["From Min"].default_value, node.inputs["From Max"].default_value = lo, hi
        node.inputs["To Min"].default_value, node.inputs["To Max"].default_value = (1, 0) if falling else (0, 1)
        links.new(value, node.inputs["Value"])
        return node.outputs[0]

    coord = nodes.new("ShaderNodeTexCoord")
    split = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coord.outputs["Object"], split.inputs[0])
    patchy = nodes.new("ShaderNodeTexNoise")
    patchy.inputs["Scale"].default_value = 1.7
    patchy.inputs["Detail"].default_value = 5
    links.new(coord.outputs["Object"], patchy.inputs["Vector"])
    amount = maths("MULTIPLY", step(0.0, reach, split.outputs["Z"], falling=True), maths("MULTIPLY", step(0.45, 0.72, patchy.outputs[0]), most))
    if grooves:
        around = maths("MULTIPLY", maths("ARCTAN2", split.outputs["Y"], split.outputs["X"]), grooves)
        amount = maths("MULTIPLY", amount, step(0.1, 0.85, maths("MULTIPLY_ADD", maths("COSINE", around), -0.5, 0.5)))
    tint = nodes.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.inputs[6].default_value = shader.inputs["Base Color"].default_value
    tint.inputs[7].default_value = (*linear(colour), 1)
    links.new(amount, tint.inputs[0])
    links.new(tint.outputs[2], shader.inputs["Base Color"])
    rough = shader.inputs["Roughness"]
    under = rough.links[0].from_socket if rough.is_linked else rough.default_value
    links.new(maths("ADD", under, maths("MULTIPLY", amount, 0.5)), rough)
    return material


def proraso(stage):
    paint = lacquer(label(), "lacquer", wear=(("Fingerprints009", 7, 0.07), ("SurfaceImperfections003", 11, 0.05)))
    enamel = worn(principled("enamel", "#dcdcd8", rough=0.3), "SurfaceImperfections003", 3, 0.25)
    soiled(enamel, 0, DOME + 0.4, colour="#e9e6dc", most=0.5)
    plastic = worn(grain(principled("cap", PLASTIC, rough=0.36), 320, 0.0015), "SurfaceImperfections003", 3, 0.2)
    soiled(plastic, RIBS, 2.2, most=0.85)

    root = stage.add("proraso", None)
    root.location = (0.04, -H / 2, 0)
    lid = cap(stage, plastic)
    lid.rotation_mode = "ZYX"
    lid.rotation_euler = (0, math.radians(90), math.radians(23))
    lid.location = (LENGTH + DOME - 0.03, 0, D / 2)
    for part in (body(stage, paint), shoulder(stage, enamel), lid):
        part.parent = root

    stage.shoot("proraso", (0, 0, W, H), bleed=1.0, shadow=1.2)


SHOTS = {"proraso": proraso}
