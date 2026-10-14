# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""The note written along the foot of the ticket, in the reference ticket's own hand.

    uv run studio/ticket/hand.py [--proof DIR]

studio/ticket/assets/hand.png is the handwritten note off the reference ticket the page follows, as the photograph
has it. No font is used: every letter here is one the reference's pen wrote, lifted from that photograph by its box
and set down again, with the next copy of it each time it comes round so that no two neighbours are the same, on
the baseline it sat on, with the spacing of the hand. A word is only ever spelt from letters the reference wrote,
so the note is worded with those alone: there is no b, f, j, q or x, and no capital but I, C, O, N, Y and T.

The photograph is small, so it is enlarged four times and its ink edge drawn again from the enlarged grey, as a
marker leaves it. Writes studio/ticket/art/hand.png, white where the ink is, as wide as the note's box on the
ticket (ticket.json's "note") at PX_PER_EM.
"""

import argparse
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TICKET = json.load(open(os.path.join(ROOT, "src", "components", "ticket", "ticket.json")))
UP = 4  # the photograph is enlarged this many times before the ink is read off it
PX_PER_EM = 164  # the reference ticket is 615 photograph pixels across, which is 15 em
TEXT = "Come say hello, any time. Or write a note, ask anything, tell me what the weather is like where you are."

# The reference's four lines: the band each sits in and its baseline, in pixels of the enlarged photograph.
LINES = ((60, 215, 165), (190, 335, 287), (318, 452, 410), (452, 565, 530))
# Every letter used, by the line it is on and its left and right edge there, in pixels of the enlarged photograph.
# Where two letters touch, the cut between them is where the pen ran from one into the next.
GLYPHS = {
    "C": [(0, 546, 604), (1, 1595, 1652)],
    "O": [(0, 1694, 1740)],
    "a": [(0, 406, 452), (0, 1483, 1530), (3, 158, 204), (3, 361, 408), (3, 511, 557), (3, 1150, 1196)],
    "c": [(0, 664, 705), (3, 1459, 1503), (3, 1588, 1631)],
    "d": [(0, 1914, 1969), (1, 222, 274), (2, 417, 470), (3, 452, 504)],
    "e": [(0, 303, 361), (0, 1247, 1305), (0, 1976, 2034), (1, 530, 590), (1, 859, 912), (1, 1123, 1183), (1, 1881, 1940), (2, 153, 212), (2, 351, 410), (2, 785, 843), (2, 1856, 1915), (3, 261, 319), (3, 621, 673), (3, 936, 995), (3, 1004, 1061)],
    "g": [(0, 1171, 1237), (1, 709, 776), (2, 971, 1039)],
    "h": [(2, 1049, 1091), (3, 111, 151), (2, 735, 776)],
    "i": [(0, 1456, 1478), (0, 1886, 1907), (1, 108, 130), (1, 355, 378), (1, 1665, 1688), (2, 539, 562), (2, 1299, 1322)],
    "k": [(1, 1479, 1552), (3, 1640, 1711)],
    "l": [(0, 187, 206), (0, 1002, 1020), (1, 503, 523), (2, 225, 245), (3, 1515, 1535)],
    "m": [(2, 1212, 1293), (3, 846, 927)],
    "n": [(0, 1119, 1163), (0, 1543, 1588), (1, 1950, 1995), (2, 570, 614)],
    "o": [(0, 214, 250), (0, 618, 653), (0, 1027, 1063), (0, 1597, 1633), (1, 1360, 1397), (2, 254, 288), (2, 1630, 1665), (2, 1768, 1803), (3, 767, 801), (3, 1382, 1417), (3, 1543, 1579)],
    "p": [(0, 1402, 1451), (2, 297, 346)],
    "r": [(1, 284, 346), (1, 788, 850), (1, 1407, 1470), (2, 1927, 1988)],
    "s": [(1, 601, 632), (2, 1334, 1366), (2, 2002, 2034)],
    "t": [(0, 1798, 1848), (1, 141, 190), (2, 1103, 1152), (2, 1376, 1420), (3, 572, 618), (3, 720, 767), (3, 1075, 1124), (3, 1211, 1260)],
    "u": [(0, 1077, 1110), (0, 1754, 1787)],
    "v": [(0, 260, 300), (2, 110, 150), (2, 1814, 1854), (3, 218, 259)],
    "w": [(1, 1189, 1252), (2, 1559, 1621)],
    "y": [(1, 913, 983)],
    ",": [(1, 632, 656), (1, 1801, 1826)],
    ".": [(0, 1638, 1654), (1, 994, 1009), (2, 1418, 1434), (3, 1719, 1734)],
}
GAP = 9  # between two letters of a word, in pixels of the enlarged photograph
SPACE = 46  # between words
LEADING = 122  # from one baseline to the next
# How deep a letter may reach below its line's band, for the tails of g, p and y.
TAIL = {"g": 70, "p": 55, "y": 64, ",": 25}


def ink(grey):
    """The marker's ink, from the enlarged grey: solid where it is dark, falling off over a pixel or two."""
    return np.clip((0.62 - grey) / 0.16, 0, 1)


def lift(page, letter, line, x0, x1):
    """One letter off the photograph: its ink in the column x0 to x1 of its line, keeping only the strokes whose
    middle lies in that column, so a neighbour's stroke that crosses into it is left behind. Returns the letter and
    how far above the baseline its top edge is."""
    top, bottom, base = LINES[line]
    bottom = max(bottom, base + TAIL.get(letter, 0))
    if letter == "y":
        bottom = base + TAIL["y"]
    crop = page[top:bottom, x0 - 6 : x1 + 6]
    labels, count = ndimage.label(crop > 0.3)
    parts = []
    for i, where in enumerate(ndimage.find_objects(labels), 1):
        cx = (where[1].start + where[1].stop) / 2
        if 6 <= cx <= crop.shape[1] - 6:
            parts.append((int((labels == i).sum()), i, where))
    # The letter is its biggest stroke and whatever else is about as big. A small mark counts only if the letter is
    # an i and the mark sits straight above it; anything else small is a neighbour's tail or dot.
    parts.sort(reverse=True)
    body = parts[0][2]
    keep = np.zeros(crop.shape, dtype=bool)
    for area, i, where in parts:
        big = area >= 0.2 * parts[0][0]
        dot = letter == "i" and where[0].stop <= body[0].start + 6 and where[0].stop >= body[0].start - 45 and where[1].start >= body[1].start - 8 and where[1].stop <= body[1].stop + 8
        if big or dot:
            keep |= labels == i
    glyph = crop * keep
    cols = np.where(glyph.max(axis=0) > 0.2)[0]
    rows = np.where(glyph.max(axis=1) > 0.2)[0]
    glyph = glyph[rows[0] : rows[-1] + 1, cols[0] : cols[-1] + 1]
    return glyph, base - (top + rows[0])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof")
    args = parser.parse_args()

    photo = Image.open(os.path.join(HERE, "assets", "hand.png")).convert("L")
    grey = np.asarray(photo.resize((photo.width * UP, photo.height * UP), Image.Resampling.BICUBIC), dtype=np.float64) / 255
    page = ink(ndimage.gaussian_filter(grey, 1.2))

    glyphs = {letter: [lift(page, letter, *where) for where in places] for letter, places in GLYPHS.items()}
    turn = {letter: 0 for letter in glyphs}

    # Set the words, then break them into lines as wide as the note's box.
    width = TICKET["note"][2] * PX_PER_EM
    words = []
    for word in TEXT.split(" "):
        placed, x = [], 0.0
        for letter in word:
            choices = glyphs[letter]
            glyph, rise = choices[turn[letter] % len(choices)]
            turn[letter] += 1
            placed.append((x, glyph, rise))
            x += glyph.shape[1] + GAP
        words.append((placed, x - GAP))
    lines, line, used = [], [], 0.0
    for placed, w in words:
        if line and used + SPACE + w > width:
            lines.append(line)
            line, used = [], 0.0
        line.append((used + (SPACE if line else 0), placed))
        used += (SPACE if line[:-1] else 0) + w
    lines.append(line)

    top = 150  # room above the first baseline for the tall letters
    height = round(top + LEADING * (len(lines) - 1) + 110)
    out = np.zeros((height, round(width)))
    rng = np.random.default_rng(4)
    for i, line in enumerate(lines):
        # A hand drifts a little off the line as it goes across.
        base = top + LEADING * i + rng.normal(0, 2)
        slope = rng.normal(0, 0.004)
        for left, placed in line:
            for x, glyph, rise in placed:
                gx = round(left + x)
                gy = round(base + slope * gx - rise + rng.normal(0, 1.2))
                h, w = glyph.shape
                y0, x0 = max(0, gy), max(0, gx)
                y1, x1 = min(height, gy + h), min(out.shape[1], gx + w)
                out[y0:y1, x0:x1] = np.maximum(out[y0:y1, x0:x1], glyph[y0 - gy : y1 - gy, x0 - gx : x1 - gx])

    out = np.clip(out, 0, 1)
    Image.fromarray((out * 255).astype(np.uint8)).save(os.path.join(HERE, "art", "hand.png"))
    if args.proof:
        Image.fromarray(((1 - out) * 255).astype(np.uint8)).save(os.path.join(args.proof, "hand.png"))
    print("wrote", len(lines), "lines,", f"{out.shape[1] / PX_PER_EM:.2f} x {out.shape[0] / PX_PER_EM:.2f} em")


main()
