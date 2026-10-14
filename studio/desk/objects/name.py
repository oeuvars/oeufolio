"""A bunch of keys. A stitched leather key tag, racing green lapped over a tan tab, has the name blind
stamped into the green, and the tab carries Lacoste's crocodile. A steel split ring leans through its brass eyelet and through the tip of a
Ferrari 458 Italia key, copied button side up from photographs of a used one: a red lacquered shell,
a black rubber pad of three buttons and a laser cut blade. The key carries no maker's mark."""

import math
import os

import bmesh
import numpy as np
from mathutils import Vector

from paint import blur, box, cloud, cover, disc, linear, ramp, segment, streaks
from solids import finish, lathe, principled, rect, worn
from stock import Sheet, fit, pixels_of, sample

W, H = 30.0, 9.625
ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art")

# The tag in its own coordinates. It is turned about its eyelet, which lies at EYE_AT in the frame.
TAG_W, TAG_H = 17.6, 8.4
SEAM = 13.8
EYE = (15.7, 1.6)
EYE_AT = (15.8, 2.2)
TURN = -3.0
HOLE = 0.56
INSET = 0.44
PITCH = 0.37
# The tag is propped a little off the mat, because the ring runs underneath its end.
THICK = 0.6

# A split ring: two turns of wire. It cannot lie flat and still go through a hole in something thick,
# so it leans, resting on the mat at its lowest point. Its level diameter runs down to the right.
RING, WIRE, LEAN = 1.9, 0.105, math.radians(35)
LEVEL = math.radians(20)

# The key, measured off the photographs in units of the width of its head. Along is from the tip the ring
# goes through towards the blade, and each profile is one half of an outline: (along, half width).
KEY_W = 6.1
KEY_TURN = 26.0
SHELL = (
    (0, 0), (0.012, 0.072), (0.05, 0.149), (0.1, 0.217), (0.15, 0.27), (0.25, 0.35), (0.35, 0.405), (0.5, 0.458),
    (0.65, 0.487), (0.8, 0.5), (0.95, 0.494), (1.03, 0.472), (1.085, 0.43), (1.125, 0.35), (1.148, 0.22),
    (1.155, 0.1), (1.156, 0),
)  # fmt: skip
PAD = (
    (0.285, 0), (0.29, 0.04), (0.305, 0.08), (0.34, 0.13), (0.4, 0.2), (0.5, 0.28), (0.6, 0.333), (0.7, 0.362),
    (0.8, 0.374), (0.87, 0.372), (0.93, 0.345), (0.98, 0.29), (1.02, 0.2), (1.043, 0.1), (1.05, 0),
)  # fmt: skip
HEAD = 1.156 * KEY_W
BORE = (0.112 * KEY_W, 0.07 * KEY_W)  # the hole for the ring: how far from the tip, and its radius
BLADE, SHANK, STEM = 0.945 * KEY_W, 0.2 * KEY_W, 0.7
# The halves of the shell part at PART above the mat, the lacquered half rises to TOP,
# and the ring crosses the hole just under the lip, at RING_Z.
PART, TOP, RING_Z = 0.75, 1.9, 1.3
MARGIN = 0.1


def spaced(outline, pitch, closed=True):
    """Points every `pitch` along a polyline, each with the heading of the line there."""
    points = list(outline) + ([outline[0]] if closed else [])
    lengths = [math.hypot(bx - ax, by - ay) for (ax, ay), (bx, by) in zip(points, points[1:])]
    count = max(1, round(sum(lengths) / pitch))
    step = sum(lengths) / count
    out, travelled, target = [], 0.0, step / 2
    for ((ax, ay), (bx, by)), length in zip(zip(points, points[1:]), lengths):
        while length > 0 and target <= travelled + length:
            t = (target - travelled) / length
            out.append((ax + (bx - ax) * t, ay + (by - ay) * t, math.atan2(by - ay, bx - ax)))
            target += step
        travelled += length
    return out


def stitch(sheet, points, thread="#e6dabb", length=0.27, width=0.09, slant=0.26):
    """Saddle stitching: each stitch leans, sits proud of the leather and ends in a hole."""
    colour = linear(thread)
    for x, y, heading in points:
        dx, dy = math.cos(heading + slant) * length / 2, math.sin(heading + slant) * length / 2
        rows, cols = sheet.window(x - 0.3, y - 0.3, x + 0.3, y + 0.3)
        X, Y = sheet.X[rows, cols], sheet.Y[rows, cols]
        for ex, ey in ((x - dx, y - dy), (x + dx, y + dy)):
            hole = cover(disc(X, Y, ex, ey, 0.055), sheet.aa * 2)
            sheet.rgb[rows, cols] *= 1 - 0.8 * hole[..., None]
            sheet.height[rows, cols] -= 0.03 * hole
        core = segment(X, Y, x - dx, y - dy, x + dx, y + dy)
        cord = cover(core - width / 2, sheet.aa)
        crown = np.sqrt(np.clip(1 - (core / (width / 2)) ** 2, 0, 1))
        # Waxed thread is two plies twisted together.
        along = (X - x) * math.cos(heading + slant) + (Y - y) * math.sin(heading + slant)
        ply = 0.86 + 0.14 * np.sin((along + core) * 2 * math.pi / 0.055)
        sheet.rgb[rows, cols] += cord[..., None] * (colour * (ply * (0.8 + 0.2 * crown))[..., None] - sheet.rgb[rows, cols])
        sheet.height[rows, cols] += 0.04 * crown * cord
        sheet.rough[rows, cols] += cord * (0.62 - sheet.rough[rows, cols])
        sheet.metal[rows, cols] *= 1 - cord


def spline(points, steps=8, closed=True):
    """A smooth curve through the points."""
    count = len(points)
    out = []
    for i in range(count if closed else count - 1):
        if closed:
            p0, p1, p2, p3 = (points[(i + k - 1) % count] for k in range(4))
        else:
            p0, p1, p2, p3 = (points[min(count - 1, max(0, i + k - 1))] for k in range(4))
        for s in range(steps):
            t = s / steps
            out.append(
                tuple(
                    0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (3 * b - a - 3 * c + d) * t**3)
                    for a, b, c, d in zip(p0, p1, p2, p3)
                )
            )
    return out if closed else out + [points[-1]]


def polygon(X, Y, points):
    """Signed distance to a closed outline. Negative inside."""
    d = np.full(X.shape, np.inf)
    inside = np.zeros(X.shape, dtype=bool)
    for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
        d = np.minimum(d, segment(X, Y, ax, ay, bx, by))
        if ay != by:
            inside ^= ((ay > Y) != (by > Y)) & (X < ax + (bx - ax) * (Y - ay) / (by - ay))
    return np.where(inside, -d, d)


def traced(sheet, points, width):
    """Coverage of a line of the given width drawn through the points."""
    d = np.full(sheet.X.shape, np.inf)
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        d = np.minimum(d, segment(sheet.X, sheet.Y, ax, ay, bx, by))
    return sheet.mask(d - width / 2)


def moulded(sheet, z):
    """A warp for Sheet.build that follows a height painted on the sheet's own grid."""

    def warp(x, y):
        return sample(z[..., None], np.asarray(x) * sheet.ppe - 0.5, np.asarray(y) * sheet.ppe - 0.5)[..., 0]

    return warp


def lay(obj, at, turn):
    """Put something built about its own origin at a point of the frame, turned clockwise as the page turns."""
    obj.location = (at[0], -at[1], 0)
    obj.rotation_euler = (0, 0, -math.radians(turn))
    return obj


def wall(stage, name, outline, z0, z1, material):
    """A band standing on an outline, with no floor and no lid."""
    bm = bmesh.new()
    low = [bm.verts.new((x, -y, z0)) for x, y in outline]
    high = [bm.verts.new((x, -y, z1)) for x, y in outline]
    for i in range(len(outline)):
        j = (i + 1) % len(outline)
        bm.faces.new((low[i], low[j], high[j], high[i]))
    return finish(stage, name, bm, material)


def split_ring(stage, name, centre, across, up, radius, wire, material, ends, steps=480, around=18):
    """Two turns of wire wound side by side. Where its two cut ends meet, the wire steps from one turn to the other.
    across and up span the plane of the ring, and ends is the angle in it at which the ends lie."""
    axis = across.cross(up)
    step_over = math.radians(15)
    bm = bmesh.new()
    loops = []
    for i in range(steps + 1):
        swept = step_over + (4 * math.pi - 2 * step_over) * i / steps
        t = min(1.0, max(0.0, (swept - (2 * math.pi - step_over)) / (2 * step_over)))
        side = wire * (2 * t * t * (3 - 2 * t) - 1)
        out = math.cos(ends + swept) * across + math.sin(ends + swept) * up
        core = centre + radius * out + side * axis
        loops.append(
            [
                bm.verts.new(core + wire * (math.cos(2 * math.pi * k / around) * out + math.sin(2 * math.pi * k / around) * axis))
                for k in range(around)
            ]
        )
    for a, b in zip(loops, loops[1:]):
        for k in range(around):
            bm.faces.new((a[k], b[k], b[(k + 1) % around], a[(k + 1) % around]))
    bm.faces.new(loops[0])
    bm.faces.new(loops[-1])
    return finish(stage, name, bm, material)


def tag(stage):
    """The leather tag and its eyelet. Returns how high the leather stands at the eyelet."""
    sheet = Sheet(TAG_W, TAG_H, "#34503f", rough=0.42)
    X, Y = sheet.X, sheet.Y
    shape = sheet.height.shape
    sheet.cut(box(X, Y, 0, 0, TAG_W, TAG_H, 1.05))
    sheet.punch(disc(X, Y, *EYE, HOLE))

    # The tab is tan, and the green body laps over it.
    sheet.paint(sheet.mask(SEAM - X), "#b07e47")
    sheet.height += 0.045 * (1 - ramp(SEAM - 0.03, SEAM + 0.05, X))
    sheet.ink(sheet.mask(np.abs(X - SEAM - 0.03) - 0.03), "#1d1916", 0.5)

    # Handling has darkened the tan round the eyelet and along its edges, and left the green a little uneven.
    handled = np.clip(0.6 + 0.5 * cloud(shape, 51, falloff=2.2), 0, 1)
    near = np.exp(-((disc(X, Y, *EYE, HOLE) / 1.3) ** 2)) + 0.6 * (1 - ramp(0.0, 0.9, -sheet.sdf))
    sheet.ink(np.clip(near, 0, 1) * handled * sheet.mask(SEAM - X), "#3a2414", 0.3)
    sheet.finish(np.clip(near, 0, 1) * handled * sheet.mask(SEAM - X), rough=0.3)
    sheet.rgb *= (1 + 0.05 * cloud(shape, 52, falloff=2.0))[..., None]

    # The name goes in before the stitching, blind stamped as a leather goods maker does it: a small brass die
    # in Geist Mono capitals, set a touch tighter than the face, pressed shallow into the grain without foil in the bottom left
    # corner of the stitched panel. It shows by its crisp walls catching the light, the floor of each letter a
    # shade darker and a little smoother than the grain round it, where the warm die has set the leather.
    r0, r1, c0, c1 = (round(v * sheet.ppe) for v in (6.35, 6.35 + 1.2, 1.15, 1.15 + 6.0))
    name = np.zeros(shape)
    name[r0:r1, c0:c1] = fit(pixels_of(os.path.join(ART, "tag-anurag.png"))[..., 3:].astype(np.float64), r1 - r0, c1 - c0)[..., 0]
    sheet.press(blur(name, 0.6), 0.02)
    set_ = blur(name, 0.5)
    sheet.rgb *= (1 - 0.14 * set_)[..., None]
    sheet.finish(set_, rough=0.3)

    # Lacoste's crocodile on the tab, in its own colours, standing a hair proud of the leather as it does on the
    # brand's own leather goods.
    sheet.art(os.path.join(ART, "lacoste-crocodile.png"), 14.4, 4.95, 17.0, 4.95 + 2.6 * 255 / 420, relief=0.02)

    # Keys have been dragged across it: a few pale hairlines, none of them straight.
    rng = np.random.default_rng(458)
    lines = np.zeros(shape)
    for _ in range(9):
        x, y = rng.uniform(0.8, TAG_W - 0.8), rng.uniform(0.8, TAG_H - 0.8)
        turn, bend, half = np.radians(rng.normal(20, 35)), np.radians(rng.normal(0, 8)), rng.uniform(0.25, 0.9)
        width, weight = rng.uniform(0.004, 0.009), rng.uniform(0.35, 0.9)
        for way, angle in ((-1, turn - bend), (1, turn + bend)):
            d = segment(X, Y, x, y, x + way * half * np.cos(angle), y + way * half * np.sin(angle), width)
            lines = np.maximum(lines, sheet.mask(d) * weight)
    lines *= np.clip(0.5 + 0.6 * cloud(shape, 55, falloff=1.2), 0, 1)
    sheet.rgb *= (1 + 0.9 * lines)[..., None]
    sheet.finish(lines, rough=0.7)
    sheet.press(lines, 0.004)

    # Edges are burnished and painted dark. The stitch line is creased in before the thread goes through.
    sheet.ink(ramp(-0.1, -0.02, sheet.sdf), "#1d1916", 0.55)
    sheet.soften(0.18, 0.07)
    around = np.abs(sheet.sdf + INSET)
    lapped = np.maximum(np.abs(X - SEAM + INSET), np.abs(Y - TAG_H / 2) - (TAG_H / 2 - INSET))
    crease = np.minimum(around, lapped)
    sheet.press(np.exp(-((crease / 0.09) ** 2)), 0.016)
    stitch(sheet, spaced(rect(INSET, INSET, TAG_W - INSET, TAG_H - INSET, 1.05 - INSET, 12), PITCH))
    stitch(sheet, spaced([(SEAM - INSET, INSET + 0.3), (SEAM - INSET, TAG_H - INSET - 0.3)], PITCH, closed=False))
    # Round the eyelet the leather is crushed down.
    sheet.press(np.exp(-((disc(X, Y, *EYE, 0.88) / 0.18) ** 2)), 0.025)

    def lie(x, y):
        return 0.05 * (1 - ((x - TAG_W / 2) / (TAG_W / 2)) ** 2) * (1 - ((y - TAG_H / 2) / (TAG_H / 2)) ** 2)

    leather = sheet.build(
        stage,
        "tag",
        thickness=THICK,
        warp=lie,
        scan="Leather037",
        scan_size=5.5,
        scan_normal=1.6,
        scan_rough=1.0,
        wear=(("SurfaceImperfections003", 12, 0.1, 0),),
        mottle=0.07,
        sheen=0.15,
        specular=0.5,
        subsurface=0.03,
        at=(-EYE[0], -EYE[1]),
    )
    lay(leather, EYE_AT, TURN)

    z = sheet.z(*EYE)
    brass = worn(principled("brass", (0.86, 0.64, 0.28), rough=0.18, metal=1.0), "Scratches003", 3, 0.2)
    rim = [(0.0, HOLE), (0.08, HOLE - 0.03), (0.13, HOLE + 0.03), (0.14, 0.7), (0.11, 0.84), (0.04, 0.92), (0.0, 0.94)]
    eyelet = lathe(stage, "eyelet", rim, brass, steps=96, axis="Z", caps=False)
    eyelet.location = (EYE_AT[0], -EYE_AT[1], z)
    return z


def ring(stage, tag_z):
    """The split ring, leaning through the eyelet. Returns where in the frame it crosses the key's hole."""
    reach = RING * math.sin(LEAN)
    height = reach + WIRE * (1 + math.cos(LEAN))
    across = Vector((math.cos(LEVEL), -math.sin(LEVEL), 0))
    uphill = Vector((math.sin(LEVEL), math.cos(LEVEL), 0))
    up = uphill * math.cos(LEAN) + Vector((0, 0, math.sin(LEAN)))

    def on(turn):
        return RING * (math.cos(turn) * across + math.sin(turn) * up)

    # The leather hangs from the low side of the ring and the key from the other end of its level diameter.
    at_tag = math.pi - math.asin((tag_z - height) / reach)
    at_key = math.asin((RING_Z - height) / reach)
    centre = Vector((EYE_AT[0], -EYE_AT[1], tag_z)) - on(at_tag)
    steel = worn(principled("steel", (0.76, 0.77, 0.79), rough=0.14, metal=1.0), "Scratches003", 4, 0.22)
    split_ring(stage, "ring", centre, across, up, RING, WIRE, steel, ends=math.radians(62))
    hole = centre + on(at_key)
    return hole.x, -hole.y


def marks(sheet, place):
    """The pictograms moulded into the buttons: an open padlock, a closed one and a car with its boot up.
    They read the right way up with the blade pointing away."""
    cut = np.zeros(sheet.height.shape)

    def line(points, width=0.06):
        nonlocal cut
        cut = np.maximum(cut, traced(sheet, [place(along, across) for across, along in points], width))

    def padlock(across, along, open_by):
        body = [(-0.052, -0.058), (0.052, -0.058), (0.052, 0.015), (-0.052, 0.015), (-0.052, -0.058)]
        line([(across + x, along + y) for x, y in body])
        bow = [(0.032 * math.cos(a), 0.045 + 0.032 * math.sin(a)) for a in np.linspace(0, math.pi, 13)]
        shackle = [(0.032, 0.015 if not open_by else 0.038), *bow, (-0.032, 0.015)]
        line([(across + open_by + x * (-1 if open_by else 1), along + y) for x, y in shackle])
        line([(across, along - 0.015), (across, along - 0.033)])

    padlock(-0.185, 0.82, -0.045)
    padlock(0.185, 0.82, 0.0)

    # The car, seen from the side.
    across, along = 0.0, 0.47
    body = [
        (-0.125, -0.022), (-0.122, 0.004), (-0.07, 0.014), (-0.036, 0.044), (0.03, 0.044), (0.062, 0.016),
        (0.118, 0.01), (0.125, -0.022), (0.096, -0.022),
    ]  # fmt: skip
    line([(across + x, along + y) for x, y in body])
    line([(across + x, along - 0.022) for x in (-0.125, -0.096)])
    line([(across + x, along - 0.022) for x in (-0.054, 0.054)])
    for wheel in (-0.075, 0.075):
        line([(across + wheel + 0.02 * math.cos(a), along - 0.024 + 0.02 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 17)], 0.04)
    line([(across + 0.064, along + 0.02), (across + 0.118, along + 0.052)])
    return cut


def key(stage, hole_at):
    """The key, built about the hole in its tip and laid with that hole where the ring crosses it."""
    length, width = HEAD + 2 * MARGIN, KEY_W + 2 * MARGIN
    middle = KEY_W / 2 + MARGIN
    hole = (BORE[0] + MARGIN, middle)

    def place(along, across):
        return along * KEY_W + MARGIN, across * KEY_W + middle

    def outline(half):
        there = [place(u, -v) for u, v in half]
        back = [place(u, v) for u, v in half[-2:0:-1]]
        return spline(there + back)

    shell_edge, pad_edge = outline(SHELL), outline(PAD)
    shell = Sheet(length, width, "#d0161a", rough=0.07)
    X, Y = shell.X, shell.Y
    shape = shell.height.shape
    edge = polygon(X, Y, shell_edge)
    opening = polygon(X, Y, pad_edge)
    bore = disc(X, Y, *hole, BORE[1])

    # The lacquered half is a pebble: it rolls over at the edge, thins towards the tip and is barely crowned.
    inside = np.clip(-edge, 0, None)
    roll = (1 - (1 - np.clip(inside / (0.3 * KEY_W), 0, 1)) ** 2.4) ** (1 / 2.4)
    taper = 0.66 + 0.34 * ramp(0, 0.5 * KEY_W, X - MARGIN)
    crown = 1 - 0.05 * ((Y - middle) / (KEY_W / 2)) ** 2
    dome = (TOP - PART) * roll * taper * crown
    # Past the edge the mesh falls away steeply, so the shading at the edge stays that of a wall.
    dome = np.where(edge > 0, np.maximum(-6 * edge, 0.05 - PART), dome)

    shell.cut(edge)
    shell.punch(opening)
    shell.punch(bore)
    # The lip of the opening for the pad and of the hole for the ring are rounded over.
    shell.height -= 0.1 * (1 - np.clip(opening / 0.09, 0, 1)) ** 2
    shell.height -= 0.1 * (1 - np.clip(bore / 0.08, 0, 1)) ** 2

    # The ring has chipped the lacquer off round the hole, down to the pale plastic.
    ragged = np.clip(cloud(shape, 61, falloff=1.7), -0.7, 1.6)
    chipped = shell.mask(bore - 0.02 - 0.075 * ragged)
    shell.paint(chipped * 0.88, "#d2c6ba")
    shell.finish(chipped, rough=0.55)
    shell.press(chipped, 0.006)

    # A pocket full of other keys: hairlines, a few nicks and dulled patches on the shoulders.
    rng = np.random.default_rng(430)
    lines = np.zeros(shape)
    for _ in range(22):
        x, y = rng.uniform(0.4, length - 0.4), rng.uniform(0.4, width - 0.4)
        turn, bend, half = np.radians(rng.uniform(0, 180)), np.radians(rng.normal(0, 9)), rng.uniform(0.15, 0.7)
        fine, weight = rng.uniform(0.003, 0.007), rng.uniform(0.3, 1.0)
        for way, angle in ((-1, turn - bend), (1, turn + bend)):
            d = segment(X, Y, x, y, x + way * half * np.cos(angle), y + way * half * np.sin(angle), fine)
            lines = np.maximum(lines, shell.mask(d) * weight)
    lines *= np.clip(0.5 + 0.6 * cloud(shape, 62, falloff=1.2), 0, 1)
    shell.rgb += (lines * 0.3)[..., None] * (linear("#e58a84") - shell.rgb)
    shell.finish(lines, rough=0.5)
    shell.press(lines, 0.003)
    nicks = np.zeros(shape)
    for _ in range(7):
        x, y, r = rng.uniform(0.5, length - 0.5), rng.uniform(0.5, width - 0.5), rng.uniform(0.012, 0.03)
        nicks = np.maximum(nicks, shell.mask(disc(X, Y, x, y, r)))
    shell.paint(nicks * 0.7, "#d9cdc3")
    shell.press(blur(nicks, 1.0), 0.008)
    shoulder = (1 - ramp(0.15, 0.9, inside)) * np.clip(cloud(shape, 63, falloff=1.6) - 0.2, 0, 1)
    shell.finish(np.clip(shoulder, 0, 1) * 0.6, rough=0.34)

    lacquer = shell.build(
        stage,
        "shell",
        thickness=PART + dome.min(),
        warp=moulded(shell, dome),
        wear=(("Scratches003", 2.6, 0.1, 0.0006), ("Fingerprints009", 4.2, 0.14, 0), ("SurfaceImperfections003", 5, 0.05, 0)),
        specular=0.5,
        at=(-hole[0], -hole[1]),
        step=0.03,
    )

    # The rubber pad sits in the opening, a little under the lacquer. Grooves split it into three buttons,
    # each one a low pillow.
    pad = Sheet(length, width, "#1b1b1c", rough=0.62)
    fork, rim = place(0.69, 0), (place(0.52, -0.34), place(0.52, 0.34), place(1.06, 0))
    grooves = np.minimum.reduce([segment(X, Y, *fork, *end) for end in rim]) - 0.05
    within = np.clip(np.minimum(-opening, grooves), 0, None)
    pillow = 0.05 * (1 - (1 - np.clip(within / 0.13, 0, 1)) ** 2) + 0.02 * (1 - (1 - np.clip(within / 0.8, 0, 1)) ** 2)
    pad.cut(opening - 0.07)
    cut = marks(pad, place)
    pad.press(blur(cut, 1.0), 0.025)
    # Thumbs have polished the crowns of the buttons, and dust has settled in the grooves and the pictograms.
    polished = np.clip(within / 0.8, 0, 1) ** 2 * np.clip(0.55 + 0.5 * cloud(shape, 64, falloff=2.0), 0, 1)
    pad.finish(polished, rough=0.4)
    low = np.clip(1 - within / 0.05, 0, 1)
    dust = np.clip(np.maximum(low, cut), 0, 1) * np.clip(0.5 + 0.45 * cloud(shape, 65, falloff=2.0), 0, 1)
    pad.paint(dust * 0.22, "#8d857a")
    pad.finish(dust, rough=0.8)
    specks = np.clip(cloud(shape, 66, falloff=0.25) - 3.1, 0, 1)
    pad.paint(np.clip(specks * 1.5, 0, 0.4), "#a39c90")
    rubber = pad.build(
        stage,
        "pad",
        thickness=PART,
        warp=moulded(pad, np.clip(dome - 0.075 + pillow, 0, None)),
        scan="Rubber004",
        scan_size=1.6,
        scan_normal=0.5,
        scan_rough=0.4,
        wear=(("SurfaceImperfections003", 3, 0.1, 0),),
        specular=0.35,
        at=(-hole[0], -hole[1]),
        step=0.03,
    )

    # The blade: nickel silver, its stem under the shell, a wide shank and then the bar the track is milled in.
    reach, girth = STEM + BLADE, 0.235 * KEY_W + 2 * MARGIN
    mid, a, b, neck = girth / 2, 0.1175 * KEY_W, 0.0925 * KEY_W, STEM + SHANK
    bar = Sheet(reach, girth, "#cbc8be", rough=0.34)
    BX, BY = bar.X, bar.Y
    grid = bar.height.shape
    profile = [
        (0, mid - a), (neck, mid - a), (neck + 0.12, mid - b), (reach - 0.1, mid - b), (reach, mid - b + 0.1),
        (reach, mid + b - 0.1), (reach - 0.1, mid + b), (neck + 0.12, mid + b), (neck, mid + a), (STEM + 0.62, mid + a),
        (STEM + 0.55, mid + a - 0.08), (STEM + 0.48, mid + a), (0, mid + a),
    ]  # fmt: skip
    bar.cut(polygon(BX, BY, profile))
    bar.metal[:] = 1.0
    # Ground along its length, then scored by the lock every time it went in.
    fine, coarse = streaks(grid, 71, 200, 0.7), streaks(grid, 72, 420, 2.0)
    bar.height += 0.00015 * fine + 0.0002 * coarse
    bar.rough += np.clip(0.03 * coarse + 0.02 * fine, -0.1, 0.12)
    bar.rgb *= (1 + 0.015 * coarse)[..., None]
    bar.chamfer(0.07, 0.05)
    # The track, as on the key in the photograph, running out through the end of the blade.
    waves = (
        (0.27, -0.19), (0.34, -0.12), (0.41, 0.19), (0.52, 0.48), (0.61, 0.19), (0.7, -0.19), (0.78, 0.0), (0.85, 0.19),
        (0.93, -0.05), (1.03, -0.42),
    )  # fmt: skip
    track = traced(bar, spline([(STEM + s * BLADE, mid + t * b) for s, t in waves], closed=False), 0.33)
    mouth = bar.mask(box(BX, BY, reach - 0.5, mid - b * 0.85, reach + 1, mid + b * 0.1, 0.05))
    track = np.maximum(track, mouth * ramp(reach - 0.5, reach - 0.2, BX))
    bar.press(blur(track, 1.3), 0.09)
    # The cutter left the floor of the track dull, with its passes still showing across it.
    bar.paint(track * 0.92, "#453d33")
    bar.rgb *= (1 + 0.1 * track * streaks(grid, 73, 1.5, 12))[..., None]
    bar.finish(track, rough=0.62)
    blade = bar.build(
        stage,
        "blade",
        thickness=PART + 0.05,
        scan="Metal009",
        scan_size=9,
        scan_normal=0.05,
        scan_rough=0.18,
        wear=(("Scratches003", 5, 0.2, 0.001), ("SurfaceImperfections003", 7, 0.08, 0)),
        brushed=0.7,
        at=(HEAD - STEM - BORE[0], -mid),
    )

    # The other half of the shell is black and is only a wall from above. Without it the light would get under.
    black = principled("base", (0.02, 0.02, 0.021), rough=0.45)
    base = wall(stage, "base", [(x - hole[0], y - hole[1]) for x, y in shell_edge], 0.03, PART + 0.01, black)
    for part in (lacquer, rubber, blade, base):
        lay(part, hole_at, KEY_TURN)
    dark = principled("bore", (0.2, 0.012, 0.014), rough=0.4)
    sleeve = lathe(stage, "bore", [(0.03, BORE[1]), (1.15, BORE[1])], dark, steps=64, axis="Z", caps=False)
    sleeve.location = (hole_at[0], -hole_at[1], 0)


def bunch(stage):
    key(stage, ring(stage, tag(stage)))
    stage.shoot("name", (0, 0, W, H), bleed=2.0, shadow=0.8, sharp=1.25)


SHOTS = {"name": bunch}
