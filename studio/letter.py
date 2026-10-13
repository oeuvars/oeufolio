# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""The letter: the reference letter itself, with most of its words changed.

    uv run studio/letter.py

Everything that is not changed is the reference's own pixels, so the card, the pen and the drawings are
the photograph's and not a likeness of them. Three things are done to it:

- The page behind the card is taken out, so the card lies on whatever page it is put on.
- The words that go are rubbed out to bare card, stroke by stroke, and the card's own grain is put back.
- The new words are written in the reference's own hand. A word the reference already wrote is lifted
  whole and set down where it is wanted. Any other word is spelt from letters the reference wrote, a
  different one each time a letter comes round, with the small unevenness of a hand. The few letters it
  never wrote are drawn with the pen's width of line. The writing in the drawings is the same hand, smaller.

Writes public/objects/letter.avif at twice the reference's size. LETTER_DEBUG=<dir> also writes the
sheets the reading of the reference was checked against.
"""

import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEBUG = os.environ.get("LETTER_DEBUG")
UP = 2  # output pixels to one of the reference's

# All in the reference's pixels.
# The drawings. A mark whose middle lies in one of these is not handwriting on a line.
DRAWINGS = (
    (355, 290, 545, 345),
    (355, 345, 507, 392),
    (130, 578, 600, 724),
    (600, 550, 870, 792),
    (540, 724, 870, 781),
    (150, 997, 585, 1120),
)
# What the reference says, line by line: where the line runs, about where its baseline is, and its words.
# Words are given as they stand apart on the card: a ~ joins two written too close to tell apart.
LINES = (
    ("D0", 640, 810, 125, "AUG 6TH 2021"),
    ("D1", 640, 810, 140, "LOS ANGELES"),
    ("L0", 140, 400, 202, "HELLO Lise,"),
    ("L1", 140, 860, 244, "I must admit I was quite excited to send a letter to~you !"),
    ("L2", 140, 860, 285, "Hopefully this survives its overseas journey (let alone the"),
    ("L3", 140, 860, 326, "Los Angeles heat) I also must admit"),
    ("L4", 140, 860, 366, "that I've been a fan of your work for"),
    ("L5", 140, 860, 406, "quite some time now , so that~probably explains the excit-"),
    ("L6", 140, 860, 447, "ement. And thank you for taking the time to answer my"),
    ("L7", 140, 860, 485, "questions regarding the Netherlands. It's actually stupid"),
    ("L8", 140, 860, 525, "how often I go read or watch content about Dutch biking"),
    ("L9", 140, 860, 567, "infrastructure. Simply put, I am a simp."),
    ("L10", 140, 540, 754, "Hopefully I shall visit someday."),
    ("L11", 140, 860, 800, "Apart from that video, I 've been trying to watch more~films"),
    ("L12", 140, 860, 838, "and ingest more media in general. Especially since I've no"),
    ("L13", 140, 860, 881, "job the last 6 months or so... are there any movies or"),
    ("L14", 140, 860, 920, "music you've been particularly enjoying? I'd love to know!"),
    ("L15", 140, 860, 961, "I've been occupied with Nicolas Cage movies and Cowboy music."),
    ("L16", 140, 860, 988, "Quite the combination..."),
    ("S0", 600, 720, 1036, "cheers,"),
    ("S1", 600, 720, 1068, "Mabel"),
)


# About how wide the hand writes each letter, to tell which letters a mark is.
WIDTH = {**dict.fromkeys("il.,'!I1", 3), **dict.fromkeys("jtfr-()", 7), **dict.fromkeys("mw", 15), **dict.fromkeys("MW", 18), "s": 8, "c": 8}
TALL = "bdfhklt"


def blurred(a, sigma):
    """Gaussian blur of a float array of rows, columns and maybe channels. sigma is in pixels."""
    if a.ndim == 3:
        return np.dstack([blurred(a[..., c], sigma) for c in range(a.shape[2])])
    return ndimage.gaussian_filter(a, sigma, mode="reflect")


class Reading:
    """The reference read as ink: every mark, the line it stands on, the word it is in and the letter it is."""

    def __init__(self, ref):
        lum = ref.mean(axis=-1)
        # The bare card under each mark: the brightest thing near it, smoothed.
        self.card = blurred(ndimage.maximum_filter(lum, size=13), 6)
        self.ink = np.clip((self.card - lum) / (self.card - 0.16), 0, 1)
        marks, count = ndimage.label(self.ink > 0.33, structure=np.ones((3, 3)))
        self.marks = marks
        # Every pixel belongs to the mark nearest it, so a mark can be taken with its soft edge.
        away, (iy, ix) = ndimage.distance_transform_edt(marks == 0, return_indices=True)
        self.owner = marks[iy, ix]
        self.away = away
        boxes = ndimage.find_objects(marks)
        mids = ndimage.center_of_mass(marks > 0, marks, range(1, count + 1))
        sizes = ndimage.sum(marks > 0, marks, range(1, count + 1))
        self.box = {i + 1: (b[1].start, b[0].start, b[1].stop, b[0].stop) for i, b in enumerate(boxes)}
        self.mid = {i + 1: (m[1], m[0]) for i, m in enumerate(mids)}
        self.size = {i + 1: s for i, s in enumerate(sizes)}

        self.base = {name: (float(y), 0.0, (x0 + x1) / 2) for name, x0, x1, y, _ in LINES}
        for _ in range(3):
            self.assign()
            self.fit()
        self.assign()
        self.words = {}
        self.letters = {}
        for name, *_, text in LINES:
            self.split(name, text.split())

    def baseline(self, name, x):
        y, slope, x0 = self.base[name]
        return y + slope * (x - x0)

    def assign(self):
        """Give each mark to the line it stands on, or to none."""
        self.line = {name: [] for name, *_ in LINES}
        for i, (cx, cy) in self.mid.items():
            if any(x0 <= cx < x1 and y0 <= cy < y1 for x0, y0, x1, y1 in DRAWINGS):
                continue
            x0, y0, x1, y1 = self.box[i]
            if y1 - y0 > 46 or x1 - x0 > 60:
                continue
            best, off = None, 17.0
            for name, lx0, lx1, *_ in LINES:
                d = abs(self.baseline(name, cx) - 7 - cy)
                if lx0 <= cx < lx1 and d < off:
                    best, off = name, d
            if best:
                self.line[best].append(i)

    def fit(self):
        """Lay each line's baseline through the feet of the letters that stand on it."""
        for name, ids in self.line.items():
            feet = np.array([(self.mid[i][0], self.box[i][3]) for i in ids if self.box[i][3] - self.box[i][1] > 6])
            if len(feet) < 4:
                if len(feet):
                    self.base[name] = (float(np.median(feet[:, 1])), 0.0, self.base[name][2])
                continue
            x0 = self.base[name][2]
            y, slope = float(np.median(feet[:, 1])), 0.0
            for _ in range(4):
                near = np.abs(feet[:, 1] - y - slope * (feet[:, 0] - x0)) < 3.5
                if near.sum() < 4:
                    break
                slope, y = np.polyfit(feet[near, 0] - x0, feet[near, 1], 1)
            self.base[name] = (float(y), float(slope), x0)

    def split(self, name, tokens):
        """Cut a line into its words, and a word into its letters where the letters stand apart."""
        ids = sorted(self.line[name], key=lambda i: self.box[i][0])
        # The widest gaps in the line are the ones between its words.
        reach = np.maximum.accumulate([self.box[i][2] for i in ids])
        gaps = [self.box[i][0] - reach[n] for n, i in enumerate(ids[1:])]
        cuts = sorted(np.argsort(gaps)[::-1][: len(tokens) - 1] + 1)
        groups = [ids[a:b] for a, b in zip([0, *cuts], [*cuts, len(ids)])]
        if DEBUG and len(tokens) > 1:
            kept = sorted(gaps, reverse=True)
            print(f"{name}: narrowest gap between words {kept[len(tokens) - 2]:.0f}, widest inside one {kept[len(tokens) - 1] if len(kept) >= len(tokens) else 0:.0f}")
        for n, (token, group) in enumerate(zip(tokens, groups)):
            self.words[f"{name}.{n}"] = (token, group, name)
            # A dot belongs to the stroke under it.
            big = [i for i in group if self.size[i] >= 12 or self.box[i][3] - self.box[i][1] >= 6]
            glyphs = {i: [i] for i in big}
            for i in group:
                if i in glyphs:
                    continue
                cx, cy = self.mid[i]
                foot = self.baseline(name, cx)
                under = [j for j in big if self.box[j][0] - 2 <= cx <= self.box[j][2] + 3 and self.box[j][1] > cy]
                if cy < foot - 9 and under:
                    glyphs[min(under, key=lambda j: self.box[j][2] - self.box[j][0])].append(i)
                else:
                    glyphs[i] = [i]
            order = sorted(glyphs.values(), key=lambda g: min(self.box[i][0] for i in g))
            if "~" not in token:
                self.spell(name, token, order)

    def spell(self, name, token, glyphs):
        """Say which letters each mark of a word is. Letters written in one stroke stay together as one mark."""
        spans = []
        for glyph in glyphs:
            x0, x1 = min(self.box[i][0] for i in glyph), max(self.box[i][2] for i in glyph)
            foot = self.baseline(name, (x0 + x1) / 2)
            spans.append((x1 - x0, foot - min(self.box[i][1] for i in glyph), max(self.box[i][3] for i in glyph) - foot))

        def cost(span, chars):
            width, rise, drop = span
            wide = sum(WIDTH.get(c, 13 if c.isupper() or c.isdigit() else 9) for c in chars) - 1.5 * (len(chars) - 1)
            off = ((width - wide) / (3 + 0.25 * wide)) ** 2
            if all(c in ".,-'" for c in chars):
                return off + (4 if rise > 12 and "'" not in chars else 0)
            tall = any(c in TALL or c.isupper() or c.isdigit() for c in chars)
            dotted = any(c in "ij!?" for c in chars)
            hangs = any(c in "gjpqy(),f" for c in chars)
            if tall != (rise > 15.5) and not (dotted and not tall and rise < 21):
                off += 4
            if not hangs and drop > 4.5 or drop < 3 and any(c in "gjpqy" for c in chars):
                off += 4
            return off

        n, m = len(glyphs), len(token)
        best = np.full((n + 1, m + 1), np.inf)
        best[0, 0] = 0
        took = {}
        for g in range(n):
            for c in range(m):
                if not np.isfinite(best[g, c]):
                    continue
                for k in range(1, min(4, m - c) + 1):
                    total = best[g, c] + cost(spans[g], token[c : c + k]) + 0.3 * (k - 1)
                    if total < best[g + 1, c + k]:
                        best[g + 1, c + k] = total
                        took[g + 1, c + k] = k
        if not np.isfinite(best[n, m]):
            return
        c = m
        for g in range(n, 0, -1):
            k = took[g, c]
            chars = token[c - k : c]
            if cost(spans[g - 1], chars) < 1.0:
                self.letters.setdefault(chars, []).append((glyphs[g - 1], name))
            c -= k

    def lift(self, ids):
        """The ink of some marks, cut out with its soft edge, and the box it was cut from."""
        x0 = min(self.box[i][0] for i in ids) - 3
        y0 = min(self.box[i][1] for i in ids) - 3
        x1 = max(self.box[i][2] for i in ids) + 3
        y1 = max(self.box[i][3] for i in ids) + 3
        cut = (slice(y0, y1), slice(x0, x1))
        mine = np.isin(self.owner[cut], ids) & (self.away[cut] < 2.6)
        return self.ink[cut] * mine, (x0, y0, x1, y1)


def sheets(ref, reading):
    """What was read, to look over: the words boxed on the reference, and every letter that was lifted."""
    z = 3
    page = Image.fromarray((ref * 255).astype(np.uint8)).resize((ref.shape[1] * z, ref.shape[0] * z), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(page)
    for key, (token, group, name) in reading.words.items():
        x0 = min(reading.box[i][0] for i in group)
        y0 = min(reading.box[i][1] for i in group)
        x1 = max(reading.box[i][2] for i in group)
        y1 = max(reading.box[i][3] for i in group)
        draw.rectangle((x0 * z, y0 * z, x1 * z, y1 * z), outline=(220, 40, 40))
        draw.text((x0 * z, y1 * z + 1), f"{key} {token}", fill=(30, 60, 220))
    for name, lx0, lx1, *_ in LINES:
        draw.line((lx0 * z, reading.baseline(name, lx0) * z, lx1 * z, reading.baseline(name, lx1) * z), fill=(40, 170, 60))
    page.save(os.path.join(DEBUG, "words.png"))

    cell, per = 44, 28
    chars = sorted(reading.letters, key=lambda c: (len(c), c))
    sheet = Image.new("L", (per * cell + 30, len(chars) * cell), 255)
    draw = ImageDraw.Draw(sheet)
    for row, char in enumerate(chars):
        draw.text((4, row * cell + 14), char, fill=0)
        for col, (glyph, name) in enumerate(reading.letters[char][:per]):
            ink, (x0, y0, x1, y1) = reading.lift(glyph)
            tile = Image.fromarray(((1 - ink) * 255).astype(np.uint8))
            foot = reading.baseline(name, (x0 + x1) / 2)
            sheet.paste(tile, (30 + col * cell + 4, row * cell + 30 - round(foot - y0)))
        draw.line((30, row * cell + 30, sheet.width, row * cell + 30), fill=200)
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.Resampling.LANCZOS).save(os.path.join(DEBUG, "letters.png"))
    print(" ".join(f"{char}:{len(found)}" for char, found in sorted(reading.letters.items(), key=lambda kv: (len(kv[0]), kv[0]))))


def main():
    ref = np.asarray(Image.open(os.path.join(HERE, "assets", "letter.jpg")).convert("RGB"), dtype=np.float64) / 255
    reading = Reading(ref)
    if DEBUG:
        sheets(ref, reading)


main()
