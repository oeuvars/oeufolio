# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""Where each piece of a folded strip's picture goes on its open page (Fold).

    uv run studio/fold.py [--proof DIR]

On a phone each folded strip shows a band of its own, made of pieces of its page set in a row: the letter's drawings,
the poster's sign and windows, a few of the desk's things, the whole contact set. On a wide screen the letter's and the
poster's strips show the same drawings and a sign and windows set down them (letter-wide, poster-wide). As the strip opens, each piece
travels from where the band has it to where the page has it, turning and growing on the way, and as it folds, back.
For each piece this writes, for the band's picture and the page's: which picture it is in (the src the page lays it
with), the outline it is cut out by, in that picture's pixels, and the point it turns about, the same point of the
thing in both; and how far it turns, clockwise, and grows, in pixels of the page's picture to one of the band's.
Everything is worked out from where the scripts that render the bands and pages put things (studio/letter.py,
studio/poster/poster.py, studio/desk/desk.json, studio/ticket/scene.py), and the letter's crop is found by matching.

Writes src/components/fold.json, with each picture's size in pixels and where the poster band's layers lie in its middle,
and public/objects/mat/desk-{band,wide}-light(-past)-bare.avif, the lamp's light on the desk without the things that
travel, and desk-wide-light(-past)-empty.avif, without anything on it (bare_light). --proof DIR also writes, for each strip, its band and page with every outline drawn
on them, and the band's pieces carried to the page and laid over it, to check they land on their things.
"""

import argparse
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage, signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OBJECTS = os.path.join(ROOT, "public", "objects")
OUT = os.path.join(ROOT, "src", "components", "fold.json")


def load(src):
    """A picture the page lays, as straight RGBA floats."""
    return np.asarray(Image.open(os.path.join(ROOT, "public", src.lstrip("/"))).convert("RGBA")).astype(np.float32) / 255


def rect(x, y, w, h):
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


def turned_rect(cx, cy, w, h, degrees):
    """A w by h box with its middle at cx, cy, turned clockwise (as the page turns things, y down)."""
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    return [[cx + c * x - s * y, cy + s * x + c * y] for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]


def beyond(outline, a, b):
    """The part of an outline on the side of the line from a to b that the line turns to when it turns clockwise
    (as the page turns things, y down): one pass of Sutherland and Hodgman's clipping."""
    side = lambda p: (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    kept = []
    for i, p in enumerate(outline):
        q = outline[(i + 1) % len(outline)]
        sp, sq = side(p), side(q)
        if sp >= 0:
            kept.append(p)
        if (sp >= 0) != (sq >= 0):
            t = sp / (sp - sq)
            kept.append([p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])])
    return kept


def apart(near, far):
    """The line between two things, from the middle of the one to the middle of the other: halfway, across."""
    mx, my = (near[0] + far[0]) / 2, (near[1] + far[1]) / 2
    dx, dy = far[0] - near[0], far[1] - near[1]
    return (mx + dy, my - dx), (mx - dy, my + dx)


def refine(each, reach=48, turns=(0,), scales=(1,)):
    """The band's picture of a thing set on the page's where it matches it best: carried by the piece's turn and scale,
    and by each of these more, then slid by up to reach pixels, at a quarter of the size. The page's camera stands
    elsewhere than the band's, so a thing that stands up off the desk is seen leaning a little differently in each."""
    q = 4
    band, page = load(each["band"]["src"]), load(each["page"]["src"])
    feature = lambda image: image[..., 3] * (0.3 + image[..., :3].mean(-1))
    small = lambda image: np.asarray(Image.fromarray(image).resize((image.shape[1] // q, image.shape[0] // q), Image.BILINEAR))
    cut = Image.new("L", (page.shape[1], page.shape[0]), 0)
    for outline in each["page"]["clip"]:
        ImageDraw.Draw(cut).polygon([tuple(p) for p in outline], fill=255)
    target = small(feature(page) * np.asarray(cut, np.float32) / 255)
    held = Image.new("L", (band.shape[1], band.shape[0]), 0)
    for outline in each["band"]["clip"]:
        ImageDraw.Draw(held).polygon([tuple(p) for p in outline], fill=255)
    source = Image.fromarray(feature(band) * np.asarray(held, np.float32) / 255)
    best = None
    for dturn in turns:
        for dscale in scales:
            turn, scale = each["turn"] + dturn, each["scale"] * dscale
            warped = small(np.asarray(carried(source, each, turn, scale, (page.shape[1], page.shape[0]))))
            r = reach // q
            score = signal.fftconvolve(np.pad(target, r), warped[::-1, ::-1], mode="valid")
            dy, dx = np.unravel_index(np.argmax(score), score.shape)
            found = (score[dy, dx] / (np.sqrt((warped ** 2).sum() * (target ** 2).sum()) + 1e-9), turn, scale, (dx - r) * q, (dy - r) * q)
            if best is None or found[0] > best[0]:
                best = found
    _, turn, scale, dx, dy = best
    each["turn"], each["scale"] = round(float(turn), 2), round(float(scale), 5)
    each["page"]["at"] = [round(each["page"]["at"][0] + dx, 1), round(each["page"]["at"][1] + dy, 1)]
    print(f"  {each['band']['src']} at {each['band']['at']}: turn {turn:.1f} scale {scale:.3f} slid {dx}, {dy} ({best[0]:.3f})")
    return each


def carried(image, each, turn, scale, size):
    """A picture of the band's, carried as a piece is onto the page's picture, size pixels."""
    bx, by = each["band"]["at"]
    px, py = each["page"]["at"]
    a = math.radians(turn)
    c, n = math.cos(a) * scale, math.sin(a) * scale
    # Image.transform maps the page's pixels back to the band's: the inverse of p + (c -n; n c)(x - b).
    det = c * c + n * n
    ia, ib, ic, id_ = c / det, n / det, -n / det, c / det
    return image.transform(size, Image.AFFINE, (ia, ib, bx - (ia * px + ib * py), ic, id_, by - (ic * px + id_ * py)), resample=Image.BILINEAR)


def piece(band_src, band_clip, band_at, page_src, page_clip, page_at, turn=0.0, scale=1.0):
    """One piece. A clip is a list of outlines, filled even-odd, so an outline inside another cuts a hole in it."""
    rounded = lambda outlines: [[[round(float(x), 1), round(float(y), 1)] for x, y in outline] for outline in outlines]
    return {
        "band": {"src": band_src, "clip": rounded(band_clip), "at": [round(float(band_at[0]), 1), round(float(band_at[1]), 1)]},
        "page": {"src": page_src, "clip": rounded(page_clip), "at": [round(float(page_at[0]), 1), round(float(page_at[1]), 1)]},
        "turn": round(float(turn), 2),
        "scale": round(float(scale), 5),
    }


def letter():
    """The letter's drawings, date and signature: each box of the folded strip's (letter.py STRIP), set in a row in the
    phone's band (letter.py band) and one under another down the wide screen's strip (letter.py strip), and where the
    page's ink has it, cut from the sheet at an offset found by matching. Returns the phone's pieces and the wide
    screen's."""
    import letter as made

    up = made.UP
    # Down the wide screen's strip: each row of boxes side by side, their feet level, where across it the row says.
    down = []
    top = made.STRIP_GAP * 3 // 4
    for across, boxes in made.STRIP:
        foot = top + max(y1 - y0 for _, y0, _, y1 in boxes)
        left = round(across * (made.STRIP_WIDTH - sum(x1 - x0 for x0, _, x1, _ in boxes)))
        for x0, y0, x1, y1 in boxes:
            down.append((left, foot - (y1 - y0)))
            left += x1 - x0
        top = foot + made.STRIP_GAP
    groups = [boxes for _, boxes in made.STRIP]
    tall = max(max(y1 - y0 for _, y0, _, y1 in boxes) for boxes in groups)
    placed = []
    left = 0
    for boxes in groups:
        high = max(y1 - y0 for _, y0, _, y1 in boxes)
        foot = (tall + high) // 2
        for x0, y0, x1, y1 in boxes:
            placed.append(((x0, y0, x1, y1), (left, foot - (y1 - y0))))
            left += x1 - x0
        left += made.BAND_GAP

    band_src, page_src = "/objects/letter-band.avif", "/objects/letter.avif"
    band, page = load(band_src)[..., 3], load(page_src)[..., 3]
    # The page's ink is cut close round it, so a box of the reference lies on it up and left by the cut. The largest
    # drawing is found on it, and the rest lie at the same offset.
    (x0, y0, x1, y1), (bx, by) = max(placed, key=lambda each: (each[0][2] - each[0][0]) * (each[0][3] - each[0][1]))
    ink = band[by * up : (by + y1 - y0) * up, bx * up : (bx + x1 - x0) * up]
    score = signal.fftconvolve(page - page.mean(), (ink - ink.mean())[::-1, ::-1], mode="valid")
    top, lft = np.unravel_index(np.argmax(score), score.shape)
    off = (x0 * up - lft, y0 * up - top)
    print(f"letter cut at {off}")
    pieces, wide = [], []
    for ((x0, y0, x1, y1), (bx, by)), (sx, sy) in zip(placed, down):
        w, h = (x1 - x0) * up, (y1 - y0) * up
        px, py = x0 * up - off[0], y0 * up - off[1]
        pieces.append(piece(band_src, [rect(bx * up, by * up, w, h)], (bx * up + w / 2, by * up + h / 2), page_src, [rect(px, py, w, h)], (px + w / 2, py + h / 2)))
        wide.append(piece("/objects/letter-strip.avif", [rect(sx * up, sy * up, w, h)], (sx * up + w / 2, sy * up + h / 2), page_src, [rect(px, py, w, h)], (px + w / 2, py + h / 2)))
    return pieces, wide


def poster():
    """The poster's sign and the windows a folded strip shows (poster.py): its two words and the three windows behind
    them, laid together as the band's middle, and the windows at its two ends, each to where it is on the poster."""
    import sys

    sys.path.insert(0, os.path.join(HERE, "poster"))
    import poster as made

    k = made.SCALE
    page_src = "/objects/poster.avif"
    pad = made.WORD_PAD * k
    words = [((x0 - made.WORD_PAD) * k, (base - made.RISE) * k - pad, (x1 - x0) * k + 2 * pad, (made.RISE + made.FALL) * k + 2 * pad) for x0, x1, base in made.WORDS]
    windows = {name: (x0 * k, y0 * k, (x1 - x0) * k, (y1 - y0) * k) for name, (x0, y0, x1, y1) in (("yellow", made.YELLOW), ("red", made.RED), ("balcony", made.BALCONY), ("sax", made.SAX), ("sitter", made.SITTER), ("candle", made.CANDLE), ("curtain", made.CURTAIN))}
    # What a word's box shares with a window stays with the window, so no two pieces lay the same light twice where
    # they land: the word's outline has each of those cut out of it. What it shares with a passage goes with the word,
    # whose letters run into the passages' boxes.

    def less(box, others):
        x, y, w, h = box
        holes = []
        for ox, oy, ow, oh in others:
            l, t, r, b = max(x, ox), max(y, oy), min(x + w, ox + ow), min(y + h, oy + oh)
            if l < r and t < b:
                holes.append(rect(l, t, r - l, b - t))
        # Holes that overlap each other would fill again, even-odd, so they are kept apart by trimming each against
        # those before it along whichever side overlaps least.
        kept = []
        for hole in holes:
            (l, t), (r, b) = hole[0], hole[2]
            for (kl, kt), _, (kr, kb), _ in kept:
                if l < kr and kl < r and t < kb and kt < b:
                    t = max(t, kb) if kb - t < r - l else t
                    l = max(l, kr) if not (kb - t < r - l) else l
            if l < r and t < b:
                kept.append(rect(l, t, r - l, b - t))
        return [rect(*box)] + kept

    def paired(boxes, tall):
        """Where pair() sets each of its windows, each set tall, PAIR_GAP apart: their boxes in its picture."""
        placed, left = [], 0
        for x, y, w, h in boxes:
            wide = round(w * tall / h) * k
            placed.append((left, 0, wide, tall * k))
            left += wide + made.PAIR_GAP * k
        return placed

    pieces = []
    # The band's middle: the sign's line over the windows behind it, both centred in it (folded_band).
    human_w = words[0][2]
    line_w = human_w + made.WORD_SPACE * k - 2 * pad + words[1][2]
    behind = paired([windows[n] for n in ("yellow", "red", "balcony")], made.BEHIND_TALL)
    behind_w = behind[-1][0] + behind[-1][2]
    middle = (max(line_w, behind_w), max(words[0][3], made.BEHIND_TALL * k))
    for name, (x, y, w, h) in zip(("human", "experience"), words):
        src = f"/objects/poster-band-{name}.avif"
        pieces.append(piece(src, [rect(0, 0, w, h)], (w / 2, h / 2), page_src, less((x, y, w, h), list(windows.values())), (x + w / 2, y + h / 2)))
    for name, (bx, by, bw, bh) in zip(("yellow", "red", "balcony"), behind):
        x, y, w, h = windows[name]
        pieces.append(piece("/objects/poster-band-behind.avif", [rect(bx, by, bw, bh)], (bx + bw / 2, by + bh / 2), page_src, [rect(x, y, w, h)], (x + w / 2, y + h / 2), scale=h / bh))
    for src, names in (("/objects/poster-band-start.avif", ("sax",)), ("/objects/poster-band-end.avif", ("candle", "curtain"))):
        for name, (bx, by, bw, bh) in zip(names, paired([windows[n] for n in names], made.BAND_WINDOWS)):
            x, y, w, h = windows[name]
            pieces.append(piece(src, [rect(bx, by, bw, bh)], (bx + bw / 2, by + bh / 2), page_src, [rect(x, y, w, h)], (x + w / 2, y + h / 2), scale=h / bh))
    # The wide screen's folded strip (folded_column): the sign's line turned a quarter clockwise down the middle of a
    # column as tall as the poster, a pair of windows above it and a pair below. Its two words overlap only in their
    # glow, which is shared between them halfway.
    column_w, column_h = (made.STRIP[1] - made.STRIP[0]) * k, Image.open(os.path.join(OBJECTS, "poster.avif")).size[1]
    deep = words[0][3]
    sign_left, sign_top = (column_w - deep) // 2, (column_h - line_w) // 2
    halfway = (human_w + line_w - words[1][2]) / 2
    wide = []
    for name, (x, y, w, h), (start, end) in zip(("human", "experience"), words, ((0, halfway), (halfway, line_w))):
        across = 0 if name == "human" else line_w - w
        at = (sign_left + deep / 2, sign_top + across + w / 2)
        wide.append(piece("/objects/poster-strip.avif", [rect(sign_left, sign_top + start, deep, end - start)], at, page_src, less((x, y, w, h), list(windows.values())), (x + w / 2, y + h / 2), turn=-90))
    room = made.GLOW_ROOM * k
    for names, top in ((("sax", "sitter"), sign_top - room - made.COLUMN_WINDOWS * k), (("candle", "curtain"), sign_top + line_w + room)):
        placed = paired([windows[n] for n in names], made.COLUMN_WINDOWS)
        left = (column_w - (placed[-1][0] + placed[-1][2])) // 2
        for name, (bx, by, bw, bh) in zip(names, placed):
            x, y, w, h = windows[name]
            wide.append(piece("/objects/poster-strip.avif", [rect(left + bx, top + by, bw, bh)], (left + bx + bw / 2, top + by + bh / 2), page_src, [rect(x, y, w, h)], (x + w / 2, y + h / 2), scale=h / bh))
    # Where the band's layers lie in its middle, as parts of it, for the page to lay them together.
    layers = {
        "size": [middle[0], middle[1]],
        "behind": [(middle[0] - behind_w) // 2, (middle[1] - made.BEHIND_TALL * k) // 2, behind_w, made.BEHIND_TALL * k],
        "human": [(middle[0] - line_w) // 2, (middle[1] - words[0][3]) // 2, words[0][2], words[0][3]],
        "experience": [(middle[0] - line_w) // 2 + line_w - words[1][2], (middle[1] - words[1][3]) // 2, words[1][2], words[1][3]],
    }
    return pieces, wide, layers


def desk():
    """The desk's things the band puts down in a row (desk.json band), each to where the wide plate has it. Both plates
    are DENSITY pixels to the em and the same things, so a thing only turns between them. Each is cut out by its box
    turned with it, a little larger for its shadow."""
    with open(os.path.join(ROOT, "src", "components", "mat", "desk.json")) as file:
        plates = json.load(file)
    density = 64
    boxes = {"ticket": (20.625, 9.375), "pick-fin": (3.145 * 1.6, 3.3 * 1.6), "pick-wedge": (2.76 * 1.6, 3.125 * 1.6), "razor": (17.5, 7.3), "card": (14.8 * 1.3, 8.46 * 1.3)}
    # How much more than its box each thing is cut by, in em, on the band, where nothing lies near it, and on the
    # page, where its neighbours do.
    room = {"ticket": (1.6, 0.9), "pick-fin": (0.8, 0.5), "pick-wedge": (0.8, 0.5), "razor": (1.2, 0.7), "card": (1.2, 0.9)}
    pieces = []
    for name, (w, h) in boxes.items():
        bx, by, br = plates["band"]["at"][name]
        px, py, pr = plates["wide"]["at"][name]
        band_room, page_room = room[name]
        band_clip = turned_rect(bx * density, by * density, (w + 2 * band_room) * density, (h + 2 * band_room) * density, br)
        page_clip = turned_rect(px * density, py * density, (w + 2 * page_room) * density, (h + 2 * page_room) * density, pr)
        pieces.append(piece("/objects/mat/desk-band.avif", [band_clip], (bx * density, by * density), "/objects/mat/desk-wide.avif", [page_clip], (px * density, py * density), turn=pr - br))
    named = dict(zip(boxes, pieces))
    # The two picks lie close on both plates, so each is cut short of the line halfway between them.
    for side in ("band", "page"):
        fin, wedge = named["pick-fin"][side], named["pick-wedge"][side]
        a, b = apart(fin["at"], wedge["at"])
        fin["clip"] = [beyond(fin["clip"][0], a, b)]
        wedge["clip"] = [beyond(wedge["clip"][0], b, a)]
    # On the page the razor lies along the Proraso tube, all but touching it: it is cut short of the tube's edge.
    razor = named["razor"]["page"]
    razor["clip"] = [beyond(razor["clip"][0], (2925, 2600), (2775, 1000))]
    for each in pieces:
        # The razor stands highest off the desk, so the two cameras see it leaning furthest apart.
        refine(each, reach=192 if each is named["razor"] else 48)
    return pieces


def contact():
    """The contact set (scene.py): the Leica, the stamps and the ticket, each from its place in the band to its place on
    the open page. Both photographs are 72 pixels to the em. In the band the stamps and the ticket lie a quarter turn
    and a little clockwise, the Leica lies all but level and 1.75 times its page's size. The two photographs are cut
    into three parts each, between the things, so every pixel of each goes with one of them."""
    density = 72
    open_x, open_y = -14.0, -8.0
    stamp_w, stamp_h, beside, bleed, w, h = 5.6, 6.6 * 3, 5.6 + 1.0, 1.2, 15.0, 27.45
    frame_h = h + 2 * bleed
    page = {
        "camera": (3.7, 1.7),
        "stamps": (0.5 + stamp_w / 2, frame_h - stamp_h - 1.0 + stamp_h / 2),
        "ticket": (beside + bleed + w / 2, bleed + h / 2),
    }
    band = {"camera": (11.2, 9.8), "stamps": (36.0, 8.2), "ticket": (67.0, 8.0)}
    # Clockwise, from the band's to the page's: the Leica turned from 4 degrees anticlockwise of level to 80, the
    # stamps and the ticket back from a quarter turn and 3 and -1 degrees more.
    turn = {"camera": -76.0, "stamps": -93.0, "ticket": -89.0}
    scale = {"camera": 1 / 1.75, "stamps": 1.0, "ticket": 1.0}
    band_src, page_src = "/objects/contact-band.avif", "/objects/contact-open.avif"
    bw, bh = Image.open(os.path.join(OBJECTS, "contact-band.avif")).size
    pw, ph = Image.open(os.path.join(OBJECTS, "contact-open.avif")).size
    # The cuts: in the band, across it, before the stamps and before the ticket; on the page, down it past the Leica and
    # the stamps, and across it between the two, in em of each.
    stamps_from, ticket_from = 24.0, 49.5
    right_of, below = (beside + bleed - 0.75 - open_x) * density, (7.75 - open_y) * density
    band_clips = {
        "camera": [rect(0, 0, stamps_from * density, bh)],
        "stamps": [rect(stamps_from * density, 0, (ticket_from - stamps_from) * density, bh)],
        "ticket": [rect(ticket_from * density, 0, bw - ticket_from * density, bh)],
    }
    page_clips = {
        "camera": [rect(0, 0, right_of, below)],
        "stamps": [rect(0, below, right_of, ph - below)],
        "ticket": [rect(right_of, 0, pw - right_of, ph)],
    }
    pieces = [
        piece(band_src, band_clips[name], (band[name][0] * density, band[name][1] * density), page_src, page_clips[name], ((page[name][0] - open_x) * density, (page[name][1] - open_y) * density), turn=turn[name], scale=scale[name])
        for name in ("camera", "stamps", "ticket")
    ]
    # The Leica's turn and size on the page are its prop's own (leica.py), so they are matched too.
    refine(pieces[0], turns=(-3, -1.5, 0, 1.5, 3), scales=(0.97, 1, 1.03))
    for each in pieces[1:]:
        refine(each)
    return pieces


def bare_light(pieces, side, proofs=None, everything=False):
    """The lamp's light on the desk's mat (desk.py light_map), on the band's plate or the page's, as it would be without
    the things that travel between them, for the mat to be lit by while they are on their way: each light map has them
    in it, their shadows and the dark under them, where they are not. Each is taken out, a little past its outline, and the
    light filled in from round it, which is smooth there. What lies under another thing's dark, or at its edge, is not filled from.
    With everything, every thing on the plate is taken out, for the rest of the page's things to come in and go with
    their shadows."""
    named = {"band": "band", "page": "wide"}[side]
    plate = json.load(open(os.path.join(ROOT, "src", "components", "mat", "desk.json")))[named]
    bleed_x, bleed_y = plate["bleed"]
    density, map_density = 64, 32
    # Where the plate's things lie: all but opaque there, as only the darkest of their shadows, right at their feet, is.
    alpha = load(f"/objects/mat/desk-{named}.avif")[..., 3]
    for name in ("light", "light-past"):
        source = os.path.join(OBJECTS, "mat", f"desk-{named}-{name}.avif")
        light = np.asarray(Image.open(source).convert("RGB")).astype(np.float32) / 255
        rows, cols = light.shape[:2]
        held = Image.new("L", (cols, rows), 0)
        for each in pieces:
            for outline in each[side]["clip"]:
                ImageDraw.Draw(held).polygon([((x / density + bleed_x) * map_density, (y / density + bleed_y) * map_density) for x, y in outline], fill=255)
        if everything:
            shown = np.zeros((rows, cols), bool)
            x, y = bleed_x * map_density, bleed_y * map_density
            seen = np.asarray(Image.fromarray(alpha).resize((alpha.shape[1] * map_density // density, alpha.shape[0] * map_density // density), Image.BILINEAR)) > 0.05
            shown[y : y + seen.shape[0], x : x + seen.shape[1]] = seen
            # The props the page lays from cameras of their own (desk.py PORTRAITS) are not in the plate: all the picture
            # of each covers.
            for seen in json.load(open(os.path.join(ROOT, "src", "components", "mat", "portrait.json")))[named].values():
                bx, by, bw, bh = seen["picture"]
                shown[int((by + bleed_y) * map_density) : int((by + bh + bleed_y) * map_density), int((bx + bleed_x) * map_density) : int((bx + bw + bleed_x) * map_density)] = True
            # The things' shadows run further from them than the pieces' do from theirs, for some stand taller.
            shown = ndimage.binary_dilation(shown, iterations=int(2.2 * map_density))
            held = Image.fromarray(shown.astype(np.uint8) * 255) if not pieces else Image.fromarray(np.maximum(np.asarray(held), shown.astype(np.uint8) * 255))
        hole = ndimage.binary_dilation(np.asarray(held) > 0, iterations=int(1.2 * map_density))
        # The light on a coarse grid, the hole's pixels and every other thing's dark left free, the rest held, and the
        # free ones relaxed until each is the mean of its neighbours: the smoothest light that meets what is round it.
        q = 8
        coarse = light[: rows // q * q, : cols // q * q].reshape(rows // q, q, cols // q, q, 3).mean((1, 3))
        taken = hole[: rows // q * q, : cols // q * q].reshape(rows // q, q, cols // q, q).any((1, 3))
        # Under every thing on the plate the light is never seen, so none of it is filled from: the plate's things, as
        # the coarse grid lies over them, a cell and a little more round each.
        cell = density * q // map_density
        things = np.zeros_like(taken)
        x0, y0 = bleed_x * map_density // q, bleed_y * map_density // q
        under = alpha[: alpha.shape[0] // cell * cell, : alpha.shape[1] // cell * cell].reshape(alpha.shape[0] // cell, cell, alpha.shape[1] // cell, cell).max((1, 3)) > 0.9
        things[y0 : y0 + under.shape[0], x0 : x0 + under.shape[1]] = under
        free = taken | ndimage.binary_dilation(things, iterations=2)
        # Begun from the light round it, spread wide, so the relaxing has only the last of the way to go.
        known = (~free).astype(np.float32)
        spread = np.stack([ndimage.gaussian_filter(coarse[..., c] * known, 24) for c in range(3)], -1) / np.maximum(ndimage.gaussian_filter(known, 24), 1e-6)[..., None]
        fill = np.where(free[..., None], spread, coarse)
        for _ in range(6000):
            mean = (np.roll(fill, 1, 0) + np.roll(fill, -1, 0) + np.roll(fill, 1, 1) + np.roll(fill, -1, 1)) / 4
            fill = np.where(free[..., None], mean, coarse)
        smooth = np.stack([np.asarray(Image.fromarray(fill[..., c].astype(np.float32)).resize((cols, rows), Image.BILINEAR)) for c in range(3)], -1)
        # Its edge eases into the light round it.
        weight = np.clip(ndimage.gaussian_filter(hole.astype(np.float32), 6), 0, 1)
        weight = np.maximum(weight, hole)[..., None]
        bare = light * (1 - weight) + smooth * weight
        kept = "empty" if everything else "bare"
        out = os.path.join(OBJECTS, "mat", f"desk-{named}-{name}-{kept}.avif")
        Image.fromarray((np.clip(bare, 0, 1) * 255 + 0.5).astype(np.uint8)).save(out, quality=98, subsampling="4:4:4", speed=2)
        if proofs:
            Image.fromarray((np.clip(bare, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((cols // 4, rows // 4)).save(os.path.join(proofs, f"desk-{named}-{name}-{kept}.png"))
        print(f"wrote {out}")


def proof(name, pieces, folder):
    """The band and the page with the outlines on them, and the band's pieces carried onto the page over it, faint."""
    os.makedirs(folder, exist_ok=True)
    pages = {}
    for each in pieces:
        pages.setdefault(each["page"]["src"], load(each["page"]["src"]))
    page_src = pieces[0]["page"]["src"]
    page = pages[page_src]
    shown = np.dstack((page[..., :3] * page[..., 3:] + 0.25 * (1 - page[..., 3:]), np.ones(page.shape[:2])))
    canvas = Image.fromarray((shown * 255).astype(np.uint8))
    for each in pieces:
        band = load(each["band"]["src"])
        cut = Image.new("L", (band.shape[1], band.shape[0]), 0)
        for outline in each["band"]["clip"]:
            ImageDraw.Draw(cut).polygon([tuple(p) for p in outline], fill=255)
        alpha = band[..., 3] * np.asarray(cut, np.float32) / 255
        moved = Image.fromarray((np.dstack((band[..., :3], alpha * 0.6)) * 255).astype(np.uint8))
        canvas.alpha_composite(carried(moved, each, each["turn"], each["scale"], canvas.size))
    draw = ImageDraw.Draw(canvas)
    for each in pieces:
        for outline in each["page"]["clip"]:
            draw.polygon([tuple(p) for p in outline], outline=(255, 40, 200, 255), width=4)
    canvas.convert("RGB").save(os.path.join(folder, f"{name}-page.png"))
    for src in sorted({each["band"]["src"] for each in pieces}):
        band = load(src)
        image = Image.fromarray((np.dstack((band[..., :3] * band[..., 3:] + 0.25 * (1 - band[..., 3:]), np.ones(band.shape[:2]))) * 255).astype(np.uint8))
        draw = ImageDraw.Draw(image)
        for each in pieces:
            if each["band"]["src"] == src:
                for outline in each["band"]["clip"]:
                    draw.polygon([tuple(p) for p in outline], outline=(255, 40, 200, 255), width=4)
        image.convert("RGB").save(os.path.join(folder, f"{name}-band-{os.path.basename(src).split('.')[0]}.png"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof")
    args = parser.parse_args()
    import sys

    sys.path.insert(0, HERE)
    poster_pieces, poster_wide, layers = poster()
    letter_pieces, letter_wide = letter()
    folds = {"letter": letter_pieces, "poster": poster_pieces, "desk": desk(), "contact": contact(), "letter-wide": letter_wide, "poster-wide": poster_wide}
    for side in ("band", "page"):
        bare_light(folds["desk"], side, args.proof)
    bare_light(folds["desk"], "page", args.proof, everything=True)
    if args.proof:
        for name, pieces in folds.items():
            proof(name, pieces, args.proof)
    # How many pixels each picture is, so the page can tell how large it lays each.
    sizes = {src: list(Image.open(os.path.join(ROOT, "public", src.lstrip("/"))).size) for pieces in folds.values() for each in pieces for src in (each["band"]["src"], each["page"]["src"])}
    with open(OUT, "w") as file:
        file.write(json.dumps({"sizes": sizes, "layers": {"poster": layers}, **folds}, separators=(",", ":")) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
