# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""The letter: the reference letter itself, with most of its words changed.

    uv run studio/letter.py

Everything that is not changed is the reference's own pixels, so the card, the pen and the drawings are
the photograph's and not a likeness of them. Three things are done to it:

- The photograph is cut down to the card, so the card lies on whatever page it is put on.
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


# Letters the reading got wrong: every letter of these words, and these letters of those.
MISREAD = {"L1.6", "L7.0", "D0.1"}
MISREAD_LETTERS = {("a", "L3.2"), ("a", "L4.0"), ("a", "L5.7"), ("c", "L14.0"), ("E", "L12.6"), ("g", "L8.10"), ("o", "L13.10"), ("o", "L14.4"), ("o", "L14.8"), ("t", "L16.2"), ("t", "L5.9"), ("s", "L15.9"), ("s", "L5.7"), ("w", "L8.0")}
# Letters cut out of a word by hand, where the pen ran them into the next: the box, and the line it is on.
CUTS = {
    "C": ((630, 937, 648, 965), "L15"),
    "M": ((626, 1049, 649, 1074), "S1"),
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
    "T'": (12, [[(1.6, -10.6), (6.6, -10.9), (12.0, -11.2)], [(7.0, -11.0), (6.5, -5), (6.2, 0.2)]]),
    "C'": (10, [[(9.8, -9.2), (6.4, -11.2), (2.4, -9.9), (0.6, -5.6), (2.2, -1.4), (6.2, -0.2), (10.0, -2.0)]]),
}
UNREADABLE = ("in", "ur")  # letters run together so that, lifted out of their word, they read as another
PEN = 2.1  # width of the pen's line
CAP = 17.0  # how tall the hand writes a capital
# Writing rubbed out by where it is, not by the line it stands on: the date, and words in the drawings.
RUBBED = (
    (664, 106, 742, 131), (780, 104, 791, 131), (650, 128, 796, 147),
    (470, 316, 514, 337),
    (308, 612, 424, 634), (332, 634, 398, 650), (338, 650, 386, 664), (340, 664, 431, 682),
    (402, 606, 418, 614),
    (565, 582, 653, 602), (556, 602, 657, 622),
    (739, 578, 786, 600), (680, 597, 729, 616), (692, 612, 734, 628),
    (404, 1022, 456, 1041), (348, 1041, 470, 1060), (362, 1056, 484, 1074), (378, 1073, 421, 1088),
)
STAYS = ((337, 300, 351, 338),)  # and a mark that stays where a word around it goes: a bracket
# The letter as it is to read. Each run of writing: the line whose baseline it follows, or a point and
# a slope; where it starts, or None to go on from the word before; how big; and its words. A plain word
# is spelt out. = leaves a word of the reference where it is, or a whole line of them. @ lifts one and
# sets it down here. + sets a word close against the one before.
WRITING = (
    ((700, 126.5, 0), 698, 1, "O'+C'+T'"),
    ("D0", None, 1, "=D0.2"),
    ((781, 127.5, 0), 781, 1, "6'"),
    ((692, 142.5, 0), 694, 1, "T'+O'+O'"),
    ((740, 142.5, 0), 738, 1, "L'+A'+T'+E'"),
    ("L0", None, 1.1, "=L0.0 younger me,"),
    ("L1", None, 1, "=L1"),
    ("L2", None, 1, "=L2.0 =L2.1 =L2.2 =L2.3 backwards @L2.5 @L2.6 @L2.7 @L2.8"),
    ("L3", 155, 1, "years in between"),
    ("L3", None, 1, "=L3.3 =L3.4 =L3.5 =L3.6"),
    ("L4", None, 1, "=L4.0 you will find"),
    ("L4", 520, 1, "all @L4.5 it stupid @L4.8"),
    ("L5", None, 1, "=L5.0 =L5.1 =L5.2 yet +@L5.4 =L5.5 =L5.6 =L5.7 =L5.8 =L5.9"),
    ("L6", None, 1, "=L6.0 =L6.1 I play an electric guitar @L5.3 +, which is loud,"),
    ("L7", 152, 1, "preferably. I wet shave too. @L7.4 @L7.5 @L7.6"),
    ("L8", None, 1, "=L8.0 long @L8.2 take with @L4.3 Merkur razor, Proraso and"),
    ("L9", 152, 1, "Clubman aftershave. @L9.1 @L9.2 @L9.3 @L9.4 @L9.5 bore."),
    ("L10", None, 1, "=L10.0 =L10.1 make sense @L10.4"),
    ("L11", None, 1, "=L11.0 =L11.1 =L11.2 +, @L11.4 +@L11.5 @L11.6 @L11.7 @L11.8 @L11.9 Arsenal win"),
    ("L12", None, 1, "=L12.0 shout up @L6.6 Gunners @L12.4 @L12.5 @L12.6 @L12.7 @L7.2"),
    ("L13", 152, 1, "cats became chief supervisors... @L13.7 @L13.8 @L13.9 @L13.10 @L13.11"),
    ("L14", None, 1, "=L14"),
    ("L15", None, 1, "=L15.0 =L15.1 =L15.2 =L15.3 loud guitars @L15.7 slow mornings."),
    ("L16", None, 1, "=L16"),
    ("S0", None, 1, "=S0"),
    ("S1", 632, 1, "Anurag"),
    # The drawings.
    ((482, 328, 0.2), 482, 0.9, "age"),
    ((313, 631, -0.03), 313, 0.8, "full Arsenal"),
    ((336, 645.5, -0.02), 336, 0.8, "match."),
    ((341, 661, -0.02), 341, 0.8, "up the"),
    ((343, 677.5, -0.05), 343, 0.8, "Gunners!"),
    ((571, 597.5, -0.035), 571, 0.78, "lose sleep"),
    ((561, 612.5, -0.02), 561, 0.8, "over it."),
    ((743, 593, -0.03), 743, 0.8, "use"),
    ((686, 608.5, 0.03), 686, 0.8, "foam"),
    ((697, 625, 0.03), 697, 0.8, "soap"),
    ((407, 1038, -0.02), 407, 0.8, "this"),
    ((354, 1053.5, -0.03), 354, 0.8, "is who I"),
    ((368, 1069, -0.035), 368, 0.8, "grow up to"),
    ((398, 1083, -0.01), 398, 0.8, "be"),
)
SPACE = 16.0  # bare card between two words, and how much it varies
PAGE = (150, 58, 640, 104)  # bare card, to take paper grain from

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
        self.moved = set()
        self.letters = {}
        for chars, found in reading.letters.items():
            good = [(glyph, name) for glyph, name, key in found if key not in MISREAD and (chars, key) not in MISREAD_LETTERS]
            sized = [self.glyph(*reading.lift(glyph), reading.baseline(name, np.mean([reading.mid[i][0] for i in glyph]))) for glyph, name in good]
            if len(sized) > 3:  # one far from the rest in size is another letter
                wide, tall = np.median([g[3] for g in sized]), np.median([g[4] for g in sized])
                sized = [g for g in sized if abs(g[3] - wide) < 0.35 * wide + 2 and abs(g[4] - tall) < 3.5]
            if sized:
                self.letters[chars] = sized
        for chars, ((x0, y0, x1, y1), name) in CUTS.items():
            self.letters[chars] = [self.glyph(reading.ink[y0:y1, x0:x1] * (reading.away[y0:y1, x0:x1] < 2.6), (x0, y0, x1, y1), reading.baseline(name, (x0 + x1) / 2))]
        for chars, (wide, strokes) in DRAWN.items():
            self.letters[chars] = [self.glyph(*self.pen(wide, strokes, seed), 0.0) for seed in range(4)]
        self.queue = {}
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

    def lay(self, mark, x, foot, size=1.0, turn=0.0, heavy=1.0):
        """Set a mark down with its body's left edge at x and its foot at `foot`, in reference pixels."""
        ink, top, left, _, _ = mark
        h, w = ink.shape
        zoom = UP * size
        side = int(np.ceil(np.hypot(h, w) * zoom)) + 6
        cos, sin = np.cos(turn), np.sin(turn)
        inverse = np.array([[cos, -sin], [sin, cos]]) / zoom
        middle = np.array([h / 2, w / 2])
        out = ndimage.affine_transform(ink, inverse, offset=middle - inverse @ np.array([side / 2, side / 2]), output_shape=(side, side), order=3, mode="constant")
        out = np.clip(out * heavy, 0, 1)
        # Where the foot of the body's left edge went.
        ay, ax = (np.array([-top, left]) - middle) * zoom
        ay, ax = side / 2 + sin * ax + cos * ay, side / 2 + cos * ax - sin * ay
        row, col = round(foot * UP - ay), round(x * UP - ax)
        r0, c0 = max(row, 0), max(col, 0)
        r1, c1 = min(row + side, self.wet.shape[0]), min(col + side, self.wet.shape[1])
        self.wet[r0:r1, c0:c1] = np.maximum(self.wet[r0:r1, c0:c1], out[r0 - row : r1 - row, c0 - col : c1 - col])

    def pick(self, chars):
        """One of the reference's ways of writing these letters, a different one each time round."""
        if not self.queue.get(chars):
            order = self.rng.permutation(len(self.letters[chars]))
            self.queue[chars] = [self.letters[chars][i] for i in order]
        return self.queue[chars].pop()

    def spell(self, word, x, base, size, turn):
        """Write a word letter by letter from x. Returns where it ends."""
        marks = word.split("+") if "'" in word else None
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
            self.lay(mark, x, base(x + wide / 2) + self.rng.normal(0, 0.3), scale, turn + self.rng.normal(0, 0.02), 1.0 if size > 0.95 else 1.25)
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
            if word.startswith("@"):
                _, group, name = reading.words[word[1:]]
                self.moved.add(word[1:])
                ink, box = reading.lift(group)
                mark = self.glyph(ink, box, reading.baseline(name, (box[0] + box[2]) / 2))
                self.lay(mark, x, base(x + mark[3] / 2), size)
                x += mark[3] * size
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
    rows, cols = ref.shape[0] * UP, ref.shape[1] * UP
    hand = Hand(reading, (rows, cols))
    for line, start, size, words in WRITING:
        end = hand.write(line, start, size, words)
        if DEBUG:
            print(f"{end:6.0f}  {words}")
    if DEBUG:
        print("gap", hand.gap)

    # Every word of a line goes unless it was left where it is. So does the writing named by its place.
    gone = {i for key, (_, group, name) in reading.words.items() if key not in hand.kept for i in group}
    for i, (cx, cy) in reading.mid.items():
        if any(x0 <= cx < x1 and y0 <= cy < y1 for x0, y0, x1, y1 in RUBBED) and reading.box[i][2] - reading.box[i][0] < 60:
            gone.add(i)
        if any(x0 <= cx < x1 and y0 <= cy < y1 for x0, y0, x1, y1 in STAYS):
            gone.discard(i)
    bare = np.clip(rubbed(ref, reading, gone), 0, 1)

    ink = ref[reading.ink > 0.93].mean(axis=0)
    page = np.dstack([np.asarray(Image.fromarray(bare[..., c].astype(np.float32), mode="F").resize((cols, rows), Image.Resampling.LANCZOS), dtype=np.float64) for c in range(3)])
    wet = np.clip(hand.wet, 0, 1)[..., None]
    page = page * (1 - wet) + ink * wet

    x0, y0, x1, y1 = (v * UP for v in card(ref))
    out = np.clip(page, 0, 1)[y0:y1, x0:x1]
    target = os.path.join(ROOT, "public", "objects", "letter.avif")
    Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(target, quality=84, subsampling="4:4:4", speed=2)
    print(f"letter {x1 - x0}x{y1 - y0} {os.path.getsize(target) / 1e3:.0f} kB")
    if DEBUG:
        Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(os.path.join(DEBUG, "out.png"))


main()
