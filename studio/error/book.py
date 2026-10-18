# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""The error page: a book of poems lying open on a dark cloth, after the decorated anthologies of the Heian court,
photographed from above in soft window light.

    uv run studio/error/book.py [--plates wide tall] [--scale 0.5] [--samples 256] [--proof DIR]

Each page is washi, kozo fibres and all, with sheets of dyed paper joined on along torn edges, patterns printed in
mica, cut gold leaf sprinkled over it, bands of gold dust and gold-leaf mist laid across it, and painted in mineral
colours, sumi and gold: cranes in flight, a weeping cherry in flower, a moon in silver, Mount Fuji in mist, pampas
grass, plovers over water and a river carrying maple leaves. Ki no Tomonori's poem (Kokinshū 84)
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
BRIGHT_SILVER = np.array([0.78, 0.78, 0.76])  # silver leaf where it has kept its shine
SHU = linear("#b3322a")  # cinnabar seal paste
# Mineral paints, ground and bound in glue, as the painters of the court used them.
GOFUN = linear("#f8f4ec")  # shell white
SAKURA = linear("#eaa9b6")  # the pink at a blossom's heart
ENJI = linear("#c25a6e")  # safflower red
MOMIJI = [linear("#c2412b"), linear("#d8692f"), linear("#b8322f"), linear("#cf8a36")]  # maple reds and ochres
ROKUSHO = linear("#5f8a64")  # malachite green
BARK = linear("#2b231d")  # sumi with a little brown in it
FUJI = linear("#8193ad")  # an indigo wash, as a filter over the paper


def catmull(points, step=0.12):
    """A smooth path through points (mm), sampled every step mm or so."""
    p = np.asarray(points, np.float64)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1 : i + 3]
        n = max(2, int(np.hypot(*(p2 - p1)) / step))
        t = np.linspace(0, 1, n, endpoint=False)[:, None]
        out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t**2 + (3 * p1 - p0 - 3 * p2 + p3) * t**3))
    out.append(p[-2][None])
    return np.vstack(out)


def place(points, x, y, size, turn=0.0, flip=False):
    """Points drawn round 0, 0 at unit size, scaled, mirrored, turned and moved to x, y (mm)."""
    p = np.asarray(points, np.float64) * size
    if flip:
        p[:, 0] = -p[:, 0]
    c, s = math.cos(turn), math.sin(turn)
    return np.stack([x + p[:, 0] * c - p[:, 1] * s, y + p[:, 0] * s + p[:, 1] * c], -1)


# A red-crowned crane in flight, flying to the right, at a wingspan of about one: its near wing raised, white with a
# black trailing edge, and the far wing behind it.
CRANE_WING_OUTLINE = [(0.06, -0.02), (0.11, -0.13), (0.10, -0.26), (0.05, -0.39), (-0.02, -0.50), (-0.06, -0.47), (-0.05, -0.42), (-0.09, -0.45), (-0.11, -0.39), (-0.14, -0.41), (-0.15, -0.34), (-0.19, -0.35), (-0.18, -0.28), (-0.22, -0.27), (-0.19, -0.20), (-0.21, -0.14), (-0.14, -0.08), (-0.07, -0.02)]
CRANE_WING = [(x * 1.35, y) for x, y in CRANE_WING_OUTLINE]
CRANE_TRAILING_LINE = [(-0.07, -0.03), (-0.15, -0.09), (-0.20, -0.15), (-0.19, -0.21), (-0.21, -0.27)]
CRANE_TRAILING = [(x * 1.35, y) for x, y in CRANE_TRAILING_LINE]
CRANE_BODY = [(0.15, -0.04), (0.08, -0.07), (-0.04, -0.07), (-0.14, -0.04), (-0.19, 0.0), (-0.13, 0.04), (-0.02, 0.05), (0.09, 0.03)]
CRANE_TAIL = [(-0.13, -0.04), (-0.22, -0.03), (-0.25, 0.01), (-0.20, 0.04), (-0.12, 0.04)]
CRANE_NECK = [(0.12, -0.03), (0.22, -0.05), (0.33, -0.065), (0.41, -0.07)]
CRANE_BEAK = [(0.44, -0.07), (0.50, -0.066), (0.545, -0.06)]
CRANE_LEGS = [[(-0.12, 0.02), (-0.27, 0.04), (-0.44, 0.055)], [(-0.12, 0.03), (-0.27, 0.06), (-0.43, 0.08)]]
# A plover (chidori), as it is drawn over waves: a round body, two pointed wings up, a short beak, facing left.
PLOVER = [(-0.62, -0.10), (-0.46, -0.13), (-0.40, -0.22), (-0.28, -0.26), (-0.16, -0.22), (-0.12, -0.30), (-0.20, -0.52), (-0.30, -0.70), (-0.08, -0.56), (0.06, -0.36), (0.10, -0.24), (0.20, -0.30), (0.34, -0.56), (0.52, -0.74), (0.44, -0.44), (0.34, -0.20), (0.48, -0.16), (0.70, -0.14), (0.50, -0.02), (0.30, 0.10), (0.06, 0.16), (-0.18, 0.12), (-0.34, 0.02), (-0.44, -0.06)]


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

    # ---------------------------------------------------------------- painting

    def cached(self, key, make):
        if not hasattr(self, "_cache"):
            self._cache = {}
        if key not in self._cache:
            self._cache[key] = make()
        return self._cache[key]

    def canvas(self):
        img = Image.new("L", (self.W, self.H), 0)
        return img, ImageDraw.Draw(img)

    @staticmethod
    def mask(img, soften=0.5):
        return ndimage.gaussian_filter(np.asarray(img, np.float32) / 255, soften)

    def stroke(self, draw, points, w0, w1, taper=(0.08, 0.2), fill=255):
        """A brush stroke along points (mm), w0 mm wide where it starts and w1 where it ends, swelling in from its
        start and lifting off at its end over the given shares of its length."""
        path = catmull(points)
        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(path, axis=0).T))])
        t = s / max(s[-1], 1e-6)
        width = w0 + (w1 - w0) * t
        if taper[0]:
            width *= np.clip(0.35 + 0.65 * t / taper[0], 0, 1)
        if taper[1]:
            width *= np.clip((1 - t) / taper[1], 0.08, 1) ** 0.7
        for (x, y), w in zip(path, width):
            r = max(w / 2, 0.06) * PX
            draw.ellipse([x * PX - r, y * PX - r, x * PX + r, y * PX + r], fill=fill)

    def polygon(self, draw, points, fill=255):
        draw.polygon([(x * PX, y * PX) for x, y in points], fill=fill)

    def pigment(self, m, colour, body=0.025, rough=0.92, vary=0.05):
        """Mineral paint laid on the paper: opaque, a little raised and grainy, missing a fleck here and there."""
        grain = self.cached("grain", lambda: np.clip(1.06 - 0.3 * np.clip(self.noise(0.08, 0.5) - 1.1, 0, 3), 0, 1))
        swirl = self.cached("swirl", lambda: self.noise(1, 8))
        a = np.clip(m, 0, 1) * grain
        tint = colour * (1 + vary * swirl)[..., None] if np.ndim(colour) == 1 else colour
        self.albedo = self.albedo * (1 - a[..., None]) + tint * a[..., None]
        self.rough = self.rough * (1 - a) + rough * a
        self.metal *= 1 - a
        self.coat *= 1 - a
        self.height += body * ndimage.gaussian_filter(m, 0.8)

    def wash(self, m, colour, pool=0.35):
        """A wash of thin colour, a filter over the paper, pooling at its edges and drying in blooms (tarashikomi)."""
        bloom = self.cached("bloom", lambda: self.noise(2, 14))
        edge = np.clip(m - ndimage.gaussian_filter(m, 0.8 * PX), 0, 1)
        a = np.clip(m * (0.8 + 0.2 * bloom) + pool * edge, 0, 1)
        self.albedo *= 1 - a[..., None] * (1 - colour)
        self.coat *= 1 - 0.5 * a

    def gilt(self, m, colour=GOLD, rough=0.42):
        """Gold ground fine and painted on in glue (kindei): softer than leaf, with a duller shine."""
        self.lay_metal(np.clip(m, 0, 1), colour * 0.9, rough, self.cached("crinkle", lambda: self.noise(0.3, 2.5)))

    def outline(self, m, density=0.55, width=0.35):
        """A fine line of sumi round what is painted, as the painter drew it before laying the colour in."""
        rim = np.clip(ndimage.grey_dilation(m, size=int(width * PX) | 1) - m, 0, 1)
        self.ink(self.brush(rim, density))

    def kasumi(self, bands, seed, leaf=True):
        """Bands of mist in cut gold leaf (suyari-gasumi), each x0, x1, y (its middle) and depth in mm: long and flat,
        rounded at the ends, their edges easing in and out. The leaf was laid in squares, and its seams show."""
        rng = np.random.default_rng(seed)
        field = np.zeros((self.H, self.W), np.float32)
        for x0, x1, y, depth in bands:
            r = depth / 2
            sway = r * 0.18 * np.sin(self.x / rng.uniform(14, 26) + rng.uniform(0, 6)) + r * 0.1 * np.sin(self.x / rng.uniform(5, 9))
            cx = np.clip(self.x, x0 + r, x1 - r)
            d = np.hypot(self.x - cx, (self.y - y) * 1.0) - (r + sway)
            field = np.maximum(field, np.clip(-d * PX + 0.5, 0, 1))
        if not leaf:
            return field
        seams = ((np.abs((self.x + 7) % 36 - 18) > 17.85) | (np.abs((self.y + 3) % 36 - 18) > 17.85)).astype(np.float32)
        crinkle = self.cached("crinkle", lambda: self.noise(0.3, 2.5))
        self.lay_metal(field, GOLD * (1 - 0.12 * seams)[..., None], 0.3, crinkle)
        self.rough += 0.12 * seams * field
        self.height += 0.01 * seams * field
        return field

    def moon(self, cx, cy, r):
        """A full moon in silver leaf, kept bright in places and gone dark in others."""
        d = np.hypot(self.x - cx, self.y - cy)
        m = np.clip((r - d) * PX + 0.5, 0, 1)
        tarnish = np.clip(0.18 + 0.14 * self.noise(10, 60) + 0.04 * self.noise(0.5, 3), 0, 1)[..., None]
        colour = BRIGHT_SILVER * (1 - tarnish) + SILVER * tarnish
        # Burnished flat, so it takes the light as one soft sheen rather than as crinkles.
        self.lay_metal(m, colour, 0.48, 0.15 * self.cached("crinkle", lambda: self.noise(0.3, 2.5)))

    def fuji(self, cx, peak, base, half):
        """Mount Fuji in an indigo wash fading down into mist, its summit under snow in shell white."""
        u = np.abs(self.x - cx) / half
        height = base - peak
        crown = np.clip(u - 0.05, 0, None) / 0.95
        profile = peak + height * (1 - np.clip(1 - crown, 0, 1) ** 2.4)
        inside = (self.y >= profile) & (u < 1)
        t = np.clip((self.y - peak) / height, 0, 1)
        body = inside * np.clip(1 - t, 0, 1) ** 0.9 * 0.75
        self.wash(ndimage.gaussian_filter(body.astype(np.float32), 0.6), FUJI)
        # The snow comes down further in the gullies.
        gullies = np.abs(np.sin((self.x - cx) / half * 9.0)) ** 3
        line = peak + height * (0.24 + 0.1 * gullies + 0.03 * np.sin((self.x - cx) * 1.3))
        snow = (inside & (self.y < line)).astype(np.float32)
        self.pigment(ndimage.gaussian_filter(snow, 0.7), GOFUN, body=0.03)
        img, draw = self.canvas()
        xs = np.linspace(cx - half * 0.98, cx + half * 0.98, 80)
        ridge = peak + height * (1 - np.clip(1 - np.clip(np.abs(xs - cx) / half - 0.05, 0, None) / 0.95, 0, 1) ** 2.4)
        left, right = xs < cx, xs >= cx
        for pick in (left, right):
            pts = list(zip(xs[pick], ridge[pick] - 0.15))
            pts = pts if pts[0][1] < pts[-1][1] else pts[::-1]
            self.stroke(draw, pts[:: max(1, len(pts) // 14)], 0.7, 0.15, taper=(0.02, 0.5))
        self.ink(self.brush(self.mask(img), 0.6))

    def water(self, region, lines, seed, silver=False):
        """Water running in long lines of gold (ryūsui), the lines bunching and parting as the current goes, with a
        curl of wave lifting off here and there. region is x0, y0, x1, y1 in mm."""
        rng = np.random.default_rng(seed)
        x0, y0, x1, y1 = region
        img, draw = self.canvas()
        phases = rng.uniform(0, 2 * np.pi, 3)
        for i in range(lines):
            base = y0 + (y1 - y0) * (i + 0.5) / lines
            xs = np.linspace(x0, x1, 28)
            ys = base + 2.6 * np.sin(xs / 31 + phases[0] + i * 0.35) + 1.2 * np.sin(xs / 11 + phases[1] + i * 0.8)
            self.stroke(draw, list(zip(xs, ys)), rng.uniform(0.5, 0.8), rng.uniform(0.35, 0.6), taper=(0.04, 0.06))
            # Curls where the water breaks: an arc lifting off the line and rolling over.
            for _ in range(rng.integers(1, 3)):
                k = rng.integers(4, 24)
                cx, cy = xs[k], ys[k]
                r = rng.uniform(2.5, 4.5)
                a = np.linspace(math.pi * 1.0, math.pi * 2.6, 14)
                curl = [(cx + r * (1 - j / 18) * math.cos(t) + j * 0.3, cy - r * 0.9 + r * (1 - j / 18) * math.sin(t) * 0.9) for j, t in enumerate(a)]
                self.stroke(draw, [(cx - r * 1.4, cy + 0.2)] + curl, 0.6, 0.15, taper=(0.1, 0.4))
        m = self.mask(img)
        if silver:
            self.lay_metal(m, BRIGHT_SILVER * 0.8, 0.4, self.cached("crinkle", lambda: self.noise(0.3, 2.5)))
        else:
            self.gilt(m)

    def plovers(self, flock):
        """Plovers flying low over the water, in sumi, as they are drawn on lacquer and paper: a round body, a short
        beak and two wings swept up into points. Each is x, y, size (mm), turn and whether it faces right."""
        img, draw = self.canvas()
        for x, y, size, turn, flip in flock:
            at = lambda pts: place(pts, x, y, size, turn, flip)
            self.polygon(draw, at([(0.32 * math.cos(t) * (1.25 if math.cos(t) > 0 else 1.0), 0.2 * math.sin(t)) for t in np.linspace(0, 2 * np.pi, 30, endpoint=False)]))
            head = at([(-0.33, -0.1)])[0]
            r = size * 0.14
            draw.ellipse([(head[0] - r) * PX, (head[1] - r) * PX, (head[0] + r) * PX, (head[1] + r) * PX], fill=255)
            self.stroke(draw, at([(-0.42, -0.1), (-0.6, -0.06)]), size * 0.07, size * 0.02, taper=(0, 0.3))
            self.stroke(draw, at([(-0.1, -0.12), (-0.18, -0.4), (-0.36, -0.66)]), size * 0.2, size * 0.03, taper=(0, 0.6))
            self.stroke(draw, at([(0.1, -0.12), (0.22, -0.42), (0.46, -0.72)]), size * 0.2, size * 0.03, taper=(0, 0.6))
            self.stroke(draw, at([(0.3, 0.0), (0.66, -0.1)]), size * 0.14, size * 0.03, taper=(0, 0.6))
        m = self.mask(img, 0.6)
        self.ink(np.clip(m * (0.9 + 0.03 * self.cached("bloom", lambda: self.noise(2, 14))), 0, 1))

    def cranes(self, flock):
        """Red-crowned cranes in flight, each x, y, wingspan (mm), turn and whether it flies left: shell white, the
        neck, legs and trailing edges of the wings in sumi, the crown in red, all drawn round in a fine line."""
        white, w_draw = self.canvas()
        shade, s_draw = self.canvas()
        black, b_draw = self.canvas()
        red, r_draw = self.canvas()
        far_black, f_draw = self.canvas()
        for x, y, span, turn, flip in flock:
            far = place(place(CRANE_WING, 0, 0, 1, -0.3), 0, 0, 0.82, -0.32)
            far = place(far + np.array([-0.02, -0.01]), x, y, span, turn, flip)
            self.polygon(s_draw, far)
            self.polygon(w_draw, place(CRANE_BODY, x, y, span, turn, flip))
            self.polygon(w_draw, place(place(CRANE_WING, 0, 0, 1, -0.3), x, y, span, turn, flip))
            self.polygon(b_draw, place(CRANE_TAIL, x, y, span, turn, flip))
            self.stroke(b_draw, place(place(CRANE_TRAILING, 0, 0, 1, -0.3), x, y, span, turn, flip), span * 0.07, span * 0.05, taper=(0.15, 0.3))
            far_trail = place(place(place(CRANE_TRAILING, 0, 0, 1, -0.3), 0, 0, 0.82, -0.32) + np.array([-0.02, -0.01]), x, y, span, turn, flip)
            self.stroke(f_draw, far_trail, span * 0.06, span * 0.04, taper=(0.15, 0.3))
            self.stroke(b_draw, place(CRANE_NECK, x, y, span, turn, flip), span * 0.035, span * 0.026, taper=(0, 0))
            head = place([(0.425, -0.07)], x, y, span, turn, flip)[0]
            rh = span * 0.024
            b_draw.ellipse([(head[0] - rh) * PX, (head[1] - rh * 0.8) * PX, (head[0] + rh) * PX, (head[1] + rh * 0.8) * PX], fill=255)
            self.stroke(b_draw, place(CRANE_BEAK, x, y, span, turn, flip), span * 0.014, span * 0.004, taper=(0, 0.3))
            for leg in CRANE_LEGS:
                self.stroke(b_draw, place(leg, x, y, span, turn, flip), span * 0.012, span * 0.008, taper=(0, 0.1))
            crown = place([(0.42, -0.083)], x, y, span, turn, flip)[0]
            rc = span * 0.012
            r_draw.ellipse([(crown[0] - rc) * PX, (crown[1] - rc) * PX, (crown[0] + rc) * PX, (crown[1] + rc) * PX], fill=255)
        near = self.mask(white)
        far_wing = self.mask(shade) * (1 - near)
        ink = np.clip(self.mask(black) + self.mask(far_black) * self.mask(shade) * (1 - near), 0, 1)
        self.pigment(far_wing, GOFUN * 0.86)
        self.pigment(near * (1 - ink), GOFUN)
        self.outline(np.clip(near + far_wing + ink, 0, 1), 0.5, 0.3)
        self.ink(self.brush(ink, 0.95))
        self.pigment(self.mask(red), SHU, body=0.02)

    def maples(self, leaves, seed):
        """Maple leaves floating on the water, each x, y, size (mm) and turn: seven pointed, toothed lobes in red and
        ochre, some in gold leaf, a stem and pale veins."""
        rng = np.random.default_rng(seed)
        for x, y, size, turn in leaves:
            angles = np.radians([-128, -86, -43, 0, 43, 86, 128])
            lengths = np.array([0.5, 0.78, 0.95, 1.0, 0.95, 0.78, 0.5])
            pts = []
            # Along a lobe, how far out and how far to either side: broad at the base, narrowing to a point, toothed.
            side = [(0.34, -0.13), (0.42, -0.17), (0.52, -0.19), (0.6, -0.17), (0.68, -0.16), (0.76, -0.12), (0.83, -0.10), (0.9, -0.06), (1.0, 0.0)]
            for i, (a, L) in enumerate(zip(angles, lengths)):
                ux, uy = math.sin(a), -math.cos(a)
                lobe = side + [(u, -v) for u, v in side[-2::-1]]
                for k, (u, v) in enumerate(lobe):
                    tooth = 0.025 * (1 if k % 2 else -1) if 0.4 < u < 0.98 else 0.0
                    v = v + tooth * np.sign(v)
                    pts.append((L * (u * ux - v * uy), L * (u * uy + v * ux)))
            leaf = place(pts, x, y, size, turn)
            img, draw = self.canvas()
            self.polygon(draw, leaf)
            m = self.mask(img)
            if rng.random() < 0.25:
                self.lay_metal(m, GOLD, 0.34, self.cached("crinkle", lambda: self.noise(0.3, 2.5)))
            else:
                self.pigment(m, MOMIJI[rng.integers(len(MOMIJI))], vary=0.12)
            img, draw = self.canvas()
            for a, L in zip(angles, lengths):
                self.stroke(draw, place([(0, 0), (0.7 * L * math.sin(a), -0.7 * L * math.cos(a))], x, y, size, turn), 0.35, 0.1, taper=(0, 0.3))
            self.pigment(self.mask(img) * m * 0.45, GOFUN * 0.85 + MOMIJI[3] * 0.15, body=0.0)
            img, draw = self.canvas()
            self.stroke(draw, place([(0, 0), (0.06, 0.28), (0.02, 0.55)], x, y, size, turn), 0.55, 0.3, taper=(0, 0.1))
            self.pigment(self.mask(img), MOMIJI[2] * 0.7)

    def cherry(self, branches, blossoms, buds, seed):
        """A branch of mountain cherry in flower: the branches in sumi with a little brown, wet ink run into them and
        dots of moss in malachite; the blossoms five petals of shell white, pink at the heart, gold at the stamens."""
        rng = np.random.default_rng(seed)
        img, draw = self.canvas()
        moss, m_draw = self.canvas()
        for points, w0, w1 in branches:
            self.stroke(draw, points, w0, w1, taper=(0.0, 0.25))
            path = catmull(points, 2.0)
            for x, y in path[rng.random(len(path)) < 0.35]:
                r = rng.uniform(0.35, 0.9) * max(w0 * 0.25, 0.5)
                m_draw.ellipse([(x - r) * PX, (y - r) * PX, (x + r) * PX, (y + r) * PX], fill=255)
        # Wet ink: a second, paler ink dropped into the first while it was wet, drying in blooms with dark rims.
        a = self.warp(self.mask(img), 0.08, 0.8)
        pool = np.clip(a - ndimage.gaussian_filter(a, 0.35 * PX), 0, 1)
        bloom = np.clip(0.5 + 0.4 * self.noise(5, 25), 0, 1)
        self.ink(np.clip(a * (0.74 + 0.18 * bloom) + 0.4 * pool, 0, 1), BARK)
        self.pigment(self.mask(moss) * 0.85, ROKUSHO, body=0.02)
        petals, p_draw = self.canvas()
        heart, h_draw = self.canvas()
        stamen, s_draw = self.canvas()
        for x, y, r, turn in blossoms:
            for k in range(5):
                a = turn + k * 2 * math.pi / 5
                ts = np.linspace(0, 1, 14)
                half = 0.42 * np.sin(np.pi * np.clip(ts * 0.95, 0, 1)) ** 0.55
                left = [(-h, t) for h, t in zip(half, ts)]
                right = [(h, t) for h, t in zip(half[::-1], ts[::-1])]
                shape = left[:-1] + [(-0.1, 0.99), (0.0, 0.9), (0.1, 0.99)] + right[1:]
                self.polygon(p_draw, place(shape, x, y, r, a + math.pi))
            for i in range(10, 0, -1):
                rr = r * 0.5 * i / 10
                h_draw.ellipse([(x - rr) * PX, (y - rr) * PX, (x + rr) * PX, (y + rr) * PX], fill=int(255 * (1 - i / 11) ** 0.6))
            for k in range(11):
                a = turn + k * 2 * math.pi / 11 + rng.normal(0, 0.1)
                L = r * rng.uniform(0.38, 0.55)
                tip = (x + L * math.cos(a), y + L * math.sin(a))
                self.stroke(s_draw, [(x, y), tip], 0.18, 0.12, taper=(0, 0))
                rd = 0.32
                s_draw.ellipse([(tip[0] - rd) * PX, (tip[1] - rd) * PX, (tip[0] + rd) * PX, (tip[1] + rd) * PX], fill=255)
        for x, y, r, turn in buds:
            pts = [(0.3 * math.sin(t), -0.5 * math.cos(t) - 0.1 * math.cos(t) ** 2) for t in np.linspace(0, 2 * np.pi, 24, endpoint=False)]
            self.polygon(p_draw, place(pts, x, y, r, turn))
            self.polygon(h_draw, place(pts, x, y, r * 0.8, turn), fill=200)
        petal = self.mask(petals)
        self.pigment(petal, GOFUN, body=0.035)
        self.pigment(petal * self.mask(heart, 1.2) * 0.85, SAKURA, body=0.0)
        self.outline(petal, 0.28, 0.25)
        self.gilt(self.mask(stamen, 0.4))

    def falling(self, region, count, seed, size=(2.6, 4.2)):
        """Single petals falling, painted, scattered over region (x0, y0, x1, y1 mm)."""
        rng = np.random.default_rng(seed)
        img, draw = self.canvas()
        x0, y0, x1, y1 = region
        ts = np.linspace(0, 1, 12)
        half = 0.42 * np.sin(np.pi * np.clip(ts * 0.95, 0, 1)) ** 0.55
        shape = [(-h, t - 0.5) for h, t in zip(half, ts)][:-1] + [(-0.1, 0.49), (0.0, 0.4), (0.1, 0.49)] + [(h, t - 0.5) for h, t in zip(half[::-1], ts[::-1])][1:]
        for _ in range(count):
            self.polygon(draw, place(shape, rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(*size), rng.uniform(0, 2 * math.pi)))
        m = self.mask(img)
        self.pigment(m, GOFUN, body=0.02)
        self.pigment(m * 0.4, SAKURA, body=0.0)
        self.outline(m, 0.22, 0.2)

    def susuki(self, stems, seed, density=0.55):
        """Autumn pampas grass drawn in gold under the writing (shita-e): long blades and drooping plumes."""
        rng = np.random.default_rng(seed)
        img, draw = self.canvas()
        for x, top, bottom, lean in stems:
            pts = [(x, bottom), (x + lean * 0.3, bottom - (bottom - top) * 0.4), (x + lean * 0.75, bottom - (bottom - top) * 0.8), (x + lean, top)]
            self.stroke(draw, pts, 0.5, 0.15, taper=(0, 0.3))
            for _ in range(7):
                a = rng.uniform(0.3, 1.1) * np.sign(lean or 1)
                L = rng.uniform(8, 16)
                sx, sy = x + lean, top
                self.stroke(draw, [(sx, sy), (sx + L * 0.5 * math.sin(a), sy + L * 0.25), (sx + L * math.sin(a) * 0.8, sy + L * 0.75)], 0.35, 0.1, taper=(0, 0.4))
            for _ in range(3):
                side = rng.choice([-1, 1])
                L = rng.uniform(30, 60)
                y0 = bottom - rng.uniform(0, 12)
                self.stroke(draw, [(x, y0), (x + side * L * 0.3, y0 - L * 0.55), (x + side * L * 0.75, y0 - L * 0.7)], 0.9, 0.12, taper=(0, 0.5))
        self.gilt(self.mask(img) * density)

    def shippo(self, region, s=11.0):
        """Linked rings printed in mica (shippō), where region is."""
        best = np.full(self.y.shape, np.inf, np.float32)
        for ox, oy in ((0, 0), (s / 2, s / 2)):
            cx = np.round((self.x - ox) / s) * s + ox
            cy = np.round((self.y - oy) / s) * s + oy
            best = np.minimum(best, np.abs(np.hypot(self.x - cx, self.y - cy) - s / math.sqrt(2) / 1.0 * 0.72))
        m = ndimage.gaussian_filter((best < 0.32).astype(np.float32), 0.6) * region
        m *= np.clip(0.75 + 0.35 * self.noise(0.4, 3), 0, 1)
        self.coat = np.maximum(self.coat, m)
        self.albedo = self.albedo * (1 + 0.07 * m[..., None])
        self.rough -= 0.25 * m

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
    """The poem's page, its gutter at its left edge: a weeping cherry in flower hanging in from the top right and
    dropping its petals down through the poem, a moon in silver behind a band of gold mist, and below, the indigo
    sheet as a river carrying maple leaves."""
    p = Page(*PAGE, seed=11)
    p.washi()
    river = p.joined(INDIGO, [(0, 198), (60, 206), (125, 230), (205, 216)], below=True, seed=4)
    p.shippo(river)
    p.dust((60, 4, 230, 34), seed=8, density=14)
    p.moon(31, 50, 19)
    p.kasumi([(-10, 74, 64, 9), (8, 58, 74, 6)], seed=3)
    p.dust((-20, 52, 90, 84), seed=10, density=10)
    p.water((0, 228, 205, 283), 7, seed=15)
    p.maples([(66, 247, 13, 0.4), (96, 266, 11, -0.6), (128, 243, 12, 1.2), (160, 270, 14, 2.4), (186, 246, 10, -1.8), (124, 280, 9, 0.9), (54, 276, 10, -2.6), (198, 278, 11, 0.2)], seed=16)
    p.leaf([(120, 214, 16, 18), (192, 262, 10, 10), (30, 100, 9, 8)], seed=12)
    branches = [
        ([(214, 4), (196, 12), (180, 20), (166, 22), (150, 17), (134, 21), (120, 15)], 5.2, 1.0),
        ([(180, 20), (184, 30), (186, 48), (190, 70), (191, 96), (189, 124)], 1.6, 0.4),
        ([(196, 12), (199, 34), (201, 62), (200, 88)], 1.4, 0.4),
        ([(166, 22), (170, 36), (174, 52), (176, 74)], 1.2, 0.35),
        ([(150, 17), (146, 8), (140, 2)], 1.4, 0.5),
        ([(134, 21), (128, 32), (118, 38)], 1.0, 0.35),
    ]
    blossoms = [(176, 13, 5.2, 0.2), (160, 27, 4.8, 1.1), (143, 12, 4.6, 0.6), (126, 26, 4.4, 2.0), (118, 39, 4.0, 0.3), (192, 22, 4.6, 1.6), (187, 40, 4.2, 0.9), (190, 60, 4.0, 2.2), (191, 82, 3.8, 0.5), (189, 104, 3.6, 1.4), (200, 44, 4.0, 2.6), (201, 72, 3.6, 0.1), (172, 44, 4.0, 1.9), (176, 66, 3.6, 0.7), (205, 22, 4.4, 1.2), (157, 9, 4.2, 2.4)]
    buds = [(189, 122, 3.0, 0.2), (200, 90, 2.8, -0.2), (177, 77, 2.6, 0.1), (139, 2, 2.6, -0.5), (186, 92, 2.4, 0.3), (182, 52, 2.4, -0.4)]
    p.cherry(branches, blossoms, buds, seed=17)
    p.falling((60, 40, 200, 200), 14, seed=18)
    p.poem(right=150, top=50, pitch=24, em=16, starts=[0, 1.7, 0.6, 2.8, 1.2], sizes=[1, 0.94, 1, 0.9, 1])
    p.signature(x=29, bottom=214, em=8.2)
    p.seal(22.5, 222, 13.5)
    return p


def left_page():
    """The reading's page, its gutter at its right edge: cranes flying over the wisteria sheet, a band of gold mist
    under them, pampas grass drawn in gold behind the writing, and at its foot Mount Fuji rising out of mist over
    water, with plovers flying low over it."""
    p = Page(*PAGE, seed=21)
    p.washi()
    p.joined(WISTERIA, [(0, 74), (70, 64), (140, 81), (205, 68)], below=False, seed=6, mica=True)
    p.dust((-30, 2, 140, 30), seed=23, density=10)
    p.kasumi([(-10, 112, 88, 8), (30, 96, 99, 5)], seed=7)
    p.susuki([(176, 120, 236, 10), (186, 104, 238, -6), (166, 140, 236, 14), (196, 128, 240, 4)], seed=24)
    p.fuji(158, 226, 266, 52)
    p.kasumi([(-10, 160, 254, 9), (96, 215, 262, 6)], seed=9)
    p.dust((-30, 240, 140, 266), seed=13, density=12)
    p.water((0, 266, 205, 284), 4, seed=25, silver=True)
    p.plovers([(24, 242, 9, 0.1, False), (46, 233, 8, -0.15, False), (68, 245, 8.5, 0.05, False), (88, 236, 7, 0.2, False)])
    p.leaf([(14, 170, 8, 6), (190, 160, 8, 6)], seed=22)
    p.cranes([(46, 36, 52, -0.12, False), (112, 21, 42, 0.06, False), (164, 48, 34, -0.2, False)])
    x = 44
    p.text(READING, x, 112, 8.4, 12.8, prefix="reading")
    p.text([SOURCE], x, 164, 5.8, 0, density=0.6, prefix="source")
    p.rule(x, 181, x + 30, 0.6)
    p.text(p.wrap(MESSAGE, 6.8, 205 - x - 26), x, 198, 6.8, 9.6, font=SERIF_MEDIUM, prefix="message")
    p.links(x, 217, 6.8, 12)
    return p


def loose_page():
    """One page of the book on its own, for a tall window: the cherry and the moon over the poem, Mount Fuji in mist
    between the poem and the reading, pampas grass in gold beside the reading, and the river of maple leaves at its foot."""
    p = Page(160.0, 335.0, seed=31)
    p.washi()
    p.joined(WISTERIA, [(0, 17), (60, 24), (110, 15), (160, 21)], below=False, seed=7, mica=True)
    river = p.joined(INDIGO, [(0, 312), (50, 304), (115, 316), (160, 307)], below=True, seed=5)
    p.shippo(river)
    p.moon(22, 50, 14)
    p.kasumi([(-10, 52, 62, 7)], seed=3)
    p.fuji(112, 160, 194, 46)
    p.kasumi([(-10, 120, 186, 8), (60, 170, 192, 5)], seed=9)
    p.dust((-30, 168, 120, 196), seed=19, density=9)
    p.water((0, 312, 160, 334), 4, seed=15)
    p.maples([(40, 322, 10, 0.4), (78, 327, 9, -0.6), (112, 320, 10, 1.2), (146, 326, 9, 2.4)], seed=16)
    p.leaf([(98, 160, 8, 6), (14, 230, 8, 6)], seed=32)
    branches = [
        ([(166, 3), (152, 12), (138, 17), (122, 14), (108, 18), (94, 13)], 4.4, 0.9),
        ([(152, 12), (150, 28), (151, 48), (150, 74), (148, 96)], 1.4, 0.35),
        ([(138, 17), (141, 32), (142, 52)], 1.1, 0.35),
        ([(122, 14), (118, 6), (112, 1)], 1.2, 0.45),
    ]
    blossoms = [(144, 8, 4.4, 0.2), (130, 22, 4.2, 1.1), (114, 8, 4.0, 0.6), (98, 22, 3.8, 2.0), (156, 20, 4.0, 1.6), (149, 38, 3.8, 0.9), (152, 60, 3.6, 2.2), (149, 82, 3.4, 0.5), (142, 42, 3.4, 1.9), (160, 34, 3.8, 1.2)]
    buds = [(148, 98, 2.6, 0.1), (142, 55, 2.4, -0.2), (111, 1, 2.4, -0.5)]
    p.cherry(branches, blossoms, buds, seed=17)
    p.falling((40, 30, 156, 150), 8, seed=18, size=(2.2, 3.6))
    p.susuki([(146, 214, 292, -8), (154, 230, 294, -4), (138, 238, 292, 6)], seed=34)
    p.plovers([(130, 297, 7, 0.1, False), (146, 289, 6, -0.1, False)])
    p.poem(right=126, top=36, pitch=20, em=14, starts=[0, 1.7, 0.6, 2.8, 1.2], sizes=[1, 0.94, 1, 0.9, 1])
    p.signature(x=24, bottom=150, em=7.2)
    p.seal(18, 157, 11.5)
    x = 18
    p.text(READING, x, 210, 7.2, 11.0, prefix="reading")
    p.text([SOURCE], x, 255, 5.0, 0, density=0.6, prefix="source")
    p.rule(x, 266, x + 26, 0.55)
    p.text(p.wrap(MESSAGE, 6.1, 160 - 2 * x), x, 280, 6.1, 8.6, font=SERIF_MEDIUM, prefix="message")
    p.links(x, 299, 6.1, 9)
    return p


PLATES = {
    # px across and down, and how many mm of the set the frame takes in across and down: the book, and a little of
    # the dark cloth it lies on, which the page carries on out to the window's edges.
    "wide": {"px": [3000, 2056], "frame": [470.0, 322.0], "pages": {"left": left_page, "right": right_page}},
    "tall": {"px": [1500, 3000], "frame": [176.0, 352.0], "pages": {"loose": loose_page}},
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
    # The cloth eases to one flat colour at the frame's edges, so the page can carry it on out to the window's.
    band = int(min(h, w) * 0.03)
    rim = np.concatenate([out[:band].reshape(-1, 3), out[-band:].reshape(-1, 3), out[:, :band].reshape(-1, 3), out[:, -band:].reshape(-1, 3)]).mean(0)
    inset = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)) / (min(h, w) * 0.06)
    keep = np.clip(inset, 0, 1) ** 1.5
    out = out * keep[..., None] + rim * (1 - keep[..., None])
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
