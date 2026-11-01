# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=11.3", "numpy>=2"]
# ///
"""My signature for the typed résumé letter, lifted off a photograph of it: uv run studio/resume/signature.py

    art/signature-photo.jpg              the photograph, cropped to the signature in black pen and its underline
    public/objects/resume/signature.webp the pen's strokes alone, dark ink on clear, at twice the photograph's size
"""

import os

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "public", "objects", "resume", "signature.webp")

SCALE = 2
# The pen's ink, a blue-black a shade off the type's.
INK = (24, 26, 38)

photo = Image.open(os.path.join(HERE, "art", "signature-photo.jpg")).convert("L")
photo = photo.resize((photo.width * SCALE, photo.height * SCALE), Image.LANCZOS)
grey = np.asarray(photo, dtype=np.float32)

# The page's light falls off across the crop, so each pixel is read against the paper around it, not a fixed white:
# a blur wide enough to swallow a stroke stands in for the bare paper.
paper = np.asarray(photo.filter(ImageFilter.GaussianBlur(18 * SCALE)), dtype=np.float32)
paper = np.maximum(paper, grey)
darkness = 1 - grey / np.maximum(paper, 1)

# Paper grain and show-through stay under LOW; a stroke's core is past HIGH. Between them the edge keeps its softness.
LOW, HIGH = 0.12, 0.45
alpha = np.clip((darkness - LOW) / (HIGH - LOW), 0, 1)

rgba = np.zeros((*alpha.shape, 4), dtype=np.uint8)
rgba[..., :3] = INK
rgba[..., 3] = np.round(alpha * 255).astype(np.uint8)
sign = Image.fromarray(rgba, "RGBA")
# Trimmed to the strokes, not to the odd faint speck of paper that only just clears LOW.
sign = sign.crop(Image.fromarray(((alpha > 0.2) * 255).astype(np.uint8)).getbbox())
sign.save(OUT, "WEBP", lossless=True)
print(OUT, sign.size)
