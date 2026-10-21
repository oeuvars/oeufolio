# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy", "openexr>=3.3"]
# ///
"""The poster's torn edge, rendered: where its print ends, the white paper the tear bares past it, and the shadow it
all leaves on the mat, in place of SiteShell's drawn tear.

    uv run studio/poster/tear.py [--samples 128] [--layout wide|phone] [--proof DIR]

Paper torn by hand does not part on one line. The printed face gives way first, on a line that wanders at every
scale, from the slow swing of the hand down to the single fibre, never in even teeth. Below it the sheet splits
through its thickness and its core holds on further, so past the print runs a rim of bare white paper, thinning as it
goes, wide where the tear ran one way and gone where it ran the other, and fibres pulled out of it lie loose past
it, most of them straight out from it, the way they were pulled. The torn strip lifts a little off the mat.

This lays that out at the scale the mat's rulers are printed at (24 CSS px to the cm, MM px to the mm): the print's
line, the rim and its fibres, each fibre as long and fine as paper's own, and tear_render.py renders it in Blender
under the copy stand's light (as studio/edgecast renders the strips' edges). The tear runs straight where the tab
grows out (SiteShell's calm span), so the tab's joins meet a straight edge, and that lies in a different place for
each layout. For each it writes, one TEAR_LENGTH long, repeating:

- public/objects/poster-edge-<layout>.png: the print's mask, TEAR_WIDTH px from the strip's edge out, at
  EDGE_DENSITY: SiteShell cuts the poster with it in place of its drawn tear;
- poster-core-<layout>.png: the bared paper and its fibres in their own colour and light, FRAME across, at DENSITY,
  for SiteShell to lay under the print;
- poster-cast-<layout>.png: the shadow on the mat, as studio/edgecast writes it, which SiteShell lays as before.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import OpenEXR
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "public", "objects")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "edgecast"))
from edgecast import CURL, CURL_LIFT, FRAME, LAYOUTS, MAT, PAPER_THICK, POSTER, TEAR_LENGTH, TEAR_WIDTH, calm_of, curl, linear  # noqa: E402

MM = 2.4  # CSS px to the mm, at the mat's rulers' scale
EDGE_DENSITY = 6  # pixels of the print's mask to the CSS px
DENSITY = 4  # and of the bared paper and the shadow
FIELD = 4  # points to the CSS px the fibres are laid by
MARGIN = 16  # rows rendered above and below one length, for the seam
# The print's line, in CSS px past the strip's edge: where it lies on average and how far either way it swings, so it
# always lies within the TEAR_WIDTH its mask has.
LINE, SWING = 5.0, 3.6
# Its wander at each scale, in CSS px across and how much: rougher the finer, but never in even teeth.
OCTAVES = ((90, 1.0), (30, 0.6), (10, 0.5), (3.5, 0.38), (1.2, 0.2), (0.4, 0.08))
RIM = 3.6  # how wide the bared paper runs past the print at most, in CSS px (1.5 mm)
EASE = 36  # over how many px the tear settles into the straight edge at the tab, as SiteShell's does
PAPER = (0.93, 0.92, 0.89)  # the poster's paper, bare, as it shows on the page: white, a little warm
# The fibres: length and width in mm (median, lognormal spread); a single one lets THROUGH of the light past it.
FIBRE, FIBRE_WIDTH, THROUGH = (1.4, 0.35), (0.03, 0.3), 0.6
PER_PX = 36.0  # fibres to the square px where the core is whole, enough to stop all light within a px of it
THIN = 0.35  # how gradually the core thins across its line, in CSS px
PULLED = 0.5  # fibres pulled out past the core, to each px down the tear


def octave(rng, sigma, n):
    """Noise that wraps round one length, sigma px across, n points to the px, at unit deviation."""
    field = ndimage.gaussian_filter1d(rng.standard_normal(TEAR_LENGTH * n), sigma * n, mode="wrap")
    return field / field.std()


def lines(layout, rng):
    """The tear down one length, at FIELD points to the px: the print's line, the core's past it, how settled into
    the straight edge each row is (0 at the tab, 1 away from it) and how far the strip lifts there."""
    y = (np.arange(TEAR_LENGTH * FIELD) + 0.5) / FIELD
    wander = sum(amount * octave(rng, sigma, FIELD) for sigma, amount in OCTAVES)
    wander /= np.sqrt(sum(amount**2 for _, amount in OCTAVES))
    settled = np.ones_like(y)
    for start, end in calm_of(layout):
        f = np.clip(np.maximum(start - y, y - end) / EASE, 0, 1)
        settled = np.minimum(settled, f * f * (3 - 2 * f))
    line = settled * (LINE + SWING * np.tanh(wander / 1.6))
    # The rim: wide where the tear ran so the core held on, a hair where it ran the other way.
    hold = np.clip(0.35 + 0.5 * octave(rng, 22, FIELD) + 0.3 * octave(rng, 5, FIELD), 0, 1)
    rim = settled * (0.25 + (RIM - 0.25) * hold**1.6)
    lift = np.interp(y, np.arange(TEAR_LENGTH + 1), curl(calm_of(layout), rng))
    return line, line + rim, settled, lift


def fibres(rng, cx, cy, heading, length, width, points=8):
    """Fibres centred at (cx, cy), heading off as given, each length mm long and width mm across (lognormal,
    median and spread), bending and wavering along their length; their points in CSS px and radius at each."""
    count = len(cx)
    reach = np.clip(rng.lognormal(np.log(length[0]), length[1], count), length[0] / 3, length[0] * 2) * MM
    t = np.linspace(-0.5, 0.5, points)
    turn = heading[:, None] + rng.normal(0, 0.8, count)[:, None] * t + np.cumsum(rng.normal(0, 0.15, (count, points)), axis=1)
    step = (reach / (points - 1))[:, None]
    x, y = np.cumsum(step * np.cos(turn), axis=1), np.cumsum(step * np.sin(turn), axis=1)
    x += cx[:, None] - x[:, points // 2 : points // 2 + 1]
    y += cy[:, None] - y[:, points // 2 : points // 2 + 1]
    thick = rng.lognormal(np.log(width[0]), width[1], count) * np.where(rng.random(count) < 0.04, 2.5, 1.0)
    radius = 0.5 * thick[:, None] * MM * (0.55 + 0.45 * np.sin(np.pi * (t + 0.5)) ** 0.5)
    return x, y, radius


def tear(layout, samples, proof):
    rng = np.random.default_rng(83 if layout == "wide" else 89)
    line, core, settled, lift = lines(layout, rng)
    rows = len(line)

    def raised(x, at):
        """How far the strip lifts at x, in the row at: rising toward its torn edge, as studio/edgecast curls it."""
        return lift[at] * np.clip(1 + (x - line[at]) / CURL, 0, 1) ** 2

    # The core's fibres: as many to the square px as make it whole well inside its line, fewer out to it and past,
    # from just under the print's edge out. Those by the edge lie along it as often as not; the rest any way.
    x = np.arange(-2 * FIELD, 24 * FIELD) / FIELD + 0.5 / FIELD
    d = core[:, None] - x[None, :]
    density = PER_PX / (1 + np.exp(-d / THIN)) * (x[None, :] > line[:, None] - 1.0) * settled[:, None] ** 0.5
    n = rng.poisson(density / FIELD**2)
    r, c = np.nonzero(n)
    r, c = np.repeat(r, n[r, c]), np.repeat(c, n[r, c])
    cx = x[c] + rng.uniform(-0.5, 0.5, len(c)) / FIELD
    cy = (r + rng.uniform(0, 1, len(c))) / FIELD
    along = rng.random(len(c)) < 0.5
    heading = np.where(along, np.pi / 2 + rng.normal(0, 0.4, len(c)) + np.pi * rng.integers(0, 2, len(c)), rng.uniform(0, 2 * np.pi, len(c)))
    bx, by, br = fibres(rng, cx, cy, heading, FIBRE, FIBRE_WIDTH)
    # Each lies in the core as deep as it is there: full under the print, thinning to nothing at its line.
    depth = PAPER_THICK * np.clip((core[r] - cx) / np.maximum(core[r] - line[r], 0.3), 0, 0.85) * rng.uniform(0.3, 1, len(c))
    bz = (depth + raised(cx, r))[:, None] + br

    # The pulled fibres: rooted in the core, lying out past it, straight out more or less.
    count = rng.poisson(PULLED * TEAR_LENGTH)
    at = rng.integers(0, rows, count)
    keep = rng.random(count) < settled[at]
    at = at[keep]
    root = core[at] - rng.uniform(0.2, 1.2, len(at))
    heading = rng.normal(0, 0.55, len(at))
    reach = np.clip(rng.lognormal(np.log(1.0), 0.4, len(at)), 0.4, 2.2) * MM
    px, py, pr = fibres(rng, root + 0.5 * reach * np.cos(heading), (at + 0.5) / FIELD + 0.5 * reach * np.sin(heading), heading, (1.0, 0.4), FIBRE_WIDTH)
    pz = (0.15 * PAPER_THICK * rng.random(len(at)) + raised(root, at))[:, None] + pr

    sets = [(bx, by, bz, br), (px, py, pz, pr)]
    copies = []
    for fx, fy, fz, fr in sets:
        middle = fy[:, fy.shape[1] // 2]
        copies.append((fx, fy, fz, fr))
        for shift, near in ((TEAR_LENGTH, middle < MARGIN + 8), (-TEAR_LENGTH, middle > TEAR_LENGTH - MARGIN - 8)):
            copies.append((fx[near], fy[near] + shift, fz[near], fr[near]))
    points = np.concatenate([np.stack([fx, -fy, fz], -1).reshape(-1, 3) for fx, fy, fz, _ in copies])
    radius = np.concatenate([fr.ravel() for *_, fr in copies])
    sizes = np.full(len(radius) // 8, 8, np.int32)
    print(f"TEAR {layout}: {len(sizes)} fibres")

    # The print and the core under it, as surfaces swept down the rows: the print flat to its line, the core on
    # under it and out past it, thinning, to just inside its own line, where its fibres are thick enough to hide
    # where it stops.
    wrap = (np.arange(-MARGIN * FIELD, (TEAR_LENGTH + MARGIN) * FIELD)) % rows
    ys = (np.arange(-MARGIN * FIELD, (TEAR_LENGTH + MARGIN) * FIELD) + 0.5) / FIELD
    back = np.array([-400.0, -120, -40, -16, -6, -2])
    print_x = np.concatenate([np.broadcast_to(back, (len(wrap), len(back))), line[wrap, None] - np.array([0.6, 0.2, 0.0])], 1)
    print_z = PAPER_THICK + raised(print_x, wrap[:, None])
    end = np.maximum(core[wrap] - 0.7, line[wrap] - 0.15)
    t = np.linspace(0, 1, 6)
    core_x = np.concatenate([np.broadcast_to(back, (len(wrap), len(back))), line[wrap, None] - 0.3 + t * (end - line[wrap] + 0.3)[:, None]], 1)
    thins = np.clip((core_x - line[wrap, None]) / np.maximum(core[wrap] - line[wrap], 0.3)[:, None], 0, 1)
    core_z = PAPER_THICK * (0.8 - 0.65 * thins) + raised(core_x, wrap[:, None])

    with tempfile.TemporaryDirectory() as work:
        np.savez(os.path.join(work, "tear.npz"), sizes=sizes, points=points, radius=radius, ys=ys, print_x=print_x, print_z=print_z, core_x=core_x, core_z=core_z)
        spec = {"paper": linear(PAPER_HEX), "print": linear(POSTER), "under": linear(MAT), "through": THROUGH, "rows": (-MARGIN, TEAR_LENGTH + MARGIN)}
        spec |= {"edge_frame": (0, TEAR_WIDTH), "edge_density": EDGE_DENSITY, "frame": FRAME, "density": DENSITY, "samples": samples}
        with open(os.path.join(work, "spec.json"), "w") as out:
            json.dump(spec, out)
        subprocess.run(["blender", "-b", "--factory-startup", "-P", os.path.join(HERE, "tear_render.py"), "--", work], check=True, stdout=subprocess.DEVNULL)
        edge = read(os.path.join(work, "edge.exr"))[..., 3]
        bared = read(os.path.join(work, "core.exr"))
        luma = np.array([0.2126, 0.7152, 0.0722], np.float32)
        cast, bare = (read(os.path.join(work, f"{name}.exr"))[..., :3] @ luma for name in ("cast", "bare"))
        flat = read(os.path.join(work, "flat.exr"))[..., :3].reshape(-1, 3).mean(axis=0)

    keep = lambda image, density: image[MARGIN * density : (MARGIN + TEAR_LENGTH) * density]  # noqa: E731
    edge, bared, cast, bare = keep(edge, EDGE_DENSITY), keep(bared, DENSITY), keep(cast, DENSITY), keep(bare, DENSITY)
    target = proof or OUT

    pixels = np.zeros(edge.shape + (4,), np.uint8)
    pixels[..., :3] = 255
    pixels[..., 3] = np.clip(edge * 255 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(pixels).save(os.path.join(target, f"poster-edge-{layout}.png"), optimize=True)

    # The bared paper in its own light: what it sends back over what the same paper lying flat does, times that
    # paper's colour, so it is as white as paper is on the page, and shaded only where it is.
    alpha = bared[..., 3]
    colour = bared[..., :3] / np.maximum(alpha, 1e-4)[..., None] / flat * np.array(linear(PAPER_HEX))
    colour = np.clip(colour, 0, 1)
    srgb = np.where(colour <= 0.0031308, colour * 12.92, 1.055 * colour ** (1 / 2.4) - 0.055)
    rgba = np.dstack([srgb, alpha])
    Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(target, f"poster-core-{layout}.png"), optimize=True)

    dark = np.clip(1 - cast / np.maximum(bare, 1e-5), 0, 1)
    shadow = np.zeros(dark.shape + (4,), np.uint8)
    shadow[..., 3] = (dark * 255 + 0.5).astype(np.uint8)
    Image.fromarray(shadow).save(os.path.join(target, f"poster-cast-{layout}.png"), optimize=True)
    print(f"TEAR {layout} edge {edge.shape[::-1]}, core {alpha.shape[::-1]}, darkest {dark.max():.3f}")


PAPER_HEX = "#" + "".join(f"{round(v * 255):02x}" for v in PAPER)


def read(path):
    with OpenEXR.File(path) as exr:
        channels = exr.channels()
        rgba = channels["RGBA"].pixels if "RGBA" in channels else np.stack([channels[c].pixels for c in "RGBA"], -1)
    return np.asarray(rgba, np.float32)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--layout", choices=tuple(LAYOUTS))
    parser.add_argument("--proof", help="write into this folder, not public/objects")
    args = parser.parse_args()
    if args.proof:
        os.makedirs(args.proof, exist_ok=True)
    for layout in LAYOUTS:
        if args.layout in (None, layout):
            tear(layout, args.samples, args.proof)


if __name__ == "__main__":
    main()
