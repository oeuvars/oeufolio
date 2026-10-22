# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=11.3"]
# ///
"""Brings a render down to what the page can use, so the page does not download points it never shows or bytes it
does not need. Run from the repository root:

    uv run studio/fit.py --width W [--quality Q] FILE.avif ...
    uv run studio/fit.py FILE.png ...

An AVIF is scaled, keeping its shape, to W pixels wide (four times what the page shows it at covers every screen up
to three device pixels to one, with room to spare) and written back over itself. A file already that narrow is left
as it is.

A PNG, which Blender writes for a render with a cut-out, is written again as lossless WebP beside it, every point as
it was at about half the size, and the PNG is removed.
"""

import argparse
import os

from PIL import Image


def shrink(path, width, quality):
    image = Image.open(path)
    image.load()
    if image.width <= width:
        print(f"{path}: {image.width} wide already")
        return
    before = os.path.getsize(path)
    height = round(image.height * width / image.width)
    image.resize((width, height), Image.Resampling.LANCZOS).save(path, "AVIF", quality=quality, speed=4)
    print(f"{path}: {image.width} x {image.height} -> {width} x {height}, {before // 1024} -> {os.path.getsize(path) // 1024} KB")


def lossless(path):
    image = Image.open(path)
    image.load()
    out = os.path.splitext(path)[0] + ".webp"
    image.save(out, "WEBP", lossless=True, quality=100, method=6)
    print(f"{path} -> {out}, {os.path.getsize(path) // 1024} -> {os.path.getsize(out) // 1024} KB")
    os.remove(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("--width", type=int)
    parser.add_argument("--quality", type=int, default=85)
    args = parser.parse_args()
    for path in args.files:
        if path.endswith(".png"):
            lossless(path)
        elif args.width:
            shrink(path, args.width, args.quality)
        else:
            parser.error(f"{path}: an AVIF needs --width")


if __name__ == "__main__":
    main()
