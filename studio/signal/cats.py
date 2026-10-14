# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""Cuts the van-patterned cats out of their photographs (studio/signal/art/cats, credited in CREDITS.md), for print.py to
lay along the signal's post:

    uv run studio/signal/cats.py

Each cat is lifted from its photograph by macOS's own subject cut-out (mask.swift, run through swift, so this needs
a Mac), the mask's edge drawn in a pixel and feathered, and the cat cropped to it. Grass lit one cat's white belly
green from below; the green is taken out of every cat, since none of them has any of its own, each coat's white is
set to the same white, and the auburn pushed up.

Writes art/cats/<name>-cut.png, the cat on clear ground.
"""

import os
import subprocess
import tempfile

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
CATS = os.path.join(HERE, "art", "cats")
WHITE = 0.97


def mask(source):
    with tempfile.TemporaryDirectory() as work:
        out = os.path.join(work, "mask.png")
        subprocess.run(["xcrun", "swift", os.path.join(HERE, "mask.swift"), source, out], check=True, capture_output=True)
        return np.asarray(Image.open(out).convert("L"), dtype=np.float32) / 255


def cut(name, file):
    source = os.path.join(CATS, file)
    rgb = np.asarray(Image.open(source).convert("RGB"), dtype=np.float32) / 255
    alpha = mask(source)
    if alpha.shape != rgb.shape[:2]:
        alpha = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).resize(rgb.shape[1::-1], Image.BILINEAR), dtype=np.float32) / 255
    inside = ndimage.binary_erosion(alpha > 0.5, iterations=1)
    alpha = ndimage.gaussian_filter(inside.astype(np.float32), 0.7)
    # Green off the white fur.
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    rgb[..., 1] = np.minimum(g, np.maximum(r, b))
    # The photographs were taken in all kinds of light. The white of each cat's coat is set to the same white,
    # the white of the sun on the signal.
    fur = np.percentile(rgb[alpha > 0.5], 92, axis=0)
    rgb = np.clip(rgb * (WHITE / fur), 0, 1)
    # And the auburn of the head and tail pushed up to the red a Van's is, which the screen would otherwise lose.
    grey = rgb.mean(axis=2, keepdims=True)
    rgb = np.clip(grey + (rgb - grey) * 1.6, 0, 1)
    ys, xs = np.nonzero(alpha > 0.05)
    box = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
    rgba = np.dstack([rgb, alpha])[box]
    Image.fromarray((np.clip(rgba, 0, 1) * 255).astype(np.uint8), "RGBA").save(os.path.join(CATS, f"{name}-cut.png"))
    print(name, rgba.shape[1], "x", rgba.shape[0])


for name, file in {
    "walk": "walk.png",
    "ledge": "ledge.jpg",
    "sleep": "sleep.jpg",
    "sniff": "sniff.jpg",
    "crouch": "crouch.jpg",
    "bw-stroll": "bw-stroll.jpg",
    "nap": "nap.jpg",
    "tabby": "tabby.jpg",
    "piper": "piper.jpg",
    "doze": "doze.jpg",
    "bw-sit": "bw-sit.jpg",
    "roof": "roof.jpg",
}.items():
    cut(name, file)
