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

Where the letter's tab grows out, its outline is cut into the sheet with scissors, so the deckle settles there onto
the strip's edge, as SiteShell's tears run straight there: the line eases onto it over SETTLE, its haze closes to a
clean cut and no fibre stands past it. Otherwise the tab's straight cut would stand out from a deckle that wanders
inside it, a step at its top with the deckle's grey haze hanging beside it. The tab lies in a different place for
each layout, so there is a mask for each.

Writes public/objects/likes-edge-<layout>.png, EDGE_WIDTH by EDGE_LENGTH CSS px at EDGE_DENSITY pixels to the CSS
px: the page's TEAR_WIDTH and TEAR_LENGTH (SiteShell), and DECKLE_PAST there is how far it lies past the strip's
edge, 9 CSS px, so the line runs 2.5 past it.
"""

import argparse
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EDGE_WIDTH, EDGE_LENGTH = 16, 1600
EDGE_DENSITY = 3  # pixels of the mask to the CSS px
OVER = 2  # drawn at twice that, then averaged down, for its edges
LINE = 6.5  # where the line runs, in CSS px from the mask's right, so a little past the strip's edge
CUT = EDGE_WIDTH - 9  # the strip's edge, in CSS px from the mask's left (SiteShell's DECKLE_PAST)
SETTLE = 36  # how far the deckle takes to settle onto the edge, in CSS px, as SiteShell's tear does
# The letter strip's tab (SiteShell's slot 2): its top and height in rem (tabTops, tabHeights over tabSpan), and each
# layout's band and how far the tab stands out (useStackMetrics), for its outline's reach.
TAB_TOP, TAB_TALL, TAB_SPAN = 4, 10, 4
LAYOUTS = {"wide": (1.9, 2.1), "phone": (1.4, 1.5)}
REM = 16


def calm_of(layout):
    """Where the tab's outline is cut, in CSS px down the strip, joins and all."""
    band, protrude = LAYOUTS[layout]
    top = TAB_TOP * REM
    height = TAB_TALL * (band + protrude) / TAB_SPAN * REM
    reach = 2 * 0.2 * protrude * REM
    return top - reach, top + height + reach


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof", help="also write the mask over a dark page, enlarged, to this file")
    args = parser.parse_args()
    for layout in LAYOUTS:
        deckle(layout, args.proof and args.proof.replace(".png", f"-{layout}.png"))


def deckle(layout, proof):
    density = EDGE_DENSITY * OVER
    cols, rows = EDGE_WIDTH * density, EDGE_LENGTH * density
    X = (np.arange(cols)[None, :] + 0.5) / density
    Y = (np.arange(rows)[:, None] + 0.5) / density
    rng = np.random.default_rng(29)

    def wander(sigma, shape):
        """Noise that wraps down the strip, sigma CSS px across, scaled to unit deviation."""
        field = ndimage.gaussian_filter(rng.standard_normal(shape), sigma * density, mode=("wrap", "reflect"))
        return field / field.std()

    # How much of the deckle is left at each row: none where the tab is cut, all of it SETTLE past that.
    start, end = calm_of(layout)
    away = np.clip(np.maximum(start - Y, Y - end) / SETTLE, 0, 1)
    settled = away * away * (3 - 2 * away)

    # The line: where the pulp stopped.
    slow, quick = wander(30, (rows, 1))[:, 0], wander(6, (rows, 1))[:, 0]
    # It wanders as far as the mask has room for, so the page's body always meets solid paper.
    line = EDGE_WIDTH - LINE + 2.5 * np.tanh((1.5 * slow + 0.9 * quick) / 2.5)
    line = CUT + settled[:, 0] * (line - CUT)

    # How far in the sheet is from its line, roughened at the scale of the fibres in it.
    inward = line[:, None] - X + settled * 3.0 * np.tanh((2.0 * wander(2.2, (rows, cols)) + 1.0 * wander(0.6, (rows, cols))) / 3.0)
    # Pulp thins toward the line: full a few pixels in, a haze at the line itself, nothing a little past it. Cut, it
    # is whole right up to the cut.
    edge = np.clip(inward / (0.3 + 6.2 * settled) + 0.45 + 0.05 * (1 - settled), 0, 1)
    edge = edge * edge * (3 - 2 * edge)
    thin = 1 - 0.3 * settled * (1 - np.clip(inward / 3.5, 0, 1))
    mask = edge * thin
    # A sheet that is thicker in places is thinner in others: the haze comes and goes down the edge.
    # It does so only toward the line: well inside, the sheet is whole.
    mask = mask * (1 - 0.14 * settled * np.clip(wander(12, (rows, cols)) * 0.5 + 0.5, 0, 1) * (1 - np.clip(inward / 5.0, 0, 1)))
    # The fibres are drawn apart, as the cut takes them away with the rest past it.
    body, mask = mask, np.zeros_like(mask)

    def fibre(y0, x0, reach, heading, curl, width, strength):
        """One fibre from (x0, y0), reach long, heading from straight out, curling, wrapping down the strip."""
        steps = max(8, int(reach * density * 2))
        t = np.linspace(0, 1, steps)
        angle = heading + curl * t
        px = x0 + np.cumsum(np.cos(angle)) * reach / steps
        py = y0 + np.cumsum(np.sin(angle)) * reach / steps
        taper = 1 - 0.55 * t
        for qx, qy, w in zip(px, py, taper):
            if qx > EDGE_WIDTH - 0.15:
                break
            for dy in (-EDGE_LENGTH, 0, EDGE_LENGTH):
                r0, r1 = max(int((qy + dy - 1.5) * density), 0), min(int((qy + dy + 1.5) * density) + 1, rows)
                if r1 <= r0:
                    continue
                d = np.hypot(X - qx, Y[r0:r1] - qy - dy)
                cover = strength * w * np.clip(0.5 + (width * w - d) * density, 0, 1)
                mask[r0:r1] = np.maximum(mask[r0:r1], cover)

    def line_at(y):
        return np.interp(y % EDGE_LENGTH, Y[:, 0], line)

    # Long fibres standing off the edge, now and then, curling.
    for _ in range(round(EDGE_LENGTH / 14)):
        y0 = rng.uniform(0, EDGE_LENGTH)
        fibre(y0, line_at(y0) - rng.uniform(0.5, 2.0), rng.uniform(2.5, 7.0), rng.normal(0, 0.55), rng.normal(0, 0.9), rng.uniform(0.22, 0.4), rng.uniform(0.45, 0.85))
    # Short ones lying along the edge, caught in it.
    for _ in range(round(EDGE_LENGTH / 9)):
        y0 = rng.uniform(0, EDGE_LENGTH)
        fibre(y0, line_at(y0) + rng.uniform(-1.5, 0.8), rng.uniform(2.0, 5.0), rng.choice((-1, 1)) * rng.uniform(1.0, 1.45), rng.normal(0, 0.5), rng.uniform(0.2, 0.34), rng.uniform(0.3, 0.6))

    mask = np.maximum(body, mask * np.maximum(settled, X < CUT))
    # Nothing runs off the mask's right side: the last pixels of it fade out, so no fibre is cut off square.
    mask = mask * np.clip((EDGE_WIDTH - X) / 1.6, 0, 1)
    mask = mask.reshape(EDGE_LENGTH * EDGE_DENSITY, OVER, EDGE_WIDTH * EDGE_DENSITY, OVER).mean(axis=(1, 3))

    pixels = np.empty(mask.shape + (4,), np.uint8)
    pixels[..., :3] = 255
    pixels[..., 3] = np.clip(mask * 255 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(pixels).save(os.path.join(ROOT, "public", "objects", f"likes-edge-{layout}.png"), optimize=True)
    print(f"EDGE {layout} {mask.shape[1]}x{mask.shape[0]}, cut from {start:.1f} to {end:.1f} px")

    if proof:
        dark = np.zeros(mask.shape + (3,), np.float32) + np.array([0.12, 0.11, 0.1])
        paper = np.array([0.93, 0.91, 0.88])
        shown = dark * (1 - mask[..., None]) + paper * mask[..., None]
        strip = (shown[:900] * 255).astype(np.uint8)
        Image.fromarray(strip).resize((strip.shape[1] * 6, strip.shape[0] * 6), Image.NEAREST).save(proof)


if __name__ == "__main__":
    main()
