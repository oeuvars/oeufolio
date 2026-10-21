# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""The loader's two crows, set in type. Run from the repository root:

    uv run studio/crows/ascii.py [--proof DIR]

art/crows.mp4 is a stop-motion loop of two crows cut from black marker drawings flapping over blue paper (where it was
found is in SOURCES.md). It runs at ten frames a second on twos: twelve drawings, played forward and back again, each
held for two frames.

Each drawing is laid on a grid of monospaced cells, 220 across for wide screens and 90 for phones, each cell as tall
as Menlo's at a line height of one. In
each cell the ink is read at 6 by 10 points, and the cell gets the printable character whose own ink, Menlo's glyph
drawn into the same cell, comes closest to it, point for point. So the edges of a wing take the characters that lean
and taper the way it does, and where the marker left a streak of paper inside a bird, the cell gets a stroke
that runs the way the streak does. The paper itself is not kept: its colour, top and bottom, is kept for each drawing, so it flickers as the photographs do.

Writes src/components/loader/crows.txt, which the loader reads:

    FPS
    the drawing shown on each frame, by number
    each drawing's paper colour at the top and the bottom
    then for each grid, COLS ROWS, and each drawing on it, a line per row, blank rows empty and trailing blanks cut

With --proof, each drawing is also set in Menlo over its paper as a PNG in DIR, to look at.
"""

import argparse
import os
import subprocess
import tempfile

import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
VIDEO = os.path.join(HERE, 'art', 'crows.mp4')
OUT = os.path.join(ROOT, 'src', 'components', 'loader', 'crows.txt')
FONT = '/System/Library/Fonts/Menlo.ttc'

GRIDS = (220, 90)
FPS = 10
# Menlo is 0.602 of an em wide; at a line height of one its cell is that wide to one tall. Ink is read at 6 by 10
# points a cell, near enough the same shape.
ADVANCE = 0.602
SUB = (6, 10)
# The marker's ink and the paper, in luma; between them, the share of ink.
INK = 24
# A cell with less ink than this is left as paper.
FAINT = 0.07
CHARS = [chr(c) for c in range(33, 127) if chr(c) != '<']
# A streak running across, down to the right, down, and up to the right, in the picture's y-down terms.
STROKES = '-\\|/'


def frames():
    """The video's frames, as RGB arrays."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['ffmpeg', '-v', 'error', '-i', VIDEO, os.path.join(tmp, '%03d.png')], check=True)
        names = sorted(os.listdir(tmp))
        return [np.asarray(Image.open(os.path.join(tmp, name)).convert('RGB')).astype(np.float32) for name in names]


def drawings(video):
    """The distinct drawings, and which one each frame shows. Frames that differ by less than a luma step on average
    are the same drawing photographed again."""
    unique, order = [], []
    for frame in video:
        luma = frame.mean(2)
        for i, seen in enumerate(unique):
            if np.abs(seen.mean(2) - luma).mean() < 2:
                order.append(i)
                break
        else:
            order.append(len(unique))
            unique.append(frame)
    return unique, order


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
        small = image.resize(SUB, Image.Resampling.BOX)
        maps.append(np.asarray(small).astype(np.float32) / 255)
    return np.stack(maps)


def setting(frame, maps, cols, rows):
    """The drawing as rows of characters."""
    luma = frame.mean(2)
    paper = np.median(luma)
    ink = np.clip((paper - luma) / (paper - INK), 0, 1)
    # The crows are the two large shapes; the shading at the photograph's corners and edges is let go.
    solid = ink > 0.5
    found, count = ndimage.label(solid)
    sizes = ndimage.sum(solid, found, range(1, count + 1))
    crows = np.isin(found, 1 + np.flatnonzero(sizes > 2000))
    ink = ink * ndimage.binary_dilation(crows, iterations=3)
    # The streaks of paper the marker left inside a bird: what is paper within its filled outline.
    # Gaps open to the paper round it, as between the feathers of a spread wing, are not streaks.
    inside = ndimage.binary_fill_holes(crows)
    streak = inside & ~crows

    sw, sh = SUB
    size = (cols * sw, rows * sh)

    def cut(a):
        big = Image.fromarray((a * 255).astype(np.uint8)).resize(size, Image.Resampling.BOX)
        return np.asarray(big).astype(np.float32).reshape(rows, sh, cols, sw).transpose(0, 2, 1, 3) / 255

    cells = cut(ink)
    streaks = cut(streak.astype(np.float32))
    within = cut(inside.astype(np.float32)).mean((-2, -1))
    # Elsewhere, the closest character, point for point.
    flat = maps.reshape(len(maps), -1)
    target = cells.reshape(rows, cols, -1)
    pick = ((target[:, :, None, :] - flat[None, None]) ** 2).sum(-1).argmin(-1)

    lines = []
    ys, xs = np.mgrid[0:sh, 0:sw]
    for r in range(rows):
        line = ''
        for c in range(cols):
            share = streaks[r, c].mean()
            if within[r, c] > 0.9 and share > 0.03:
                # A streak through the cell is drawn as a stroke that runs its way.
                w = streaks[r, c]
                x, y = (xs * w).sum() / w.sum(), (ys * w).sum() / w.sum()
                xx = ((xs - x) ** 2 * w).sum()
                yy = ((ys - y) ** 2 * w).sum()
                xy = ((xs - x) * (ys - y) * w).sum()
                angle = np.degrees(0.5 * np.arctan2(2 * xy, xx - yy))
                line += STROKES[round((angle % 180) / 45) % 4] if share > 0.08 else '.'
            elif cells[r, c].mean() > FAINT:
                line += CHARS[pick[r, c]]
            else:
                line += ' '
        lines.append(line.rstrip())
    return lines


def colours(frame):
    """The paper's colour along the top and the bottom of the drawing, where there are no crows."""
    luma = frame.mean(2)
    paper = luma > np.median(luma) - 30
    out = []
    for band in (slice(0, 60), slice(-60, None)):
        pick = paper[band]
        rgb = frame[band][pick].mean(0)
        out.append('#' + ''.join(f'{round(v):02x}' for v in rgb))
    return out


def proof(lines, top, bottom, cols, rows, path):
    size = 14
    font = ImageFont.truetype(FONT, size)
    w, h = round(cols * size * ADVANCE), rows * size
    a = np.array([int(top[i : i + 2], 16) for i in (1, 3, 5)], np.float32)
    b = np.array([int(bottom[i : i + 2], 16) for i in (1, 3, 5)], np.float32)
    t = np.linspace(0, 1, h)[:, None]
    grad = (a * (1 - t) + b * t)[:, None, :].repeat(w, 1)
    image = Image.fromarray(grad.astype(np.uint8))
    draw = ImageDraw.Draw(image)
    ascent, descent = font.getmetrics()
    baseline = (size - (ascent + descent)) / 2 + ascent
    for r, line in enumerate(lines):
        draw.text((0, r * size + baseline), line, font=font, fill=(16, 20, 26), anchor='ls')
    image.save(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--proof')
    args = parser.parse_args()

    video = frames()
    height, width = video[0].shape[:2]
    unique, order = drawings(video)
    maps = glyphs()
    paper = [colours(frame) for frame in unique]

    out = [str(FPS), ' '.join(map(str, order)), ' '.join(f'{t},{b}' for t, b in paper)]
    for cols in GRIDS:
        rows = round(height / (width / cols / ADVANCE))
        sets = [setting(frame, maps, cols, rows) for frame in unique]
        out.append(f'{cols} {rows}')
        for lines in sets:
            out.extend(lines)
        if args.proof:
            os.makedirs(args.proof, exist_ok=True)
            for i, (lines, (top, bottom)) in enumerate(zip(sets, paper)):
                proof(lines, top, bottom, cols, rows, os.path.join(args.proof, f'{cols}-{i:02d}.png'))
    with open(OUT, 'w') as f:
        f.write('\n'.join(out) + '\n')
    print(f'{len(unique)} drawings on {", ".join(map(str, GRIDS))} columns, {os.path.getsize(OUT)} bytes -> {os.path.relpath(OUT, ROOT)}')


if __name__ == '__main__':
    main()
