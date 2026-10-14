# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""Cuts two of the signal's lamps out of their references, for studio/signal/render.py to lay in the housing:

    uv run studio/signal/cut.py

The sunflower with an eye for a heart is already a halftone print, on white. Its dots are taken out with a blur
before it is cut, since print.py screens the whole picture again and two screens over each other beat into a moire.
It is cut from its paper by the white that reaches in from the edges, so the white of the eye stays.

The Victoria lily pad is a painted plate on cream paper. It is cut as the round of everything that is not paper.

Writes studio/signal/art/sunflower.png and lily.png, square, with the flower filling the square.
"""

import os

import numpy as np
from PIL import Image
from scipy import ndimage

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art")


def load(name):
    return np.asarray(Image.open(os.path.join(ART, name)).convert("RGB"), dtype=np.float32) / 255


def save(rgb, alpha, name):
    ys, xs = np.nonzero(alpha > 0.5)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    half = int(max(ys.max() - ys.min(), xs.max() - xs.min()) / 2) + 4
    pad = half + 4
    rgba = np.dstack([rgb, alpha])
    rgba = np.pad(rgba, ((pad, pad), (pad, pad), (0, 0)))
    y0, x0 = int(cy) + pad - half, int(cx) + pad - half
    square = rgba[y0 : y0 + 2 * half, x0 : x0 + 2 * half]
    Image.fromarray((np.clip(square, 0, 1) * 255).astype(np.uint8), "RGBA").save(os.path.join(ART, name))


def sunflower():
    rgb = load("sunflower-reference.jpg")
    # The screen's pitch is about five pixels; a blur of that width leaves the tone and the drawing.
    soft = ndimage.gaussian_filter(rgb, sigma=(2.2, 2.2, 0))
    paper = soft.min(axis=2) > 0.86
    labels, _ = ndimage.label(paper)
    edge = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    outside = np.isin(labels, edge[edge > 0])
    inside = ndimage.binary_fill_holes(~outside)
    inside = ndimage.binary_opening(inside, iterations=2)
    alpha = ndimage.gaussian_filter(ndimage.binary_erosion(inside, iterations=3).astype(np.float32), 0.8)
    save(soft, alpha, "sunflower.png")


def lily():
    rgb = load("lily-reference.jpg")
    paper = np.array([0.93, 0.91, 0.86])
    away = np.abs(ndimage.gaussian_filter(rgb, sigma=(1.5, 1.5, 0)) - paper).max(axis=2) > 0.12
    pad = ndimage.binary_fill_holes(ndimage.binary_opening(away, iterations=3))
    labels, count = ndimage.label(pad)
    sizes = ndimage.sum(pad, labels, range(1, count + 1))
    pad = labels == 1 + int(np.argmax(sizes))
    alpha = ndimage.gaussian_filter(ndimage.binary_erosion(pad, iterations=3).astype(np.float32), 0.8)
    save(rgb, alpha, "lily.png")


sunflower()
lily()
