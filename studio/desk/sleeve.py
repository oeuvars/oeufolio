# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3"]
# ///
"""The business card's vinyl sleeve, cut from the photograph of the badge's holder (studio/assets/reference.jpg),
so that the card wears the same vinyl the badge does and not a likeness of it.

    uv run studio/desk/sleeve.py

As studio/badge.py does, it measures what the vinyl does to the white page under it. Vinyl is not a tint: its
welds, its rolled edge and its film scatter light back, so they show grey on whatever lies under them, darker
than white paper and lighter than a dark mat. Each pixel is kept as how much of a grey film, GREY, would darken
the page as the photograph shows it, and how much of a white film would lighten it. The sleeve in the desk
(objects/card.py) is that film, lit by the desk's own light.

The holder's bottom-left corner is the sleeve's corners, mirrored. Its left edge, along its length, is the
sleeve's ends, and its bottom edge the sleeve's long sides: the rolled outer edge, the seam welded a couple of
millimetres in, and the flat film inside it. Over the card the film is the flat film's own measure.

Writes studio/desk/art/sleeve.png: red is the white film, green the grey film, at twice the reference's size,
for the card at 14.8 by 8.46 em with the band round it.
"""

import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCE = os.path.join(HERE, "..", "assets", "reference.jpg")
OUT = os.path.join(HERE, "art", "sleeve.png")

# The film's own colour, as objects/card.py lights it.
GREY = 0.55
# In the reference's pixels. The page shows bare outside these.
BARE = (92, 634, 893)
# The holder's outline, and the radius of its corners: outside it there is only page.
HOLDER = (105, 15, 620, 882, 22)
# The band of vinyl round the card at the holder's bottom left: from the card's bottom edge out past the holder's.
BAND = 35
CORNER = (101, 851)  # its top left, where the left edge and the bottom edge meet
SIDE = (400, 800)  # rows of the left edge where it runs straight
BOTTOM = (200, 520)  # columns of the bottom edge where it runs straight
FLAT = (140, 155, 400, 800)  # flat film over bare page, between the seam and the card
# The card is 89 by 51 mm, and the reference's ID card 54 mm across 415 pixels.
CARD = (round(415 * 89 / 54), round(415 * 51 / 54))
UP = 2


def films(ref):
    """How much white film and how much grey film give the photograph over the bare page fitted round it."""
    lum = ref.mean(axis=-1)
    rows, cols = lum.shape
    Y, X = np.mgrid[0:rows, 0:cols].astype(np.float64)
    left, right, below = BARE
    bare = (X < left) | (X > right) | (Y > below)
    a, b, c = np.linalg.lstsq(np.column_stack((np.ones(bare.sum()), X[bare], Y[bare])), lum[bare], rcond=None)[0]
    page = np.clip(a + b * X + c * Y, 0, 0.995)
    white = np.where(lum > page, np.clip((lum - page) / (1 - page), 0, 1), 0)
    grey = np.where(lum > page, 0, np.clip((page - lum) / np.maximum(page - GREY, 1e-3), 0, 1))
    x0, y0, x1, y1, r = HOLDER
    dx = np.maximum(np.maximum(x0 + r - (X + 0.5), (X + 0.5) - (x1 - r)), 0)
    dy = np.maximum(np.maximum(y0 + r - (Y + 0.5), (Y + 0.5) - (y1 - r)), 0)
    held = np.clip(r + 0.5 - np.hypot(dx, dy), 0, 1)
    return white * held, grey * held


def stretched(a, length, axis):
    """A run of an edge, stretched along its length. The photograph's JPEG blocks are smoothed out along it
    first, or stretching draws them out into dashes."""
    kernel = np.exp(-0.5 * (np.arange(-12, 13) / 4.0) ** 2)
    kernel /= kernel.sum()
    a = np.apply_along_axis(lambda run: np.convolve(np.pad(run, 12, mode="edge"), kernel, mode="valid"), axis, a)
    image = Image.fromarray(a.astype(np.float32), mode="F")
    size = (length, a.shape[0]) if axis == 1 else (a.shape[1], length)
    return np.asarray(image.resize(size, Image.Resampling.BICUBIC))


def sleeve(m):
    """One film over the whole sleeve, the card in the middle and the band round it."""
    cx, cy = CORNER
    w, h = CARD
    out = np.full((h + 2 * BAND, w + 2 * BAND), np.median(m[FLAT[2] : FLAT[3], FLAT[0] : FLAT[1]]))
    corner = m[cy : cy + BAND, cx : cx + BAND]  # the bottom left
    end = stretched(m[SIDE[0] : SIDE[1], cx : cx + BAND], h, 0)  # the left end, top to bottom
    side = stretched(m[cy : cy + BAND, BOTTOM[0] : BOTTOM[1]], w, 1)  # the bottom side, left to right
    out[-BAND:, :BAND] = corner
    out[-BAND:, -BAND:] = corner[:, ::-1]
    out[:BAND, :BAND] = corner[::-1]
    out[:BAND, -BAND:] = corner[::-1, ::-1]
    out[BAND:-BAND, :BAND] = end
    out[BAND:-BAND, -BAND:] = end[:, ::-1]
    out[-BAND:, BAND:-BAND] = side
    out[:BAND, BAND:-BAND] = side[::-1]
    return out


def main():
    ref = np.asarray(Image.open(REFERENCE).convert("RGB"), dtype=np.float64) / 255
    white, grey = (sleeve(m) for m in films(ref))
    size = (white.shape[1] * UP, white.shape[0] * UP)
    up = [np.asarray(Image.fromarray(m.astype(np.float32), mode="F").resize(size, Image.Resampling.BICUBIC)) for m in (white, grey)]
    rgb = np.dstack((up[0], up[1], np.zeros_like(up[0])))
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8), mode="RGB").save(OUT)
    print(f"sleeve {size[0]}x{size[1]}, band {BAND / (415 / 54):.1f} mm, flat film {np.median(grey):.3f} grey {np.median(white):.3f} white")


main()
