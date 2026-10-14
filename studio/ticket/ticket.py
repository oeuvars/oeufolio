"""The contact page's cinema ticket, photographed lying on the page. It is bright white uncoated ticket card,
risograph printed in four spot inks, black, vermilion, teal and yellow, as the illustrated tickets the page follows
are: each ink a stencil laid down on its own pass, translucent, so where two overlap they mix into a third colour,
and never quite in register with the others. It has bites along both ends and a notch either side of the line it was
meant to tear along. It has been carried: folded once along the tear line, its top corner dog-eared and put back,
its edges a little scuffed. Then the same ticket with the conductor's punch through it, and a roll of the small
tickets for the strip. Run from the repository root, after studio/ticket/ink.py and studio/ticket/plate.mjs:

    blender -b --factory-startup -P studio/ticket/ticket.py -- [ticket punched roll ...] [--scale 0.5] [--samples 64] [--proofs DIR]

Writes public/objects/ticket.avif, the ticket and the shadow it leaves; public/objects/ticket-punched.avif, the same
with the conductor's punch through it, for the page to show in its place; and public/objects/ticket-roll.avif, the roll. Uses the
copy stand from the oeusume studio, so it is lit as every other object on the site is. Set OEUSUME if that checkout
is not in ~/Documents/oeusume.

Every measure is in the ticket's em, from src/components/ticket/ticket.json, which the page reads too. What is
printed comes from the page's own type, captured by plate.mjs into studio/ticket/art as one plate per ink
(plate-<ink>.png), so the words in the photograph sit under the page's live words; from hand.py's note in the
reference's own handwriting (hand.png); and from ink.py's plates of the picture (river-<ink>.png for the ticket, river-tower-<ink>.png for the strip's).
"""

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OEUSUME = os.environ.get("OEUSUME", os.path.expanduser("~/Documents/oeusume"))
sys.path.insert(0, os.path.join(OEUSUME, "studio"))

import numpy as np  # noqa: E402

import stage as stage_module  # noqa: E402
from paint import blur, box, cloud, disc, segment  # noqa: E402
from stage import Stage  # noqa: E402
from stock import Sheet, drift, fit, pixels_of  # noqa: E402

TICKET = json.load(open(os.path.join(ROOT, "src", "components", "ticket", "ticket.json")))
W, H = TICKET["size"]
BLEED = TICKET["bleed"]
PANEL = "#861812"  # the red leather the ticket lies on (leather.py), which lights it from below
CARD = "#f6f5f0"  # bright white uncoated card
# The four riso inks, in the order the press laid them down, and how far each pass landed off true, in em.
INKS = (("yellow", "#ffd23f", (0.035, -0.02)), ("teal", "#0f8b8d", (-0.025, 0.03)), ("red", "#ff4a3d", (0.02, 0.025)), ("k", "#121212", (0.0, 0.0)))
GRIME = "#7a7770"
ART = os.path.join(HERE, "art")
OUT = os.path.join(ROOT, "public", "objects")
SHARP = 1.5  # the page shows the ticket at up to 72 pixels to its em
EXPOSURE = 0.3  # matte white card reads grey at the stand's usual exposure


def placed(sheet, coverage, x0, y0, w, h):
    """An array of ink coverage, rows from the top, laid into the sheet over the box at x0, y0, w by h em."""
    out = np.zeros(sheet.height.shape)
    rows, cols = round(h * sheet.ppe), round(w * sheet.ppe)
    ink = fit(coverage[..., None], rows, cols)[..., 0]
    r0, c0 = round(y0 * sheet.ppe), round(x0 * sheet.ppe)
    r1, c1 = min(out.shape[0], r0 + rows), min(out.shape[1], c0 + cols)
    out[max(0, r0) : r1, max(0, c0) : c1] = ink[max(0, -r0) : r1 - r0, max(0, -c0) : c1 - c0]
    return np.clip(out, 0, 1)


def plate(sheet, ink, view, x0=0.0, y0=0.0, scale=1.0):
    """What one ink prints on one ticket, laid at x0, y0 on the sheet and scaled: the type plate.mjs captured for it,
    if the type is printed in it, and ink.py's plate of the picture named by view, cut to fill the picture's box as
    the page's background-size: cover does."""
    out = np.zeros(sheet.height.shape)
    path = os.path.join(ART, f"plate-{ink}.png")
    if os.path.exists(path):
        stored = pixels_of(path)[..., :3].astype(np.float64)
        out = printer(sheet, placed(sheet, 1 - stored.mean(axis=-1), x0, y0, W * scale, H * scale), seed={"k": 5, "red": 7, "teal": 9}[ink], scale=scale)
    if ink == "k":
        # The note along the foot, in the reference's own hand (hand.py), printed with the rest of the black.
        nx, ny, nw, nh = TICKET["note"]
        hand = pixels_of(os.path.join(ART, "hand.png"))[..., 0].astype(np.float64)
        written = placed(sheet, hand, x0 + nx * scale, y0 + ny * scale, nw * scale, nh * scale)
        # A marker's line is already as heavy as it will be: it only wicks a little into the card.
        out = np.maximum(out, np.clip(blur(written, 0.6 * sheet.ppe * scale / 96) * 1.15, 0, 1))
    art = pixels_of(os.path.join(ART, f"{view}-{ink}.png"))[..., 0].astype(np.float64)
    ax, ay, aw, ah = TICKET["art"]
    rows, cols = art.shape
    if aw / ah < cols / rows:
        keep = round(rows * aw / ah)
        art = art[:, (cols - keep) // 2 : (cols - keep) // 2 + keep]
    else:
        keep = round(cols * ah / aw)
        art = art[(rows - keep) // 2 : (rows - keep) // 2 + keep]
    return np.maximum(out, placed(sheet, art, x0 + ax * scale, y0 + ay * scale, aw * scale, ah * scale))


def smooth(lo, hi, x):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def line(sheet, a, b):
    """Signed distance across the line through a and b, in em."""
    (ax, ay), (bx, by) = a, b
    length = math.hypot(bx - ax, by - ay)
    return ((sheet.X - ax) * (by - ay) - (sheet.Y - ay) * (bx - ax)) / length


def printer(sheet, m, seed, scale=1.0):
    """The type as a printer puts it on card, not as a screen draws it. The ink spreads into the card, so every
    stroke is heavier than the type it was set in and the small counters half close; its edge follows the fibres it
    soaked into and is nowhere crisp. The drum or ribbon never inks evenly: slow patches are lighter, a faint band
    runs across the feed, and solids have pinholes where it missed. Stray specks of ink land round the letters."""
    rows, cols = m.shape
    px = sheet.ppe * scale / 96  # the measures below are in pixels of the full-size ticket's sheet
    fibres = cloud((rows, cols), seed, falloff=0.5)
    fibres /= max(1e-6, np.abs(fibres).max())
    gained = smooth(0.16, 0.4, blur(m, 2.1 * px) + 0.12 * fibres)
    # The ink is dense where it lies thick and thins only at its edges, where it wicked out into the card.
    wicked = np.maximum(gained * 0.92, blur(gained, 0.9 * px))
    wicked = smooth(0.0, 0.55, wicked)
    patches = np.clip(cloud((rows, cols), seed + 1, falloff=1.4) * 0.05 + 0.97, 0.85, 1.0)
    band = 1 - 0.05 * smooth(0.55, 1.0, np.sin(2 * np.pi * sheet.Y / (1.7 * scale)) * 0.5 + 0.5)
    holes = smooth(2.3, 2.8, cloud((rows, cols), seed + 2, falloff=0.15))
    near = smooth(0.02, 0.2, blur(m, 7 * px)) * (1 - smooth(0.2, 0.5, gained))
    specks = smooth(2.9, 3.3, cloud((rows, cols), seed + 3, falloff=0.12)) * near
    return np.clip(wicked * patches * band * (1 - 0.85 * holes) + 0.8 * specks, 0, 1)


def riso(sheet, plates, seed, scale=1.0):
    """Print the plates as a risograph does, one pass per ink. Each ink goes down through its stencil a little off
    true from the others; it is translucent, so it multiplies with whatever is under it; it is thin and soaks into
    the card, a touch heavier at the edges of a shape and mottled across a solid, with the odd pin hole where the
    drum skipped. The ink stays as matte as the card. plates maps each ink to its coverage. Returns where anything
    printed."""
    rows, cols = sheet.height.shape
    printed = np.zeros((rows, cols))
    for i, (name, colour, (dx, dy)) in enumerate(INKS):
        m = plates.get(name)
        if m is None:
            continue
        m = np.roll(m, (round(dy * scale * sheet.ppe), round(dx * scale * sheet.ppe)), axis=(0, 1))
        fibres = cloud((rows, cols), seed + 10 * i, falloff=0.55)
        fibres /= max(1e-6, np.abs(fibres).max())
        m = np.clip(blur(m, 0.5) + 0.05 * fibres * (m > 0.05), 0, 1)
        rim = np.clip(blur(m, 0.6) - blur(m, 2.6), 0, 1)
        # Black goes down dense; the colours thinner, and mottled across a solid.
        mottle = 1.0 if name == "k" else np.clip(cloud((rows, cols), seed + 10 * i + 1, falloff=1.2) * 0.07 + 0.93, 0.8, 1)
        skip = cloud((rows, cols), seed + 10 * i + 2, falloff=0.2) > 2.5
        strength = np.clip((0.94 if name != "k" else 1.0) * mottle * (1 - 0.9 * skip) + 0.05 * rim, 0, 1)
        sheet.ink(m, colour, strength)
        printed = np.maximum(printed, m)
    sheet.finish(printed, rough=0.93)
    return printed


def star(sheet, cx, cy, outer, inner, turn=0.0):
    """Signed distance to a five-pointed star, as a conductor's punch cuts it. Only worked out near the star."""
    d = np.full(sheet.height.shape, 1.0)
    rs, cs = sheet.window(cx - outer - 0.1, cy - outer - 0.1, cx + outer + 0.1, cy + outer + 0.1)
    X, Y = sheet.X[rs, cs], sheet.Y[rs, cs]
    points = []
    for k in range(10):
        a = math.radians(turn - 90) + k * math.pi / 5
        r = outer if k % 2 == 0 else inner
        points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    edge = np.full(X.shape, np.inf)
    inside = np.zeros(X.shape, dtype=bool)
    for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
        edge = np.minimum(edge, segment(X, Y, ax, ay, bx, by))
        inside ^= ((ay > Y) != (by > Y)) & (X < (bx - ax) * (Y - ay) / (by - ay + 1e-12) + ax)
    d[rs, cs] = np.where(inside, -edge, edge)
    return d


def die(sheet, x0, y0, scale):
    """Cut one ticket's shape into the sheet, at x0, y0 and scale: the bites along its two ends and the notches
    either side of its tear line. On the roll a ticket's end bites fall on the next one's and make whole holes."""
    s = scale
    bites = TICKET["bites"]
    first = (W - (bites["count"] - 1) * bites["pitch"]) / 2
    for k in range(bites["count"]):
        bx = x0 + (first + k * bites["pitch"]) * s
        for end in (y0, y0 + H * s):
            sheet.punch(disc(sheet.X, sheet.Y, bx, end, bites["radius"] * s))
    for ny in TICKET["notches"]:
        for nx in (x0, x0 + W * s):
            sheet.punch(disc(sheet.X, sheet.Y, nx, y0 + ny * s, TICKET["notch"] * s))


def carried(sheet, printed, seed, scale=1.0, folded=True):
    """What being carried did to it. It was folded once along the tear line: a valley there, the ink cracked white
    where the fold broke the card's surface, a faint grey worked into the crease. The dog-ear is a second, softer
    crease. The ink is rubbed a little thin at the edges, the edges are scuffed grey, and the cut edge is no longer
    clean. It has not yellowed: the card is still white."""
    rows, cols = sheet.height.shape
    paper = sheet.rgb.copy()
    inside = np.clip(-sheet.sdf, 0, None) / scale
    worn = (1 - smooth(0.0, 0.7, inside)) * smooth(1.6, 2.8, cloud((rows, cols), seed, falloff=0.9) + 2.2)
    sheet.rgb += (printed * worn * 0.35)[..., None] * (paper - sheet.rgb)
    sheet.ink((1 - smooth(0.0, 0.12, inside)) * 0.5, GRIME, 0.25)
    if folded:
        for key, depth, crack in (("fold", 0.012, 1.0), ("ear", 0.007, 0.5)):
            a, b = TICKET[key]
            d = line(sheet, a, b)
            valley = np.exp(-((d / 0.05) ** 2))
            sheet.height -= depth * valley - 0.25 * depth * np.exp(-(((np.abs(d) - 0.12) / 0.06) ** 2))
            fibre = smooth(-0.4, 0.8, cloud((rows, cols), seed + 4, falloff=0.5))
            split = np.exp(-((d / 0.02) ** 2)) * fibre * crack
            sheet.rgb += (printed * split)[..., None] * (paper - sheet.rgb)
            sheet.ink(np.exp(-((d / 0.12) ** 2)) * 0.5, GRIME, 0.12 * crack)
            sheet.finish(valley, rough=0.97)
    fray = cloud((rows, cols), seed + 5, falloff=0.45)
    sheet.sdf = sheet.sdf + 0.02 * scale * fray / max(1e-6, np.abs(fray).max())
    sheet.cut(box(sheet.X, sheet.Y, 0, 0, sheet.w, sheet.h, 0.25 * scale))


def warp(base):
    """How the old ticket lies: never flat, its two halves rising a little either side of the fold, and the
    dog-eared corner standing up off the page."""
    (fx0, fy0), (fx1, fy1) = TICKET["fold"]
    fl = math.hypot(fx1 - fx0, fy1 - fy0)
    (ex0, ey0), (ex1, ey1) = TICKET["ear"]
    el = math.hypot(ex1 - ex0, ey1 - ey0)

    def z(x, y):
        fold = ((x - fx0) * (fy1 - fy0) - (y - fy0) * (fx1 - fx0)) / fl
        ear = ((x - ex0) * (ey1 - ey0) - (y - ey0) * (ex1 - ex0)) / el
        return base(x, y) + 0.03 * np.sqrt(fold * fold + 0.1) + 0.28 * np.clip(-ear, 0, None) ** 1.3

    return z


def card(w, h, seed):
    sheet = Sheet(w, h, CARD, rough=0.9)
    rows, cols = sheet.height.shape
    sheet.rgb *= (1 + 0.025 * cloud((rows, cols), seed, falloff=1.8))[..., None]
    return sheet


def build(sheet, name, warp):
    return sheet.build(
        STAGE,
        name,
        thickness=0.05,
        warp=warp,
        scan="Paper001",
        scan_size=6,
        scan_normal=0.8,
        scan_rough=0.4,
        scan_colour=0.2,
        wear=(("SurfaceImperfections003", 9, 0.1, 0.002), ("Scratches003", 7, 0.05, 0.0015), ("Fingerprints009", 5, 0.05, 0)),
        fibre=0.002,
        fibre_scale=42,
        sheen=0.0,
        specular=0.04,
    )


def ticket(punched):
    sheet = card(W, H, 3)
    printed = riso(sheet, {name: plate(sheet, name, "river") for name, _, _ in INKS}, 5)
    if punched:
        px, py, pr = TICKET["punch"]
        sheet.punch(star(sheet, px, py, pr, pr * 0.45, turn=8))
    die(sheet, 0, 0, 1)
    carried(sheet, printed, 21)
    sheet.soften(0.06, 0.02)
    build(sheet, "ticket", warp(drift(W, H, 0.1, 11)))
    return STAGE.shoot("ticket-punched" if punched else "ticket", (0, 0, W, H), bleed=BLEED, shadow=0.75, sharp=SHARP, exposure=EXPOSURE)


def roll():
    """The roll: the same ticket at a third of the size, again and again, each joined to the next where their
    bites meet, so that the bites there are whole round holes. Its picture is its own: a look up the near tower."""
    spec = TICKET["roll"]
    s, count = spec["scale"], spec["count"]
    w, h = W * s, H * s * count
    sheet = card(w, h, 13)
    plates = {}
    for name, _, _ in INKS:
        plates[name] = np.zeros(sheet.height.shape)
        for i in range(count):
            plates[name] = np.maximum(plates[name], plate(sheet, name, "river-tower", 0, i * H * s, s))
    printed = riso(sheet, plates, 17, scale=s)
    for i in range(count):
        die(sheet, 0, i * H * s, s)
    carried(sheet, printed, 23, scale=s, folded=False)
    sheet.soften(0.03, 0.012)
    build(sheet, "ticket-roll", drift(w, h, 0.1, 19))
    shown = spec["shown"] * H * s
    return STAGE.shoot("ticket-roll", (0, (h - shown) / 2, w, shown), bleed=0.5, shadow=0.75, sharp=1.0, exposure=EXPOSURE)


SHOTS = {"ticket": lambda: ticket(False), "punched": lambda: ticket(True), "roll": roll}

parser = argparse.ArgumentParser()
parser.add_argument("shots", nargs="*")
parser.add_argument("--scale", type=float, default=1.0)
parser.add_argument("--samples", type=int, default=160)
parser.add_argument("--proofs")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
unknown = [name for name in args.shots if name not in SHOTS]
if unknown:
    sys.exit(f"Unknown shots: {', '.join(unknown)}. Known: {', '.join(SHOTS)}")
os.makedirs(OUT, exist_ok=True)
if args.proofs:
    os.makedirs(args.proofs, exist_ok=True)
stage_module.MAT = PANEL
STAGE = Stage(OUT, args.proofs, scale=args.scale, samples=args.samples)
for name in args.shots or SHOTS:
    STAGE.clear()
    SHOTS[name]()
