# /// script
# dependencies = ["numpy", "pillow", "scipy"]
# ///
"""The Seiko Prospex Alpinist SPB119's dial, taken from the user's photograph (art/watch-photo.jpg) and unwarped to
square on, 12 o'clock up: what objects/watch.py lays over its dial and compass ring from above. The photograph
sees the watch from a little to one side, so the round opening of the crystal is an ellipse in it: found along the
steel lip outside the cream ring, it is drawn back out to a circle, the ring's edge at RING_R, and turned upright.
The numerals, the indices, SEIKO, the hands and the date are the photograph's own. Run from the repository root:

    uv run studio/desk/art/watchphoto.py

It writes studio/desk/art/watch-dial.png: SIZE millimetres across, PX pixels to the millimetre, the middle of the
dial in the middle."""

import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO = os.path.join(HERE, "watch-photo.jpg")
OUT = os.path.join(HERE, "watch-dial.png")
SIZE = 36.0
PX = 60
# The crystal's opening in the photograph: the ellipse's middle, in pixels, and its matrix: a point p is on it where
# (p - CENTRE) . OPENING . (p - CENTRE) = 1.
CENTRE = [377.21, 521.865]
OPENING = [[3.49732e-05, 4.05961e-07], [4.05961e-07, 3.58522e-05]]
# The ellipse runs along the steel lip, outside the cream ring, whose edge lies at 15.8 of its 16.6 mm: so it is
# drawn out to this radius, the ring's edge at the 16.5 mm the model has it.
RING_R = 16.6 * 16.5 / 15.8
# The photograph's 12 o'clock leans this many degrees from upright.
TURN = 2.6


def main():
    photo = np.asarray(Image.open(PHOTO).convert("RGB")).astype(np.float32)
    weights, axes = np.linalg.eigh(np.array(OPENING))
    if np.linalg.det(axes) < 0:
        axes[:, 0] *= -1
    semi = 1 / np.sqrt(weights)
    n = round(SIZE * PX)
    steps = (np.arange(n) + 0.5) / PX - SIZE / 2
    x, y = np.meshgrid(steps, -steps)
    t = np.radians(TURN)
    # The dial in mm, 12 o'clock up, turned as the photograph has it, onto the unit circle and out to the ellipse.
    u = np.stack(((x * np.cos(t) - y * np.sin(t)) / RING_R, -(x * np.sin(t) + y * np.cos(t)) / RING_R), -1)
    at = np.array(CENTRE) + (u * semi) @ axes.T
    out = np.dstack([ndimage.map_coordinates(photo[..., k], [at[..., 1], at[..., 0]], order=3, mode="nearest") for k in range(3)])
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(OUT)
    print(OUT, out.shape)


main()
