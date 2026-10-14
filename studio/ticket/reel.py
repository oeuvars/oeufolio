# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "OpenEXR>=3.3", "scipy"]
# ///
"""What is on the old film that lies down the contact strip, before it is laid out: a black and white 35 mm positive
print, frame after frame, as a map of how much light each point of it lets through.

    uv run studio/ticket/reel.py [--proof DIR]

The film is the standard's: 35 mm wide, four perforations to a frame, a frame every 19 mm. Each frame is the picture
river.py renders, seen as the print stock sees it: the bright sky nearly clear, the steel of the bridge dense silver.
The shots run four to six frames each, the camera drifting a little from one to the next, as frames of a film do.
Between frames the frame line is black; down the left of the picture runs the optical soundtrack, a clear wavering
band in black; outside the perforations the base is clear but for the edge codes printed on the stock.

It has been run through projectors for years: the silver is grainy, no two frames are printed quite as dense,
long scratches run down it where it was dragged through a gate, some cut into the emulsion and clear, some in the
base and dark, and there is dust on it, dark where it is dirt on this print and clear where it was dirt on the
negative it was printed from. A hair lies across one frame.

Writes studio/ticket/art/reel.png, how much light gets through (16 bit, 1 is clear base), and reel-holes.png, the
perforations, along the film from its head at the top, at PX_PER_EM.
"""

import argparse
import os

import numpy as np
import OpenEXR
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "art")
PX_PER_EM = 96
WIDTH = 4.4  # the film's width in em: 35 mm
MM = WIDTH / 35
FRAMES = 24
PITCH = 19 * MM  # a frame
LENGTH = FRAMES * PITCH
# The perforations: 2.8 by 1.98 mm, four to a frame, their centres 3.41 mm in from either edge.
PERF = (2.8 * MM, 1.98 * MM, 4.75 * MM, 3.41 * MM)
PICTURE = (9.2 * MM, 29.8 * MM, 15.6 * MM)  # left and right edges of the picture, and its height
TRACK = (6.6 * MM, 8.8 * MM)  # the soundtrack's left and right edges
# The shots, in order: which render, how many frames, and how far the camera drifts over them, as a fraction of the
# frame across and down.
SHOTS = (("river", 6, (0.04, 0.0)), ("river-boat", 5, (-0.03, 0.01)), ("river-span", 5, (0.02, -0.01)), ("river-tower", 4, (0.0, 0.03)), ("river", 4, (0.03, 0.0)))
TINT = 0.72  # how much light the clear base and its fog let through: old acetate is greyed
DENSE = 0.02  # how much the densest silver lets through


def passes(path):
    found = {}
    for part in OpenEXR.File(path, separate_channels=True).parts:
        for name, channel in part.channels.items():
            found[name.split(".", 1)[1]] = channel.pixels.astype(np.float64)
    return found


def field(shape, seed, sigma):
    n = ndimage.gaussian_filter(np.random.default_rng(seed).standard_normal(shape), sigma)
    return n / max(n.std(), 1e-9)


def smooth(lo, hi, x):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def tone(view):
    """A render as the print shows it: how bright each point of the scene is, through the print stock's steep curve."""
    p = passes(os.path.join(ART, f"{view}.exr"))
    lum = 0.2126 * p["Combined.R"] + 0.7152 * p["Combined.G"] + 0.0722 * p["Combined.B"]
    lum = np.clip(lum, 0, 1) ** (1 / 2.2)
    lum = (lum - np.percentile(lum, 1)) / max(1e-6, np.percentile(lum, 99.5) - np.percentile(lum, 1))
    return smooth(0.0, 1.0, np.clip(lum, 0, 1))


def frame(picture, w, h, drift, t):
    """One frame of a shot, t of the way through it: the render cut to the frame's shape, a little in from its edges
    so the camera can drift, and drifted t of the way."""
    rows, cols = picture.shape
    if cols / rows > w / h:
        ch, cw = rows * 0.9, rows * 0.9 * w / h
    else:
        cw, ch = cols * 0.9, cols * 0.9 * h / w
    x0 = (cols - cw) / 2 + drift[0] * cols * (t - 0.5)
    y0 = (rows - ch) / 2 + drift[1] * rows * (t - 0.5)
    box = (round(x0), round(y0), round(x0 + cw), round(y0 + ch))
    img = Image.fromarray((picture * 65535).astype(np.uint16)).crop(box).resize((w, h), Image.Resampling.LANCZOS)
    return np.asarray(img, dtype=np.float64) / 65535


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof")
    args = parser.parse_args()

    k = PX_PER_EM
    rows, cols = round(LENGTH * k), round(WIDTH * k)
    Y, X = np.mgrid[0:rows, 0:cols].astype(np.float64) / k
    rng = np.random.default_rng(3)
    light = np.full((rows, cols), TINT)
    silver = np.zeros((rows, cols))  # how dense the silver is, 0 to 1, before it is turned into light let through

    # The frames: a black frame line between each, the picture inside.
    left, right, tall = PICTURE
    pw, ph = round((right - left) * k), round(tall * k)
    pictures = {}
    n = 0
    for view, count, drift in SHOTS:
        if view not in pictures:
            pictures[view] = tone(view)
        for i in range(count):
            top = n * PITCH
            r0, c0 = round(top * k), round(left * k)
            r1 = round((top + PITCH) * k)
            silver[r0:r1, c0 : c0 + pw] = 1.0
            image = frame(pictures[view], pw, ph, drift, i / max(1, count - 1))
            # No two frames printed quite alike.
            flicker = rng.normal(0, 0.04)
            pr = r0 + round((PITCH - tall) / 2 * k)
            silver[pr : pr + ph, c0 : c0 + pw] = np.clip(1 - image + flicker, 0, 1)
            n += 1

    # The soundtrack: black, with a clear band down its middle that swells and shrinks with the sound.
    t0, t1 = TRACK
    middle, half = (t0 + t1) / 2, (t1 - t0) / 2
    sound = field((rows,), 5, 0.6 * k * 0.02) * 0.5 + field((rows,), 6, 0.08 * k) * 0.35
    quiet = smooth(-0.6, 0.4, field((rows,), 7, 1.2 * k))
    width = np.clip(0.12 + 0.75 * np.abs(sound) * quiet, 0.04, 0.95) * half
    inside = (X >= t0) & (X <= t1)
    silver[inside] = 1.0
    clear = np.abs(X - middle) < width[:, None]
    silver[inside & clear] = 0.0

    # The edge codes printed on the stock, outside the perforations on the right: a dash and a run of dots every
    # sixteen frames.
    for f in range(0, FRAMES, 4):
        y = f * PITCH + 0.3
        x = WIDTH - 0.13
        for j, size in enumerate((0.16, 0.05, 0.05, 0.05, 0.09, 0.05)):
            yy = y + j * 0.11 + (0.05 if j else 0)
            mark = (np.abs(X - x) < 0.025) & (Y >= yy) & (Y < yy + size)
            silver[mark] = 0.9

    # Grain: the silver is clumped, most of all in the mid tones. Where there is no silver there is no grain.
    grain = field((rows, cols), 11, 0.55) * 0.09 + field((rows, cols), 12, 1.4) * 0.03
    silver = np.clip(silver + grain * np.sqrt(silver) * (0.25 + silver * (1 - silver) * 2.5), 0, 1)

    # Scratches down the length, where the film was dragged through a gate: a few long ones that wander a little.
    for s in range(7):
        x0 = rng.uniform(0.3, WIDTH - 0.3)
        wander = field((rows,), 20 + s, 3 * k) * 0.02
        line = np.exp(-(((X - x0 - wander[:, None]) * k / rng.uniform(0.5, 1.1)) ** 2))
        start, stop = sorted(rng.uniform(0, LENGTH, 2))
        if rng.random() < 0.4:
            start, stop = 0, LENGTH
        line *= smooth(start, start + 0.3, Y) * (1 - smooth(stop - 0.3, stop, Y))
        line *= smooth(-0.3, 0.6, field((rows,), 40 + s, 0.4 * k))[:, None]
        if s % 3 == 0:
            light *= 1 - 0.35 * line  # in the base, which is dulled and darkened
        else:
            silver *= 1 - 0.9 * line  # through the emulsion, so the silver is gone along it

    # Dust: dark where it is dirt on this print, clear where it was dirt on the negative.
    specks = ndimage.gaussian_filter((rng.random((rows, cols)) > 0.9999).astype(np.float64), 0.9) * 30
    silver = np.clip(silver + np.clip(specks, 0, 1), 0, 1)
    holes = ndimage.gaussian_filter((rng.random((rows, cols)) > 0.99988).astype(np.float64), 1.1) * 30
    silver *= 1 - np.clip(holes, 0, 1)
    # A hair, caught on the negative, lying across the sixth frame.
    u = np.linspace(0, 1, 400)
    hx = 1.6 + 1.6 * u + 0.12 * np.sin(u * 7)
    hy = 5.3 * PITCH + 0.4 + 0.9 * u + 0.1 * np.sin(u * 11)
    hair = np.zeros((rows, cols))
    for x, y in zip(hx, hy):
        r, c = int(y * k), int(x * k)
        if 0 <= r < rows and 0 <= c < cols:
            hair[r, c] = 1
    hair = np.clip(ndimage.gaussian_filter(hair, 0.6) * 6, 0, 1)
    silver *= 1 - hair

    # How much light gets through: the clear base's, cut down by the silver's density, logarithmically.
    density = silver * -np.log10(DENSE / TINT)
    light = light * 10.0 ** (-density)

    # The perforations, with their corners eased.
    pw_, ph_, pitch, inset = PERF
    py = (Y + pitch / 2) % pitch - pitch / 2
    perfs = np.zeros((rows, cols))
    for cx in (inset, WIDTH - inset):
        dx = np.clip(np.abs(X - cx) - (pw_ / 2 - 0.5 * MM), 0, None)
        dy = np.clip(np.abs(py) - (ph_ / 2 - 0.5 * MM), 0, None)
        perfs = np.maximum(perfs, np.clip((0.5 * MM - np.hypot(dx, dy)) * k + 0.5, 0, 1))

    Image.fromarray((np.clip(light, 0, 1) * 65535).astype(np.uint16)).save(os.path.join(ART, "reel.png"))
    Image.fromarray((perfs * 255).astype(np.uint8)).save(os.path.join(ART, "reel-holes.png"))
    if args.proof:
        view = np.clip(light, 0, 1) ** (1 / 2.2) * (1 - perfs) + perfs * 0.3
        Image.fromarray((view * 255).astype(np.uint8)).save(os.path.join(args.proof, "reel.png"))
    print(f"film {WIDTH} x {LENGTH:.2f} em, {FRAMES} frames, {cols} x {rows} px")


main()
