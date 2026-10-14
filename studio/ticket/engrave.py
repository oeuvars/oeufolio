# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "OpenEXR>=3.3", "scipy"]
# ///
"""Cuts the street (studio/ticket/street.py) into a block for one ink, as a wood engraver would.

    uv run studio/ticket/engrave.py [--proof DIR]

Tone is carried by lines whose width follows how dark the render is there. Their direction follows the
thing they lie on: on the house fronts and the road they run to where the street vanishes, on whatever
faces us they run across, on the sky they are gouged in long strokes. The edges between things are cut as
a black line. Rain is cut through it all: white through the dark, black over the light. Nothing is quite
straight, as nothing cut by hand is.

Writes studio/ticket/art/street-ink.png: white where the block prints, black where it was cut away.
"""

import argparse
import json
import os

import numpy as np
import OpenEXR
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "art")
KIND = {"sky": 0, "facade": 1, "dark": 2, "road": 3, "tram": 4, "bridge": 5, "figure": 6, "wire": 7, "trim": 8, "glass": 9, "pavement": 10}
UP = 2  # the block is cut at this many times the render's size, then brought down, so its edges are clean
LINES = 170  # lines across the picture
PROOF = 700  # the size the other measures here were judged at, in pixels across
HAZE = 0.45  # how far the haze lightens what is furthest away
EXPOSURE = 2.2  # the render is dim: this brings plaster up near white


def passes(path):
    parts = OpenEXR.File(path, separate_channels=True).parts
    found = {}
    for part in parts:
        for name, channel in part.channels.items():
            found[name.split(".", 1)[1]] = channel.pixels.astype(np.float64)
    return found


def enlarge(a, order=1):
    return ndimage.zoom(a, UP, order=order, mode="nearest")


def smooth(x, lo, hi):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def field(shape, seed, sigma):
    """Slow noise of unit deviation, for the hand's unevenness."""
    rng = np.random.default_rng(seed)
    n = ndimage.gaussian_filter(rng.standard_normal(shape), sigma, mode="wrap")
    return n / n.std()


def lines(phase, cover, soft):
    """Coverage of a screen of lines, one per unit of phase, each as wide as cover of its period.
    soft is how much phase one pixel spans, to antialias with."""
    s = np.abs((phase % 1.0) - 0.5) * 2  # 1 at the middle of each line, 0 between
    return np.clip((s - (1 - cover)) / np.maximum(soft * 2, 1e-4) + 0.5, 0, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof")
    args = parser.parse_args()

    p = passes(os.path.join(ART, "street.exr"))
    meta = json.load(open(os.path.join(ART, "street.json")))
    rows, cols = p["Combined.R"].shape
    lum = 0.2126 * p["Combined.R"] + 0.7152 * p["Combined.G"] + 0.0722 * p["Combined.B"]
    tone = np.clip(lum * EXPOSURE, 0, 1) ** (1 / 2.2)
    haze = np.clip(p["Mist.Z"], 0, 1)
    tone = tone * (1 - HAZE * haze) + HAZE * haze
    kind = np.rint(p["Object Index.X"]).astype(int)
    depth = np.where(kind == 0, 1e4, p["Depth.Z"])
    nx, ny, nz = p["Normal.X"], p["Normal.Y"], p["Normal.Z"]

    # Edges, found at the render's size: where one thing meets another, where depth jumps, where a surface turns.
    jump = np.zeros((rows, cols), dtype=bool)
    for axis in (0, 1):
        dk = np.diff(kind, axis=axis, append=np.take(kind, [-1], axis=axis)) != 0
        ld = np.log(np.maximum(depth, 1e-3))
        dd = np.abs(np.diff(ld, axis=axis, append=np.take(ld, [-1], axis=axis))) > 0.035
        dn = sum(np.abs(np.diff(n, axis=axis, append=np.take(n, [-1], axis=axis))) for n in (nx, ny, nz)) > 0.6
        jump |= dk | dd | dn
    k = cols / PROOF
    if k > 1.5:
        jump = ndimage.binary_dilation(jump, iterations=round(k) - 1)
    near = np.clip(1 - haze * 1.3, 0, 1)  # far edges are cut finer and fade into the haze

    # Up to the block's size.
    tone, haze, near = enlarge(tone), enlarge(haze), enlarge(near)
    kind = enlarge(kind, order=0)
    nx, ny, nz = enlarge(nx), enlarge(ny), enlarge(nz)
    edge = enlarge(jump.astype(np.float64))
    R, C = tone.shape
    Y, X = np.mgrid[0:R, 0:C].astype(np.float64)

    # The hand: every line strays a little, slowly.
    X = X + field((R, C), 3, 40 * k) * 1.2 * UP * k
    Y = Y + field((R, C), 4, 40 * k) * 1.2 * UP * k

    pitch = C / LINES
    vx, vy = meta["vanishing"][0] * C, meta["vanishing"][1] * R
    angle = np.arctan2(Y - vy, X - vx)
    radius = np.hypot(X - vx, Y - vy)
    # Lines to the vanishing point, spaced a pitch apart half a frame from it.
    radial = angle * (0.5 * C) / pitch
    radial_soft = (0.5 * C) / pitch / np.maximum(radius, 1.0)
    across = Y / pitch
    up = X / pitch

    raw = np.clip(1 - tone, 0, 1)
    dark = raw
    dark = smooth(dark, 0.22, 0.95)

    side = np.abs(nx) > 0.6  # house fronts, seen along the street
    facing = np.abs(ny) > 0.6  # what faces down the street at us
    flat = nz > 0.6  # the road, pavements, ledges

    ink = np.zeros((R, C))
    # House fronts and the ground: toward the vanishing point.
    run = (side | flat) & ~np.isin(kind, (KIND["sky"], KIND["dark"], KIND["wire"], KIND["figure"]))
    ink = np.where(run, lines(radial, dark, radial_soft), ink)
    # Whatever faces us: straight across.
    face = facing & ~run & ~np.isin(kind, (KIND["sky"], KIND["dark"], KIND["wire"], KIND["figure"]))
    ink = np.where(face, lines(across, dark, 1 / pitch), ink)
    rest = ~(run | face)
    ink = np.where(rest & (kind != KIND["sky"]), lines(across * 0.8 + up * 0.25, dark, 1 / pitch), ink)
    # Where the lines get finer than the block can hold, near the vanishing point, they close up into tone.
    crowd = smooth(radial_soft * 2.5, 0.35, 1.0) * run
    ink = ink * (1 - crowd) + smooth(dark, 0.45, 0.6) * crowd
    # Solid things stay solid: windows and doorways, the coat and umbrella, the wires.
    solid = np.isin(kind, (KIND["dark"], KIND["wire"]))
    ink = np.where(solid, np.maximum(ink, smooth(dark, 0.25, 0.55)), ink)
    # The walker is a silhouette, coat and umbrella alike.
    ink = np.where(kind == KIND["figure"], 1.0, ink)

    # The bridge stands in the haze as steel does: solid, every member a line of its own.
    ink = np.where(kind == KIND["bridge"], smooth(raw, 0.06, 0.16), ink)

    # The sky: an engraver's ruled sky, heaviest at the top and gone before it reaches the roofs.
    sky = kind == KIND["sky"]
    fall = smooth(1 - Y / (0.36 * R), 0.0, 1.0) * 0.42
    ruled = lines(Y / (pitch * 1.1) + field((R, C), 13, 160 * k) * 0.35, fall, 1 / pitch)
    ink = np.where(sky, ruled, ink)

    # Edges, as a black line, thinner and paler with distance.
    outline = ndimage.gaussian_filter(edge, 0.6 * UP * k)
    outline = np.clip(outline * 3.2, 0, 1) * (0.25 + 0.75 * near)
    ink = np.maximum(ink, smooth(outline, 0.25, 0.6))

    # Rain: short streaks leaning a little to the right, cut white through ink and printed black on paper.
    rng = np.random.default_rng(21)
    streak = np.zeros((R, C))
    count = int(R * C / (1500 * UP * UP * k * k))
    xs = rng.uniform(0, C, count)
    ys = rng.uniform(0, R, count)
    lengths = rng.uniform(7, 22, count) * UP * k
    lean = 0.17
    for x0, y0, length in zip(xs, ys, lengths):
        t = np.linspace(0, 1, int(length))
        px = np.clip((x0 + lean * length * t).astype(int), 0, C - 1)
        py = np.clip((y0 + length * t).astype(int), 0, R - 1)
        streak[py, px] = 1
    streak = np.clip(ndimage.gaussian_filter(streak, 0.35 * UP * k) * 2.2, 0, 1)
    streak *= 1 - 0.5 * haze  # thinner far off
    ink = np.where(ink > 0.5, ink * (1 - streak), np.maximum(ink, streak * 0.9))

    # The figure is cut free of what is behind it by a thin white margin, as an engraver keeps a shape
    # from sinking into a dark ground.
    body = ndimage.gaussian_filter((kind == KIND["figure"]).astype(np.float64), 0.5 * UP * k) > 0.5
    margin = ndimage.binary_dilation(body, iterations=int(2.2 * UP * k)) & ~body
    ink = np.where(margin, 0.0, ink)

    # Down to the output's size, with the antialiasing that brings.
    out = ink.reshape(rows, UP, cols, UP).mean(axis=(1, 3))
    image = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    image.save(os.path.join(ART, "street-ink.png"))
    if args.proof:
        Image.fromarray(((1 - np.clip(out, 0, 1)) * 255).astype(np.uint8)).save(os.path.join(args.proof, "street-ink.png"))
    print("engraved", cols, "x", rows)


main()
