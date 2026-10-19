"""The surface the badge hangs on: a length of light yellow European linen, washed and laid flat on the copy stand. Run
from the repository root:

    blender -b --factory-startup -P studio/linen.py -- [--scale 0.5] [--samples 64] [--proof DIR]

The cloth is a plain weave, one over and one under, of wet-spun flax yarn, dyed a pale butter yellow.

- Each yarn is its own: it wanders off straight, swells into slubs and thins between them, as flax yarn does, and no
  two are quite the same tone. Its fibres run along it at a slight twist, and it is round, so it is darker down its
  edges than along its crown, and darker where it dips under the yarn it crosses.
- The gaps between yarns show the board under the cloth.
- Shives, the brown splinters of the flax stalk the scutching left in, are spun into the odd yarn, and a few stray
  fibres lie loose over the face.
- Washing left the cloth wrinkled: long soft ridges and shorter crinkles, which the octabox rakes.

All of it is painted here and given to Cycles as the cloth's colour and relief. Nothing repeats.

Writes public/objects/linen.avif, the whole plate.
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--proof")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    if args.proof:
        os.makedirs(args.proof, exist_ok=True)
    stage = Stage(OUT, args.proof, scale=args.scale, samples=args.samples)
    stage.clear()
    level = lay(stage, args.proof)
    stage.shoot("linen", (0, 0, WIDTH, HEIGHT), exposure=EXPOSURE, lens=False, mat=False, eye=EYE, level=level, sharp=2.0)


if __name__ == "__main__":
    main()
