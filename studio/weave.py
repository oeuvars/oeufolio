"""The surface the badge hangs on: a mat woven of split palm strips, photographed on the copy stand. Run from the
repository root:

    blender -b --factory-startup -P studio/weave.py -- [--scale 0.5] [--samples 64] [--proof DIR]

The weave is the reference's (a basket's side, close up): a plain weave, one over and one under, of flat strips
split from a dried leaf. Upright strips, wide and cupped, run down the plate; narrower ones run across it.

- Each strip is a ribbon of its own, built here: it rises over the strip it crosses and dips under the next, cups
  across its width, twists a little and wanders off straight, and no two are the same width or colour.
- Its face is painted: fibres down its length, in ridges and grooves, pale and brown from strip to strip and along
  each one, its edges frayed where the knife split it, and here and there a crack along the grain.
- Behind the weave is a dark board, which the gaps between strips show.

The strips cast real shadows where one lies over another, and onto the board through the gaps. Nothing repeats.

Writes public/objects/weave.avif, the whole plate.
"""

import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "desk"))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

from paint import blur, cloud, linear, ramp, streaks  # noqa: E402
from stage import Stage  # noqa: E402

OUT = os.path.join(ROOT, "public", "objects")
WIDTH, HEIGHT = 36.0, 24.0  # the plate the page shows, in em
MARGIN = 1.5  # the weave runs on past the frame, so no strip ends in it
# The strips are made at the sizes below, in strip units, and the whole weave is shrunk to SIZE em to the unit.
SIZE = 0.2
UPRIGHT = (2.0, 1.7)  # the upright strips' pitch and width, in strip units
ACROSS = (1.9, 1.45)  # the strips across: pitch and width
LIFT = 0.11  # how far a strip rises over the strip it crosses, and dips under the next
THICK = 0.03  # how thick a strip is
PAD = 0.1  # how far past a strip's edge its ribbon runs, for fibres the fraying leaves sticking out
BAND = 2.2  # how wide a strip's band of the painted atlas is
PPE = 20  # pixels to the strip unit of the painted atlas: 100 to the em, about twice what the page shows
STRAW = ["#c99f63", "#be9156", "#d4b07a", "#b0834b", "#946537", "#d8b985"]  # the strips' colours, pale to brown
BOARD = "#0d0a07"  # the board behind the weave
EXPOSURE = 0.0
TISSUE_EXPOSURE = 0.4  # the tissue is white paper: shot a little brighter, so it reads white and not grey
TISSUE = "#f8f6f1"  # the tissue paper laid over the weave, with --tissue
TISSUE_COVER = 0.8  # how much of the light the tissue's fibres catch; the rest goes straight through, unscattered
TISSUE_THROUGH = 0.7  # of the light the fibres catch, how much they pass on through the sheet rather than back
TISSUE_STEP = 0.025  # the pitch of the tissue's mesh, in em
EYE = 60.0  # how high above the weave the lens is, in em


def wobble(rng, s, scale, amount):
    """A smooth wander along a strip, s in em: a few sines of random phase, the widest scale longest."""
    out = np.zeros_like(s)
    for k in range(4):
        out += np.sin(2 * math.pi * s / (scale / 2**k) + rng.uniform(0, 2 * math.pi)) / 2**k
    return amount * out / 1.875


def heights(at, crossings, signs, hold):
    """A strip's height along it, at positions `at` in em: LIFT over each crossing whose sign is 1, under each
    whose sign is -1, held level for `hold` of the pitch either side of each, across the strip it crosses, and eased
    between them in the gap."""
    k = np.clip(np.searchsorted(crossings, at) - 1, 0, len(crossings) - 2)
    a, b = crossings[k], crossings[k + 1]
    t = np.clip(((at - a) / (b - a) - hold) / (1 - 2 * hold), 0, 1)
    ease = (1 - np.cos(math.pi * t)) / 2
    return LIFT * (signs[k] * (1 - ease) + signs[k + 1] * ease)


class Strip:
    """One strip of the weave: its line, its width and its shape along its length, and its band of the atlas."""

    def __init__(self, index, upright, at, start, length, crossings, signs, seed):
        rng = np.random.default_rng(seed)
        self.index, self.upright, self.start, self.length = index, upright, start, length
        self.seed = seed
        width = (UPRIGHT if upright else ACROSS)[1]
        self.at = at + rng.normal(0, 0.03)
        self.lean = rng.normal(0, 0.001)
        self.wide = width * rng.uniform(0.86, 1.08)
        self.cup = rng.uniform(0.02, 0.05) if upright else rng.uniform(0.0, 0.03)
        self.colour = linear(STRAW[rng.integers(len(STRAW))]) * rng.uniform(0.92, 1.05)
        self.curl = rng.uniform(-0.015, 0.02)  # its edges, turned up or down as it dried
        self.crossings, self.signs = crossings, signs
        # It stays level across the widest of the strips it crosses, and turns in the gaps between them.
        pitch, crossed = ACROSS if upright else UPRIGHT
        self.hold = min(0.54 * crossed / pitch, 0.45)

    def _smooth(self, s, scale, amount, k):
        """The strip's own wobble k, the same each time it is asked for."""
        rng = np.random.default_rng(self.seed * 100 + k)
        return wobble(rng, s, scale, amount)

    def width(self, s):
        return self.wide * (1 + self._smooth(s, 9.0, 0.04, 1))

    def centre(self, s):
        return self.at + self.lean * (s - self.start) + self._smooth(s, 16.0, 0.05, 2)

    def twist(self, s):
        return self._smooth(s, 6.0, 0.025, 3)

    def mesh(self, band_row, atlas_w, atlas_h, step=0.2, across=8):
        """The strip's ribbon: rows of vertices along it, each across it, in page em (y down) and height."""
        s = np.arange(self.start, self.start + self.length + step, step)
        v = np.linspace(-1, 1, across + 1)
        S, V = np.meshgrid(s, v, indexing="ij")
        half = self.width(S) / 2 + PAD
        a = V * half
        c = self.centre(S)
        lift = heights(S, self.crossings, self.signs, self.hold)
        z = lift + self.shape(S, a)
        x, y = (c + a, S) if self.upright else (S, c + a)
        verts = np.column_stack((x.ravel(), -y.ravel(), z.ravel() + 0.4))
        n, m = len(s), across + 1
        index = np.arange(n * m).reshape(n, m)
        faces = np.column_stack((index[:-1, :-1].ravel(), index[1:, :-1].ravel(), index[1:, 1:].ravel(), index[:-1, 1:].ravel()))
        if not self.upright:
            faces = faces[:, ::-1]
        u = (S - self.start) * PPE / atlas_w
        w = 1 - (band_row + (a + BAND / 2) * PPE) / atlas_h
        return verts, faces, np.column_stack((u.ravel(), w.ravel()))

    def shape(self, s, a):
        """How far the strip's face stands off its line, at s along it and a across it: cupped, highest along its
        middle, its edges curled, turned a little about its length, and rippled along it where it dried unevenly."""
        across = np.clip(a / (self.width(s) / 2), -1.2, 1.2)
        ripple = self._smooth(s, 1.6, 0.012, 5) + self._smooth(s + 3.1 * across, 0.9, 0.005, 6)
        return self.cup * (1 - across**2) + self.curl * across**4 + self.twist(s) * a + ripple

    def paint(self):
        """The strip's face, as its band of the atlas: colour and cover, and height and roughness, rows across it
        from one edge and columns along it."""
        rows, cols = int(BAND * PPE), math.ceil(self.length * PPE) + 1
        A = (np.arange(rows)[:, None] + 0.5) / PPE - BAND / 2
        S = self.start + np.arange(cols)[None, :] / PPE
        half = self.width(S) / 2
        inside = half - np.abs(A)  # em in from the nearer edge
        seed = self.seed * 10
        # A leaf's fibres run its whole length: striations, nearly even, with no figure as wood has. Each is dead
        # straight and runs on a long way, fading in and out along it. They stand up as ridges a pixel or two of
        # the photograph apart, so the face is ribbed and not smooth.
        fine = streaks((rows, cols), seed + 1, length=24.0 * PPE, width=1.0)
        fine = fine * (0.7 + 0.3 * streaks((rows, cols), seed + 8, length=2.0 * PPE, width=1.0))
        ribs = 1 - np.abs(np.tanh(streaks((rows, cols), seed + 9, length=20.0 * PPE, width=2.2)))
        coarse = streaks((rows, cols), seed + 2, length=30.0 * PPE, width=3.0)
        # Pits and specks where the skin of the leaf flaked, all over it.
        pits = ramp(1.6, 3.0, -streaks((rows, cols), seed + 10, length=1.2, width=1.2))
        # Veins: a few fibres darker than the rest, in thin lines, and a few paler ones.
        veins = ramp(2.2, 3.2, streaks((rows, cols), seed + 11, length=12.0 * PPE, width=0.8))
        # Fraying: the edge eaten back by a few hundredths of an em, more in places, along the grain.
        fray = 0.02 + 0.035 * np.clip(streaks((rows, cols), seed + 3, length=0.3 * PPE, width=0.7), 0, None)
        cover = ramp(-0.006, 0.006, inside - fray)
        # A few fibres split off the edge and stand out past it.
        hair = streaks((rows, cols), seed + 4, length=1.2 * PPE, width=0.35)
        cover = np.maximum(cover, ramp(2.9, 3.4, hair) * (inside > -0.08) * (inside < 0.02))
        # Cracks along the grain, ragged, where the strip split as it dried.
        rng = np.random.default_rng(seed + 5)
        crack = np.zeros((rows, cols))
        for _ in range(rng.poisson(self.length / 12)):
            s0 = rng.uniform(self.start, self.start + self.length)
            span = rng.uniform(0.8, 4.0)
            line = rng.uniform(-0.6, 0.6) * self.wide / 2 + 0.03 * np.sin(S * rng.uniform(2, 5))
            along = np.clip(1 - np.abs(S - s0 - span / 2) / (span / 2), 0, 1)
            gap = 0.012 * along**0.5 * (1 + 0.5 * fine.clip(-1, 1))
            crack = np.maximum(crack, ramp(0.004, -0.004, np.abs(A - line) - gap) * (along > 0))
        cover = cover * (1 - crack)

        # Colour: the strip's own, drifting along it, streaked by its fibres, browner in stains, darker at the cut edge.
        drift = self._smooth(S, 9.0, 0.08, 4) + 0.05 * np.tanh(cloud((rows, cols), seed + 6, falloff=1.8, stretch=6.0))
        stain = ramp(0.8, 2.0, cloud((rows, cols), seed + 7, falloff=1.6, stretch=4.0)) * 0.5
        rgb = self.colour[None, None, :] * (1 + drift)[..., None]
        rgb = rgb * (1 - stain[..., None]) + linear("#7a5530")[None, None, :] * stain[..., None]
        grooves = ramp(1.0, 2.4, -fine)
        bright = ramp(1.4, 2.8, fine)
        rgb = rgb * (1 + 0.06 * coarse)[..., None] * (1 - 0.28 * grooves)[..., None]
        rgb = rgb * (1 - bright[..., None] * 0.35) + linear("#ead9b6")[None, None, :] * bright[..., None] * 0.35
        rgb = rgb * (1 - 0.25 * ramp(0.08, 0.0, inside))[..., None]
        rgb = rgb * (1 - 0.5 * blur(crack, 2))[..., None]
        rgb = rgb * (1 - 0.45 * veins[..., None]) + linear("#6b4a2a")[None, None, :] * 0.45 * veins[..., None]
        rgb = rgb * (1 + 0.1 * (ribs - 0.5))[..., None] * (1 - 0.3 * pits)[..., None]
        height = 0.45 * np.clip(fine, -2.5, 2.5) + 1.2 * ribs + 0.3 * coarse - 0.8 * grooves - 1.0 * pits
        rough = 0.66 - 0.06 * bright + 0.1 * grooves + 0.06 * stain + 0.1 * pits
        return np.dstack((rgb, cover)), np.dstack((height, rough, np.zeros_like(rough), np.zeros_like(rough)))


def weave():
    """Both sets of strips, the uprights over and under the strips across in turn."""
    x0, y0 = -MARGIN / SIZE, -MARGIN / SIZE
    w, h = (WIDTH + 2 * MARGIN) / SIZE, (HEIGHT + 2 * MARGIN) / SIZE
    cols = np.arange(x0 - UPRIGHT[0], x0 + w + UPRIGHT[0], UPRIGHT[0]) + UPRIGHT[0] / 2
    rows = np.arange(y0 - ACROSS[0], y0 + h + ACROSS[0], ACROSS[0]) + ACROSS[0] / 2
    strips = []
    for i, x in enumerate(cols):
        signs = np.array([1 if (i + j) % 2 == 0 else -1 for j in range(len(rows))])
        strips.append(Strip(len(strips), True, x, y0 - 0.5, h + 1, rows, signs, 100 + i))
    for j, y in enumerate(rows):
        signs = np.array([-1 if (i + j) % 2 == 0 else 1 for i in range(len(cols))])
        strips.append(Strip(len(strips), False, y, x0 - 0.5, w + 1, cols, signs, 300 + j))
    # Each strip crosses the others where they really are, leaning and wandering, not where they were laid out.
    upright = [s for s in strips if s.upright]
    across = [s for s in strips if not s.upright]
    for strip in upright:
        strip.crossings = np.array([a.centre(strip.centre(a.at)) for a in across])
    for strip in across:
        strip.crossings = np.array([u.centre(strip.centre(u.at)) for u in upright])
    return strips


def image(name, pixels, colour=False):
    """An 8-bit image of an atlas held as bytes, rows from the top. The colour one is sRGB."""
    rows, cols = pixels.shape[:2]
    img = bpy.data.images.new(name, cols, rows, alpha=True)
    img.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    img.alpha_mode = "CHANNEL_PACKED"
    img.pixels.foreach_set((pixels[::-1].astype(np.float32) / 255).ravel())
    img.pack()
    return img


def material(colour, data):
    """The strips' face: the atlas's colour and cover, its fibres as bump, and a sheen drawn out along the grain."""
    mat = bpy.data.materials.new("strip")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes["Principled BSDF"]
    place = nodes.new("ShaderNodeTexCoord")
    maps = []
    for img in (colour, data):
        node = nodes.new("ShaderNodeTexImage")
        node.image = img
        node.interpolation = "Cubic"
        node.extension = "EXTEND"
        links.new(place.outputs["UV"], node.inputs["Vector"])
        maps.append(node)
    split = nodes.new("ShaderNodeSeparateColor")
    links.new(maps[1].outputs["Color"], split.inputs["Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.0
    bump.inputs["Distance"].default_value = 0.08 * SIZE
    links.new(split.outputs["Red"], bump.inputs["Height"])
    tangent = nodes.new("ShaderNodeTangent")
    tangent.direction_type = "UV_MAP"
    links.new(maps[0].outputs["Color"], shader.inputs["Base Color"])
    links.new(maps[0].outputs["Alpha"], shader.inputs["Alpha"])
    links.new(split.outputs["Green"], shader.inputs["Roughness"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(tangent.outputs["Tangent"], shader.inputs["Tangent"])
    shader.inputs["Anisotropic"].default_value = 0.3
    shader.inputs["Specular IOR Level"].default_value = 0.35
    return mat


def lay(stage, proof=None):
    strips = weave()
    band = int(BAND * PPE)
    atlas_w = math.ceil(max(s.length for s in strips) * PPE) + 1
    atlas_h = band * len(strips)
    # Held as bytes: the atlas of a fine weave is too big to hold as floats. The colour is stored as sRGB, the
    # height about the middle of the range.
    colour = np.zeros((atlas_h, atlas_w, 4), dtype=np.uint8)
    data = np.zeros((atlas_h, atlas_w, 4), dtype=np.uint8)
    meshes = []
    for strip in strips:
        face, finish = strip.paint()
        face[..., :3] = np.where(face[..., :3] <= 0.0031308, 12.92 * face[..., :3], 1.055 * np.clip(face[..., :3], 0, None) ** (1 / 2.4) - 0.055)
        finish[..., 0] = 0.5 + finish[..., 0] / 8
        r0 = strip.index * band
        colour[r0 : r0 + band, : face.shape[1]] = np.round(np.clip(face, 0, 1) * 255)
        data[r0 : r0 + band, : finish.shape[1]] = np.round(np.clip(finish, 0, 1) * 255)
        meshes.append(strip.mesh(r0, atlas_w, atlas_h))
    if proof:
        np.save(os.path.join(proof, "weave-atlas.npy"), colour[: band * 4, :1200])
    mat = material(image("weave-colour", colour, colour=True), image("weave-data", data))
    del colour, data

    verts, faces, uvs, offset = [], [], [], 0
    for v, f, uv in meshes:
        verts.append(v)
        faces.append(f + offset)
        uvs.append(uv)
        offset += len(v)
    verts, faces, uvs = np.vstack(verts) * SIZE, np.vstack(faces), np.vstack(uvs)
    mesh = bpy.data.meshes.new("weave")
    mesh.from_pydata(verts.tolist(), [], faces.tolist())
    loops = np.empty(len(mesh.loops), dtype=np.int32)
    mesh.loops.foreach_get("vertex_index", loops)
    mesh.uv_layers.new(name="UVMap").data.foreach_set("uv", uvs[loops].ravel())
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.materials.append(mat)
    obj = stage.add("weave", mesh)
    body = obj.modifiers.new("body", "SOLIDIFY")
    body.thickness = THICK * SIZE
    body.offset = -1

    board = bpy.data.meshes.new("board")
    board.from_pydata([(-20, 20, 0), (60, 20, 0), (60, -50, 0), (-20, -50, 0)], [], [(0, 1, 2, 3)])
    paint = bpy.data.materials.new("board")
    paint.use_nodes = True
    paint.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*linear(BOARD), 1)
    paint.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
    board.materials.append(paint)
    stage.add("board", board)
    return strips


def widest(a, reach):
    """The highest of each point's neighbours up to `reach` pixels off along either axis."""
    for axis in (0, 1):
        out = a.copy()
        for k in range(1, reach + 1):
            out = np.maximum(out, np.roll(a, k, axis=axis))
            out = np.maximum(out, np.roll(a, -k, axis=axis))
        a = out
    return a


def top(strips, X, Y):
    """The height of the weave's top face over each point of a grid laid out as np.meshgrid lays it (strip units,
    y down), or 0 where only the board is. Each strip is only looked for in the rows or columns it can reach."""
    out = np.zeros_like(X)
    for strip in strips:
        lines = X[0] if strip.upright else Y[:, 0]
        reach = strip.wide * 0.6 + abs(strip.lean) * strip.length + 0.2
        near = np.flatnonzero(np.abs(lines - strip.at) < reach)
        if not len(near):
            continue
        cut = (slice(None), near) if strip.upright else (near, slice(None))
        s, across = (Y[cut], X[cut]) if strip.upright else (X[cut], Y[cut])
        a = across - strip.centre(s)
        z = 0.4 + heights(s, strip.crossings, strip.signs, strip.hold) + strip.shape(s, a)
        out[cut] = np.where(np.abs(a) < strip.width(s) / 2, np.maximum(out[cut], z), out[cut])
    return out


def creases(X, Y, seed, count, reach, height, width):
    """Creases pressed into a sheet by crumpling it: zig-zags of straight runs, each run up to `reach` em long and
    turned off the last at an angle, as paper folds. Each stands up in a ridge `height` em high at most, coming to a
    sharp crest and spreading `width` em either side."""
    rng = np.random.default_rng(seed)
    step, x0, y0 = X[0, 1] - X[0, 0], X[0, 0], Y[0, 0]
    rows, cols = X.shape
    out = np.zeros_like(X)
    for _ in range(count):
        # The crease's corners first, then the patch of the sheet it reaches.
        corners = [(rng.uniform(x0, X[0, -1]), rng.uniform(y0, Y[-1, 0]))]
        turn = rng.uniform(0, 2 * math.pi)
        for _ in range(rng.integers(2, 6)):
            run = reach * rng.uniform(0.3, 1.0)
            corners.append((corners[-1][0] + run * math.cos(turn), corners[-1][1] + run * math.sin(turn)))
            turn += rng.choice([-1, 1]) * rng.uniform(0.35, 1.2)
        rise, spread = height * rng.uniform(0.3, 1.0), width * rng.uniform(0.7, 1.3)
        cx, cy = np.array(corners).T
        pad = 4 * spread
        c0, c1 = max(int((cx.min() - pad - x0) / step), 0), min(int((cx.max() + pad - x0) / step) + 2, cols)
        r0, r1 = max(int((cy.min() - pad - y0) / step), 0), min(int((cy.max() + pad - y0) / step) + 2, rows)
        if c1 <= c0 or r1 <= r0:
            continue
        PX, PY = X[r0:r1, c0:c1], Y[r0:r1, c0:c1]
        crease = np.zeros_like(PX)
        for (ax, ay), (bx, by) in zip(corners, corners[1:]):
            dx, dy = bx - ax, by - ay
            t = np.clip(((PX - ax) * dx + (PY - ay) * dy) / (dx * dx + dy * dy), 0, 1)
            crease = np.maximum(crease, rise * np.exp(-np.hypot(PX - ax - t * dx, PY - ay - t * dy) / spread))
            rise *= rng.uniform(0.6, 1.1)
        out[r0:r1, c0:c1] += crease
    return out


def tissue(stage, strips):
    """A sheet of tissue paper laid over the weave, after it was crumpled and smoothed out again. Most of it lies
    down on the strips' tops, bridging the narrow gaps between them; along the creases the crumpling left it stands
    up in thin sharp ridges, a network of long ones and finer ones between, and here and there it lifts off in a
    soft bubble. Its fibres catch most of the light and scatter it, on through the sheet and back, so the weave
    shows through crisp where the paper touches it and goes milky where the paper stands off."""
    x0, y0 = -MARGIN, -MARGIN
    w, h = WIDTH + 2 * MARGIN, HEIGHT + 2 * MARGIN
    xs, ys = np.arange(x0, x0 + w + TISSUE_STEP, TISSUE_STEP), np.arange(y0, y0 + h + TISSUE_STEP, TISSUE_STEP)
    X, Y = np.meshgrid(xs, ys)
    per = 1 / TISSUE_STEP
    # Where it rests: the tops of the strips, bridged over the gaps between them, as a sheet with any stiffness lies.
    under = top(strips, X / SIZE, Y / SIZE) * SIZE
    rest = np.maximum(blur(widest(under, round(0.05 * per)), 0.04 * per), under)
    # The creases: long ones from the first crumpling, shorter ones between, and fine crinkles all over.
    area = w * h
    folds = creases(X, Y, 61, round(0.4 * area), 2.5, 0.08, 0.08)
    folds += creases(X, Y, 62, round(2.0 * area), 0.8, 0.03, 0.045)
    folds += creases(X, Y, 63, round(4.0 * area), 0.3, 0.01, 0.03)
    lifts = 0.09 * ramp(0.8, 2.4, blur(cloud(X.shape, 53, falloff=2.2), 0.6 * per))
    Z = rest + 0.002 + folds + lifts

    rows, cols = X.shape
    index = np.arange(rows * cols).reshape(rows, cols)
    faces = np.column_stack((index[:-1, :-1].ravel(), index[1:, :-1].ravel(), index[1:, 1:].ravel(), index[:-1, 1:].ravel()))
    verts = np.column_stack((X.ravel(), -Y.ravel(), Z.ravel()))
    mesh = bpy.data.meshes.new("tissue")
    mesh.from_pydata(verts.tolist(), [], faces[:, ::-1].tolist())
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))

    mat = bpy.data.materials.new("tissue")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    colour = (*linear(TISSUE), 1)
    place = nodes.new("ShaderNodeTexCoord")
    # Its fibres: a fine felt in the paper's face, which the light rakes.
    felt = nodes.new("ShaderNodeTexNoise")
    felt.inputs["Scale"].default_value = 60.0
    felt.inputs["Detail"].default_value = 6.0
    felt.inputs["Roughness"].default_value = 0.7
    links.new(place.outputs["Object"], felt.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.002
    links.new(felt.outputs["Fac"], bump.inputs["Height"])
    face = nodes.new("ShaderNodeBsdfDiffuse")
    face.inputs["Color"].default_value = colour
    through = nodes.new("ShaderNodeBsdfTranslucent")
    through.inputs["Color"].default_value = colour
    for shader in (face, through):
        links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    clear = nodes.new("ShaderNodeBsdfTransparent")
    sheet = nodes.new("ShaderNodeMixShader")
    sheet.inputs[0].default_value = TISSUE_THROUGH
    links.new(face.outputs[0], sheet.inputs[1])
    links.new(through.outputs[0], sheet.inputs[2])
    # The paper is thicker in flocs, where its fibres clumped as it was made, and thinner between.
    flocs = nodes.new("ShaderNodeTexNoise")
    flocs.inputs["Scale"].default_value = 4.0
    flocs.inputs["Detail"].default_value = 8.0
    flocs.inputs["Roughness"].default_value = 0.6
    links.new(place.outputs["Object"], flocs.inputs["Vector"])
    density = nodes.new("ShaderNodeMapRange")
    density.inputs["From Min"].default_value = 0.3
    density.inputs["From Max"].default_value = 0.7
    density.inputs["To Min"].default_value = TISSUE_COVER - 0.07
    density.inputs["To Max"].default_value = TISSUE_COVER + 0.07
    links.new(flocs.outputs["Fac"], density.inputs["Value"])
    seen = nodes.new("ShaderNodeMixShader")
    links.new(density.outputs["Result"], seen.inputs[0])
    links.new(clear.outputs[0], seen.inputs[1])
    links.new(sheet.outputs[0], seen.inputs[2])
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(seen.outputs[0], out.inputs["Surface"])
    mesh.materials.append(mat)
    stage.add("tissue", mesh)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--proof")
    parser.add_argument("--tissue", action="store_true", help="lay tissue paper over the weave")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    if args.proof:
        os.makedirs(args.proof, exist_ok=True)
    stage = Stage(OUT, args.proof, scale=args.scale, samples=args.samples)
    stage.clear()
    strips = lay(stage, args.proof)
    name, exposure = "weave", EXPOSURE
    if args.tissue:
        tissue(stage, strips)
        name, exposure = "weave-tissue", TISSUE_EXPOSURE
    stage.shoot(name, (0, 0, WIDTH, HEIGHT), exposure=exposure, lens=False, mat=False, eye=EYE, level=0.4 * SIZE, sharp=1.6)


if __name__ == "__main__":
    main()
