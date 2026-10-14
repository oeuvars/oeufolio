# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""The cats printed on the ticket in place of the usernames, one beside each link, lifted from a sheet of cat
drawings the page was given (studio/ticket/assets/cats.png): the one with a knife in its teeth, the one hanging
from its own claw marks, and the one smoking.

    uv run studio/ticket/cats.py

Each is cut out of the sheet by its box, keeping only the strokes that are its own: a neighbour's stroke that
reaches into the box touches its edge, and is left behind. The sheet is small, so each is enlarged UP times and its
ink edge drawn again from the enlarged grey, as a pen leaves it. Writes studio/ticket/art/cat-<name>.png, white where
the ink is, and prints each one's width to height, which ticket.json's "cats" boxes keep.
"""

import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
UP = 3
# Each cat's box on the sheet, in its pixels: left, top, right, bottom.
CATS = {"knife": (190, 455, 425, 690), "scratch": (22, 305, 152, 652), "smoke": (510, 250, 725, 490)}


def main():
    sheet = Image.open(os.path.join(HERE, "assets", "cats.png")).convert("L")
    for name, (x0, y0, x1, y1) in CATS.items():
        crop = sheet.crop((x0, y0, x1, y1))
        grey = np.asarray(crop.resize((crop.width * UP, crop.height * UP), Image.Resampling.BICUBIC), dtype=np.float64) / 255
        ink = np.clip((0.6 - ndimage.gaussian_filter(grey, 0.8)) / 0.2, 0, 1)
        labels, count = ndimage.label(ink > 0.3)
        keep = np.zeros(ink.shape, dtype=bool)
        rows, cols = ink.shape
        for i, where in enumerate(ndimage.find_objects(labels), 1):
            touches = where[0].start == 0 or where[1].start == 0 or where[0].stop == rows or where[1].stop == cols
            if not touches:
                keep |= labels == i
        cat = ink * ndimage.binary_dilation(keep, iterations=2)
        r = np.where(cat.max(axis=1) > 0.2)[0]
        c = np.where(cat.max(axis=0) > 0.2)[0]
        cat = cat[r[0] : r[-1] + 1, c[0] : c[-1] + 1]
        Image.fromarray((cat * 255).astype(np.uint8)).save(os.path.join(HERE, "art", f"cat-{name}.png"))
        print(name, f"{cat.shape[1] / cat.shape[0]:.3f}")


main()
