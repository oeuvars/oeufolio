# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf>=1.24", "pillow>=11.3"]
# ///
"""The two pieces of art the rolled resume carries, for resume.py: uv run studio/resume/art.py

    art/page.png   the resume's page as the printer laid it down, public/resume.pdf at 300 dpi, black on white
    art/stamp.png  the tag's rubber stamp, RESUME in Futura Condensed ExtraBold inside a ruled frame, turned to
                   read down the tag, white on clear
"""

import os

import pymupdf
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ART = os.path.join(HERE, "art")
FUTURA = "/System/Library/Fonts/Supplemental/Futura.ttc"
CONDENSED_EXTRABOLD = 4

os.makedirs(ART, exist_ok=True)
page = pymupdf.open(os.path.join(ROOT, "public", "resume.pdf"))[0]
page.get_pixmap(dpi=300, colorspace=pymupdf.csGRAY).save(os.path.join(ART, "page.png"))

# The stamp's face, as cut: the word and a rule round it, at PX pixels to the em.
PX = 160
face = ImageFont.truetype(FUTURA, round(0.95 * PX), index=CONDENSED_EXTRABOLD)
word = "RÉSUMÉ"
left, top, right, bottom = face.getbbox(word)
pad, rule = round(0.14 * PX), round(0.06 * PX)
w, h = right - left + 2 * pad + 2 * rule, bottom - top + 2 * pad + 2 * rule
stamp = Image.new("L", (w, h), 0)
draw = ImageDraw.Draw(stamp)
draw.rounded_rectangle((0, 0, w - 1, h - 1), radius=round(0.08 * PX), outline=255, width=rule)
draw.text((pad + rule - left, pad + rule - top), word, font=face, fill=255)
clear = Image.new("RGBA", (w, h), (255, 255, 255, 0))
clear.putalpha(stamp)
clear.rotate(-90, expand=True).save(os.path.join(ART, "stamp.png"))
print("stamp", h / PX, "x", w / PX, "em")
