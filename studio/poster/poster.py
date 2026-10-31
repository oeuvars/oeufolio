# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""The work page's poster: a copy of the reference poster (art/reference.jpg, 736 x 981), lit windows of a
block of flats at night with "human experience" glowing across them and four italic passages set between them,
printed at three times its size.

    node studio/poster/type.mjs      (after changing type.html or type.json)
    uv run studio/poster/poster.py [--proof DIR]

The windows, the dark wall and its light leaks are the reference's own, scaled up. The type is set again from the
plates type.mjs photographs (art/title.png, art/body.png), in the same place, so it is sharp at the new size: the old
passages are lifted off the wall first, and the title is laid over the old one as the reference has it, a photograph
of a lit sign, its letters soft, glowing, and broken into the dots of the screen it was shown on. Each company named in
the passages has a stroke of white highlighter run over it where type.mjs found it (src/components/poster.json), under
the print, so its letters come out dark on the stroke. New grain goes over the whole, at the new size, so the
scaled-up picture reads as film again.

The page is one material: the poster's bare wall, as a tile of paper. Writes public/objects/poster-paper.avif, that
tile; public/objects/poster.avif, the light printed on it (the windows, the sign and the passages, black where the
wall was), which the page screens over the paper; public/objects/poster-strip.avif, the same for the work strip
folded, as a column as wide as the poster's middle; and public/objects/poster-band.avif, the same for a folded phone
strip, which lies across the window. The column is a strip of old film as wide as the strip, its holes and the white
round it left clear for the paper: a photograph of one (art/film.jpg), its five frames printed with five of the
poster's windows under the film's own scratches, dust and stains, and the whole of "human experience" laid down it as
light in one line: the poster's own sign, its two words cut from its plate and set a word space apart on one baseline,
and lit as the poster's is. The band is the poster recut along it: its windows set off a grid at different sizes, and
the sign's two words where they fall among them. The passages come with the page when the strip opens.
"""

import argparse
import io
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCALE = 3
# The passages' boxes in the reference's pixels (left, top, right, bottom), a little past their ink.
PASSAGES = [(305, 302, 398, 453), (512, 374, 642, 451), (100, 484, 302, 561), (300, 622, 530, 709)]
# How many pixels across a wide screen's folded strip has the film (the strip shows it about 250 CSS px across).
STRIP_WIDE = 882
# The sign's two words on its plate (art/title.png): where each runs from and to across and where its baseline lies,
# how far its letters run above and below a baseline, and the word space set between the two in one line, in the
# reference's pixels.
WORDS = ((99, 334, 370), (244, 631, 613))
RISE, FALL = 64, 20
WORD_SPACE = 22
# The poster's windows, each by its box in the reference's pixels: the candle's, the two women's at the yellow window
# (all of it, and as far as the second woman's knee), the child's at the lilac curtain, the red one's, the woman's over
# the city, the saxophonist's, the one of the woman sitting high in hers, the curtained one's, and the man's at the
# yellow window.
CANDLE, WOMEN, WOMAN, CURTAIN = (520, 228, 638, 368), (105, 566, 288, 708), (105, 566, 246, 708), (415, 709, 528, 859)
RED, CITY, SAX, SITTER = (310, 455, 419, 549), (238, 715, 339, 832), (308, 163, 390, 293), (408, 122, 501, 239)
CURTAINS, YELLOW = (118, 193, 300, 296), (104, 390, 290, 478)
# A wide screen's folded strip is a strip of film (art/film.jpg, a photograph of an old one on white), its five frames
# printed with five of those windows, down it in this order.
FILM = "film.jpg"
FILM_FRAMES = ("CANDLE", "WOMEN", "CURTAIN", "RED", "CITY")
# What of the photograph is the white it lay on (each channel over FILM_CLEAR: the film is dark, and its frames' pale
# sepia has a dark blue channel), and what is a frame's pale base (its luminance between these two) and not the film's
# darker bars and edges.
FILM_CLEAR, FILM_FRAME, FILM_WHITE = 0.7, 0.55, 0.88
# A patch of white smaller than this, in the photograph's pixels, is a fleck on the film, not a hole through it. How far
# round the white the film's edge is blurred into it, in those pixels, and how light the film itself is there, at its
# lightest channel (the dark rebate by the holes).
FILM_SPECK, FILM_RIM, FILM_RIM_FILM = 40, 3, 0.3
# A window printed on the film: how far its blacks are lifted, the warm cast of the old print, and how strongly the
# film's scratches, dust and stains lie over it.
FILM_LIFT, FILM_WARM, FILM_WEAR = 0.07, np.array([1.0, 0.95, 0.86]), 1.0
# How much of their colour the film's prints keep, and of their light, so the sign over them reads; and how much of its
# colour the film's own base keeps.
FILM_COLOUR, FILM_LIGHT, FILM_BASE = 0.45, 0.68, 0.75
# The sign's height across the film, as a part of its width.
FILM_SIGN = 0.41
# A phone's folded strip is a band of the poster recut: windows set along it off a grid at different sizes, and the
# sign's two words where they fall among them. The band in pixels (it shows 21 by 3.875 rem), how much of their light
# the windows keep, and each window by where its top left lies and how tall it is, as parts of the band, then each word
# by where its top left lies, as parts of the band, and how tall its letters and their glow are, as a part of its depth.
BAND = (2016, 372)
BAND_LIGHT = 0.82
BAND_WINDOWS = (("SAX", 0.01, 0.08, 0.30), ("SITTER", 0.06, 0.52, 0.38), ("CURTAINS", 0.13, 0.10, 0.40), ("CANDLE", 0.30, 0.30, 0.62),
                ("YELLOW", 0.40, 0.06, 0.40), ("RED", 0.55, 0.44, 0.52), ("WOMAN", 0.66, 0.06, 0.62), ("CITY", 0.82, 0.14, 0.58),
                ("CURTAIN", 0.92, 0.20, 0.70))
BAND_WORDS = ((0.10, -0.05), (0.42, 0.45))
BAND_WORD = 0.5
# How far round each word of the sign a folded strip takes the poster's light with it, and the room left round the
# word for that, in the reference's pixels.
WORD_REACH, WORD_PAD = 6, 24
# The paper tile: how many pixels of the poster it takes, and how many it is written at (twice the CSS pixels it
# is shown at, src/components/site-shell.tsx PAPER, the poster being shown about a third of its size).
PAPER_TAKES = 420
PAPER_SIZE = 280
# How far over the paper's own dark the wall's light has to be to count as light printed on it.
FLOOR = 0.012
# The type's colour: the passages are printed a warm white, the sign is a cold one.
INK = np.array([0.93, 0.91, 0.87])
SIGN = np.array([0.90, 0.91, 0.92])
# The highlighter: a white paint marker, a little less than opaque, and the companies it is run over.
MARKER = np.array([0.93, 0.92, 0.89])
MARKS = os.path.join(ROOT, "src", "components", "poster.json")


def load(name):
    return np.asarray(Image.open(os.path.join(HERE, "art", name)).convert("RGB")).astype(np.float32) / 255


def plate(name, size):
    image = Image.open(os.path.join(HERE, "art", name)).convert("L")
    if image.size != size:
        raise SystemExit(f"art/{name} is {image.size}, not {size}: run studio/poster/type.mjs again.")
    return np.asarray(image).astype(np.float32) / 255


def box_mask(shape, boxes, feather):
    """1 inside the boxes (scaled up), falling off softly past their edges."""
    mask = np.zeros(shape, np.float32)
    for left, top, right, bottom in boxes:
        mask[top * SCALE : bottom * SCALE, left * SCALE : right * SCALE] = 1
    return ndimage.gaussian_filter(mask, feather)


def lift_type(picture, mask):
    """The wall under the passages with their letters taken off: a grey opening wider than a stroke keeps what is
    broad (the window frames, the title's glow) and drops what is thin."""
    size = 6 * SCALE + 1
    bare = np.stack([ndimage.grey_opening(picture[..., c], size=(size, size)) for c in range(3)], -1)
    bare = np.stack([ndimage.gaussian_filter(bare[..., c], SCALE) for c in range(3)], -1)
    return picture * (1 - mask[..., None]) + bare * mask[..., None]


def lift_sign(picture, title):
    """The wall with the old sign's letters filled in from round them, so none of them shows past the new ones."""
    under = ndimage.grey_dilation(title, size=(4 * SCALE + 1, 4 * SCALE + 1))
    under = np.clip(1.5 * ndimage.gaussian_filter(under, 0.5 * SCALE), 0, 1)
    keep = 1 - under
    # From close by where there is wall close by, and from further off where the letters crowd it out.
    def spread(image):
        return ndimage.gaussian_filter(image, 3 * SCALE) + 0.05 * ndimage.gaussian_filter(image, 10 * SCALE)

    fill = np.stack([spread(picture[..., c] * keep) for c in range(3)], -1) / (spread(keep) + 1e-6)[..., None]
    return picture * keep[..., None] + fill * under[..., None]


def light_sign(picture, title, shape):
    """A photograph of a lit sign, as the reference has it: its letters a little out of focus, made of a screen's dots
    that do not quite keep their grid, lit unevenly, and grained as film is; their light bleeds close round them and
    then wide. Then the camera's losses: the whole is kept at the reference's size and as a JPEG, as the reference was,
    and scaled up as the windows round it are, so the sign is as soft and as grainy as they are on the page. Made only
    at the new size, its dots line up into a moire and its grain is too fine to survive the page showing it smaller."""
    rng = np.random.default_rng(5)
    letters = ndimage.gaussian_filter(title, 1.4 * SCALE)
    dots = screen_dots(shape, 2.1 * SCALE, 0.3 * SCALE * reference_noise(rng, shape, 6), 0.3 * SCALE * reference_noise(rng, shape, 6))
    mottle = 1 + 0.08 * reference_noise(rng, shape, 3) + 0.05 * reference_noise(rng, shape, 12)
    grain = reference_noise(rng, shape, 0.6)
    face = SIGN * np.clip((0.6 + 0.34 * dots) * mottle + 0.04 * grain, 0, 1)[..., None]
    picture = picture * (1 - letters[..., None]) + face * letters[..., None]
    glow = (0.22 * ndimage.gaussian_filter(title, 1.8 * SCALE) + 0.3 * ndimage.gaussian_filter(title, 3.5 * SCALE)
            + 0.18 * ndimage.gaussian_filter(title, 12 * SCALE))
    glow = np.clip(glow * (mottle + 0.1 * grain), 0, 1)[..., None] * SIGN
    return through_reference(1 - (1 - picture) * (1 - glow)), letters


def reference_noise(rng, shape, blur):
    """Noise in the reference's own pixels, blurred by blur of them, scaled up to the new size: about -1 to 1."""
    noise = ndimage.gaussian_filter(rng.standard_normal((shape[0] // SCALE, shape[1] // SCALE)).astype(np.float32), blur)
    return ndimage.zoom(noise / (2 * noise.std()), SCALE, order=3)


def through_reference(image):
    """The picture as the reference keeps it, at its size and as a JPEG, then scaled up to the new size again."""
    big = Image.fromarray((np.clip(image, 0, 1) * 255 + 0.5).astype(np.uint8))
    small = big.resize((big.width // SCALE, big.height // SCALE), Image.LANCZOS)
    kept = io.BytesIO()
    small.save(kept, "JPEG", quality=80)
    return np.asarray(Image.open(kept).convert("RGB").resize(big.size, Image.LANCZOS)).astype(np.float32) / 255


def sign_words(lit, title):
    """The poster's sign's two words, each cut from the lit poster with the light round it, as far as its glow runs
    (WORD_REACH). What lies under the glow on the poster, the window it crosses, comes with it."""
    pad, reach = WORD_PAD * SCALE, WORD_REACH * SCALE
    cut = []
    for x0, x1, base in WORDS:
        rows = slice((base - RISE) * SCALE - pad, (base + FALL) * SCALE + pad)
        cols = slice(x0 * SCALE - pad, x1 * SCALE + pad)
        glow = ndimage.gaussian_filter(ndimage.grey_dilation(title[rows, cols], size=(reach, reach)), reach / 2)
        cut.append(lit[rows, cols] * np.clip(1.4 * glow / glow.max(), 0, 1)[..., None])
    return cut


def one_line(lit, title):
    """The poster's sign in one line, as the poster shows it: its two words (sign_words), "experience" set a word space
    on from "human", on the same baseline."""
    pad = WORD_PAD * SCALE
    human, experience = sign_words(lit, title)
    line = np.zeros((human.shape[0], human.shape[1] + WORD_SPACE * SCALE - 2 * pad + experience.shape[1], 3), np.float32)
    put(line, human, 0, 0)
    at = line.shape[1] - experience.shape[1]
    line[:, at:] = np.maximum(line[:, at:], experience)
    return line


def put(canvas, image, left, top):
    canvas[top : top + image.shape[0], left : left + image.shape[1]] = image


def resized(image, width, height):
    image = Image.fromarray((np.clip(image, 0, 1) * 255 + 0.5).astype(np.uint8))
    return np.asarray(image.resize((round(width), round(height)), Image.LANCZOS)).astype(np.float32) / 255


def film_plate():
    """The photograph of the film (art/film.jpg), cut to the film: its colour, and
    how much of each pixel is film. It was photographed on white, which shows round it and through its sprocket holes:
    none of that is film, so the page's own paper shows there. Where the film's edge is blurred into the white, the
    white is taken back out of its colour, so no pale rim is left round a hole."""
    photo = load(FILM)
    lightest = photo.min(-1)
    parts, count = ndimage.label(lightest > FILM_CLEAR)
    # The white that is not film: round the film and through each hole, not a fleck of dust on it.
    sizes = ndimage.sum(np.ones_like(lightest), parts, range(1, count + 1))
    white = np.isin(parts, 1 + np.flatnonzero(sizes >= FILM_SPECK))
    rim = ndimage.binary_dilation(white, iterations=FILM_RIM) & ~white
    cover = np.where(rim, np.clip((1 - lightest) / (1 - FILM_RIM_FILM), 0, 1), 1.0).astype(np.float32)
    cover[white] = 0
    seen = np.maximum(cover, 1e-3)[..., None]
    photo = np.clip(np.where(rim[..., None], (photo - (1 - seen)) / seen, photo), 0, 1)
    rows, cols = np.where(cover > 0)
    box = (slice(rows.min(), rows.max() + 1), slice(cols.min(), cols.max() + 1))
    return photo[box], cover[box]


def film_frames(photo, film):
    """The film's frames: the pale sepia windows between its bars and its sprocket holes, each as a mask."""
    luma = photo @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    pale = ndimage.binary_opening((luma > FILM_FRAME) & (luma < FILM_WHITE) & (film > 0), np.ones((5, 5)))
    parts, count = ndimage.label(pale)
    sizes = ndimage.sum(pale, parts, range(1, count + 1))
    frames = [ndimage.binary_fill_holes(parts == n + 1) for n in np.argsort(sizes)[::-1][: len(FILM_FRAMES)]]
    return sorted(frames, key=lambda frame: np.argwhere(frame)[:, 0].min())


def folded_film(bare, lit, title):
    """A wide screen's folded strip: the film, its frames printed with the poster's windows, and the sign laid down it as
    light. A print on old film: muted, darker, its blacks lifted, a little warm, and under the film's own scratches,
    dust and stains, which are the photograph's, the frame's own light against its blur. It runs down the strip as wide
    as it, past its top and foot. Round the film and through its holes there is no light: the paper shows."""
    photo, film = film_plate()
    k = STRIP_WIDE / photo.shape[1]
    photo = resized(photo, photo.shape[1] * k, photo.shape[0] * k)
    film = resized(np.repeat(film[..., None], 3, -1), film.shape[1] * k, film.shape[0] * k)[..., 0]
    luma = photo @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    wear = luma / (ndimage.gaussian_filter(luma, 4 * k) + 1e-6)
    photo = luma[..., None] + FILM_BASE * (photo - luma[..., None])
    for frame, name in zip(film_frames(photo, film), FILM_FRAMES):
        (top, left), (bottom, right) = np.argwhere(frame).min(0), np.argwhere(frame).max(0) + 1
        x0, y0, x1, y1 = globals()[name]
        window = bare[y0 * SCALE : y1 * SCALE, x0 * SCALE : x1 * SCALE]
        cover = max((right - left) / window.shape[1], (bottom - top) / window.shape[0])
        window = resized(window, window.shape[1] * cover, window.shape[0] * cover)
        dy, dx = (window.shape[0] - (bottom - top)) // 2, (window.shape[1] - (right - left)) // 2
        window = window[dy : dy + bottom - top, dx : dx + right - left]
        grey = (window @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
        window = FILM_LIGHT * (grey + FILM_COLOUR * (window - grey))
        printed = (FILM_LIFT + (1 - FILM_LIFT) * window) * FILM_WARM
        printed = np.clip(printed * wear[top:bottom, left:right, None] ** FILM_WEAR, 0, 1)
        edge = ndimage.gaussian_filter(frame[top:bottom, left:right].astype(np.float32), 0.6 * k)[..., None]
        photo[top:bottom, left:right] = photo[top:bottom, left:right] * (1 - edge) + printed * edge
    canvas = photo * film[..., None]
    sign = one_line(lit, title)
    across = FILM_SIGN * canvas.shape[1]
    sign = np.ascontiguousarray(np.rot90(resized(sign, sign.shape[1] * across / sign.shape[0], across), -1))
    lay(canvas, sign, (canvas.shape[1] - sign.shape[1]) // 2, (canvas.shape[0] - sign.shape[0]) // 2)
    return canvas


def folded_band(bare, lit, title):
    """A phone's folded strip: the poster recut along the band (BAND_WINDOWS), its windows whole at their own shapes,
    a little dimmed, on no wall, so the paper shows between them, and the sign's two words, each cut from the lit poster
    with its glow, laid over them as light where BAND_WORDS puts them."""
    wide, deep = BAND
    band = np.zeros((deep, wide, 3), np.float32)
    for name, left, top, tall in BAND_WINDOWS:
        x0, y0, x1, y1 = globals()[name]
        window = bare[y0 * SCALE : y1 * SCALE, x0 * SCALE : x1 * SCALE]
        window = resized(window, tall * deep * (x1 - x0) / (y1 - y0), tall * deep) * BAND_LIGHT
        x, y = round(left * wide), round(top * deep)
        window = window[: deep - y, : wide - x]
        band[y : y + window.shape[0], x : x + window.shape[1]] = window
    for word, (left, top) in zip(sign_words(lit, title), BAND_WORDS):
        word = resized(word, word.shape[1] * BAND_WORD * deep / word.shape[0], BAND_WORD * deep)
        x, y = round(left * wide), round(top * deep)
        cut = word[max(0, -y) : deep - y, : wide - x]
        lay(band, cut, x, max(0, y))
    return band


def lay(canvas, image, left, top):
    """Light laid over the light already there (a screen)."""
    under = canvas[top : top + image.shape[0], left : left + image.shape[1]]
    canvas[top : top + image.shape[0], left : left + image.shape[1]] = 1 - (1 - under) * (1 - image)


def paper(image):
    """The flattest square of bare wall in the poster, made to repeat without a seam: the square and the same square
    turned half over in both directions, mixed so each edge is the middle of the other, and its slow light taken out."""
    luma = ndimage.gaussian_filter(image @ np.array([0.2126, 0.7152, 0.0722], np.float32), 12)
    best = None
    for top in range(0, image.shape[0] - PAPER_TAKES, 40):
        for left in range(0, image.shape[1] - PAPER_TAKES, 40):
            patch = luma[top : top + PAPER_TAKES, left : left + PAPER_TAKES]
            score = patch.std() + abs(patch.mean() - 0.05)
            if best is None or score < best[0]:
                best = (score, top, left)
    _, top, left = best
    square = image[top : top + PAPER_TAKES, left : left + PAPER_TAKES]
    half = PAPER_TAKES // 2
    rolled = np.roll(square, (half, half), (0, 1))
    ramp = 1 - np.abs(np.linspace(-1, 1, PAPER_TAKES, dtype=np.float32))
    weight = np.minimum.outer(ramp, ramp)[..., None]
    rolled_weight = np.roll(weight, (half, half), (0, 1))
    tile = (square * weight + rolled * rolled_weight) / (weight + rolled_weight + 1e-6)
    tile = np.asarray(Image.fromarray((np.clip(tile, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((PAPER_SIZE, PAPER_SIZE), Image.LANCZOS))
    tile = tile.astype(np.float32) / 255
    # Only the grain is kept: the wall's slow light would show as a pattern where the tile repeats.
    slow = np.stack([ndimage.gaussian_filter(tile[..., c], PAPER_SIZE / 16, mode="wrap") for c in range(3)], -1)
    return tile - slow + tile.mean((0, 1))


def wander(rng, count, smooth):
    """A slow random line, count samples long, about -1 to 1."""
    line = ndimage.gaussian_filter(rng.standard_normal(count + 8 * int(smooth)), smooth, mode="wrap")
    line = line[4 * int(smooth) : 4 * int(smooth) + count]
    return line / (np.abs(line).max() + 1e-6)


def highlighter(shape, marks, rng):
    """How much of the highlighter covers each pixel: one stroke a word, laid from a little before it to a little
    past it, over the letters' bodies and not quite up to their capitals. A stroke by hand: tilted a hair, its edges
    not quite straight, its chisel ends cut on a slant and ragged where the tip lifts, streaked along its length where
    the felt laid more or less paint, and a little heavier along its edges, where the paint pools. The paint lies on
    the paper as paint does: it skips over the paper's tooth in specks, more as the tip runs dry towards the tail and
    along the edges, and it lies thicker and thinner in blotches. Then the camera takes it as it took the windows,
    its edges as soft as theirs and its blotches the size of their grain."""
    cover = np.zeros(shape, np.float32)
    for mark in marks:
        size = mark["size"] * SCALE
        start = (mark["left"] - 0.06 * mark["size"]) * SCALE
        end = (mark["right"] + 0.26 * mark["size"]) * SCALE
        middle = (mark["baseline"] - 0.32 * mark["size"]) * SCALE
        half = 0.55 * size
        top, bottom = int(middle - 2 * size), int(middle + 2 * size)
        left, right = int(start - size), int(end + size)
        y, x = np.mgrid[top:bottom, left:right].astype(np.float32)
        tilt = np.radians(rng.uniform(-0.9, 0.4))
        u = x - start
        v = (y - middle) - np.tan(tilt) * u
        # Its edges, wavering a little along its length.
        along = np.clip(u, 0, end - start).astype(int)
        upper = half * (1 + 0.04 * wander(rng, int(end - start) + 1, 6 * SCALE))[along]
        lower = half * (1 + 0.04 * wander(rng, int(end - start) + 1, 6 * SCALE))[along]
        edge = 0.35 * SCALE
        across = np.clip((v + upper) / edge, 0, 1) * np.clip((lower - v) / edge, 0, 1)
        # Its ends, cut on the chisel's slant and ragged across the stroke where the tip lifts.
        rows = np.clip(((v + 2 * size) / (4 * size)) * 4 * size, 0, 4 * size - 1).astype(int)
        slant = 0.18 * v
        head = start + slant + 0.5 * SCALE * wander(rng, int(4 * size), 0.8 * SCALE)[rows]
        tail = end + slant + 0.8 * SCALE * wander(rng, int(4 * size), 0.6 * SCALE)[rows]
        ends = np.clip((x - head) / edge, 0, 1) * np.clip((tail - x) / (1.5 * edge), 0, 1)
        # Its streaks, lines along it, and the paint pooled at its edges.
        streak = 0.93 + 0.07 * wander(rng, int(4 * size), 0.5 * SCALE)[rows]
        pool = 1 + 0.04 * np.exp(-np.minimum(v + upper, lower - v).clip(0) / (0.8 * SCALE))
        # The tooth: specks of bare paper, a few at the head, more towards the tail and the edges.
        tooth = ndimage.gaussian_filter(rng.standard_normal(u.shape).astype(np.float32), 0.4 * SCALE)
        tooth /= tooth.std()
        dry = np.clip(u / (end - start), 0, 1) + 1.5 * np.exp(-np.minimum(v + upper, lower - v).clip(0) / (0.6 * SCALE))
        bare = np.clip((tooth - (2.4 - 0.9 * dry)) / 0.5, 0, 1)
        stroke = np.clip(0.97 * across * ends * streak * pool * (1 - 0.85 * bare), 0, 1)
        window = cover[top:bottom, left:right]
        cover[top:bottom, left:right] = 1 - (1 - window) * (1 - stroke)
    # The blotches, then the lens.
    blotch = ndimage.gaussian_filter(rng.standard_normal(shape).astype(np.float32), 1.2 * SCALE)
    cover *= 1 + 0.05 * blotch / blotch.std()
    return np.clip(ndimage.gaussian_filter(cover, 0.6 * SCALE), 0, 1)


def screen_dots(shape, pitch, drift_x, drift_y):
    """The sign's screen, a grid of lit dots turned 45 degrees, 1 on a dot and 0 between, each dot drifted off the
    grid by drift (in pixels), as a screen photographed through a lens is."""
    y, x = np.mgrid[0 : shape[0], 0 : shape[1]].astype(np.float32)
    x, y = x + drift_x, y + drift_y
    u, v = (x + y) / np.sqrt(2), (x - y) / np.sqrt(2)
    return 0.5 + 0.5 * np.cos(2 * np.pi * u / pitch) * np.cos(2 * np.pi * v / pitch)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof", help="also write the poster as a PNG into this folder")
    args = parser.parse_args()

    source = Image.open(os.path.join(HERE, "art", "reference.jpg")).convert("RGB")
    size = (source.width * SCALE, source.height * SCALE)
    picture = np.asarray(source.resize(size, Image.LANCZOS)).astype(np.float32) / 255
    shape = picture.shape[:2]

    # The old passages come off the wall.
    picture = lift_type(picture, box_mask(shape, PASSAGES, 1.5 * SCALE))

    # The sign in place of the old one, and in one line on the folded strips, cut from the poster as it is lit.
    title = plate("title.png", size)
    bare = lift_sign(picture, title)
    picture, letters = light_sign(bare, title, shape)
    strip, band = folded_film(bare, picture, title), folded_band(bare, picture, title)

    # The highlighter goes over the companies before the passages are printed, so their letters print dark on it.
    with open(MARKS) as file:
        marks = json.load(file)["marks"]
    stroke = highlighter(shape, marks, np.random.default_rng(11))[..., None]
    picture = picture * (1 - stroke) + MARKER * stroke

    # The new passages go on in the old ones' place, a touch soft, as print on a print is. They are printed as the
    # reference prints them, as a difference: white on the dark wall, dark where they run into the sign's glow, and
    # gone under its letters.
    ink = ndimage.gaussian_filter(plate("body.png", size), 0.45 * SCALE) * (1 - np.clip(1.4 * letters, 0, 1))
    picture = picture * (1 - ink[..., None]) + np.abs(picture - INK) * ink[..., None]

    # Grain at the new size, a little stronger in the middle tones, as film's is.
    rng = np.random.default_rng(7)
    grains = {}

    def grained(image):
        if image.shape[:2] not in grains:
            grains[image.shape[:2]] = ndimage.gaussian_filter(rng.standard_normal(image.shape[:2]).astype(np.float32), 0.7)
        grain = grains[image.shape[:2]]
        luma = image @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        return image + (0.035 + 0.05 * luma * (1 - luma))[..., None] * grain[..., None]

    # The paper: the poster's bare wall, grain and all, as a tile. The page is made of it, round the poster and under it.
    sheet = paper(np.clip(grained(picture), 0, 1))
    write(Image.fromarray((sheet * 255 + 0.5).astype(np.uint8)), "poster-paper", args.proof)

    # The poster itself is only the light printed on that paper: the windows, the sign and its glow, the passages. The
    # wall is the paper's own dark, so what is no brighter than it comes off, and the page lays the rest over the paper
    # as light (a screen), so the wall it shows is the paper.
    floor = sheet.reshape(-1, 3).mean(0) + FLOOR
    for name, image in (("poster", picture), ("poster-strip", strip), ("poster-band", band)):
        light = np.clip(image - floor, 0, None)
        lit = np.clip(light.max(-1) / 0.06, 0, 1)[..., None]
        light = grained(light) * lit + light * (1 - lit)
        write(Image.fromarray((np.clip(light, 0, 1) * 255 + 0.5).astype(np.uint8)), name, args.proof)


def write(image, name, proof):
    image.save(os.path.join(ROOT, "public", "objects", f"{name}.avif"), quality=82, subsampling="4:4:4", speed=2)
    if proof:
        os.makedirs(proof, exist_ok=True)
        image.save(os.path.join(proof, f"{name}.png"))

if __name__ == "__main__":
    main()
