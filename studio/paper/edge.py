# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy", "openexr>=3.3"]
# ///
"""The letter's deckle edge, rendered: the mask the page cuts its handmade sheet with, and the shadow the sheet
leaves on the strip after it, in place of a drop shadow.

    uv run studio/paper/edge.py [--samples 256] [--layout wide|phone] [--proof DIR]

A sheet couched on a mould is never cut. Where the pulp ran up against the mould's deckle it stopped on a line that
wanders, and past the line it did not stop all at once: a sheet is nothing but cotton fibres matted together, and
toward the line there are fewer and fewer of them, so the last millimetre is a translucent lace of fibres, and past
it single fibres lie loose, some along the edge where the water drained and some straight out of it. This lays
that pulp fibre by fibre at the paper's own scale (studio/paper/paper.py: SHEET mm to its tile, shown at half its
pixels, MM CSS px to the mm), and deckle.py renders it in Blender:

- the line wanders slowly and a little faster, and never runs straight for more than a few centimetres, nor
  smooth for more than a millimetre, where the pulp lay in lumps;
- fibres are as many to the square px well inside as make the sheet solid, thinning out to the line and past it,
  more where the pulp flocked and fewer between, each one FIBRE mm long and FIBRE_WIDTH mm across (cotton rag,
  beaten), lying flat, curling a little, letting most light through;
- the body of the sheet is a surface where the pulp lies solid, the paper's thickness, its edge cockled up off the
  page in slow swells as a handmade sheet dries.

The letter's tab is the same sheet, its deckle running on round it: the edge follows the strip's edge down to the
tab, out round the tab's outline (SiteShell's tabOutline) and back, and the pulp thins square to it wherever it
turns. The tab lies in a different place for each layout and stands out a different way, so there is a mask and a
shadow for each.

Writes public/objects/likes-edge-<layout>.webp, edge_width(layout) by EDGE_LENGTH CSS px at EDGE_DENSITY pixels to the
CSS px, the strip's edge CUT px from its left: its right lies past the tab's outline as far as DECKLE_PAST lies past
a strip's edge (SiteShell), 9 CSS px. And likes-cast-<layout>.webp, from the same left CAST_PAST px further, at
CAST_DENSITY: black, as dark as the sheet makes the page under and beside it, for SiteShell to lay under the sheet.
"""

import argparse
import json
import math
import os
import subprocess
import tempfile

import numpy as np
import OpenEXR
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "public", "objects")
EDGE_LENGTH = 1600
EDGE_DENSITY = 6  # pixels of the mask to the CSS px: fine enough for a lace of fibres, zoomed in
CAST_DENSITY = 4  # and of the shadow, which is soft
CAST_PAST = 8  # how much further right the shadow runs than the mask, in CSS px
LINE = 2.0  # where the line runs on average, in CSS px past the edge
WANDER = 1.5  # and how far either side of that it wanders
CUT = 7  # the strip's edge, in CSS px from the mask's left (16 - SiteShell's DECKLE_PAST)
PAST = 9  # how far the mask runs past the tab's outline (SiteShell's DECKLE_PAST)
# The letter strip's tab (SiteShell's slot 2): its top and height in rem (tabTops, tabHeights over tabSpan), and each
# layout's band and how far the tab stands out (useStackMetrics).
TAB_TOP, TAB_TALL, TAB_SPAN = 4, 10, 4
LAYOUTS = {"wide": (1.9, 2.1), "phone": (0.98, 1.05)}
REM = 16
# The paper's scale: paper.py's tile is 230 mm across in 1536 pixels, shown at 768 CSS px.
MM = 768 / 230
PULP = (0.925, 0.912, 0.880)  # paper.py's PULP, the sheet as it shows on the page
UNDER = (0x2A / 255, 0x26 / 255, 0x22 / 255)  # what it lies on: the poster's print at its edge (studio/edgecast)
THICK = 0.56  # the paper's thickness, in CSS px, as the poster's (studio/edgecast PAPER_THICK)
LIFT, CURL = 0.8, 16.0  # how far the edge cockles up off the page at most, and how far in from its line that begins
# The fibres: length and width in mm, median and lognormal spread; a single one lets THROUGH of the light past it.
FIBRE, FIBRE_WIDTH = (1.6, 0.35), (0.035, 0.3)
FINE, FINES = (0.25, 0.5), 1.5  # the fines, bits of fibre the beater broke off, and how many to each fibre
THROUGH = 0.6
SOLID = 4.0  # how far in from the line the sheet is solid, in CSS px: there the body takes over from the fibres
THIN = 0.5  # how gradually the pulp thins across the line, in CSS px
# Fibres to the square CSS px where the pulp is whole: enough that well before SOLID the sheet stops all light.
PER_PX = 20.0
FIELD_DENSITY = 4  # points to the CSS px of the fields the fibres are laid by
BACK = 24  # how far left of the mask the fields run, so the sheet is whole there
MARGIN = 16  # rows above and below one length, in CSS px


def edge_width(layout):
    """The mask's width in CSS px: in from the strip's edge, out past the tab."""
    return math.ceil(CUT + LAYOUTS[layout][1] * REM + PAST)


def outline(layout):
    """The edge down one length, in CSS px from the strip's edge and down the strip: straight down to the tab, then
    SiteShell's tabOutline round it (its joins easing out of the edge and back, its corners rounded), then straight
    on down. Points close enough to follow its curves."""
    band, protrude = (v * REM for v in LAYOUTS[layout])
    top = TAB_TOP * REM
    height = TAB_TALL * (band + protrude) / TAB_SPAN
    rise, ease = protrude * 0.33, protrude * 0.2
    reach = 2 * ease
    corners = [(0, -reach), (0, 0), (protrude, rise), (protrude, height - rise), (0, height), (0, height + reach)]

    def toward(a, b):
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        return a[0] + (b[0] - a[0]) / length * ease, a[1] + (b[1] - a[1]) / length * ease

    points = [(0.0, -top), corners[0]]
    for i in range(1, len(corners) - 1):
        before, after = toward(corners[i], corners[i - 1]), toward(corners[i], corners[i + 1])
        points.append(before)
        for t in np.linspace(0, 1, 24)[1:]:
            points.append(tuple((1 - t) ** 2 * np.array(before) + 2 * (1 - t) * t * np.array(corners[i]) + t**2 * np.array(after)))
    points += [corners[-1], (0.0, EDGE_LENGTH - top)]
    xy = np.array(points)
    xy[:, 1] += top
    return xy


def wander(rng, sigma, shape, density):
    """Noise that wraps down the strip, sigma CSS px across at density pixels to the px, scaled to unit deviation."""
    field = ndimage.gaussian_filter(rng.standard_normal(shape), sigma * density, mode=("wrap", "reflect") if len(shape) == 2 else "wrap")
    return field / field.std()


def swell(rng):
    """How far the sheet's edge lifts off the page at each px down: a few slow swells round one length, as a sheet
    couched by hand cockles as it dries."""
    y = np.arange(EDGE_LENGTH)
    rise = np.zeros(EDGE_LENGTH)
    for cycles in (3, 5, 8, 13):
        rise += rng.uniform(0.5, 1) / cycles**0.5 * np.sin(2 * np.pi * cycles * y / EDGE_LENGTH + rng.uniform(0, 2 * np.pi))
    return LIFT * ((rise - rise.min()) / (rise.max() - rise.min())) ** 2


def fibres(rng, count, cx, cy, d, normal, length, width, points):
    """count fibres of the pulp, centred at (cx, cy), each length mm long and width mm across (lognormal, median
    and spread), as polylines of points points: each heads off at random, or near the line along it, as the pulp
    drained along the deckle, and bends and wavers along its length as a twisted cotton fibre does. Returns its points, in
    CSS px, and the radius at each."""
    along = np.arctan2(normal[:, 1], normal[:, 0]) + np.pi / 2
    near = rng.random(count) < 0.9 * np.clip(1.5 - d / SOLID, 0, 1)
    heading = np.where(near, along + rng.normal(0, 0.35, count) + np.pi * rng.integers(0, 2, count), rng.uniform(0, 2 * np.pi, count))
    reach = np.clip(rng.lognormal(np.log(length[0]), length[1], count), length[0] / 3, length[0] * 1.8) * MM
    t = np.linspace(-0.5, 0.5, points)
    turn = heading[:, None] + rng.normal(0, 1.0, count)[:, None] * t + np.cumsum(rng.normal(0, 0.2, (count, points)), axis=1)
    step = (reach / (points - 1))[:, None]
    x = np.cumsum(step * np.cos(turn), axis=1)
    y = np.cumsum(step * np.sin(turn), axis=1)
    x += cx[:, None] - x[:, points // 2 : points // 2 + 1]
    y += cy[:, None] - y[:, points // 2 : points // 2 + 1]
    thick = rng.lognormal(np.log(width[0]), width[1], count) * np.where(rng.random(count) < 0.04, 2.5, 1.0)
    # A fibre thins toward its ends.
    radius = 0.5 * thick[:, None] * MM * (0.55 + 0.45 * np.sin(np.pi * (t + 0.5)) ** 0.5)
    return x, y, radius


def deckle(layout, samples, proof):
    rng = np.random.default_rng(29)
    width = edge_width(layout)
    G = FIELD_DENSITY
    # The field, in CSS px: in from the frame's left far enough for the sheet to be whole, out past the shadow's
    # frame, and a margin above and below one length, which repeats.
    x = -BACK + (np.arange((BACK + width + CAST_PAST) * G) + 0.5) / G
    y = -MARGIN + (np.arange((EDGE_LENGTH + 2 * MARGIN) * G) + 0.5) / G
    period = (np.arange(len(y)) - MARGIN * G) % (EDGE_LENGTH * G)

    # How far in from the sheet's outline each point lies, square to it wherever it turns.
    path = outline(layout)
    path[:, 0] += CUT
    inside = x[None, :] < np.interp(y % EDGE_LENGTH, path[:, 1], path[:, 0])[:, None]
    square = (ndimage.distance_transform_edt(inside) - ndimage.distance_transform_edt(~inside)) / G
    gy, gx = np.gradient(square)
    norm = np.maximum(np.hypot(gx, gy), 1e-6)

    # Where the pulp stopped: a line wandering past the outline down its length, and in from it, how deep the pulp
    # lies, its flocs pushing it out and in a little at the scale of a fibre.
    rows = EDGE_LENGTH * G
    slow, quick, lumps = wander(rng, 30, (rows,), G), wander(rng, 6, (rows,), G), wander(rng, 2.5, (rows,), G)
    line = LINE + WANDER * np.tanh((1.5 * slow + 0.9 * quick) / 2.5) + 0.5 * lumps
    floc = wander(rng, 1.2, (rows, len(x)), G)[period]
    d = square + line[period][:, None] + 0.6 * np.tanh(floc)
    # The sheet thins toward the line: as many fibres to the square px as make it solid well inside, fewer and fewer
    # out to the line and past it, and in clumps where the pulp flocked.
    clumps = np.exp(0.35 * wander(rng, 0.8, (rows, len(x)), G))[period]
    density = PER_PX / (1 + np.exp(-d / THIN)) * clumps * (d < SOLID + 1.5)
    lift = swell(rng)

    def laid(count_per_px, length, width_, points):
        own = (y >= 0) & (y < EDGE_LENGTH)
        n = rng.poisson(density[own] * count_per_px / PER_PX / G**2)
        r, c = np.nonzero(n)
        k = n[r, c]
        r, c = np.repeat(r, k), np.repeat(c, k)
        rr = r + int(np.argmax(own))
        cx = x[c] + rng.uniform(-0.5, 0.5, len(c)) / G
        cy = y[rr] + rng.uniform(-0.5, 0.5, len(c)) / G
        normal = np.stack([gx[rr, c], gy[rr, c]], -1) / norm[rr, c][:, None]
        px, py, radius = fibres(rng, len(c), cx, cy, d[rr, c], normal, length, width_, points)
        # Each lies in the pulp as deep as the pulp is there, on the page past the line, and lifts with the edge.
        deep = THICK * np.clip(d[rr, c] / SOLID, 0, 1) * rng.random(len(c))
        up = lift[np.round(cy).astype(int) % EDGE_LENGTH] * np.clip(1 - d[rr, c] / CURL, 0, 1) ** 2
        pz = np.repeat((deep + up)[:, None], points, axis=1) + radius
        # Round one length and on: those near either end again a length on, so the edge repeats without a seam.
        copies = [(px, py, pz, radius)]
        for shift, near in ((EDGE_LENGTH, cy < MARGIN + 8), (-EDGE_LENGTH, cy > EDGE_LENGTH - MARGIN - 8)):
            copies.append((px[near], py[near] + shift, pz[near], radius[near]))
        return [np.concatenate(part) for part in zip(*copies)]

    long_ = laid(PER_PX, FIBRE, FIBRE_WIDTH, 8)
    fines = laid(PER_PX * FINES, FINE, FIBRE_WIDTH, 4)
    sizes = np.concatenate([np.full(len(long_[0]), 8), np.full(len(fines[0]), 4)]).astype(np.int32)
    points = np.concatenate([np.stack([p[0], -p[1], p[2]], -1).reshape(-1, 3) for p in (long_, fines)])
    radius = np.concatenate([long_[3].ravel(), fines[3].ravel()])
    print(f"EDGE {layout}: {len(sizes)} fibres")

    # The body: the sheet's top wherever the pulp lies solid, at two to a px.
    step = G // 2
    body = np.where(d[::step, ::step] > SOLID, THICK + (lift[np.round(y[::step]).astype(int) % EDGE_LENGTH] [:, None] * np.clip(1 - d[::step, ::step] / CURL, 0, 1) ** 2), np.nan)

    with tempfile.TemporaryDirectory() as work:
        np.savez(os.path.join(work, "fibres.npz"), sizes=sizes, points=points, radius=radius, body=body, body_x=x[::step], body_y=y[::step])
        spec = {"thick": THICK, "paper": linear(PULP), "under": linear(UNDER), "through": THROUGH, "rows": (-MARGIN, EDGE_LENGTH + MARGIN)}
        spec |= {"mask_frame": (0, width), "mask_density": EDGE_DENSITY, "mask_samples": max(64, samples // 2), "cast_frame": (0, width + CAST_PAST), "cast_density": CAST_DENSITY, "samples": samples}
        json.dump(spec, open(os.path.join(work, "spec.json"), "w"))
        subprocess.run(["blender", "-b", "--factory-startup", "-P", os.path.join(HERE, "deckle.py"), "--", work], check=True, stdout=subprocess.DEVNULL)
        mask = read(os.path.join(work, "mask.exr"))[..., 3]
        luma = np.array([0.2126, 0.7152, 0.0722], np.float32)
        cast, bare = (read(os.path.join(work, f"{name}.exr"))[..., :3] @ luma for name in ("cast", "bare"))

    mask = mask[MARGIN * EDGE_DENSITY : (MARGIN + EDGE_LENGTH) * EDGE_DENSITY]
    # Nothing runs off the mask's right side: its last pixels fade out, so no fibre is cut off square.
    mask = mask * np.clip((width - (np.arange(mask.shape[1]) + 0.5) / EDGE_DENSITY) / 1.6, 0, 1)
    pixels = np.empty(mask.shape + (4,), np.uint8)
    pixels[..., :3] = 255
    pixels[..., 3] = np.clip(mask * 255 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(pixels).save(os.path.join(proof or OUT, f"likes-edge-{layout}.webp"), lossless=True, quality=100, method=6)

    ratio = (cast / np.maximum(bare, 1e-5))[MARGIN * CAST_DENSITY : (MARGIN + EDGE_LENGTH) * CAST_DENSITY]
    dark = np.clip(1 - ratio, 0, 1)
    shadow = np.zeros(dark.shape + (4,), np.uint8)
    shadow[..., 3] = (dark * 255 + 0.5).astype(np.uint8)
    Image.fromarray(shadow).save(os.path.join(proof or OUT, f"likes-cast-{layout}.webp"), lossless=True, quality=100, method=6)
    edge = round((CUT + LINE) * CAST_DENSITY)
    print(f"EDGE {layout} mask {mask.shape[::-1]}, cast {dark.shape[::-1]}, shadow past the line by px:", np.round(dark[:, edge : edge + 8 * CAST_DENSITY : CAST_DENSITY].mean(axis=0), 3))

    if proof:
        # Over the poster's dark print and over white, enlarged: the top of the length, round the tab.
        size = (dark.shape[1] * EDGE_DENSITY // CAST_DENSITY, mask.shape[0])
        shade = 1 - np.asarray(Image.fromarray(dark.astype(np.float32)).resize(size, Image.BILINEAR))[:, : mask.shape[1]]
        for name, ground in (("dark", np.array([0.12, 0.11, 0.10])), ("light", np.array([0.95, 0.95, 0.95]))):
            shown = ground * shade[..., None] * (1 - mask[..., None]) + np.array(PULP) * mask[..., None]
            part = (np.clip(shown[: 260 * EDGE_DENSITY], 0, 1) * 255).astype(np.uint8)
            Image.fromarray(part).resize((part.shape[1] * 2, part.shape[0] * 2), Image.NEAREST).save(os.path.join(proof, f"likes-edge-{layout}-{name}.png"))


def read(path):
    with OpenEXR.File(path) as exr:
        channels = exr.channels()
        rgba = channels["RGBA"].pixels if "RGBA" in channels else np.stack([channels[c].pixels for c in "RGBA"], -1)
    return np.asarray(rgba, np.float32)


def linear(srgb):
    srgb = np.asarray(srgb, np.float64)
    return np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4).tolist()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument("--layout", choices=tuple(LAYOUTS))
    parser.add_argument("--proof", help="write into this folder, not public/objects, with proofs over dark and light")
    args = parser.parse_args()
    if args.proof:
        os.makedirs(args.proof, exist_ok=True)
    for layout in LAYOUTS:
        if args.layout in (None, layout):
            deckle(layout, args.samples, args.proof)


if __name__ == "__main__":
    main()
