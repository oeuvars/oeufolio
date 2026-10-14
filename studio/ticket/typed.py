# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""The email address typed on the ticket, as a box office would type it on: on a manual typewriter, after the ticket
was printed, so it is the typewriter's own letters and not a font.

    uv run studio/ticket/typed.py [--proof DIR]

studio/ticket/assets/typewriter.png is a type specimen typed on a Hermes Rocket in 1959 and scanned flat (Arlo James
Barnes, public domain, Wikimedia Commons: File:Hermes_Rocket_1959_type_specimen.png). Every character here is one
its type slugs struck, lifted from the scan by its column, with the grain of the ribbon's cloth still in its ink,
and set down again on the machine's fixed pitch, each on the baseline it was struck on. Where the specimen has a
letter twice the copies take turns, so two strikes of the same key are not the same strike.

Writes studio/ticket/art/typed.png, white where the ink is, at PX_PER_EM, with TEXT's characters ticket.json's
"typed" pitch apart from its x, on its baseline; and studio/ticket/art/typed.json, the box on the ticket it fills.
"""

import argparse
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TICKET = json.load(open(os.path.join(ROOT, "src", "components", "ticket", "ticket.json")))
TEXT = "sudo@anurag.gg"
PITCH = 58.3  # the machine's pitch on the scan, in its pixels: ten characters to the inch
PX_PER_EM = 192
TILT = -0.3  # degrees: the ticket went into the typewriter not quite square
# The specimen's lines, in its pixels: the band each takes up, and where the line starts.
LINES = {"serial": (232, 335, 1012), "qwerty": (545, 670, 1011), "asdf": (665, 780, 1005), "caps": (665, 780, 1771), "zxcv": (775, 885, 1005)}
# Every character used: the line it is on, its place along the line, and the baseline it was struck on.
GLYPHS = {
    "s": [("serial", 0, 306), ("asdf", 1, 746)],
    "u": [("qwerty", 6, 630), ("serial", 8, 302)],
    "d": [("asdf", 2, 745)],
    "o": [("qwerty", 8, 629)],
    "@": [("caps", 10, 748)],
    "a": [("asdf", 0, 747), ("serial", 4, 306)],
    "n": [("zxcv", 5, 847), ("serial", 7, 302)],
    "r": [("serial", 2, 305), ("serial", 12, 300)],
    "g": [("asdf", 4, 746)],
    ".": [("zxcv", 8, 848)],
}


def lift(page, line, place, base):
    """One strike off the scan: the ink in its column, keeping only the marks whose middle lies in it, so a
    neighbour's serif that reaches across is left behind. Returns the strike, as wide as the pitch, and how far its
    top lies above the baseline."""
    top, bottom, start = LINES[line]
    x0 = round(start + place * PITCH)
    crop = page[top:bottom, x0 - 8 : x0 + round(PITCH) + 8]
    labels, count = ndimage.label(crop > 0.12)
    keep = np.zeros(crop.shape, dtype=bool)
    for i, where in enumerate(ndimage.find_objects(labels), 1):
        cx = (where[1].start + where[1].stop) / 2
        # A mark too small to be part of a letter is a speck of ink on the specimen.
        if 8 <= cx <= crop.shape[1] - 8 and (labels[where] == i).sum() >= 40:
            keep |= labels == i
    strike = crop * ndimage.binary_dilation(keep, iterations=2)
    return strike, base - top


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof")
    args = parser.parse_args()

    grey = np.asarray(Image.open(os.path.join(HERE, "assets", "typewriter.png")).convert("L"), dtype=np.float64) / 255
    # The paper is not quite white and not even: the ink is how far a point is below the paper round it.
    paper = ndimage.median_filter(grey[::4, ::4], size=25)
    paper = np.asarray(Image.fromarray((paper * 255).astype(np.uint8)).resize(grey.shape[::-1], Image.Resampling.BILINEAR), dtype=np.float64) / 255
    page = np.clip((paper - grey - 0.06) / 0.5, 0, 1)

    strikes = {char: [lift(page, *where) for where in places] for char, places in GLYPHS.items()}
    turn = {char: 0 for char in strikes}
    rise = max(r for choices in strikes.values() for _, r in choices)
    fall = max(s.shape[0] - r for choices in strikes.values() for s, r in choices)
    out = np.zeros((rise + fall, round(PITCH * len(TEXT)) + 16))
    for i, char in enumerate(TEXT):
        strike, r = strikes[char][turn[char] % len(strikes[char])]
        turn[char] += 1
        y0, x0 = rise - r, round(i * PITCH)
        h, w = strike.shape
        out[y0 : y0 + h, x0 : x0 + w] = np.maximum(out[y0 : y0 + h, x0 : x0 + w], strike)

    # To the ticket, at the pitch ticket.json gives: the first character's cell starts at its x, the baseline at its
    # y. The strikes reach a little past their cells, so the picture starts a margin to the left of the first.
    x, baseline, pitch = TICKET["typed"]
    em = pitch / PITCH  # em to one pixel of the scan
    size = (round(out.shape[1] * em * PX_PER_EM), round(out.shape[0] * em * PX_PER_EM))
    typed = Image.fromarray((out * 255).astype(np.uint8)).rotate(TILT, Image.Resampling.BICUBIC).resize(size, Image.Resampling.LANCZOS)
    typed.save(os.path.join(HERE, "art", "typed.png"))
    box = [round(v, 4) for v in (x - 8 * em, baseline - rise * em, out.shape[1] * em, out.shape[0] * em)]
    json.dump({"box": box}, open(os.path.join(HERE, "art", "typed.json"), "w"))
    if args.proof:
        Image.fromarray(255 - np.asarray(typed)).save(os.path.join(args.proof, "typed.png"))
    print(f"typed {len(TEXT)} characters into", box)


main()
