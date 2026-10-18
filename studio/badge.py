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
- The portrait is replaced inside the print's own outline, which sits a little askew in its printed box. It is
  a passport photograph: a white border of photo paper round the picture, and the paper a little bigger than
  the print it replaces. It is an old one, faded and warm, scratched (from a scan of real scratches), creased
  across a corner, its edge frayed and nicked, a corner torn away and a split torn into one side.
- The words in REWRITTEN are rubbed out to bare card and put back in the reference's own letters, lifted
  and set in a new order. That goes for the type, the dot-matrix stamp and the handwriting. A letter the
  reference never used is made from ones it did: a G from a C, a 5 from an E and a 3, stamp figures from
  the stamp's own grid of dots, and a few capitals drawn with the marker's width of pen.
- The title alone is not the reference's. It is set in Instrument Serif and printed as old letterpress is
  (see letterpress).
- The mark beside the line under the title, and the three rules, come from studio/assets/overlay.png,
  a capture of studio/plate.html.

Writes public/objects/badge.avif at twice the reference's size. studio/badge_model.py is the earlier
Blender model of the same badge; the page does not use it.
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UP = 2  # output pixels to one of the reference's

# All in the reference's pixels.
HOLDER = (105, 15, 620, 882, 22)
RING = (345, 0, 442, 18)  # the part of the ring that stands clear of the holder
CARD = (162, 195, 577, 850)
EDGE = (163.5, 191.5, 579, 848.5)  # the card's own cut edge, measured where its shadow starts
# The corners of the portrait print, clockwise from the top left. It was stuck down by hand.
PRINT = ((274.2, 372.0), (456.8, 373.4), (458.4, 600.2), (271.4, 601.0))
BLANK = (478, 385, 566, 595)  # bare card, to take paper grain from
REWRITTEN = (
    (188, 203, 440, 264),  # the title, a line at a time, so the drop number beside it is left alone
    (188, 258.5, 558, 322),
    (188, 321, 558, 333),  # the rule under it
    (452, 236, 556, 258),  # the drop number, and where it moves to
    (186, 331, 560, 362),  # the line under the title
    (320.5, 804.2, 380, 815.5),  # the end of the small print
    (434, 788, 474, 832),  # the stamp, either side of its dash
    (486, 788, 547, 832),
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
PHOTO_PAPER = np.array([0.95, 0.94, 0.915])
GROW = 3.0  # how far the photo paper runs past the old print's outline, in the reference's pixels
BORDER = 7.5  # the white border of the passport photograph, from the paper's edge to the picture
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
    # The vinyl lies flat on the page for a little way round the card. The page there is only a touch brighter
    # than the fit, and the photograph's grain would make that a ragged white film, so there it only darkens.
    x0, y0, x1, y1 = EDGE
    round_card = inside(X + 0.5, Y + 0.5, x0 - 26, y0 - 26, x1 + 26, y1 + 26, 4.0)
    amount = amount * (1 - white * round_card)
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
    """Lay an old passport photograph over the old print, its paper a little bigger than the print was."""
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
    # The photo paper's own frame, in output pixels from its top left: it is the old print grown by GROW all round.
    grow = GROW * UP
    lx, ly = u * w + grow, v * h + grow
    pw, ph = w + 2 * grow, h + 2 * grow
    shape = (math.ceil(ph) + 1, math.ceil(pw) + 1)
    rng = np.random.default_rng(21)

    def field(sigma):
        """Smooth noise of unit deviation in the paper's frame, sigma in output pixels, read at every pixel."""
        n = blurred(rng.standard_normal(shape), sigma)
        return ndimage.map_coordinates(n / n.std(), [ly, lx], order=1, mode="nearest")

    def scan(name, scale, at, turn=0.0):
        """An ambientCG scan laid over the paper, `scale` of its pixels to one of the paper's, from `at`, the scan
        turned by `turn` degrees first."""
        path = os.path.join(HERE, "desk", "assets", name, f"{name}_1K-JPG_Opacity.jpg")
        img = Image.open(path).convert("L").rotate(turn, resample=Image.Resampling.BICUBIC)
        box = (at[0], at[1], at[0] + round(shape[1] * scale), at[1] + round(shape[0] * scale))
        n = np.asarray(img.crop(box).resize(shape[::-1], Image.Resampling.BOX), dtype=np.float64) / 255
        return ndimage.map_coordinates(n, [ly, lx], order=1, mode="nearest")

    # The paper's edge: cut straight once, now frayed and nicked, one corner torn away and one side split.
    sheet = np.minimum(np.minimum(lx, pw - lx), np.minimum(ly, ph - ly))
    sheet = sheet + 0.3 * UP * field(0.5 * UP) + 0.35 * UP * field(4 * UP)
    torn = np.full(lx.shape, np.inf)
    for side, at, r in ((0, 0.3, 1.6), (1, 0.7, 1.1), (2, 0.55, 2.0), (3, 0.2, 1.3), (1, 0.15, 0.9), (2, 0.85, 1.2)):
        cx, cy = ((at * pw, 0), (pw, at * ph), (at * pw, ph), (0, at * ph))[side]
        torn = np.minimum(torn, np.hypot(lx - cx, ly - cy) - r * UP)
    # The bottom left corner, torn off across.
    c1, c2 = 24 * UP, 15 * UP
    across = (lx * c1 - (ly - (ph - c1)) * c2) / math.hypot(c1, c2)
    torn = np.minimum(torn, across + 0.9 * UP * field(0.8 * UP) + 1.2 * UP * field(4 * UP))
    # A split in from the right edge, a third of the way down, closing as it goes in.
    sx, sy, ex, ey = pw, 0.36 * ph, pw - 15 * UP, 0.36 * ph + 4 * UP
    t = np.clip(((lx - sx) * (ex - sx) + (ly - sy) * (ey - sy)) / ((ex - sx) ** 2 + (ey - sy) ** 2), 0, 1)
    split = np.hypot(lx - sx - t * (ex - sx), ly - sy - t * (ey - sy)) - 1.4 * UP * (1 - t) ** 1.5 - 0.15 * UP
    torn = np.minimum(torn, split + 0.25 * UP * field(0.6 * UP))
    sheet = np.minimum(sheet, torn)
    cover = np.clip(sheet + 0.8, 0, 1)
    # Where the paper tore away, the card shows: bare, with nothing of the old print left on it.
    old = np.minimum(np.minimum(lx, pw - lx), np.minimum(ly, ph - ly)) - grow
    under = np.clip(old + 2 * UP, 0, 1)
    card = card * (1 - under[..., None]) + paper(card, X, Y) * under[..., None]
    # Its shadow on the card, deeper where a torn edge has lifted off it.
    lifted = 1 + 1.5 * np.exp(-np.maximum(torn, 0) / (3 * UP)) * (torn < sheet + 1.0)
    card = card * (1 - 0.1 * lifted * np.exp(np.minimum(sheet, 0) / (1.8 * UP)) * (sheet < 0))[..., None]

    # The picture, inside the white border.
    border = BORDER * UP
    picture = np.clip(np.minimum(np.minimum(lx, pw - lx), np.minimum(ly, ph - ly)) - border + 0.8, 0, 1)
    face = np.asarray(Image.open(os.path.join(HERE, "assets", "face.png")).convert("RGB"), dtype=np.float64) / 255
    fh, fw = face.shape[:2]
    face = face[round(fh * 0.13) : round(fh * 0.88), round(fw * 0.2) : round(fw * 0.8)]
    side = (round(ph - 2 * border), round(pw - 2 * border))
    face = np.dstack([np.asarray(Image.fromarray((face[..., c] * 255).astype(np.uint8)).resize(side[::-1], Image.Resampling.LANCZOS), dtype=np.float64) / 255 for c in range(3)])
    face = blurred(face, 0.3 * UP)
    # An old print: its contrast and colour faded, its blacks lifted, and the whole gone a little warm.
    grey = face.mean(axis=-1, keepdims=True)
    face = (grey + (face - grey) * 0.8) * 0.84 + 0.07
    face *= np.array([1.04, 1.0, 0.93])
    iy = np.clip((ly - border).astype(int), 0, side[0] - 1)
    ix = np.clip((lx - border).astype(int), 0, side[1] - 1)
    # Where the paper tore, the picture came away with it a little way back from the tear, to the white core.
    core = np.clip((1.8 * UP - torn - 0.3 * UP * field(1.2 * UP)) / (0.5 * UP), 0, 1)
    picture = picture * (1 - core)
    photo = PHOTO_PAPER * (1 - picture[..., None]) + face[iy, ix] * picture[..., None]
    photo = photo * (1 - core[..., None] * 0.5) + np.array([0.975, 0.97, 0.96]) * core[..., None] * 0.5

    # A crease across the top right corner: a fold's light and shade, and the picture cracked along it.
    fx0, fy0, fx1, fy1 = 0.62 * pw, 0.0, pw, 0.3 * ph
    fold = ((lx - fx0) * (fy1 - fy0) - (ly - fy0) * (fx1 - fx0)) / math.hypot(fx1 - fx0, fy1 - fy0)
    fold = fold + 1.2 * UP * field(10 * UP)
    photo = photo * (1 - 0.1 * np.tanh(fold / (1.2 * UP)) * np.exp(-np.abs(fold) / (3 * UP)))[..., None]
    crack = np.clip(1 - np.abs(fold) / (0.4 * UP), 0, 1) * np.clip(field(1.0 * UP) + 0.3, 0, 1)
    photo = photo * (1 - (crack * picture * 0.5)[..., None]) + PHOTO_PAPER * (crack * picture * 0.5)[..., None]
    photo = photo * (1 - 0.12 * crack * (1 - picture))[..., None]

    # Scratches, from a scan of real ones, and grime worked into the paper along its edges.
    # The scan's long scratches all run one way, so it is turned to lay them on a slant, and its faintest web is
    # left out: what is left is the few that went through the emulsion.
    scratch = np.clip(scan("Scratches003", 1.3, (330, 300), turn=28) * 1.6, 0, 1) ** 2.0
    photo = photo * (1 - (scratch * picture * 0.45)[..., None]) + PHOTO_PAPER * (scratch * picture * 0.45)[..., None]
    photo = photo * (1 - 0.2 * scratch * (1 - picture))[..., None]
    grime = scan("SurfaceImperfections003", 1.2, (300, 200))
    near = np.exp(-np.maximum(sheet, 0) / (3 * UP)) * np.clip(grime * 2.2, 0, 1)
    photo = photo * (1 - near[..., None] * np.array([0.16, 0.2, 0.3]))
    return card * (1 - cover[..., None]) + photo * cover[..., None]


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


# The title is not the reference's: it is set in Geist Mono and printed as old letterpress is.
# Its last line stands as far above the rule as the reference's title did at nine tenths of its size,
# and its capitals are 15% shorter than that title's were, then a tenth taller again.
# Instrument Serif is kept beside it: TITLE_FACE "InstrumentSerif-Regular.ttf", TITLE_WEIGHT None,
# TITLE_BOLD 0.8 and TITLE_TRACK -1.9 set the title in that.
HEADLINE = ("THE", "PERFORMER")
TITLE_FACE = os.path.join(HERE, "assets", "fonts", "GeistMono[wght].ttf")
TITLE_WEIGHT = 800  # where the face has a weight axis; None where it has one weight
TITLE_AT = (193.0, 311.0)  # the left edge, and the baseline of the last line
TITLE_CAP = 48.0 * 0.9 * 0.85 * 1.1  # the height of a capital
TITLE_BOLD = 0.0  # a face with one weight has every stroke thickened by this much on each side
TITLE_TRACK = -3.0  # the letters are set this much closer, so they run into each other as the reference's do
TITLE_LEAD = 1.16  # baseline to baseline, in capitals
TITLE_BOX = (186, 200, 560, 322)  # the part of the card it is printed in
RULE_UP = 2.0
DROP_RIGHT = 38.5  # the drop number is moved along to end where the rule does
TYPE = (200.6, 10.22, 335.5, 353.5)  # the line under the title: middle of its first letter, pitch, top, bottom
TITLE = "PRODUCT-FIRST ENGINEER"
# Where each of its letters comes from. A number and two edges is a letter of the reference's own line,
# SKIN-FIRST FOUNDATION: which one, counting from nought, and where it begins and ends. Its letters are
# wider than their pitch and run into each other, so each is cut where it is clear of its neighbours.
FROM_LINE = {
    "R": (7, 266.2, 277.9),
    "O": (19, 387.4, 399.7),
    "D": (15, 349.6, 359.9),
    "U": (13, 328.4, 338.9),
    "T": (9, 287.7, 299.6),
    "N": (3, 225.0, 237.8),
    "I": (6, 258.8, 265.2),
    "-": (4, 238.2, 245.0),
    "F": (5, 246.2, 257.0),
    "S": (8, 277.9, 287.7),
}
# The rest come from the narrower type the card's labels are set in. It is the same face, and the line
# under the title is that face drawn out to about half as wide again: so are these.
FROM_LABELS = {"P": (480.0, 239, 488.6, 254), "C": (205.0, 688, 212.6, 702.4), "E": (222.6, 633, 229.7, 646)}
STAMP = (794.0, 5.33, 3.15)  # the stamp's dots: top row, and the pitch down and across
# The left column of each figure the reference stamped, 45-12H, and of the six places a figure goes.
STRUCK = {"5": 457.6, "2": 509.4, "H": 528.4}
PLACES = (438.5, 457.6, None, 489.7, 509.4, 528.4)
# 02-03X, each figure as bands of the reference's own figures, top to bottom: which figure, the rows the
# band runs between, and the row it is laid at. Rows count from nought and a band may start part way
# through one. A 3 is the top of the 2 on the bottom of the 5. A 0 is the same with the H's uprights
# between, taken clear of its bar. An X is the ends of the H's uprights with five single dots crossing.
STAMPED = {
    0: (("2", 0, 2, 0), ("H", 1.83, 2.83, 2), ("H", 1.83, 2.83, 3), ("H", 4.17, 5.17, 4), ("5", 5, 7, 5)),
    1: (("2", 0, 7, 0),),
    3: (("2", 0, 2, 0), ("H", 1.83, 2.83, 2), ("H", 1.83, 2.83, 3), ("H", 4.17, 5.17, 4), ("5", 5, 7, 5)),
    4: (("2", 0, 4, 0), ("5", 4, 7, 4)),
    5: (("H", 0, 2.26, 0), ("H", 4.74, 7, 4.74)),
}
CROSS = ((1, 2), (3, 2), (2, 3), (1, 4), (3, 4))  # the X's single dots: column and row
DOT = (513.0, 815.3)  # a dot of the reference's stamp that stands alone


def letterpress():
    """The title as ink, 0 for bare card to 1 for black, over TITLE_BOX at the output's size.

    Old metal type on soft card does four things a screen does not. The ink spreads, so the letters are a
    little fatter than the face and their edges are rough where it crept into the grain. It is squeezed
    out from under the type, so it lies thicker round the edge of a letter than in the middle. It does not
    take evenly, so a stem is paler in patches and the card's tooth and fibres leak through it, while a
    little of the ink leaks out into the card round each letter. And the sorts are worn and never sit dead
    level, so each letter stands a hair off its line."""
    fine = 4  # drawn this many times the output's size, so the roughness is in the ink and not the pixels
    px = UP * fine
    x0, y0, x1, y1 = TITLE_BOX
    cols, rows = (x1 - x0) * px, (y1 - y0) * px
    rng = np.random.default_rng(23)

    def cut(size):
        font = ImageFont.truetype(TITLE_FACE, size)
        if TITLE_WEIGHT:
            font.set_variation_by_axes([TITLE_WEIGHT])
        return font

    top, bottom = cut(400).getbbox("H")[1], cut(400).getbbox("H")[3]
    bold = round(TITLE_BOLD * px)
    face = cut(round(400 * (TITLE_CAP * px - 2 * bold) / (bottom - top)))
    sheet = Image.new("L", (cols, rows), 0)
    draw = ImageDraw.Draw(sheet)
    left, last = TITLE_AT
    for i, line in enumerate(HEADLINE):
        base = last - (len(HEADLINE) - 1 - i) * TITLE_CAP * TITLE_LEAD
        x = (left - x0) * px - face.getbbox(line[0])[0] + bold
        for j, letter in enumerate(line):
            dx, dy = rng.normal(0, 0.1 * px), rng.normal(0, 0.22 * px)
            at = (x + dx, (base - y0) * px - bold + dy)
            draw.text(at, letter, font=face, fill=255, anchor="ls", stroke_width=bold, stroke_fill=255)
            pair = line[j : j + 2]
            if len(pair) == 2:
                x += face.getlength(pair) - face.getlength(pair[1:]) + 2 * bold + TITLE_TRACK * px
    type_ = np.asarray(sheet, dtype=np.float64) / 255

    def noise(sigma):
        field = blurred(rng.standard_normal((rows, cols)), sigma * px)
        return field / field.std()

    # Spread, with a ragged edge: the line between ink and card wanders with the grain.
    soft = blurred(type_, 0.42 * px)
    edge = 0.4 + 0.085 * noise(0.33) + 0.035 * noise(1.3)
    inked = np.clip((soft - edge) / 0.05 + 0.5, 0, 1)
    # Squash: thicker at the rim than in the body of a stroke.
    body = np.clip((blurred(inked, 1.0 * px) - 0.62) / 0.3, 0, 1)
    weight = 1.0 - 0.07 * body
    # Uneven take: slow patches, and pinholes where a fleck of card stayed dry.
    weight *= np.clip(0.97 + 0.05 * noise(4.0), 0.84, 1.0)
    weight *= 1 - 0.22 * np.clip((noise(1.6) - 1.3) / 0.6, 0, 1)
    holes = np.clip((noise(0.22) - 2.05) / 0.3, 0, 1) * body
    inked = inked * weight * (1 - 0.85 * holes)
    # The card leaks through. Its tooth shows as flecks where the type did not press ink down into it, and
    # its fibres as short pale streaks along the sheet. Both come thick where the type is worn and thin
    # where it is not, so the wear lies across the words in patches.
    def grain(across, down):
        fy = np.fft.fftfreq(rows)[:, None]
        fx = np.fft.rfftfreq(cols)[None, :]
        kernel = np.exp(-2 * np.pi**2 * ((across * px * fx) ** 2 + (down * px * fy) ** 2))
        field = np.fft.irfft2(np.fft.rfft2(rng.standard_normal((rows, cols))) * kernel, s=(rows, cols))
        return field / field.std()

    worn = np.clip(0.5 + 0.55 * noise(7.0), 0, 1)
    tooth = np.clip((grain(0.17, 0.17) - (1.95 - 1.05 * worn)) / 0.3, 0, 1)
    fibres = np.clip((grain(1.5, 0.2) - (2.35 - 1.0 * worn)) / 0.3, 0, 1)
    inked *= 1 - np.maximum(0.8 * tooth, 0.9 * fibres)
    # And the ink leaks out: a faint stain round each letter, running a little way along the fibres.
    stain = np.clip(blurred(type_, 1.0 * px) * 2.4, 0, 1) * np.clip(0.45 + 0.5 * grain(1.1, 0.3), 0, 1)
    inked = np.maximum(inked, 0.2 * stain)
    # Flecks of ink the type threw clear of itself.
    near = np.clip(blurred(type_, 2.2 * px) * 3, 0, 1) * (1 - np.clip(soft * 4, 0, 1))
    inked = np.maximum(inked, 0.55 * near * np.clip((noise(0.2) - 2.6) / 0.25, 0, 1))

    small = inked.reshape(rows // fine, fine, cols // fine, fine).mean(axis=(1, 3))
    return np.clip(blurred(small, 0.3 * UP), 0, 1)


def printed(ref, shape):
    """The reference's printed letters in their new places, as ink at the output's size."""
    lum = ref.mean(axis=-1)
    ink = np.clip((0.94 - lum) / (0.94 - PRINT_INK.mean()), 0, 1)
    out = np.zeros(shape)

    def take(x0, y0, x1, y1, w=None, h=None):
        """The ink in a box of the reference, resampled to w by h reference pixels."""
        w, h = w or x1 - x0, h or y1 - y0
        rows, cols = round(h * UP), round(w * UP)
        ys = y0 + (np.arange(rows) + 0.5) / rows * (y1 - y0) - 0.5
        xs = x0 + (np.arange(cols) + 0.5) / cols * (x1 - x0) - 0.5
        return np.clip(ndimage.map_coordinates(ink, np.meshgrid(ys, xs, indexing="ij"), order=3, mode="nearest"), 0, 1)

    def tight(x0, y0, x1, y1):
        """The box drawn in to the ink inside it."""
        found = ink[round(y0) : round(y1), round(x0) : round(x1)] > 0.3
        ys, xs = np.nonzero(found)
        return round(x0) + xs.min() - 0.7, round(y0) + ys.min() - 0.7, round(x0) + xs.max() + 1.7, round(y0) + ys.max() + 1.7

    def put(mark, x, y):
        top, left = round(y * UP), round(x * UP)
        h, w = mark.shape
        out[top : top + h, left : left + w] = np.maximum(out[top : top + h, left : left + w], mark)

    # The title, in its own face, and the reference's rule under it.
    put(letterpress(), TITLE_BOX[0], TITLE_BOX[1])
    put(take(190, 323.5, 556, 328.6), 190, 323.5 - RULE_UP)

    # The line under the title.
    first, pitch, top, bottom = TYPE
    for i, letter in enumerate(TITLE):
        middle = first + i * pitch
        if letter == " ":
            continue
        if letter in FROM_LINE:
            source, x0, x1 = FROM_LINE[letter]
            put(take(x0, top, x1, bottom), middle - (first + source * pitch - x0), top)
            continue
        box = tight(*FROM_LABELS["C" if letter == "G" else letter])
        wide = {"P": 10.4, "C": 10.6, "E": 9.8, "G": 10.8}[letter] + 1.4
        mark = np.clip(take(*box, wide, 16.4) * 1.3, 0, 1) ** 0.85
        if letter == "G":  # a C with a bar and a spur
            h, w = mark.shape
            bar = np.zeros_like(mark)
            bar[round(0.5 * h) : round(0.5 * h) + round(2.0 * UP), round(0.52 * w) : w - round(1.5 * UP)] = 0.85
            bar[round(0.5 * h) : round(0.76 * h), w - round(4.0 * UP) : w - round(1.5 * UP)] = 0.85
            mark = np.maximum(mark, blurred(bar, 0.45 * UP))
        put(mark, middle - wide / 2 + (0.5 if letter in "PE" else 0.0), 336.3)

    # The drop number's 5: the top of an E on the bottom of the 3 it replaces.
    three = tight(505.0, 239, 513.4, 255)
    w, h = three[2] - three[0], three[3] - three[1]
    lower, upper = take(*three), take(*tight(*FROM_LABELS["E"]), w, h)
    rows = np.arange(lower.shape[0])[:, None] / lower.shape[0]
    put(np.maximum(upper * (rows < 0.55), lower * (rows > 0.45)), three[0] + DROP_RIGHT, three[1])
    put(take(454, 237, 504.6, 257), 454 + DROP_RIGHT, 237)

    # The small print ends FOR ME. Both letters are in PERFORMER, side by side.
    put(take(276.3, 804.2, 289.2, 815), 322.6, 804.2)

    # The stamp, from the reference's own dots.
    top, down, across = STAMP

    def edge(row):
        """Where one row of dots ends and the next begins."""
        return 790.5 if row <= 0 else 830.0 if row >= 7 else top + (row - 0.5) * down

    for place, bands in STAMPED.items():
        for figure, start, end, at in bands:
            x0 = STRUCK[figure] - 2.4
            put(take(x0, edge(start), x0 + 4 * across + 4.8, edge(end)), PLACES[place] - 2.4, edge(at))
    cx, cy = DOT
    dot = take(cx - 3.2, cy - 3.2, cx + 3.2, cy + 3.2)
    span = (np.arange(dot.shape[0]) + 0.5) / UP - 3.2
    dot = dot * np.clip((3.0 - np.hypot(span[None, :], span[:, None])) / 0.6, 0, 1)
    for column, row in CROSS:
        put(dot, PLACES[5] + column * across - 3.2, top + row * down - 3.2)
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
    ink = np.maximum(ink, printed(ref, X.shape) * (rubbed > 0.5))
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

    # The card stays solid, out to its own edge: it is the photograph as it is. Past it is only vinyl, and its
    # shadow on the page under the vinyl comes through as the vinyl's darkening.
    x0, y0, x1, y1 = EDGE
    solid = inside(X, Y, x0 * UP, y0 * UP, x1 * UP, y1 * UP, 1.5)
    alpha = solid + (1 - solid) * amount
    colour = (card * solid[..., None] + white[..., None] * ((1 - solid) * amount)[..., None]) / np.maximum(alpha, 1e-4)[..., None]

    out = np.dstack((np.clip(colour, 0, 1), np.clip(alpha, 0, 1)))
    target = os.path.join(ROOT, "public", "objects", "badge.avif")
    Image.fromarray((out * 255 + 0.5).astype(np.uint8), mode="RGBA").save(target, quality=95, subsampling="4:4:4", speed=2)
    print(f"badge {cols}x{rows} {os.path.getsize(target) / 1e3:.0f} kB")


main()
