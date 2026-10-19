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
HEIGHT = os.path.join(HERE, "proraso-height.png")
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
# The lacquer's white in the print, #c7c9ca, low enough under the glints' white to leave them their light; how far the light divided out is smoothed, along and round, and the
# size of the crumples' relief, in em.
BODY = (0xC7, 0xC9, 0xCA)
BROAD = (2.0, 0.04)
# How far round from the middle of the front the photograph is read, in shares of the way round.
SIDE = 0.22
# The photographer's shadow: from this far along (em), over the left side from this share round left of the middle
# out to the edge.
SHADOW = (16.5, 0.08)
FINE = 0.12
# The brightest a glint may be in the print, as linear white.
GLINT = 0.92
# The photograph's light, the way toward it across and down the print, and how steep a facet is per unit of log
# brightness (a key about 60 degrees up).
LIGHT = np.array((-0.3, -0.95))
SLOPE = 2.6
# The logo panel, from and to this far down the print (em).
PANEL = (2.6, 7.8)
# The crumples kept are finer than this (em), and their creases sharpened this much.
BULGE = 0.4
SHARPEN = 2.5


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
    # Toward each side the photograph sees the tube edge on, dark and with the marble in it: past as far round as
    # it reads, the print is reflected back on itself.
    reach = np.abs(front - 0.5)
    facing = reach.copy()
    front = 0.5 + np.sign(front - 0.5) * np.where(reach > SIDE, 2 * SIDE - reach, reach)
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
    # Its broad light divided out, colour and all: smoothed far along the tube and hardly round it, so the falloff
    # toward each edge goes and the crumples, which run every way, keep their own light and dark.
    sigma = (BROAD[0] * PX, BROAD[1] * PX)
    weight = ndimage.gaussian_filter(white.astype(np.float64), sigma, mode=("nearest", "wrap"))
    light = np.stack([ndimage.gaussian_filter(lin[..., k] * white, sigma, mode=("nearest", "wrap")) for k in range(3)], -1) / np.maximum(weight, 1e-6)[..., None]
    # The photographer's shadow lies over the left of the foot: there the light is read much closer.
    def smoothed(sigma):
        weight = ndimage.gaussian_filter(white.astype(np.float64), sigma, mode=("nearest", "wrap"))
        return np.stack([ndimage.gaussian_filter(lin[..., k] * white, sigma, mode=("nearest", "wrap")) for k in range(3)], -1) / np.maximum(weight, 1e-6)[..., None]

    v0, x0 = SHADOW
    box = np.clip((v[:, None] - v0) / 1.5, 0, 1) * np.clip((0.5 - front - x0) / 0.04, 0, 1)[None, :]
    box = ndimage.gaussian_filter(box, 0.1 * PX)[..., None]
    light = light * (1 - box) + smoothed((0.3 * PX, 0.08 * PX)) * box
    # For the print, the light is only the falloff toward each edge, the same all along, times the room's, brighter
    # toward one end and the same all round. Neither has any crumple in it, so the crumples' shading and glints stay
    # in the print just as the photograph has them.
    lacquer = np.where((white & (box[..., 0] < 0.01))[..., None], lin, np.nan)
    across = np.nanmedian(np.where(((v > 1.0) & (v < LENGTH - 0.6))[:, None, None], lacquer, np.nan), axis=0)
    across = ndimage.gaussian_filter1d(across, 0.1 * PX, axis=0, mode="wrap")
    down = np.nanmedian(np.where((np.abs(front - 0.5) < 0.12)[None, :, None], lacquer / across, np.nan), axis=1)
    known = ~np.isnan(down)
    down = ndimage.gaussian_filter1d(np.where(known, down, 0), PX, axis=0, mode="nearest") / np.maximum(ndimage.gaussian_filter1d(known.astype(np.float64), PX, axis=0, mode="nearest"), 1e-6)
    lit = down[:, None] * across[None]
    lit = lit * (1 - box) + smoothed((0.3 * PX, 0.08 * PX)) * box
    flat = lin / np.maximum(lit, 1e-4)
    # Under it, and at the edge beside it where the marble shows, the lacquer is the other side's, mirrored; the
    # signature's ink stays its own.
    stroke = (ndimage.grey_closing(grey, size=(9, 9)) - grey) > 0.22 * light.mean(-1)
    printed = ndimage.gaussian_filter(ndimage.binary_dilation(ink | stroke, iterations=2).astype(np.float64), 1)[..., None]
    borrow = box * (1 - printed) * (1 - printed[:, ::-1])
    flat = flat * (1 - borrow) + flat[:, ::-1] * borrow
    # Past what the photograph reads, only its coloured inks carry round; the lacquer there is plain, and takes its
    # crumples from the wall's own shape.
    beyond = np.clip((facing - (SIDE - 0.03)) / 0.03, 0, 1)[None, :, None]
    coloured = ndimage.gaussian_filter(ndimage.binary_dilation(((g > 1.2 * r) & (g > 1.1 * b)) | ((r > 2.5 * g) & (r > 0.1)) | ((grey < 0.06) & (facing < SIDE)[None, :]), iterations=2).astype(np.float64), 1)[..., None]
    lacquer = np.median(flat[white & (np.abs(front - 0.5) < 0.1)[None, :]], axis=0)
    flat = flat * (1 - beyond * (1 - coloured)) + lacquer * beyond * (1 - coloured)
    # The glints are kept, as bright as the print can hold: up to GLINT white, eased in.
    body = linear(np.array(BODY) / 255)
    head = (GLINT - body) / body
    flat = np.where(flat > 1, 1 + head * np.tanh((flat - 1) / head), flat) * body
    srgb = np.clip(encode(flat) * 255, 0, 255).astype(np.uint8)
    Image.fromarray(srgb, "RGB").save(PRINT)

    # The crumples' relief: the white's fine light and dark, the inks left out.
    # The gold and the grey of the panel's frame are inks here too: any line much darker than the lacquer around it.
    gilt = (r > g) & (g > b) & (chroma > 0.5)
    # Thin printed lines (the frame, the rules, the signature): much darker than a closing of the picture over them.
    lines = (ndimage.grey_closing(grey, size=(9, 9)) - grey) > 0.22 * light.mean(-1)
    # The logo panel's grey frame is broad and pale: inside its band, a wider and gentler test.
    band = ((v > PANEL[0]) & (v < PANEL[1]))[:, None]
    lines |= band & ((ndimage.grey_closing(grey, size=(19, 19)) - grey) > 0.1 * light.mean(-1))
    clean = white & ~ndimage.binary_dilation(gilt | lines, iterations=3)
    plain = ndimage.gaussian_filter(ndimage.binary_erosion(clean, iterations=6).astype(np.float64), 2)
    level = np.log(np.maximum(grey, 1e-3) / np.maximum(light.mean(-1), 1e-3))
    # Smoothed over the white alone, so the inks leave no halo.
    near = ndimage.gaussian_filter(plain, FINE * PX)
    fine = level - ndimage.gaussian_filter(level * plain, FINE * PX) / np.maximum(near, 1e-6)
    fine *= plain
    relief = 128 + 127 * np.clip(fine / (3 * fine[plain > 0.5].std()), -1, 1)
    Image.fromarray(relief.astype(np.uint8), "L").save(RELIEF)

    # The creases themselves, for the wall's shape, from the photograph's shading. Its light fell from the crimp's end
    # and a little from the left (LIGHT, toward it in the print, x across and y down), so a facet tilted toward it
    # is lighter and one tilted away darker: the shading is the slope along that way, SLOPE em up per unit of
    # log brightness. The height whose slope that is comes from a Poisson solve. Where there is ink, and in the
    # glints, the shading is not the metal's: there the slope is carried over smoothly from the lacquer round it.
    # The photographer's shadow is not the metal's either.
    plain = plain * (1 - box[..., 0])
    shade = np.clip(level, -0.6, 0.25)
    shade = shade - ndimage.gaussian_filter(shade * plain, 0.8 * PX) / np.maximum(ndimage.gaussian_filter(plain, 0.8 * PX), 1e-6)
    near = ndimage.gaussian_filter(plain, 0.05 * PX)
    filled = ndimage.gaussian_filter(shade * plain, 0.05 * PX) / np.maximum(near, 1e-6)
    shade = shade * plain + filled * (1 - plain) * np.clip(near / 0.2, 0, 1)
    # Under the photographer's shadow the crumples are borrowed from the other side of the front, mirrored.
    hidden = box[..., 0]
    shade = shade * (1 - hidden) + shade[:, ::-1] * hidden
    dx, dy = LIGHT / np.hypot(*LIGHT)
    slope = -SLOPE * shade
    gx, gy = slope * dx, slope * dy
    # Mirrored down, so the solve wraps cleanly both ways; once round already wraps across.
    gx = np.concatenate((gx, gx[::-1]), 0)
    gy = np.concatenate((gy, -gy[::-1]), 0)
    div = (np.roll(gx, -1, 1) - np.roll(gx, 1, 1)) / 2 + (np.roll(gy, -1, 0) - np.roll(gy, 1, 0)) / 2
    fy, fx = np.meshgrid(np.fft.fftfreq(div.shape[0]), np.fft.fftfreq(div.shape[1]), indexing="ij")
    lap = -(np.sin(np.pi * fx) ** 2 + np.sin(np.pi * fy) ** 2) * 4
    lap[0, 0] = 1
    solved = np.fft.fft2(div) / lap
    solved[0, 0] = 0
    height = np.real(np.fft.ifft2(solved))[:rows_out] / PX
    # The tube's own roundness the model has already: only the crumples, finer than an em or so, are kept.
    height -= ndimage.gaussian_filter(height, (BULGE * PX, BULGE * PX), mode=("nearest", "wrap"))
    # Thin metal folds in flat facets meeting at sharp creases: the finest of the solve, which a Poisson solve
    # always softens, given back.
    height += SHARPEN * (height - ndimage.gaussian_filter(height, 0.05 * PX, mode=("nearest", "wrap")))
    span = float(np.abs(height).max())
    Image.fromarray(((height / span * 0.5 + 0.5) * 65535).astype(np.uint16)).save(HEIGHT)
    with open(SHAPE) as file:
        record = json.load(file)
    record["crumple"] = span
    with open(SHAPE, "w") as file:
        json.dump(record, file)
    print("crumples", round(height.std(), 4), "em deep (sd),", round(span, 3), "at most")
    print(cols_out, "x", rows_out, "white", round(white.mean(), 3), "crimp", round(a[0], 2), "shoulder", round(a[-1], 2), "em half width")


if __name__ == "__main__":
    main()
