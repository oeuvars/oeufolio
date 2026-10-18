# /// script
# dependencies = ["numpy", "pillow", "scipy"]
# ///
"""The watch's strap, taken from the user's photograph of it (art/watch-strap-photo.jpg) and unwarped flat: what
objects/watch.py lays over the top of each half. The photograph sees the strap undone and crossed, from a little
above: each half is followed down its middle (traced by hand, below), and the photograph sampled square across it,
edge to edge, so its creases, its stitches, its holes and the photograph's own light on them come out straight.
Run from the repository root:

    uv run studio/desk/art/strapphoto.py

It writes studio/desk/art/watch-strap-long.png and watch-strap-short.png: across, the strap's width; down, from the
end at the lugs to the tip, and to the fold round the buckle's bar; PX pixels to the photograph's pixel.

Where the short half lies across the long one in the photograph, the long half is hidden: that stretch is filled from
the short half's own creased middle and from the long half below its holes, feathered in."""

import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO = os.path.join(HERE, "watch-strap-photo.jpg")
PX = 2
# Each half's middle in the photograph, in pixels, from beyond its end at the lugs to beyond its far end; how far
# the middle traced lies off the strap's true middle, across, and how wide the strap is, in photograph pixels; and
# where along the trace (in photograph pixels) its end at the lugs and its far end lie.
LONG = ([(640, 140), (623, 168), (590, 248), (440, 522), (393, 650), (370, 712), (340, 795), (322, 850)], 3.0, 142.0, (25.0, 772.0))
SHORT = ([(650, 305), (618, 316), (555, 335), (400, 381), (350, 405), (255, 435), (200, 452), (160, 465)], -1.0, 135.0, (27.0, 479.0))
# The long half hidden under the short one: from this far along it, down to a line across it from this far along at
# its one edge to this far along at its other, the shadow included; but for the first hole, which shows, here (across
# from the one edge, in shares of the width, and along) and this round. It is filled from the short half, this far along
# it on, and from the long half's own, this far along it on, the two joined this far along the long half; feathered
# over this many photograph pixels, and the two sources over this many.
HIDDEN = (105.0, 292.0, 494.0)
SHOWN = (0.4, 357.0, 19.0)
FILL = (78.0, 530.0, 308.0)
FEATHER = 14.0
SEAM = 40.0


def spline(points, step):
    """A smooth path through points (Catmull and Rom), sampled every step pixels along it."""
    points = np.asarray(points, dtype=float)
    padded = np.vstack((2 * points[0] - points[1], points, 2 * points[-1] - points[-2]))
    dense = []
    for k in range(1, len(padded) - 2):
        p0, p1, p2, p3 = padded[k - 1 : k + 3]
        for t in np.linspace(0, 1, 80, endpoint=False):
            dense.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t**3))
    dense.append(points[-1])
    dense = np.array(dense)
    along = np.concatenate(([0], np.cumsum(np.linalg.norm(np.diff(dense, axis=0), axis=1))))
    s = np.arange(0, along[-1], step)
    return np.column_stack([np.interp(s, along, dense[:, axis]) for axis in range(2)])


def unwarp(photo, half):
    """The half laid straight: rows down it from its end at the lugs, every 1/PX of a photograph pixel; columns
    across it, edge to edge."""
    trace, off, width, (start, end) = half
    step = 1 / PX
    middle = spline(trace, step)
    ahead = np.gradient(middle, axis=0)
    ahead /= np.linalg.norm(ahead, axis=1)[:, None]
    normal = np.column_stack((-ahead[:, 1], ahead[:, 0]))
    rows = slice(int(start * PX), int(end * PX))
    across = off + np.arange(-width / 2, width / 2, step) + step / 2
    points = middle[rows, None, :] + across[None, :, None] * normal[rows, None, :]
    return np.stack([ndimage.map_coordinates(photo[..., k], [points[..., 1], points[..., 0]], order=3, mode="nearest") for k in range(3)], -1)


def resample(image, width):
    """An image's columns stretched or squeezed to width."""
    columns = image.shape[1]
    x = (np.arange(width) + 0.5) * columns / width - 0.5
    y = np.arange(image.shape[0])
    yy, xx = np.meshgrid(y, x, indexing="ij")
    return np.stack([ndimage.map_coordinates(image[..., k], [yy, xx], order=1, mode="nearest") for k in range(3)], -1)


def main():
    photo = np.asarray(Image.open(PHOTO).convert("RGB")).astype(np.float32)
    long = unwarp(photo, LONG)
    short = unwarp(photo, SHORT)
    # The fill, as wide as the long half: the short half's creased middle, then the long half's own below its holes.
    start = LONG[3][0]
    top, edge, other = HIDDEN
    from_short, from_long, joined = FILL
    rows = np.arange(long.shape[0]) / PX + start
    wide = resample(short, long.shape[1])
    first = wide[np.clip(((rows - top + from_short - SHORT[3][0]) * PX).astype(int), 0, wide.shape[0] - 1)]
    then = long[np.clip(((rows - joined + from_long - start) * PX).astype(int), 0, long.shape[0] - 1)]
    seam = np.clip((rows - joined) / SEAM + 0.5, 0, 1)[:, None, None]
    fill = first * (1 - seam) + then * seam
    # Laid over what the short half hides.
    across = np.linspace(0, 1, long.shape[1])[None, :]
    bottom = edge + (other - edge) * across
    inside = np.minimum((rows[:, None] - top) / FEATHER, (bottom - rows[:, None]) / FEATHER)
    u, a, round_ = SHOWN
    hole = np.hypot((across - u) * LONG[2], rows[:, None] - a)
    inside = np.minimum(inside, (hole - round_) / FEATHER)
    weight = np.clip(inside + 0.5, 0, 1)[..., None]
    long = long * (1 - weight) + fill * weight
    for name, image in (("long", long), ("short", short)):
        Image.fromarray(np.clip(image, 0, 255).astype(np.uint8)).save(os.path.join(HERE, f"watch-strap-{name}.png"))
        print(name, image.shape[1], "x", image.shape[0])


if __name__ == "__main__":
    main()
