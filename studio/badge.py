# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""The ID badge: the reference photograph itself, with the portrait and some of the words changed.

    uv run studio/badge.py

Everything that is not changed is the reference's own pixels, so the holder, the ring, the light on the
vinyl and the card are the photograph's and not a likeness of them. Three things are done to it:

- The page behind the holder is taken out. Where only vinyl lies over the page, the image keeps how much
  the vinyl darkens or lightens it and nothing else, so the vinyl is see-through on whatever page it is
  laid on, and on a white one it reads as the photograph does.
- The portrait is replaced inside the print's own outline, which sits a little askew in its printed box.
- The words in REWRITTEN are rubbed out to bare card. The printed ones are set again from
  studio/assets/overlay.png, a capture of studio/plate.html. The handwritten ones are written again in
  the reference's own hand: its letters are lifted and put in a new order, and the few it never wrote
  are drawn with the same pen.

Writes public/objects/badge.avif at twice the reference's size. studio/badge_model.py is the earlier
Blender model of the same badge; the page does not use it.
"""

import os

import numpy as np
from PIL import Image
from scipy import ndimage

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
    (240, 603, 565, 668),  # and what is written on them
    (282, 662, 565, 724),
    (242, 718, 565, 781),
)
# Letters of the reference's handwriting, by the box each sits in.
LETTERS = {
    "a": (493, 622, 515, 653),
    "a2": (458, 736, 480, 768),
    "i": (348, 619, 356, 650),
    "e": (361, 618, 380, 645),
    "e2": (393, 683, 418, 712),
    "u": (386, 738, 408, 769),
    "r": (430, 739, 447, 769),
}
PEN = 4.4  # width of the marker's line
HAND = 0.9  # size of the writing against the reference's own
# What to write: the left edge and the baseline of each line, then its letters. A letter is a lifted one
# by name, or a drawn one starting with "+". Each may be followed by a gap before it, a size and a lean.
WRITING = (
    (262, 653, (("+A",), ("n", 3), ("u", 0, 1.0, 3), ("r", 1, 1.0, -2), ("a2", 0), ("g", 0, 1.0, 2), ("+D", 15), ("a", 3, 1.04, -3), ("+s", 2))),
    (308, 712, (("+E",), ("n", 3, 1.03, -2), ("g", 0), ("i", 2), ("n", 2, 0.97, 3), ("e", 1), ("e2", 0), ("r", -1, 1.05, 3))),
    (256, 769, (("+T",), ("+3", 6), ("+W", 16), ("a", 3, 1.0, 2), ("r", 1, 0.97, -3), ("+m", 2))),
)
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
    # Grain only: a fleck in the patch would come round again in every tile.
    grain = np.clip(patch - blurred(patch, 5), -0.012, 0.012)
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

    face = np.asarray(Image.open(os.path.join(HERE, "assets", "face.png")).convert("RGB"), dtype=np.float64) / 255
    fh, fw = face.shape[:2]
    face = face[round(fh * 0.13) : round(fh * 0.88), round(fw * 0.2) : round(fw * 0.8)]
    side = (round(h), round(w))
    face = np.dstack([np.asarray(Image.fromarray((face[..., c] * 255).astype(np.uint8)).resize(side[::-1], Image.Resampling.LANCZOS), dtype=np.float64) / 255 for c in range(3)])
    # The reference's print is a little flat and a touch warm. It is also soft, but this one is left nearly
    # as sharp as the output can hold: it is the one thing on the card that is not the reference's.
    face = blurred(face, 0.3 * UP)
    grey = face.mean(axis=-1, keepdims=True)
    face = (grey + (face - grey) * 0.92) * 0.88 + 0.05
    face *= np.array([1.02, 1.0, 0.965])
    iy = np.clip((v * side[0]).astype(int), 0, side[0] - 1)
    ix = np.clip((u * side[1]).astype(int), 0, side[1] - 1)
    return card * (1 - cover[..., None]) + face[iy, ix] * cover[..., None]


def pen(shape, strokes):
    """Marker lines through the given points, in output pixels. The pen rests a moment where a line ends."""
    out = np.zeros(shape)
    half = PEN * HAND * UP / 2
    for points in strokes:
        pts = np.array(points, dtype=np.float64)
        # No hand puts a point where it meant to. The same line always strays the same way.
        stray = np.random.default_rng(int(abs(pts).sum() * 7) % 2**32)
        pts[1:-1] += stray.normal(0, 0.55 * UP, pts[1:-1].shape)
        for _ in range(3):  # round the corners off, as a hand does
            q, r = 0.75 * pts[:-1] + 0.25 * pts[1:], 0.25 * pts[:-1] + 0.75 * pts[1:]
            pts = np.concatenate(([pts[0]], np.column_stack((q, r)).reshape(-1, 2), [pts[-1]]))
        x0, y0 = np.floor(pts.min(axis=0) - half - 3).astype(int)
        x1, y1 = np.ceil(pts.max(axis=0) + half + 3).astype(int)
        Y, X = np.mgrid[y0:y1, x0:x1] + 0.5
        d = np.full(X.shape, 1e9)
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            t = np.clip(((X - ax) * (bx - ax) + (Y - ay) * (by - ay)) / max((bx - ax) ** 2 + (by - ay) ** 2, 1e-9), 0, 1)
            d = np.minimum(d, np.hypot(X - ax - t * (bx - ax), Y - ay - t * (by - ay)))
        for ex, ey in (pts[0], pts[-1]):
            d = np.minimum(d, np.hypot(X - ex, Y - ey) - 0.2 * half)
        out[y0:y1, x0:x1] = np.maximum(out[y0:y1, x0:x1], np.clip((half - d) / 1.6 + 0.5, 0, 1) * 0.9)
    return out


DRAWN = {
    # Letters the reference never wrote, or wrote in a way that will not read in these words, in its plain
    # upright print. Points are in a box of the given width and height, standing on the baseline.
    "+A": (29, 44, [[(3, 44), (9, 22), (14, 1)], [(14, 1), (20, 21), (27, 44)], [(7, 30), (15, 28), (23, 28)]]),
    "+D": (26, 43, [[(5, 2), (4, 22), (5, 43)], [(2, 3), (13, 2), (22, 10), (24, 23), (20, 35), (12, 42), (3, 42)]]),
    "+E": (23, 42, [[(4, 1), (3, 21), (4, 41)], [(3, 2), (12, 2), (21, 3)], [(4, 21), (11, 20), (17, 21)], [(4, 41), (13, 40), (22, 40)]]),
    "+T": (27, 39, [[(1, 4), (13, 2), (26, 2)], [(14, 2), (13, 20), (13, 39)]]),
    "+3": (20, 39, [[(2, 6), (9, 1), (16, 5), (15, 13), (8, 18), (16, 23), (18, 31), (11, 38), (2, 34)]]),
    "+W": (38, 40, [[(2, 3), (6, 20), (11, 39)], [(11, 39), (15, 26), (19, 14)], [(19, 14), (23, 27), (27, 39)], [(27, 39), (32, 20), (36, 2)]]),
    "+s": (18, 31, [[(16, 6), (10, 2), (4, 6), (5, 12), (11, 16), (15, 22), (12, 28), (6, 30), (1, 26)]]),
    "+m": (36, 30, [[(3, 3), (3, 16), (4, 29)], [(4, 12), (9, 4), (15, 6), (17, 16), (17, 29)], [(17, 12), (23, 4), (29, 6), (31, 16), (32, 29)]]),
}


def handwriting(ref, shape):
    """The lines in WRITING as ink, 0 for bare card to 1 for the marker's black, at the output's size."""
    lum = ref.mean(axis=-1)
    ink = np.clip((0.92 - lum) / (0.92 - 0.24), 0, 1)
    marks, _ = ndimage.label(lum < 118 / 255, structure=np.ones((3, 3)))

    def lifted(name):
        x0, y0, x1, y1 = LETTERS[name]
        found = marks[y0:y1, x0:x1]
        own = ndimage.binary_dilation(marks == np.bincount(found[found > 0]).argmax(), iterations=2)
        ys, xs = np.nonzero(own)
        cut = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
        return ink[cut] * own[cut]

    def letter(name):
        if name == "n":  # an n is a u turned over
            return lifted("u")[::-1, ::-1]
        return lifted(name)

    out = np.zeros(shape)

    def lay(mark, x, base, size=1.0, lean=0.0, drop=0.0):
        """Put a letter down with its left edge at x and its foot on the baseline, in reference pixels."""
        mark = ndimage.zoom(mark, UP * size, order=3)
        if lean:
            mark = ndimage.rotate(mark, lean, reshape=True, order=3)
        mark = np.clip(mark, 0, 1)
        h, w = mark.shape
        top, left = round((base + drop) * UP) - h, round(x * UP)
        out[top : top + h, left : left + w] = np.maximum(out[top : top + h, left : left + w], mark)
        return w / UP, h / UP

    for x, base, line in WRITING:
        for name, gap, size, lean in ((*item, *(0, 1.0, 0.0)[len(item) - 1 :]) for item in line):
            x += gap * HAND
            size *= HAND
            if name.startswith("+"):
                w, h, strokes = DRAWN[name]
                out[:] = np.maximum(out, pen(shape, [[((x + px * HAND) * UP, (base + (py - h) * HAND) * UP) for px, py in stroke] for stroke in strokes]))
                x += w * HAND
            elif name == "g":  # an a, with the tail the reference gives its J
                w, _ = lay(letter("a2"), x, base, size, lean)
                tail = ((0, -8), (0.5, 4), (-1, 10), (-6, 13), (-12, 11))
                out[:] = np.maximum(out, pen(shape, [[((x + w + (dx - 4.5) * HAND) * UP, (base + dy * HAND) * UP) for dx, dy in tail]]))
                x += w
            elif name == "i":
                w, h = lay(letter("i"), x, base, size, lean)
                dot = ((0.3, -6.5), (1.3, -5.5))
                out[:] = np.maximum(out, pen(shape, [[((x + w / 2 + dx * HAND) * UP, (base - h + dy * HAND) * UP) for dx, dy in dot]]))
                x += w
            else:
                x += lay(letter(name), x, base, size, lean)[0]
    return out


def words(card, X, Y, ref):
    """Rub the old words out to bare card and put the new ones there."""
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
    card = card * (1 - ink[..., None]) + PRINT_INK * ink[..., None]

    # A marker runs a little dry in places.
    rng = np.random.default_rng(5)
    dry = np.clip(0.97 - 0.2 * blurred(rng.standard_normal(X.shape), 2.5 * UP) * 2.5 * UP, 0.7, 1.0)
    written = np.clip(blurred(handwriting(ref, X.shape), 0.35 * UP) * dry, 0, 1)
    return card * (1 - written[..., None]) + MARKER_INK * written[..., None]


def main():
    ref = np.asarray(Image.open(os.path.join(HERE, "assets", "reference.jpg")).convert("RGB"), dtype=np.float64) / 255
    rows, cols = ref.shape[0] * UP, ref.shape[1] * UP
    Y, X = np.mgrid[0:rows, 0:cols] + 0.5
    card = np.clip(enlarged(ref, Image.Resampling.LANCZOS), 0, 1)
    card = portrait(words(card, X, Y, ref), X, Y)

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
