# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "opencv-python-headless"]
# ///
"""The Leica's face, for leica.py to lay on its model: a Leica M3 with its collapsible 5 cm Summicron, photographed
straight on to its front (studio/ticket/assets/leica-m3.jpg: Hannes Grobe, CC BY 3.0, Wikimedia Commons,
File:Leica-m3_hg.JPG), the same camera and lens as the photograph the page was given, at 4256 pixels across.

    uv run studio/ticket/leica_face.py

The front of the body is found by its corners and scaled to the model's millimetres, 23.95 pixels to the
millimetre, which makes it 138 by 75. What is above the top cover, the knobs and the lever seen edge on, comes along,
so the knobs' sides have something to show. Writes studio/ticket/art/leica-front.png at PX_PER_MM, MARGIN mm round
the front on every side and TOP_MARGIN above it, and leica-body.png, the same with the lens's footprint on the
vulcanite filled with the vulcanite's own grain, for the body under the lens.
"""

import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
L, H = 138.0, 75.0
PX_PER_MM = 16
MARGIN, TOP_MARGIN = 12.0, 14.0
LENS = (78.7, 33.5)  # the lens's axis on the front, as leica.py has it
VULCANITE = (5.5, 55.0)  # the vulcanite's foot and top


def corners():
    """The front's corners in the photograph: the top cover's left end, its right end, then the bottom plate's right
    and left ends, read off the photograph's edges."""
    return np.float32([[495, 602], [3800, 602], [3800, 2398], [495, 2398]])


def main():
    photo = cv2.imread(os.path.join(HERE, "assets", "leica-m3.jpg"))
    k = PX_PER_MM
    w, h = round((L + 2 * MARGIN) * k), round((H + MARGIN + TOP_MARGIN) * k)
    # Model millimetres to the texture: x from MARGIN in, y up from the bottom with the top margin above.
    to = lambda x, y: ((x + MARGIN) * k, (H + TOP_MARGIN - y) * k)  # noqa: E731
    dst = np.float32([to(0, H), to(L, H), to(L, 0), to(0, 0)])
    warp = cv2.getPerspectiveTransform(corners(), dst)
    face = cv2.warpPerspective(photo, warp, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    cv2.imwrite(os.path.join(HERE, "art", "leica-front.png"), face)
    # The body's own: the photograph shows the lens's side lying over the vulcanite below it, as it looked down at
    # it; on the model the lens stands straight up, and that vulcanite shows. It is filled with the vulcanite's own
    # grain from the far end of the body, feathered in.
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    x_mm, y_mm = xs / k - MARGIN, H + TOP_MARGIN - ys / k
    swept = np.zeros((h, w), np.float32)
    for t in np.linspace(0, 1, 40):
        cy, r = LENS[1] - 1.0 * t, 26.6
        swept = np.maximum(swept, ((x_mm - LENS[0]) ** 2 + (y_mm - cy) ** 2 < r * r).astype(np.float32))
    swept *= (y_mm < VULCANITE[1]).astype(np.float32)
    swept = cv2.GaussianBlur(swept, (0, 0), 0.8 * k)
    x0, x1 = 102.0, 132.0
    sx = (x0 + np.mod(x_mm - x0, x1 - x0) + MARGIN) * k
    grain = cv2.remap(face, sx.astype(np.float32), ys, cv2.INTER_LINEAR)
    body = (face * (1 - swept[..., None]) + grain * swept[..., None]).astype(np.uint8)
    cv2.imwrite(os.path.join(HERE, "art", "leica-body.png"), body)
    print("face", w, "x", h)


main()
