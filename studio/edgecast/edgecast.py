# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "openexr>=3.3"]
# ///
"""The shadow two strips' edges leave on the strip after them, rendered, in place of a drop shadow.

    uv run studio/edgecast/edgecast.py [--only mat|poster] [--samples 1024] [--proof DIR]

The extras strip is a leather mat, MAT_THICK thick, lying on the contact strip; the work strip is the poster, paper
torn down its edge, lying on the mat. render.py builds each edge in Blender, the mat's cut burnished round and the
poster's along the very tear SiteShell cuts it with, all in white under the copy stand's light (as studio/tabcut
renders the tabs' cuts), and renders it with and without the strip. The one divided by the other is only what the
strip does to the light: dark where it shuts the room off the page beside it, and on its own edge where that turns
from the light, light where its edge catches it. That is written as black and white over a clear ground, so laid over
the edge it shades whatever lies there.

The mat is cut straight, so one CSS px of it serves its whole length: public/objects/mat-cast.png. The poster's tear
runs straight where its tab grows out, and where that is depends on the layout, so there is a length of it for each:
public/objects/poster-cast-<layout>.png. Each runs FRAME across, in CSS px from the strip's edge, at DENSITY. The
mat's edge lays only its shadow. The contact strip's hide is a leather mat as well, cut and burnished as the green
one is, lying on the walnut desk past the folders: contact-cast.png, and its lit rim, which is leather's colour
brightened, not paler, a layer of its own, contact-cast-light.png (dodge).

The spine is paper too, printed blue with the traffic signal, torn down its whole length with no tab, lying on the
linen strip's card in its sleeve: public/objects/spine-cast.png. Its print lying flat catches no more light at its
edge than on its face, so it has no light layer. Its tear bites in from the strip's edge (SiteShell's tear, not outward), so its
frame runs SPINE_FRAME, further in.
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "public", "objects")
FRAME = (-6.0, 34.0)  # CSS px from the strip's edge: in over the strip's own edge, out over the strip beyond
DENSITY = 4  # pixels to a CSS px, for a screen at twice its CSS pixels with room to spare
# The mat's leather, at the scale its rulers are printed (24 CSS px to a cm, mat/rulers.tsx): 2.5 mm.
MAT_THICK = 6.0
# The poster's paper, as thick as the tabs' (studio/tabcut THICK, 0.035 rem).
PAPER_THICK = 0.56
# How far the torn paper curls up off the mat at most, and how far in from the tear the curl begins, in CSS px.
CURL_LIFT, CURL = 1.2, 16.0
# How strongly the light the edge catches shows, as on the tabs.
LIGHT = 0.6
# What each is, as it shows on the page: the mat's leather (--color-mat), the contact strip's hide (its panel in
# SiteShell) and the poster's print at its torn edge, a dark night scene.
MAT, CONTACT, POSTER = "#236653", "#651415", "#2a2622"
# The walnut desk past the folders (studio/resume), as it shows beside the contact strip.
WALNUT = "#1e1610"
# Each leather mat: its name, its leather and what it lies on.
# The green mat's lit rim showed as a stripe of paler green down its edge beside its shadow, so it has none: only its
# shadow is laid.
LEATHERS = (("mat", MAT, CONTACT, False), ("contact", CONTACT, WALNUT, True))

# The spine's tear bites up to REACH * 1.4 in from its edge, so its frame starts further in.
SPINE_FRAME = (-16.0, 34.0)
# The spine's print at its edge, the signal's blue, and the card in the linen strip's sleeve, under it.
SPINE, CARD = "#1e5a96", "#fbf7eb"
SPINE_SEED = 7

# SiteShell's tear, which cuts the work strip: TEAR_LENGTH, the work strip's seed and the core's reach and grain,
# its tab's top (tabTops) and height (tabHeights over tabSpan, by band and protrude in rem, useStackMetrics).
TEAR_LENGTH, TEAR_WIDTH = 1600, 16
SEED, REACH = 31 + 17 * 2, 7
GRAIN = ((60, 0.55), (14, 0.3), (3, 0.55))
TAB_TOP, TAB_TALL, TAB_SPAN = 6.5, 10, 4
LAYOUTS = {"wide": (1.9, 2.1), "phone": (1.4, 1.5)}
REM = 16


def tear(calm, seed=SEED, outward=True):
    """SiteShell's tear(seed, reach, grain, calm, outward), the edge's x at each px down one length, from the strip's
    edge: outward, the tile lies just past the strip and the tear out past its edge; otherwise the tile ends at the
    strip's edge and the tear bites in from it."""
    m = 0xFFFFFFFF
    state = seed

    def random():
        nonlocal state
        state = (state + 0x6D2B79F5) & m
        t = ((state ^ (state >> 15)) * (1 | state)) & m
        t = ((t + (((t ^ (t >> 7)) * (61 | t)) & m)) & m) ^ t
        return ((t ^ (t >> 14)) & m) / 4294967296

    most = sum(amount for _, amount in GRAIN)
    scales = []
    for every, amount in GRAIN:
        knots = [random() for _ in range(math.floor(TEAR_LENGTH / every + 0.5))]
        scales.append((knots, amount))
    xs = []
    for y in range(TEAR_LENGTH + 1):
        wander = 0.0
        for knots, amount in scales:
            at = y / TEAR_LENGTH * len(knots)
            i = math.floor(at)
            f = at - i
            ease = f * f * (3 - 2 * f)
            wander += amount * (knots[i % len(knots)] * (1 - ease) + knots[(i + 1) % len(knots)] * ease)
        settled = 1.0
        for start, end in calm:
            f = min(max(start - y, y - end, 0) / 36, 1)
            settled = min(settled, f * f * (3 - 2 * f))
        xs.append(round(settled * REACH * (most - wander), 2) if outward else round(TEAR_WIDTH - settled * REACH * wander, 2) - TEAR_WIDTH)
    return np.array(xs)


def calm_of(layout):
    """Where the work strip's tear runs straight, for its tab, in px down: SiteShell's calm span."""
    band, protrude = LAYOUTS[layout]
    top = TAB_TOP * REM
    height = TAB_TALL * (band + protrude) / TAB_SPAN * REM
    reach = 2 * 0.2 * protrude * REM
    return [(top - reach, top + height + reach)]


def curl(calm, rng):
    """How far the torn edge curls up at each px down: a few slow swells round one length, so it repeats without a
    seam, flat where the tear runs straight for the tab and the tab's own render takes over."""
    y = np.arange(TEAR_LENGTH + 1)
    swell = np.zeros(len(y))
    for cycles in (3, 5, 8, 13):
        swell += rng.uniform(0.5, 1) / cycles**0.5 * np.sin(2 * np.pi * cycles * y / TEAR_LENGTH + rng.uniform(0, 2 * np.pi))
    swell = (swell - swell.min()) / (swell.max() - swell.min())
    flat = np.ones(len(y))
    for start, end in calm:
        away = np.clip(np.maximum(start - y, y - end) / 60, 0, 1)
        flat = np.minimum(flat, away * away * (3 - 2 * away))
    return CURL_LIFT * swell**2 * flat


def read(path):
    with OpenEXR.File(path) as exr:
        channels = exr.channels()
        rgb = channels["RGBA"].pixels if "RGBA" in channels else np.stack([channels[c].pixels for c in "RGB"], -1)
    return np.asarray(rgb, np.float32)[..., :3]


def linear(hex_colour):
    srgb = np.array([int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5)])
    return np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4).tolist()


def render(spec, samples, edge, frame=FRAME):
    """What the strip does to the light, pixel by pixel: off it, the page with it over the bare page; on it, its top
    over the same top lying flat, far from any edge. edge gives where the edge lies across each row, in CSS px.
    Returns that and how far in each pixel lies from the edge."""
    with tempfile.TemporaryDirectory() as work:
        path = os.path.join(work, "spec.json")
        json.dump({**spec, "frame": frame, "density": DENSITY, "samples": samples}, open(path, "w"))
        subprocess.run(["blender", "-b", "--factory-startup", "-P", os.path.join(HERE, "render.py"), "--", path, work], check=True, stdout=subprocess.DEVNULL)
        cast, bare, flat = (read(os.path.join(work, f"{name}.exr")) for name in ("cast", "bare", "flat"))
    luma = np.array([0.2126, 0.7152, 0.0722], np.float32)
    cast, bare, flat = cast @ luma, bare @ luma, flat @ luma
    x = frame[0] + (np.arange(cast.shape[1]) + 0.5) / DENSITY
    inward = edge[:, None] - x[None, :]
    cover = (inward > 0).astype(np.float32)
    return cast / np.maximum(cover * flat + (1 - cover) * bare, 1e-5), inward


def dodge(ratio, inward):
    """The light an edge catches as a colour-dodge layer, <name>-light.png: laid over the leather, it divides it by one
    less its grey, so it brightens the leather by the rendered ratio and keeps its colour, as a lit leather edge
    does in the reference photographs. White laid over it, as on paper, washes the green out pale instead. The
    ratio is in linear light, so on the page's sRGB it is ratio ** (1 / 2.2)."""
    brighter = np.maximum(ratio, 1) ** (1 / 2.2)
    # Only on the strip itself, in from its edge: past it the strip after lies in a layer of its own, so there is
    # nothing under this one to brighten, and its grey would show. Half a CSS px in, clear of the edge's own
    # antialiasing, where the strip is only partly there.
    on = (inward > 0.5).astype(np.float32)
    grey = (1 - 1 / brighter) * on
    return np.dstack([grey, grey, grey, on])


def save(ratio, inward, name, proof, frame=FRAME, coloured=False, lit=True):
    """Writes the shadow; coloured, the strip's lit edge is a colour, leather or print, so its light is a layer of
    its own (dodge), not white, unless it is not to be lit at all."""
    dark = np.clip(1 - ratio, 0, 1)
    light = np.clip((ratio - 1) * LIGHT, 0, 1)
    if coloured:
        light = np.zeros_like(light)
        layer = dodge(ratio, inward)
        brightest = float(1 / (1 - layer[..., 0].max()))
        # Paper flat on paper catches no more light at its edge than on its face: then there is no layer to lay.
        if lit and brightest > 1.02:
            Image.fromarray((np.clip(layer, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(proof or OUT, f"{name}-light.png"), optimize=True)
        print(name + "-light", "brightest", round(brightest, 3), "" if lit and brightest > 1.02 else "(none written)")
    alpha = dark + light
    colour = np.where(light > dark, 1.0, 0.0)
    rgba = np.dstack([colour, colour, colour, alpha])
    image = Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
    image.save(os.path.join(proof or OUT, f"{name}.png"), optimize=True)
    edge = round(-frame[0] * DENSITY)
    print(name, image.size, "darkest", round(float(dark.max()), 3), "lightest", round(float(light.max()), 3), "past the edge, by px:", np.round(dark[..., edge : edge + 10 * DENSITY : DENSITY].mean(axis=tuple(range(dark.ndim - 1))), 3))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=("mat", "contact", "poster", "spine"))
    parser.add_argument("--samples", type=int, default=1024)
    parser.add_argument("--proof")
    args = parser.parse_args()
    if args.proof:
        os.makedirs(args.proof, exist_ok=True)

    for name, leather, under, lit in LEATHERS:
        if args.only not in (None, name):
            continue
        # Straight, so a short length of it, averaged down, is every row of it.
        spec = {"kind": "mat", "thick": MAT_THICK, "length": 64, "past": 0, "colour": linear(leather), "roughness": 0.55, "under": linear(under)}
        ratio, inward = render(spec, args.samples, np.zeros(64 * DENSITY))
        rows = ratio[8:-8].mean(axis=0, keepdims=True)
        save(np.repeat(rows, DENSITY, axis=0), np.repeat(inward[:1], DENSITY, axis=0), f"{name}-cast", args.proof, coloured=True, lit=lit)

    if args.only in (None, "poster"):
        rng = np.random.default_rng(67)
        for layout in LAYOUTS:
            calm = calm_of(layout)
            edge = tear(calm)
            spec = {"kind": "poster", "thick": PAPER_THICK, "length": TEAR_LENGTH, "past": 120, "curl": CURL, "edge": edge.tolist(), "lift": curl(calm, rng).tolist()}
            spec |= {"colour": linear(POSTER), "roughness": 0.8, "under": linear(MAT)}
            rows = np.mod((np.arange((TEAR_LENGTH + 240) * DENSITY) + 0.5) / DENSITY - 120, TEAR_LENGTH)
            ratio, inward = render(spec, args.samples, np.interp(rows, np.arange(TEAR_LENGTH + 1), edge))
            top = 120 * DENSITY
            save(ratio[top : top + TEAR_LENGTH * DENSITY], inward[top : top + TEAR_LENGTH * DENSITY], f"poster-cast-{layout}", args.proof)

    if args.only in (None, "spine"):
        # Torn its whole length, so its curl swells all the way down.
        edge = tear([], SPINE_SEED, outward=False)
        spec = {"kind": "poster", "thick": PAPER_THICK, "length": TEAR_LENGTH, "past": 120, "curl": CURL, "edge": edge.tolist(), "lift": curl([], np.random.default_rng(71)).tolist()}
        spec |= {"colour": linear(SPINE), "roughness": 0.8, "under": linear(CARD)}
        rows = np.mod((np.arange((TEAR_LENGTH + 240) * DENSITY) + 0.5) / DENSITY - 120, TEAR_LENGTH)
        ratio, inward = render(spec, args.samples, np.interp(rows, np.arange(TEAR_LENGTH + 1), edge), SPINE_FRAME)
        top = 120 * DENSITY
        part = slice(top, top + TEAR_LENGTH * DENSITY)
        save(ratio[part], inward[part], "spine-cast", args.proof, SPINE_FRAME, coloured=True)


if __name__ == "__main__":
    main()
