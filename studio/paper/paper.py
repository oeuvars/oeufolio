# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""The likes page's paper: an off-white handmade sheet, cotton rag couched on felt, as a tile that repeats without a
seam.

    uv run studio/paper/paper.py [--samples 128] [--proof DIR]

A handmade sheet is uneven all through, and every part of that is drawn here at the sheet's own scale, the tile
being SHEET millimetres across:

- formation: the pulp lies thicker in some places than others, in soft clouds a few centimetres across, and the
  thin places are a shade darker;
- the felt it was couched on presses its weave into both faces, a fine close relief under everything;
- fibres: short cotton ones by the thousand, a little whiter than the pulp, and a few long ones that stand proud
  and catch the light;
- inclusions: now and then a fleck of husk or a short dark thread that was never beaten out.

These are made here as maps that wrap round at their edges (every noise is drawn in the frequency domain, every
fibre wraps), and render.py lays them on a sheet in Blender and lights it with a low lamp, so the relief is real
light and shadow. The sheet is wider than the tile and the camera sees only the middle tile, so a shadow falling
over the edge comes in again from the other side, as it would on the next tile.

Writes public/objects/likes-paper.avif, TILE pixels square, for the page to show at half that in CSS pixels.
"""

import argparse
import os
import subprocess
import tempfile

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TILE = 1536
SHEET = 230.0  # millimetres across the tile
MM = TILE / SHEET  # pixels to the millimetre
# The sheet's colour as it shows on the page: an unbleached off-white, not aged.
PULP = np.array([0.925, 0.912, 0.880])

rng = np.random.default_rng(23)


def noise(low, high):
    """Noise that wraps round, holding only features between low and high millimetres across, scaled to unit
    deviation."""
    f = np.fft.fftfreq(TILE) * MM  # cycles per millimetre
    radius = np.hypot(*np.meshgrid(f, f, indexing="ij"))
    band = np.exp(-((radius * low) ** 2)) - np.exp(-((radius * high) ** 2))
    field = np.real(np.fft.ifft2(np.fft.fft2(rng.standard_normal((TILE, TILE))) * band))
    return (field / field.std()).astype(np.float32)


def strands(count, length, width, wander):
    """Fibres, as a map of how much of each pixel they cover: each a thread length millimetres long (a range),
    width wide, its direction wandering as it goes, wrapping round the tile's edges."""
    cover = np.zeros((TILE, TILE), np.float32)
    for _ in range(count):
        steps = max(2, int(rng.uniform(*length) * MM * 2))
        turn = np.cumsum(rng.normal(0, wander, steps)) + rng.uniform(0, 2 * np.pi)
        x = rng.uniform(0, TILE) + np.cumsum(0.5 * np.cos(turn))
        y = rng.uniform(0, TILE) + np.cumsum(0.5 * np.sin(turn))
        # It thins towards both ends.
        weight = np.sin(np.linspace(0, np.pi, steps)) ** 0.5
        np.add.at(cover, (np.round(y).astype(int) % TILE, np.round(x).astype(int) % TILE), weight)
    # A line of deposits half a pixel apart, blurred, peaks at 2 / (sqrt(2 pi) sigma) across: brought to 1.
    sigma = max(width * MM, 0.6)
    return np.clip(ndimage.gaussian_filter(cover, sigma, mode="wrap") * np.sqrt(2 * np.pi) * sigma / 2, 0, 1)


def flecks(count, size):
    """Small irregular specks, size millimetres across (a range), as cover."""
    cover = np.zeros((TILE, TILE), np.float32)
    for _ in range(count):
        r = rng.uniform(*size) * MM / 2
        n = int(max(3, r * r * 2))
        y = rng.uniform(0, TILE) + rng.normal(0, r * 0.6, n) * rng.uniform(0.5, 1.5)
        x = rng.uniform(0, TILE) + rng.normal(0, r * 0.6, n)
        np.add.at(cover, (np.round(y).astype(int) % TILE, np.round(x).astype(int) % TILE), 1)
    return np.clip(ndimage.gaussian_filter(cover, 0.5, mode="wrap") * 2, 0, 1)


def maps():
    formation = noise(15, 80)
    felt = noise(0.25, 1.2)
    cotton = strands(9000, (1.5, 5), 0.05, 0.25)
    long = strands(260, (6, 18), 0.07, 0.12)
    straw = strands(120, (4, 12), 0.06, 0.15)
    husk = flecks(40, (0.2, 0.7))
    threads = strands(14, (1.5, 4), 0.06, 0.3)

    height = 0.12 * formation + 0.5 * felt + 0.9 * cotton + 1.6 * long + 1.2 * straw - 0.2 * husk
    shade = 1 + 0.012 * formation + 0.035 * cotton + 0.05 * long
    albedo = PULP * shade[..., None]
    # Some fibres were never quite bleached: a little warmer and darker than the pulp.
    albedo = albedo * (1 - 0.35 * straw[..., None]) + np.array([0.80, 0.74, 0.64]) * 0.35 * straw[..., None]
    albedo = albedo * (1 - 0.55 * husk[..., None]) + np.array([0.48, 0.42, 0.34]) * 0.55 * husk[..., None]
    albedo = albedo * (1 - 0.7 * threads[..., None]) + np.array([0.40, 0.36, 0.33]) * 0.7 * threads[..., None]
    height = (height - height.min()) / (height.max() - height.min())
    return np.clip(albedo, 0, 1), height


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--proof", help="also write the tile and its maps into this folder")
    args = parser.parse_args()

    albedo, height = maps()
    with tempfile.TemporaryDirectory() as work:
        Image.fromarray((albedo * 255 + 0.5).astype(np.uint8)).save(os.path.join(work, "albedo.png"))
        Image.fromarray((height * 65535 + 0.5).astype(np.uint16)).save(os.path.join(work, "height.png"))
        out = os.path.join(work, "render.png")
        subprocess.run(
            ["blender", "-b", "--factory-startup", "-P", os.path.join(HERE, "render.py"), "--", work, out, str(TILE), str(args.samples)],
            check=True,
        )
        lit = np.asarray(Image.open(out).convert("RGB")).astype(np.float32) / 255
        if args.proof:
            os.makedirs(args.proof, exist_ok=True)
            for name in ("albedo.png", "height.png", "render.png"):
                os.replace(os.path.join(work, name), os.path.join(args.proof, name))

    # The light is set to the sheet's own colour on average, so the page is the paper's colour and not the lamp's.
    lit = lit * (PULP / lit.reshape(-1, 3).mean(0))
    tile = Image.fromarray((np.clip(lit, 0, 1) * 255 + 0.5).astype(np.uint8))
    tile.save(os.path.join(ROOT, "public", "objects", "likes-paper.avif"), quality=70, subsampling="4:4:4", speed=2)
    if args.proof:
        tile.save(os.path.join(args.proof, "likes-paper.png"))
    print("mean", "#%02x%02x%02x" % tuple(int(v * 255 + 0.5) for v in np.asarray(tile).reshape(-1, 3).mean(0) / 255))


if __name__ == "__main__":
    main()
