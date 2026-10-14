"""The contact page's cinema ticket, photographed lying on the page: a die-cut card of cheap flecked board,
printed letterpress in one black ink, with bites along its ends, a notch either side of each tear line and the
tear lines themselves perforated through. Then the same ticket punched and stamped, and a roll of it for the
folded strip. Run from the repository root, after studio/ticket/plate.mjs:

    blender -b --factory-startup -P studio/ticket/ticket.py -- [ticket punched roll ...] [--scale 0.5] [--samples 64] [--proofs DIR]

Writes public/objects/ticket.avif, the ticket and the shadow it leaves; public/objects/ticket-punched.avif,
the corner of it the conductor punched and stamped, to lay over the first; and public/objects/ticket-roll.avif,
the roll. Uses the copy stand from the oeusume studio, so it is lit as every other object on the site is. Set
OEUSUME if that checkout is not in ~/Documents/oeusume.

Every measure is in the ticket's em, from src/components/ticket/ticket.json, which the page reads too. What is
printed comes from the page's own type, captured by plate.mjs into studio/ticket/art/plate.png, so the words
in the photograph sit under the page's live words.
"""

import argparse
import json
import math
import os
import subprocess
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
PANEL = "#10150f"  # the contact page's panel, which the ticket lies on and which lights it from below
CARD = "#f2ead7"
INK = "#0d0c0a"
STAMP_INK = "#a3271f"
ART = os.path.join(HERE, "art")
OUT = os.path.join(ROOT, "public", "objects")
SHARP = 1.5  # the page shows the ticket at up to 72 pixels to its em


def plate(name, sheet, x0=0.0, y0=0.0, scale=1.0):
    """A captured plate as ink coverage, 1 where it prints, laid at x0, y0 on the sheet and scaled."""
    stored = pixels_of(os.path.join(ART, f"{name}.png"))[..., :3].astype(np.float64)
    rows = round(H * scale * sheet.ppe)
    cols = round(W * scale * sheet.ppe)
    ink = 1 - fit(stored, rows, cols).mean(axis=-1)
    out = np.zeros(sheet.height.shape)
    r0, c0 = round(y0 * sheet.ppe), round(x0 * sheet.ppe)
    r1, c1 = min(out.shape[0], r0 + rows), min(out.shape[1], c0 + cols)
    out[max(0, r0) : r1, max(0, c0) : c1] = ink[max(0, -r0) : r1 - r0, max(0, -c0) : c1 - c0]
    return np.clip(out, 0, 1)


def letterpress(sheet, m, seed, depth=0.006):
    """Print a plate as letterpress does: the type bites into the board, the ink sits a little heavier at the
    edge of each letter where the press squeezed it, and in the middle of a solid it did not quite take."""
    soft = blur(m, 0.7)
    sheet.press(soft, depth)
    rim = np.clip(soft - blur(m, 2.5), 0, 1)
    rows, cols = m.shape
    starve = np.clip(cloud((rows, cols), seed, falloff=1.2) * 0.5 + 0.5, 0, 1)
    speck = cloud((rows, cols), seed + 1, falloff=0.2) > 2.4  # pin holes where the ink missed the board
    strength = (0.9 + 0.1 * starve) * (1 - speck * 0.75)
    sheet.ink(m, INK, 0.975 * strength + 0.025 * rim)
    # Dried ink is a touch less matte than the board.
    sheet.finish(m, rough=0.8)


def stamp(sheet, m, seed):
    """A rubber stamp struck by hand: the ink is thin and uneven, heavier on one side, missing in places, and
    it soaks into the board rather than sitting on it."""
    rows, cols = m.shape
    patchy = np.clip(cloud((rows, cols), seed, falloff=1.4) * 0.35 + 0.72, 0, 1)
    lean = np.clip(0.75 + 0.25 * (sheet.X - sheet.X.mean()) / max(1e-6, sheet.X.std()), 0.5, 1)
    gaps = np.clip(cloud((rows, cols), seed + 3, falloff=0.6) * 0.8 + 0.6, 0, 1)
    sheet.ink(blur(m, 0.5), STAMP_INK, 0.95 * patchy * lean * gaps)
    sheet.press(m, 0.0015)


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
        crosses = ((ay > Y) != (by > Y)) & (X < (bx - ax) * (Y - ay) / (by - ay + 1e-12) + ax)
        inside ^= crosses
    d[rs, cs] = np.where(inside, -edge, edge)
    return d


def die(sheet, x0, y0, scale):
    """Cut one ticket's shape into the sheet, at x0, y0 and scale: the bites along its ends, the notches either
    side of its tear lines, and the tear lines perforated with short slots. On the roll a ticket's end bites
    fall on the next ticket's, and make whole holes."""
    s = scale
    bites = TICKET["bites"]
    span = (bites["count"] - 1) * bites["pitch"]
    first = (W - span) / 2
    for k in range(bites["count"]):
        bx = x0 + (first + k * bites["pitch"]) * s
        for end in (y0, y0 + H * s):
            sheet.punch(disc(sheet.X, sheet.Y, bx, end, bites["radius"] * s))
    notch = TICKET["notch"] * s
    slot, gap, tall = 0.24 * s, 0.13 * s, max(0.05 * s, 0.026)
    for tear in TICKET["tears"]:
        ty = y0 + tear * s
        sheet.punch(disc(sheet.X, sheet.Y, x0, ty, notch))
        sheet.punch(disc(sheet.X, sheet.Y, x0 + W * s, ty, notch))
        x = x0 + notch + 0.28 * s
        end = x0 + W * s - notch - 0.28 * s
        rs, cs = sheet.window(x0, ty - 0.2 * s, x0 + W * s, ty + 0.2 * s)
        holes = np.full(sheet.height[rs, cs].shape, 1.0)
        X, Y = sheet.X[rs, cs], sheet.Y[rs, cs]
        while x + slot <= end:
            holes = np.minimum(holes, box(X, Y, x, ty - tall / 2, x + slot, ty + tall / 2, tall / 2))
            x += slot + gap
        hole = np.full(sheet.height.shape, 1.0)
        hole[rs, cs] = holes
        sheet.punch(hole)


def card(w, h, seed):
    sheet = Sheet(w, h, CARD, rough=0.88)
    # Board is never one colour: a slow cloud of warmer and cooler, and the odd darker fibre.
    rows, cols = sheet.height.shape
    tint = cloud((rows, cols), seed, falloff=1.8)
    sheet.rgb *= (1 + 0.025 * tint)[..., None]
    return sheet


def build(sheet, name, warp):
    return sheet.build(
        STAGE,
        name,
        thickness=0.055,
        warp=warp,
        scan="Paper002",
        scan_size=7,
        scan_normal=0.55,
        scan_rough=0.35,
        scan_colour=0.45,
        wear=(("SurfaceImperfections003", 10, 0.06, 0),),
        fibre=0.0012,
        fibre_scale=36,
        sheen=0.15,
        specular=0.25,
    )


def ticket(punched):
    sheet = card(W, H, 3)
    letterpress(sheet, plate("plate", sheet), 5)
    if punched:
        stamp(sheet, plate("stamp", sheet), 9)
        px, py, pr = TICKET["punch"]
        sheet.punch(star(sheet, px, py, pr, pr * 0.45, turn=8))
    die(sheet, 0, 0, 1)
    sheet.soften(0.05, 0.02)
    build(sheet, "ticket", drift(W, H, 0.24, 11))
    return STAGE.shoot("ticket-punched" if punched else "ticket", (0, 0, W, H), bleed=BLEED, shadow=0.7, sharp=SHARP)


def patch():
    """Cut the punched corner out of the punched photograph, to lay over the unpunched one. Where the punch went
    through, the photograph shows nothing, and laid over the unpunched one that would show paper: there it is
    filled with the panel the ticket lies on, in the shadow of the card. Its edge is feathered, so it melts
    into the photograph under it."""
    x, y, w, h = TICKET["patch"]
    density = 48 * SHARP * STAGE.scale
    script = f"""
from PIL import Image
import numpy as np
path = {os.path.join(OUT, "ticket-punched.avif")!r}
whole = {os.path.join(OUT, "ticket.avif")!r}
x0, y0 = round(({x} + {BLEED}) * {density}), round(({y} + {BLEED}) * {density})
x1, y1 = x0 + round({w} * {density}), y0 + round({h} * {density})
crop = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32)[y0:y1, x0:x1] / 255
under = np.asarray(Image.open(whole).convert("RGBA")).astype(np.float32)[y0:y1, x0:x1] / 255
hole = np.array({[c / 255 * 0.6 for c in bytes.fromhex(PANEL[1:])]}, dtype=np.float32)
a = crop[..., 3:]
rgb = crop[..., :3] * a + hole * (1 - a)
alpha = np.maximum(a[..., 0], under[..., 3])
feather = 0.35 * {density}
rows, cols = crop.shape[:2]
ry = np.minimum(np.arange(rows), np.arange(rows)[::-1]) / feather
rx = np.minimum(np.arange(cols), np.arange(cols)[::-1]) / feather
fade = np.clip(np.minimum.outer(ry, rx), 0, 1)
alpha *= fade * fade * (3 - 2 * fade)
out = np.dstack((rgb, alpha))
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, quality=95, subsampling="4:4:4", speed=2)
print("PATCH", cols, rows)
"""
    subprocess.run(["uv", "run", "--quiet", "--with", "pillow>=11.3", "--with", "numpy", "python", "-I", "-c", script], check=True)


def roll():
    """The roll: the same ticket at a third of the size, again and again, each joined to the next where their
    bites meet, so that the bites there are whole round holes. It curls a little more than one ticket would."""
    spec = TICKET["roll"]
    s, count = spec["scale"], spec["count"]
    w, h = W * s, H * s * count
    sheet = card(w, h, 13)
    ink = np.zeros(sheet.height.shape)
    for i in range(count):
        ink = np.maximum(ink, plate("plate", sheet, 0, i * H * s, s))
    letterpress(sheet, ink, 17, depth=0.004)
    for i in range(count):
        die(sheet, 0, i * H * s, s)
    sheet.soften(0.03, 0.012)
    build(sheet, "ticket-roll", drift(w, h, 0.1, 19))
    shown = spec["shown"] * H * s
    return STAGE.shoot("ticket-roll", (0, (h - shown) / 2, w, shown), bleed=0.5, shadow=0.7, sharp=1.0)


SHOTS = {"ticket": lambda: ticket(False), "punched": lambda: (ticket(True), patch()), "roll": roll}

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
