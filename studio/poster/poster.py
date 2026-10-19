# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""The work page's poster: a copy of the reference poster (art/reference.jpg, 736 x 981), lit windows of a
block of flats at night with "human experience" glowing across them and four italic passages set between them,
printed at three times its size.

    node studio/poster/type.mjs      (after changing type.html or type.json)
    uv run studio/poster/poster.py [--proof DIR]

The windows, the dark wall and its light leaks are the reference's own, scaled up. The type is set again from the
plates type.mjs photographs (art/title.png, art/body.png), in the same place, so it is sharp at the new size: the old
passages are lifted off the wall first, and the title is laid over the old one as the reference has it, a photograph
of a lit sign, its letters soft, glowing, and broken into the dots of the screen it was shown on. Each company named in
the passages has a stroke of white highlighter run over it where type.mjs found it (src/components/poster.json), under
the print, so its letters come out dark on the stroke. New grain goes over the whole, at the new size, so the
scaled-up picture reads as film again.

The page is one material: the poster's bare wall, as a tile of paper. Writes public/objects/poster-paper.avif, that
tile; public/objects/poster.avif, the light printed on it (the windows, the sign and the passages, black where the
wall was), which the page screens over the paper; and public/objects/poster-strip.avif, the same for the work strip
folded: the poster's middle column of windows, the full height of it, with the sign's light across it but none of
the passages, which come with the page when the strip opens.
"""

import argparse
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCALE = 3
# The passages' boxes in the reference's pixels (left, top, right, bottom), a little past their ink.
PASSAGES = [(305, 302, 398, 453), (512, 374, 642, 451), (100, 484, 302, 561), (300, 622, 530, 709)]
# The folded strip's column, in the reference's pixels: the windows stacked down its middle.
STRIP = (300, 594)
# The paper tile: how many pixels of the poster it takes, and how many it is written at (twice the CSS pixels it
# is shown at, src/components/site-shell.tsx PAPER, the poster being shown about a third of its size).
PAPER_TAKES = 420
PAPER_SIZE = 280
# How far over the paper's own dark the wall's light has to be to count as light printed on it.
FLOOR = 0.012
# The type's colour: the passages are printed a warm white, the sign is a cold one.
INK = np.array([0.93, 0.91, 0.87])
SIGN = np.array([0.90, 0.91, 0.92])
# The highlighter: a white paint marker, a little less than opaque, and the companies it is run over.
MARKER = np.array([0.93, 0.92, 0.89])
MARKS = os.path.join(ROOT, "src", "components", "poster.json")


def load(name):
    return np.asarray(Image.open(os.path.join(HERE, "art", name)).convert("RGB")).astype(np.float32) / 255


def plate(name, size):
    image = Image.open(os.path.join(HERE, "art", name)).convert("L")
    if image.size != size:
        raise SystemExit(f"art/{name} is {image.size}, not {size}: run studio/poster/type.mjs again.")
    return np.asarray(image).astype(np.float32) / 255


def box_mask(shape, boxes, feather):
    """1 inside the boxes (scaled up), falling off softly past their edges."""
    mask = np.zeros(shape, np.float32)
    for left, top, right, bottom in boxes:
        mask[top * SCALE : bottom * SCALE, left * SCALE : right * SCALE] = 1
    return ndimage.gaussian_filter(mask, feather)


def lift_type(picture, mask):
    """The wall under the passages with their letters taken off: a grey opening wider than a stroke keeps what is
    broad (the window frames, the title's glow) and drops what is thin."""
    size = 6 * SCALE + 1
    bare = np.stack([ndimage.grey_opening(picture[..., c], size=(size, size)) for c in range(3)], -1)
    bare = np.stack([ndimage.gaussian_filter(bare[..., c], SCALE) for c in range(3)], -1)
    return picture * (1 - mask[..., None]) + bare * mask[..., None]


def lift_sign(picture, title):
    """The wall with the old sign's letters filled in from round them, so none of them shows past the new ones."""
    under = ndimage.grey_dilation(title, size=(4 * SCALE + 1, 4 * SCALE + 1))
    under = np.clip(1.5 * ndimage.gaussian_filter(under, 0.5 * SCALE), 0, 1)
    keep = 1 - under
    # From close by where there is wall close by, and from further off where the letters crowd it out.
    def spread(image):
        return ndimage.gaussian_filter(image, 3 * SCALE) + 0.05 * ndimage.gaussian_filter(image, 10 * SCALE)

    fill = np.stack([spread(picture[..., c] * keep) for c in range(3)], -1) / (spread(keep) + 1e-6)[..., None]
    return picture * keep[..., None] + fill * under[..., None]


def paper(image):
    """The flattest square of bare wall in the poster, made to repeat without a seam: the square and the same square
    turned half over in both directions, mixed so each edge is the middle of the other, and its slow light taken out."""
    luma = ndimage.gaussian_filter(image @ np.array([0.2126, 0.7152, 0.0722], np.float32), 12)
    best = None
    for top in range(0, image.shape[0] - PAPER_TAKES, 40):
        for left in range(0, image.shape[1] - PAPER_TAKES, 40):
            patch = luma[top : top + PAPER_TAKES, left : left + PAPER_TAKES]
            score = patch.std() + abs(patch.mean() - 0.05)
            if best is None or score < best[0]:
                best = (score, top, left)
    _, top, left = best
    square = image[top : top + PAPER_TAKES, left : left + PAPER_TAKES]
    half = PAPER_TAKES // 2
    rolled = np.roll(square, (half, half), (0, 1))
    ramp = 1 - np.abs(np.linspace(-1, 1, PAPER_TAKES, dtype=np.float32))
    weight = np.minimum.outer(ramp, ramp)[..., None]
    rolled_weight = np.roll(weight, (half, half), (0, 1))
    tile = (square * weight + rolled * rolled_weight) / (weight + rolled_weight + 1e-6)
    tile = np.asarray(Image.fromarray((np.clip(tile, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((PAPER_SIZE, PAPER_SIZE), Image.LANCZOS))
    tile = tile.astype(np.float32) / 255
    # Only the grain is kept: the wall's slow light would show as a pattern where the tile repeats.
    slow = np.stack([ndimage.gaussian_filter(tile[..., c], PAPER_SIZE / 16, mode="wrap") for c in range(3)], -1)
    return tile - slow + tile.mean((0, 1))


def wander(rng, count, smooth):
    """A slow random line, count samples long, about -1 to 1."""
    line = ndimage.gaussian_filter(rng.standard_normal(count + 8 * int(smooth)), smooth, mode="wrap")
    line = line[4 * int(smooth) : 4 * int(smooth) + count]
    return line / (np.abs(line).max() + 1e-6)


def highlighter(shape, marks, rng):
    """How much of the highlighter covers each pixel: one stroke a word, laid from a little before it to a little
    past it, over the letters' bodies and not quite up to their capitals. A stroke by hand: tilted a hair, its edges
    not quite straight, its chisel ends cut on a slant and ragged where the tip lifts, streaked along its length where
    the felt laid more or less paint, and a little heavier along its edges, where the paint pools. The paint lies on
    the paper as paint does: it skips over the paper's tooth in specks, more as the tip runs dry towards the tail and
    along the edges, and it lies thicker and thinner in blotches. Then the camera takes it as it took the windows,
    its edges as soft as theirs and its blotches the size of their grain."""
    cover = np.zeros(shape, np.float32)
    for mark in marks:
        size = mark["size"] * SCALE
        start = (mark["left"] - 0.06 * mark["size"]) * SCALE
        end = (mark["right"] + 0.26 * mark["size"]) * SCALE
        middle = (mark["baseline"] - 0.32 * mark["size"]) * SCALE
        half = 0.55 * size
        top, bottom = int(middle - 2 * size), int(middle + 2 * size)
        left, right = int(start - size), int(end + size)
        y, x = np.mgrid[top:bottom, left:right].astype(np.float32)
        tilt = np.radians(rng.uniform(-0.9, 0.4))
        u = x - start
        v = (y - middle) - np.tan(tilt) * u
        # Its edges, wavering a little along its length.
        along = np.clip(u, 0, end - start).astype(int)
        upper = half * (1 + 0.04 * wander(rng, int(end - start) + 1, 6 * SCALE))[along]
        lower = half * (1 + 0.04 * wander(rng, int(end - start) + 1, 6 * SCALE))[along]
        edge = 0.35 * SCALE
        across = np.clip((v + upper) / edge, 0, 1) * np.clip((lower - v) / edge, 0, 1)
        # Its ends, cut on the chisel's slant and ragged across the stroke where the tip lifts.
        rows = np.clip(((v + 2 * size) / (4 * size)) * 4 * size, 0, 4 * size - 1).astype(int)
        slant = 0.18 * v
        head = start + slant + 0.5 * SCALE * wander(rng, int(4 * size), 0.8 * SCALE)[rows]
        tail = end + slant + 0.8 * SCALE * wander(rng, int(4 * size), 0.6 * SCALE)[rows]
        ends = np.clip((x - head) / edge, 0, 1) * np.clip((tail - x) / (1.5 * edge), 0, 1)
        # Its streaks, lines along it, and the paint pooled at its edges.
        streak = 0.93 + 0.07 * wander(rng, int(4 * size), 0.5 * SCALE)[rows]
        pool = 1 + 0.04 * np.exp(-np.minimum(v + upper, lower - v).clip(0) / (0.8 * SCALE))
        # The tooth: specks of bare paper, a few at the head, more towards the tail and the edges.
        tooth = ndimage.gaussian_filter(rng.standard_normal(u.shape).astype(np.float32), 0.4 * SCALE)
        tooth /= tooth.std()
        dry = np.clip(u / (end - start), 0, 1) + 1.5 * np.exp(-np.minimum(v + upper, lower - v).clip(0) / (0.6 * SCALE))
        bare = np.clip((tooth - (2.4 - 0.9 * dry)) / 0.5, 0, 1)
        stroke = np.clip(0.97 * across * ends * streak * pool * (1 - 0.85 * bare), 0, 1)
        window = cover[top:bottom, left:right]
        cover[top:bottom, left:right] = 1 - (1 - window) * (1 - stroke)
    # The blotches, then the lens.
    blotch = ndimage.gaussian_filter(rng.standard_normal(shape).astype(np.float32), 1.2 * SCALE)
    cover *= 1 + 0.05 * blotch / blotch.std()
    return np.clip(ndimage.gaussian_filter(cover, 0.6 * SCALE), 0, 1)


def screen_dots(shape, pitch):
    """The sign's screen, a grid of lit dots turned 45 degrees, 1 on a dot and 0 between."""
    y, x = np.mgrid[0 : shape[0], 0 : shape[1]].astype(np.float32)
    u, v = (x + y) / np.sqrt(2), (x - y) / np.sqrt(2)
    return 0.5 + 0.5 * np.cos(2 * np.pi * u / pitch) * np.cos(2 * np.pi * v / pitch)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof", help="also write the poster as a PNG into this folder")
    args = parser.parse_args()

    source = Image.open(os.path.join(HERE, "art", "reference.jpg")).convert("RGB")
    size = (source.width * SCALE, source.height * SCALE)
    picture = np.asarray(source.resize(size, Image.LANCZOS)).astype(np.float32) / 255
    shape = picture.shape[:2]

    # The old passages come off the wall.
    picture = lift_type(picture, box_mask(shape, PASSAGES, 1.5 * SCALE))

    # The sign: its letters a little out of focus, made of dots, in place of the old ones, then the light they throw.
    title = plate("title.png", size)
    picture = lift_sign(picture, title)
    letters = ndimage.gaussian_filter(title, 1.1 * SCALE)
    dots = screen_dots(shape, 2.1 * SCALE)
    face = SIGN * (0.6 + 0.34 * dots)[..., None]
    picture = picture * (1 - letters[..., None]) + face * letters[..., None]
    glow = 0.42 * ndimage.gaussian_filter(title, 3 * SCALE) + 0.18 * ndimage.gaussian_filter(title, 12 * SCALE)
    glow = np.clip(glow, 0, 1)[..., None] * SIGN
    picture = 1 - (1 - picture) * (1 - glow)

    strip = picture

    # The highlighter goes over the companies before the passages are printed, so their letters print dark on it.
    with open(MARKS) as file:
        marks = json.load(file)["marks"]
    stroke = highlighter(shape, marks, np.random.default_rng(11))[..., None]
    picture = picture * (1 - stroke) + MARKER * stroke

    # The new passages go on in the old ones' place, a touch soft, as print on a print is. They are printed as the
    # reference prints them, as a difference: white on the dark wall, dark where they run into the sign's glow, and
    # gone under its letters.
    ink = ndimage.gaussian_filter(plate("body.png", size), 0.45 * SCALE) * (1 - np.clip(1.4 * letters, 0, 1))
    picture = picture * (1 - ink[..., None]) + np.abs(picture - INK) * ink[..., None]

    # Grain at the new size, a little stronger in the middle tones, as film's is.
    rng = np.random.default_rng(7)
    grain = ndimage.gaussian_filter(rng.standard_normal(shape).astype(np.float32), 0.7)

    def grained(image):
        luma = image @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        return image + (0.035 + 0.05 * luma * (1 - luma))[..., None] * grain[..., None]

    # The paper: the poster's bare wall, grain and all, as a tile. The page is made of it, round the poster and under it.
    sheet = paper(np.clip(grained(picture), 0, 1))
    write(Image.fromarray((sheet * 255 + 0.5).astype(np.uint8)), "poster-paper", args.proof)

    # The poster itself is only the light printed on that paper: the windows, the sign and its glow, the passages. The
    # wall is the paper's own dark, so what is no brighter than it comes off, and the page lays the rest over the paper
    # as light (a screen), so the wall it shows is the paper.
    floor = sheet.reshape(-1, 3).mean(0) + FLOOR
    left, right = (x * SCALE for x in STRIP)
    for name, image in (("poster", picture), ("poster-strip", strip)):
        light = np.clip(image - floor, 0, None)
        lit = np.clip(light.max(-1) / 0.06, 0, 1)[..., None]
        light = grained(light) * lit + light * (1 - lit)
        if name == "poster-strip":
            light = light[:, left:right]
        write(Image.fromarray((np.clip(light, 0, 1) * 255 + 0.5).astype(np.uint8)), name, args.proof)


def write(image, name, proof):
    image.save(os.path.join(ROOT, "public", "objects", f"{name}.avif"), quality=82, subsampling="4:4:4", speed=2)
    if proof:
        os.makedirs(proof, exist_ok=True)
        image.save(os.path.join(proof, f"{name}.png"))

if __name__ == "__main__":
    main()
