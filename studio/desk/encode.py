# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=11.3"]
# ///
"""Encodes a render as AVIF: uv run studio/encode.py render.png render.avif

The stage calls this for every shot. Blender can write AVIF itself, but only with colour at half
resolution (4:2:0), which frays coloured edges such as red enamel on metal. This keeps full colour."""

import sys

from PIL import Image

QUALITY = 98

source, target = sys.argv[1:3]
Image.open(source).convert("RGBA").save(target, quality=QUALITY, subsampling="4:4:4", speed=2)
