# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""The error page: a book of poems lying open on white silk, after the decorated anthologies of the Heian court,
photographed from above in soft window light.

    uv run studio/error/book.py [--plates wide tall] [--scale 0.5] [--samples 256] [--proof DIR]

Each page is washi, kozo fibres and all, with sheets of dyed paper joined on along torn edges, waves printed in mica,
cut gold leaf sprinkled over it and bands of gold dust laid across it like mist. Ki no Tomonori's poem (Kokinshū 84)
is brushed down the right-hand page in sumi, his name under it and a seal in cinnabar under that; the left-hand page
is printed with a reading of the poem, what happened and the two things to do about it. Every word is in the
photograph: the page lays clear live text over the same places, from src/components/error.json.

This script draws each page as maps (colour, relief, where there is metal, how rough, where mica lies), scene.py
lays them on the book in Blender and lights it, and this script then finishes the render the way it would be in
Photoshop: levels, a highlight glow, a warm leak of light, a vignette and grain. The wide plate is the open book, for
a window wider than tall; the tall plate is one loose page of it, for a phone.

Writes public/objects/error-<plate>.avif and src/components/error.json.
"""

import argparse
import json
import math
import os
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FONTS = os.path.join(HERE, "fonts")
BRUSH = os.path.join(FONTS, "YujiSyuku-Regular.ttf")
SERIF = os.path.join(FONTS, "EBGaramond-400.ttf")
SERIF_MEDIUM = os.path.join(FONTS, "EBGaramond-500.ttf")
SEAL_CUT = os.path.join(FONTS, "ShipporiMincho-Medium.ttf")
PX = 10  # map pixels to the millimetre

POEM = ["ひさかたの", "光のどけき", "春の日に", "しづ心なく", "花の散るらむ"]
POET = "紀友則"
SEAL = "散花"
READING = ["The light of far heaven", "lies calm on this spring day.", "Why, then, do the blossoms", "fall with such unsettled hearts?"]
SOURCE = "Ki no Tomonori, Kokinshū 84"
MESSAGE = "This page hit an error while it was opening."
AGAIN = "Open it again"
HOME = "Go to the first page"


def linear(hex_colour):
    c = np.array([int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def encode(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


WASHI = linear("#f1ede2")  # unbleached kozo, a little warm
INDIGO = linear("#c4d7d9")  # paper dyed pale with indigo
WISTERIA = linear("#d9cee0")  # paper dyed with wisteria
SUMI = linear("#151311")
GOLD = np.array([1.0, 0.74, 0.33])  # gold leaf, as metal
PALE_GOLD = np.array([0.98, 0.83, 0.52])  # leaf beaten with a little silver in it
SILVER = np.array([0.30, 0.29, 0.27])  # silver leaf, gone dark as old silver leaf does
SHU = linear("#b3322a")  # cinnabar seal paste


class Page:
    """One sheet's maps, w by h millimetres, x across from its left edge and y down from its top."""

    def __init__(self, w, h, seed):
        self.w, self.h = w, h
        self.W, self.H = int(round(w * PX)), int(round(h * PX))
        self.rng = np.random.default_rng(seed)
        self.albedo = np.ones((self.H, self.W, 3), np.float32) * WASHI
        self.height = np.zeros((self.H, self.W), np.float32)
        self.metal = np.zeros((self.H, self.W), np.float32)
        self.rough = np.full((self.H, self.W), 0.86, np.float32)
        self.coat = np.zeros((self.H, self.W), np.float32)
        self.fibres = np.zeros((self.H, self.W), np.float32)
        self.anchors = []
        self.y, self.x = np.mgrid[0 : self.H, 0 : self.W].astype(np.float32) / PX

    # ---------------------------------------------------------------- noise

    def noise(self, low, high, aspect=1.0):
        """Noise holding features between low and high millimetres across, unit deviation; aspect stretches it
        along x."""
        fy = np.fft.fftfreq(self.H) * PX
        fx = np.fft.fftfreq(self.W) * PX * aspect
        radius = np.hypot(*np.meshgrid(fy, fx, indexing="ij"))
        band = np.exp(-((radius * low) ** 2)) - np.exp(-((radius * high) ** 2))
        field = np.real(np.fft.ifft2(np.fft.fft2(self.rng.standard_normal((self.H, self.W))) * band))
        return (field / (field.std() + 1e-9)).astype(np.float32)

    def strands(self, count, length, width, wander, region=None):
        """Fibres, as how much of each pixel they cover: each length millimetres long (a range), its direction
        wandering as it goes. region, a box in mm, keeps them to it."""
        cover = np.zeros((self.H, self.W), np.float32)
        x0, y0, x1, y1 = region or (0, 0, self.w, self.h)
        for _ in range(count):
            steps = max(2, int(self.rng.uniform(*length) * PX * 2))
            turn = np.cumsum(self.rng.normal(0, wander, steps)) + self.rng.uniform(0, 2 * np.pi)
            x = self.rng.uniform(x0, x1) * PX + np.cumsum(0.5 * np.cos(turn))
            y = self.rng.uniform(y0, y1) * PX + np.cumsum(0.5 * np.sin(turn))
            keep = (x >= 0) & (x < self.W - 1) & (y >= 0) & (y < self.H - 1)
            weight = np.sin(np.linspace(0, np.pi, steps)) ** 0.5
            np.add.at(cover, (np.round(y[keep]).astype(int), np.round(x[keep]).astype(int)), weight[keep])
        sigma = max(width * PX, 0.6)
        return np.clip(ndimage.gaussian_filter(cover, sigma) * np.sqrt(2 * np.pi) * sigma / 2, 0, 1)

    # ---------------------------------------------------------------- paper

    def washi(self):
        """Kozo paper: the pulp lying unevenly in clouds, long bast fibres through it, a few flecks of bark."""
        formation = self.noise(6, 40)
        area = self.w * self.h
        long = self.strands(int(area * 0.07), (6, 26), 0.03, 0.07)
        short = self.strands(int(area * 0.16), (1.5, 6), 0.025, 0.2)
        bark = self.strands(int(area * 0.0012), (0.6, 2.5), 0.05, 0.4)
        self.fibres = np.clip(long + 0.6 * short, 0, 1)
        shade = 1 + 0.009 * formation + 0.06 * long + 0.03 * short
        self.albedo *= shade[..., None]
        self.albedo = self.albedo * (1 - 0.6 * bark[..., None]) + linear("#8a7a62") * 0.6 * bark[..., None]
        self.height += 0.012 * formation + 0.05 * long + 0.025 * short
        self.rough -= 0.05 * long

    def joined(self, colour, edge, below, seed, mica=False):
        """A sheet of dyed paper joined on, torn along edge (points in mm, left to right), covering what is below
        the edge or above it. Its torn edge feathers out in fibres, paler than the dyed sheet."""
        rng = np.random.default_rng(seed)
        xs, ys = np.array(edge, np.float32).T
        line = np.interp(self.x[0], xs, ys)
        # The tear wanders at two scales as it goes.
        for scale, amount in ((14, 1.6), (3.5, 0.5), (0.9, 0.18)):
            knots = rng.normal(0, amount, int(self.w / scale) + 3)
            line += np.interp(self.x[0] / scale, np.arange(len(knots)), knots)
        depth = (self.y - line[None, :]) * (1 if below else -1)  # mm inside the sheet
        inside = np.clip(depth * PX + 0.5, 0, 1)
        fringe_fibres = self.strands(int(self.w * 6), (0.8, 3.0), 0.025, 0.35)
        fringe = fringe_fibres * np.clip(1 + depth / 1.6, 0, 1) * (depth < 0.4)
        cover = np.maximum(inside, np.clip(fringe * 1.6, 0, 1))
        paler = np.clip(fringe * (depth < 0.6), 0, 1)
        dyed = colour * (1 + 0.02 * self.noise(5, 30))[..., None]
        tint = dyed * (1 - 0.55 * paler[..., None]) + WASHI * 0.55 * paler[..., None]
        self.albedo = self.albedo * (1 - cover[..., None]) + tint * cover[..., None] * (self.albedo / WASHI)
        self.height += 0.035 * inside + 0.05 * fringe
        if mica:
            self.mica(inside)
        return inside

    def mica(self, region, r=8.5):
        """Waves printed in mica from a woodblock (seigaiha): rings of overlapping circles, the lower rows over the
        upper, only where region is. Mica is a sheen, not a colour."""
        rows = r / 2
        k = np.floor(self.y / rows)
        best = np.full(self.y.shape, np.inf, np.float32)
        for dk in (2, 1, 0):  # lower rows cover the ones above
            row = k + dk
            shift = np.where(row % 2 == 0, 0, r)
            cx = np.round((self.x - shift) / (2 * r)) * 2 * r + shift
            d = np.hypot(self.x - cx, self.y - row * rows)
            best = np.where(np.isinf(best) & (d < r), d, best)
        rings = np.abs(((best + 0.5) % 2.0) - 1.0) < 0.28
        print_ = rings & np.isfinite(best) & (best < r - 0.6)
        mottle = np.clip(0.75 + 0.35 * self.noise(0.4, 3), 0, 1)
        m = ndimage.gaussian_filter(print_.astype(np.float32), 0.6) * mottle * region
        self.coat = np.maximum(self.coat, m)
        self.albedo = self.albedo * (1 + 0.06 * m[..., None])
        self.rough -= 0.25 * m

    # ---------------------------------------------------------------- gold

    def leaf(self, drifts, seed):
        """Cut gold leaf, sprinkled in drifts (centre x, y, spread in mm, count): squares, slivers and needles, a few
        of silver gone dark. Each is crinkled where it was pressed down."""
        rng = np.random.default_rng(seed)
        layers = {tone: Image.new("L", (self.W, self.H), 0) for tone in ("gold", "pale", "silver")}
        draws = {tone: ImageDraw.Draw(img) for tone, img in layers.items()}
        for cx, cy, spread, count in drifts:
            for _ in range(count):
                r = spread * math.sqrt(rng.random())
                a = rng.random() * 2 * math.pi
                x, y = cx + r * math.cos(a), cy + r * math.sin(a) * 1.4
                kind = rng.choice(["square", "sliver", "needle", "chip"], p=[0.22, 0.2, 0.14, 0.44])
                size = {"square": rng.uniform(1.8, 6.5) ** 1.0, "sliver": rng.uniform(1.5, 5), "needle": rng.uniform(5, 16), "chip": rng.uniform(0.4, 1.6)}[kind]
                if kind == "needle":
                    pts = [(-size / 2, -0.25), (size / 2, -0.2), (size / 2, 0.25), (-size / 2, 0.3)]
                elif kind == "sliver":
                    pts = [(-size / 2, -size / 2), (size / 2, -size / 3), (-size / 4, size / 2)]
                else:
                    pts = [(-size / 2, -size / 2), (size / 2, -size / 2), (size / 2, size / 2), (-size / 2, size / 2)]
                turn = rng.random() * math.pi
                c, s = math.cos(turn), math.sin(turn)
                poly = [((x + (px + rng.normal(0, size * 0.04)) * c - py * s) * PX, (y + (px * s + py * c) + rng.normal(0, size * 0.04)) * PX) for px, py in pts]
                tone = rng.choice(["gold", "pale", "silver"], p=[0.62, 0.3, 0.08])
                draws[tone].polygon(poly, fill=255)
        crinkle = self.noise(0.3, 2.5)
        for tone, colour in (("gold", GOLD), ("pale", PALE_GOLD), ("silver", SILVER)):
            m = np.asarray(layers[tone], np.float32) / 255
            m = ndimage.gaussian_filter(m, 0.5)
            self.lay_metal(m, colour, 0.34 if tone != "silver" else 0.5, crinkle)

    def lay_metal(self, m, colour, rough, crinkle):
        self.albedo = self.albedo * (1 - m[..., None]) + colour * m[..., None]
        self.metal = np.maximum(self.metal, m)
        self.rough = self.rough * (1 - m) + (rough + 0.06 * crinkle) * m
        self.height += m * (0.02 + 0.012 * crinkle)

    def dust(self, band, seed, density=26.0):
        """A band of gold dust laid across the page like mist (sunago): a long cloud, x0, y0, x1, y1 in mm, thick in
        its body and thinning to nothing at its edges, sown with grains from a tenth to a third of a millimetre."""
        rng = np.random.default_rng(seed)
        x0, y0, x1, y1 = band
        cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
        # A long, flat cloud: an ellipse whose rim billows in lobes.
        ux, uy = (self.x - cx) / rx, (self.y - cy) / ry
        billow = 0.22 * self.noise(6, 30, aspect=0.35)
        field = np.clip((1 - np.hypot(ux ** 1, uy * (1 + 0.15 * ux ** 2)) + billow) * 2.2, 0, 1) ** 1.3
        n = int(rx * ry * math.pi * density)
        gx = rng.uniform(x0, x1, n)
        gy = rng.uniform(y0, y1, n)
        keep = rng.random(n) < field[np.clip((gy * PX).astype(int), 0, self.H - 1), np.clip((gx * PX).astype(int), 0, self.W - 1)]
        gx, gy = gx[keep], gy[keep]
        grains = np.zeros((self.H, self.W), np.float32)
        size = rng.uniform(0.6, 1.0, len(gx)) ** 3 * 2.2 + 0.5  # px
        for big in (False, True):
            pick = (size > 1.6) == big
            ix = np.clip((gx[pick] * PX).astype(int), 0, self.W - 1)
            iy = np.clip((gy[pick] * PX).astype(int), 0, self.H - 1)
            np.add.at(grains, (iy, ix), 1.0)
        grains = np.clip(ndimage.gaussian_filter(grains, 0.55) * 3.5, 0, 1)
        grains = np.maximum(grains, np.clip(ndimage.grey_dilation(grains, size=2) - 0.4, 0, 1) * 0.6)
        crinkle = self.noise(0.2, 1)
        # The size the dust was laid down with stains the paper golden under it, and the finest dust lies in it as a
        # haze too small to see grain by grain.
        haze = ndimage.gaussian_filter(field, 4) * (0.7 + 0.3 * self.noise(1, 8))
        self.albedo *= 1 - 0.09 * haze[..., None] * np.array([0, 0.3, 0.9])
        self.lay_metal(np.clip(0.16 * haze, 0, 1), GOLD, 0.45, crinkle)
        self.lay_metal(grains * 0.95, PALE_GOLD * 0.6 + GOLD * 0.4, 0.36, crinkle)

    def rule(self, x0, y, x1, thick=0.55, seed=3):
        """A cut strip of gold leaf laid as a rule."""
        rng = np.random.default_rng(seed)
        wobble = np.interp(self.x[0], np.linspace(x0, x1, 8), rng.normal(0, 0.06, 8))
        top = y - thick / 2 + wobble
        m = np.clip((self.y - top[None, :]) * PX, 0, 1) * np.clip((top[None, :] + thick - self.y) * PX, 0, 1)
        m *= np.clip((self.x - x0) * PX, 0, 1) * np.clip((x1 - self.x) * PX, 0, 1)
        self.lay_metal(m, GOLD, 0.32, self.noise(0.3, 2))

    # ---------------------------------------------------------------- ink

    def glyphs(self, draw_fn):
        img = Image.new("L", (self.W, self.H), 0)
        draw_fn(ImageDraw.Draw(img))
        return np.asarray(img, np.float32) / 255

    def warp(self, a, amount, scale):
        dx = self.noise(scale, scale * 6) * amount * PX
        dy = self.noise(scale, scale * 6) * amount * PX
        yy, xx = np.mgrid[0 : self.H, 0 : self.W].astype(np.float32)
        return ndimage.map_coordinates(a, [yy + dy, xx + dx], order=1)

    def brush(self, a, density=1.0):
        """Sumi from a brush: the hand's wobble, the ink wicking a little along the fibres, pooling darker at the
        edges of a stroke, and running dry in streaks here and there."""
        a = self.warp(a, 0.1, 0.6)
        soft = ndimage.gaussian_filter(a, 0.12 * PX)
        a = np.maximum(a, soft * 0.85)
        a = np.clip(a + ndimage.gaussian_filter(a, 0.4 * PX) * self.fibres * 0.35, 0, 1)
        pool = np.clip(a - ndimage.gaussian_filter(a, 0.3 * PX), 0, 1)
        streak = self.noise(0.15, 1.2, aspect=4.0)
        zone = np.clip(self.noise(6, 18) - 0.9, 0, 1)
        dry = np.clip(streak - 0.4, 0, 1) * zone
        d = a * (0.9 + 0.06 * self.noise(1, 6)) * (1 - 0.7 * dry) + 0.3 * pool
        return np.clip(d * density, 0, 1)

    def press(self, a, density=0.95):
        """Type printed from metal: the ink squeezed a little past the face, taken unevenly, the paper dented."""
        spread = np.maximum(a, ndimage.gaussian_filter(a, 0.08 * PX) * 0.8)
        salt = np.clip(1 - np.clip(self.noise(0.1, 0.5) - 1.6, 0, 1), 0, 1)
        self.height -= 0.02 * ndimage.gaussian_filter(a, 0.15 * PX)
        return np.clip(spread * salt * density, 0, 1)

    def ink(self, d, colour=SUMI, rough=0.62):
        self.albedo = self.albedo * (1 - d[..., None]) + colour * d[..., None]
        self.rough = self.rough * (1 - d) + rough * d
        self.metal *= 1 - d

    def poem(self, right, top, pitch, em, starts, sizes, advance=1.1):
        """The poem brushed in columns, the first at right (mm), each starting lower by its share of starts (in em)."""
        font_cache = {}

        def draw(d):
            for i, line in enumerate(POEM):
                size = em * sizes[i]
                font = font_cache.setdefault(size, ImageFont.truetype(BRUSH, int(size * PX)))
                x = right - i * pitch
                y = top + starts[i] * em
                for ch in line:
                    d.text((x * PX, (y + size / 2) * PX), ch, font=font, fill=255, anchor="mm")
                    y += size * advance
                self.anchors.append({"id": f"poem-{i}", "text": line, "box": [x - size / 2, top + starts[i] * em, x + size / 2, y], "vertical": True})

        self.ink(self.brush(self.glyphs(draw)))

    def signature(self, x, bottom, em):
        font = ImageFont.truetype(BRUSH, int(em * PX))
        top = bottom - len(POET) * em * 1.25

        def draw(d):
            for i, ch in enumerate(POET):
                d.text((x * PX, (top + em * (0.5 + 1.25 * i)) * PX), ch, font=font, fill=255, anchor="mm")

        self.ink(self.brush(self.glyphs(draw), 0.92))
        self.anchors.append({"id": "poet", "text": POET, "box": [x - em / 2, top, x + em / 2, bottom], "vertical": True})

    def seal(self, x0, y0, size):
        """A seal in cinnabar, its two characters cut so the paper shows through (散花, scattered blossoms)."""
        font = ImageFont.truetype(SEAL_CUT, int(size * 0.47 * PX))
        rng = np.random.default_rng(31)
        corners = [(x0 + rng.normal(0, 0.15), y0 + rng.normal(0, 0.15)), (x0 + size + rng.normal(0, 0.15), y0 + rng.normal(0, 0.15)), (x0 + size + rng.normal(0, 0.15), y0 + size + rng.normal(0, 0.15)), (x0 + rng.normal(0, 0.15), y0 + size + rng.normal(0, 0.15))]

        def stone(d):
            d.rounded_rectangle([x0 * PX, y0 * PX, (x0 + size) * PX, (y0 + size) * PX], radius=size * 0.08 * PX, fill=255)
            d.polygon([(cx * PX, cy * PX) for cx, cy in corners], fill=255)

        def cut(d):
            for i, ch in enumerate(SEAL):
                d.text(((x0 + size / 2) * PX, (y0 + size * (0.29 + 0.44 * i)) * PX), ch, font=font, fill=255, anchor="mm")

        m = self.glyphs(stone) * (1 - self.glyphs(cut))
        m = self.warp(m, 0.12, 0.8)
        # The paste takes the paper's grain: it misses the low places and the tops of fibres.
        taken = np.clip(1.15 - np.clip(self.noise(0.1, 0.6) - 0.5, 0, 2) * 0.5 - self.fibres * 0.25, 0, 1)
        m = np.clip(m * taken, 0, 1) * 0.93
        self.ink(m, SHU * (1 + 0.08 * self.noise(0.5, 3))[..., None], rough=0.48)
        self.height += 0.012 * m

    def text(self, lines, x, baseline, size, leading, font=SERIF, density=0.95, prefix="line", colour=SUMI):
        """Lines of type, the first sitting on baseline (mm), each leading below the last."""
        f = ImageFont.truetype(font, int(size * PX))

        def draw(d):
            for i, line in enumerate(lines):
                d.text((x * PX, (baseline + i * leading) * PX), line, font=f, fill=255, anchor="ls")

        self.ink(self.press(self.glyphs(draw), density), colour)
        for i, line in enumerate(lines):
            width = f.getlength(line) / PX
            y = baseline + i * leading
            self.anchors.append({"id": f"{prefix}-{i}", "text": line, "box": [x, y - size * 0.78, x + width, y + size * 0.24]})
        return [f.getlength(line) / PX for line in lines]

    def width(self, line, size, font=SERIF):
        return ImageFont.truetype(font, int(size * PX)).getlength(line) / PX

    def wrap(self, words, size, room, font=SERIF):
        lines, line = [], ""
        for word in words.split():
            trial = f"{line} {word}".strip()
            if line and self.width(trial, size, font) > room:
                lines.append(line)
                line = word
            else:
                line = trial
        return lines + [line]

    def links(self, x, baseline, size, gap):
        """The two things to do, printed, each underlined with a strip of gold leaf."""
        wa = self.text([AGAIN], x, baseline, size, 0, font=SERIF_MEDIUM, prefix="again")[0]
        x2 = x + wa + gap
        wh = self.text([HOME], x2, baseline, size, 0, font=SERIF_MEDIUM, prefix="home")[0]
        self.rule(x, baseline + size * 0.3, x + wa, 0.38, seed=5)
        self.rule(x2, baseline + size * 0.3, x2 + wh, 0.38, seed=6)

    # ---------------------------------------------------------------- out

    def save(self, folder, name):
        rough = np.clip(self.rough, 0.05, 1)
        h = self.height
        h = (h - h.min()) / (h.max() - h.min() + 1e-9)
        Image.fromarray((encode(self.albedo) * 255 + 0.5).astype(np.uint8)).save(os.path.join(folder, f"{name}-albedo.png"))
        Image.fromarray((h * 65535 + 0.5).astype(np.uint16)).save(os.path.join(folder, f"{name}-height.png"))
        Image.fromarray((np.clip(self.metal, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(folder, f"{name}-metal.png"))
        Image.fromarray((rough * 255 + 0.5).astype(np.uint8)).save(os.path.join(folder, f"{name}-rough.png"))
        Image.fromarray((np.clip(self.coat, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(folder, f"{name}-coat.png"))
        return {"size": [self.w, self.h], "relief": float(self.height.max() - self.height.min()), "anchors": self.anchors}


# ----------------------------------------------------------------------- layouts

PAGE = (205.0, 285.0)


def right_page():
    """The poem's page, its gutter at its left edge."""
    p = Page(*PAGE, seed=11)
    p.washi()
    p.joined(INDIGO, [(0, 196), (60, 204), (125, 229), (205, 214)], below=True, seed=4)
    p.dust((70, 14, 230, 44), seed=8)
    p.dust((-20, 238, 120, 262), seed=9, density=7)
    p.leaf([(168, 30, 20, 40), (120, 214, 18, 28), (192, 262, 12, 18), (30, 60, 10, 12)], seed=12)
    p.poem(right=166, top=50, pitch=24, em=16, starts=[0, 1.7, 0.6, 2.8, 1.2], sizes=[1, 0.94, 1, 0.9, 1])
    p.signature(x=44, bottom=214, em=8.2)
    p.seal(37.5, 222, 13.5)
    return p


def left_page():
    """The reading's page, its gutter at its right edge."""
    p = Page(*PAGE, seed=21)
    p.washi()
    p.joined(WISTERIA, [(0, 72), (70, 62), (140, 79), (205, 66)], below=False, seed=6, mica=True)
    p.dust((-30, 236, 140, 262), seed=13)
    p.dust((40, 255, 190, 276), seed=14, density=6)
    p.leaf([(40, 30, 22, 36), (150, 52, 16, 22), (180, 210, 14, 16), (12, 170, 8, 9)], seed=22)
    x = 38
    p.text(READING, x, 108, 8.4, 12.8, prefix="reading")
    p.text([SOURCE], x, 160, 5.8, 0, density=0.6, prefix="source")
    p.rule(x, 177, x + 30, 0.6)
    p.text(p.wrap(MESSAGE, 6.8, 205 - x - 30), x, 195, 6.8, 9.6, font=SERIF_MEDIUM, prefix="message")
    p.links(x, 214, 6.8, 12)
    return p


def loose_page():
    """One page of the book on its own, for a tall window: the poem above, the reading below it."""
    p = Page(160.0, 335.0, seed=31)
    p.washi()
    p.joined(WISTERIA, [(0, 17), (60, 24), (110, 15), (160, 21)], below=False, seed=7, mica=True)
    p.joined(INDIGO, [(0, 314), (50, 306), (115, 318), (160, 309)], below=True, seed=5)
    p.dust((40, 22, 190, 46), seed=18)
    p.dust((-30, 168, 110, 186), seed=19, density=7)
    p.leaf([(128, 36, 16, 30), (98, 160, 12, 15), (136, 178, 10, 12), (122, 324, 14, 16)], seed=32)
    p.poem(right=130, top=36, pitch=21, em=14, starts=[0, 1.7, 0.6, 2.8, 1.2], sizes=[1, 0.94, 1, 0.9, 1])
    p.signature(x=27, bottom=152, em=7.2)
    p.seal(21, 159, 11.5)
    x = 22
    p.text(READING, x, 206, 7.2, 11.0, prefix="reading")
    p.text([SOURCE], x, 251, 5.0, 0, density=0.6, prefix="source")
    p.rule(x, 263, x + 26, 0.55)
    p.text(p.wrap(MESSAGE, 6.1, 160 - 2 * x), x, 278, 6.1, 8.6, font=SERIF_MEDIUM, prefix="message")
    p.links(x, 298, 6.1, 9)
    return p


PLATES = {
    # px across and down, and how many mm of the set the frame takes in across and down. Each takes in enough silk
    # round the pages that a window can crop it to its own shape and still show every page whole: the open book any
    # window from 0.95 to 2.4 times as wide as it is tall, the loose page any from 0.42 to 0.95.
    "wide": {"px": [3050, 1800], "frame": [780.0, 460.0], "pages": {"left": left_page, "right": right_page}},
    "tall": {"px": [2100, 2550], "frame": [333.0, 405.0], "pages": {"loose": loose_page}},
}


# ----------------------------------------------------------------------- finish


def gaussian(img, sigma):
    return np.stack([ndimage.gaussian_filter(img[..., c], sigma) for c in range(3)], -1)


def finish(rgb, pages):
    """The render taken into Photoshop: levels set off the paper, a soft glow off the highlights, a warm leak of
    window light from the top left, a little warmth in the shadows, a vignette and fine grain."""
    h, w, _ = rgb.shape
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722])
    on = np.zeros((h, w), bool)
    for x0, y0, x1, y1 in pages:
        on[int(y0 * h) : int(y1 * h), int(x0 * w) : int(x1 * w)] = True
    paper = np.percentile(lum[on], 70)
    rgb = rgb * (0.80 / paper)
    # Glow: what is over white spreads into what is around it, as a lens and a soft-focus filter would.
    over = np.clip(rgb - 1.05, 0, 4)
    glow = gaussian(over, w * 0.003) * 0.22 + gaussian(over, w * 0.018) * 0.16
    rgb = rgb + glow
    # Light from a window at the top left, warm, falling off across the frame.
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    leak = np.exp(-(((xx / w + 0.05) ** 2) / 0.35 + ((yy / h + 0.1) ** 2) / 0.5))
    rgb = rgb * (1 + 0.10 * leak[..., None] * np.array([1.0, 0.92, 0.75]))
    # Tone: a film shoulder so the paper's whites roll off instead of clipping.
    knee = 0.78
    over = np.maximum(rgb - knee, 0)
    rgb = np.where(rgb <= knee, rgb, knee + (1 - knee) * (1 - np.exp(-over / (1 - knee))))
    out = encode(rgb)
    # Warm the shadows a touch, lift the blacks off zero.
    out = out * 0.975 + 0.012 * np.array([1.0, 0.85, 0.7])
    # Vignette.
    r = np.hypot((xx / w - 0.5) * 1.1, (yy / h - 0.48))
    out = out * (1 - 0.16 * np.clip(r - 0.25, 0, 1) ** 1.6)[..., None]
    # Grain, finer in the highlights.
    rng = np.random.default_rng(7)
    grain = ndimage.gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), 0.6)
    out = out + (0.018 * grain * (1 - 0.6 * out.mean(-1)))[..., None]
    return np.clip(out, 0, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plates", nargs="*", default=list(PLATES))
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument("--proof", help="also write the maps and the raw render into this folder")
    args = parser.parse_args()

    places_path = os.path.join(ROOT, "src", "components", "error.json")
    places = json.load(open(places_path)) if os.path.exists(places_path) else {}
    for plate in args.plates:
        spec = PLATES[plate]
        with tempfile.TemporaryDirectory() as work:
            pages = {}
            for name, build in spec["pages"].items():
                print(plate, name, flush=True)
                pages[name] = build().save(work, name)
            px = [int(round(v * args.scale)) for v in spec["px"]]
            layout = {"plate": plate, "px": px, "frame": spec["frame"], "pages": pages, "samples": args.samples}
            json.dump(layout, open(os.path.join(work, "layout.json"), "w"))
            subprocess.run(["blender", "-b", "--factory-startup", "-P", os.path.join(HERE, "scene.py"), "--", work], check=True)
            raw = np.load(os.path.join(work, "render.npy"))
            boxes = json.load(open(os.path.join(work, "boxes.json")))
            if args.proof:
                os.makedirs(args.proof, exist_ok=True)
                for f in os.listdir(work):
                    if f.endswith(".png"):
                        os.replace(os.path.join(work, f), os.path.join(args.proof, f"{plate}-{f}"))
        rgb = raw[..., :3].astype(np.float32)
        spread = boxes.pop("_pages")
        out = finish(rgb, spread)
        image = Image.fromarray((out * 255 + 0.5).astype(np.uint8))
        image.save(os.path.join(ROOT, "public", "objects", f"error-{plate}.avif"), quality=64, subsampling="4:4:4", speed=4)
        if args.proof:
            image.save(os.path.join(args.proof, f"error-{plate}.png"))
        # The part of the plate the pages cover, which the page keeps in the window however it crops the rest, and the
        # colour the plate's edges fall to, which the page lays round it when the window is the wrong shape for it.
        cover = [min(b[0] for b in spread), min(b[1] for b in spread), max(b[2] for b in spread), max(b[3] for b in spread)]
        rim = np.concatenate([out[:8].reshape(-1, 3), out[-8:].reshape(-1, 3), out[:, :8].reshape(-1, 3), out[:, -8:].reshape(-1, 3)]).mean(0)
        places[plate] = {"size": spec["px"], "pages": [round(v, 4) for v in cover], "edge": "#%02x%02x%02x" % tuple(int(v * 255 + 0.5) for v in rim), "boxes": boxes}
        json.dump(places, open(places_path, "w"), indent=1, ensure_ascii=False)
        print("wrote", plate, flush=True)


if __name__ == "__main__":
    main()
