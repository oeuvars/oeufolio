"""The surface the contact page's ticket lies on: red top-grain leather, photographed on the same copy stand as the
ticket, so the one studio light shades both and the ticket's shadow falls on it as it would on the real thing. Run
from the repository root:

    blender -b --factory-startup -P studio/ticket/leather.py -- [--scale 0.5] [--samples 64] [--proof DIR]

Top grain is the outer face of the hide with its natural grain left on. Its surface is a field of pebbles: rounded,
uneven in size, packed close, each a millimetre or two across, with narrow creases between them. The dye pools in
the creases and dries darker there; the finish wears smoother and brighter on the crown of each pebble, so the tops
catch the light in small soft highlights and the creases stay matte. Pores show as fine pits scattered over it, and
here and there a longer crease runs across where the hide flexed on the animal.

All of that is grown here rather than read from a scan, so the grain is the right size for the ticket and deep
enough to read: the pebbles from the cells of a jittered grid (a Voronoi pattern, its distance to the nearest edge
rounding each cell into a dome), the creases from where cells meet, the pores and the long creases from noise. It is
grown on a torus, so the square meets itself on every side and the page can repeat it.

Writes public/objects/leather.avif, one square of the hide, which the page repeats under the contact strip. Set
OEUSUME if that checkout is not in ~/Documents/oeusume.
"""

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OEUSUME = os.environ.get("OEUSUME", os.path.expanduser("~/Documents/oeusume"))
sys.path.insert(0, os.path.join(OEUSUME, "studio"))

import numpy as np  # noqa: E402

import stage as stage_module  # noqa: E402
from paint import blur, cloud, linear  # noqa: E402
from stage import Stage  # noqa: E402
from stock import Sheet  # noqa: E402

OUT = os.path.join(ROOT, "public", "objects")
TILE = 8.0  # the square the page repeats, in em
PEBBLE = 0.3  # the mean distance between pebbles, in em: at the ticket's scale, about a millimetre and a half
DEPTH = 0.03  # how far a pebble's crown stands above the crease, in em
DYE = "#9c1d15"  # the red on the crowns
POOLED = "#4a0906"  # the red the dye dries to in the creases
QUALITY = 86


def smooth(lo, hi, x):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def voronoi(n, seed):
    """Distances to the nearest and second nearest of a jittered grid of points, on a torus TILE across, sampled on
    n by n pixels. Each point carries a weight that is taken off its distance, so cells come in different sizes and
    the line where two meet is curved, not straight; and the plane is warped before it is measured, so every cell is
    a little irregular. Together they make the rounded, uneven pebbles of a hide rather than a mosaic."""
    rng = np.random.default_rng(seed)
    cells = round(TILE / PEBBLE)
    size = TILE / cells
    gx, gy = np.meshgrid(np.arange(cells), np.arange(cells))
    pts = (np.stack([gx.ravel(), gy.ravel()], 1) + 0.5 + rng.uniform(-0.4, 0.4, (cells * cells, 2))) * size
    weight = (rng.random(cells * cells) ** 1.5 * 0.32 * size).reshape(cells, cells)
    ax = (np.arange(n) + 0.5) * TILE / n
    X, Y = np.meshgrid(ax, ax)
    X = X + cloud((n, n), seed + 1, falloff=1.7) * 0.12 * size
    Y = Y + cloud((n, n), seed + 2, falloff=1.7) * 0.12 * size
    f1 = np.full((n, n), np.inf)
    f2 = np.full((n, n), np.inf)
    ci = np.floor(X / size).astype(int)
    cj = np.floor(Y / size).astype(int)
    grid = pts.reshape(cells, cells, 2)
    for dj in (-2, -1, 0, 1, 2):
        for di in (-2, -1, 0, 1, 2):
            jj, ii = (cj + dj) % cells, (ci + di) % cells
            p = grid[jj, ii]
            dx = X - p[..., 0]
            dy = Y - p[..., 1]
            dx -= TILE * np.round(dx / TILE)
            dy -= TILE * np.round(dy / TILE)
            d = np.hypot(dx, dy) - weight[jj, ii]
            f2 = np.where(d < f1, f1, np.minimum(f2, d))
            f1 = np.minimum(f1, d)
    return f1, f2


def grain(n):
    """The hide's relief, how deep each point lies in a crease (0 on a crown, 1 at the bottom of a crease), and
    where the pores are, all n by n and seamless."""
    f1, f2 = voronoi(n, 7)
    edge = (f2 - f1) / PEBBLE  # 0 where two pebbles meet, growing toward each pebble's middle
    edge = np.clip(edge, 0, None)
    # Each pebble a soft dome: rounded up from the crease, and falling away a little from its middle.
    # Each pebble rounds up out of the crease over a short shoulder, then swells gently toward its middle. The shoulder
    # is saturated before the line inside a cell where its second neighbour changes, so no ridge shows across it.
    shoulder = smooth(0.0, 0.2, edge)
    bulge = 1 - np.clip((f1 + 0.1 * PEBBLE) / (0.75 * PEBBLE), 0, 1) ** 2
    dome = shoulder * (0.3 + 0.7 * blur(bulge, 1.5))
    crease = 1 - smooth(0.0, 0.1, edge)
    # Long creases where the hide flexed: thin, shallow valleys along the zero lines of a slow noise.
    flex = cloud((n, n), 5, falloff=2.0, stretch=1.8)
    long = (1 - smooth(0.0, 0.05, np.abs(flex))) * smooth(0.0, 0.7, cloud((n, n), 6, falloff=1.6))
    # Pores: small soft pits, scattered.
    pits = smooth(0.45, 0.8, blur(smooth(2.6, 3.2, cloud((n, n), 9, falloff=0.1)), 1.2) * 3)
    height = blur(DEPTH * (dome - 0.3 * long - 0.15 * pits) + 0.002 * cloud((n, n), 13, falloff=1.4), 1.0)
    return height, np.clip(crease + 0.6 * long, 0, 1), pits


def leather(stage, proof=None):
    sheet = Sheet(TILE * 3, TILE * 3, DYE, rough=0.5, density=2)
    rows, cols = sheet.height.shape
    n = rows // 3
    height, crease, pits = grain(n)
    tile = lambda a: np.tile(a, (3, 3))[:rows, :cols]  # noqa: E731
    height, crease, pits = tile(height), tile(crease), tile(pits)
    # Colour: the dye on the crowns, darker where it pooled, a slow mottle across the hide as no hide takes dye evenly.
    mottle = tile(cloud((n, n), 21, falloff=1.9))
    top = linear(DYE) * (1 + 0.06 * mottle)[..., None]
    pool = linear(POOLED)
    dark = np.clip(0.55 * blur(crease, 1.5) + 0.25 * pits, 0, 1)[..., None]
    sheet.rgb = top * (1 - dark) + pool * dark
    sheet.height = height
    # The finish: smooth and bright on the crowns, matte in the creases and pores.
    sheet.rough = 0.5 + 0.25 * np.clip(crease + pits, 0, 1)
    sheet.coat = 0.0 * crease
    if proof:
        np.save(os.path.join(proof, "leather-albedo.npy"), sheet.rgb[:n, :n].astype(np.float32))
    # The sheet is three squares across and the frame the middle one, so the square meets itself on every side. The
    # lens is left out: it leans the light across the frame, which would show as a step where two squares meet.
    # The fine texture of the grain's surface, pores and all, from a scan of real hide, faint, one tile to the square.
    sheet.build(stage, "leather", thickness=0.1, scan="Leather037", scan_size=TILE / 4, scan_normal=0.5, scan_rough=0.3, sheen=0.35, specular=0.4, coat_rough=0.4, at=(-TILE, -TILE))
    stage.shoot("leather", (0, 0, TILE, TILE), exposure=0.35, lens=False, sharp=2.0)


parser = argparse.ArgumentParser()
parser.add_argument("--scale", type=float, default=1.0)
parser.add_argument("--samples", type=int, default=96)
parser.add_argument("--proof")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
stage_module.MAT = DYE
STAGE = Stage(OUT, None, scale=args.scale, samples=args.samples)
STAGE.clear()
leather(STAGE, args.proof)
# Again, smaller: the stage encodes every shot as it does the objects, near lossless.
script = f"""
from PIL import Image
path = {os.path.join(OUT, "leather.avif")!r}
Image.open(path).convert("RGB").save(path, quality={QUALITY}, subsampling="4:2:0", speed=2)
"""
subprocess.run(["uv", "run", "--quiet", "--with", "pillow>=11.3", "python", "-I", "-c", script], check=True)
