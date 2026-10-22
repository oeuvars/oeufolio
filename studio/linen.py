"""The surface the badge hangs on: a length of light yellow European linen, washed and laid flat on the copy stand. Run
from the repository root:

    blender -b --factory-startup -P studio/linen.py -- [--scale 0.5] [--samples 64] [--proof DIR]
    blender -b --factory-startup -P studio/linen.py -- --edge
    blender -b --factory-startup -P studio/linen.py -- --shadow [--samples 1024] [--proof DIR]

The cloth is a plain weave, one over and one under, of wet-spun flax yarn, dyed a pale butter yellow.

- Each yarn is its own: it wanders off straight, swells into slubs and thins between them, as flax yarn does, and no
  two are quite the same tone. Its fibres run along it at a slight twist, and it is round, so it is darker down its
  edges than along its crown, and darker where it dips under the yarn it crosses.
- The gaps between yarns show the board under the cloth.
- Shives, the brown splinters of the flax stalk the scutching left in, are spun into the odd yarn, and a few stray
  fibres lie loose over the face.
- Washing left the cloth wrinkled: long soft ridges and shorter crinkles, which the octabox rakes.

All of it is painted here and given to Cycles as the cloth's colour and relief. Nothing repeats.

Writes public/objects/linen.avif, the whole plate; with --edge, linen-edge.png, the mask the page cuts the strip
with; with --shadow, linen-shadow.png, the shadow the cut cloth leaves on the page beyond it. Blender writes those two
as PNG; make them the WebP the page asks for after:

    uv run studio/fit.py public/objects/linen-edge.png public/objects/linen-shadow.png
"""

import argparse
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "desk"))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

from mathutils import Quaternion  # noqa: E402
from paint import blur, cloud, linear, ramp, streaks  # noqa: E402
from stage import ASSETS, BOX_IN_ROOM, BOX_ON_STAND, GAIN, ROOM, ROOM_ROLL, Stage, shoulder  # noqa: E402

OUT = os.path.join(ROOT, "public", "objects")
WIDTH, HEIGHT = 36.0, 24.0  # the plate the page shows, in em
MARGIN = 0.6  # the cloth runs on past the frame
PITCH = (0.05, 0.052)  # how far apart the warp yarns (running down) and the weft yarns (across) are, in em
YARN = (0.041, 0.043)  # how wide a warp and a weft yarn are where they are neither slub nor thin
ROUND = 0.42  # how high a yarn stands, for its width
UNDULATE = 0.009  # how far a yarn rises over the yarn it crosses, and dips under the next, in em
PPE = 220  # pixels to the em of the painted maps: about four times what the page shows, ten to a yarn
COLOURS = ["#ffeba3", "#fce596", "#fff0b3", "#f9e08e", "#fee99f", "#fbe49a"]  # the yarns, pale to deeper
SHIVE = "#7b6440"  # the flax stalk's splinters
BOARD = "#cdb366"  # the board under the cloth, seen through the gaps
STEP = 0.04  # the pitch of the cloth's mesh, in em, for its wrinkles
EXPOSURE = 0.95
EYE = 60.0  # how high above the cloth the lens is, in em


def wobble(rng, s, scale, amount):
    """A smooth wander along a yarn, s in em: a few sines of random phase, the widest scale longest."""
    out = np.zeros_like(s)
    for k in range(4):
        out += np.sin(2 * math.pi * s / (scale / 2**k) + rng.uniform(0, 2 * math.pi)) / 2**k
    return amount * out / 1.875


class Yarn:
    """One yarn: its line, its width and slubs along it, its tone, and where it goes over and under."""

    def __init__(self, index, warp, at, seed):
        rng = np.random.default_rng(seed)
        self.index, self.warp, self.seed = index, warp, seed
        pitch, wide = (PITCH[0], YARN[0]) if warp else (PITCH[1], YARN[1])
        self.at = at + rng.normal(0, 0.05 * pitch)
        self.wide = wide * rng.uniform(0.9, 1.08)
        tone = linear(COLOURS[rng.integers(len(COLOURS))])
        self.colour = tone * rng.normal(1, 0.045)
        # Slubs: thick lengths where the drafting let more fibre through, and thin ones between, unevenly spread.
        span = (HEIGHT if warp else WIDTH) + 2 * MARGIN
        count = rng.poisson(span / 1.8)
        self.slubs = np.column_stack((
            rng.uniform(-MARGIN, span - MARGIN, count),
            rng.uniform(0.12, 0.9, count),
            np.where(rng.random(count) < 0.8, rng.uniform(0.2, 0.6, count), -rng.uniform(0.15, 0.3, count)),
            rng.normal(0, 0.07, count),
        ))
        self.crossings = None

    def _smooth(self, s, scale, amount, k):
        rng = np.random.default_rng(self.seed * 100 + k)
        return wobble(rng, s, scale, amount)

    def slub(self, s, column):
        """The slubs' swelling (column 2) or their change of tone (column 3) at s."""
        out = np.zeros_like(s)
        for s0, length, swell, tone in self.slubs:
            t = np.clip(1 - np.abs(s - s0) / (length / 2), 0, 1)
            out = out + (swell, tone)[column - 2] * t * t * (3 - 2 * t)
        return out

    def half(self, s):
        return self.wide / 2 * (1 + self._smooth(s, 0.9, 0.08, 1) + self.slub(s, 2))

    def centre(self, s):
        return self.at + self._smooth(s, 4.0, 0.006, 2) + self._smooth(s, 0.5, 0.0015, 3)

    def paint(self, S, A):
        """The yarn over a band of the maps, at s along it and a across it (arrays that broadcast, rows across the
        yarn and columns along it): its height, cover, colour and roughness."""
        half = self.half(S)
        d = A - self.centre(S)
        inside = 1 - (d / half) ** 2
        profile = np.sqrt(np.clip(inside, 0, 1))
        t = np.interp(S, self.crossings, np.arange(len(self.crossings)))
        over = np.cos(math.pi * (t + self.index + (0 if self.warp else 1)))
        height = UNDULATE * over + ROUND * half * profile
        # The yarn's edge, antialiased over a pixel.
        cover = np.clip(0.5 + (half - np.abs(d)) * PPE, 0, 1)

        rows, cols = np.broadcast_shapes(np.shape(S), np.shape(A))
        seed = self.seed * 10
        # Its fibres: fine lines along it, turned a little by the yarn's twist, and coarser streaks of tone.
        fibre = streaks((rows, cols), seed + 1, length=0.25 * PPE, width=0.6)
        shear = (np.arange(cols) * 0.15).astype(int)
        fibre = fibre[(np.arange(rows)[:, None] + shear[None, :]) % rows, np.arange(cols)[None, :]]
        tone = 1 + 0.05 * np.tanh(streaks((rows, cols), seed + 2, length=1.5 * PPE, width=2.0))
        tone = tone * (1 + self._smooth(S, 2.0, 0.035, 4) + self.slub(S, 3))
        # Round and set down among its neighbours: darker down its sides and where it dips under the next yarn.
        cavity = (0.62 + 0.38 * profile**0.6) * (0.72 + 0.28 * ((1 + over) / 2) ** 0.7)
        rgb = self.colour[None, None, :] * (tone * (1 + 0.04 * fibre) * cavity)[..., None]
        height = height + 0.002 * np.clip(fibre, -2.5, 2.5) * profile
        rough = 0.82 - 0.14 * profile * (0.5 + 0.5 * over)
        return height, cover, rgb, rough


def cloth():
    """The warp yarns down the cloth and the weft yarns across it, each going over and under the others in turn."""
    x0, y0 = -MARGIN, -MARGIN
    w, h = WIDTH + 2 * MARGIN, HEIGHT + 2 * MARGIN
    warp = [Yarn(i, True, x0 + (i + 0.5) * PITCH[0], 1000 + i) for i in range(int(w / PITCH[0]) + 1)]
    weft = [Yarn(j, False, y0 + (j + 0.5) * PITCH[1], 5000 + j) for j in range(int(h / PITCH[1]) + 1)]
    for yarn in warp:
        yarn.crossings = np.array([other.centre(yarn.at) for other in weft])
    for yarn in weft:
        yarn.crossings = np.array([other.centre(yarn.at) for other in warp])
    return warp, weft


def segments(H, RGB, xs, ys, seed, count, length, width, colour, strength, rise, bend, along):
    """Short lines laid over the face: shives spun into the yarns (straight, along a yarn) or stray fibres (curled,
    any way). Each is a few runs long, `width` em wide, painted `colour` at up to `strength`, standing `rise` em."""
    rng = np.random.default_rng(seed)
    step = 1 / PPE
    for _ in range(count):
        points = [(rng.uniform(xs[0], xs[-1]), rng.uniform(ys[0], ys[-1]))]
        turn = (rng.integers(2) * math.pi / 2 + rng.normal(0, 0.08)) if along else rng.uniform(0, 2 * math.pi)
        total = length * rng.uniform(0.3, 1.0)
        for _ in range(4):
            points.append((points[-1][0] + total / 4 * math.cos(turn), points[-1][1] + total / 4 * math.sin(turn)))
            turn += rng.normal(0, bend)
        px, py = np.array(points).T
        pad = 3 * width
        c0, c1 = max(int((px.min() - pad - xs[0]) / step), 0), min(int((px.max() + pad - xs[0]) / step) + 2, len(xs))
        r0, r1 = max(int((py.min() - pad - ys[0]) / step), 0), min(int((py.max() + pad - ys[0]) / step) + 2, len(ys))
        if c1 <= c0 or r1 <= r0:
            continue
        X, Y = xs[None, c0:c1], ys[r0:r1, None]
        near = np.full((r1 - r0, c1 - c0), np.inf)
        for (ax, ay), (bx, by) in zip(points, points[1:]):
            dx, dy = bx - ax, by - ay
            t = np.clip(((X - ax) * dx + (Y - ay) * dy) / (dx * dx + dy * dy), 0, 1)
            near = np.minimum(near, np.hypot(X - ax - t * dx, Y - ay - t * dy))
        half = width / 2 * rng.uniform(0.6, 1.2)
        ink = strength * rng.uniform(0.5, 1.0) * np.clip(0.5 + (half - near) * PPE, 0, 1)
        RGB[r0:r1, c0:c1] = RGB[r0:r1, c0:c1] * (1 - ink[..., None]) + colour[None, None, :] * ink[..., None]
        H[r0:r1, c0:c1] = np.maximum(H[r0:r1, c0:c1], H[r0:r1, c0:c1] + rise * ink)


def maps(proof=None):
    """The cloth's face as maps over the whole plate and its margin: colour and cover, and relief and roughness."""
    warp, weft = cloth()
    x0, y0 = -MARGIN, -MARGIN
    cols, rows = math.ceil((WIDTH + 2 * MARGIN) * PPE), math.ceil((HEIGHT + 2 * MARGIN) * PPE)
    xs = (x0 + (np.arange(cols) + 0.5) / PPE).astype(np.float32)
    ys = (y0 + (np.arange(rows) + 0.5) / PPE).astype(np.float32)
    H = np.full((rows, cols), -1.0, dtype=np.float32)
    C = np.zeros((rows, cols), dtype=np.float32)
    RGB = np.zeros((rows, cols, 3), dtype=np.float32)
    R = np.full((rows, cols), 0.85, dtype=np.float32)
    for yarn in warp + weft:
        reach = yarn.wide * 1.2
        lines = xs if yarn.warp else ys
        lo, hi = np.searchsorted(lines, yarn.at - reach), np.searchsorted(lines, yarn.at + reach)
        if yarn.warp:
            # Rows across the yarn and columns along it, so the yarn's band is turned on its side.
            height, cover, rgb, rough = yarn.paint(ys[None, :], xs[lo:hi, None])
            height, cover, rough, rgb = height.T, cover.T, rough.T, rgb.transpose(1, 0, 2)
            cut = (slice(None), slice(lo, hi))
        else:
            height, cover, rgb, rough = yarn.paint(xs[None, :], ys[lo:hi, None])
            cut = (slice(lo, hi), slice(None))
        on = (height > H[cut]) & (cover > 0)
        mix = np.where(on, cover, 0)
        RGB[cut] = RGB[cut] * (1 - mix[..., None]) + rgb * mix[..., None]
        R[cut] = np.where(on, rough, R[cut])
        H[cut] = np.where(on, height, H[cut])
        C[cut] = np.maximum(C[cut], cover)

    # The whole cloth a little uneven in tone, as a washed and dried length is.
    small = cloud((rows // 8 + 1, cols // 8 + 1), 7, falloff=2.0)
    mottle = np.repeat(np.repeat(small, 8, axis=0), 8, axis=1)[:rows, :cols]
    RGB *= (1 + 0.025 * mottle)[..., None]
    area = WIDTH * HEIGHT
    segments(H, RGB, xs, ys, 11, round(0.15 * area), 0.08, 0.006, linear(SHIVE), 0.8, 0.004, 0.05, True)
    segments(H, RGB, xs, ys, 12, round(0.1 * area), 0.03, 0.008, linear("#5e4a2c"), 0.6, 0.006, 0.05, True)
    segments(H, RGB, xs, ys, 13, round(0.25 * area), 0.35, 0.004, linear("#f6eecb"), 0.55, 0.012, 0.5, False)
    H = np.where(C > 0, H, H[C > 0].min())
    RGB = np.where(C[..., None] > 0, RGB / np.maximum(C, 1e-3)[..., None], linear(BOARD))
    if proof:
        np.save(os.path.join(proof, "linen-colour.npy"), RGB[:600, :900])
    return RGB, C, H, R, xs, ys


def image(name, pixels, colour=False):
    """An 8-bit image of a map, rows from the top. The colour one is sRGB."""
    rows, cols = pixels.shape[:2]
    img = bpy.data.images.new(name, cols, rows, alpha=True)
    img.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    img.alpha_mode = "CHANNEL_PACKED"
    img.pixels.foreach_set((pixels[::-1].astype(np.float32) / 255).ravel())
    img.pack()
    return img


def wrinkles(X, Y, seed, count, reach, height, width, turn):
    """Wrinkles washing left: curving runs each up to `reach` em long, as ridges or troughs up to `height` em,
    rounded, `width` em either side."""
    rng = np.random.default_rng(seed)
    step, x0, y0 = X[0, 1] - X[0, 0], X[0, 0], Y[0, 0]
    rows, cols = X.shape
    out = np.zeros_like(X)
    for _ in range(count):
        corners = [(rng.uniform(x0, X[0, -1]), rng.uniform(y0, Y[-1, 0]))]
        heading = rng.uniform(0, 2 * math.pi)
        for _ in range(rng.integers(3, 7)):
            run = reach / 4 * rng.uniform(0.5, 1.0)
            corners.append((corners[-1][0] + run * math.cos(heading), corners[-1][1] + run * math.sin(heading)))
            heading += rng.normal(0, turn)
        rise = height * rng.uniform(0.3, 1.0) * (1 if rng.random() < 0.7 else -0.6)
        spread = width * rng.uniform(0.7, 1.3)
        cx, cy = np.array(corners).T
        pad = 3 * spread
        c0, c1 = max(int((cx.min() - pad - x0) / step), 0), min(int((cx.max() + pad - x0) / step) + 2, cols)
        r0, r1 = max(int((cy.min() - pad - y0) / step), 0), min(int((cy.max() + pad - y0) / step) + 2, rows)
        if c1 <= c0 or r1 <= r0:
            continue
        PX, PY = X[r0:r1, c0:c1], Y[r0:r1, c0:c1]
        near = np.full_like(PX, np.inf)
        along = np.zeros_like(PX)
        total = 0.0
        for (ax, ay), (bx, by) in zip(corners, corners[1:]):
            dx, dy = bx - ax, by - ay
            t = np.clip(((PX - ax) * dx + (PY - ay) * dy) / (dx * dx + dy * dy), 0, 1)
            d = np.hypot(PX - ax - t * dx, PY - ay - t * dy)
            closer = d < near
            near = np.where(closer, d, near)
            along = np.where(closer, total + t * math.hypot(dx, dy), along)
            total += math.hypot(dx, dy)
        # Strongest in the middle of its length, dying away at either end.
        fade = np.sin(math.pi * np.clip(along / total, 0, 1)) ** 0.7
        out[r0:r1, c0:c1] += rise * fade * np.exp(-((near / spread) ** 2))
    return out


def lay(stage, proof=None):
    RGB, C, H, R, xs, ys = maps(proof)
    lo, hi = float(H.min()), float(H.max())
    srgb = np.where(RGB <= 0.0031308, 12.92 * RGB, 1.055 * np.clip(RGB, 0, None) ** (1 / 2.4) - 0.055)
    colour = np.round(np.clip(np.dstack((srgb, C)), 0, 1) * 255).astype(np.uint8)
    del srgb, RGB
    zero = np.zeros_like(C)
    data = np.round(np.clip(np.dstack(((H - lo) / (hi - lo), R, zero, zero)), 0, 1) * 255).astype(np.uint8)
    del H, R, C, zero
    tex_w, tex_h = xs[-1] - xs[0] + 1 / PPE, ys[-1] - ys[0] + 1 / PPE
    x0, y0 = xs[0] - 0.5 / PPE, ys[0] - 0.5 / PPE

    mat = bpy.data.materials.new("linen")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes["Principled BSDF"]
    place = nodes.new("ShaderNodeTexCoord")
    found = []
    for img in (image("linen-colour", colour, colour=True), image("linen-data", data)):
        node = nodes.new("ShaderNodeTexImage")
        node.image = img
        node.interpolation = "Cubic"
        node.extension = "EXTEND"
        links.new(place.outputs["UV"], node.inputs["Vector"])
        found.append(node)
    del colour, data
    split = nodes.new("ShaderNodeSeparateColor")
    links.new(found[1].outputs["Color"], split.inputs["Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.0
    bump.inputs["Distance"].default_value = hi - lo
    links.new(split.outputs["Red"], bump.inputs["Height"])
    links.new(found[0].outputs["Color"], shader.inputs["Base Color"])
    links.new(found[0].outputs["Alpha"], shader.inputs["Alpha"])
    links.new(split.outputs["Green"], shader.inputs["Roughness"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    # Linen has a soft lustre off its flax fibres, along the yarns' crowns.
    shader.inputs["Sheen Weight"].default_value = 0.35
    shader.inputs["Sheen Roughness"].default_value = 0.45
    shader.inputs["Specular IOR Level"].default_value = 0.3

    # The cloth's mesh: flat but for the wrinkles, with the maps laid over it.
    gx = np.arange(-MARGIN, WIDTH + MARGIN + STEP, STEP)
    gy = np.arange(-MARGIN, HEIGHT + MARGIN + STEP, STEP)
    X, Y = np.meshgrid(gx, gy)
    area = WIDTH * HEIGHT
    Z = wrinkles(X, Y, 21, round(0.06 * area), 5.0, 0.09, 0.32, 0.25)
    Z += wrinkles(X, Y, 22, round(0.35 * area), 1.4, 0.025, 0.09, 0.4)
    Z += 0.06 * blur(cloud(X.shape, 23, falloff=2.4), 0.4 / STEP)
    rows, cols = X.shape
    index = np.arange(rows * cols).reshape(rows, cols)
    faces = np.column_stack((index[:-1, :-1].ravel(), index[1:, :-1].ravel(), index[1:, 1:].ravel(), index[:-1, 1:].ravel()))
    verts = np.column_stack((X.ravel(), -Y.ravel(), Z.ravel()))
    mesh = bpy.data.meshes.new("linen")
    mesh.from_pydata(verts.tolist(), [], faces[:, ::-1].tolist())
    loops = np.empty(len(mesh.loops), dtype=np.int32)
    mesh.loops.foreach_get("vertex_index", loops)
    uv = np.column_stack(((X.ravel() - x0) / tex_w, 1 - (Y.ravel() - y0) / tex_h))
    mesh.uv_layers.new(name="UVMap").data.foreach_set("uv", uv[loops].ravel())
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.materials.append(mat)
    stage.add("linen", mesh)

    board = bpy.data.meshes.new("board")
    under = float(Z.min()) - 0.03
    board.from_pydata([(-20, 20, under), (60, 20, under), (60, -50, under), (-20, -50, under)], [], [(0, 1, 2, 3)])
    paint = bpy.data.materials.new("board")
    paint.use_nodes = True
    paint.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*linear(BOARD), 1)
    paint.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    board.materials.append(paint)
    stage.add("board", board)
    return float(Z.mean())


EDGE = (16, 1600)  # the cut edge's mask, in CSS px: TEAR_WIDTH and TEAR_LENGTH in SiteShell, down which it repeats
EDGE_DENSITY = 2  # pixels of the mask to the CSS px
EDGE_PITCH = 2.6  # how far apart the weft yarns are where the page shows the cloth, in CSS px
WARP_PITCH = 2.5  # how far apart the warp yarns are, across the cloth, in CSS px
RADIUS = 1.0  # a yarn's radius, in CSS px
TWIST = 7.0  # how far along a yarn its plies take to go once round it, in CSS px
THICK = 1.6  # how thick the cloth is, in CSS px: 0.35 mm, at EDGE_PITCH to a weft yarn of 0.5 mm
LAYERS = 6  # sheets of the cloth stacked through its thickness, so its cut stands as tall as the cloth
OPEN = 0.12  # how much light the weave lets straight through its gaps
SCATTER = 0.25  # how much of the light its yarns take they pass on through, scattered
PEEL = 26.0  # how far in from the cut the cloth starts to lift off the page where it curls, in CSS px
SHADOW_FRAME = (-4.0, 40.0)  # the render across the edge's mask, in CSS px from its left: in under the cloth, out over the page
SHADOW_PAST = 120.0  # how far the render runs on past either end of the mask's length, for what crosses its ends
SHADOW_DENSITY = 4  # pixels of the render to the CSS px
# The plate paints each yarn's tone straight; built ply by ply, the plies light each other and deepen it. Their dye is
# taken this much paler (as a power of each channel), measured so the fringe matches the plate on the page.
PALE = 0.7
PAPER = (234.7, 231.8, 224.2)  # the letter's handmade sheet (likes-paper.avif) on average, which the linen lies over


class Fray:
    """The strip's edge as scissors and handling leave linen, drawn once for the mask the page cuts the cloth with
    (edge) and for the render of what lies past it (shadow), so the two meet. Lengths in CSS px, x across the mask
    from its left, y down it, z up off the page. It repeats down the strip without a seam.

    - The blades cut in snips, each a little off the last, so the cut runs in short straight lengths that turn where
      one snip met the next.
    - Along some stretches handling has shaken the outermost warp yarn, or two, out of the weave. There the woven
      cloth ends that much further in, and the weft yarns those warps held run on free to the cut: a fringe, each
      yarn still waved from going over and under, its plies untwisting and its fibres splaying at the cut end.
    - Elsewhere the wefts were cut just past the last warp, and only their ends tuft out.
    - Here and there a shaken-out warp lies loose over its fringe, and stray fibres lie on the page along the edge."""

    def __init__(self, seed=71):
        rng = np.random.default_rng(seed)
        width, self.length = EDGE
        length = self.length
        ys = np.concatenate(([0.0], np.cumsum(rng.uniform(40, 90, round(length / 65)))))
        self.ys = ys * length / ys[-1]
        xs = rng.normal(0, 0.7, len(ys)) + np.cumsum(rng.normal(0, 0.5, len(ys)))
        xs = xs - np.linspace(0, xs[-1] - xs[0], len(ys))
        self.line = width - 9.0 + np.clip(xs - xs.mean(), -2.2, 2.2)
        self.gaps = []
        at = rng.uniform(0, 60)
        while at < length - 30:
            span = rng.uniform(15, 90)
            if rng.random() < 0.45:
                self.gaps.append((at, min(span, length - at - 10), 2 if rng.random() < 0.15 else 1))
            at += span + rng.uniform(10, 60)
        # Where the cut edge curls up off the page, along much of its length and by as much as a millimetre.
        self.curls = [(rng.uniform(0, length), rng.uniform(25, 90), rng.gamma(2.0, 0.9)) for _ in range(24)]
        self.rng = rng

    def cut(self, y):
        return np.interp(np.asarray(y) % self.length, self.ys, self.line)

    def lost(self, y):
        """How many warp yarns have come out of the weave at y, easing from one count to the next over a yarn."""
        y = np.asarray(y, dtype=np.float64)
        out = np.zeros_like(y)
        for at, span, count in self.gaps:
            s = (y - at) % self.length
            inside = np.clip(np.minimum(s, span - s) / 2.0, 0, 1)
            out = np.maximum(out, count * inside * inside * (3 - 2 * inside))
        return out

    def body(self, y):
        """Where the woven cloth ends: at the cut, or as many warps in from it as have come out."""
        return self.cut(y) - WARP_PITCH * self.lost(y)

    def lift(self, x, y):
        """How far the cloth's underside stands off the page: a little everywhere, as washed linen rests on its yarns'
        crowns and its cockle, and more where it curls."""
        y = np.asarray(y, dtype=np.float64)
        rise = np.full_like(y, 0.4)
        for at, spread, height in self.curls:
            away = (y - at + self.length / 2) % self.length - self.length / 2
            rise = rise + height * np.exp(-((away / spread) ** 2))
        inward = np.clip((np.asarray(x) - (self.body(y) - PEEL)) / PEEL, 0, 1)
        return rise * inward * inward * (3 - 2 * inward)

    def mask(self):
        """The woven cloth, solid to the left of its edge and clear past it, at EDGE_DENSITY."""
        over = 4
        density = EDGE_DENSITY * over
        width, length = EDGE
        X = (np.arange(width * density)[None, :] + 0.5) / density
        Y = (np.arange(length * density) + 0.5) / density
        mask = np.clip(0.5 + (self.body(Y)[:, None] - X) * density, 0, 1).astype(np.float32)
        return mask.reshape(length * EDGE_DENSITY, over, width * EDGE_DENSITY, over).mean(axis=(1, 3))

    def strands(self):
        """Every ply and fibre past the woven cloth, as (points, radii, tone): the fringe's wefts and the tufted
        ends, the loose warps and the stray fibres. Points run from the root, which lies in under the cloth."""
        rng = np.random.default_rng(171)
        out = []
        rows = round(self.length / EDGE_PITCH)
        pitch = self.length / rows
        for j in range(rows):
            y = (j + 0.5) * pitch + rng.normal(0, 0.12 * pitch)
            root, tip = float(self.body(y)), float(self.cut(y))
            if tip - root > 0.8:
                tip += rng.normal(0, 0.35) + (rng.uniform(1.5, 5) if rng.random() < 0.06 else 0)
                splay = min(rng.uniform(0.8, 1.8), 0.7 * (tip - root))
            elif rng.random() < 0.55:
                tip += rng.uniform(0.1, 0.7)
                splay = tip - root + 0.6
            else:
                continue
            s = np.arange(root - 1.5, tip + 1.2, 0.2)
            free = np.clip(s - root, 0, None)
            lean, bend = rng.normal(0, 0.08), rng.normal(0, 0.12)
            phase = rng.uniform(0, 2 * math.pi)
            # It rises out of the cloth's middle and comes down onto the page within a yarn or two, waved.
            top = float(self.lift(root, y)) + THICK / 2
            z = RADIUS + (top - RADIUS) * np.exp(-free / 1.5) + 0.22 * np.sin(math.pi * free / WARP_PITCH + phase) * np.clip(free, 0, 1)
            centre = np.column_stack((s, y + lean * free + bend * free**2 / 4 + 0.12 * np.sin(math.pi * free / WARP_PITCH), z))
            tone = int(rng.integers(len(COLOURS)))
            out += [(p, r, tone) for p, r in self.yarn(centre, tip - (root - 1.5), splay, rng)]
        # The warps shaken out, lying loose over their fringe for a length.
        for at, span, count in self.gaps:
            if rng.random() > 0.45:
                continue
            y0 = at + rng.uniform(0, 0.3) * span
            y1 = y0 + rng.uniform(0.4, 0.9) * (at + span - y0)
            t = np.arange(y0, y1, 0.2)
            x = self.cut(t) - WARP_PITCH * (count - 0.5) + 0.5 * np.sin((t - y0) / rng.uniform(9, 20)) + rng.normal(0, 0.3)
            z = 1.9 * RADIUS + 0.2 * np.sin(math.pi * (t - y0) / EDGE_PITCH)
            centre = np.column_stack((x, t, z))
            tone = int(rng.integers(len(COLOURS)))
            out += [(p, r, tone) for p, r in self.yarn(centre, y1 - y0, rng.uniform(1.0, 2.0), rng)]
        # Stray fibres, out from under the cloth's edge and lying on the page.
        for _ in range(round(self.length / 7)):
            y = rng.uniform(0, self.length)
            x0 = float(self.body(y)) - rng.uniform(0.3, 1.5)
            steps = np.linspace(0, 1, 30)
            angle = rng.normal(0, 0.7) + rng.normal(0, 1.2) * steps + np.cumsum(rng.normal(0, 0.08, 30))
            reach = rng.uniform(1.5, 6)
            px = x0 + np.cumsum(np.cos(angle)) * reach / 30
            py = y + np.cumsum(np.sin(angle)) * reach / 30
            pz = 0.08 + (THICK * 0.6) * np.exp(-np.clip(px - x0, 0, None) / 0.8)
            radius = rng.uniform(0.04, 0.08)
            out.append((np.column_stack((px, py, pz)), np.full(30, radius) * (1 - 0.5 * steps), int(rng.integers(len(COLOURS)))))
        # The ends near the top and foot of the length again past the other end, so the repeat has no seam.
        shifted = []
        for points, radii, tone in out:
            for dy in (-self.length, self.length):
                moved = points + (0, dy, 0)
                if (moved[:, 1] > -SHADOW_PAST - 10).any() and (moved[:, 1] < self.length + SHADOW_PAST + 10).any():
                    shifted.append((moved, radii, tone))
        return out + shifted

    @staticmethod
    def yarn(centre, nominal, splay, rng):
        """A yarn along a line, as its plies twisted round it: a core and six round it, each turning once a TWIST.
        Toward the end, over splay, the twist lets go, the plies part and end raggedly, and fibres come off them.
        nominal is how far along the line the yarn runs; the line goes on a little past, for fibres to run out on."""
        step = np.linalg.norm(np.diff(centre, axis=0), axis=1)
        run = np.concatenate(([0.0], np.cumsum(step)))
        tangent = np.gradient(centre, axis=0)
        tangent /= np.linalg.norm(tangent, axis=1, keepdims=True)
        side = np.cross(tangent, (0.0, 0.0, 1.0))
        side /= np.maximum(np.linalg.norm(side, axis=1, keepdims=True), 1e-6)
        up = np.cross(side, tangent)
        loose = np.clip((run - (nominal - splay)) / splay, 0, 1)
        turn = 2 * math.pi * np.concatenate(([0.0], np.cumsum((1 - loose[1:]) * step))) / TWIST
        out = []
        for i in range(7):
            ring = 0.0 if i == 0 else 0.62 * RADIUS
            angle = turn + i * 2 * math.pi / 6 + rng.normal(0, 0.1)
            drift = rng.normal(0, 1, 2) * rng.uniform(0.4, 1.2)
            spread = ring * (1 + 0.9 * loose**1.5)
            across = spread * np.cos(angle) + drift[0] * loose**2
            over = spread * np.sin(angle) + 0.5 * drift[1] * loose**2
            points = centre + side * across[:, None] + up * over[:, None]
            end = nominal - rng.uniform(0, 0.45 * splay)
            thin = np.clip((run - (end - 0.4 * splay)) / (0.4 * splay), 0, 1)
            radius = 0.36 * RADIUS * (1 - 0.6 * thin)
            points[:, 2] = np.maximum(points[:, 2], radius)
            keep = run <= end
            if keep.sum() > 1:
                out.append((points[keep], radius[keep]))
            # Fibres working loose off it where it is free, running on past its end.
            for _ in range(rng.integers(1, 4)):
                start = nominal - splay * rng.uniform(0.3, 1.0)
                stop = min(end + rng.uniform(0.2, 1.1), run[-1])
                pick = (run >= start) & (run <= stop)
                if pick.sum() < 2:
                    continue
                away = run[pick] - start
                wander = rng.normal(0, 1, 3) * 0.35
                fibre = points[pick] + np.outer(away, wander) + np.outer(np.sin(away * rng.uniform(2, 5)), rng.normal(0, 0.08, 3))
                thick = rng.uniform(0.05, 0.1)
                fibre[:, 2] = np.maximum(fibre[:, 2], thick)
                out.append((fibre, np.full(len(fibre), thick)))
        return out


def edge():
    """Writes the mask the page cuts the cloth with: the woven cloth only, as everything past it is rendered."""
    mask = Fray().mask()
    rows, cols = mask.shape
    img = bpy.data.images.new("linen-edge", cols, rows, alpha=True)
    img.colorspace_settings.name = "Non-Color"
    pixels = np.zeros((rows, cols, 4), dtype=np.float32)
    pixels[..., 3] = mask
    img.pixels.foreach_set(pixels[::-1].ravel())
    img.filepath_raw = os.path.join(OUT, "linen-edge.png")
    img.file_format = "PNG"
    img.save()
    print(f"EDGE {cols}x{rows}")


def yarn_material(name, colour):
    """A yarn of the cloth: its dye, the flax's soft lustre, and some light let through, as thin flax does."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*colour, 1)
    shader.inputs["Roughness"].default_value = 0.8
    shader.inputs["Sheen Weight"].default_value = 0.35
    shader.inputs["Sheen Roughness"].default_value = 0.45
    shader.inputs["Specular IOR Level"].default_value = 0.3
    through = nodes.new("ShaderNodeBsdfTranslucent")
    through.inputs["Color"].default_value = (*colour, 1)
    mix = nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = SCATTER
    links.new(shader.outputs["BSDF"], mix.inputs[1])
    links.new(through.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], nodes["Material Output"].inputs["Surface"])
    return material, mix


def shadow(samples, proof=None):
    """What lies past the woven cloth's edge and the shadow it all leaves on the letter's paper, for the page to lay
    under the strip's linen and out over the strip beyond. The cloth is THICK thick, lets OPEN of the light through
    its gaps and scatters SCATTER of the rest through its yarns, so its shadow is light and warm. It lies flat on the
    page in most places and curls off it in a few. Past it the fringe and loose yarns are built ply by ply (Fray).
    All of it is under the copy stand's studio light (stage.py's room and octabox, as studio/tabcut uses). Three
    renders: the page bare, the page under the cloth (the two divided give the shadow, colour by colour), and the
    yarns alone, developed as the plate is. Writes public/objects/linen-shadow.png: the yarns over the shadow,
    laid for PAPER, SHADOW_FRAME's right part from the mask's left, the mask's length long."""
    fray = Fray()
    width, length = EDGE
    mask = fray.mask()
    rows, cols = mask.shape
    scene = Stage(OUT, samples=samples).clear()
    scene.render.film_transparent = False
    scene.cycles.transparent_max_bounces = 4 * LAYERS
    scene.cycles.use_adaptive_sampling = False

    # The room, turned so its octabox hangs where the copy stand wants it.
    nodes, links = scene.world.node_tree.nodes, scene.world.node_tree.links
    coord = nodes.new("ShaderNodeTexCoord")
    turn = nodes.new("ShaderNodeMapping")
    aim = BOX_ON_STAND.rotation_difference(BOX_IN_ROOM) @ Quaternion(BOX_ON_STAND, ROOM_ROLL)
    turn.inputs["Rotation"].default_value = aim.to_euler()
    room = nodes.new("ShaderNodeTexEnvironment")
    room.image = bpy.data.images.load(os.path.join(ASSETS, ROOM))
    links.new(coord.outputs["Generated"], turn.inputs["Vector"])
    links.new(turn.outputs["Vector"], room.inputs["Vector"])
    links.new(room.outputs["Color"], nodes["Background"].inputs["Color"])

    page = bpy.data.meshes.new("page")
    page.from_pydata([(-200, 200, 0), (200, 200, 0), (200, -length - 400, 0), (-200, -length - 400, 0)], [], [(0, 1, 2, 3)])
    sheet = bpy.data.materials.new("page")
    sheet.use_nodes = True
    paper = sheet.node_tree.nodes["Principled BSDF"]
    paper.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1)
    paper.inputs["Roughness"].default_value = 0.9
    paper.inputs["Specular IOR Level"].default_value = 0.2
    page.materials.append(sheet)
    page_obj = bpy.data.objects.new("page", page)
    scene.collection.objects.link(page_obj)

    # The woven cloth: the mask on each sheet, solid to its left, its length repeating down the strip. Each sheet
    # lets through what the weave's gaps do, shared out over the sheets, and less the more steeply light crosses it,
    # as a ray at a low angle runs through that much more cloth.
    img = bpy.data.images.new("linen-cut", cols, rows, alpha=True)
    img.colorspace_settings.name = "Non-Color"
    img.alpha_mode = "CHANNEL_PACKED"
    pixels = np.ones((rows, cols, 4), dtype=np.float32)
    pixels[..., 3] = mask
    img.pixels.foreach_set(pixels[::-1].ravel())
    img.pack()
    tone = np.mean([linear(c) for c in COLOURS], axis=0) ** PALE
    cloth, woven = yarn_material("cloth", tone)
    nodes, links = cloth.node_tree.nodes, cloth.node_tree.links
    where = nodes.new("ShaderNodeTexCoord")
    split = nodes.new("ShaderNodeSeparateXYZ")
    across = nodes.new("ShaderNodeMath")
    across.operation = "DIVIDE"
    across.inputs[1].default_value = width
    # Held off the mask's outer columns, where the length's repeat would wrap the solid left onto the clear right.
    held = nodes.new("ShaderNodeClamp")
    held.inputs["Min"].default_value = 1.5 / cols
    held.inputs["Max"].default_value = 1 - 1.5 / cols
    down = nodes.new("ShaderNodeMath")
    down.operation = "DIVIDE"
    down.inputs[1].default_value = length
    uv = nodes.new("ShaderNodeCombineXYZ")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = img
    texture.interpolation = "Linear"
    texture.extension = "REPEAT"
    facing = nodes.new("ShaderNodeLayerWeight")
    cosine = nodes.new("ShaderNodeMath")
    cosine.operation = "SUBTRACT"
    cosine.inputs[0].default_value = 1.0
    least = nodes.new("ShaderNodeMath")
    least.operation = "MAXIMUM"
    least.inputs[1].default_value = 0.02
    path = nodes.new("ShaderNodeMath")
    path.operation = "DIVIDE"
    path.inputs[0].default_value = 1.0
    passed = nodes.new("ShaderNodeMath")
    passed.operation = "POWER"
    passed.inputs[0].default_value = OPEN ** (1 / LAYERS)
    stopped = nodes.new("ShaderNodeMath")
    stopped.operation = "SUBTRACT"
    stopped.inputs[0].default_value = 1.0
    solid = nodes.new("ShaderNodeMath")
    solid.operation = "MULTIPLY"
    links.new(facing.outputs["Facing"], cosine.inputs[1])
    links.new(cosine.outputs[0], least.inputs[0])
    links.new(least.outputs[0], path.inputs[1])
    links.new(path.outputs[0], passed.inputs[1])
    links.new(passed.outputs[0], stopped.inputs[1])
    links.new(stopped.outputs[0], solid.inputs[1])
    clear = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(where.outputs["Object"], split.inputs["Vector"])
    links.new(split.outputs["X"], across.inputs[0])
    links.new(across.outputs[0], held.inputs["Value"])
    links.new(held.outputs["Result"], uv.inputs["X"])
    links.new(split.outputs["Y"], down.inputs[0])
    links.new(down.outputs[0], uv.inputs["Y"])
    links.new(uv.outputs["Vector"], texture.inputs["Vector"])
    links.new(texture.outputs["Alpha"], solid.inputs[0])
    links.new(solid.outputs[0], mix.inputs["Fac"])
    links.new(clear.outputs["BSDF"], mix.inputs[1])
    links.new(woven.outputs["Shader"], mix.inputs[2])
    links.new(mix.outputs["Shader"], nodes["Material Output"].inputs["Surface"])

    gx = np.arange(SHADOW_FRAME[0] - 60, width + 0.5, 0.5)
    gy = np.arange(-SHADOW_PAST - 40, length + SHADOW_PAST + 40, 2.0)
    X, Y = np.meshgrid(gx, gy)
    bottom = fray.lift(X, Y)
    rows_g, cols_g = X.shape
    index = np.arange(rows_g * cols_g).reshape(rows_g, cols_g)
    faces = np.column_stack((index[:-1, :-1].ravel(), index[:-1, 1:].ravel(), index[1:, 1:].ravel(), index[1:, :-1].ravel()))
    hidden = []
    for layer in range(LAYERS):
        verts = np.column_stack((X.ravel(), -Y.ravel(), (bottom + THICK * (layer + 0.5) / LAYERS).ravel()))
        mesh = bpy.data.meshes.new(f"cloth-{layer}")
        mesh.vertices.add(len(verts))
        mesh.vertices.foreach_set("co", verts.astype(np.float32).ravel())
        mesh.loops.add(faces.size)
        mesh.loops.foreach_set("vertex_index", faces.astype(np.int32).ravel())
        mesh.polygons.add(len(faces))
        mesh.polygons.foreach_set("loop_start", np.arange(0, faces.size, 4, dtype=np.int32))
        mesh.update()
        mesh.materials.append(cloth)
        obj = bpy.data.objects.new(f"cloth-{layer}", mesh)
        obj.visible_camera = False
        scene.collection.objects.link(obj)
        hidden.append(obj)

    # The yarns past it, each ply a round strand.
    strands = bpy.data.curves.new("fray", "CURVE")
    strands.dimensions = "3D"
    strands.bevel_depth = 1.0
    strands.bevel_resolution = 2
    strands.use_fill_caps = True
    for i, colour in enumerate(COLOURS):
        strands.materials.append(yarn_material(f"yarn-{i}", linear(colour) ** PALE)[0])
    count = 0
    for points, radii, shade in fray.strands():
        spline = strands.splines.new("POLY")
        spline.points.add(len(points) - 1)
        co = np.column_stack((points[:, 0], -points[:, 1], points[:, 2], np.ones(len(points))))
        spline.points.foreach_set("co", co.astype(np.float32).ravel())
        spline.points.foreach_set("radius", np.asarray(radii, dtype=np.float32))
        spline.material_index = shade
        spline.use_smooth = True
        count += 1
    yarns = bpy.data.objects.new("fray", strands)
    scene.collection.objects.link(yarns)
    print(f"STRANDS {count}")

    x0, x1 = SHADOW_FRAME
    y0, y1 = -SHADOW_PAST, length + SHADOW_PAST
    optics = bpy.data.cameras.new("overhead")
    optics.type = "ORTHO"
    optics.ortho_scale = max(x1 - x0, y1 - y0)
    optics.clip_end = 1000
    camera = bpy.data.objects.new("overhead", optics)
    camera.location = ((x0 + x1) / 2, -(y0 + y1) / 2, 300)
    scene.collection.objects.link(camera)
    scene.camera = camera
    scene.render.resolution_x = round((x1 - x0) * SHADOW_DENSITY)
    scene.render.resolution_y = round((y1 - y0) * SHADOW_DENSITY)
    scene.render.resolution_percentage = 100

    raw = os.path.join(tempfile.gettempdir(), "linen-shadow.exr")

    def expose():
        scene.render.filepath = raw
        bpy.ops.render.render(write_still=True)
        image = bpy.data.images.load(raw)
        out = np.empty(image.size[0] * image.size[1] * 4, dtype=np.float32)
        image.pixels.foreach_get(out)
        shape = (image.size[1], image.size[0], 4)
        bpy.data.images.remove(image)
        os.remove(raw)
        return out.reshape(shape)[::-1]

    for obj in hidden + [yarns]:
        obj.hide_render = True
    bare = expose()[..., :3]
    for obj in hidden + [yarns]:
        obj.hide_render = False
    yarns.visible_camera = False
    shade = expose()[..., :3]
    # The yarns alone, over the letter's paper, which lights them from below as it would.
    yarns.visible_camera = True
    page_obj.visible_camera = False
    paper.inputs["Base Color"].default_value = (*linear("#%02x%02x%02x" % tuple(round(c) for c in PAPER)), 1)
    scene.render.film_transparent = True
    lit = expose()

    # The shadow, colour by colour, as the colour and cover that give it over PAPER.
    ratio = np.clip(shade / np.maximum(bare, 1e-4), 0, 1)
    under = np.array(PAPER, dtype=np.float32) / 255
    under_linear = np.where(under <= 0.04045, under / 12.92, ((under + 0.055) / 1.055) ** 2.4)
    dimmed = under_linear * ratio
    target = np.where(dimmed <= 0.0031308, dimmed * 12.92, 1.055 * dimmed ** (1 / 2.4) - 0.055)
    dark = np.clip(((under - target) / under).max(axis=-1), 0, 1)
    tint = np.clip((target - under * (1 - dark[..., None])) / np.maximum(dark, 1e-4)[..., None], 0, 1)
    # The yarns, developed as the plate is (stage.py's develop), laid over it.
    cover = np.clip(lit[..., 3], 0, 1)
    light = lit[..., :3] * GAIN * 2.0**EXPOSURE
    colour = shoulder(light / np.maximum(cover, 1e-6)[..., None])
    colour = np.where(colour <= 0.0031308, colour * 12.92, 1.055 * np.clip(colour, 0, None) ** (1 / 2.4) - 0.055)
    total = cover + dark * (1 - cover)
    rgb = (colour * cover[..., None] + tint * (dark * (1 - cover))[..., None]) / np.maximum(total, 1e-6)[..., None]

    top, left = round(SHADOW_PAST * SHADOW_DENSITY), round(-x0 * SHADOW_DENSITY)
    tile = np.dstack((rgb, total))[top : top + length * SHADOW_DENSITY, left:]
    tile = np.clip(tile + (np.random.default_rng(0).random(tile.shape, dtype=np.float32) - 0.5) / 255, 0, 1)
    rows, cols = tile.shape[:2]
    img = bpy.data.images.new("linen-shadow", cols, rows, alpha=True)
    img.alpha_mode = "STRAIGHT"
    img.pixels.foreach_set(tile[::-1].astype(np.float32).ravel())
    img.filepath_raw = os.path.join(proof or OUT, "linen-shadow.png")
    img.file_format = "PNG"
    img.save()
    beside = tile[:, round((width - 8) * SHADOW_DENSITY) : round((width - 4) * SHADOW_DENSITY), 3]
    print(f"SHADOW {cols}x{rows}, cover one to five px past the cut: mean {float(beside.mean()):.3f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--proof")
    parser.add_argument("--edge", action="store_true", help="only write the mask of the cloth's cut edge")
    parser.add_argument("--shadow", action="store_true", help="only write the shadow the cut cloth leaves on the page")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    if args.edge:
        return edge()
    if args.shadow:
        if args.proof:
            os.makedirs(args.proof, exist_ok=True)
        return shadow(args.samples, args.proof)
    if args.proof:
        os.makedirs(args.proof, exist_ok=True)
    stage = Stage(OUT, args.proof, scale=args.scale, samples=args.samples)
    stage.clear()
    level = lay(stage, args.proof)
    stage.shoot("linen", (0, 0, WIDTH, HEIGHT), exposure=EXPOSURE, lens=False, mat=False, eye=EYE, level=level, sharp=2.0)


if __name__ == "__main__":
    main()
