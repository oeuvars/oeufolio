# /// script
# dependencies = ["numpy", "pillow", "scipy"]
# ///
"""The Seiko 7A28 quartz chronograph's dial, taken from the user's photograph of it face on (art/chrono-photo.jpg) and
laid out square, 12 o'clock up: what objects/chrono.py lays over its dial from above. The photograph sees the dial
all but square on, so the black ring round its tachymeter scale is all but a circle in it: found along that ring, it
is drawn out to a circle of RING_R. SEIKO, the scales, the hands and the subdials are the photograph's own; the name
of the account that posted it, written across the dial under QUARTZ, is taken out and the dial filled in under it.
Run from the repository root:

    uv run studio/desk/art/chronophoto.py

It writes studio/desk/art/chrono-dial.png: SIZE millimetres across, PX pixels to the millimetre, the middle of the
dial in the middle."""

import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO = os.path.join(HERE, "chrono-photo.jpg")
OUT = os.path.join(HERE, "chrono-dial.png")
SIZE = 36.0
PX = 40
# The black ring round the tachymeter scale in the photograph: the ellipse's middle, in pixels, and its matrix: a
# point p is on it where (p - CENTRE) . RING . (p - CENTRE) = 1. The photograph shows this many of its pixels to the
# mm (the case 38.6 mm across), which puts the ring this far out.
CENTRE = [390.651, 569.547]
RING = [[1.90239e-05, -1.84e-09], [-1.84e-09, 1.91337e-05]]
SCALE = 13.4
RING_R = 229.0 / SCALE
# The account's name: within this box of the photograph (left, top, right, bottom), what is darker than the dial
# round it by this much, and this many pixels round that. The seconds hand runs down through it, upright, its middle
# at this column and this many pixels either side: there the hand is drawn again from just below the name.
NAME = (300, 490, 484, 515)
DARKER = 14.0
HALO = 2
HAND = (390, 4)


def unsigned(photo):
    """The photograph with the account's name taken out of it."""
    grey = photo.mean(-1)
    x0, y0, x1, y1 = NAME
    box = (slice(y0, y1), slice(x0, x1))
    around = ndimage.median_filter(grey, size=25)
    mask = np.zeros(grey.shape, bool)
    mask[box] = around[box] - grey[box] > DARKER
    mask = ndimage.binary_dilation(mask, iterations=HALO)
    middle, half = HAND
    rows = slice(y0 - 2, y1 + 2)
    columns = slice(middle - half, middle + half + 1)
    mask[rows, columns] = True
    # The dial under the name and the hand: its own colour from round about, smoothed in from the edges of the hole.
    out = photo.copy()
    keep = (~mask).astype(np.float32)
    for k in range(3):
        weight = ndimage.gaussian_filter(keep, 3.0)
        fill = ndimage.gaussian_filter(photo[..., k] * keep, 3.0) / np.maximum(weight, 1e-6)
        out[..., k] = np.where(mask, fill, photo[..., k])
    # The hand where the name crossed it: its own columns from just below the name.
    out[rows, columns] = photo[y1 + 2 : y1 + 14, columns].mean(0)[None]
    # The grain of the photograph, back over the smoothed patch.
    rng = np.random.default_rng(5)
    out += mask[..., None] * rng.normal(0, 2.0, out.shape[:2])[..., None]
    return out


def main():
    photo = unsigned(np.asarray(Image.open(PHOTO).convert("RGB")).astype(np.float32))
    weights, axes = np.linalg.eigh(np.array(RING))
    if np.linalg.det(axes) < 0:
        axes[:, 0] *= -1
    semi = 1 / np.sqrt(weights)
    n = round(SIZE * PX)
    steps = (np.arange(n) + 0.5) / PX - SIZE / 2
    x, y = np.meshgrid(steps, -steps)
    # The dial in mm, 12 o'clock up, onto the unit circle and out to the ellipse.
    u = np.stack((x / RING_R, -y / RING_R), -1)
    at = np.array(CENTRE) + (u @ axes) * semi @ axes.T
    out = np.dstack([ndimage.map_coordinates(photo[..., k], [at[..., 1], at[..., 0]], order=3, mode="nearest") for k in range(3)])
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(OUT)
    print(OUT, out.shape)


main()
