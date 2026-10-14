"""Billfold wallet, closed and well used, after Lacoste's black leather billfolds: pebbled leather that has
gone lighter where it is handled, one row of tonal stitching round three sides, the fold along the top and
the green crocodile at the lower corner. It no longer shuts flat: the back half shows past the front, and
the front lifts toward its open edge.

wallet-open is the same billfold unfolded upward and seen from inside, after the interior of Lacoste's
NH4014PN: an ID window on the half that swings up, two card slots and a slanted slip pocket on the half
that stays, the note pocket's mouth down the left edge. The picture behind the window is printed from
studio/art/wallet-photo.png, a placeholder silhouette. Put a portrait there in its place (5 wide by 7 tall,
the face in the middle, since the frame hides the outer tenth) and render the shot again."""

import os

import numpy as np

from paint import blur, box, cloud, cover, ramp, segment
from stock import Sheet, fit, pixels_of

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art")

W, H = 14.8, 18.0
LEATHER = "#131211"
RUBBED = "#3d3833"
THREAD = "#2b2826"
SEAM = 0.42
PITCH = 0.5
EDGE = 0.4
SWELL = 0.85
# How far the back half has slid out from under the front, and how far it has turned.
SLID = (0.34, 0.42)
SKEW = -1.6
GAPE = 0.75


def half(seed, front):
    """One half of the wallet, seen from outside."""
    sheet = Sheet(W, H, LEATHER, rough=0.4)
    X, Y = sheet.X, sheet.Y
    shape = sheet.height.shape
    # The cut corners are round, the ends of the fold along the top are tighter, and no edge is quite straight.
    sheet.cut(np.minimum(box(X, Y, 0, 0, W, H, 0.8), box(X, Y, 0, 0, W, H / 2, 0.3)) + 0.04 * cloud(shape, seed, falloff=2.6))
    inside = -sheet.sdf

    # Black leather is never one black: it pulls lighter where it flexes, and the corners and edges rub pale.
    hide = cloud(shape, seed + 1, falloff=1.8)
    sheet.paint(np.clip(0.14 + 0.12 * hide, 0, 0.4), RUBBED)
    rubbed = (1 - ramp(0.0, 1.5, inside)) * np.clip(0.5 + 0.45 * cloud(shape, seed + 2, falloff=1.2), 0, 1)
    corners = sum(1 - ramp(0.4, 2.6, np.hypot(X - cx, Y - cy)) for cx in (0, W) for cy in (H,))
    sheet.paint(np.clip(rubbed * 0.45 + corners * 0.35, 0, 0.7), RUBBED)
    sheet.finish(np.clip(0.5 + 0.5 * hide, 0, 1) * 0.6, rough=0.27)

    def wrinkles(at, stretch, width):
        return np.exp(-((cloud(shape, at, falloff=1.7, stretch=stretch) / width) ** 2))

    # Wrinkles: long ones the fold gathers, shorter ones across the back where it bends in a pocket.
    gathered = (wrinkles(seed + 3, 6.0, 0.05) + wrinkles(seed + 6, 4.0, 0.04)) * (1 - ramp(0.8, 6.0, Y))
    across = sum(wrinkles(seed + n, 2.5, 0.035) * np.clip(cloud(shape, seed + n + 10, falloff=2.2), 0, 1.4) for n in (4, 7, 8))
    lines = blur((gathered * 0.8 + across * 0.6) * ramp(0.2, 1.0, inside), 1.3)
    sheet.press(lines, 0.012)
    sheet.paint(np.clip(lines, 0, 1) * 0.16, RUBBED)

    if front:
        # A stack of cards inside stands a little proud, and the leather has polished over its edge.
        cards = box(X, Y, W / 2 - 4.5, 2.2, W / 2 + 4.5, 2.2 + 14.3, 0.5)
        sheet.height += 0.02 * blur(sheet.mask(cards), 12)
        sheet.paint(blur(np.exp(-((cards / 0.2) ** 2)), 6) * 0.14, RUBBED)
        sheet.art(os.path.join(ART, "lacoste-crocodile.png"), W - 4.5, H - 3.2, W - 1.5, H - 3.2 + 3.0 * 261 / 420, relief=0.03)

    # One row of stitching down both sides and across the foot. Each stitch sits in the channel the thread pulls.
    seam = np.abs(inside - SEAM)
    run = ramp(0.7, 1.1, Y)
    sheet.press(np.exp(-((seam / 0.11) ** 2)) * run, 0.024)
    along = np.where(X < W / 2, X + Y, X - Y)
    stitch = blur(np.clip(np.cos(2 * np.pi * along / PITCH) * 1.6 + 0.9, 0, 1) * sheet.mask(seam - 0.045) * run, 0.8)
    sheet.paint(stitch, THREAD)
    sheet.height += 0.02 * stitch
    sheet.finish(stitch, rough=0.8)
    # The cut edge is burnished smooth, and has worn through to grey in places.
    burnished = 1 - ramp(0.0, 0.14, inside)
    sheet.finish(burnished, rough=0.28)
    sheet.soften(0.22, 0.12)
    return sheet


def leather(sheet, stage, name, thickness, warp):
    return sheet.build(
        stage,
        name,
        thickness=thickness,
        warp=warp,
        scan="Leather030",
        scan_size=10,
        scan_normal=3.0,
        scan_rough=1.2,
        scan_colour=0.9,
        wear=(("Scratches003", 9, 0.12, 0.0015), ("SurfaceImperfections003", 8, 0.18, 0), ("Fingerprints009", 6, 0.1, 0)),
        sheen=0.3,
        specular=0.55,
    )


def wallet(stage):
    def swell(x, y):
        """Thin where the two halves are stitched, full across the middle and up to the fold, and lifting
        off the back half toward the open edge at the foot, one corner more than the other."""
        u, v = np.abs(2 * x / W - 1), np.abs(np.clip(2 * y / H - 1, -0.8, 1))
        full = SWELL * np.cos(np.pi / 2 * u**2.4) * np.cos(np.pi / 2 * v**2.4)
        return full + GAPE * (y / H) ** 2 * (0.55 + 0.45 * x / W) + 0.04 * np.sin(1.3 + 2.2 * x / W) * np.cos(0.4 + 1.9 * y / H)

    back = leather(half(60, False), stage, "wallet-back", EDGE, lambda x, y: 0.05 * np.sin(0.7 + 1.8 * x / W + 1.1 * y / H))
    back.location = (SLID[0], -SLID[1], 0)
    back.rotation_euler = (0, 0, np.radians(SKEW))
    front = leather(half(20, True), stage, "wallet", EDGE, swell)
    front.location = (0, 0, EDGE + 0.06)
    stage.shoot("wallet", (0, 0, W, H), bleed=1.0, shadow=0.9, exposure=0.2, card=1.6)


# The open wallet is measured across (x) and down (v) from its top left corner, with the fold across the middle
# at v = H. The upper half is the one that swings up, and the lower one stays where the closed wallet lay.
# The note pocket opens down the left edge, where its back shows this far past the inner wall.
LIP = 0.75
# Bare inner wall either side of the fold, before the pockets begin.
SPINE = 1.3
# Mouths of the pockets, as distances from the left edge. Upper half: a card slot, then the window's panel.
SLOT, PANEL = 2.35, 2.95
PANE = (3.9, 2.5, 12.6, 15.45)
# The print behind the window is wallet size, 2.5 by 3.5 inches, and reaches under the frame all round.
PRINT = (3.3, 2.05, 13.2, 15.9)
# Lower half: two card slots, then a slip pocket whose mouth is cut in a shallow V.
SLOTS = (2.26, 3.9)
SLIP, DIP, APEX = 5.6, 1.4, 27.2
# The cards left in the slots: the card's left edge, its top and its colour. A card is 8.4 em across and
# 13.3 down, lying on its side, so most of it is out of sight. The first is in the upper half's slot.
CARDS = ((1.62, 2.0, "#d9d6cc"), (1.55, 20.95, "#1a2c4e"), (3.08, 21.4, "#8f2226"))
CARD = (8.4, 13.3)
# How far the fold stands off the mat, how thick the wallet is at its edge, and how far in that edge is rounded.
RISE, THICK, ROLL = 1.6, 0.34, 0.3
DUST = "#9a9488"


def lie(x, v):
    """The top of the outer leather, off the mat. An open billfold will not go flat: it stands on its two
    ends with the fold in the air, each half bowed along and across, and a corner of each lifting."""
    far = np.clip(np.abs(v - H) / H, 0, 1)
    lower = ramp(H - 1.0, H + 1.0, v)
    tent = RISE * np.clip(1 - np.sqrt(far**2 + 0.035**2), 0, 1) ** 1.15
    full = (0.25 + 0.25 * lower) * np.sin(np.pi * far) ** 1.5
    dome = -(0.22 + 0.12 * lower) * (2 * x / W - 1) ** 2 * np.sin(np.pi * far) ** 0.5
    corner = 0.35 * lower * ramp(0.5, 1.0, far) * (x / W) ** 2 + 0.15 * (1 - lower) * ramp(0.5, 1.0, far) * (1 - x / W) ** 2
    lumps = 0.04 * np.sin(1.3 + 6.6 * x / W) * np.cos(0.4 + 3.1 * v / H) + 0.03 * np.sin(2.1 + 5.3 * v / H + 1.7 * x / W)
    return THICK + 0.08 + tent + full + dome + corner + lumps


def rolled(x, v, z):
    """Every layer turns down into the wallet's edge, which is as thick as the leather stacked in it."""
    under = lie(x, v) - THICK
    return under + (z - under) * np.sqrt(1 - (1 - np.clip(-edge(x, v) / ROLL, 0, 1)) ** 2)


def along(v):
    """How far down a pocket's mouth a point is, from 0 at the fold to 1 at the wallet's end."""
    return np.clip((np.abs(v - H) - SPINE) / (H - SPINE), 0, 1)


def sagged(lip, v, sag=0.1):
    """A mouth that cards have been pushed past for years is no longer cut straight: it sags in the middle."""
    return lip + sag * np.sin(np.pi * along(v)) ** 1.2


def slip(v):
    """Where the slip pocket's mouth is, down the lower half: deepest at the point of its V."""
    reach = np.where(v < APEX, APEX - (H + SPINE), 2 * H - APEX)
    return sagged(SLIP + DIP * np.clip(1 - np.abs(v - APEX) / reach, 0, 1), v, 0.06)


def agape(x, v, lip, amount):
    """A pocket that no longer shuts: its mouth stands off the layer below, most in the middle of its length."""
    return amount * np.exp(-np.clip(x - lip, 0, None) / 1.1) * np.sin(np.pi * along(v)) ** 0.8


def swell(x, v, card):
    """A card lifts the leather over it by its own thickness, with a soft shoulder round its edge."""
    x0, v0, _ = card
    across = ramp(x0 - 0.5, x0 + 0.2, x) * (1 - ramp(x0 + CARD[0] - 0.2, x0 + CARD[0] + 0.6, x))
    return 0.11 * across * ramp(v0 - 0.5, v0 + 0.3, v) * (1 - ramp(v0 + CARD[1] - 0.3, v0 + CARD[1] + 0.5, v))


# Each layer's height off the mat. Every one rides on the layer beneath it.
def inner_at(x, v):
    return lie(x, v) + 0.08 + agape(x, v, LIP, 0.2 + 0.16 * ramp(H - 1, H + 1, v))


def slot_at(x, v):
    return inner_at(x, v) + 0.12 + agape(x, v, sagged(SLOT, v), 0.14) + swell(x, v, CARDS[0])


def panel_at(x, v):
    return slot_at(x, v) + 0.1 + agape(x, v, sagged(PANEL, v, 0.05), 0.06)


def first_at(x, v):
    return inner_at(x, v) + 0.12 + agape(x, v, sagged(SLOTS[0], v), 0.18) + swell(x, v, CARDS[1])


def second_at(x, v):
    return first_at(x, v) + 0.12 + agape(x, v, sagged(SLOTS[1], v), 0.16) + swell(x, v, CARDS[2])


def slip_at(x, v):
    return second_at(x, v) + 0.1 + agape(x, v, slip(v), 0.14)


def edge(x, v):
    """Signed distance to the open wallet's outline. The sides draw in where it folds and are nowhere straight."""
    waist = 0.14 * np.exp(-(((v - H) / 1.4) ** 2)) + 0.04 * np.sin(0.9 + 0.55 * v)
    drift = 0.05 * np.sin(0.4 + 0.21 * v)
    ends = 0.05 * np.sin(1.1 + 0.8 * x)
    return np.maximum(box(x, v, 0, ends, W, 2 * H + ends, 0.8), np.abs(x - W / 2 - drift) - (W / 2 - 0.05 - waist))


def part(x0, v0, x1, v1, colour, rough):
    """A sheet covering one rectangle of the open wallet, and where its pixels fall on the wallet."""
    sheet = Sheet(x1 - x0, v1 - v0, colour, rough=rough)
    return sheet, sheet.X + x0, sheet.Y + v0


def hide(sheet, seed):
    """Black leather is never one black: it pulls lighter where it flexes. And used leather is never flat."""
    shape = sheet.height.shape
    tone = cloud(shape, seed, falloff=1.8)
    sheet.paint(np.clip(0.12 + 0.1 * tone, 0, 0.4), RUBBED)
    sheet.finish(np.clip(0.5 + 0.5 * tone, 0, 1) * 0.6, rough=0.27)
    sheet.height += 0.07 * cloud(shape, seed + 500, falloff=2.6) + 0.018 * cloud(shape, seed + 501, falloff=2.0)


def sew(sheet, across, down, run=1.0):
    """A row of stitching along the line where `across` is zero, `down` measuring the way along it.
    Each stitch sits in the channel the thread pulls."""
    seam = np.abs(across)
    sheet.press(np.exp(-((seam / 0.11) ** 2)) * run, 0.024)
    stitch = blur(np.clip(np.cos(2 * np.pi * down / PITCH) * 1.6 + 0.9, 0, 1) * sheet.mask(seam - 0.045) * run, 0.8)
    sheet.paint(stitch, THREAD)
    sheet.height += 0.02 * stitch
    sheet.finish(stitch, rough=0.8)


def seams(sheet, X, V, left):
    """The stitching a pocket piece shares with the wallet: round its outer edges, and down the side of the
    fold where the pockets are sewn to the inner wall. It starts `left` em from the wallet's left edge."""
    inside = -edge(X, V)
    run = ramp(left, left + 0.15, X) * ramp(SPINE + 0.2, SPINE + 0.5, np.abs(V - H))
    sew(sheet, inside - SEAM, np.where(X > W - 1.2, V, X), run)
    stop = ramp(0.0, 0.2, W - SEAM - X)
    sew(sheet, np.abs(V - H) - SPINE - 0.4, X, ramp(left, left + 0.15, X) * stop)


def mouth(sheet, d, seed, wear=0.4):
    """The mouth of a pocket, `d` em in from its cut edge: creased behind the turn, burnished,
    and rubbed pale where cards are drawn past it."""
    worn = np.clip(0.55 + 0.45 * cloud(sheet.height.shape, seed, falloff=1.3), 0, 1)
    sheet.press(np.exp(-(((d - 0.3) / 0.06) ** 2)) * worn, 0.007)
    sheet.paint(np.clip((1 - ramp(0.0, 0.25, d)) * wear * worn, 0, 0.8), RUBBED)
    sheet.finish(1 - ramp(0.0, 0.3, d), rough=0.24)


def tuck(sheet, d, depth=0.7, reach=0.2):
    """Darkness where a layer goes under the edge of the one above it, `d` em out from that edge."""
    sheet.ink(np.exp(-np.clip(d, 0, None) / reach), "#000000", depth)


def lint(sheet, seed, where, amount):
    """Dust and pocket fluff: a few specks, nearly all of them where `where` is high."""
    rng = np.random.default_rng(seed)
    for size, share in ((0.8, 0.7), (1.5, 0.3)):
        specks = (rng.random(sheet.height.shape) < amount * share * where) * rng.uniform(0.3, 1.0, sheet.height.shape)
        sheet.paint(np.clip(blur(specks, size) * 6 * size**2, 0, 1) * 0.7, DUST)


def hairlines(sheet, seed, count, reach):
    """Scratches in every direction, as keys and coins leave them: a mask of thin straight lines."""
    rng = np.random.default_rng(seed)
    marks = np.zeros(sheet.height.shape)
    for _ in range(count):
        x, y, turn, length = rng.uniform(0, sheet.w), rng.uniform(0, sheet.h), rng.uniform(0, np.pi), rng.uniform(0.3, reach)
        dx, dy = np.cos(turn) * length / 2, np.sin(turn) * length / 2
        rows, cols = sheet.window(x - abs(dx) - 0.1, y - abs(dy) - 0.1, x + abs(dx) + 0.1, y + abs(dy) + 0.1)
        line = cover(segment(sheet.X[rows, cols], sheet.Y[rows, cols], x - dx, y - dy, x + dx, y + dy, 0.005), sheet.aa)
        marks[rows, cols] = np.maximum(marks[rows, cols], rng.uniform(0.25, 1.0) * line)
    return marks


def lay(stage, sheet, name, at, level, **finish):
    """Put a part on the stage at its place on the open wallet, `level(x, v)` above the mat."""
    low = []

    def warp(x, y):
        z = rolled(x + at[0], y + at[1], level(x + at[0], y + at[1]))
        low.append(float(np.min(z)))
        return z

    obj = sheet.build(stage, name, thickness=0.0, warp=warp, step=0.1, **finish)
    obj.location = (at[0], H - at[1], low[0])
    return obj


def lined(stage, sheet, X, V, name, at, level, size=8.0):
    """The leather of the inside: the same hide as the outside, finer in the grain and less handled."""
    sheet.finish(1 - ramp(0.0, 0.14, -sheet.sdf), rough=0.28)
    sheet.finish(1 - ramp(0.0, ROLL, -edge(X, V)), rough=0.55)
    sheet.soften(0.16, 0.08)
    return lay(
        stage,
        sheet,
        name,
        at,
        level,
        scan="Leather030",
        scan_size=size,
        scan_normal=2.2,
        scan_rough=1.2,
        scan_colour=0.9,
        wear=(("Scratches003", 9, 0.1, 0.001), ("SurfaceImperfections003", 8, 0.18, 0), ("Fingerprints009", 6, 0.12, 0)),
        sheen=0.3,
        specular=0.55,
    )


def back(stage):
    """The back of the note pocket: the strip of the outer leather's facing that shows past the inner wall."""
    sheet, X, V = part(0, 0, 1.9, 2 * H, LEATHER, 0.4)
    sheet.cut(edge(X, V))
    hide(sheet, 81)
    sew(sheet, -edge(X, V) - SEAM, np.where(np.abs(V - H) > H - 0.8, X, V), ramp(0.7, 1.1, np.abs(V - H)))
    tuck(sheet, LIP + 0.1 - X, 0.75, 0.3)
    lint(sheet, 82, np.exp(-np.abs(LIP - X) / 0.15), 0.0012)
    lined(stage, sheet, X, V, "wallet-open-back", (0, 0), lie, size=9.0)


def inner(stage):
    """The inner wall: one piece from end to end, hemmed along the note pocket's mouth, bare across the fold."""
    sheet, X, V = part(LIP, 0, W, 2 * H, LEATHER, 0.4)
    shape = sheet.height.shape
    hem = X - LIP - 0.05 * cloud(shape, 90, falloff=2.4)
    sheet.cut(np.maximum(edge(X, V) + 0.02, -hem))
    hide(sheet, 91)
    fold = np.abs(V - H)

    # The fold: one hard crease where it shuts, broken ones beside it, and the ripples the pockets' ends pull.
    lean = 0.16 * cloud(shape, 92, falloff=2.2, stretch=5)
    strength = np.clip(0.7 + 0.5 * cloud(shape, 96, falloff=1.6, stretch=3), 0.1, 1.3)
    crease = np.exp(-(((V - H - lean) / 0.08) ** 2)) + 0.5 * strength * np.exp(-(((fold - 0.5 - 1.6 * lean) / 0.07) ** 2))
    near = np.exp(-((fold / 1.1) ** 2))
    ripples = sum(np.exp(-((cloud(shape, 93 + n, falloff=1.7, stretch=7) / 0.06) ** 2)) for n in range(3)) * near * strength
    lines = blur(crease + 0.9 * ripples, 1.2)
    sheet.press(lines, 0.03)
    sheet.paint(np.clip(lines * (0.5 + 0.3 * cloud(shape, 97, falloff=1.4)), 0, 1) * 0.45, RUBBED)
    sheet.paint(near * np.clip(0.5 + 0.5 * cloud(shape, 98, falloff=1.5), 0, 1) * 0.2, RUBBED)

    mouth(sheet, hem, 99, 0.5)
    sew(sheet, hem - 0.36, V)
    inside = -edge(X, V)
    sew(sheet, inside - SEAM, np.where(X > W - 1.2, V, X), ramp(0.7, 1.1, fold) * ramp(1.2, 1.5, X - LIP))

    # Where it goes under the pockets.
    bare = 3 * (1 - ramp(SPINE - 0.05, SPINE + 0.05, fold))
    tuck(sheet, np.where(V < H, sagged(SLOT, V), sagged(SLOTS[0], V)) - X + bare)
    tuck(sheet, SPINE - fold, 0.6, 0.16)
    lint(sheet, 100, np.exp(-np.abs(SPINE - fold) / 0.12) + np.exp(-((fold / 0.15) ** 2)), 0.0012)
    lined(stage, sheet, X, V, "wallet-open-inner", (LIP, 0), inner_at)


def window(stage):
    """The print behind the window, and over it the clear plastic: no longer flat, scratched, lying on the
    print in patches and gone dull low down, where a thumb pushes whatever is in the pocket back out."""
    x0, v0, x1, v1 = PRINT
    sheet, X, V = part(x0, v0, x1, v1, "#e9e6df", 0.5)
    shape = sheet.height.shape
    sheet.art(os.path.join(ART, "wallet-photo.png"), 0, 0, x1 - x0, v1 - v0)
    pane = -box(X, V, *PANE, 0.45)

    # Where the plastic stands off the print the picture goes milky, and where it touches it stays deep.
    apart = 1 - ramp(-0.5, 0.7, cloud(shape, 110, falloff=2.4))
    sheet.paint(0.03 + 0.09 * apart, "#c6c3b8")
    thumb = np.exp(-(((X - 8.6) / 2.7) ** 2 + ((V - 12.1) / 2.3) ** 2)) * np.clip(0.75 + 0.35 * cloud(shape, 111, falloff=1.4), 0, 1)
    sheet.paint(thumb * 0.2, "#bfbcb0")
    scratched = hairlines(sheet, 112, 34, 2.4)
    sheet.paint(scratched * 0.14, "#ecebe6")
    sheet.press(blur(scratched, 0.6), 0.004)
    # Dust gathers along the frame, and the frame keeps the light off the plastic next to it.
    tuck(sheet, pane, 0.5, 0.1)
    lint(sheet, 114, np.exp(-np.clip(pane, 0, None) / 0.12) + 0.02, 0.004)

    # The plastic ripples, and is drawn into shallow folds from the corners of the frame.
    pull = np.exp(-(((X - x0) - (V - v0) * 0.62 - 0.8) / 1.1) ** 2) - np.exp(-(((X - x0) + (V - v0) * 0.55 - 9.0) / 1.4) ** 2)
    sheet.height += 0.03 * cloud(shape, 115, falloff=2.6) + 0.012 * cloud(shape, 116, falloff=2.1) + 0.02 * pull
    sheet.coat[:] = 1 - 0.8 * thumb
    lay(
        stage,
        sheet,
        "wallet-open-window",
        (x0, v0),
        lambda x, v: slot_at(x, v) + 0.04,
        wear=(("Scratches003", 5, 0.0, 0.0014), ("Fingerprints009", 7, 0.0, 0.0006)),
        coat_rough=0.06,
        specular=0.4,
    )


def upper(stage):
    """The half that swings up: a card slot, and over it the panel with the window cut in it."""
    end = H - SPINE
    sheet, X, V = part(SLOT, 0, 4.6, end, LEATHER, 0.4)
    shape = sheet.height.shape
    cut = X - sagged(SLOT, V) - 0.04 * cloud(shape, 120, falloff=2.4)
    sheet.cut(np.maximum(edge(X, V) + 0.02, -cut))
    hide(sheet, 121)
    mouth(sheet, cut, 122)
    seams(sheet, X, V, SLOT + 0.3)
    tuck(sheet, sagged(PANEL, V, 0.05) - X)
    lined(stage, sheet, X, V, "wallet-open-slot", (SLOT, 0), slot_at, size=7.4)

    sheet, X, V = part(PANEL, 0, W, end, LEATHER, 0.4)
    shape = sheet.height.shape
    cut = X - sagged(PANEL, V, 0.05) - 0.04 * cloud(shape, 130, falloff=2.4)
    sheet.cut(np.maximum(edge(X, V) + 0.02, -cut))
    pane = box(X, V, *PANE, 0.45)
    sheet.punch(pane + 0.02 * cloud(shape, 131, falloff=2.2))
    hide(sheet, 132)

    # Creases the fold pulls across the frame, and the ones a hip pocket bends into it.
    gathered = np.exp(-((cloud(shape, 133, falloff=1.7, stretch=6) / 0.04) ** 2)) * ramp(end - 5.0, end - 0.5, V)
    across = np.exp(-((cloud(shape, 134, falloff=1.7, stretch=0.4) / 0.035) ** 2)) * np.clip(cloud(shape, 135, falloff=2.2), 0, 1.4)
    lines = blur(gathered * 0.6 + across * 0.5, 1.3) * ramp(0.1, 0.5, pane)
    sheet.press(lines, 0.012)
    sheet.paint(np.clip(lines, 0, 1) * 0.16, RUBBED)

    # The window's edge: creased all round a little way out, and its edge paint cracked to grey.
    sheet.press(np.exp(-(((pane - 0.3) / 0.05) ** 2)), 0.012)
    cracked = (1 - ramp(0.0, 0.07, pane)) * np.clip(cloud(shape, 137, falloff=1.0) + 0.2, 0, 1)
    sheet.paint(np.clip(cracked, 0, 1) * 0.55, "#77726a")
    sheet.finish(1 - ramp(0.0, 0.2, pane), rough=0.25)
    mouth(sheet, cut, 138)
    seams(sheet, X, V, PANEL + 0.3)
    lint(sheet, 139, np.exp(-np.abs(pane - 0.3) / 0.06) + np.exp(-np.abs(inside_seam(X, V)) / 0.08), 0.0012)
    lined(stage, sheet, X, V, "wallet-open-panel", (PANEL, 0), panel_at)


def inside_seam(X, V):
    """Distance from the row of stitching that runs round the wallet's outer edge."""
    return -edge(X, V) - SEAM


def lower(stage):
    """The half that stays: two card slots one over the other, and the slip pocket with its V mouth and the
    maker's name blind stamped near the outer edge."""
    top = H + SPINE
    for n, (lip, level, far) in enumerate(((SLOTS[0], first_at, 5.6), (SLOTS[1], second_at, 8.6))):
        sheet, X, V = part(lip, top, far, 2 * H, LEATHER, 0.4)
        shape = sheet.height.shape
        above = sagged(SLOTS[1], V) if n == 0 else slip(V)
        cut = X - sagged(lip, V) - 0.04 * cloud(shape, 140 + 10 * n, falloff=2.4)
        sheet.cut(np.maximum(edge(X, V) + 0.02, -cut))
        hide(sheet, 141 + 10 * n)
        mouth(sheet, cut, 142 + 10 * n, 0.55)
        seams(sheet, X, V, lip + 0.3)
        tuck(sheet, above - X)
        lint(sheet, 143 + 10 * n, np.exp(-np.abs(above - X) / 0.12), 0.0012)
        lined(stage, sheet, X, V, f"wallet-open-slot-{n + 1}", (lip, top), level, size=7.0 + n)

    sheet, X, V = part(SLIP, top, W, 2 * H, LEATHER, 0.4)
    shape = sheet.height.shape
    cut = X - slip(V) - 0.04 * cloud(shape, 160, falloff=2.4)
    sheet.cut(np.maximum(edge(X, V) + 0.02, -cut))
    hide(sheet, 161)
    gathered = np.exp(-((cloud(shape, 162, falloff=1.7, stretch=6) / 0.045) ** 2)) * (1 - ramp(top + 0.5, top + 6.0, V))
    across = sum(
        np.exp(-((cloud(shape, 163 + n, falloff=1.7, stretch=0.4) / 0.035) ** 2)) * np.clip(cloud(shape, 166 + n, falloff=2.2), 0, 1.4)
        for n in range(2)
    )
    lines = blur(gathered * 0.7 + across * 0.5, 1.3) * ramp(0.2, 0.9, cut)
    sheet.press(lines, 0.012)
    sheet.paint(np.clip(lines, 0, 1) * 0.16, RUBBED)
    # The cards behind it have polished the leather over their far edges.
    for n, (x0, v0, _) in enumerate(CARDS[1:]):
        over = np.exp(-((box(X, V, x0, v0, x0 + CARD[0], v0 + CARD[1], 0.5) / 0.25) ** 2))
        sheet.paint(over * np.clip(0.4 + 0.5 * cloud(shape, 170 + n, falloff=1.4), 0, 1) * 0.16, RUBBED)

    # LACOSTE, stamped blind: pressed in and burnished, no colour. It reads up the wallet.
    name = np.rot90(pixels_of(os.path.join(ART, "lacoste-wordmark.png"))[..., 3:].astype(np.float64))
    rows, cols = sheet.window(12.5 - SLIP, 25.3 - top, 13.1 - SLIP, 28.75 - top)
    stamp = blur(fit(name, rows.stop - rows.start, cols.stop - cols.start)[..., 0], 0.8)
    sheet.height[rows, cols] -= 0.03 * stamp
    sheet.rgb[rows, cols] *= 1 - 0.35 * stamp[..., None]
    sheet.rough[rows, cols] += stamp * (0.22 - sheet.rough[rows, cols])

    mouth(sheet, cut, 172, 0.5)
    seams(sheet, X, V, SLIP + DIP + 0.4)
    lint(sheet, 173, np.exp(-np.abs(np.abs(V - H) - SPINE - 0.4) / 0.1) + np.exp(-np.abs(inside_seam(X, V)) / 0.08) + 0.03, 0.0012)
    lined(stage, sheet, X, V, "wallet-open-slip", (SLIP, top), slip_at)


def cards(stage):
    """A few cards left in the slots. Only the long edge of each stands out, with the corners it has worn."""
    under = (inner_at, inner_at, first_at)
    lips = (SLOT, SLOTS[0], SLOTS[1])
    for n, ((x0, v0, colour), below, lip) in enumerate(zip(CARDS, under, lips)):
        sheet, X, V = part(x0, v0, x0 + 2.1, v0 + CARD[1], colour, 0.34)
        shape = sheet.height.shape
        sheet.cut(box(X, V, x0, v0, x0 + CARD[0], v0 + CARD[1], 0.5))
        inside = -sheet.sdf
        # The print wears off the edge to the white of the plastic, and the lacquer scuffs.
        sheet.paint((1 - ramp(0.0, 0.07, inside)) * np.clip(0.6 + 0.5 * cloud(shape, 180 + n, falloff=1.2), 0, 1), "#e9e7e1")
        sheet.paint(hairlines(sheet, 183 + n, 9, 1.2) * 0.16, "#e9e7e1")
        sheet.paint(np.clip(0.1 + 0.08 * cloud(shape, 186 + n, falloff=1.6), 0, 0.3), "#8d8a82")
        sheet.coat[:] = 0.7
        tuck(sheet, sagged(lip, V) - X, 0.65, 0.14)
        sheet.height += 0.02 * cloud(shape, 189 + n, falloff=2.6)
        sheet.soften(0.06, 0.05)
        lay(
            stage,
            sheet,
            f"wallet-open-card-{n}",
            (x0, v0),
            lambda x, v, below=below: below(x, v) + 0.05,
            wear=(("Scratches003", 5, 0.25, 0.002), ("SurfaceImperfections003", 6, 0.2, 0)),
            coat_rough=0.12,
            specular=0.5,
        )


def wallet_open(stage):
    back(stage)
    inner(stage)
    cards(stage)
    upper(stage)
    window(stage)
    lower(stage)
    stage.shoot("wallet-open", (0, -H, W, 2 * H), bleed=2.0, shadow=1.3, exposure=0.2, card=1.6)


SHOTS = {"wallet": wallet, "wallet-open": wallet_open}
