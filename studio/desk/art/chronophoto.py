# /// script
# dependencies = ["numpy", "pillow", "scipy"]
# ///
"""The Seiko 7A28 quartz chronograph's dial, taken from the user's photograph of it face on (art/chrono-photo.jpg) and
laid out square, 12 o'clock up: what objects/chrono.py lays over its dial from above. The photograph sees the dial
all but square on, so the black ring round its tachymeter scale is all but a circle in it: found along that ring, it
is drawn out to a circle of RING_R. SEIKO, the scales and the subdials are the photograph's own; the name of the
account that posted it, written across the dial under QUARTZ, is taken out and the dial filled in under it.

The hands are taken off the dial too, for objects/chrono.py stands real ones over it, which throw their shadows on it
and catch the light: measured off the photograph (HANDS), each is filled in across its width from the dial either
side of it, the ticks of the small dial at 6 under the minute hand from its own ticks further round, and the two
letters the hands hid (the second O of CHRONOGRAPH and the 0 of 60) from their twins. Then the photograph's own light
is taken out of the dial, its white brought to the white of the paint and its black to the black of the print, and
its print, softened by the photograph, sharpened a little.

Run from the repository root:

    uv run studio/desk/art/chronophoto.py

It writes studio/desk/art/chrono-dial.png: SIZE millimetres across, PX pixels to the millimetre, the middle of the
dial in the middle; and beside it chrono-hands.json, the hands as measured, which objects/chrono.py builds."""

import json

import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO = os.path.join(HERE, "chrono-photo.jpg")
OUT = os.path.join(HERE, "chrono-dial.png")
HANDS_OUT = os.path.join(HERE, "chrono-hands.json")
SIZE = 36.0
PX = 40
# The black ring round the tachymeter scale in the photograph: the ellipse's middle, in pixels, and its matrix: a
# point p is on it where (p - CENTRE) . RING . (p - CENTRE) = 1. The photograph shows this many of its pixels to the
# mm (the case 38.6 mm across), which puts the ring this far out.
CENTRE = [390.651, 569.547]
RING = [[1.90239e-05, -1.84e-09], [-1.84e-09, 1.91337e-05]]
SCALE = 13.4
RING_R = 229.0 / SCALE
# The account's name: within this box of the photograph (left, top, right, bottom), what is darker than the dial
# round it by this much, and this many pixels round that. The seconds hand runs down through it, upright, its middle
# at this column and this many pixels either side: there the hand is drawn again from just below the name.
NAME = (300, 490, 484, 515)
DARKER = 14.0
HALO = 2
HAND = (390, 4)
# The hands, in mm on the dial, 12 o'clock up, their angles clockwise from 12: the three on the middle (pivot), the
# hour hand and the minute hand each this long and this wide, the chronograph's seconds hand this long, its tail this
# long behind the pivot, this wide, its pip this far out, this long and this wide; the cap over them this round (the
# broad hands narrow from the first width at the pivot to the second at their tip). The three small dials' hands:
# each its pivot and angle, the hands this long and this wide, their hubs this round.
HANDS = {
    "pivot": [-0.1, 0.1],
    "hour": {"angle": 135.6, "length": 8.0, "width": [0.85, 0.75]},
    "minute": {"angle": 170.5, "length": 11.6, "width": [1.15, 0.7]},
    "chrono": {"angle": 0.6, "length": 13.8, "tail": 4.7, "width": 0.2, "counterweight": 0.75, "pip": [7.6, 0.8, 0.45]},
    "cap": 1.15,
    "small": {"at": [[-7.78, -0.03, 0.0], [7.5, -0.08, 0.0], [-0.12, -7.62, 7.8]], "length": 4.3, "width": 0.32, "hub": 0.6, "shadow": 0.85},
}
# Round each broad hand, this much more taken off with it: its edge and its shadow in the photograph; round the thin
# ones (the seconds hand and the small dials' hands), this much. Where the seconds hand crosses the I of SEIKO,
# between these rows, it lies within the letter's stroke and is left.
MARGIN = 0.4
NEEDLE = 0.13
SEIKO_I = (362, 393)
# Beyond this far out along the small dials' hands, where they lay between the two ticks at 12, the dial is left
# white. The ticks of the small dial at 6, between these distances from its middle, are filled from this far round it.
CLEAR = 3.75
TICKS = (3.3, 4.8, 36.0)
# Under each hand the dial is smoothed in from round about, the photograph's grain, this strong, laid back over it;
# under the thin hands, which cross print, filled across their width from either side instead.
GRAIN = 2.5
# The letters the hands hid, each from its twin: a box of the dial (left, top, right, bottom, in its pixels) laid this
# far across and down over it. The O of CHRONOGRAPH from the O before it; the 30 of the small dial at 9 and the 0 of
# the one at 3 from the 30 of the one at 6; and the 0 of its 60, from the same, as high as the 6 beside it (found
# between these rows, in these columns).
LETTERS = ((626, 400, 665, 442, 76, 0), (680, 1112, 752, 1164, -300, -519), (714, 1112, 754, 1164, 286, -519))
ZERO = ((714, 1110, 754, 1166), (688, 712, 880, 965))
# The dial's white and the print's black, in the picture's values: the photograph's light taken out, its white comes
# to this, and its black down to this; and its print sharpened over this many pixels, this much.
WHITE = (226.0, 229.0, 231.0)
BLACK = (34.0, 22.0)
SHARPEN = (2.0, 0.7)


def unsigned(photo):
    """The photograph with the account's name taken out of it."""
    grey = photo.mean(-1)
    x0, y0, x1, y1 = NAME
    box = (slice(y0, y1), slice(x0, x1))
    around = ndimage.median_filter(grey, size=25)
    mask = np.zeros(grey.shape, bool)
    mask[box] = around[box] - grey[box] > DARKER
    mask = ndimage.binary_dilation(mask, iterations=HALO)
    middle, half = HAND
    rows = slice(y0 - 2, y1 + 2)
    columns = slice(middle - half, middle + half + 1)
    mask[rows, columns] = True
    # The dial under the name and the hand: its own colour from round about, smoothed in from the edges of the hole.
    out = photo.copy()
    keep = (~mask).astype(np.float32)
    for k in range(3):
        weight = ndimage.gaussian_filter(keep, 3.0)
        fill = ndimage.gaussian_filter(photo[..., k] * keep, 3.0) / np.maximum(weight, 1e-6)
        out[..., k] = np.where(mask, fill, photo[..., k])
    # The hand where the name crossed it: its own columns from just below the name.
    out[rows, columns] = photo[y1 + 2 : y1 + 14, columns].mean(0)[None]
    # The grain of the photograph, back over the smoothed patch.
    rng = np.random.default_rng(5)
    out += mask[..., None] * rng.normal(0, 2.0, out.shape[:2])[..., None]
    return out


def pixels(point):
    """A point on the dial in mm (12 o'clock up) as a pixel of the laid-out dial (x across, y down)."""
    return np.array([point[0] * PX + SIZE * PX / 2 - 0.5, -point[1] * PX + SIZE * PX / 2 - 0.5])


def bars():
    """Each hand as a bar in pixels: its pivot, its direction down its length (x across, y down), how far back and
    forward it runs, its half width, and how much round it to take off with it."""
    made = []
    pivot = pixels(HANDS["pivot"])
    margin = MARGIN * PX
    for name in ("hour", "minute", "chrono"):
        hand = HANDS[name]
        a = np.radians(hand["angle"])
        along = np.array([np.sin(a), -np.cos(a)])
        if name == "chrono":
            made.append((pivot, along, 0.0, hand["length"] * PX, hand["width"] / 2 * PX, NEEDLE * PX))
            made.append((pivot, along, hand["tail"] * PX, 0.0, hand["counterweight"] / 2 * PX, NEEDLE * PX))
        else:
            made.append((pivot, along, 0.0, hand["length"] * PX, np.array(hand["width"]) / 2 * PX, margin))
    small = HANDS["small"]
    for x, y, angle in small["at"]:
        a = np.radians(angle)
        made.append((pixels((x, y)), np.array([np.sin(a), -np.cos(a)]), 0.8 * PX, small["length"] * PX, small["width"] / 2 * PX, NEEDLE * PX))
    return made


def smoothed(image, hidden):
    """What is hidden, filled in from the bare dial round about it (not its print): smoothed over ever wider rounds
    until each pixel has enough of the dial near it to be drawn from."""
    out = image.copy()
    left = hidden.copy()
    grey = image.mean(-1)
    bare = grey > ndimage.median_filter(grey, 41) - 25
    keep = (~hidden & bare).astype(np.float32)
    for sigma in (4, 8, 16, 32, 64):
        weight = ndimage.gaussian_filter(keep, sigma)
        ready = left & (weight > 0.08)
        for k in range(3):
            fill = ndimage.gaussian_filter(image[..., k] * keep, sigma) / np.maximum(weight, 1e-6)
            out[..., k] = np.where(ready, fill, out[..., k])
        left &= ~ready
    return out


def handless(dial):
    """The dial with its hands taken off, filled in as the module's docstring says."""
    n = dial.shape[0]
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    masks = []
    for pivot, along, back, forward, half, margin in bars():
        dx, dy = xx - pivot[0], yy - pivot[1]
        t = dx * along[0] + dy * along[1]
        w = np.abs(-dx * along[1] + dy * along[0])
        if np.ndim(half):
            half = half[0] + (half[1] - half[0]) * np.clip(t / forward, 0, 1)
        masks.append((t > -back - margin) & (t < forward + margin) & (w < half + margin))
    # The seconds hand is left where it lies within the I of SEIKO.
    pivot = pixels(HANDS["pivot"])
    r0, r1 = SEIKO_I
    masks[2][r0:r1] = False
    # The chronograph hand's pip, the cap and the small hands' hubs, round.
    margin = MARGIN * PX
    chrono = HANDS["chrono"]
    out_, long_, wide_ = chrono["pip"]
    a = np.radians(chrono["angle"])
    pip = pivot + out_ * PX * np.array([np.sin(a), -np.cos(a)])
    discs = [(pip, max(long_, wide_) / 2 * PX + NEEDLE * PX), (pivot, HANDS["cap"] * PX + margin)]
    discs += [(pixels((x, y)), HANDS["small"]["shadow"] * PX) for x, y, _ in HANDS["small"]["at"]]
    round_ = np.zeros((n, n), bool)
    for centre, radius in discs:
        round_ |= np.hypot(xx - centre[0], yy - centre[1]) < radius
    i_columns = slice(int(pivot[0]) - 12, int(pivot[0]) + 16)
    round_[r0:r1, i_columns] = False
    hidden = round_ | np.any(masks, axis=0)
    out = smoothed(dial, hidden)
    rng = np.random.default_rng(7)
    out += hidden[..., None] * rng.normal(0, GRAIN, (n, n))[..., None]
    # Under the thin hands: filled across their width from the dial either side.
    thin = [k for k, bar in enumerate(bars()) if bar[5] == NEEDLE * PX]
    for k in thin:
        pivot, along, _, forward = bars()[k][:4]
        across = np.array([-along[1], along[0]])
        ys, xs = np.nonzero(masks[k] & ~round_)
        sides = []
        for sign in (1, -1):
            found = np.full(len(xs), np.nan, np.float32)
            for step in range(1, 40):
                qx = np.clip(np.round(xs + sign * step * across[0]).astype(int), 0, n - 1)
                qy = np.clip(np.round(ys + sign * step * across[1]).astype(int), 0, n - 1)
                found[np.isnan(found) & ~hidden[qy, qx]] = step
            sides.append(found)
        ok = ~np.isnan(sides[0]) & ~np.isnan(sides[1])
        ys, xs, a_, b_ = ys[ok], xs[ok], sides[0][ok], sides[1][ok]
        qa = [np.clip(np.round(c + a_ * d).astype(int), 0, n - 1) for c, d in ((xs, across[0]), (ys, across[1]))]
        qb = [np.clip(np.round(c - b_ * d).astype(int), 0, n - 1) for c, d in ((xs, across[0]), (ys, across[1]))]
        mix = (b_ / (a_ + b_))[:, None]
        filled = dial[qa[1], qa[0]] * mix + dial[qb[1], qb[0]] * (1 - mix)
        # A small hand at 12 lay between the two ticks there: between them the dial is white.
        if k > 3:
            far = ((xs - pivot[0]) * along[0] + (ys - pivot[1]) * along[1]) > CLEAR * PX
            filled[far] = out[ys[far], xs[far]]
        out[ys, xs] = filled
    # The ticks of the small dial at 6 under the minute hand, from its own ticks further round.
    x, y, _ = HANDS["small"]["at"][2]
    hub = pixels((x, y))
    inner, outer, turn = TICKS
    r = np.hypot(xx - hub[0], yy - hub[1]) / PX
    ys, xs = np.nonzero(masks[1] & (r > inner) & (r < outer))
    for sign in (-1, 1):
        t = np.radians(sign * turn)
        sx = hub[0] + (xs - hub[0]) * np.cos(t) - (ys - hub[1]) * np.sin(t)
        sy = hub[1] + (xs - hub[0]) * np.sin(t) + (ys - hub[1]) * np.cos(t)
        clear = ~hidden[np.round(sy).astype(int), np.round(sx).astype(int)]
        for k in range(3):
            out[ys[clear], xs[clear], k] = ndimage.map_coordinates(dial[..., k], [sy[clear], sx[clear]], order=1)
        ys, xs = ys[~clear], xs[~clear]
    # What was filled in, brought to the brightness of the bare dial just round it.
    grey = out.mean(-1)
    bare = grey > ndimage.median_filter(grey, 41) - 25
    ring = ndimage.binary_dilation(hidden, iterations=6) & ~hidden & bare
    inside = hidden & bare
    for k in range(3):
        near = ndimage.gaussian_filter(out[..., k] * ring, 12) / np.maximum(ndimage.gaussian_filter(ring.astype(np.float32), 12), 1e-6)
        own = ndimage.gaussian_filter(out[..., k] * inside, 12) / np.maximum(ndimage.gaussian_filter(inside.astype(np.float32), 12), 1e-6)
        out[..., k] = np.where(inside, out[..., k] + (near - own), out[..., k])
    # The letters, from their twins, laid in over what is there, their edges feathered.
    def laid(x0, y0, x1, y1, dx, dy):
        h, w = y1 - y0, x1 - x0
        edge = np.minimum.outer(np.minimum(np.arange(h), np.arange(h)[::-1]), np.minimum(np.arange(w), np.arange(w)[::-1]))
        weight = np.clip(edge / 4.0, 0, 1)[..., None]
        target = out[y0 + dy : y1 + dy, x0 + dx : x1 + dx]
        target[:] = target * (1 - weight) + clean[y0:y1, x0:x1] * weight

    clean = out.copy()
    for box in LETTERS:
        laid(*box)
    (x0, y0, x1, y1), (c0, c1, r0, r1) = ZERO
    grey = out.mean(-1)
    rows = np.nonzero((grey[r0:r1, c0:c1] < grey[r0:r1, c0:c1].max() - 60).any(1))[0]
    six = r0 + (rows.min() + rows.max()) / 2
    zero = np.nonzero((grey[y0:y1, x0:x1] < grey[y0:y1, x0:x1].max() - 60).any(1))[0]
    shift = int(round(six - (y0 + (zero.min() + zero.max()) / 2)))
    laid(x0, y0, x1, y1, 0, shift)
    return out


def developed(dial):
    """The photograph's light taken out of the dial: its broad light, read off the white of the dial and of the scale
    round it, divided out; its white brought to WHITE and its black to BLACK; its print sharpened."""
    grey = dial.mean(-1)
    n = dial.shape[0]
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx - n / 2, yy - n / 2) / PX
    white = (grey > ndimage.median_filter(grey, 25) - 8) & (r < RING_R - 0.4)
    keep = white.astype(np.float32)
    weight = ndimage.gaussian_filter(keep, 60.0)
    light = np.stack([ndimage.gaussian_filter(dial[..., k] * keep, 60.0) / np.maximum(weight, 1e-6) for k in range(3)], -1)
    out = dial / np.maximum(light, 1.0) * np.array(WHITE)
    # The print's black, darker: values below the white pulled down so the photograph's grey black comes to BLACK.
    seen, black = BLACK
    level = np.array(WHITE)
    out = np.where(out < level, level - (level - out) * (level - black) / (level - seen) / (level.mean() - black) * (level.mean() - black), out)
    radius, amount = SHARPEN
    soft = np.stack([ndimage.gaussian_filter(out[..., k], radius) for k in range(3)], -1)
    out = out + amount * (out - soft)
    # Outside the dial, past the black ring, the photograph is left as it was: the model has its own steel there.
    inside = (r < RING_R + 0.15)[..., None]
    return np.where(inside, out, dial)


def main():
    photo = unsigned(np.asarray(Image.open(PHOTO).convert("RGB")).astype(np.float32))
    weights, axes = np.linalg.eigh(np.array(RING))
    if np.linalg.det(axes) < 0:
        axes[:, 0] *= -1
    semi = 1 / np.sqrt(weights)
    n = round(SIZE * PX)
    steps = (np.arange(n) + 0.5) / PX - SIZE / 2
    x, y = np.meshgrid(steps, -steps)
    # The dial in mm, 12 o'clock up, onto the unit circle and out to the ellipse.
    u = np.stack((x / RING_R, -y / RING_R), -1)
    at = np.array(CENTRE) + (u @ axes) * semi @ axes.T
    out = np.dstack([ndimage.map_coordinates(photo[..., k], [at[..., 1], at[..., 0]], order=3, mode="nearest") for k in range(3)])
    out = developed(handless(out))
    with open(HANDS_OUT, "w") as file:
        json.dump(HANDS, file, indent=2)
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(OUT)
    print(OUT, out.shape)


main()
