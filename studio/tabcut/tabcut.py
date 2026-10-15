# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "openexr>=3.3"]
# ///
"""The folder tabs' cut paper, rendered: how the light falls on each tab's edge and the shadow it leaves, for the
page to lay over the tab, whatever its strip is made of.

    uv run studio/tabcut/tabcut.py [--samples 256] [--proof DIR]

Each tab is drawn by SiteShell as a flat shape cut out of its strip. render.py builds the same shape in Blender as a
sheet of paper with a ragged cut, its tab lifting a little off the folder, all in white under the copy stand's light,
and renders it with and without the paper. The one divided by the other is only what the paper does to the light:
darker where its cut turns from the lamp and where its shadow falls on the page below, lighter where its edge catches
the light. That is written as black and white over a clear ground, so laid over any strip it shades the strip's own
paper, leather or picture, and the tab and its page stay one surface.

There is one render for each size of tab SiteShell cuts: on a wide screen and on a phone (their band and how far the
tab stands out differ), at each tab height. Writes public/objects/tabcut-<layout>-<height>.avif, and
src/components/tabcut.json, where each lies in the tab's own rem and which file is which.
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


def read(path):
    with OpenEXR.File(path) as exr:
        channels = exr.channels()
        rgb = channels["RGBA"].pixels if "RGBA" in channels else np.stack([channels[c].pixels for c in "RGB"], -1)
    return np.asarray(rgb, np.float32)[..., :3]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument("--proof")
    args = parser.parse_args()

    table = {}
    for layout, (band, protrude) in LAYOUTS.items():
        for tall in HEIGHTS:
            height = tall * (band + protrude) / TAB_SPAN
            reach = 2 * 0.2 * protrude
            frame = (band - INTO, -reach - ALONG, INTO + protrude + OUT, height + 2 * (reach + ALONG))
            with tempfile.TemporaryDirectory() as work:
                spec = os.path.join(work, "spec.json")
                json.dump({"band": band, "protrude": protrude, "height": height, "frame": frame, "density": DENSITY, "samples": args.samples, "seed": round(tall * 10)}, open(spec, "w"))
                subprocess.run(["blender", "-b", "--factory-startup", "-P", os.path.join(HERE, "render.py"), "--", spec, work], check=True, stdout=subprocess.DEVNULL)
                cut, bare = read(os.path.join(work, "cut.exr")), read(os.path.join(work, "bare.exr"))
            ratio = (cut @ [0.2126, 0.7152, 0.0722]) / np.maximum(bare @ [0.2126, 0.7152, 0.0722], 1e-4)
            dark = np.clip(1 - ratio, 0, 1)
            light = np.clip((ratio - 1) * LIGHT, 0, 1)
            # The strip's edge runs straight only as far as the tab's joins (SiteShell's tear is calm there); past them it
            # is torn, and wanders off the straight edge rendered here. So the render fades out within the joins.
            rows = (np.arange(ratio.shape[0]) + 0.5) / DENSITY + frame[1]
            fade = np.clip(np.minimum(rows + reach, height + reach - rows) / (0.6 * reach), 0, 1) ** 1.5
            alpha = (dark + light) * fade[:, None]
            colour = np.where(light > dark, 1.0, 0.0)
            rgba = np.dstack([colour, colour, colour, alpha])
            name = f"tabcut-{layout}-{str(tall).replace('.', '_')}"
            image = Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
            image.save(os.path.join(ROOT, "public", "objects", f"{name}.avif"), quality=80, subsampling="4:4:4", speed=2)
            if args.proof:
                os.makedirs(args.proof, exist_ok=True)
                image.save(os.path.join(args.proof, f"{name}.png"))
            table[f"{layout}-{tall}"] = {"src": f"/objects/{name}.avif", "x": frame[0], "y": frame[1], "width": frame[2], "height": frame[3]}
            print(name, "darkest", round(float(dark.max()), 3), "lightest", round(float(light.max()), 3))

    with open(os.path.join(ROOT, "src", "components", "tabcut.json"), "w") as out:
        json.dump(table, out, indent=2)
        out.write("\n")


if __name__ == "__main__":
    main()
