# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3"]
# ///
"""The ID badge: the reference photograph itself, with the portrait and some of the words changed.

    uv run studio/badge.py

Everything that is not changed is the reference's own pixels, so the holder, the ring, the light on the
vinyl and the card are the photograph's and not a likeness of them. Three things are done to it:

- The page behind the holder is taken out. Where only vinyl lies over the page, the image keeps how much
  the vinyl darkens or lightens it and nothing else, so the vinyl is see-through on whatever page it is
  laid on, and on a white one it reads as the photograph does.
- The portrait is replaced inside the print's own outline, which sits a little askew in its printed box.
- The words in REWRITTEN are rubbed out to bare card and set again from studio/assets/overlay.png, which
  is a capture of studio/plate.html.

Writes public/objects/badge.avif at twice the reference's size. studio/badge_model.py is the earlier
Blender model of the same badge; the page does not use it.
"""

import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UP = 2  # output pixels to one of the reference's

# All in the reference's pixels.
HOLDER = (105, 15, 620, 882, 22)
RING = (345, 0, 442, 18)  # the part of the ring that stands clear of the holder
CARD = (162, 195, 577, 850)
# The corners of the portrait print, clockwise from the top left. It was stuck down by hand.
PRINT = ((274.2, 372.0), (456.8, 373.4), (458.4, 600.2), (271.4, 601.0))
BLANK = (478, 385, 566, 595)  # bare card, to take paper grain from
REWRITTEN = (
    (502.6, 236, 514, 257),  # the last figure of the drop number
    (190, 331, 560, 362),  # the line under the title
    (190, 653, 565, 660),  # the three rules
    (190, 708.5, 565, 715),
    (190, 764.5, 565, 771),
    (240, 603, 565, 665),  # and what is written on them
    (282, 665, 565, 721),
    (242, 721, 565, 781),
)
HAND_FROM = 603  # below this line the new words are handwriting
PRINT_INK = np.array([0.125, 0.13, 0.12])
MARKER_INK = np.array([0.2, 0.2, 0.205])


def blurred(a, sigma):
    """Gaussian blur of a float array of rows, columns and maybe channels. sigma is in pixels."""
    if a.ndim == 3:
        return np.dstack([blurred(a[..., c], sigma) for c in range(a.shape[2])])
    pad = int(sigma * 3) + 1
    padded = np.pad(a, pad, mode="reflect")
    fy = np.fft.fftfreq(padded.shape[0])[:, None]
    fx = np.fft.rfftfreq(padded.shape[1])[None, :]
    kernel = np.exp(-2 * (np.pi * sigma) ** 2 * (fx * fx + fy * fy))
    return np.fft.irfft2(np.fft.rfft2(padded) * kernel, s=padded.shape)[pad:-pad, pad:-pad]


def enlarged(a, method=Image.Resampling.BICUBIC):
    if a.ndim == 3:
        return np.dstack([enlarged(a[..., c], method) for c in range(a.shape[2])])
    rows, cols = a.shape
    return np.asarray(Image.fromarray(a.astype(np.float32), mode="F").resize((cols * UP, rows * UP), method), dtype=np.float64)


def inside(X, Y, x0, y0, x1, y1, soft=1.0, r=0.0):
    """Coverage of a rectangle, rounded by r, feathered over `soft` pixels."""
    qx = np.abs(X - (x0 + x1) / 2) - ((x1 - x0) / 2 - r)
    qy = np.abs(Y - (y0 + y1) / 2) - ((y1 - y0) / 2 - r)
    d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
    return np.clip(0.5 - d / soft, 0, 1)


def veil(ref):
    """What the vinyl does to the page, as a black or white film and how much of it."""
    lum = ref.mean(axis=-1)
    rows, cols = lum.shape
    Y, X = np.mgrid[0:rows, 0:cols].astype(np.float64)
    # The bare page, with the slow fall-off the photograph has across it, fitted where nothing covers it.
    bare = (X < 92) | (X > 634) | (Y > 893)
    a, b, c = np.linalg.lstsq(np.column_stack((np.ones(bare.sum()), X[bare], Y[bare])), lum[bare], rcond=None)[0]
    page = np.clip(a + b * X + c * Y, 0, 0.995)
    darker = np.clip(1 - lum / page, 0, 1)
    lighter = np.clip((lum - page) / (1 - page), 0, 1)
    white = (lum > page).astype(np.float64)
    amount = np.where(lum > page, lighter, darker)
    x0, y0, x1, y1, r = HOLDER
    kept = np.maximum(inside(X + 0.5, Y + 0.5, x0 - 2, y0 - 2, x1 + 2, y1 + 2, 1.5, r + 2), inside(X + 0.5, Y + 0.5, *RING, 1.5))
    return white, amount * kept


def paper(card, X, Y):
    """The card with nothing on it: its slow change of colour across the sheet, and its grain."""
    lum = card.mean(axis=-1)
    x0, y0, x1, y1 = (v * UP for v in CARD)
    (ax, ay), (bx, by), (cx, cy), (dx, dy) = PRINT
    clean = (lum > 0.9) & (inside(X, Y, x0 + 16, y0 + 16, x1 - 16, y1 - 16) > 0.5)
    clean &= inside(X, Y, (min(ax, dx) - 8) * UP, (min(ay, by) - 8) * UP, (max(bx, cx) + 8) * UP, (max(cy, dy) + 8) * UP) < 0.5
    weight = blurred(clean.astype(np.float64), 24)
    field = blurred(card * clean[..., None], 24) / np.maximum(weight, 1e-4)[..., None]
    gx0, gy0, gx1, gy1 = (v * UP for v in BLANK)
    patch = card[gy0:gy1, gx0:gx1]
    grain = patch - blurred(patch, 5)
    grain = np.concatenate((grain, grain[::-1]), axis=0)
    grain = np.concatenate((grain, grain[:, ::-1]), axis=1)
    rows, cols = card.shape[:2]
    tiled = np.tile(grain, (rows // grain.shape[0] + 1, cols // grain.shape[1] + 1, 1))[:rows, :cols]
    return field + tiled


def portrait(card, X, Y):
    """Lay the new print into the old one's outline, with the look of the old one: soft, and a little flat."""
    A, B, C, D = (np.array(p) * UP for p in PRINT)
    # A point of the outline is A + u(B - A) + v(D - A) + uv(A - B + C - D). Solve that for u and v.
    e, f, g = B - A, D - A, A - B + C - D
    u = np.full(X.shape, 0.5)
    v = np.full(X.shape, 0.5)
    for _ in range(6):
        fx = A[0] + u * e[0] + v * f[0] + u * v * g[0] - X
        fy = A[1] + u * e[1] + v * f[1] + u * v * g[1] - Y
        j00, j01 = e[0] + v * g[0], f[0] + u * g[0]
        j10, j11 = e[1] + v * g[1], f[1] + u * g[1]
        det = j00 * j11 - j01 * j10
        u -= (fx * j11 - fy * j01) / det
        v -= (fy * j00 - fx * j10) / det
    w, h = np.linalg.norm(e), np.linalg.norm(f)
    edge = np.minimum(np.minimum(u, 1 - u) * w, np.minimum(v, 1 - v) * h)
    cover = np.clip(edge + 0.8, 0, 1)

    face = np.asarray(Image.open(os.path.join(ROOT, "public", "photos", "face.jpg")).convert("RGB"), dtype=np.float64) / 255
    fh, fw = face.shape[:2]
    face = face[round(fh * 0.13) : round(fh * 0.88), round(fw * 0.2) : round(fw * 0.8)]
    side = (round(h), round(w))
    face = np.dstack([np.asarray(Image.fromarray((face[..., c] * 255).astype(np.uint8)).resize(side[::-1], Image.Resampling.LANCZOS), dtype=np.float64) / 255 for c in range(3)])
    # The reference's print is soft, a little flat and a touch warm.
    face = blurred(face, 0.6 * UP)
    grey = face.mean(axis=-1, keepdims=True)
    face = (grey + (face - grey) * 0.92) * 0.88 + 0.05
    face *= np.array([1.02, 1.0, 0.965])
    iy = np.clip((v * side[0]).astype(int), 0, side[0] - 1)
    ix = np.clip((u * side[1]).astype(int), 0, side[1] - 1)
    return card * (1 - cover[..., None]) + face[iy, ix] * cover[..., None]


def words(card, X, Y):
    """Rub the old words out to bare card and print the new ones there."""
    rubbed = np.zeros(X.shape)
    for x0, y0, x1, y1 in REWRITTEN:
        rubbed = np.maximum(rubbed, inside(X, Y, x0 * UP, y0 * UP, x1 * UP, y1 * UP, 2.0))
    card = card * (1 - rubbed[..., None]) + paper(card, X, Y) * rubbed[..., None]

    cx0, cy0, cx1, cy1 = (v * UP for v in CARD)
    plate = Image.open(os.path.join(HERE, "assets", "overlay.png")).convert("L").resize((cx1 - cx0, cy1 - cy0), Image.Resampling.LANCZOS)
    ink = np.zeros(X.shape)
    ink[cy0:cy1, cx0:cx1] = 1 - np.asarray(plate, dtype=np.float64) / 255
    # The photograph's own type has spread and softened. So does this, or it would sit on top of the picture.
    ink = np.clip(blurred(ink, 0.6 * UP) * 1.08, 0, 1) * (rubbed > 0.5)
    by_hand = Y > HAND_FROM * UP
    # A marker runs a little dry in places.
    rng = np.random.default_rng(5)
    dry = np.clip(0.93 - 0.22 * blurred(rng.standard_normal(X.shape), 2.5 * UP) * 2.5 * UP, 0.66, 1.0)
    colour = np.where(by_hand[..., None], MARKER_INK, PRINT_INK)
    strength = np.where(by_hand, ink * dry, ink)
    return card * (1 - strength[..., None]) + colour * strength[..., None]


def main():
    ref = np.asarray(Image.open(os.path.join(HERE, "assets", "reference.jpg")).convert("RGB"), dtype=np.float64) / 255
    rows, cols = ref.shape[0] * UP, ref.shape[1] * UP
    Y, X = np.mgrid[0:rows, 0:cols] + 0.5
    card = np.clip(enlarged(ref, Image.Resampling.LANCZOS), 0, 1)
    card = portrait(words(card, X, Y), X, Y)

    white, amount = veil(ref)
    amount = np.clip(enlarged(amount), 0, 1)
    white = np.clip(enlarged(white * veil(ref)[1]) / np.maximum(amount, 1e-4), 0, 1)

    # The card, and a few pixels of the vinyl round it, stay solid: they are the photograph as it is.
    x0, y0, x1, y1 = CARD
    solid = inside(X, Y, (x0 - 5) * UP, (y0 - 5) * UP, (x1 + 5) * UP, (y1 + 5) * UP, 3.0)
    alpha = solid + (1 - solid) * amount
    colour = (card * solid[..., None] + white[..., None] * ((1 - solid) * amount)[..., None]) / np.maximum(alpha, 1e-4)[..., None]

    out = np.dstack((np.clip(colour, 0, 1), np.clip(alpha, 0, 1)))
    target = os.path.join(ROOT, "public", "objects", "badge.avif")
    Image.fromarray((out * 255 + 0.5).astype(np.uint8), mode="RGBA").save(target, quality=95, subsampling="4:4:4", speed=2)
    print(f"badge {cols}x{rows} {os.path.getsize(target) / 1e3:.0f} kB")


main()
