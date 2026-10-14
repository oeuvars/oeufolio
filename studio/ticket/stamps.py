# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=11.3"]
# ///
"""The type on the strip of stamps that lies beside the ticket, one plate per ink, before it is printed.

    uv run studio/ticket/stamps.py

Each stamp is an Indian one, as the stamp sheets in the reference's feed are each their own country's: the name of
the country in Devanagari and in English along its foot, in black, and its value in rupees beside them, in
vermilion. The type is the page's own, from the font files the page loads: Martel for the Devanagari, the rupee
sign and the figures, Domine for the Latin. Writes studio/ticket/art/stamps-k.png and stamps-red.png, white where the ink prints,
the whole strip (ticket.json's "stamps") at PX_PER_EM. ticket.py prints them.
"""

import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TICKET = json.load(open(os.path.join(ROOT, "src", "components", "ticket", "ticket.json")))
FONTS = os.path.join(ROOT, "node_modules", "@fontsource")
PX_PER_EM = 192
MARTEL = os.path.join(FONTS, "martel", "files", "martel-devanagari-800-normal.woff")
DIGITS = os.path.join(FONTS, "martel", "files", "martel-latin-800-normal.woff")
DOMINE = os.path.join(FONTS, "domine", "files", "domine-latin-700-normal.woff")


def main():
    spec = TICKET["stamps"]
    sw, sh = spec["size"]
    ax, ay, aw, ah = spec["art"]
    count = len(spec["views"])
    size = (round(sw * PX_PER_EM), round(sh * count * PX_PER_EM))
    plates = {ink: Image.new("L", size, 0) for ink in ("k", "red")}
    draw = {ink: ImageDraw.Draw(plate) for ink, plate in plates.items()}
    em = PX_PER_EM
    deva = ImageFont.truetype(MARTEL, round(0.5 * em))
    latin = ImageFont.truetype(DOMINE, round(0.34 * em))
    sign = ImageFont.truetype(MARTEL, round(0.62 * em))
    value = ImageFont.truetype(DIGITS, round(0.78 * em))
    for i, rupees in enumerate(spec["values"]):
        top = i * sh * em
        # The keyline round the picture.
        x0, y0, x1, y1 = (ax - 0.07) * em, top + (ay - 0.07) * em, (ax + aw + 0.07) * em, top + (ay + ah + 0.07) * em
        draw["k"].rectangle((x0, y0, x1, y1), outline=255, width=round(0.035 * em))
        # The foot: the country, then its value to the right, all on one baseline.
        base = top + (ay + ah + 0.95) * em
        draw["k"].text((ax * em, base), "भारत", font=deva, fill=255, anchor="ls")
        left = ax * em + draw["k"].textlength("भारत", font=deva) + 0.12 * em
        draw["k"].text((left, base), "INDIA", font=latin, fill=255, anchor="ls")
        right = (ax + aw) * em
        draw["red"].text((right, base + 0.04 * em), rupees, font=value, fill=255, anchor="rs")
        right -= draw["red"].textlength(rupees, font=value) + 0.03 * em
        draw["red"].text((right, base + 0.04 * em), "₹", font=sign, fill=255, anchor="rs")
    for ink, plate in plates.items():
        plate.save(os.path.join(HERE, "art", f"stamps-{ink}.png"))
    print("wrote", count, "stamps,", f"{size[0]} x {size[1]} px")


main()
