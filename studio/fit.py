# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=11.3"]
# ///
"""Brings a render down to the size the page can use, so the page does not download points it never shows. Run from
the repository root:

    uv run studio/fit.py --width W [--quality Q] FILE ...

Each AVIF is scaled, keeping its shape, to W pixels wide (four times what the page shows it at covers every screen
up to three device pixels to one, with room to spare) and written back over itself. A file already that narrow is
left as it is.
"""

import argparse
import os

from PIL import Image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--quality", type=int, default=85)
    args = parser.parse_args()
    for path in args.files:
        image = Image.open(path)
        image.load()
        if image.width <= args.width:
            print(f"{path}: {image.width} wide already")
            continue
        before = os.path.getsize(path)
        height = round(image.height * args.width / image.width)
        image.resize((args.width, height), Image.Resampling.LANCZOS).save(path, "AVIF", quality=args.quality, speed=4)
        print(f"{path}: {image.width} x {image.height} -> {args.width} x {height}, {before // 1024} -> {os.path.getsize(path) // 1024} KB")


if __name__ == "__main__":
    main()
