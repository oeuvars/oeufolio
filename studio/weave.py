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
UPRIGHT = (2.0, 1.8)  # the upright strips' pitch and width, in em
ACROSS = (1.9, 1.45)  # the strips across: pitch and width
LIFT = 0.08  # how far a strip rises over the strip it crosses, and dips under the next, in em
THICK = 0.03  # how thick a strip is
PAD = 0.1  # how far past a strip's edge its ribbon runs, for fibres the fraying leaves sticking out
BAND = 2.2  # how wide a strip's band of the painted atlas is, in em
PPE = 64  # pixels to the em of the painted atlas
STRAW = ["#c99f63", "#be9156", "#d4b07a", "#b0834b", "#946537", "#d8b985"]  # the strips' colours, pale to brown
BOARD = "#0d0a07"  # the board behind the weave
EXPOSURE = 0.0
EYE = 60.0  # how high above the weave the lens is, in em


def wobble(rng, s, scale, amount):
    """A smooth wander along a strip, s in em: a few sines of random phase, the widest scale longest."""
    out = np.zeros_like(s)
    for k in range(4):
        out += np.sin(2 * math.pi * s / (scale / 2**k) + rng.uniform(0, 2 * math.pi)) / 2**k
    return amount * out / 1.875


def heights(at, crossings, signs):
    """A strip's height along it, at positions `at` in em: LIFT over each crossing whose sign is 1, under each
    whose sign is -1, eased between them."""
    k = np.clip(np.searchsorted(crossings, at) - 1, 0, len(crossings) - 2)
    a, b = crossings[k], crossings[k + 1]
    t = np.clip((at - a) / (b - a), 0, 1)
    ease = (1 - np.cos(math.pi * t)) / 2
    return LIFT * (signs[k] * (1 - ease) + signs[k + 1] * ease)


class Strip:
    """One strip of the weave: its line, its width and its shape along its length, and its band of the atlas."""

    def __init__(self, index, upright, at, start, length, crossings, signs, seed):
        rng = np.random.default_rng(seed)
        self.index, self.upright, self.start, self.length = index, upright, start, length
        self.seed = seed
        width = (UPRIGHT if upright else ACROSS)[1]
        self.at = at + rng.normal(0, 0.06)
        self.lean = rng.normal(0, 0.005)
        self.wide = width * rng.uniform(0.86, 1.08)
        self.cup = rng.uniform(0.02, 0.05) if upright else rng.uniform(0.0, 0.03)
        self.colour = linear(STRAW[rng.integers(len(STRAW))]) * rng.uniform(0.92, 1.05)
        self.crossings, self.signs = crossings, signs

    def _smooth(self, s, scale, amount, k):
        """The strip's own wobble k, the same each time it is asked for."""
        rng = np.random.default_rng(self.seed * 100 + k)
        return wobble(rng, s, scale, amount)

    def width(self, s):
        return self.wide * (1 + self._smooth(s, 9.0, 0.04, 1))

    def centre(self, s):
        return self.at + self.lean * (s - self.start) + self._smooth(s, 16.0, 0.08, 2)

    def twist(self, s):
        return self._smooth(s, 6.0, 0.025, 3)

    def mesh(self, band_row, atlas_w, atlas_h, step=0.08, across=12):
        """The strip's ribbon: rows of vertices along it, each across it, in page em (y down) and height."""
        s = np.arange(self.start, self.start + self.length + step, step)
        v = np.linspace(-1, 1, across + 1)
        S, V = np.meshgrid(s, v, indexing="ij")
        half = self.width(S) / 2 + PAD
        a = V * half
        c = self.centre(S)
        lift = heights(S, self.crossings, self.signs)
        # Cupped across, highest along its middle, and turned a little about its length.
        z = lift + self.cup * (1 - (a / (self.width(S) / 2)) ** 2) + self.twist(S) * a
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

    def paint(self):
        """The strip's face, as its band of the atlas: colour and cover, and height and roughness, rows across it
        from one edge and columns along it."""
        rows, cols = int(BAND * PPE), math.ceil(self.length * PPE) + 1
        A = (np.arange(rows)[:, None] + 0.5) / PPE - BAND / 2
        S = self.start + np.arange(cols)[None, :] / PPE
        half = self.width(S) / 2
        inside = half - np.abs(A)  # em in from the nearer edge
        seed = self.seed * 10
        # A leaf's fibres run its whole length: fine striations, nearly even, with no figure as wood has.
        # Each striation is dead straight and runs on for em, fading in and out along it.
        fine = streaks((rows, cols), seed + 1, length=24.0 * PPE, width=0.4)
        fine = fine * (0.75 + 0.25 * streaks((rows, cols), seed + 8, length=2.0 * PPE, width=0.6))
        coarse = streaks((rows, cols), seed + 2, length=30.0 * PPE, width=1.2)
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
        height = 0.5 * np.clip(fine, -2.5, 2.5) + 0.4 * coarse - 0.8 * grooves
        rough = 0.5 - 0.08 * bright + 0.12 * grooves + 0.06 * stain
        return np.dstack((rgb, cover)), np.dstack((height, rough, np.zeros_like(rough), np.zeros_like(rough)))


def weave():
    """Both sets of strips, the uprights over and under the strips across in turn."""
    x0, y0 = -MARGIN, -MARGIN
    w, h = WIDTH + 2 * MARGIN, HEIGHT + 2 * MARGIN
    cols = np.arange(x0 - UPRIGHT[0], x0 + w + UPRIGHT[0], UPRIGHT[0]) + UPRIGHT[0] / 2
    rows = np.arange(y0 - ACROSS[0], y0 + h + ACROSS[0], ACROSS[0]) + ACROSS[0] / 2
    strips = []
    for i, x in enumerate(cols):
        signs = np.array([1 if (i + j) % 2 == 0 else -1 for j in range(len(rows))])
        strips.append(Strip(len(strips), True, x, y0 - 0.5, h + 1, rows, signs, 100 + i))
    for j, y in enumerate(rows):
        signs = np.array([-1 if (i + j) % 2 == 0 else 1 for i in range(len(cols))])
        strips.append(Strip(len(strips), False, y, x0 - 0.5, w + 1, cols, signs, 300 + j))
    return strips


def image(name, pixels):
    rows, cols = pixels.shape[:2]
    img = bpy.data.images.new(name, cols, rows, alpha=True, float_buffer=True)
    img.colorspace_settings.name = "Non-Color"
    img.alpha_mode = "CHANNEL_PACKED"
    img.pixels.foreach_set(pixels[::-1].astype(np.float32).ravel())
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
    bump.inputs["Distance"].default_value = 0.004
    links.new(split.outputs["Red"], bump.inputs["Height"])
    tangent = nodes.new("ShaderNodeTangent")
    tangent.direction_type = "UV_MAP"
    links.new(maps[0].outputs["Color"], shader.inputs["Base Color"])
    links.new(maps[0].outputs["Alpha"], shader.inputs["Alpha"])
    links.new(split.outputs["Green"], shader.inputs["Roughness"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(tangent.outputs["Tangent"], shader.inputs["Tangent"])
    shader.inputs["Anisotropic"].default_value = 0.5
    shader.inputs["Specular IOR Level"].default_value = 0.45
    return mat


def lay(stage, proof=None):
    strips = weave()
    band = int(BAND * PPE)
    atlas_w = math.ceil(max(s.length for s in strips) * PPE) + 1
    atlas_h = band * len(strips)
    colour = np.zeros((atlas_h, atlas_w, 4), dtype=np.float32)
    data = np.zeros((atlas_h, atlas_w, 4), dtype=np.float32)
    meshes = []
    for strip in strips:
        face, finish = strip.paint()
        r0 = strip.index * band
        colour[r0 : r0 + band, : face.shape[1]] = face
        data[r0 : r0 + band, : finish.shape[1]] = finish
        meshes.append(strip.mesh(r0, atlas_w, atlas_h))
    if proof:
        np.save(os.path.join(proof, "weave-atlas.npy"), colour[: band * 4, :1200])
    mat = material(image("weave-colour", colour), image("weave-data", data))
    del colour, data

    verts, faces, uvs, offset = [], [], [], 0
    for v, f, uv in meshes:
        verts.append(v)
        faces.append(f + offset)
        uvs.append(uv)
        offset += len(v)
    verts, faces, uvs = np.vstack(verts), np.vstack(faces), np.vstack(uvs)
    mesh = bpy.data.meshes.new("weave")
    mesh.from_pydata(verts.tolist(), [], faces.tolist())
    loops = np.empty(len(mesh.loops), dtype=np.int32)
    mesh.loops.foreach_get("vertex_index", loops)
    mesh.uv_layers.new(name="UVMap").data.foreach_set("uv", uvs[loops].ravel())
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.materials.append(mat)
    obj = stage.add("weave", mesh)
    body = obj.modifiers.new("body", "SOLIDIFY")
    body.thickness = THICK
    body.offset = -1

    board = bpy.data.meshes.new("board")
    board.from_pydata([(-20, 20, 0), (60, 20, 0), (60, -50, 0), (-20, -50, 0)], [], [(0, 1, 2, 3)])
    paint = bpy.data.materials.new("board")
    paint.use_nodes = True
    paint.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*linear(BOARD), 1)
    paint.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
    board.materials.append(paint)
    stage.add("board", board)


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
    lay(stage, args.proof)
    stage.shoot("weave", (0, 0, WIDTH, HEIGHT), exposure=EXPOSURE, lens=False, mat=False, eye=EYE, level=0.4, sharp=1.6)


if __name__ == "__main__":
    main()
