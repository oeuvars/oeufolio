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
PEBBLE = 0.13  # the mean distance between pebbles, in em: at the ticket's scale, about two thirds of a millimetre
DEPTH = 0.028  # how far a pebble's crown stands above the crease, in em
DYE = "#e0080f"  # the red on the crowns, as the dye reflects it: a strong red that reflects almost no green or blue
POOLED = "#500006"  # the red the dye dries to in the creases
# The hide is lit dimly, as a dark red is: under the stand's usual light the white the finish reflects would grey the
# red. Two stops down, the photograph comes out the deep crimson of the colour reference, about #651415.
QUALITY = 86
EXPOSURE = -2.05


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
    weight = (rng.random(cells * cells) ** 2.0 * 0.55 * size).reshape(cells, cells)
    ax = (np.arange(n) + 0.5) * TILE / n
    X, Y = np.meshgrid(ax, ax)
    X = X + cloud((n, n), seed + 1, falloff=1.5) * 0.3 * size
    Y = Y + cloud((n, n), seed + 2, falloff=1.5) * 0.3 * size
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
    edge = np.clip((f2 - f1) / PEBBLE, 0, None)  # 0 where two pebbles meet, growing toward each pebble's middle
    # Each pebble a rounded dome, rising out of the crease over a soft shoulder and swelling toward its middle, so
    # the light falls broad across its crown and shades its far side, and never glints along the crease's rim.
    bulge = 1 - np.clip(f1 / (0.75 * PEBBLE), 0, 1) ** 2
    dome = smooth(0.0, 0.45, edge) * (0.45 + 0.55 * bulge)
    crease = 1 - smooth(0.0, 0.14, edge)
    # Here and there a longer, shallow crease across the pebbles, where the hide flexed on the animal: a soft valley
    # along the zero line of a slow noise, shown only in patches.
    line = 1 - smooth(0.0, 0.05, np.abs(cloud((n, n), 5, falloff=1.6, stretch=1.8)))
    long = blur(line * smooth(0.2, 0.9, cloud((n, n), 105, falloff=1.7)), 1.5)
    # Pores, and the fine roughness of the grain's face.
    pits = smooth(0.5, 0.85, blur(smooth(2.5, 3.1, cloud((n, n), 9, falloff=0.1)), 0.8) * 3)
    face = blur(cloud((n, n), 13, falloff=0.6), 0.6)
    height = DEPTH * (blur(dome, 1.0) - 0.5 * long - 0.25 * pits + 0.03 * face) + 0.002 * cloud((n, n), 15, falloff=1.6)
    return height, crease, pits, long


def leather(stage, proof=None):
    sheet = Sheet(TILE * 3, TILE * 3, DYE, rough=0.5, density=2)
    rows, cols = sheet.height.shape
    n = rows // 3
    height, crease, pits, long = grain(n)
    tile = lambda a: np.tile(a, (3, 3))[:rows, :cols]  # noqa: E731
    height, crease, pits, long = tile(height), tile(crease), tile(pits), tile(long)
    # Colour: the dye on the crowns, darker where it pooled, and a faint unevenness, as no hide takes dye evenly.
    mottle = tile(cloud((n, n), 21, falloff=1.2))
    top = linear(DYE) * (1 + 0.05 * mottle)[..., None]
    pool = linear(POOLED)
    dark = np.clip(0.85 * blur(crease, 0.6) + 0.3 * long + 0.4 * pits, 0, 1)[..., None]
    sheet.rgb = top * (1 - dark) + pool * dark
    sheet.height = height
    # The finish: a satin wax, worn a little smoother on the crowns, matte in the creases and pores. No sheen: that is
    # the fuzz of velvet, and it greys the red.
    sheet.rough = 0.5 + 0.3 * np.clip(crease + long + pits, 0, 1)
    sheet.coat = 0.0 * crease
    if proof:
        np.save(os.path.join(proof, "leather-albedo.npy"), sheet.rgb[:n, :n].astype(np.float32))
    # The sheet is three squares across and the frame the middle one, so the square meets itself on every side. The
    # lens is left out: it leans the light across the frame, which would show as a step where two squares meet.
    # The scan of real hide only varies the shine: its relief is a coarser grain than this one, and would show through.
    sheet.build(stage, "leather", thickness=0.1, scan="Leather037", scan_size=TILE / 4, scan_normal=0.0, scan_rough=0.2, specular=0.5, at=(-TILE, -TILE))
    stage.shoot("leather", (0, 0, TILE, TILE), exposure=EXPOSURE, lens=False, sharp=2.0)


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
