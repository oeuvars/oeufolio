# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""Prints the signal (studio/signal/render.py) as the references are printed: a coarse four-colour halftone in
loud colour, the dots a little ragged where the ink spread into the paper and the inks a hair out of register.

It stands against a clear sky, deep blue overhead and paler down the strip, printed in the same screens.

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
SENT = 360  # the width the page is sent
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


SKY_TOP = np.array([0.13, 0.38, 0.75], dtype=np.float32)
SKY_LOW = np.array([0.58, 0.78, 0.95], dtype=np.float32)


def sky(h, w):
    """The sky down the picture, a colour per row: deepest at the top, palest where the tallest screen ends."""
    t = np.clip(np.arange(h, dtype=np.float32) / (9 * w), 0, 1)[:, None] ** 0.85
    return SKY_TOP * (1 - t) + SKY_LOW * t


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

    signal = Image.open(args.source).convert("RGBA")
    air = sky(signal.height, signal.width)
    image = np.asarray(signal, dtype=np.float32) / 255
    alpha = image[..., 3:]
    rgb = image[..., :3] * alpha + air[:, None, :] * (1 - alpha)
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
    # The spine shows it about 250 pixels wide on a dense screen. Sent any larger, the screened sky only weighs more.
    out = out.resize((SENT, round(out.height * SENT / out.width)), Image.LANCZOS)
    if args.proof:
        os.makedirs(args.proof, exist_ok=True)
        out.save(os.path.join(args.proof, "signal-print.png"))
        return
    out.save(os.path.join(ROOT, "public", "objects", "signal.avif"), quality=62, subsampling="4:4:4", speed=4)


main()
