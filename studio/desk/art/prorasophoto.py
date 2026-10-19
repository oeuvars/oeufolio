# /// script
# dependencies = ["numpy", "pillow", "scipy"]
# ///
"""The tube's print, taken from a photograph of a real one (art/proraso-photo.jpg, Proraso's own, the white tube lying
on its back on oats, seen from above) and unrolled flat: what objects/proraso.py lays over the front of the tube.
The photograph sees the front half of a tube flat at the crimp and nearly round at the shoulder. Each row is an oval
of the tube's girth, as wide as the tube is there in the photograph; the print is sampled evenly along that oval,
so it comes out at its true width all the way across. The photograph's own light is read off the white lacquer and
divided out, which also takes out its blue cast. Run from the repository root:

    uv run studio/desk/art/prorasophoto.py

It writes studio/desk/art/proraso-print.png: across, the front half of the tube, FRONT em, its middle in the middle;
down, from the crimped edge to the shoulder, LENGTH em; PX pixels to the em. Its alpha fades out toward the sides,
where the photograph sees the tube too obliquely to read."""

import math
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO = os.path.join(HERE, "proraso-photo.jpg")
OUT = os.path.join(HERE, "proraso-print.png")
# As objects/proraso.py has them: the front's flat width and the tube's length, crimp to shoulder, in em.
FRONT = math.pi * 5.0 / 2
LENGTH = 2.84 * FRONT
PX = 90
# The tube's two edges in the photograph, as x = a y^2 + b y + c in pixels, fitted along its length below the crimp;
# and how far inside them its lit face starts, past the dark line of its edge.
LEFT = (-2.2678e-06, 0.059964, 475.081)
RIGHT = (2.4104e-05, -0.092253, 849.814)
EDGE = 1.5
# The crimped edge, at its left and right corner, and the shoulder, in photograph rows.
CRIMP = (297.0, 303.0)
SHOULDER = 1265.0
# The crimp is flat and as wide as the front: its pixels to the em across. The girth follows from it.
ACROSS = (832.0 - 481.0) / FRONT
# The drawing in objects/proraso.py, which the sides keep, is laid out a little wider and longer than the
# photograph, and lower: the photograph is scaled across and down by these, then moved across and down by these (em),
# fitted on its inks.
ALIGN = (1.036, 1.042, -0.091, 0.201)
# The share of the front's half width over which the print fades out at either side.
FADE = (0.62, 0.8)
# The white lacquer: where the photograph is at least this light, and close to the lacquer's own colour.
WHITE = np.array([202.6, 204.4, 235.5])
# objects/proraso.py's lacquer white, #e4e4df.
BODY = (0xE4, 0xE4, 0xDF)


def linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def encode(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def arc(a, b, phi):
    """Distance along an oval of half width a and half depth b, from the middle of its front to angle phi."""
    t = np.linspace(0, 1, 513)[None, :] * phi[:, None]
    ds = np.hypot(a * np.cos(t), b * np.sin(t))
    return np.trapezoid(ds, t, axis=1)


def main():
    photo = np.asarray(Image.open(PHOTO).convert("RGB")).astype(np.float64)
    rows, cols = round(LENGTH * PX), round(FRONT * PX)
    # Each pixel of the print where the drawing has it, then where the photograph has it.
    sx, sy, tx, ty = ALIGN
    v = np.clip(((np.arange(rows) + 0.5) / PX - ty) / sy, 0.05, LENGTH)
    u = ((np.arange(cols) + 0.5) / PX - FRONT / 2 - tx) / sx
    girth = 2 * FRONT * ACROSS
    # Where each row of the print lies in the photograph: the crimp's corners are not quite level.
    top = np.array(CRIMP).mean()
    tilt = (CRIMP[1] - CRIMP[0]) / (832.0 - 481.0)
    ys = top + v / LENGTH * (SHOULDER - top)
    left = np.maximum(np.polyval(LEFT, ys), 481.0) + EDGE
    right = np.minimum(np.polyval(RIGHT, ys), 832.0) - EDGE
    middle, a = (left + right) / 2, (right - left) / 2
    # Each row's depth: the oval of the tube's girth as wide as the photograph shows it.
    b = np.zeros(rows)
    for i in range(rows):
        lo, hi = 0.0, a[i]
        for _ in range(40):
            mid = (lo + hi) / 2
            h = ((a[i] - mid) / (a[i] + mid)) ** 2
            perimeter = math.pi * (a[i] + mid) * (1 + 3 * h / (10 + math.sqrt(4 - 3 * h)))
            lo, hi = (mid, hi) if perimeter < girth else (lo, mid)
        b[i] = (lo + hi) / 2
    # Along each oval to each column of the print.
    phis = np.linspace(0, math.pi / 2, 721)
    xs = np.empty((rows, cols))
    for i in range(rows):
        s = arc(a[i], b[i], phis)
        reach = np.abs(u) * ACROSS
        xs[i] = middle[i] + np.sign(u) * a[i] * np.sin(np.interp(reach, s, phis, right=math.pi / 2))
    yy = ys[:, None] + tilt * (xs - middle[:, None])
    print_ = np.stack([ndimage.map_coordinates(photo[..., k], [yy, xs], order=3, mode="nearest") for k in range(3)], -1)

    # The photograph's light, read off the white lacquer and smoothed, more along the tube than round it.
    near = np.abs(print_ / WHITE - (print_ / WHITE).mean(-1, keepdims=True)).max(-1) < 0.05
    white = near & (print_.mean(-1) > 0.75 * WHITE.mean())
    white = ndimage.binary_erosion(white, iterations=3)
    sigma = (0.5 * PX, 0.12 * PX)
    weight = ndimage.gaussian_filter(white.astype(np.float64), sigma)
    light = np.stack([ndimage.gaussian_filter(print_[..., k] * white, sigma) for k in range(3)], -1) / np.maximum(weight, 1e-6)[..., None]
    # Where the print covers a whole stretch of the front, the light comes from further along.
    wide = (2.0 * PX, 0.4 * PX)
    far = ndimage.gaussian_filter(white.astype(np.float64), wide)
    broad = np.stack([ndimage.gaussian_filter(print_[..., k] * white, wide) for k in range(3)], -1) / np.maximum(far, 1e-6)[..., None]
    trust = np.clip(weight / 0.25, 0, 1)[..., None]
    light = light * trust + broad * (1 - trust)
    # Divided out in linear light, the lacquer coming to the white the model paints it.
    flat = np.clip(linear(print_ / 255) / np.maximum(linear(light / 255), 1e-3), 0, 1.1) * linear(np.array(BODY) / 255)
    # The photograph's compression leaves faint squares in the plain white: smoothed there, and only there.
    plain = ndimage.gaussian_filter(ndimage.binary_erosion(white, iterations=4).astype(np.float64), 2)[..., None]
    smooth = np.stack([ndimage.gaussian_filter(flat[..., k], 0.05 * PX) for k in range(3)], -1)
    flat = flat * (1 - plain) + smooth * plain
    srgb = np.clip(encode(flat) * 255, 0, 255)

    side = np.abs(u) / (FRONT / 2)
    alpha = np.clip((FADE[1] - side) / (FADE[1] - FADE[0]), 0, 1)
    alpha = np.broadcast_to(alpha * alpha * (3 - 2 * alpha), (rows, cols))
    out = np.dstack((srgb, alpha * 255)).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(OUT)
    print(cols, "x", rows, "white kept", round(white.mean(), 3))


if __name__ == "__main__":
    main()
