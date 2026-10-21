# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "openexr>=3.3"]
# ///
"""The folder tabs' cut paper, rendered: how the light falls on each tab's edge and the shadow it leaves, for the
page to lay over the tab, whatever its strip is made of.

    uv run studio/tabcut/tabcut.py [--samples 256] [--proof DIR] [--leather]

Each tab is drawn by SiteShell as a flat shape cut out of its strip. render.py builds the same shape in Blender as a
sheet of paper with a ragged cut, its tab lifting a little off the folder, all in white under the copy stand's light,
and renders it with and without the paper. The one divided by the other is only what the paper does to the light:
darker where its cut turns from the lamp and where its shadow falls on the page below, lighter where its edge catches
the light. That is written as black and white over a clear ground, so laid over any strip it shades the strip's own
paper, leather or picture, and the tab and its page stay one surface.

There is one render for each size of tab SiteShell cuts: on a wide screen and on a phone (their band and how far the
tab stands out differ), at each tab height. Writes public/objects/tabcut-<layout>-<height>.avif, and
src/components/tabcut.json, where each lies in the tab's own rem and which file is which. The extras strip's tab is
not paper but its mat's thick leather, cut as the mat's own edge is, so it has one of its own,
tabcut-<layout>-10-leather.avif, with the light its edge catches apart in tabcut-<layout>-10-leather-light.avif,
for the page to lay over it in colour-dodge; so has the contact strip's tab, cut from its hide,
tabcut-<layout>-11_5-hide.avif. --leather renders only those.
"""

import argparse
import json
import os
import subprocess
import tempfile

import numpy as np
import OpenEXR
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
# SiteShell's tabs: the band and how far the tab stands out, in rem (useStackMetrics), and the heights its tabs
# come in (tabHeights over tabSpan, by the tab's width).
LAYOUTS = {"wide": (1.9, 2.1), "phone": (1.4, 1.5)}
HEIGHTS = (10, 11.5)
TAB_SPAN = 4
DENSITY = 64  # pixels to a rem: four to each CSS pixel, for a screen at twice its CSS pixels with room to spare
# How far the render runs past the tab, in rem: into its own page, out over the page beyond, and along the strip's
# edge, for the shadow's sake.
INTO, OUT, ALONG = 0.6, 0.9, 1.0
# How strongly the light the edge catches shows, over a page as light as the letter's.
LIGHT = 0.6
# The extras strip's tab is cut from its leather mat (SiteShell's leather tab): 2.5 mm of it at the scale the mat's
# rulers are printed, 24 CSS px to a cm, lying flat, its cut straight, the mat's green (--color-mat) on the contact
# strip's red hide, as studio/edgecast renders the strip's own edge. Its tab is the one height.
# Its cut is the mat's own (studio/edgecast): knife-straight, its top edge burnished round by ROUND of its thickness.
ROUND = 0.32
LEATHER = {"name": "leather", "thick": 0.375, "lift": 0.0, "ragged": 0.0, "round": ROUND, "colour": "#236653", "roughness": 0.55, "under": "#651415"}
# The contact strip's tab is cut from its hide, a leather mat as thick, the hide's red (its panel in SiteShell) on the
# walnut desk beyond the folders (studio/resume), as it shows past the strip. Its tab is the taller one.
HIDE = {**LEATHER, "name": "hide", "colour": "#651415", "under": "#1e1610"}
LEATHERS = ((LEATHER, 10), (HIDE, 11.5))


def read(path, channel=slice(0, 3)):
    with OpenEXR.File(path) as exr:
        channels = exr.channels()
        rgb = channels["RGBA"].pixels if "RGBA" in channels else np.stack([channels[c].pixels for c in "RGBA" if c in channels], -1)
    return np.asarray(rgb, np.float32)[..., channel]


def linear(hex_colour):
    srgb = np.array([int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5)])
    return np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4).tolist()


def cut(layout, tall, samples, proof, stuff=None):
    """Renders one tab's cut and writes it, and returns where it lies. stuff makes it other than white paper on white
    paper (LEATHER): a sheet of its own thickness and colour on a page of its own colour."""
    band, protrude = LAYOUTS[layout]
    height = tall * (band + protrude) / TAB_SPAN
    reach = 2 * 0.2 * protrude
    frame = (band - INTO, -reach - ALONG, INTO + protrude + OUT, height + 2 * (reach + ALONG))
    luma = np.array([0.2126, 0.7152, 0.0722], np.float32)
    with tempfile.TemporaryDirectory() as work:
        spec = os.path.join(work, "spec.json")
        extra = {} if stuff is None else {**stuff, "colour": linear(stuff["colour"]), "under": linear(stuff["under"])}
        json.dump({"band": band, "protrude": protrude, "height": height, "frame": frame, "density": DENSITY, "samples": samples, "seed": round(tall * 10), **extra}, open(spec, "w"))
        subprocess.run(["blender", "-b", "--factory-startup", "-P", os.path.join(HERE, "render.py"), "--", spec, work], check=True, stdout=subprocess.DEVNULL)
        lit, bare = read(os.path.join(work, "cut.exr")) @ luma, read(os.path.join(work, "bare.exr")) @ luma
        if stuff is None:
            under = bare
        else:
            # Over the page, what the sheet does to the bare page; on the sheet, to its own flat top.
            cover = read(os.path.join(work, "cover.exr"), 3)
            under = cover * (read(os.path.join(work, "flat.exr")) @ luma) + (1 - cover) * bare
    ratio = lit / np.maximum(under, 1e-5)
    dark = np.clip(1 - ratio, 0, 1)
    light = np.clip((ratio - 1) * LIGHT, 0, 1)
    # The strip's edge runs straight only as far as the tab's joins (SiteShell's tear is calm there); past them it
    # is torn, and wanders off the straight edge rendered here. So the render fades out within the joins.
    rows = (np.arange(ratio.shape[0]) + 0.5) / DENSITY + frame[1]
    fade = np.clip(np.minimum(rows + reach, height + reach - rows) / (0.6 * reach), 0, 1) ** 1.5
    name = f"tabcut-{layout}-{str(tall).replace('.', '_')}" + ("" if stuff is None else f"-{stuff['name']}")
    entry = {"src": f"/objects/{name}.avif", "x": frame[0], "y": frame[1], "width": frame[2], "height": frame[3]}
    if stuff is not None:
        # Leather's lit edge is brighter leather, not paler: a colour-dodge layer of its own, which brightens what is
        # under it by the ratio (on the page's sRGB, ratio ** (1 / 2.2)) and keeps its colour, as studio/edgecast
        # lights the mat's own edge, so the two meet at the tab's joins as one edge.
        # Only on the leather: off it, nothing lies under the layer to brighten, and the grey would show.
        grey = (1 - 1 / np.maximum(ratio, 1) ** (1 / 2.2)) * (cover > 0.5)
        # The tab's leather covers the strip's edge, and the strip's lit rim with it, from one join to the other, so
        # its own rim runs at full there and stops square where the strip's takes over: faded in as the shadow is,
        # the rim went dark along the joins.
        joins = (rows >= -reach) & (rows <= height + reach)
        layer = np.dstack([grey, grey, grey, (cover > 0.5) * joins[:, None]])
        write(layer, f"{name}-light", proof)
        entry["light"] = f"/objects/{name}-light.avif"
        print(name + "-light", "brightest", round(float(1 / (1 - grey.max())), 3))
        light = np.zeros_like(light)
    alpha = (dark + light) * fade[:, None]
    colour = np.where(light > dark, 1.0, 0.0)
    write(np.dstack([colour, colour, colour, alpha]), name, proof)
    print(name, "darkest", round(float(dark.max()), 3), "lightest", round(float(light.max()), 3))
    return entry


def write(rgba, name, proof):
    image = Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
    image.save(os.path.join(ROOT, "public", "objects", f"{name}.avif"), quality=80, subsampling="4:4:4", speed=2)
    if proof:
        os.makedirs(proof, exist_ok=True)
        image.save(os.path.join(proof, f"{name}.png"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument("--proof")
    parser.add_argument("--leather", action="store_true", help="only render the mat's leather tab, keeping the rest")
    args = parser.parse_args()

    path = os.path.join(ROOT, "src", "components", "tabcut.json")
    table = json.load(open(path)) if args.leather else {}
    for layout in LAYOUTS:
        if not args.leather:
            for tall in HEIGHTS:
                table[f"{layout}-{tall}"] = cut(layout, tall, args.samples, args.proof)
        for stuff, tall in LEATHERS:
            table[f"{layout}-{tall}-{stuff['name']}"] = cut(layout, tall, args.samples, args.proof, stuff)

    with open(path, "w") as out:
        json.dump(table, out, indent=2)
        out.write("\n")


if __name__ == "__main__":
    main()
