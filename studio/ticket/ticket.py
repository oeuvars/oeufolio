"""The contact page's cinema ticket, photographed lying on the page. It is bright white uncoated ticket card,
risograph printed in four spot inks, black, vermilion, teal and yellow, as the illustrated tickets the page follows
are: each ink a stencil laid down on its own pass, translucent, so where two overlap they mix into a third colour,
and never quite in register with the others. It has bites along both ends and a notch either side of the line it was
meant to tear along. The email address was typed on at the box office. It has been carried: folded once along the
tear line, its top corner dog-eared and put back, its edges a little scuffed. Then the same ticket with the
conductor's punch through it, and the strip of stamps that lies beside it. Run from the repository root, after
studio/ticket/ink.py, hand.py, cats.py, typed.py, stamps.py and plate.mjs:

    blender -b --factory-startup -P studio/ticket/ticket.py -- [ticket punched stamps ...] [--scale 0.5] [--samples 64] [--proofs DIR]

Writes public/objects/ticket.avif, the ticket and the shadow it leaves; public/objects/ticket-punched.avif, the same
with the conductor's punch through it, for the page to show in its place; and public/objects/ticket-stamps.avif, the
stamps. Uses the copy stand from the oeusume studio, so it is lit as every other object on the site is. Set OEUSUME
if that checkout is not in ~/Documents/oeusume.

Every measure is in the ticket's em, from src/components/ticket/ticket.json, which the page reads too. What is
printed comes from the page's own type, captured by plate.mjs into studio/ticket/art as one plate per ink
(plate-<ink>.png), so the words in the photograph sit under the page's live words; from hand.py's note in the
reference's own handwriting (hand.png); from cats.py's cats, one for each link (cat-<name>.png); from typed.py's
strikes of a typewriter (typed.png); and from ink.py's plates of the picture (river-<ink>.png for the ticket,
river-tower-, river-boat- and river-span-<ink>.png for the stamps).
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
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import key as key_light  # noqa: E402
import stage as stage_module  # noqa: E402
from paint import blur, box, cloud, disc, segment  # noqa: E402
from stage import Stage  # noqa: E402
from stock import Sheet, drift, fit, pixels_of  # noqa: E402

TICKET = json.load(open(os.path.join(ROOT, "src", "components", "ticket", "ticket.json")))
W, H = TICKET["size"]
BLEED = TICKET["bleed"]
PANEL = "#651415"  # the red leather the ticket lies on (leather.py), which lights it from below
CARD = "#f6f5f0"  # bright white uncoated card
# The four riso inks, in the order the press laid them down, and how far each pass landed off true, in em.
INKS = (("yellow", "#ffd23f", (0.035, -0.02)), ("teal", "#0f8b8d", (-0.025, 0.03)), ("red", "#ff4a3d", (0.02, 0.025)), ("k", "#121212", (0.0, 0.0)))
MM = 15 / 60  # em to the millimetre: the ticket is about 60 mm across its 15 em
RIDGE = 0.3  # mm the fold stands up, pressed out again
EAR = 1.5  # mm the dog-ear's tip stands off the table
RIBBON = "#24201d"  # a typewriter ribbon's black
GRIME = "#7a7770"
ART = os.path.join(HERE, "art")
OUT = os.path.join(ROOT, "public", "objects")
SHARP = 1.5  # the page shows the ticket at up to 72 pixels to its em
EXPOSURE = 0.3  # matte white card reads grey at the stand's usual exposure
KEYED = -2.5  # the stops taken off what the key lamp (key.py) lights, which is about five times the stand's room again


def placed(sheet, coverage, x0, y0, w, h):
    """An array of ink coverage, rows from the top, laid into the sheet over the box at x0, y0, w by h em."""
    out = np.zeros(sheet.height.shape)
    rows, cols = round(h * sheet.ppe), round(w * sheet.ppe)
    ink = fit(coverage[..., None], rows, cols)[..., 0]
    r0, c0 = round(y0 * sheet.ppe), round(x0 * sheet.ppe)
    r1, c1 = min(out.shape[0], r0 + rows), min(out.shape[1], c0 + cols)
    out[max(0, r0) : r1, max(0, c0) : c1] = ink[max(0, -r0) : r1 - r0, max(0, -c0) : c1 - c0]
    return np.clip(out, 0, 1)


def cover(art, w, h):
    """The middle of a picture, cut to the shape of a w by h box, as background-size: cover cuts it."""
    rows, cols = art.shape
    if w / h < cols / rows:
        keep = round(rows * w / h)
        return art[:, (cols - keep) // 2 : (cols - keep) // 2 + keep]
    keep = round(cols * h / w)
    return art[(rows - keep) // 2 : (rows - keep) // 2 + keep]


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
        # The cats where the usernames would be (cats.py). They are pen drawings, as the note is: printed as their
        # lines were drawn, a little heavier where the ink wicked, and not thinned and broken as type is.
        for entry in TICKET["cats"]:
            bx, by, bw, bh = entry["box"]
            cat = pixels_of(os.path.join(ART, f"cat-{entry['cat']}.png"))[..., 0].astype(np.float64)
            drawn = placed(sheet, cat, x0 + bx * scale, y0 + by * scale, bw * scale, bh * scale)
            out = np.maximum(out, np.clip(blur(drawn, 0.6 * sheet.ppe * scale / 96) * 1.4, 0, 1))
    art = pixels_of(os.path.join(ART, f"{view}-{ink}.png"))[..., 0].astype(np.float64)
    ax, ay, aw, ah = TICKET["art"]
    return np.maximum(out, placed(sheet, cover(art, aw, ah), x0 + ax * scale, y0 + ay * scale, aw * scale, ah * scale))


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
    """How the carried ticket lies, as photographs of carried tickets lying on a table show it: flat. Card folded and
    pressed out again keeps a low ridge along the fold, and a dog-ear, put back, stands its tip up off the table; the
    rest lies down. Photographed tickets show no more lift than a millimetre or two, at a corner or along a curled
    edge (the Surya Cinema ticket, North Lakhimpur, on Wikimedia Commons, lifts about that much along its left edge,
    by the narrow shadow it throws on the ruled paper under it). The ticket is about 60 mm across its 15 em, so a
    millimetre is MM em."""
    (fx0, fy0), (fx1, fy1) = TICKET["fold"]
    fl = math.hypot(fx1 - fx0, fy1 - fy0)
    (ex0, ey0), (ex1, ey1) = TICKET["ear"]
    el = math.hypot(ex1 - ex0, ey1 - ey0)

    def z(x, y):
        fold = ((x - fx0) * (fy1 - fy0) - (y - fy0) * (fx1 - fx0)) / fl
        # How far past the dog-ear's crease a point lies, toward the corner it folded; nothing on the ticket's side.
        ear = np.clip(((x - ex0) * (ey1 - ey0) - (y - ey0) * (ex1 - ex0)) / el, 0, None)
        reach = 1.45  # em from the dog-ear's crease to its tip
        return base(x, y) + RIDGE * MM * np.exp(-((fold / 0.5) ** 2)) + EAR * MM * (ear / reach) ** 1.3

    return z


def card(w, h, seed):
    sheet = Sheet(w, h, CARD, rough=0.9)
    rows, cols = sheet.height.shape
    sheet.rgb *= (1 + 0.025 * cloud((rows, cols), seed, falloff=1.8))[..., None]
    return sheet


def build(sheet, name, warp, at=(0.0, 0.0)):
    return sheet.build(
        STAGE,
        name,
        at=at,
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


def typed(sheet):
    """The email address, typed on at the box office after the ticket was printed (typed.py's strikes). The ribbon
    leaves a black that is not the press's: thinner, a little warm, with the weave of its cloth in it. Each slug hit
    the card hard enough to press its letter into it. Returns where the ribbon inked."""
    x, y, w, h = json.load(open(os.path.join(ART, "typed.json")))["box"]
    struck = placed(sheet, pixels_of(os.path.join(ART, "typed.png"))[..., 0].astype(np.float64), x, y, w, h)
    # A fresh ribbon, struck hard: the scan's ink, a little denser, as the specimen's paper took it lighter than card.
    struck = np.clip(struck * 1.5, 0, 1)
    sheet.ink(struck, RIBBON, 0.95)
    sheet.press(blur(np.clip(struck * 3, 0, 1), 0.8 * sheet.ppe / 96), 0.004)
    sheet.finish(struck, rough=0.85)
    return struck


def lay_ticket(punched, at=(0.0, 0.0)):
    """The ticket, built and laid on the stage with its top left at at, in page em."""
    sheet = card(W, H, 3)
    printed = riso(sheet, {name: plate(sheet, name, "river") for name, _, _ in INKS}, 5)
    printed = np.maximum(printed, typed(sheet))
    if punched:
        px, py, pr = TICKET["punch"]
        sheet.punch(star(sheet, px, py, pr, pr * 0.45, turn=8))
    die(sheet, 0, 0, 1)
    carried(sheet, printed, 21)
    sheet.soften(0.06, 0.02)
    build(sheet, "ticket", warp(drift(W, H, 0.3 * MM, 11)), at)


def ticket(punched):
    lay_ticket(punched)
    key_light.add((W / 2, -H / 2))
    return STAGE.shoot("ticket-punched" if punched else "ticket", (0, 0, W, H), bleed=BLEED, shadow=0.85, sharp=SHARP, exposure=EXPOSURE + KEYED)


def lay_stamps(key="stamps", at=(0.0, 0.0)):
    """The strip of stamps beside the ticket: three Indian stamps still joined, each its own picture of the same river,
    printed in the ticket's four inks, with the country and the value along the foot (stamps.py's plates). The
    perforations run between them, whole round holes, and round the strip's edge, where it was torn off the sheet,
    as the teeth the holes leave. Mint and lying flat, but for the curl gummed paper takes."""
    spec = {**TICKET["stamps"], **TICKET[key]}
    sw, sh = spec["size"]
    ax, ay, aw, ah = spec["art"]
    radius, pitch = spec["perf"]
    count = len(spec["views"])
    w, h = sw, sh * count
    sheet = card(w, h, 29)
    plates = {}
    for name, _, _ in INKS:
        m = np.zeros(sheet.height.shape)
        for i, view in enumerate(spec["views"]):
            art = cover(pixels_of(os.path.join(ART, f"{view}-{name}.png"))[..., 0].astype(np.float64), aw, ah)
            m = np.maximum(m, placed(sheet, art, ax, i * sh + ay, aw, ah))
        path = os.path.join(ART, f"{key}-{name}.png")
        if os.path.exists(path):
            typed = pixels_of(path)[..., 0].astype(np.float64)
            m = np.maximum(m, printer(sheet, placed(sheet, typed, 0, 0, w, h), seed={"k": 31, "red": 33}[name], scale=0.5))
        plates[name] = m
    printed = riso(sheet, plates, 37, scale=0.5)
    # The perforations: a row of holes along every line between stamps and along every edge, spaced evenly on each.
    across = round(w / pitch)
    down = round(sh / pitch)
    for k in range(across + 1):
        for i in range(count + 1):
            sheet.punch(disc(sheet.X, sheet.Y, k * w / across, i * sh, radius))
    for k in range(down * count + 1):
        for x in (0, w):
            sheet.punch(disc(sheet.X, sheet.Y, x, k * sh / down, radius))
    carried(sheet, printed, 41, scale=0.4, folded=False)
    sheet.soften(0.02, 0.008)
    # Gummed paper curls a little across, toward its gum.
    wave = drift(w, h, 0.15 * MM, 43)
    build(sheet, f"ticket-{key}", lambda x, y: wave(x, y) + 0.4 * MM * ((x - w / 2) / (w / 2)) ** 2, at)
    return w, h


def stamps(key="stamps"):
    w, h = lay_stamps(key)
    key_light.add((w / 2, -h / 2))
    return STAGE.shoot(f"ticket-{key}", (0, 0, w, h), bleed=1.6, shadow=0.85, sharp=SHARP, exposure=EXPOSURE + KEYED)


SHOTS = {"ticket": lambda: ticket(False), "punched": lambda: ticket(True), "stamps": stamps}
STAGE = None  # the stage the builders lay their sheets on: main's, or a scene's (scene.py)


def main():
    global STAGE
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


if __name__ == "__main__":
    main()
