"""The surface the badge hangs on: a plate of scuffed stainless steel, photographed on the copy stand. Run from the
repository root:

    blender -b --factory-startup -P studio/steel.py -- [--scale 0.5] [--samples 64] [--proof DIR]

The steel is the reference's (a scratched, grimy steel disc under one soft light): bare metal with no finish, so all
of its look is what it reflects and how its marks break that reflection up.

- Hairline scratches in their thousands, most of them faint, a few deep. Most run one way, as a hand wiping the
  plate drags its grit; the rest go every way. Each is a narrow groove a few thousandths of an em deep, so one wall
  of it catches the light and the other falls away from it, and it shows as a bright line or a dark one.
- Grime: a band of fine dark pits and scuffs, where the plate was worked hardest, dull and dark in the hollows.
- Smudges: soft dull patches, where hands and the air dulled the metal.

All of it is painted here, not read from a scan, so nothing in the plate repeats. The plate is lit by the stand's
studio room, its octabox turned to the top left, through a real lens, so the box's reflection sweeps across the
metal from bright at the top left to dark at the bottom right, as the light falls across the reference.

Writes public/objects/steel.avif, the whole plate.
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
from mathutils import Vector  # noqa: E402

import stage as stage_module  # noqa: E402
from paint import blur, cloud, linear  # noqa: E402
from stage import Stage  # noqa: E402
from stock import Sheet  # noqa: E402

OUT = os.path.join(ROOT, "public", "objects")
WIDTH, HEIGHT = 36.0, 24.0  # the plate the page shows, in em
MARGIN = 1.0  # the metal runs on past the frame, so its edge is never in it
STEEL = "#94bfb9"  # the bare metal's reflectance: a cool steel, as the reference's light leaves it
ROUGH = 0.36
DIRT = "#1d2726"  # what is left in the pits  # the bare metal's: polished once, long since dulled
SCRATCHES = 22000
GRAIN = math.radians(72)  # the way most scratches run, from the page's horizontal
DEEP = 0.0024  # how deep the deepest scratch is, in em
EYE = 40.0  # how high above the plate the lens is, in em
EXPOSURE = -0.7


def smooth(lo, hi, x):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def scratches(shape, ppe, seed):
    """How deep each point of the plate lies in a scratch, from 0 to 1, rows by columns at ppe pixels to the em.
    Each scratch is a groove drawn along a gently bent line, shallow at its ends, and broken here and there where the
    grit skipped."""
    rows, cols = shape
    rng = np.random.default_rng(seed)
    depth = np.zeros(shape)
    for _ in range(SCRATCHES):
        cx, cy = rng.uniform(0, cols / ppe), rng.uniform(0, rows / ppe)
        turn = GRAIN + rng.normal(0, 0.3) if rng.random() < 0.45 else rng.uniform(0, math.pi)
        length = math.exp(rng.uniform(math.log(0.12), math.log(3.5)))
        bend = rng.normal(0, 0.008) * length
        strength = rng.random() ** 4.0  # most are faint
        t = np.linspace(-0.5, 0.5, max(4, int(length * ppe * 2)))
        along, across = np.cos(turn), np.sin(turn)
        offset = bend * (4 * t * t - 1)
        x = (cx + t * length * along - offset * across) * ppe
        y = (cy + t * length * across + offset * along) * ppe
        taper = np.sin(np.pi * (t + 0.5)) ** 0.4
        skips = smooth(-0.6, 0.2, np.sin(t * length * rng.uniform(3, 9) + rng.uniform(0, 6)))
        d = strength * taper * (skips if rng.random() < 0.4 else 1.0)
        ix, iy = np.round(x).astype(int), np.round(y).astype(int)
        inside = (ix >= 0) & (ix < cols) & (iy >= 0) & (iy < rows)
        np.maximum.at(depth, (iy[inside], ix[inside]), d[inside])
    # A groove is a little over a pixel wide, deepest along its middle.
    return np.clip(blur(depth, 0.6) * 2.2, 0, 1)


def plate(stage, proof=None):
    """The plate, laid with its top left MARGIN em above and left of the frame's."""
    w, h = WIDTH + 2 * MARGIN, HEIGHT + 2 * MARGIN
    sheet = Sheet(w, h, STEEL, rough=ROUGH, density=2)
    rows, cols = sheet.height.shape
    ppe = sheet.ppe
    cut = scratches((rows, cols), ppe, 3)

    # Grime: a broad band across the plate, top left to bottom right of its middle, and inside it fine pits.
    X, Y = sheet.X / w, sheet.Y / h
    band = np.exp(-(((X - 0.38) * 0.55 + (Y - 0.42) * -0.83) / 0.16) ** 2)
    patchy = smooth(-0.2, 1.2, cloud((rows, cols), 11, falloff=1.5) + 2.2 * band - 0.9)
    specks = smooth(1.1, 2.1, blur(cloud((rows, cols), 12, falloff=0.2), 0.7) * 2.2)
    scuff = smooth(0.3, 1.8, cloud((rows, cols), 13, falloff=1.0, stretch=3.0))
    pits = np.clip(patchy * (specks + 0.45 * scuff * patchy), 0, 1)

    # Smudges: soft dull patches, some broad, some no bigger than a thumb.
    broad = smooth(0.5, 1.8, blur(cloud((rows, cols), 21, falloff=1.9), 3))
    thumbs = smooth(1.4, 2.4, blur(cloud((rows, cols), 22, falloff=1.2), 2))
    dull = np.clip(0.8 * broad + 0.7 * thumbs, 0, 1)

    mottle = cloud((rows, cols), 31, falloff=1.4)
    shade = (1 + 0.04 * mottle) * (1 - 0.6 * dull)
    # The grime in the pits is dirt, not metal: dark and dull, the colour the metal's oxide and old grease dry to.
    sheet.rgb = linear(STEEL) * shade[..., None] * (1 - pits[..., None]) + linear(DIRT) * pits[..., None]
    sheet.metal[:] = 1.0 - 0.9 * pits
    sheet.rough = ROUGH + 0.45 * pits + 0.08 * dull - 0.06 * cut
    sheet.height = -DEEP * cut - 0.004 * blur(pits, 0.5) + 0.00015 * blur(cloud((rows, cols), 41, falloff=0.8), 0.8)
    if proof:
        np.save(os.path.join(proof, "steel-albedo.npy"), sheet.rgb.astype(np.float32))
    sheet.build(stage, "steel", thickness=0.0, at=(-MARGIN, -MARGIN), step=0.5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--proof")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    # The octabox up to the top left of the plate, so its reflection lies there.
    stage_module.BOX_ON_STAND = Vector((-0.375, 0.375, 0.848)).normalized()
    stage = Stage(OUT, args.proof, scale=args.scale, samples=args.samples)
    stage.clear()
    plate(stage, args.proof)
    stage.shoot("steel", (0, 0, WIDTH, HEIGHT), exposure=EXPOSURE, lens=False, mat=False, eye=EYE, sharp=1.6)


if __name__ == "__main__":
    main()
