# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "opencv-python-headless"]
# ///
"""The top of the film roll, for film.py to lay on the wound film: a real roll of 35 mm film on its orange plastic
core, photographed lying on a table (studio/ticket/assets/film-roll.jpg: DR Kulturarvsprojekt, CC BY-SA 2.0,
Wikimedia Commons, File:35mm_blank_film_(6498625859)_(cropped_version).jpg), seen from straight above.

    uv run studio/ticket/roll_top.py

The photograph looks at the roll from the side and above, so its round top is an ellipse, as tall as CIRCLE's
squash of its width. It is cut out round the roll's outer turn and stretched back to a circle. Writes
studio/ticket/art/roll-top.png, square, the roll's outer turn touching its edges, clear outside it and through the
spindle hole. film.py sizes the core to CORE of the roll and the hole to HOLE of the core.
"""

import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
# The top in the photograph, in its pixels: the centre, the outer turn's half width, and how much shorter it is tall.
CIRCLE = ((1000, 394), 496, 0.625)
CORE = 0.516  # the core's radius, of the outer turn's
HOLE = 0.39  # the spindle hole's, of the core's
SIZE = 1024


def main():
    photo = cv2.imread(os.path.join(HERE, "assets", "film-roll.jpg"))
    (cx, cy), a, squash = CIRCLE
    k = SIZE / (2 * a)
    # Straighten: x as it is, y stretched back by the squash, centred.
    warp = np.float32([[k, 0, SIZE / 2 - k * cx], [0, k / squash, SIZE / 2 - k * cy / squash]])
    top = cv2.warpAffine(photo, warp, (SIZE, SIZE), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    r = np.hypot(xx - SIZE / 2 + 0.5, yy - SIZE / 2 + 0.5) / (SIZE / 2)
    alpha = np.clip((0.965 - r) * SIZE / 2, 0, 1) * np.clip((r - CORE * HOLE) * SIZE / 2, 0, 1)
    cv2.imwrite(os.path.join(HERE, "art", "roll-top.png"), np.dstack((top, (alpha * 255).astype(np.uint8))))
    print("top", SIZE)


main()
