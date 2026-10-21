# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""The letter's deckle edge, as a mask for the page to cut its sheet with, for paper.py's handmade paper.

    uv run studio/paper/edge.py [--proof FILE]

A sheet couched on a mould is never cut. Where the pulp ran up against the mould's deckle it stopped on a line
that wanders, and past the line it did not stop all at once: the pulp thins to a bare few fibres, so the last
millimetre of the sheet is translucent, and what lies beyond that is single cotton fibres, some floating loose off
the edge and some lying along it. This draws that edge as a mask, solid to the left, clear to the right, repeating
down the strip without a seam:

- the line wanders slowly and a little faster, and never runs straight for more than a few centimetres;
- the pulp thins toward the line: the mask is a soft, uneven falloff, not a step, and its last few pixels let
  the page behind show through;
- fibres: long ones standing off the edge, curling, and short ones lying along it.

The letter's tab is the same sheet, its deckle running on round it: the edge follows the strip's edge down to the
tab, out round the tab's outline (SiteShell's tabOutline) and back, and the pulp's line, its haze and its fibres
lie across the edge wherever it turns, measured square to it. The tab lies in a different place for each layout and
stands out a different way, so there is a mask for each, as wide as the strip's edge and the tab together.

Writes public/objects/likes-edge-<layout>.png, edge_width(layout) by EDGE_LENGTH CSS px at EDGE_DENSITY pixels to
the CSS px, the strip's edge CUT px from its left: its right lies past the tab's outline as far as DECKLE_PAST lies
past a strip's edge (SiteShell), 9 CSS px, so the line runs 2.5 past the edge, round the tab too.
"""

import argparse
import math
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EDGE_LENGTH = 1600
EDGE_DENSITY = 6  # pixels of the mask to the CSS px: fine enough for its fibres, a third of a px across, zoomed in
OVER = 2  # drawn at twice that, then averaged down, for its edges
LINE = 2.5  # where the line runs on average, in CSS px past the edge
CUT = 7  # the strip's edge, in CSS px from the mask's left (16 - SiteShell's DECKLE_PAST)
PAST = 9  # how far the mask runs past the tab's outline (SiteShell's DECKLE_PAST)
# The letter strip's tab (SiteShell's slot 2): its top and height in rem (tabTops, tabHeights over tabSpan), and each
# layout's band and how far the tab stands out (useStackMetrics).
TAB_TOP, TAB_TALL, TAB_SPAN = 4, 10, 4
LAYOUTS = {"wide": (1.9, 2.1), "phone": (1.4, 1.5)}
REM = 16


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof", help="also write the mask over a dark page, enlarged, to this file")
    args = parser.parse_args()
    for layout in LAYOUTS:
        deckle(layout, args.proof and args.proof.replace(".png", f"-{layout}.png"))


def deckle(layout, proof):
    density = EDGE_DENSITY * OVER
    width = edge_width(layout)
    cols, rows = width * density, EDGE_LENGTH * density
    X = (np.arange(cols)[None, :] + 0.5) / density
    Y = (np.arange(rows)[:, None] + 0.5) / density
    rng = np.random.default_rng(29)

    def wander(sigma, shape):
        """Noise that wraps down the strip, sigma CSS px across, scaled to unit deviation."""
        field = ndimage.gaussian_filter(rng.standard_normal(shape), sigma * density, mode=("wrap", "reflect"))
        return field / field.std()

    # The edge: where the sheet would end if the pulp stopped on a line, and how far in from it each pixel is,
    # square to it, wherever it turns (negative past it).
    path = outline(layout)
    path[:, 0] += CUT
    inside = X < np.interp(Y[:, 0], path[:, 1], path[:, 0])[:, None]
    square = (ndimage.distance_transform_edt(inside) - ndimage.distance_transform_edt(~inside)) / density

    # The line: where the pulp stopped, wandering past the edge as it goes down it.
    slow, quick = wander(30, (rows, 1))[:, 0], wander(6, (rows, 1))[:, 0]
    # It wanders as far as the mask has room for, so the page's body always meets solid paper.
    line = LINE + 2.5 * np.tanh((1.5 * slow + 0.9 * quick) / 2.5)

    # How far in the sheet is from its line, roughened at the scale of the fibres in it.
    inward = square + line[:, None] + 3.0 * np.tanh((2.0 * wander(2.2, (rows, cols)) + 1.0 * wander(0.6, (rows, cols))) / 3.0)
    # Pulp thins toward the line: full a few pixels in, a haze at the line itself, nothing a little past it.
    edge = np.clip(inward / 6.5 + 0.45, 0, 1)
    edge = edge * edge * (3 - 2 * edge)
    thin = 0.7 + 0.3 * np.clip(inward / 3.5, 0, 1)
    mask = edge * thin
    # A sheet that is thicker in places is thinner in others: the haze comes and goes down the edge.
    # It does so only toward the line: well inside, the sheet is whole.
    mask = mask * (1 - 0.14 * np.clip(wander(12, (rows, cols)) * 0.5 + 0.5, 0, 1) * (1 - np.clip(inward / 5.0, 0, 1)))

    def fibre(y0, x0, reach, heading, curl, width_, strength):
        """One fibre from (x0, y0), reach long, heading from straight out, curling, wrapping down the strip."""
        steps = max(8, int(reach * density * 2))
        t = np.linspace(0, 1, steps)
        angle = heading + curl * t
        px = x0 + np.cumsum(np.cos(angle)) * reach / steps
        py = y0 + np.cumsum(np.sin(angle)) * reach / steps
        taper = 1 - 0.55 * t
        for qx, qy, w in zip(px, py, taper):
            if qx > width - 0.15:
                break
            for dy in (-EDGE_LENGTH, 0, EDGE_LENGTH):
                r0, r1 = max(int((qy + dy - 1.5) * density), 0), min(int((qy + dy + 1.5) * density) + 1, rows)
                if r1 <= r0:
                    continue
                d = np.hypot(X - qx, Y[r0:r1] - qy - dy)
                cover = strength * w * np.clip(0.5 + (width_ * w - d) * density, 0, 1)
                mask[r0:r1] = np.maximum(mask[r0:r1], cover)

    # Where along the edge a fibre starts, as many to a px of it round the tab as down the strip: the point, the way
    # straight out from the edge there, and the line's distance past it.
    run = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(path, axis=0).T))])

    def along(s):
        x, y = np.interp(s, run, path[:, 0]), np.interp(s, run, path[:, 1])
        k = min(np.searchsorted(run, s, side="right"), len(run) - 1)
        dx, dy = path[k] - path[k - 1]
        return x, y, math.atan2(-dx, dy), float(np.interp(y % EDGE_LENGTH, Y[:, 0], line))

    # Long fibres standing off the edge, now and then, curling.
    for _ in range(round(run[-1] / 14)):
        x, y, out, past = along(rng.uniform(0, run[-1]))
        back = past - rng.uniform(0.5, 2.0)
        fibre(y + back * math.sin(out), x + back * math.cos(out), rng.uniform(2.5, 7.0), out + rng.normal(0, 0.55), rng.normal(0, 0.9), rng.uniform(0.22, 0.4), rng.uniform(0.45, 0.85))
    # Short ones lying along the edge, caught in it.
    for _ in range(round(run[-1] / 9)):
        x, y, out, past = along(rng.uniform(0, run[-1]))
        back = past + rng.uniform(-1.5, 0.8)
        fibre(y + back * math.sin(out), x + back * math.cos(out), rng.uniform(2.0, 5.0), out + rng.choice((-1, 1)) * rng.uniform(1.0, 1.45), rng.normal(0, 0.5), rng.uniform(0.2, 0.34), rng.uniform(0.3, 0.6))

    # Nothing runs off the mask's right side: the last pixels of it fade out, so no fibre is cut off square.
    mask = mask * np.clip((width - X) / 1.6, 0, 1)
    mask = mask.reshape(EDGE_LENGTH * EDGE_DENSITY, OVER, width * EDGE_DENSITY, OVER).mean(axis=(1, 3))

    pixels = np.empty(mask.shape + (4,), np.uint8)
    pixels[..., :3] = 255
    pixels[..., 3] = np.clip(mask * 255 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(pixels).save(os.path.join(ROOT, "public", "objects", f"likes-edge-{layout}.png"), optimize=True)
    print(f"EDGE {layout} {width}x{EDGE_LENGTH} CSS px")

    if proof:
        dark = np.zeros(mask.shape + (3,), np.float32) + np.array([0.12, 0.11, 0.1])
        paper = np.array([0.93, 0.91, 0.88])
        shown = dark * (1 - mask[..., None]) + paper * mask[..., None]
        strip = (shown[:900] * 255).astype(np.uint8)
        Image.fromarray(strip).resize((strip.shape[1] * 4, strip.shape[0] * 4), Image.NEAREST).save(proof)


if __name__ == "__main__":
    main()
