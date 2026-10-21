# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""What the loader needs to set the Tetons at dusk in type, and the PRS birds flying over them. Run from the
repository root:

    uv run studio/tetons/ascii.py [--proof DIR]

The loader sets the mountains itself, at whatever grid fits the screen, about five pixels a character, so it keeps
as much of the photograph as type can. From here it gets:

- public/loader/tetons.webp: the photograph (art/tetons.jpg) worked over for type, twice as tall as it is. Its top
  half is each point's colour, mapped from its tone through teal, azure and ice, bright, since type covers only part
  of its cell and must still read as the picture does. Its bottom half is each point's tone, which picks
  the character: the photograph's brightest channel with its local contrast raised, so snow stands off rock. The sky,
  flat and as bright as the snow, is given a tone and colour of its own, lower, so the peaks stand against it.
- public/loader/tetons.txt: the night the type is set on; the sky's colour; the ramp of characters, bare to full,
  ordered by Menlo's own ink; where the sky ends in each column of the photograph, traced down from the top to where
  the picture first parts from the sky's colour, so the loader can draw the ridge in strokes the way it runs; and the
  birds.

The birds (art/prs-birds.png) are the nine of PRS's bird inlays, turned upright as if seen from below in flight, those
that look left turned to look right and all leaned a little into their flight. Each is set at a range of heights: in
each cell its silhouette is read at 6 by 10 points and the cell gets the printable character whose own ink, Menlo's
glyph drawn into the same cell, comes closest to it, point for point, with a slow wave of brightness across the bird
for the figure of the pearl.

With --proof, the birds are also set in Menlo as a PNG in DIR, to look at.
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
OUT = os.path.join(ROOT, 'public', 'loader')
FONT = '/System/Library/Fonts/Menlo.ttc'

ADVANCE = 0.602
SUB = (6, 10)
CHARS = [chr(c) for c in range(32, 127) if chr(c) != '<']
# The night the type is set on.
NIGHT = '#04080e'
# Tone, from the photograph's brightest channel, between what reads as bare and as full, with local contrast raised.
DARK, LIGHT = 34, 168
CONTRAST = 1.2
SKY_TONE = 0.45
# The colours, by tone, bare to full: deep teal in the shadows, through azure in the rock, to ice on the snow; the
# sky a cobalt of its own. A little of the photograph's own colour is kept in each.
STOPS = [(0.0, (18, 84, 112)), (0.25, (26, 140, 176)), (0.5, (52, 146, 240)), (0.75, (122, 192, 255)), (1.0, (236, 246, 255))]
SKY_COLOUR = np.array([74, 124, 232])
KEEP = 0.2
# The ramp, re-sorted by Menlo's own ink.
RAMP = " .,:;-~=+*xoe%#&@"
# The birds: their heights, in rows; which look left and are turned; how far they lean into their flight, in degrees.
HEIGHTS = (4, 5, 6, 8, 11, 15)
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
    """The closest character to each cell of `target`, point for point."""
    flat = maps.reshape(len(maps), -1)
    pick = np.empty(target.shape[:2], np.int64)
    for r in range(target.shape[0]):
        pick[r] = ((target[r][:, None, :] - flat[None]) ** 2).sum(-1).argmin(-1)
    return pick


def hex_colour(rgb):
    return '#' + ''.join(f'{round(v):02x}' for v in rgb)


def mountains(maps):
    rgb = np.asarray(Image.open(PHOTO).convert('RGB')).astype(np.float32)
    height, width = rgb.shape[:2]

    # The sky: in each column, down to where the picture first parts from the sky's colour.
    colour = np.median(rgb[:40].reshape(-1, 3), 0)
    apart = ndimage.median_filter(np.sqrt(((rgb - colour) ** 2).sum(2)), 3) > 9
    ridge = np.argmax(apart, axis=0)
    sky = np.arange(height)[:, None] < ridge[None, :]

    value = rgb.max(2)
    detail = value + CONTRAST * (value - ndimage.gaussian_filter(value, 5))
    tone = ndimage.gaussian_filter(np.clip((detail - DARK) / (LIGHT - DARK), 0, 1), 0.6)
    tone[sky] = SKY_TONE

    marks = [t for t, _ in STOPS]
    paint = np.stack([np.interp(tone, marks, [c[i] for _, c in STOPS]) for i in range(3)], -1)
    # The photograph's own colour, brought up to the same brightness, kept a little.
    own = rgb * (paint.mean(-1, keepdims=True) / np.maximum(rgb.mean(-1, keepdims=True), 1))
    paint = paint * (1 - KEEP) + np.clip(own, 0, 255) * KEEP
    sky_colour = SKY_COLOUR
    paint[sky] = sky_colour

    sheet = np.concatenate([paint, np.repeat(tone[..., None] * 255, 3, 2)], 0)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'tetons.webp')
    Image.fromarray(np.clip(sheet, 0, 255).astype(np.uint8)).save(path, quality=86, method=6)
    print(f'{width} x {height} photograph, {os.path.getsize(path)} bytes -> {os.path.relpath(path, ROOT)}')

    ink = {CHARS[i]: maps[i].mean() for i in range(len(CHARS))}
    ramp = ''.join(sorted(RAMP, key=lambda c: ink[c]))
    return [NIGHT, hex_colour(sky_colour), ramp, ' '.join(map(str, ridge))]


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
        mask = mask.resize((mask.width * 6, mask.height * 6), Image.Resampling.LANCZOS)
        mask = mask.rotate(-LEAN, expand=True, resample=Image.Resampling.BICUBIC)
        ink = ndimage.gaussian_filter(np.asarray(mask).astype(np.float32) / 255, 2)
        ys, xs = np.nonzero(ink > 0.05)
        ink = ink[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
        for rows in HEIGHTS:
            sw, sh = SUB
            cols = max(1, round(ink.shape[1] / ink.shape[0] * rows * sh / sw))
            sub = cells(ink, cols, rows)
            # The pearl's figure: a slow wave of brightness across the bird.
            r, c = np.mgrid[0:rows, 0:cols]
            sheen = 0.78 + 0.22 * np.sin((c * 0.9 + r * 1.7) / max(rows, 4) * 3)
            pick = match(np.clip(sub * sheen[..., None], 0, 1), maps)
            lines = [''.join(CHARS[i] if sub[y, x].mean() > 0.08 else ' ' for x, i in enumerate(row)).rstrip() for y, row in enumerate(pick)]
            out.append(f'{b} {rows} {cols}')
            out.extend(lines)
            if rows == HEIGHTS[-1]:
                proofs.append(lines)
    if proof:
        lines = []
        for bird in proofs:
            lines.extend(bird + [''])
        render(lines, os.path.join(proof, 'birds.png'))
    return out, len(shapes)


def render(lines, path):
    size = 14
    font = ImageFont.truetype(FONT, size)
    cell = size * ADVANCE
    image = Image.new('RGB', (round(max(len(line) for line in lines) * cell) + 1, len(lines) * size), NIGHT)
    draw = ImageDraw.Draw(image)
    ascent, descent = font.getmetrics()
    baseline = (size - (ascent + descent)) / 2 + ascent
    for r, line in enumerate(lines):
        draw.text((0, r * size + baseline), line, font=font, fill='#eef2f4', anchor='ls')
    image.save(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--proof')
    args = parser.parse_args()
    if args.proof:
        os.makedirs(args.proof, exist_ok=True)
    maps = glyphs()
    head = mountains(maps)
    flock, count = birds(maps, args.proof)
    path = os.path.join(OUT, 'tetons.txt')
    with open(path, 'w') as f:
        f.write('\n'.join(head + flock) + '\n')
    print(f'{count} birds at {", ".join(map(str, HEIGHTS))} rows, {os.path.getsize(path)} bytes -> {os.path.relpath(path, ROOT)}')


if __name__ == '__main__':
    main()
