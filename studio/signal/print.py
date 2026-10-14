# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""Prints the signal (studio/signal/render.py) as the references are printed: a coarse four-colour halftone in
loud colour, the dots a little ragged where the ink spread into the paper and the inks a hair out of register.

First the Turkish Vans (studio/signal/cats.py) are pasted down the post, as the poster's eyes were pasted into its
signal. The post is their floor: the picture is turned a quarter round for them, so their up is the strip's right and
they walk, sit and sleep along the strip's length, each on the post's edge, some with a tail hung over it. Each is
cut round with a dark line, as the eyed sunflower is, so the white cats hold their shape on the white paper.

    uv run studio/signal/print.py [--proof DIR]

Each ink is screened at its own angle with a round dot that grows into a chequer at half tone and closes to white
holes in the shadows, as an offset screen does. The screens are drawn at three times the picture's size and brought
down, so the dots' edges are soft as printed dots are and not stepped.

Writes public/objects/signal.avif: the inks on white paper, which the page multiplies onto the spine's own paper.
"""

import argparse
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
UP = 3
PITCH = 6.0  # the screen's ruling, in the picture's pixels
# Each ink as what it lets through of white light, its screen angle and how far it sits out of register.
INKS = {
    "cyan": ((0.0, 0.6, 0.88), 15, (0.6, -0.4)),
    "magenta": ((0.9, 0.08, 0.42), 75, (-0.5, 0.5)),
    "yellow": ((1.0, 0.88, 0.04), 0, (0.0, 0.0)),
    "black": ((0.1, 0.1, 0.11), 45, (0.0, 0.0)),
}


def separate(rgb):
    """Splits a colour into cyan, magenta, yellow and black, the black taking all of the grey, so a dark colour is
    black with one or two inks in its gaps and not a scatter of all three."""
    # The black runs heavy, so the dark paint prints as a solid with only small holes in it.
    k = np.clip((1 - rgb.max(axis=2)) * 1.25, 0, 1) ** 0.85
    rest = np.clip((1 - rgb - k[..., None]) / np.maximum(1 - k[..., None], 1e-3), 0, 1)
    return {"cyan": rest[..., 0], "magenta": rest[..., 1], "yellow": rest[..., 2], "black": k}


# Down the post from the signal: each cat, how tall it stands off the post as a share of the picture's width, how
# far down its cut-out its feet are (below that its tail hangs over the post), and whether it faces up the post.
CATS = [
    ("ledge", 0.5, 0.62, True),
    ("walk", 0.5, 1.0, True),
    ("sleep", 0.27, 0.86, False),
    ("sit", 0.55, 0.98, True),
    ("loaf", 0.36, 0.95, False),
    ("back", 0.52, 0.6, True),
    ("paw", 0.34, 0.7, False),
    ("sniff", 0.32, 0.95, True),
    ("momo", 0.55, 0.98, False),
]
GAP = 0.05  # between one cat and the next, as a share of the width
KEYLINE = 3  # the line cut round each cat, in pixels


def lay_cats(signal):
    """Pastes the cats down the post of the signal, an RGBA image, and returns it."""
    w = signal.width
    alpha = np.asarray(signal.getchannel("A"), dtype=np.float32) / 255 > 0.5
    across = alpha.sum(axis=1)
    # The post is the run of rows below the head that are only as wide as it is.
    head = int(np.argmax(across > 0.6 * w))
    rows = np.nonzero((across > 0) & (across < 0.25 * w) & (np.arange(len(across)) > head))[0]
    right = np.array([np.nonzero(alpha[y])[0].max() for y in rows])
    slope, offset = np.polyfit(rows, right, 1)
    edge = lambda y: offset + slope * y
    lean = np.degrees(np.arctan(slope))
    out = signal.copy()
    y = rows[0] + 0.12 * w
    for name, tall, ground, up in CATS:
        cat = Image.open(os.path.join(HERE, "art", "cats", f"{name}-cut.png"))
        scale = tall * w / (ground * cat.height)
        cat = cat.resize((round(cat.width * scale), round(cat.height * scale)), Image.LANCZOS)
        if up:
            cat = cat.transpose(Image.FLIP_LEFT_RIGHT)
        length = cat.width
        # A quarter turn clockwise: the cat's up is the strip's right, its feet on a line down the strip.
        feet = np.array([cat.height * (1 - ground), cat.width / 2])
        cat = cat.rotate(-90, expand=True)
        # Then tilted with the post, round its own middle.
        middle = np.array(cat.size) / 2
        cat = cat.rotate(-lean, expand=True, resample=Image.BICUBIC)
        a = np.radians(-lean)
        d = feet - middle
        feet = np.array([np.cos(a) * d[0] + np.sin(a) * d[1], -np.sin(a) * d[0] + np.cos(a) * d[1]]) + np.array(cat.size) / 2
        centre = y + length / 2
        at = (round(edge(centre) - 0.035 * w - feet[0]), round(centre - feet[1]))
        # The cut line, then the cat on it.
        shape = np.asarray(cat.getchannel("A"), dtype=np.float32) / 255
        line = ndimage.grey_dilation(shape, footprint=disc(KEYLINE))
        keyline = Image.fromarray(np.dstack([np.full_like(line, 22), np.full_like(line, 22), np.full_like(line, 24), line * 255]).astype(np.uint8), "RGBA")
        out.alpha_composite(keyline, dest=(max(at[0], 0), at[1]), source=(max(-at[0], 0), 0))
        out.alpha_composite(cat, dest=(max(at[0], 0), at[1]), source=(max(-at[0], 0), 0))
        y += length + GAP * w
        if y > signal.height:
            break
    return out


def disc(radius):
    ys, xs = np.mgrid[-radius : radius + 1, -radius : radius + 1]
    return xs * xs + ys * ys <= radius * radius


def screen(cover, angle, offset, rng):
    h, w = cover.shape
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    xs, ys = xs / UP - offset[0], ys / UP - offset[1]
    a = np.radians(angle)
    u = (xs * np.cos(a) + ys * np.sin(a)) * 2 * np.pi / PITCH
    v = (-xs * np.sin(a) + ys * np.cos(a)) * 2 * np.pi / PITCH
    spot = (np.cos(u) + np.cos(v)) / 2  # 1 in the middle of a dot, -1 between them
    # The ink creeps along the paper's fibres, so a dot's edge wanders.
    fibre = ndimage.gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), UP * 0.7)
    fibre /= fibre.std()
    # Only where there is ink to spread: blank paper takes none.
    level = (spot + 1) / 2 + 0.025 * fibre * np.sqrt(np.clip(cover * (1 - cover) * 4, 0, 1))
    return np.where(cover > 0.015, np.clip((level - (1 - cover)) * UP * 2.2 + 0.5, 0, 1), 0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=os.path.join(HERE, "art", "signal.png"))
    parser.add_argument("--proof")
    args = parser.parse_args()

    image = np.asarray(lay_cats(Image.open(args.source).convert("RGBA")), dtype=np.float32) / 255
    alpha = image[..., 3:]
    rgb = image[..., :3] * alpha + (1 - alpha)
    # A press gains contrast and pushes colour: the dark paint goes deep and the lamps stay bright.
    rgb = np.clip((rgb - 0.5) * 1.12 + 0.5, 0, 1)
    grey = rgb.mean(axis=2, keepdims=True)
    rgb = np.clip(grey + (rgb - grey) * 1.45, 0, 1)
    h, w = rgb.shape[:2]
    big = np.asarray(Image.fromarray((rgb * 255).astype(np.uint8)).resize((w * UP, h * UP), Image.BICUBIC), dtype=np.float32) / 255

    rng = np.random.default_rng(7)
    paper = np.ones_like(big)
    for name, cover in separate(big).items():
        through, angle, offset = INKS[name]
        dots = screen(cover, angle, offset, rng)
        paper *= 1 - dots[..., None] * (1 - np.array(through, dtype=np.float32))
    printed = np.asarray(Image.fromarray((np.clip(paper, 0, 1) * 255).astype(np.uint8)).resize((w, h), Image.LANCZOS), dtype=np.float32) / 255

    out = Image.fromarray((printed * 255).astype(np.uint8), "RGB")
    if args.proof:
        os.makedirs(args.proof, exist_ok=True)
        out.save(os.path.join(args.proof, "signal-print.png"))
        return
    out.save(os.path.join(ROOT, "public", "objects", "signal.avif"), quality=68, subsampling="4:4:4", speed=4)


main()
