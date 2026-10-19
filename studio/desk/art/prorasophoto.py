# /// script
# dependencies = ["numpy", "pillow", "scipy"]
# ///
"""The tube, taken from the user's photograph of their own, used and crumpled, lying on its back on marble, seen from
straight above (art/proraso-own.jpg): its outline, and its print unrolled round it. Run from the repository root:

    uv run studio/desk/art/prorasophoto.py

The tube's two edges are followed down the photograph, from hand-picked guesses to the strongest edge near each. They
give the tube's width and middle at every row, which objects/proraso.py builds the wall to (art/proraso-shape.json):
the crimp flattened and flared, the body narrowing to the shoulder, every dent in the outline. Each row of the wall is
an oval, as wide as the photograph shows it and as deep as DEEP says, and the print is sampled evenly round that oval,
as the model's UV map runs. The back, which the photograph cannot see, is the front mirrored about the sides.

The photograph's own light is kept: the crumples' shading and glints are what make it read as a used tube. Only its
broadest light (brighter at one end, the room's falloff) is divided out, and its white set to the model's lacquer.
art/proraso-print.png: across, once round the tube, the middle of the front in the middle; down, crimp to shoulder;
PX pixels to the em. art/proraso-relief.png beside it: the crumples' fine light and dark, mid grey for none, the
print's inks left out."""

import json
import math
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO = os.path.join(HERE, "proraso-own.jpg")
PRINT = os.path.join(HERE, "proraso-print.png")
RELIEF = os.path.join(HERE, "proraso-relief.png")
SHAPE = os.path.join(HERE, "proraso-shape.json")
# As objects/proraso.py has it: the tube's length from the crimped edge to the shoulder, and the print's width once
# round, in em.
LENGTH = 22.31
ROUND = 15.708
PX = 90
# The edges, guessed by hand as (row, column) in the photograph, and the crimped edge's row and the shoulder's.
LEFT = [(572, 385), (675, 400), (775, 410), (875, 431), (975, 440), (1075, 432), (1175, 438), (1275, 455), (1375, 479), (1475, 490), (1575, 505), (1675, 502), (1775, 500), (1880, 517)]
RIGHT = [(572, 864), (632, 846), (776, 846), (860, 840), (900, 822), (1010, 810), (1160, 804), (1310, 798), (1460, 790), (1600, 781), (1760, 780), (1880, 778)]
CRIMP = 568.0
# The edges are smoothed over this many rows: the dents stay, but no ring runs round the whole tube.
EVEN = 14
SHOULDER = 1900.0
# How deep the tube is, as a share of how wide, from the crimp to the shoulder: shut flat at the crimp, pressed flat
# for the first few em, round by the shoulder. (along in em, share)
DEEP = ((0.0, 0.03), (0.7, 0.03), (0.85, 0.02), (1.5, 0.05), (3.5, 0.09), (5.5, 0.17), (8.0, 0.3), (11.0, 0.47), (14.0, 0.62), (17.0, 0.8), (20.0, 0.95), (LENGTH, 1.0))
# The lacquer's white in the model, #e4e4df; how far the light divided out is smoothed, along and round, and the
# size of the crumples' relief, in em.
BODY = (0xE4, 0xE4, 0xDF)
BROAD = (1.0, 0.25)
# How far round from the middle of the front the photograph is read, in shares of the way round.
SIDE = 0.235
# The photographer's shadow: from this far along (em), over the left side from this share round to this.
SHADOW = (16.0, 0.25, 0.45)
FINE = 0.12
# How much brighter than the lacquer a glint may stay.
GLINT = 0.04


def linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def encode(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def edges(photo):
    """Each edge's column at every row from the crimp to the shoulder."""
    lum = ndimage.gaussian_filter(photo.mean(-1), 1.5)
    slope = ndimage.sobel(lum, axis=1)
    rows = np.arange(int(CRIMP), int(SHOULDER) + 1)
    found = []
    for guesses, sign in ((LEFT, 1), (RIGHT, -1)):
        guess = np.interp(rows, *zip(*guesses))
        cols = []
        for y, x0 in zip(rows, guess):
            a = int(x0 - 12)
            seg = slope[y, a : a + 25] * sign
            cols.append(a + np.argmax(seg) if seg.max() > 4 else x0)
        cols = ndimage.median_filter(np.array(cols, float), 21)
        cols = np.where(np.abs(cols - guess) > 10, guess, cols)
        found.append(ndimage.gaussian_filter1d(cols, EVEN))
    return rows, found[0] + 1.0, found[1] - 1.0


def perimeter(a, b):
    h = ((a - b) / (a + b)) ** 2
    return math.pi * (a + b) * (1 + 3 * h / (10 + np.sqrt(4 - 3 * h)))


def main():
    photo = np.asarray(Image.open(PHOTO).convert("RGB")).astype(np.float64)
    rows, left, right = edges(photo)
    scale = (SHOULDER - CRIMP) / LENGTH
    middle, half = (left + right) / 2, (right - left) / 2
    # The tube's axis is the straight line through its middles; the middle wanders off it.
    axis = np.polyval(np.polyfit(rows, middle, 1), rows)

    # The shape, for the model: every 0.05 em along, its half width, its depth and its middle off the axis.
    along = np.arange(0, LENGTH + 1e-6, 0.05)
    at = CRIMP + along * scale
    a = np.interp(at, rows, half) / scale
    b = a * np.interp(along, *zip(*DEEP))
    off = np.interp(at, rows, middle - axis) / scale
    with open(SHAPE, "w") as file:
        json.dump({"along": along.round(3).tolist(), "half": a.round(4).tolist(), "deep": b.round(4).tolist(), "off": off.round(4).tolist()}, file)

    # The print: each of its rows an oval as the model builds it, sampled evenly round it.
    rows_out, cols_out = round(LENGTH * PX), round(ROUND * PX)
    v = (np.arange(rows_out) + 0.5) / PX
    share = (np.arange(cols_out) + 0.5) / cols_out
    # The back is the front mirrored about the sides.
    front = np.where(share < 0.25, 0.5 - share, np.where(share > 0.75, 1.5 - share, share))
    # Toward each side the photograph sees the tube edge on, dark and with the marble in it: there the print is
    # carried out from as far round as the photograph reads it.
    front = np.clip(front, 0.5 - SIDE, 0.5 + SIDE)
    ya = CRIMP + v * scale
    ra = np.interp(ya, rows, half)
    rb = ra * np.interp(v, *zip(*DEEP))
    rm = np.interp(ya, rows, middle)
    phis = np.linspace(0, math.pi / 2, 721)
    xs = np.empty((rows_out, cols_out))
    for i in range(rows_out):
        t = np.linspace(0, 1, 257)[None, :] * phis[:, None]
        ds = np.hypot(ra[i] * np.cos(t), rb[i] * np.sin(t))
        arc = np.trapezoid(ds, t, axis=1)
        reach = np.abs(front - 0.5) * perimeter(ra[i], rb[i])
        xs[i] = rm[i] + np.sign(front - 0.5) * ra[i] * np.sin(np.interp(reach, arc, phis))
    yy = np.broadcast_to(ya[:, None], xs.shape)
    picture = np.stack([ndimage.map_coordinates(photo[..., k], [yy, xs], order=3, mode="nearest") for k in range(3)], -1)

    # The lacquer: whatever is not ink. The green, the red and the black are found by colour; the gold is too thin
    # to matter.
    lin = linear(np.clip(picture, 0, 255) / 255)
    r, g, b = lin[..., 0], lin[..., 1], lin[..., 2]
    grey = lin.mean(-1)
    chroma = (lin.max(-1) - lin.min(-1)) / np.maximum(grey, 1e-3)
    # The black is all well inside the sides; dark near the sides is the tube turning away.
    inside = (np.abs(front - 0.5) < 0.17)[None, :]
    ink = ((g > 1.2 * r) & (g > 1.1 * b)) | ((r > 2.5 * g) & (r > 0.1)) | ((grey < 0.05) & (chroma < 0.8) & inside)
    white = ~ndimage.binary_dilation(ink, iterations=2)
    # Its broad light divided out, colour and all: smoothed far along the tube and a little round it, so the falloff
    # toward each edge goes and the crumples, which never run far, keep their own light and dark.
    sigma = (BROAD[0] * PX, BROAD[1] * PX)
    weight = ndimage.gaussian_filter(white.astype(np.float64), sigma, mode=("nearest", "wrap"))
    light = np.stack([ndimage.gaussian_filter(lin[..., k] * white, sigma, mode=("nearest", "wrap")) for k in range(3)], -1) / np.maximum(weight, 1e-6)[..., None]
    # The photographer's shadow lies over the left of the foot: there the light is read much closer.
    def smoothed(sigma):
        weight = ndimage.gaussian_filter(white.astype(np.float64), sigma, mode=("nearest", "wrap"))
        return np.stack([ndimage.gaussian_filter(lin[..., k] * white, sigma, mode=("nearest", "wrap")) for k in range(3)], -1) / np.maximum(weight, 1e-6)[..., None]

    v0, s0, s1 = SHADOW
    box = np.clip((v[:, None] - v0) / 1.5, 0, 1) * np.clip(1 - np.abs(np.abs(front - 0.5) * np.sign(0.5 - front) - (0.5 - (s0 + s1) / 2)) / ((s1 - s0) / 2), 0, 1)[None, :]
    box = ndimage.gaussian_filter(box, 0.3 * PX)[..., None]
    light = light * (1 - box) + smoothed((0.3 * PX, 0.08 * PX)) * box
    flat = lin / np.maximum(light, 1e-4)
    # The photograph's glints are its lamp's, not the desk's: anything brighter than the lacquer is pressed back
    # to it, and the render's own gloss puts the desk's glints on the crumples.
    flat = np.where(flat > 1, 1 + GLINT * np.tanh((flat - 1) / GLINT), flat) * linear(np.array(BODY) / 255)
    srgb = np.clip(encode(flat) * 255, 0, 255).astype(np.uint8)
    Image.fromarray(srgb, "RGB").save(PRINT)

    # The crumples' relief: the white's fine light and dark, the inks left out.
    # The gold and the grey of the panel's frame are inks here too: any line much darker than the lacquer around it.
    gilt = (r > g) & (g > b) & (chroma > 0.5)
    lines = (grey < 0.55 * light.mean(-1)) & ~ndimage.binary_opening(grey < 0.55 * light.mean(-1), iterations=4)
    clean = white & ~ndimage.binary_dilation(gilt | lines, iterations=3)
    plain = ndimage.gaussian_filter(ndimage.binary_erosion(clean, iterations=6).astype(np.float64), 2)
    level = np.log(np.maximum(grey, 1e-3) / np.maximum(light.mean(-1), 1e-3))
    # Smoothed over the white alone, so the inks leave no halo.
    near = ndimage.gaussian_filter(plain, FINE * PX)
    fine = level - ndimage.gaussian_filter(level * plain, FINE * PX) / np.maximum(near, 1e-6)
    fine *= plain
    relief = 128 + 127 * np.clip(fine / (3 * fine[plain > 0.5].std()), -1, 1)
    Image.fromarray(relief.astype(np.uint8), "L").save(RELIEF)
    print(cols_out, "x", rows_out, "white", round(white.mean(), 3), "crimp", round(a[0], 2), "shoulder", round(a[-1], 2), "em half width")


if __name__ == "__main__":
    main()
