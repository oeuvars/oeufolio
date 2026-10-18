# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "OpenEXR>=3.3", "scipy"]
# ///
"""Inks the river (studio/ticket/river.py) in the manner of the illustrated cinema tickets the page
follows: a pen drawing with the weight of a woodcut.

    uv run studio/ticket/ink.py [--proof DIR]

The sky is ruled in loose wavy lines, and clouds stand in it as scalloped shapes drawn round with a line, ruled
closer inside and black along their undersides. The steel of the bridge and the piers it stands on, the boat and the
figure under the umbrella are solid black, with a white line cut along the edges that face the light. The banks are a
band of blocks hatched upright. The river is drawn in wavy lines that run close and thin far off and open and heavy
near, thickening where the bridge and the boat are mirrored in it. Rain falls across all of it, black on the white and
white through the black. Nothing is quite straight, as nothing drawn by hand is.

Writes one plate per ink to studio/ticket/art: river-k.png, river-red.png, river-teal.png and river-yellow.png,
white where that ink prints. The picture is printed as a stencil-printed poster is, black over three colours that
overprint and mix: a teal sky going yellow and orange toward a vermilion sun low behind the bridge, teal clouds lit
red from below, a teal river with the sun's road laid across it, and the boat's hood and the umbrella vermilion.
"""

import argparse
import json
import os

import numpy as np
import OpenEXR
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "art")
KIND = {"sky": 0, "steel": 1, "water": 2, "boat": 3, "figure": 4, "city": 5, "pier": 6, "deck": 7}
UP = 2  # drawn at twice the render's size, then brought down, so the lines' edges are clean
PROOF = 700  # the width the measures below were judged at


def passes(path):
    found = {}
    for part in OpenEXR.File(path, separate_channels=True).parts:
        for name, channel in part.channels.items():
            found[name.split(".", 1)[1]] = channel.pixels.astype(np.float64)
    return found


def smooth(lo, hi, x):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def field(shape, seed, sigma):
    """Slow noise of unit deviation, for the hand's unevenness."""
    n = ndimage.gaussian_filter(np.random.default_rng(seed).standard_normal(shape), sigma, mode="wrap")
    return n / n.std()


def lines(phase, cover, soft):
    """Coverage of a screen of lines, one per unit of phase, each as wide as cover of its period. soft is how much
    phase one pixel spans, to antialias with."""
    s = np.abs((phase % 1.0) - 0.5) * 2
    return np.clip((s - (1 - cover)) / np.maximum(soft * 2, 1e-4) + 0.5, 0, 1)


def stroke(mask, width):
    """The outline of a shape, drawn as a line of the given width in pixels."""
    inside = ndimage.distance_transform_edt(mask)
    outside = ndimage.distance_transform_edt(~mask)
    return np.clip(width / 2 + 0.5 - np.where(mask, inside, outside), 0, 1)


def clouds(R, C, horizon, k, seed):
    """Cloud banks as a pen draws them: each a row of round puffs on a flat floor, wider at the base. Returns the
    clouds as a mask, and a field that is 1 along each cloud's floor and fades upward, for the shadow."""
    rng = np.random.default_rng(seed)
    Y, X = np.mgrid[0:R, 0:C].astype(np.float64)
    mask = np.zeros((R, C), dtype=bool)
    under = np.zeros((R, C))
    banks = [(0.16, 0.18, 0.4), (0.74, 0.12, 0.34), (0.47, 0.36, 0.26), (0.9, 0.44, 0.22), (0.1, 0.5, 0.2)]
    for cx, cy, w in banks:
        x0, x1 = (cx - w / 2) * C, (cx + w / 2) * C
        floor = cy * horizon * R
        puffs = int(7 + w * 22)
        for i in range(puffs):
            t = (i + 0.5) / puffs
            px = x0 + (x1 - x0) * t + rng.uniform(-0.012, 0.012) * C
            hump = np.sin(np.pi * t) ** 0.7
            r = (0.012 + 0.04 * hump * rng.uniform(0.55, 1.2)) * C
            py = floor - r * rng.uniform(0.15, 0.7) - 0.02 * hump * C * rng.uniform(0.3, 1.0)
            mask |= ((X - px) ** 2 + (Y - py) ** 2 < r * r) & (Y < floor)
        depth = np.clip(1 - (floor - Y) / (0.022 * C), 0, 1) * ((Y < floor) & (X > x0) & (X < x1))
        under = np.maximum(under, depth)
    return mask, under * mask


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof")
    parser.add_argument("--view", default="river", help="which render to ink: river or river-tower")
    args = parser.parse_args()

    p = passes(os.path.join(ART, f"{args.view}.exr"))
    meta = json.load(open(os.path.join(ART, f"{args.view}.json")))
    rows, cols = p["Combined.R"].shape
    k = cols / PROOF
    lum = 0.2126 * p["Combined.R"] + 0.7152 * p["Combined.G"] + 0.0722 * p["Combined.B"]
    tone = np.clip(lum, 0, 1) ** (1 / 2.2)
    kind = np.rint(p["Object Index.X"]).astype(int)
    haze = np.clip(p["Mist.Z"], 0, 1)
    nx, ny, nz = p["Normal.X"], p["Normal.Y"], p["Normal.Z"]

    def big(a, order=1):
        return ndimage.zoom(a, UP, order=order, mode="nearest")

    tone, haze, nx, ny, nz = big(tone), big(haze), big(nx), big(ny), big(nz)
    kind = big(kind, order=0)
    R, C = tone.shape
    Y, X = np.mgrid[0:R, 0:C].astype(np.float64)
    s = UP * k  # pixels of the block to one pixel of the proof
    # The hand: every line strays a little, slowly.
    wx = field((R, C), 3, 30 * s) * 1.4 * s
    wy = field((R, C), 4, 30 * s) * 1.4 * s
    Xh, Yh = X + wx, Y + wy
    hy = meta["horizon"] * R
    # Four plates, one per ink, each 1 where it prints: black, vermilion, teal and yellow.
    K, RED, TEAL, YEL = (np.zeros((R, C)) for _ in range(4))
    sky = kind == KIND["sky"]
    water = kind == KIND["water"]
    city = kind == KIND["city"]
    boat = kind == KIND["boat"]
    figure = kind == KIND["figure"]

    # The sun, low behind the suspended span, and the light of it.
    sx, sy, sr = 0.6 * C, hy - 0.12 * R, 0.068 * C
    d_sun = np.hypot(X - sx, Y - sy)
    disc = smooth(sr + 0.6 * s, sr - 0.6 * s, d_sun)

    # The sky: teal at the top, yellow lower down going to orange at the horizon, ruled across in teal lines that go
    # green where they cross the yellow, each line running on unbroken until a cloud, the sun or the bridge stops it.
    pitch = 7.5 * s
    wave = 1.6 * s * np.sin(2 * np.pi * Xh / (90 * s) + field((R, C), 5, 80 * s) * 1.2)
    rule = lines((Yh + wave) / pitch, 0.16, 1 / pitch)
    TEAL = np.where(sky, np.maximum(smooth(0.6 * hy, 0.0, Y) * 0.7, rule), TEAL)
    YEL = np.where(sky, np.clip(smooth(0.2 * hy, 0.95 * hy, Y) * 0.9 + 0.6 * np.exp(-((d_sun / (0.28 * C)) ** 2)), 0, 1), YEL)
    RED = np.where(sky, np.clip(smooth(0.62 * hy, hy, Y) * 0.5 + 0.45 * np.exp(-((d_sun / (0.13 * C)) ** 2)), 0, 1), RED)
    RED = np.maximum(RED, disc * sky)
    YEL = YEL * (1 - disc * sky)
    TEAL = TEAL * (1 - disc * sky)

    # Clouds: teal, drawn round and ruled close in black, lit red from below by the sun.
    cloud, under = clouds(R, C, meta["horizon"], k, 11)
    cloud &= sky
    close = lines((Yh + wave * 0.6) / (pitch * 0.5), 0.22, 2 / pitch)
    shade = smooth(0.15, 0.85, under)
    TEAL = np.where(cloud, 0.55 * (1 - shade), TEAL)
    YEL = np.where(cloud, 0.0, YEL)
    RED = np.where(cloud, shade, RED)
    K = np.where(cloud, close * (1 - shade), K)
    K = np.maximum(K, stroke(cloud, 2.2 * s) * sky)

    # The far bank: teal blocks in the haze, hatched upright in black.
    TEAL = np.where(city, 0.75, TEAL)
    YEL = np.where(city, 0.25, YEL)
    K = np.where(city, lines(Xh / (3.0 * s), 0.28, 1 / (3.0 * s)), K)
    K = np.maximum(K, stroke(city, 1.2 * s) * (city | sky))

    # Steel, deck, piers, boat, figure: solid black, a little heavier than the render draws them, as ink spreads.
    solid = np.isin(kind, (KIND["steel"], KIND["deck"], KIND["pier"], KIND["boat"], KIND["figure"]))
    solid = ndimage.binary_dilation(solid, iterations=max(1, round(0.6 * s)))
    K = np.where(solid, 1.0, K)
    pier = kind == KIND["pier"]
    # The boat's hood of matting is vermilion, its ribs black; the umbrella is vermilion too.
    lit = (nx * -0.55 + nz * 0.5 + ny * -0.65) > 0.45
    hood = boat & (nz > 0.25) & lit
    RED = np.where(hood, 1.0, RED)
    K = np.where(hood, lines(Xh / (6.0 * s), 0.3, 1 / (6.0 * s)), K)
    canopy = figure & (nz > 0.3)
    RED = np.where(canopy, 1.0, RED)
    K = np.where(canopy, stroke(canopy, 1.0 * s) * canopy, K)

    # The river: teal, drawn over in black wavy lines, close and fine far off, open and heavy near, thickening where
    # it mirrors something dark. The sun lays a road of yellow and orange across it toward the lens.
    below = np.maximum(Yh - hy, 1.0)
    lap = 0.35 * np.sin(2 * np.pi * Xh / (np.maximum(below, 6 * s) * 2.2) + field((R, C), 7, 25 * s) * 2.2)
    phase = 15.0 * np.log(below / s) + lap
    soft = 15.0 / below
    dark = 1 - tone
    cover = np.clip(0.1 + 0.75 * smooth(0.25, 0.8, dark) + 0.18 * smooth(0, 0.6, below / R), 0, 0.78)
    # The road is the sun caught on the crests between the dark lines. Each ripple's glint runs out at its own length
    # and sits a little to one side of the last, so the road has no straight edge. In it the dark lines thin to half
    # their period, and they thin gradually toward its middle, as the colours grade toward it, the stencil grading
    # each tint in dots: teal into yellow, yellow into orange, orange into vermilion.
    spread = sr * (0.7 + 2.2 * np.clip((Y - hy) / (R - hy), 0, 1))
    ripple = np.clip(np.floor(phase).astype(int) + 64, 0, 255)
    glints = np.random.default_rng(10)
    reach = glints.uniform(0.75, 1.35, 256)[ripple]
    shift = glints.normal(0, 0.12, 256)[ripple]
    across = np.abs((Xh + 0.6 * field((R, C), 9, 6 * s) * s - sx) / spread - shift) / reach
    glow = smooth(1.2, 0.55, across) * water
    cover = cover - (cover - np.minimum(cover, 0.5)) * glow
    river = lines(phase, cover, soft)
    far = smooth(14 * s, 3 * s, below)
    dashes = smooth(-0.1, 0.3, field((R, C), 8, 3 * s)) * smooth(0.2, 0.6, dark + 0.25)
    river = river * (1 - far) + dashes * far * 0.6
    K = np.where(water, river, K)
    crest = lines(phase + 0.5, 0.5, soft) * (1 - far) * water
    YEL = np.where(water, np.maximum(YEL, glow * crest), YEL)
    RED = np.where(water, np.maximum(RED, smooth(0.75, 0.3, across) * crest), RED)
    TEAL = np.where(water, 0.8 * (1 - smooth(1.1, 0.5, across)), TEAL)

    # Rain: short strokes leaning a little left, cut white through every plate.
    rng = np.random.default_rng(21)
    streak = np.zeros((R, C))
    for _ in range(int(R * C / (1300 * s * s))):
        x0, y0 = rng.uniform(0, C), rng.uniform(0, R)
        length = rng.uniform(9, 24) * s
        t = np.linspace(0, 1, int(length))
        px = np.clip((x0 - 0.22 * length * t).astype(int), 0, C - 1)
        py = np.clip((y0 + length * t).astype(int), 0, R - 1)
        streak[py, px] = 1
    streak = ndimage.binary_dilation(streak > 0, iterations=max(1, round(0.55 * s)))
    streak = np.clip(ndimage.gaussian_filter(streak.astype(np.float64), 0.6 * UP), 0, 1)
    cut = streak * (Y < hy + 0.02 * R)  # the river takes the rain as rings, not as streaks

    # The boat and the bridge's piers sit on the water with a line of white between them and their reflections, and the
    # figure and its umbrella are kept apart from the boat behind them by a hairline of white.
    hull = ndimage.binary_dilation(boat | pier, iterations=max(1, round(0.6 * s)))
    waterline = ndimage.binary_dilation(hull, iterations=max(1, round(1.4 * s))) & ~hull & water
    walker = ndimage.binary_dilation(figure, iterations=max(1, round(0.6 * s)))
    halo = ndimage.binary_dilation(walker, iterations=max(1, round(1.3 * s))) & ~walker
    clear = np.maximum(cut, (waterline | halo).astype(np.float64))

    def grain(cover, seed):
        """A flat or graded tint as the stencil prints it: dots of ink, as many as the tint asks for, no greys."""
        noise = ndimage.gaussian_filter(np.random.default_rng(seed).random((R, C)), 0.55 * UP)
        noise = (noise - noise.min()) / (noise.max() - noise.min())
        noise = smooth(0.3, 0.7, noise)
        return np.where(cover > 0.97, 1.0, smooth(-0.05, 0.05, cover - noise))

    plates = {"k": K, "red": grain(RED, 31), "teal": grain(TEAL, 32), "yellow": grain(YEL, 33)}
    ink = {}
    for name, plate in plates.items():
        plate = plate * (1 - clear)
        out = plate.reshape(rows, UP, cols, UP).mean(axis=(1, 3))
        ink[name] = np.clip(out, 0, 1)
        Image.fromarray((ink[name] * 255).astype(np.uint8)).save(os.path.join(ART, f"{args.view}-{name}.png"))
    if args.proof:
        paper = np.array([0.95, 0.92, 0.85])
        colours = {"yellow": (0.97, 0.77, 0.16), "teal": (0.07, 0.5, 0.53), "red": (0.89, 0.25, 0.16), "k": (0.1, 0.09, 0.08)}
        proof = np.ones((rows, cols, 3)) * paper
        for name in ("yellow", "teal", "red", "k"):
            proof *= 1 - ink[name][..., None] * (1 - np.array(colours[name]))
        Image.fromarray((proof * 255).astype(np.uint8)).save(os.path.join(args.proof, f"{args.view}-ink.png"))
    print("inked", cols, "x", rows)

main()
