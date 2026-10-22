# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""The letter: a new letter, written in the reference letter's own hand.

    uv run studio/letter.py

The ink is the reference's, so the pen is the photograph's and not a likeness of it. Four things are done:

- The card is taken out from under the ink. What is left is the ink alone, see-through wherever the card
  was bare, so it is written on whatever page it is put on. The card's grain goes out separately, as a
  texture that page can be given.
- The reference's own words and drawings are taken off, all but the few words that stay where they are.
- The new words are written in the reference's hand. A word the reference already wrote is lifted whole
  and set down where it is wanted. Any other word is spelt from letters the reference wrote, a different
  one each time a letter comes round, with the small unevenness of a hand. The few letters it never wrote
  are drawn with the pen's width of line.
- New drawings are made with the same pen, in the reference's manner: quick outlines, scribbled hair,
  speech in bubbles. Some of what is said in them is the reference's own, lifted as it was written.

Writes public/objects/letter.avif, the ink at twice the reference's size and cut close to it;
public/objects/letter-strip.avif, the same drawings set one under another for the page's folded strip;
public/objects/letter-band.avif, the same drawings set side by side for the strip folded on a phone, where it lies
across the window;
and public/photos/laid.avif, the card's grain as a tile to multiply a page's colour by. LETTER_DEBUG=<dir>
also writes the sheets the reading of the reference was checked against.
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


# Letters the reading got wrong: every letter of these words, and these letters of those.
MISREAD = {"L1.6", "L7.0", "D0.1"}
MISREAD_LETTERS = {("a", "L3.2"), ("a", "L4.0"), ("a", "L5.7"), ("c", "L14.0"), ("E", "L12.6"), ("g", "L8.10"), ("o", "L13.10"), ("o", "L14.4"), ("o", "L14.8"), ("t", "L16.2"), ("t", "L5.9"), ("s", "L15.9"), ("s", "L5.7"), ("w", "L8.0")}
# Letters cut out of a word by hand, where the pen ran them into the next: the box, and the line it is on.
CUTS = {
    "C": ((630, 937, 648, 965), "L15"),
    "M": ((626, 1049, 649, 1074), "S1"),
    "k~know": ((715, 905, 727, 930), "L14"),
    "k~taking": ((469, 430, 482, 453), "L6"),
    "O'": ((667, 128, 681, 144), "D1"),
    "L'": ((652, 128, 665, 144), "D1"),
    "A'": ((700, 128, 715, 144), "D1"),
    "E'": ((766, 129, 778, 144), "D1"),
    "6'": ((710, 109, 724, 129), "D0"),
}
# Letters the reference never wrote, as pen strokes: how wide, then points right of the letter's left edge
# and down from its foot.
DRAWN = {
    "z": (9, [[(1.5, -9.4), (9.6, -10.0), (0.6, -0.9), (9.2, -0.5)]]),
    "P": (10, [[(3.4, -16.6), (2.2, -8), (1.0, 0.4)], [(2.8, -16.2), (8.2, -16.8), (10.6, -13.4), (8.4, -9.6), (2.2, -8.6)]]),
    "Y": (12, [[(1.4, -16.8), (4.6, -12.6), (6.6, -8.8)], [(12.4, -17.2), (8.6, -11.6), (6.6, -8.8), (5.4, -4.4), (4.4, 0.3)]]),
    "T": (13, [[(0.8, -16.4), (7.0, -16.8), (13.2, -17.2)], [(7.6, -16.9), (6.6, -8.4), (5.6, 0.3)]]),
    "5": (10, [[(8.6, -15.6), (2.6, -15.4), (2.0, -9.2), (5.8, -10.2), (9.0, -7.2), (8.6, -2.6), (5.0, -0.3), (1.2, -2.2)]]),
    "T'": (12, [[(1.6, -10.6), (6.6, -10.9), (12.0, -11.2)], [(7.0, -11.0), (6.5, -5), (6.2, 0.2)]]),
    "C'": (10, [[(9.8, -9.2), (6.4, -11.2), (2.4, -9.9), (0.6, -5.6), (2.2, -1.4), (6.2, -0.2), (10.0, -2.0)]]),
}
UNREADABLE = ("in", "ur", "ic")  # letters run together so that, lifted out of their word, they read as another
PEN = 2.1  # width of the pen's line
CAP = 17.0  # how tall the hand writes a capital
# Things said in the reference's drawings that are said again in the new ones: where each is, and its baseline.
SAID = {
    "how": ((568, 638, 608, 654), 651),
    "relaxing!": ((563, 654, 644, 677), 668),
    "golly!": ((343, 683, 395, 706), 697),
}
# The letter as it is to read. Each run of writing: the line whose baseline it follows, or a point and
# a slope; where it starts, or None to go on from the word before; how big; and its words. A word the
# reference wrote, and that has not been used yet, is lifted whole and set down; any other is spelt out.
# = leaves a word of the reference where it is. # lifts something said in a drawing. + sets a word close
# against the one before.
WRITING = (
    ((700, 126.5, 0), 698, 1, "O'+C'+T'"),
    ((745, 127.3, 0), 745, 1, "2026"),
    ((692, 142.5, 0), 694, 1, "T'+O'+O'"),
    ((740, 142.5, 0), 738, 1, "L'+A'+T'+E'"),
    ("L0", None, 1.1, "=L0.0 younger me,"),
    ((160, 243, -0.004), 160, 1, "I know what you're like, so I know you'll call all of"),
    ((156, 282, -0.004), 156, 1, "this stupid. I'm telling you anyway."),
    ((160, 326, -0.004), 160, 1, "You pick up an electric guitar and"),
    ((158, 365, -0.004), 158, 1, "you don't put it down."),
    ((160, 436, -0.004), 160, 1, "You learn to shave slowly, the old way, and it ends"),
    ((156, 475, -0.004), 156, 1, "up being the part of the morning that is yours."),
    ((160, 644, -0.004), 160, 1, "You give your heart to Arsenal, which is a stupid"),
    ((158, 683, -0.004), 158, 1, "thing to do with a heart."),
    ((160, 842, -0.004), 160, 1, "And the cats. You think you are not a"),
    ((156, 881, -0.004), 156, 1, "cat person. Then Dilly falls asleep on"),
    ((158, 920, -0.004), 158, 1, "top of your keyboard and it's wraps."),
    ((160, 1003, -0.004), 160, 1, "It isn't impressive, any of it, and I wouldn't trade it."),
    ((158, 1042, -0.004), 158, 1, "Take your time getting here."),
    ((612, 1113, -0.01), 612, 1, "cheers,"),
    ((622, 1147, -0.01), 622, 1, "Anurag"),
)
TALL_PAGE = 1240  # the new letter runs longer than the card did
# The folded strip: the date, the drawings and the signature, cut from the page and set one under another.
# Each row is where it sits across the strip, from 0 at the left to 1 at the right, and the boxes it is
# made of, side by side with their feet level.
STRIP = (
    (1.0, ((688, 106, 800, 150),)),
    (0.5, ((594, 256, 796, 408),)),
    (1.0, ((646, 490, 758, 608),)),
    (0.5, ((388, 506, 452, 593), (456, 506, 526, 593), (544, 496, 612, 593))),
    (0.5, ((280, 686, 480, 806),)),
    (0.9, ((550, 700, 640, 806),)),
    (0.5, ((598, 810, 840, 982),)),
    (0.4, ((144, 1048, 329, 1216),)),
    (0.9, ((604, 1088, 712, 1164),)),
)
STRIP_WIDTH, STRIP_GAP = 244, 58
# On a phone the strip folds to a band across the window, and the same drawings are set in a row along it, each in the
# middle of the row's height, this far apart.
BAND_GAP = 46
STRIP_CLEARED = ((584, 360, 608, 396), (376, 586, 394, 600), (576, 586, 592, 600), (329, 1085, 540, 1216))  # ends of things cut through
SPACE = 16.0  # bare card between two words, and how much it varies
PAGE = (150, 58, 640, 104)  # bare card, to take paper grain from
SHEET = (108, 58, 640, 172)  # a larger piece of it, for the texture
FAINT = 0.1  # what the eye reads as ink on bare card and is only its grain

# About how wide the hand writes each letter, to tell which letters a mark is.
WIDTH = {**dict.fromkeys(".,'!1", 3), **dict.fromkeys("ilI", 6), **dict.fromkeys("jr-sce", 9), **dict.fromkeys("gp()", 12), "m": 16, "w": 14, "M": 16}
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
                self.spell(name, f"{name}.{n}", token, order)

    def spell(self, name, key, token, glyphs):
        """Say which letters each mark of a word is. Letters written in one stroke stay together as one mark."""
        spans = []
        for glyph in glyphs:
            x0, x1 = min(self.box[i][0] for i in glyph), max(self.box[i][2] for i in glyph)
            foot = self.baseline(name, (x0 + x1) / 2)
            spans.append((x1 - x0, foot - min(self.box[i][1] for i in glyph), max(self.box[i][3] for i in glyph) - foot))

        def cost(span, chars):
            width, rise, drop = span
            wide = sum(WIDTH.get(c, 12 if c.isupper() or c.isdigit() else 10) for c in chars) - 1.0 * (len(chars) - 1)
            off = ((width - wide) / (3 + 0.25 * wide)) ** 2
            if all(c in ".,-'" for c in chars):
                return off + (4 if rise > 12 and "'" not in chars else 0)
            tall = any(c in TALL or c.isupper() or c.isdigit() for c in chars)
            dotted = any(c in "ij!?" for c in chars)
            hangs = any(c in "gjpqy(),f" for c in chars)
            if tall and rise < 12.5 or not tall and rise > 14.5 and not (dotted and rise < 21):
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
                if chars not in ("i", "j") or len(glyphs[g - 1]) > 1:
                    self.letters.setdefault(chars, []).append((glyphs[g - 1], name, key))
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


class Hand:
    """Writes on the card in the reference's hand."""

    def __init__(self, reading, shape):
        self.reading = reading
        self.wet = np.zeros(shape)  # the new ink, at the output's size
        self.rng = np.random.default_rng(11)
        self.kept = set()
        self.letters = {}
        for chars, found in reading.letters.items():
            good = [(glyph, name) for glyph, name, key in found if key not in MISREAD and (chars, key) not in MISREAD_LETTERS]
            if not set(chars) & set("ij!?"):  # a dot read into a letter that has none is its neighbour's
                good = [([i for i in glyph if reading.size[i] >= 12] or glyph, name) for glyph, name in good]
            sized = [self.glyph(*reading.lift(glyph), reading.baseline(name, np.mean([reading.mid[i][0] for i in glyph]))) for glyph, name in good]
            if len(sized) > 3:  # one far from the rest in size is another letter
                wide, tall = np.median([g[3] for g in sized]), np.median([g[4] for g in sized])
                sized = [g for g in sized if abs(g[3] - wide) < 0.35 * wide + 2 and abs(g[4] - tall) < 3.5]
                if chars == "m":  # a narrow m reads as an n
                    sized = [g for g in sized if g[3] >= wide]
            if sized:
                self.letters[chars] = sized
        for chars, ((x0, y0, x1, y1), name) in CUTS.items():
            self.letters.setdefault(chars.split("~")[0], []).append(self.glyph(reading.ink[y0:y1, x0:x1] * (reading.away[y0:y1, x0:x1] < 2.6), (x0, y0, x1, y1), reading.baseline(name, (x0 + x1) / 2)))
        for chars, (wide, strokes) in DRAWN.items():
            self.letters[chars] = [self.glyph(*self.pen(wide, strokes, seed), 0.0) for seed in range(4)]
        self.queue = {}
        self.shift = np.zeros(2)
        self.grown = (1.0, np.zeros(2))  # how much larger the pen draws, and about what point
        self.drawn = np.zeros((shape[0] // UP, shape[1] // UP))  # the drawings' ink, at the reference's size
        self.spare = {}  # the reference's own words, by what they say, till each is used
        for key, (token, _, name) in reading.words.items():
            if name.startswith("L") and name != "L0" and "~" not in token:
                self.spare.setdefault(token, []).append(key)
        gaps = []
        for token, group, name in reading.words.values():
            marks = sorted(group, key=lambda i: reading.box[i][0])
            gaps += [reading.box[b][0] - reading.box[a][2] for a, b in zip(marks, marks[1:]) if reading.size[a] > 12 and reading.size[b] > 12]
        self.gap = max(float(np.median(gaps)), 2.0)

    @staticmethod
    def glyph(ink, box, foot):
        """A mark ready to set down: its ink, where its top is against its foot, and where its body runs."""
        x0, y0, x1, y1 = box
        ink = np.clip((ink - 0.07) / 0.93, 0, 1)  # the card is never quite bare of ink to the eye that reads it
        rows = np.arange(y0, y1)
        band = ink[(rows > foot - 10) & (rows < foot + 1.5)]
        cols = np.nonzero(band.max(axis=0) > 0.3)[0] if len(band) else []
        if len(cols) == 0:
            cols = np.nonzero(ink.max(axis=0) > 0.3)[0]
        top = np.nonzero(ink.max(axis=1) > 0.3)[0][0]
        return ink, y0 - foot, cols[0], cols[-1] + 1 - cols[0], foot - (y0 + top)

    def pen(self, wide, strokes, seed):
        """A letter drawn with the pen: lines through the given points, as ink, and the box they are in."""
        stray = np.random.default_rng(seed)
        pad, tall, deep = 4, 20, 5
        Y, X = np.mgrid[0 : (tall + deep) * 4, 0 : (wide + 2 * pad) * 4] / 4 + 0.125
        d = np.full(X.shape, 1e9)
        for points in strokes:
            pts = np.array(points, dtype=np.float64) + (pad, tall)
            pts += stray.normal(0, 0.35, pts.shape)  # no hand puts a point where it meant to
            for _ in range(2):  # round the corners off, as a hand does
                q, r = 0.8 * pts[:-1] + 0.2 * pts[1:], 0.2 * pts[:-1] + 0.8 * pts[1:]
                pts = np.concatenate(([pts[0]], np.column_stack((q, r)).reshape(-1, 2), [pts[-1]]))
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                t = np.clip(((X - ax) * (bx - ax) + (Y - ay) * (by - ay)) / max((bx - ax) ** 2 + (by - ay) ** 2, 1e-9), 0, 1)
                d = np.minimum(d, np.hypot(X - ax - t * (bx - ax), Y - ay - t * (by - ay)))
        ink = np.clip((PEN / 2 - d) / 0.9 + 0.5, 0, 1) * 0.93
        ink = blurred(ink, 2.2).reshape(tall + deep, 4, wide + 2 * pad, 4).mean(axis=(1, 3))
        return ink, (0, -tall, wide + 2 * pad, deep)

    def lay(self, mark, x, foot, size=1.0, turn=0.0):
        """Set a mark down with its body's left edge at x and its foot at `foot`, in reference pixels."""
        ink, top, left, _, _ = mark
        h, w = ink.shape
        zoom = UP * size
        side = int(np.ceil(np.hypot(h, w) * zoom)) + 6
        cos, sin = np.cos(turn), np.sin(turn)
        inverse = np.array([[cos, -sin], [sin, cos]]) / zoom
        middle = np.array([h / 2, w / 2])
        out = ndimage.affine_transform(ink, inverse, offset=middle - inverse @ np.array([side / 2, side / 2]), output_shape=(side, side), order=3, mode="constant")
        if size < 0.95:  # the pen is no finer for writing small
            out = blurred(ndimage.grey_dilation(out, size=(2, 2)), 0.6)
        out = np.clip(out, 0, 1)
        # Where the foot of the body's left edge went.
        ay, ax = (np.array([-top, left]) - middle) * zoom
        ay, ax = side / 2 + sin * ax + cos * ay, side / 2 + cos * ax - sin * ay
        row, col = round(foot * UP - ay), round(x * UP - ax)
        r0, c0 = max(row, 0), max(col, 0)
        r1, c1 = min(row + side, self.wet.shape[0]), min(col + side, self.wet.shape[1])
        self.wet[r0:r1, c0:c1] = np.maximum(self.wet[r0:r1, c0:c1], out[r0 - row : r1 - row, c0 - col : c1 - col])

    def stroke(self, points, round_off=2, stray=0.45, width=PEN * 0.8):
        """One line of the pen through some points, in reference pixels."""
        pts = (np.array(points, dtype=np.float64) - self.grown[1]) * self.grown[0] + self.grown[1] + self.shift
        # A long line is not drawn in one go: it wanders a little all the way along.
        steps = [max(int(np.hypot(*(b - a)) / 9), 1) for a, b in zip(pts, pts[1:])]
        pts = np.concatenate([a + (b - a) * np.arange(n)[:, None] / n for (a, b), n in zip(zip(pts, pts[1:]), steps)] + [pts[-1:]])
        pts += self.rng.normal(0, stray, pts.shape)  # no hand puts a point where it meant to
        for _ in range(round_off):  # round the corners off, as a hand does
            q, r = 0.75 * pts[:-1] + 0.25 * pts[1:], 0.25 * pts[:-1] + 0.75 * pts[1:]
            pts = np.concatenate(([pts[0]], np.column_stack((q, r)).reshape(-1, 2), [pts[-1]]))
        # The pen bears down more in some places than others, and comes off the paper lightly.
        press = blurred(self.rng.normal(0, 1, len(pts) + 8), 3)[4:-4]
        press = 0.9 + 0.5 * press / max(press.std(), 1e-6) * 0.3
        press[0] = press[-1] = 0.72
        dark = self.rng.uniform(0.8, 0.97)
        reach = width + 3
        x0, y0 = np.maximum(np.floor(pts.min(axis=0) - reach).astype(int), 0)
        x1, y1 = np.ceil(pts.max(axis=0) + reach).astype(int)
        Y, X = np.mgrid[y0:y1, x0:x1] + 0.5
        ink = np.zeros(X.shape)
        for (ax, ay), (bx, by), bear in zip(pts, pts[1:], np.clip(press, 0.6, 1.25)):
            t = np.clip(((X - ax) * (bx - ax) + (Y - ay) * (by - ay)) / max((bx - ax) ** 2 + (by - ay) ** 2, 1e-9), 0, 1)
            d = np.hypot(X - ax - t * (bx - ax), Y - ay - t * (by - ay))
            ink = np.maximum(ink, np.clip((width / 2 * bear - d) / 0.9 + 0.5, 0, 1) * dark * min(bear + 0.12, 1))
        rows, cols = self.drawn.shape
        self.drawn[y0:y1, x0:x1] = np.maximum(self.drawn[y0:y1, x0:x1], ink[: rows - y0, : cols - x0])

    def strokes(self, *lines, **how):
        for line in lines:
            self.stroke(line, **how)

    def sketch(self, *lines, **how):
        """Lines gone over twice, as the outline of a thing is."""
        for line in lines:
            self.stroke(line, **how)
            self.stroke(line, **{**how, "stray": 1.5 * how.get("stray", 0.45), "width": PEN * 0.6})

    def blank(self, points):
        """Take the ink off a patch, so what is drawn next stands in front of what was there."""
        patch = Image.new("L", self.drawn.shape[::-1], 0)
        ImageDraw.Draw(patch).polygon([tuple(p) for p in (np.array(points, dtype=np.float64) - self.grown[1]) * self.grown[0] + self.grown[1] + self.shift], fill=1)
        self.drawn[np.asarray(patch) > 0] = 0

    def loop(self, cx, cy, rx, ry, square=1.0, n=18):
        """Points round an oval, or a box with its corners eased when `square` is small, ending past its start."""
        t = np.linspace(0, 2 * np.pi * 1.04, n) + self.rng.uniform(0, 6)
        c, s = np.cos(t), np.sin(t)
        return np.column_stack((cx + rx * np.sign(c) * np.abs(c) ** square, cy + ry * np.sign(s) * np.abs(s) ** square))

    def oval(self, cx, cy, rx, ry, **how):
        self.stroke(self.loop(cx, cy, rx, ry), **{"stray": min(0.45, 0.12 * min(rx, ry)), **how})

    def box(self, x0, y0, x1, y1):
        """A box drawn a side at a time, each running a little past its corner."""
        over = lambda: self.rng.uniform(-0.5, 2.0)
        self.stroke([(x0 - over(), y0), (x1 + over(), y0)], round_off=1)
        self.stroke([(x1, y0 - over()), (x1, y1 + over())], round_off=1)
        self.stroke([(x1 + over(), y1), (x0 - over(), y1)], round_off=1)
        self.stroke([(x0, y1 + over()), (x0, y0 - over())], round_off=1)

    def hatch(self, x0, y0, x1, y1, count, lean=0.35):
        """Shading: quick slanted lines across a patch."""
        for k in range(count):
            x = x0 + (x1 - x0) * (k + 0.5) / count
            top = y0 + self.rng.uniform(0, 0.2) * (y1 - y0)
            self.stroke([(x + lean * (y1 - y0) / 2, top), (x - lean * (y1 - y0) / 2, y1 - self.rng.uniform(0, 0.15) * (y1 - y0))], round_off=0, stray=0.5, width=PEN * 0.6)

    def dot(self, x, y):
        self.stroke([(x - 0.4, y - 0.3), (x + 0.5, y + 0.4)], stray=0.1, width=PEN * 1.1)

    def bubble(self, x0, y0, x1, y1, tip):
        """A speech bubble, in front of whatever it lies over, open where its tail leaves it for the one speaking."""
        round_ = self.loop((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, 0.62, 30)[:-2]
        round_ = np.roll(round_, -int(np.argmin(np.hypot(*(round_ - tip).T))), axis=0)
        self.blank(np.concatenate((round_[1:], [tip])))
        self.stroke(round_[1:], round_off=2)
        self.stroke([round_[-1], tip, round_[1]], round_off=0, stray=0.3)

    def hair(self, cx, cy, rx, ry, lean=0.5):
        """Hair, the way the reference does it: the pen run back and forth until the paper is nearly covered."""
        for way in (lean, -0.6 * lean):
            count = int(2 * rx / (1.2 if way == lean else 2.4))
            for k in range(count):
                u = -1 + 2 * (k + 0.5) / count + self.rng.normal(0, 0.03)
                reach = np.sqrt(max(1 - u * u, 0.04)) * ry * self.rng.uniform(0.8, 1.25)
                x = cx + u * rx
                self.stroke([(x + way * reach, cy - reach), (x + self.rng.normal(0, 0.8), cy), (x - way * reach, cy + reach)], round_off=1, stray=0.7, width=PEN * 0.75)
        for _ in range(int(rx)):  # and the ends that stand out of it
            turn = self.rng.uniform(0, 2 * np.pi)
            edge = np.array([cx + rx * np.cos(turn), cy + ry * np.sin(turn)])
            out = np.array([np.cos(turn), np.sin(turn)]) * self.rng.uniform(1.5, 4.5)
            self.stroke([edge - out, edge + 0.3 * out + self.rng.normal(0, 1, 2), edge + out], round_off=1, stray=0.4, width=PEN * 0.6)

    def arrow(self, *points):
        """A line with a head on its far end."""
        self.stroke(points, stray=0.3)
        (ax, ay), (bx, by) = np.array(points[-2]), np.array(points[-1])
        along = np.array([bx - ax, by - ay]) / max(np.hypot(bx - ax, by - ay), 1e-6)
        across = np.array([-along[1], along[0]])
        for side in (1, -1):
            self.stroke([(bx, by), tuple(np.array([bx, by]) - 4.5 * along + side * 3 * across)], round_off=0, stray=0.2)

    def dry(self):
        """Let the drawings take on the paper: its grain breaks the line up a little, and the lens softens it."""
        grain = blurred(self.rng.standard_normal(self.drawn.shape), 0.8)
        ink = blurred(self.drawn, 0.5) * np.clip(1 - 0.09 * grain / grain.std(), 0.7, 1.08)
        self.wet = np.maximum(self.wet, np.clip(ndimage.zoom(ink, UP, order=3), 0, 1))

    def say(self, x, y, slope, size, words):
        """Writing that belongs to a drawing, and moves with it."""
        x, y = (np.array([x, y]) - self.grown[1]) * self.grown[0] + self.grown[1] + self.shift
        self.write((x, y, slope), x, size, words)

    def pick(self, chars):
        """One of the reference's ways of writing these letters, a different one each time round."""
        if not self.queue.get(chars):
            order = self.rng.permutation(len(self.letters[chars]))
            self.queue[chars] = [self.letters[chars][i] for i in order]
        return self.queue[chars].pop()

    def spell(self, word, x, base, size, turn):
        """Write a word letter by letter from x. Returns where it ends."""
        marks = word.split("+") if "'+" in word or len(word) == 2 and word[1] == "'" else None
        at = 0
        while at < (len(marks) if marks else len(word)):
            if marks:
                chars = marks[at]
                at += 1
            else:
                # Letters the hand ran together in one stroke are kept together when it wrote them so.
                joined = [word[at : at + n] for n in (3, 2) if word[at : at + n] in self.letters and word[at : at + n] not in UNREADABLE]
                chars = joined[0] if joined and self.rng.random() < 0.55 else word[at]
                at += len(chars)
            mark = self.pick(chars)
            if chars[0].isupper() and len(chars) == 1 and mark[4] < CAP - 2.5 and any(m[4] >= CAP - 2.5 for m in self.letters[chars]):
                mark = next(m for m in self.letters[chars] if m[4] >= CAP - 2.5)
            scale = size * self.rng.normal(1, 0.025)
            if chars[0].isupper() and len(chars) == 1 and mark[4] < CAP - 2:
                scale *= CAP / mark[4]
            if chars in ".,":
                x -= 0.8 * size
            wide = mark[3] * scale
            self.lay(mark, x, base(x + wide / 2) + self.rng.normal(0, 0.3), scale, turn + self.rng.normal(0, 0.02))
            x += wide + (self.gap + self.rng.normal(0, 0.5)) * size
        return x - self.gap * size

    def write(self, line, start, size, words):
        reading = self.reading
        if isinstance(line, str):
            base, turn = (lambda x: reading.baseline(line, x)), 0.0
        else:
            x0, y0, slope = line
            base, turn = (lambda x: y0 + slope * (x - x0)), float(np.arctan(slope))
        x, first = start, True
        for word in words.split():
            close = word.startswith("+")
            word = word.lstrip("+")
            if word.startswith("="):
                keys = [k for k in reading.words if k == word[1:] or k.startswith(word[1:] + ".")]
                self.kept.update(keys)
                x, first = max(reading.box[i][2] for k in keys for i in reading.words[k][1]), False
                continue
            if not first:
                x += 2.0 * size if close else (SPACE + self.rng.normal(0, 1.2)) * size
            first = False
            if word.startswith("#"):
                (bx0, by0, bx1, by1), foot = SAID[word[1:]]
                group = [i for i, (cx, cy) in reading.mid.items() if bx0 <= cx < bx1 and by0 <= cy < by1 and reading.box[i][2] - reading.box[i][0] < 45]
                mark = self.glyph(*reading.lift(group), foot)
                self.lay(mark, x, base(x + mark[3] / 2), size)
                x += mark[3] * size
            else:
                whole = word.rstrip(".,!?")
                if size > 0.95 and not self.spare.get(word) and self.spare.get(whole):
                    word, rest = whole, word[len(whole) :]
                else:
                    rest = ""
                if size > 0.95 and self.spare.get(word):
                    _, group, name = reading.words[self.spare[word].pop(0)]
                    ink, box = reading.lift(group)
                    mark = self.glyph(ink, box, reading.baseline(name, (box[0] + box[2]) / 2))
                    self.lay(mark, x, base(x + mark[3] / 2), size)
                    x += mark[3] * size
                    if rest:
                        x = self.spell(rest, x + 2.0, base, size, turn)
                else:
                    x = self.spell(word, x, base, size, turn)
        return x


def rubbed(ref, reading, gone):
    """The reference with some of its marks taken off: bare card where they were, with the card's grain."""
    clear = (reading.away > 3.5).astype(np.float64)
    field = blurred(ref * clear[..., None], 5) / np.maximum(blurred(clear, 5), 1e-4)[..., None]
    x0, y0, x1, y1 = PAGE
    patch = ref[y0:y1, x0:x1]
    grain = patch - blurred(patch, 4)
    grain = np.concatenate((grain, grain[::-1]), axis=0)
    grain = np.concatenate((grain, grain[:, ::-1]), axis=1)
    rows, cols = ref.shape[:2]
    tiled = np.tile(grain, (rows // grain.shape[0] + 1, cols // grain.shape[1] + 1, 1))[:rows, :cols]
    cover = blurred((np.isin(reading.owner, list(gone)) & (reading.away < 3.2)).astype(np.float64), 0.7)
    cover = np.clip(cover * 1.6, 0, 1)[..., None]
    return ref * (1 - cover) + (field + tiled) * cover


def drawings(pen):
    """The drawings, in reference pixels, and what is said in them."""
    # An amplifier with the guitar leaning on it, its lead on the floor, and a note of how it is played.
    pen.shift[:] = 0, 8
    pen.sketch([(628, 326), (692, 326), (692, 380), (628, 380), (628, 326)], round_off=1)
    pen.strokes([(628, 326), (639, 315), (703, 315), (692, 326)], [(703, 315), (703, 369), (692, 380)], [(629, 336), (691, 336)], [(660, 317), (662, 311), (682, 311), (684, 317)], round_off=1, stray=0.35)
    for x in (637, 646, 655, 664):
        pen.oval(x, 331, 1.8, 1.8)
    pen.strokes([(677, 329), (686, 329), (686, 333), (677, 333), (677, 329)], [(634, 341), (686, 341), (686, 375), (634, 375), (634, 341)], round_off=0, stray=0.3)
    pen.hatch(636, 343, 685, 373, 13, 0.6)
    pen.hatch(636, 343, 685, 373, 9, -0.6)
    pen.hatch(694, 324, 702, 372, 4, 0.1)
    pen.oval(660, 358, 11, 11, width=PEN * 0.6)
    pen.stroke([(616, 384), (640, 387), (662, 384), (690, 387), (716, 384)], stray=0.6, width=PEN * 0.6)
    pen.stroke([(630, 332), (618, 340), (611, 362), (622, 389), (660, 397), (708, 395), (738, 392), (756, 389), (764, 379)], round_off=3)
    pen.strokes([(622, 318), (614, 312), (618, 307), (608, 300)], [(650, 309), (647, 302), (652, 299), (649, 291)], [(712, 322), (721, 318), (718, 312), (728, 305)], [(716, 338), (724, 337), (722, 331), (731, 329)], round_off=0, stray=0.5)
    pen.oval(600, 338, 3, 2.3)
    pen.dot(600, 338)
    pen.strokes([(603, 337), (603, 322)], [(603, 322), (609, 326)], stray=0.2)
    # A PRS Silver Sky: the longer bass-side horn, three single coils with the bridge one slanted, birds up
    # the neck, six tuners in a line and the scoop cut out of the headstock's tip.
    lean = np.deg2rad(12)

    def sky(*points):
        x, y = np.array(points, dtype=np.float64).T * 0.95
        return np.column_stack((750 + x * np.cos(lean) - y * np.sin(lean), 352 + x * np.sin(lean) + y * np.cos(lean)))

    body = [(-5, -24), (-9, -33), (-15, -38), (-19, -33), (-18, -24), (-21, -14), (-19, -6), (-22, 4), (-24, 16), (-20, 27), (-10, 33), (0, 34), (11, 32), (20, 26), (24, 15), (22, 4), (18, -5), (19, -13), (17, -22), (15, -30), (10, -27), (7, -21), (5, -24)]
    head = [(-4, -78), (-7, -82), (-8, -104), (-5, -110), (-1, -106), (3, -109), (6, -104), (7, -92), (5, -84), (4, -78)]
    pen.blank(sky(*body))
    pen.sketch(sky(*body, body[0]), stray=0.35)
    pen.blank(sky((-5, -24), (-4, -78), *head[1:-1], (4, -78), (5, -24)))
    pen.strokes(sky((-5, -24), (-4, -78)), sky((5, -24), (4, -78)), sky(*head), sky((-4, -78), (4, -78)), stray=0.25)
    pen.stroke(sky((-3, -22), (-12, -20), (-15, -10), (-13, 0), (-8, 10), (2, 18), (12, 20), (17, 12), (14, -2), (10, -14), (6, -22)), stray=0.3, width=PEN * 0.6)
    for y, slant in ((-12, 0), (-2, 0), (8, 2)):
        pen.strokes(sky((-7, y + slant - 1.5), (7, y - slant - 1.5)), sky((-7, y + slant + 1.5), (7, y - slant + 1.5)), sky((-7, y + slant - 1.5), (-7, y + slant + 1.5)), sky((7, y - slant - 1.5), (7, y - slant + 1.5)), round_off=0, stray=0.15, width=PEN * 0.6)
    pen.strokes(sky((-7, 15), (7, 15), (7, 20), (-7, 20), (-7, 15)), sky((14, 0), (17, 4)), round_off=0, stray=0.2)
    for y in (-27, -39, -51, -63, -75):
        pen.stroke(sky((-4.5, y), (4.5, y)), round_off=0, stray=0.15, width=PEN * 0.4)
    for y in (-33, -45, -57, -69):  # the birds
        pen.stroke(sky((-3.2, y - 1.6), (-1.2, y - 1.8), (0, y + 1.6), (1.4, y - 1.4), (3.4, y - 2.2)), round_off=1, stray=0.1, width=PEN * 0.55)
    for y in range(-84, -108, -4):
        pen.stroke(sky((-8, y), (-12, y)), round_off=0, stray=0.15, width=PEN * 0.6)
        pen.dot(*sky((-12.5, y))[0])
    for spot in ((11, 10), (13, 17), (9, 23), (16, 25)):
        pen.dot(*sky(spot)[0])
    pen.hatch(732, 372, 750, 382, 4)
    pen.say(652, 271, -0.03, 0.75, "silver sky")
    pen.arrow((726, 275), (740, 279), (753, 287))
    pen.say(440, 376, 0.0, 0.8, "loud, preferably")
    pen.arrow((588, 371), (598, 366), (606, 360))

    # Shaving, in three frames: a lathered face that will not be hurried, the kit on its shelf, a younger onlooker.
    pen.shift[:] = 0, 36
    pen.box(160, 452, 336, 568)
    pen.box(346, 452, 626, 568)
    pen.sketch(pen.loop(222, 508, 25, 29), stray=0.5)
    pen.strokes([(197, 505), (193, 509), (197, 516)], [(247, 505), (251, 509), (247, 516)], [(198, 488), (196, 500)], [(246, 488), (248, 500)], [(207, 497), (216, 495)], [(228, 495), (237, 497)], [(208, 503), (212, 505), (216, 503)], [(228, 503), (232, 505), (236, 503)], [(221, 503), (224, 512), (219, 514)], stray=0.2)
    pen.hair(222, 483, 27, 13)
    pen.blank([(199, 516), (196, 524), (201, 537), (212, 546), (227, 548), (239, 541), (246, 528), (245, 516)])
    pen.sketch([(199, 516), (196, 524), (201, 529), (201, 537), (208, 539), (212, 546), (220, 544), (227, 548), (232, 542), (239, 541), (240, 533), (246, 528), (245, 516)], round_off=1)
    pen.strokes([(199, 516), (206, 521), (213, 517), (221, 521), (229, 517), (237, 521), (245, 516)], [(217, 529), (226, 529)], [(238, 520), (241, 534)], [(243, 519), (245, 531)], round_off=1, stray=0.3)
    for x, y in ((205, 531), (230, 536), (212, 538)):
        pen.dot(x, y)
    pen.strokes([(212, 547), (211, 556)], [(232, 547), (234, 556)], [(211, 556), (192, 560), (178, 568)], [(234, 556), (254, 560), (268, 568)], [(240, 557), (262, 566)], stray=0.3)
    pen.hatch(186, 560, 214, 567, 5)
    pen.hatch(246, 560, 262, 567, 4, -0.4)
    # The razor's head lies flat on the cheek and its handle stands out from it to the hand.
    pen.blank([(246, 508), (256, 508), (284, 518), (290, 568), (258, 568), (258, 532), (246, 530)])
    pen.strokes([(247, 511), (249, 528)], [(251, 510), (253, 527)], [(247, 511), (251, 510)], [(249, 528), (253, 527)], [(252, 517), (267, 522)], [(252, 520.5), (266, 525.5)], stray=0.15)
    pen.oval(274, 527, 8.5, 7.5)
    pen.strokes([(270, 522), (271, 532)], [(274, 521), (275, 533)], [(278, 522), (278, 532)], stray=0.15, width=PEN * 0.5)
    pen.strokes([(267, 533), (263, 568)], [(281, 533), (285, 568)], stray=0.25)
    pen.strokes([(243, 532), (242, 538)], [(239, 534), (238, 539)], stray=0.15, width=PEN * 0.5)
    pen.strokes([(164, 470), (172, 462)], [(164, 482), (180, 462)], [(316, 566), (334, 548)], [(324, 566), (334, 556)], stray=0.3, width=PEN * 0.5)
    pen.bubble(268, 452, 382, 509, (251, 499))
    pen.say(284, 470, -0.03, 0.75, "Stretch and")
    pen.say(283, 485, -0.03, 0.75, "go with the")
    pen.say(304, 500, -0.03, 0.75, "grain")
    pen.sketch([(356, 548), (486, 549), (616, 547)], stray=0.3)
    pen.strokes([(380, 549), (380, 562), (392, 549)], [(590, 549), (590, 562), (578, 549)], stray=0.3)
    pen.hatch(360, 551, 612, 555, 22, 1.4)
    pen.oval(416, 545, 9, 3)
    pen.strokes([(414, 543), (414, 506)], [(419, 543), (419, 506)], [(404, 500), (430, 500), (432, 506), (402, 506), (404, 500)], [(406, 503), (428, 503)], round_off=0, stray=0.25)
    for y in (512, 518, 524, 530, 536):
        pen.stroke([(414, y), (419, y - 1)], round_off=0, stray=0.2, width=PEN * 0.5)
    pen.say(393, 489, -0.02, 0.75, "Merkur")
    pen.arrow((417, 492), (417, 497))
    pen.oval(491, 523, 29, 5)
    pen.oval(491, 518, 29, 5)
    pen.strokes([(462, 518), (462, 524), (464, 548)], [(520, 518), (520, 524), (518, 548)], [(465, 532), (517, 532)], [(466, 542), (516, 542)], [(474, 537), (480, 535), (486, 538), (492, 535), (498, 538), (506, 535)], stray=0.3)
    pen.hatch(508, 526, 518, 547, 3, 0.1)
    pen.say(463, 505, -0.02, 0.75, "Proraso")
    pen.strokes([(562, 512), (562, 548)], [(598, 512), (598, 548)], [(562, 512), (566, 504), (574, 500)], [(598, 512), (594, 504), (586, 500)], [(574, 500), (574, 492)], [(586, 500), (586, 492)], [(572, 483), (588, 483), (588, 492), (572, 492), (572, 483)], [(576, 484), (576, 491)], [(580, 484), (580, 491)], [(584, 484), (584, 491)], [(566, 520), (594, 520), (594, 540), (566, 540), (566, 520)], [(570, 527), (576, 525), (582, 528), (590, 526)], [(570, 534), (578, 532), (586, 535)], [(563, 516), (597, 515)], round_off=0, stray=0.25)
    pen.hatch(590, 514, 597, 547, 3, 0.1)
    pen.say(548, 477, -0.02, 0.75, "Clubman")
    pen.sketch(pen.loop(700, 528, 16, 17), stray=0.4)
    pen.hair(700, 512, 17, 7)
    pen.strokes([(684, 526), (681, 529), (684, 534)], [(716, 526), (719, 529), (716, 534)], [(691, 523), (697, 524)], [(703, 524), (709, 523)], [(695, 537), (700, 536), (705, 537)], [(700, 529), (701, 533)], [(693, 545), (692, 550)], [(707, 545), (708, 550)], [(692, 550), (674, 555), (664, 568)], [(708, 550), (726, 555), (736, 568)], [(668, 563), (690, 557), (716, 561)], [(672, 567), (700, 563), (730, 565)], stray=0.25)
    pen.dot(694, 529)
    pen.dot(706, 529)
    pen.hatch(680, 552, 722, 558, 6)
    pen.bubble(652, 458, 752, 502, (706, 511))
    pen.say(682, 478, 0, 1, "#how")
    pen.say(666, 495, 0, 1, "#relaxing!")

    # Arsenal on the television, someone on their feet for it with a scarf held up, and the same onlooker.
    pen.shift[:] = 0, 78
    pen.stroke([(156, 724), (330, 725), (520, 724)], stray=0.3)
    pen.sketch([(176, 640), (260, 640), (260, 700), (176, 700), (176, 640)], round_off=1)
    pen.strokes([(183, 646), (240, 646), (240, 694), (183, 694), (183, 646)], [(166, 700), (270, 700), (270, 722), (166, 722), (166, 700)], [(218, 701), (218, 721)], [(214, 640), (198, 620)], [(222, 640), (242, 622)], [(266, 650), (274, 646)], [(268, 664), (277, 664)], [(266, 678), (274, 682)], round_off=1, stray=0.3)
    pen.strokes([(245, 650), (255, 650)], [(245, 655), (255, 655)], [(245, 660), (255, 660)], [(245, 665), (255, 665)], [(211, 647), (211, 693)], [(183, 660), (192, 660), (192, 680), (183, 680)], [(240, 660), (231, 660), (231, 680), (240, 680)], [(221, 664), (226, 667)], round_off=0, stray=0.2, width=PEN * 0.5)
    pen.oval(211, 670, 7, 7, width=PEN * 0.5)
    pen.oval(250, 678, 2.2, 2.2)
    pen.oval(250, 688, 2.2, 2.2)
    for x, y in ((198, 620), (242, 622), (200, 664), (204, 678), (222, 658), (229, 669), (224, 684), (210, 711), (226, 711)):
        pen.dot(x, y)
    pen.hatch(168, 702, 216, 720, 8)
    pen.strokes([(288, 668), (290, 654), (300, 650), (384, 650), (394, 654), (396, 668)], [(284, 672), (284, 716), (400, 716), (400, 672)], [(284, 672), (296, 672), (296, 692)], [(400, 672), (388, 672), (388, 692)], [(296, 692), (388, 692)], [(342, 652), (342, 690)], stray=0.4)
    pen.hatch(298, 696, 386, 714, 13)
    pen.blank([(324, 658), (310, 628), (296, 628), (296, 612), (384, 610), (384, 628), (370, 628), (356, 658), (358, 726), (322, 726)])
    pen.blank(pen.loop(340, 644, 13, 14))
    pen.sketch(pen.loop(340, 644, 12, 13), stray=0.4)
    pen.hair(340, 632, 13, 5)
    pen.strokes([(333, 640), (337, 638)], [(343, 638), (347, 640)], [(336, 657), (336, 661)], [(344, 657), (344, 661)], [(328, 661), (325, 700), (355, 700), (352, 661)], [(328, 661), (340, 665), (352, 661)], [(329, 662), (318, 648), (312, 630)], [(335, 659), (325, 646), (319, 629)], [(351, 662), (362, 648), (368, 630)], [(345, 659), (355, 646), (361, 629)], [(331, 700), (330, 723), (324, 724)], [(338, 700), (338, 722)], [(343, 700), (343, 722)], [(350, 700), (351, 723), (357, 724)], stray=0.25)
    pen.dot(335, 644)
    pen.dot(345, 644)
    pen.oval(340, 651, 3.2, 2.8)
    pen.dot(340, 651)
    pen.hatch(330, 666, 351, 698, 8)
    pen.strokes([(298, 618), (382, 616)], [(298, 627), (382, 625)], [(298, 618), (298, 627)], [(382, 616), (382, 625)], stray=0.3)
    for x in range(304, 380, 9):
        pen.hatch(x, 618, x + 4, 626, 2, 0.2)
    for y in (619, 622, 625):
        pen.strokes([(298, y), (292, y + 1)], [(382, y - 1), (388, y)], stray=0.3, width=PEN * 0.5)
    pen.blank(pen.loop(315, 623, 5, 6))
    pen.blank(pen.loop(365, 622, 5, 6))
    pen.oval(315, 623, 4.5, 5.5)
    pen.oval(365, 622, 4.5, 5.5)
    pen.bubble(398, 630, 474, 664, (354, 652))
    pen.say(417, 654, -0.03, 0.9, "Ozi")  # the l is drawn, tall enough to read as one
    pen.stroke([(452.5, 638.5), (451, 646), (449.6, 653.5)], stray=0.2, width=PEN * 0.95)
    pen.dot(420.5, 637.5)
    pen.dot(425.5, 637)
    pen.sketch(pen.loop(600, 686, 15, 16), stray=0.4)
    pen.hair(600, 671, 16, 6.5)
    pen.strokes([(585, 684), (582, 687), (585, 692)], [(615, 684), (618, 687), (615, 692)], [(590, 679), (596, 681)], [(603, 678), (609, 677)], [(600, 687), (601, 691)], [(594, 702), (593, 707)], [(606, 702), (607, 707)], [(593, 707), (576, 712), (568, 724)], [(607, 707), (624, 712), (632, 724)], stray=0.25)
    pen.dot(593, 686)
    pen.dot(604, 686)
    pen.oval(600, 696, 2.2, 2)
    pen.hatch(582, 711, 620, 722, 7)
    pen.bubble(556, 626, 634, 658, (602, 663))
    pen.say(571, 648, 0, 1, "#golly!")

    # Dilly asleep on the MacBook's keyboard, curled up with her tail over the front edge, having typed a line
    # of k's. She is a long-haired van: white, a ginger cap parted by a white blaze, a ginger patch on her left
    # lip, two ginger spots on the right of her back, and a solid ginger tail.
    pen.shift[:] = 0, 0
    fine = {"round_off": 0, "stray": 0.2, "width": PEN * 0.55}

    def front(points, closed=True, **how):
        pen.blank(points)
        pen.sketch([*points, points[0]] if closed else points, **{"stray": 0.3, "round_off": 1, **how})

    def ginger(cx, cy, rx, ry, step=2.0, below=None, blaze=None):
        """Ginger fur: short hatching filling an oval, down to `below`, clear of a blaze between two x's."""
        x = cx - rx + step / 2
        while x < cx + rx:
            if not (blaze and blaze[0] < x < blaze[1]):
                reach = ry * np.sqrt(max(1 - ((x - cx) / rx) ** 2, 0))
                top, foot = cy - reach + 1.2, min(cy + reach - 1.2, below or 1e9)
                if foot - top > 1.5:
                    pen.stroke([(x + 0.25 * (foot - top) / 2, top), (x - 0.25 * (foot - top) / 2, foot)], round_off=0, stray=0.35, width=PEN * 0.5)
            x += step

    def fluff(cx, cy, rx, ry, n=40, tuft=1.6):
        """An oval with a long coat's tufts round its edge."""
        t = np.linspace(0, 2 * np.pi, n, endpoint=False) + pen.rng.uniform(0, 1)
        r = 1 + np.where(np.arange(n) % 2, tuft / max(rx, ry), -0.2 * tuft / max(rx, ry))
        return [(cx + rx * k * np.cos(a), cy + ry * k * np.sin(a)) for a, k in zip(t, r)]

    # The lid, standing behind: bezel, notch, an editor's lines, and what she typed.
    pen.sketch([(628, 818), (812, 814), (816, 908), (624, 911), (628, 818)], stray=0.35)
    pen.stroke([(634, 823), (806, 820), (809, 903), (631, 906), (634, 823)], stray=0.3, width=PEN * 0.6)
    pen.stroke([(713, 821), (714, 825), (728, 825), (729, 821)], round_off=0, stray=0.15, width=PEN * 0.6)
    for y, x0, x1 in ((832, 642, 690), (838, 650, 718), (844, 650, 700), (850, 658, 742), (856, 650, 690), (862, 642, 664)):
        pen.stroke([(x0, y), (x1, y - 0.3)], round_off=0, stray=0.25, width=PEN * 0.55)
    pen.say(642, 875, -0.004, 0.55, "kkkkkkkkkkkkkkkkkkkkkkk")
    pen.strokes([(784, 866), (784, 876)], stray=0.1, width=PEN * 0.6)
    # The deck coming forward: the keyboard's well and its rows of keys, the trackpad, the front edge.
    deck = [(624, 911), (816, 908), (836, 953), (604, 958)]
    front(deck)
    pen.strokes([(604, 958), (606, 963), (834, 958), (836, 953)], [(708, 958), (710, 961), (730, 961), (732, 957)], round_off=0, stray=0.25)

    def across(y, u):
        """A point of the deck, from its back edge (y = 0) to its front (y = 1), and left (u = 0) to right."""
        left = np.array([624, 911]) + (np.array([604, 958]) - np.array([624, 911])) * y
        right = np.array([816, 908]) + (np.array([836, 953]) - np.array([816, 908])) * y
        return tuple(left + (right - left) * u)

    rows = np.linspace(0.08, 0.52, 6)
    pen.stroke([across(rows[0], 0.06), across(rows[0], 0.94), across(rows[-1], 0.94), across(rows[-1], 0.06), across(rows[0], 0.06)], round_off=0, stray=0.25, width=PEN * 0.6)
    for a, b in zip(rows, rows[1:]):
        pen.stroke([across(b, 0.06), across(b, 0.94)], round_off=0, stray=0.2, width=PEN * 0.45)
        for k in range(1, 14):
            u = 0.06 + 0.88 * k / 14 + (0.02 if a > 0.3 else 0)
            pen.stroke([across(a + 0.01, u), across(b - 0.01, u)], round_off=0, stray=0.15, width=PEN * 0.45)
    pen.stroke([across(0.6, 0.38), across(0.6, 0.62), across(0.9, 0.62), across(0.9, 0.38), across(0.6, 0.38)], round_off=0, stray=0.25, width=PEN * 0.6)
    # Dilly: her body curled on the keys, her head down on her paws at the left.
    front(fluff(732, 904, 50, 26))
    ginger(724, 889, 13, 7, 1.3)
    ginger(748, 889, 6.5, 4.5, 1.3)
    pen.strokes([(700, 920), (712, 926)], [(742, 926), (756, 921)], [(760, 896), (768, 902)], **fine)
    front(fluff(676, 928, 8, 4, 16, 0.8))
    front(fluff(695, 929, 8, 4, 16, 0.8))
    pen.strokes([(672, 929), (673, 931)], [(677, 929), (677, 931.5)], [(691, 930), (692, 932)], [(696, 930), (696, 932.5)], **fine)
    front([(668, 897), (669, 881), (680, 891)], round_off=0)
    front([(689, 890), (697, 880), (700, 896)], round_off=0)
    pen.blank(fluff(684, 908, 18.5, 17, 30, 1.2))
    head = fluff(684, 908, 18, 16.5, 30, 1.2)
    pen.sketch([*head, head[0]], stray=0.3, round_off=1)
    ginger(684, 908, 17, 15.5, 1.3, below=903, blaze=(681.8, 686.4))
    pen.strokes([(669.5, 885), (670, 893)], [(671.5, 886), (673, 892)], [(674, 888), (677, 892)], [(696.5, 883), (695, 893)], [(698, 886), (697, 894)], [(694, 886), (692, 892)], **fine)
    pen.strokes([(673, 906.5), (677, 909.5), (681, 906.5)], [(687, 906.5), (691, 909.5), (695, 906.5)], round_off=1, stray=0.12, width=PEN * 0.7)
    pen.strokes([(682.4, 913), (685.6, 913), (684, 915.2), (682.4, 913)], [(684, 915.2), (684, 916.6)], [(684, 916.6), (681.5, 918.2)], [(684, 916.6), (686.5, 918.2)], **fine)
    ginger(691, 916.5, 3.6, 2.4, 1.1)
    pen.strokes([(679, 915), (664, 912)], [(679, 917), (663, 918)], [(689, 915), (705, 911)], [(689, 917), (706, 917)], round_off=0, stray=0.3, width=PEN * 0.45)
    # Her tail, solid ginger and bushy, from the back of her over the front edge.
    path = np.array([(776, 914), (790, 924), (800, 938), (805, 954), (803, 968), (796, 976)], dtype=np.float64)
    normal = np.gradient(path, axis=0)[:, ::-1] * (1, -1)
    normal /= np.linalg.norm(normal, axis=1)[:, None]
    wide = np.array([6.5, 7, 7, 6.5, 6, 4.5])
    tail = [tuple(p) for p in path + normal * wide[:, None]] + [tuple(p) for p in (path - normal * wide[:, None])[::-1]]
    front(tail)
    for side in np.linspace(-0.75, 0.75, 7):  # filled lengthwise, so it reads solid and not ringed
        pen.stroke(path[:-1] + normal[:-1] * (wide[:-1, None] * side), round_off=2, stray=0.45, width=PEN * 0.5)
    for k in np.linspace(0.3, len(path) - 1.3, 12):
        i, f = int(k), k - int(k)
        at, along = path[i] * (1 - f) + path[i + 1] * f, path[i + 1] - path[i]
        out = normal[i] * wide[i] * (1 if k % 2 < 1 else -1)
        pen.stroke([tuple(at + out * 0.6), tuple(at + out * 1.15 + along * 0.25)], round_off=0, stray=0.3, width=PEN * 0.5)
    pen.strokes([(606, 878), (612, 878), (606, 884), (612, 884)], [(612, 862), (620, 862), (612, 870), (620, 870)], round_off=0, stray=0.25)

    # Me on the bench, seen from the side, pressing 225 lbs: the bar end-on with its two plates, and not trying.
    pen.shift[:] = 0, 209
    pen.grown = (1.15, np.array([150.0, 996.0]))
    pen.stroke([(148, 996), (240, 997), (336, 996)], stray=0.3)
    pen.hatch(156, 998, 330, 1002, 18, 1.6)
    pen.strokes([(212, 975), (211, 996)], [(217, 975), (217, 996)], [(204, 996), (224, 996)], [(284, 975), (284, 996)], [(289, 975), (290, 996)], [(277, 996), (297, 996)], stray=0.25)
    pen.box(196, 968, 304, 975)
    pen.hatch(200, 969, 300, 974, 14, 0.3)
    legs = [(213, 967), (192, 958), (184, 990), (186, 996), (160, 996), (164, 989), (172, 988), (180, 948), (188, 944), (215, 955)]
    pen.blank(legs)
    pen.sketch(legs, stray=0.3)
    pen.strokes([(186, 990), (165, 990)], [(196, 951), (192, 958)], [(170, 992), (170, 995)], [(176, 992), (176, 995)], stray=0.2, width=PEN * 0.55)
    pen.hatch(194, 950, 212, 964, 4)
    torso = [(215, 967), (215, 956), (232, 950), (252, 945), (270, 946), (277, 952), (278, 967)]
    pen.blank(torso)
    pen.sketch(torso, stray=0.3)
    pen.strokes([(228, 951), (227, 967)], [(268, 946), (272, 952), (277, 952)], stray=0.2)
    pen.hatch(234, 952, 264, 965, 7)
    pen.blank(pen.loop(290, 955, 12.5, 12.5))
    pen.sketch(pen.loop(290, 955, 12, 12), stray=0.3)
    pen.hair(298, 956, 5.5, 10, 0.3)
    pen.strokes([(283, 944.5), (280, 940.5), (286, 943.2)], [(283, 949), (287, 947.5)], [(280, 954.5), (283, 958), (286.5, 956)], [(290, 962), (293, 960)], round_off=0, stray=0.15, width=PEN * 0.6)
    pen.dot(285.5, 951.5)
    arms = [(259, 950), (255, 938), (258, 924), (268, 924), (272, 938), (269, 950)]
    pen.blank(arms)
    pen.sketch([(259, 950), (255, 938), (258, 924)], [(269, 950), (272, 938), (268, 924)], stray=0.25)
    pen.strokes([(258, 940), (261, 934), (259, 929)], stray=0.2, width=PEN * 0.55)
    pen.sketch(pen.loop(258, 904, 22, 22, n=26), stray=0.3)
    pen.blank(pen.loop(263, 903, 22.5, 22.5, n=26))
    pen.sketch(pen.loop(263, 903, 22, 22, n=26), stray=0.3)
    pen.oval(263, 903, 17.5, 17.5, width=PEN * 0.55)
    pen.oval(263, 903, 6, 6)
    pen.oval(263, 903, 2.2, 2.2)
    pen.dot(263, 903)
    pen.strokes([(250, 892), (254, 895)], [(247, 897), (251, 899)], [(272, 915), (276, 912)], [(268, 918), (271, 916)], stray=0.2, width=PEN * 0.55)
    pen.strokes([(236, 878), (231, 871)], [(263, 875), (263, 867)], [(290, 878), (295, 871)], round_off=0, stray=0.3)
    pen.say(152, 903, -0.02, 0.85, "225 lbs")
    pen.arrow((212, 896), (226, 897), (237, 899))
    pen.bubble(322, 904, 432, 946, (306, 948))
    pen.say(336, 922, -0.02, 0.85, "damn, light")
    pen.say(360, 937, -0.02, 0.85, "work")
    pen.grown = (1.0, np.zeros(2))
    pen.shift[:] = 0, 0
    pen.dry()


def strip(reading):
    """The ink of the folded strip: the page's drawings again, with its date and signature, in one column."""
    hand = Hand(reading, (TALL_PAGE * UP, reading.marks.shape[1] * UP))
    for run in WRITING[:4] + WRITING[-2:]:
        hand.write(*run)
    drawings(hand)
    ink = np.clip((hand.wet - FAINT) / (0.92 - FAINT), 0, 1)
    for x0, y0, x1, y1 in STRIP_CLEARED:
        ink[y0 * UP : y1 * UP, x0 * UP : x1 * UP] = 0
    tall = sum(max(y1 - y0 for _, y0, _, y1 in boxes) for _, boxes in STRIP) + STRIP_GAP * (len(STRIP) + 1) - STRIP_GAP // 2
    out = np.zeros((tall * UP, STRIP_WIDTH * UP))
    top = STRIP_GAP * 3 // 4
    for across, boxes in STRIP:
        foot = top + max(y1 - y0 for _, y0, _, y1 in boxes)
        left = round(across * (STRIP_WIDTH - sum(x1 - x0 for x0, _, x1, _ in boxes)))
        for x0, y0, x1, y1 in boxes:
            out[(foot - y1 + y0) * UP : foot * UP, left * UP : (left + x1 - x0) * UP] = ink[y0 * UP : y1 * UP, x0 * UP : x1 * UP]
            left += x1 - x0
        top = foot + STRIP_GAP
    return out


def band(reading):
    """The ink of the strip folded on a phone: the folded strip's drawings, date and signature, side by side in one row."""
    hand = Hand(reading, (TALL_PAGE * UP, reading.marks.shape[1] * UP))
    for run in WRITING[:4] + WRITING[-2:]:
        hand.write(*run)
    drawings(hand)
    ink = np.clip((hand.wet - FAINT) / (0.92 - FAINT), 0, 1)
    for x0, y0, x1, y1 in STRIP_CLEARED:
        ink[y0 * UP : y1 * UP, x0 * UP : x1 * UP] = 0
    pieces = [boxes for _, boxes in STRIP]
    tall = max(max(y1 - y0 for _, y0, _, y1 in boxes) for boxes in pieces)
    wide = sum(sum(x1 - x0 for x0, _, x1, _ in boxes) for boxes in pieces) + BAND_GAP * (len(pieces) - 1)
    out = np.zeros((tall * UP, wide * UP))
    left = 0
    for boxes in pieces:
        high = max(y1 - y0 for _, y0, _, y1 in boxes)
        foot = (tall + high) // 2
        for x0, y0, x1, y1 in boxes:
            out[(foot - y1 + y0) * UP : foot * UP, left * UP : (left + x1 - x0) * UP] = ink[y0 * UP : y1 * UP, x0 * UP : x1 * UP]
            left += x1 - x0
        left += BAND_GAP
    return out


def laid(ref, reading):
    """The card's grain on its own: how much lighter or darker than itself the bare card is at each point."""
    x0, y0, x1, y1 = SHEET
    lum = ref[y0:y1, x0:x1].mean(axis=-1)
    grain = lum / blurred(lum, 6)
    even = ndimage.median_filter(grain, 9)
    fleck = ndimage.binary_dilation(np.abs(grain - even) > 3.2 * grain.std(), iterations=2)
    grain[fleck] = even[fleck]  # a fleck would come round again in every tile
    grain = np.clip(0.96 + 1.9 * (grain - 1), 0, 1)
    grain = np.concatenate((grain, grain[::-1]), axis=0)
    return np.concatenate((grain, grain[:, ::-1]), axis=1)


def card(ref):
    """Where the card lies on the page it was photographed on: its edges, a little way in from each."""
    warm = blurred(ref[..., 0] - ref[..., 2], 1.5)  # the card is cream and the page behind it is grey
    on = warm > (np.percentile(warm, 10) + np.percentile(warm, 60)) / 2
    cols = np.nonzero(on.mean(axis=0) > 0.5)[0]
    rows = np.nonzero(on.mean(axis=1) > 0.5)[0]
    return cols[0] + 4, rows[0] + 4, cols[-1] - 3, rows[-1] - 4


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

    cell, per = 46, 30
    chars = sorted(reading.letters, key=lambda c: (len(c), c))
    sheet = Image.new("L", (per * cell + 30, len(chars) * cell), 255)
    draw = ImageDraw.Draw(sheet)
    for row, char in enumerate(chars):
        draw.text((4, row * cell + 14), char, fill=0)
        for col, (glyph, name, key) in enumerate(reading.letters[char][:per]):
            ink, (x0, y0, x1, y1) = reading.lift(glyph)
            tile = Image.fromarray(((1 - ink) * 255).astype(np.uint8))
            foot = reading.baseline(name, (x0 + x1) / 2)
            sheet.paste(tile, (30 + col * cell + 4, row * cell + 26 - round(foot - y0)))
            draw.text((30 + col * cell + 2, row * cell + 34), key, fill=120)
        draw.line((30, row * cell + 26, sheet.width, row * cell + 26), fill=200)
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.Resampling.LANCZOS).save(os.path.join(DEBUG, "letters.png"))
    print(" ".join(f"{char}:{len(found)}" for char, found in sorted(reading.letters.items(), key=lambda kv: (len(kv[0]), kv[0]))))


def main():
    ref = np.asarray(Image.open(os.path.join(HERE, "assets", "letter.jpg")).convert("RGB"), dtype=np.float64) / 255
    reading = Reading(ref)
    if DEBUG:
        sheets(ref, reading)
    rows, cols = TALL_PAGE * UP, ref.shape[1] * UP
    hand = Hand(reading, (rows, cols))
    for line, start, size, words in WRITING:
        end = hand.write(line, start, size, words)
        if DEBUG:
            print(f"{end:6.0f}  {words}")
    if DEBUG:
        print("gap", hand.gap)

    drawings(hand)

    # All of the reference's ink goes but the words left where they are.
    gone = set(reading.box) - {i for key in hand.kept for i in reading.words[key][1]}
    bare = np.clip(rubbed(ref, reading, gone), 0, 1)

    # What is left on the card, read as ink again, with the new writing over it.
    dry = np.clip((reading.card - bare.mean(axis=-1)) / (reading.card - 0.16), 0, 1)
    dry *= np.clip(3.2 - reading.away, 0, 1) * ~np.isin(reading.owner, list(gone))  # ink is only where a mark is
    x0, y0, x1, y1 = card(ref)
    dry[:y0], dry[y1:], dry[:, :x0], dry[:, x1:] = 0, 0, 0, 0
    dry = np.pad(dry, ((0, TALL_PAGE - dry.shape[0]), (0, 0)))
    dry = np.asarray(Image.fromarray(dry.astype(np.float32), mode="F").resize((cols, rows), Image.Resampling.LANCZOS), dtype=np.float64)
    wet = np.clip((np.maximum(dry, hand.wet) - FAINT) / (0.92 - FAINT), 0, 1)
    ys, xs = np.nonzero(wet > 0.3)
    edge = 4 * UP
    cut = (slice(ys.min() - edge, ys.max() + edge), slice(xs.min() - edge, xs.max() + edge))
    colour = ref[reading.ink > 0.93].mean(axis=0)
    out = np.dstack((np.broadcast_to(colour, (rows, cols, 3)), wet))[cut]
    target = os.path.join(ROOT, "public", "objects", "letter.avif")
    Image.fromarray((out * 255 + 0.5).astype(np.uint8), mode="RGBA").save(target, quality=84, subsampling="4:4:4", speed=2)
    print(f"letter {out.shape[1]}x{out.shape[0]} {os.path.getsize(target) / 1e3:.0f} kB")

    folded = strip(reading)
    folded = np.dstack((np.broadcast_to(colour, (*folded.shape, 3)), folded))
    target = os.path.join(ROOT, "public", "objects", "letter-strip.avif")
    Image.fromarray((folded * 255 + 0.5).astype(np.uint8), mode="RGBA").save(target, quality=84, subsampling="4:4:4", speed=2)
    print(f"strip {folded.shape[1]}x{folded.shape[0]} {os.path.getsize(target) / 1e3:.0f} kB")
    if DEBUG:
        shown = np.array([0.812, 0.808, 0.796]) * (1 - folded[..., 3:]) + folded[..., :3] * folded[..., 3:]
        Image.fromarray((shown * 255 + 0.5).astype(np.uint8)).save(os.path.join(DEBUG, "strip.png"))

    row = band(reading)
    row = np.dstack((np.broadcast_to(colour, (*row.shape, 3)), row))
    target = os.path.join(ROOT, "public", "objects", "letter-band.avif")
    Image.fromarray((row * 255 + 0.5).astype(np.uint8), mode="RGBA").save(target, quality=84, subsampling="4:4:4", speed=2)
    print(f"band {row.shape[1]}x{row.shape[0]} {os.path.getsize(target) / 1e3:.0f} kB")
    if DEBUG:
        shown = np.array([0.812, 0.808, 0.796]) * (1 - row[..., 3:]) + row[..., :3] * row[..., 3:]
        Image.fromarray((shown * 255 + 0.5).astype(np.uint8)).save(os.path.join(DEBUG, "band.png"))

    grain = laid(ref, reading)
    target = os.path.join(ROOT, "public", "photos", "laid.avif")
    Image.fromarray((grain * 255 + 0.5).astype(np.uint8)).save(target, quality=88, speed=2)
    print(f"laid {grain.shape[1]}x{grain.shape[0]} {os.path.getsize(target) / 1e3:.0f} kB")
    if DEBUG:
        on = np.array([0.812, 0.808, 0.796]) * np.tile(grain, (out.shape[0] // grain.shape[0] + 1, out.shape[1] // grain.shape[1] + 1))[: out.shape[0], : out.shape[1], None]
        shown = on * (1 - out[..., 3:]) + out[..., :3] * out[..., 3:]
        Image.fromarray((shown * 255 + 0.5).astype(np.uint8)).save(os.path.join(DEBUG, "out.png"))


main()
