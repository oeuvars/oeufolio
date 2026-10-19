# /// script
# dependencies = ["numpy", "pillow", "scipy"]
# ///
"""The coffee in the mug, taken from the user's photograph of a cup of it (art/coffee-photo.jpg): crema with milk
marbled through it and a ring of bubbles at the wall. The photograph looks down on the cup from a little in front, so
the round surface of the coffee is an ellipse in it, its near side hidden under the rim. That ellipse is found from
the coffee itself, by its colour, and drawn back out to a circle; where the rim or the wall hid the coffee, it is
filled with what lies just inside, mirrored, so the bubbles run on round the edge. Run from the repository root:

    uv run studio/desk/art/coffeephoto.py

It writes studio/desk/art/coffee-surface.png: PX pixels square, the surface's edge touching its sides, the far side
of the cup in the photograph at the top."""

import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO = os.path.join(HERE, "coffee-photo.jpg")
OUT = os.path.join(HERE, "coffee-surface.png")
PX = 1024
# Where the cup lies in the photograph, in pixels: an ellipse round it, its middle and its half widths. Coffee is
# looked for only inside it, so the brown of the desk under the cup is left out.
CUP = (290, 490, 250, 230)
# Coffee is brown: warmer red than green, green than blue, and this saturated. The white wall and the blue rim are not.
SATURATION = 0.28
# The mirror starts this far in from where the coffee was last seen, so the last ragged pixels at the wall are left out.
INSIDE = 0.97


def coffee(rgb):
    """Where the photograph shows coffee: one solid patch."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    top, bottom = rgb.max(-1), rgb.min(-1)
    brown = ((top - bottom) / (top + 1e-6) > SATURATION) & (r > g) & (g > b) & (b < 0.75)
    rows, cols = brown.shape
    y, x = np.mgrid[:rows, :cols]
    cx, cy, ax, ay = CUP
    brown &= ((x - cx) / ax) ** 2 + ((y - cy) / ay) ** 2 < 1
    brown = ndimage.binary_closing(brown, iterations=6)
    labels, count = ndimage.label(brown)
    sizes = ndimage.sum(brown, labels, range(1, count + 1))
    return ndimage.binary_fill_holes(labels == sizes.argmax() + 1)


def main():
    rgb = np.asarray(Image.open(PHOTO).convert("RGB")).astype(np.float32) / 255
    mask = coffee(rgb)
    # The ellipse with the patch's own spread: a filled ellipse's covariance is a quarter of its half axes squared.
    ys, xs = np.nonzero(mask)
    middle = np.array([xs.mean(), ys.mean()])
    spread = np.cov(np.vstack((xs, ys)))
    values, vectors = np.linalg.eigh(spread)
    axes = vectors @ np.diag(2 * np.sqrt(values)) @ vectors.T

    # Every pixel of the circle, in units of its radius, and how far out along its direction coffee was seen.
    u = (np.arange(PX) + 0.5) / PX * 2 - 1
    U, V = np.meshgrid(u, u)
    rho = np.hypot(U, V)
    theta = np.arctan2(V, U)
    angles = np.linspace(-np.pi, np.pi, 720, endpoint=False)
    steps = np.linspace(0, 1.2, 600)
    dirs = np.stack((np.cos(angles), np.sin(angles)))
    along = middle[:, None, None] + np.einsum("ij,jak->iak", axes, dirs[:, :, None] * steps[None, None, :])
    seen = ndimage.map_coordinates(mask.astype(np.float32), [along[1], along[0]], order=1) > 0.5
    # The first step out along each direction where the coffee ends.
    reach = steps[np.argmin(seen, axis=1) - 1]
    reach = ndimage.uniform_filter1d(reach, 9, mode="wrap") * INSIDE
    edge = np.interp(theta, angles, reach, period=2 * np.pi)
    # Past the edge, the coffee just inside it, mirrored.
    rho = np.where(rho > edge, np.maximum(2 * edge - rho, 0), rho)
    src = middle[:, None, None] + np.einsum("ij,jkl->ikl", axes, np.stack((rho * np.cos(theta), rho * np.sin(theta))))
    out = np.dstack([ndimage.map_coordinates(rgb[..., c], [src[1], src[0]], order=3, mode="nearest") for c in range(3)])
    Image.fromarray((np.clip(out, 0, 1) * 255).round().astype(np.uint8)).save(OUT)
    print(f"ELLIPSE middle {middle.round(2).tolist()} axes {axes.round(2).tolist()} -> {OUT}")


if __name__ == "__main__":
    main()
