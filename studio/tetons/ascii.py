# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""The loader's picture, set in type: the Tetons at dusk, and the PRS birds flying over them. Run from the repository
root:

    uv run studio/tetons/ascii.py [--proof DIR]

The mountains (art/tetons.jpg) are set on three grids of monospaced cells, 200, 300 and 450 across the photograph,
each cell as tall as Menlo's at a line height of one, so the loader can keep its type between about seven and eleven
pixels on any screen. In each cell the photograph's brightness is read at 6 by 10 points and the cell gets the
printable character whose own ink, Menlo's glyph drawn into the same cell, comes closest to it, point for point: so a
ridge takes the slashes and underscores that run its way, snow takes the dense letters and the dark flats the dots. A
little noise is added before each match so a flat sky is not one character over and over. Each cell also keeps how
bright the photograph is there, as one of sixteen steps, and the colour the photograph has at that brightness, so the
type is coloured as the picture is.

The birds (art/prs-birds.png) are the nine of PRS's bird inlays, turned upright as if seen from below in flight, those
that look left turned to look right and all leaned a little into their flight, set the same way at a few heights, with
a slow wave of brightness across each for the figure of the pearl.

Writes public/loader/tetons.txt, which the loader fetches:

    BACKGROUND and the sixteen colours, darkest first
    then for each grid, COLS ROWS, its rows of characters, and its rows of brightness steps in hex

and src/components/loader/birds.txt, which it carries inline:

    for each bird at each height, BIRD ROWS COLS, and its rows of characters

With --proof, each grid and the birds are also set in Menlo as PNGs in DIR, to look at.
"""

import argparse
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PHOTO = os.path.join(HERE, 'art', 'tetons.jpg')
BIRDS = os.path.join(HERE, 'art', 'prs-birds.png')
OUT = os.path.join(ROOT, 'public', 'loader', 'tetons.txt')
BIRDS_OUT = os.path.join(ROOT, 'src', 'components', 'loader', 'birds.txt')
FONT = '/System/Library/Fonts/Menlo.ttc'

GRIDS = (200, 300, 450)
ADVANCE = 0.602
SUB = (6, 10)
CHARS = [chr(c) for c in range(32, 127) if chr(c) != '<']
LEVELS = 16
# The colours: how much bluer than the photograph, and the pale they are lifted toward.
SATURATE = 1.5
PALE = (214, 232, 255)
# The night the type is set on.
BACKGROUND = '#04080e'
# Brightness, from the photograph's brightest channel. Its sky is flat and as bright as the snow, so it is set apart
# and laid as a calm field of colons in its own colour, lighter than the rock and darker than the snow, as in the
# picture; the mountains are read from DARK to LIGHT with their local contrast raised, so snow stands off rock.
DARK, LIGHT = 34, 168
SKY_TONE = 0.45
CONTRAST = 1.2
# The ramp of characters from bare to full, re-sorted by Menlo's own ink.
BOURKE = " .,:;-~=+*xoe%#&@"
STEPS = 17
# Where the sky meets the mountains, the cell draws the ridge instead: a stroke the way it runs.
STROKES = '-\\|/'
# How much noise is added to each cell's tone, so a flat sky is not one character over and over.
DITHER = 0.035
# The sky's mark, and now and then another.
SKY = ':'
SKY_ELSE = ".:'.-"
SKY_ODD = 0.07
# The birds: their heights, in rows; which look left and are turned; how far they lean into their flight, in degrees.
HEIGHTS = (5, 8, 12, 17)
LEFTWARD = (5, 6, 7)
LEAN = 14


def glyphs():
    """Each character's ink in a cell, at SUB points, from Menlo drawn large with the baseline where CSS puts it at a
    line height of one."""
    em = 200
    font = ImageFont.truetype(FONT, em)
    ascent, descent = font.getmetrics()
    baseline = (em - (ascent + descent)) / 2 + ascent
    w, h = round(em * ADVANCE), em
    maps = []
    for char in CHARS:
        image = Image.new('L', (w, h), 0)
        ImageDraw.Draw(image).text((0, baseline), char, font=font, fill=255, anchor='ls')
        maps.append(np.asarray(image.resize(SUB, Image.Resampling.BOX)).astype(np.float32) / 255)
    return np.stack(maps)


def cells(values, cols, rows):
    """`values` read at SUB points a cell, as rows x cols x points."""
    sw, sh = SUB
    big = Image.fromarray(values.astype(np.float32), 'F').resize((cols * sw, rows * sh), Image.Resampling.BICUBIC)
    return np.asarray(big).reshape(rows, sh, cols, sw).transpose(0, 2, 1, 3).reshape(rows, cols, -1)


def match(target, maps):
    """The closest character to each cell of `target`, point for point; empty cells stay blank."""
    flat = maps.reshape(len(maps), -1)
    rows, cols, _ = target.shape
    pick = np.empty((rows, cols), np.int64)
    for r in range(rows):
        pick[r] = ((target[r][:, None, :] - flat[None]) ** 2).sum(-1).argmin(-1)
    return pick


def brightness(rgb):
    value = rgb.max(2)
    # The sky: in each column, down to where the picture first parts from the sky's colour.
    colour = np.median(rgb[:40].reshape(-1, 3), 0)
    apart = ndimage.median_filter(np.sqrt(((rgb - colour) ** 2).sum(2)), 3) > 9
    ridge = np.argmax(apart, axis=0)
    sky = np.arange(rgb.shape[0])[:, None] < ridge[None, :]
    detail = value + CONTRAST * (value - ndimage.gaussian_filter(value, 5))
    tone = np.clip((detail - DARK) / (LIGHT - DARK), 0, 1)
    tone = ndimage.gaussian_filter(tone, 0.6)
    tone[sky] = SKY_TONE
    return tone, sky


def ramp(maps):
    """The ramp's characters and how inked each is, lightest first."""
    ink = {CHARS[i]: maps[i].mean() for i in range(len(CHARS))}
    chars = sorted((c for c in dict.fromkeys(BOURKE) if c in ink), key=lambda c: ink[c])
    marks = np.array([ink[c] for c in chars])
    marks = (marks - marks[0]) / (marks[-1] - marks[0])
    picked = [chars[int(np.abs(marks - t).argmin())] for t in np.linspace(0, 1, STEPS)]
    return list(dict.fromkeys(picked))


def palette(rgb, tone):
    """The photograph's colour at each step of brightness, made bluer and lifted toward a pale blue-white the brighter
    the step, so that type, which covers only part of its cell, still reads as the picture does: deep blue below,
    the sky between, the snow palest."""
    steps = np.minimum((tone * LEVELS).astype(int), LEVELS - 1)
    luma = rgb @ np.array([0.299, 0.587, 0.114])
    colours = []
    for s in range(LEVELS):
        pick = steps == s
        mean = rgb[pick].mean(0) if pick.any() else rgb.reshape(-1, 3).mean(0)
        grey = luma[pick].mean() if pick.any() else luma.mean()
        mean = np.clip(grey + (mean - grey) * SATURATE, 0, 255)
        lift = 0.06 + 0.7 * (s / (LEVELS - 1)) ** 1.4
        mean = mean + (np.array(PALE) - mean) * lift
        colours.append('#' + ''.join(f'{round(v):02x}' for v in mean))
    return colours, steps


def mountains(maps, proof):
    rgb = np.asarray(Image.open(PHOTO).convert('RGB')).astype(np.float32)
    height, width = rgb.shape[:2]
    tone, sky = brightness(rgb)
    colours, _ = palette(rgb, tone)
    out = [' '.join([BACKGROUND] + colours)]
    rand = np.random.default_rng(5)
    chars = ramp(maps)
    for cols in GRIDS:
        rows = round(height / (width / cols / ADVANCE))
        sub = cells(tone, cols, rows)
        mean = sub.mean(-1)
        shade = np.clip(mean + rand.normal(0, DITHER, mean.shape), 0, 1)
        pick = np.minimum((shade * len(chars)).astype(int), len(chars) - 1)
        # The ridge: cells partly sky, and which way the sky's edge runs through them.
        sw, sh = SUB
        grid = cells(sky.astype(np.float32), cols, rows).reshape(rows, cols, sh, sw)
        share = grid.mean((-2, -1))
        # Per point across and down, as a cell is taller than it is wide.
        gx = (grid[..., :, sw // 2 :].mean((-2, -1)) - grid[..., :, : sw // 2].mean((-2, -1))) / sw
        gy = (grid[..., sh // 2 :, :].mean((-2, -1)) - grid[..., : sh // 2, :].mean((-2, -1))) / sh
        # The stroke runs across the slope; in a y-down picture, angle 0 is a level edge.
        angle = (np.degrees(np.arctan2(gy, gx)) + 90) % 180
        lines = []
        for r in range(rows):
            line = ''
            for c in range(cols):
                if 0.15 < share[r, c] < 0.85:
                    a = angle[r, c]
                    line += '_' if (a < 22.5 or a >= 157.5) and gy[r, c] < 0 else STROKES[round(a / 45) % 4]
                elif share[r, c] >= 0.85:
                    line += SKY_ELSE[int(rand.random() * len(SKY_ELSE))] if rand.random() < SKY_ODD else SKY
                else:
                    line += chars[pick[r, c]]
            lines.append(line)
        level = np.minimum((sub.mean(-1) * LEVELS).astype(int), LEVELS - 1)
        out.append(f'{cols} {rows}')
        out.extend(lines)
        out.extend(''.join(f'{v:x}' for v in row) for row in level)
        if proof:
            render(lines, [[colours[v] for v in row] for row in level], os.path.join(proof, f'tetons-{cols}.png'))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        f.write('\n'.join(out) + '\n')
    print(f'mountains on {", ".join(map(str, GRIDS))} columns, {os.path.getsize(OUT)} bytes -> {os.path.relpath(OUT, ROOT)}')


def birds(maps, proof):
    strip = np.asarray(Image.open(BIRDS).convert('L')) > 128
    found, count = ndimage.label(strip)
    sizes = ndimage.sum(strip, found, range(1, count + 1))
    shapes = [(box, i + 1) for i, box in enumerate(ndimage.find_objects(found)) if sizes[i] > 200]
    shapes.sort(key=lambda each: each[0][1].start)
    out = []
    proofs = []
    for b, (box, label) in enumerate(shapes):
        mask = Image.fromarray(((found[box] == label) * 255).astype(np.uint8))
        # Upright, as if seen from below, looking right, and leaning into the flight.
        mask = mask.rotate(-90, expand=True)
        if b in LEFTWARD:
            mask = mask.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        mask = mask.resize((mask.width * 4, mask.height * 4), Image.Resampling.LANCZOS)
        mask = mask.rotate(-LEAN, expand=True, resample=Image.Resampling.BICUBIC)
        ink = np.asarray(mask).astype(np.float32) / 255
        ys, xs = np.nonzero(ink > 0.05)
        ink = ink[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
        for rows in HEIGHTS:
            sw, sh = SUB
            cols = max(1, round(ink.shape[1] / ink.shape[0] * rows * sh / sw))
            sub = cells(ink, cols, rows)
            # The pearl's figure: a slow wave of brightness across the bird.
            r, c = np.mgrid[0:rows, 0:cols]
            sheen = 0.78 + 0.22 * np.sin((c * 0.9 + r * 1.7) / max(rows, 4) * 3)
            target = np.clip(sub * sheen[..., None], 0, 1)
            pick = match(target, maps)
            lines = [''.join(CHARS[i] if sub[y, x].mean() > 0.08 else ' ' for x, i in enumerate(row)).rstrip() for y, row in enumerate(pick)]
            out.append(f'{b} {rows} {cols}')
            out.extend(lines)
            if rows == HEIGHTS[-1]:
                proofs.append(lines)
    with open(BIRDS_OUT, 'w') as f:
        f.write('\n'.join(out) + '\n')
    print(f'{len(shapes)} birds at {", ".join(map(str, HEIGHTS))} rows, {os.path.getsize(BIRDS_OUT)} bytes -> {os.path.relpath(BIRDS_OUT, ROOT)}')
    if proof:
        lines = []
        for bird in proofs:
            lines.extend(bird + [''])
        render(lines, None, os.path.join(proof, 'birds.png'), ink='#eef2f4')


def render(lines, colours, path, ink=None):
    size = 14
    font = ImageFont.truetype(FONT, size)
    cell = size * ADVANCE
    w = round(max(len(line) for line in lines) * cell) + 1
    image = Image.new('RGB', (w, len(lines) * size), BACKGROUND)
    draw = ImageDraw.Draw(image)
    ascent, descent = font.getmetrics()
    baseline = (size - (ascent + descent)) / 2 + ascent
    for r, line in enumerate(lines):
        for c, char in enumerate(line):
            if char != ' ':
                draw.text((c * cell, r * size + baseline), char, font=font, fill=ink or colours[r][c], anchor='ls')
    image.save(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--proof')
    args = parser.parse_args()
    if args.proof:
        os.makedirs(args.proof, exist_ok=True)
    maps = glyphs()
    mountains(maps, args.proof)
    birds(maps, args.proof)


if __name__ == '__main__':
    main()
