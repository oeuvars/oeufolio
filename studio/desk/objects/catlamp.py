"""The desk lamp: a glazed porcelain cat, stretched in a play bow, its tail rising from the rump and arching
forward over its back. From the tail's tip hangs the lamp's head, after an arched floor lamp's: an orange enamelled
dome gilded inside, on a brass neck, with the bulb up inside it, lighting the cat and the desk below.

The cat is the household's own, a long-haired Turkish Van, modelled from her photographs. She is white, with a
ginger cap over the top and back of her head and the backs of her ears, down to her upper lids in front and her
upper neck behind, parted by a white blaze that is as wide as the gap between her eyes and narrows to a point at the
top of her forehead. Her nose and the insides of her ears are pink, there is a ginger patch on her left upper lip,
four ginger spots in two pairs on her shoulders, and her tail is ginger from its root. Her head is turned to her
right and lifted, to look up at whoever stands at the near side of the desk, with amber glass eyes set in lidded
sockets, as a figurine maker sets them. The colours are airbrushed on under a thick glossy glaze.

The body is one smooth solid, modelled as a signed distance field (sdf.py): the head in its own turned frame, with
its cheeks, muzzle, brows, eyelids and cupped ears, the chest and back, the legs and paws, and the tail along a
curve, blended into each other as a figurine is modelled in clay, combed into long hair, and cut flat underneath
where it stands. Where each colour goes is laid on the vertices.

Built in its own coordinates, in em: the head toward -x, her right toward +y, the tail toward +x, standing on z = 0.
The lamp is the light marked "bulb", at no power until desk.py turns it up."""

import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix

from paint import linear
from sdf import cone, ellipsoid, mesh, smax, smin
from solids import lathe

# The box the cat stands in, in em, and where the cat's own origin lies in it.
W, H = 27.0, 16.5
ORIGIN = (2.6, 5.5)
# Fine enough for the rims of the eyelids.
STEP = 0.055

# The porcelain, and the underglaze colours: her ginger, light and deep, the pink of her nose and the insides of
# her ears, the dark brown of the rims of her eyelids, and the dusky pink of the line of her mouth.
WHITE = "#f7ecdc"
GINGER = "#e2934c"
DEEP = "#bd6527"
PINK = "#e79a94"
LINE = "#3b2219"
LIP = "#b9746c"
# The glass eyes: amber, greener round the pupil, a dark ring at the rim of the iris.
IRIS = (("#7f8a34", 0.0), ("#a7a03a", 0.3), ("#d99b2d", 0.55), ("#c27a1f", 0.76), ("#4b2c10", 0.86), ("#efe4c8", 0.92))
# The lamp: the same warm bulb as the pendant it replaces.
BULB_COLOUR = (1.0, 0.74, 0.46)
BULB_R = 0.8
# The head: where the tail's tip holds it, the brass neck's length, and the dome's radius and thickness.
ENAMEL = "#e5591a"
NECK = 0.9
SHADE_R = 3.0
SHADE_T = 0.1

# The tail rises from the rump and arches forward over the cat's left side, so the lamp hangs over her head and lights
# her lifted face, and the markings on her back are left in sight of the camera on her right. It is a long-haired
# plume: thin at its root, full along its middle, and gathered again where it holds the lamp.
TAIL = ((17.4, 0.0, 7.4), (22.0, -1.0, 14.5), (12.5, -4.6, 21.0), (5.5, -3.2, 17.8))
HEAD = (5.5, -3.2, 17.8)

# Her head: the middle of her skull, and how it is held: turned this many degrees to her right, her chin lifted,
# and cocked a little, to look up at whoever holds a camera over the near side of the desk, and into the lamp's light.
SKULL = np.array([4.3, 0.35, 5.0])
TURN, LIFT, COCK = 40.0, 50.0, -8.0
# The eyes, in the head's frame: an eyeball's radius, how thick the lids are over it, and how far the lids are
# open on either side of the gaze, across and up, as the tangent of the angle.
EYE_R = 0.6
LID = 0.1
EYE_AT = (-1.38, 0.95, 0.12)
OPEN = (1.4, 0.95)
SLANT = math.radians(12)


def turned():
    # Turning to her right is turning clockwise seen from above.
    a, b, c = (math.radians(v) for v in (-TURN, LIFT, COCK))
    yaw = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    lift = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    cock = np.array([[1, 0, 0], [0, math.cos(c), -math.sin(c)], [0, math.sin(c), math.cos(c)]])
    return yaw @ lift @ cock


# From the head's frame to the cat's: a column for each of the head's axes.
TURNED = turned()


def in_head(p):
    return (p - SKULL) @ TURNED


def unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def eyes():
    """Each eye, in the head's frame: its centre, where it looks, and which way is out and which up across it."""
    out = []
    for side in (1, -1):
        centre = np.array([EYE_AT[0], side * EYE_AT[1], EYE_AT[2]])
        gaze = unit((-1.0, side * 0.18, 0.07))
        up = unit(np.array([0, 0, 1.0]) - gaze[2] * gaze)
        across = unit(np.cross(up, gaze)) * -side
        out.append((centre, gaze, across, up))
    return out


EYES = eyes()


def sphere(p, centre, r):
    return np.linalg.norm(p - np.asarray(centre), axis=-1) - r


def both(p, part):
    """A part the cat has on both sides, given for her right one (+y)."""
    return np.minimum(part(p), part(p * np.array([1, -1, 1])))


def soft(x, edge, width):
    t = np.clip((x - edge) / width + 0.5, 0, 1)
    return t * t * (3 - 2 * t)


def waves(p, size, seed, count=6, across=None, squeeze=0.15):
    """A sum of plane waves, about -1 to 1. Given a direction, the waves run along it, as combed hair does."""
    rng = np.random.default_rng(seed)
    out = np.zeros(p.shape[:-1])
    for _ in range(count):
        k = rng.normal(size=3)
        if across is not None:
            k = k - (1 - squeeze) * (k @ across) * np.asarray(across)
        k = k / np.linalg.norm(k) / size * rng.uniform(0.7, 1.3)
        out += np.sin(p @ k + rng.uniform(0, 6.3))
    return out / math.sqrt(count)


def opening(h, eye):
    """Where the lids part over an eye: a cone from the eye's centre, its mouth an almond slanted up toward the outer
    corner, and no deeper than the lids."""
    centre, gaze, across, up = eye
    q = h - centre
    g = q @ gaze
    a0, b0 = q @ across, q @ up
    a = a0 * math.cos(SLANT) + b0 * math.sin(SLANT)
    b = -a0 * math.sin(SLANT) + b0 * math.cos(SLANT)
    depth = np.maximum(g, 0.02)
    r = np.linalg.norm(q, axis=-1)
    spread = np.sqrt((a / (OPEN[0] * depth)) ** 2 + (np.abs(b) / (OPEN[1] * depth)) ** 2)
    mouth = np.where(g > 0, (spread - 1) * np.minimum(r, 0.8) * 0.5, 1.0)
    return np.maximum(mouth, r - (EYE_R + 0.45))


def ear_frame(side):
    """An ear's base, its length up to the tip, and its axes: across the base, up to the tip, and out of its cup."""
    base = np.array([0.45, side * 1.5, 1.45])
    tip = np.array([0.85, side * 2.45, 3.75])
    up = unit(tip - base)
    front = unit((-1.0, side * 0.45, 0.1))
    front = unit(front - (front @ up) * up)
    across = np.cross(up, front)
    return base, np.linalg.norm(tip - base), across, up, front


def triangle(u, v, corners):
    """The distance in a plane to a triangle, negative inside."""
    (ax, ay), (bx, by), (cx, cy) = corners
    best = np.full(u.shape, np.inf)
    sign = np.ones(u.shape)
    for (px, py), (qx, qy) in (((ax, ay), (bx, by)), ((bx, by), (cx, cy)), ((cx, cy), (ax, ay))):
        ex, ey = qx - px, qy - py
        wx, wy = u - px, v - py
        t = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey), 0, 1)
        dx, dy = wx - ex * t, wy - ey * t
        best = np.minimum(best, dx * dx + dy * dy)
        sign = np.where(ex * wy - ey * wx > 0, sign, -1)
    return np.sqrt(best) * np.where(sign > 0, -1, 1)


def ear_coords(h, side):
    base, length, across, up, front = ear_frame(side)
    q = h - base
    u, v, w = q @ across, q @ up, q @ front
    flat = triangle(u * side, v, ((-1.15, -0.7), (1.15, -0.7), (0.05, length - 0.3))) - 0.28
    along = np.clip(v / length, 0, 1)
    # The cup: its sides curl forward round the hollow, and the ear is thicker where it grows from the head.
    middle = 0.45 * (u / 1.15) ** 2 * np.clip(1 - along, 0.3, 1)
    return flat, w - middle, 0.09 + 0.24 * (1 - along) ** 2, along


def ear(h, side):
    flat, w, thick, _ = ear_coords(h, side)
    return smax(flat, np.abs(w) - thick, 0.07)


def head(h):
    """The head in its own frame, looking along -x: a round skull, full cheeks, a short straight nose, round
    whisker pads, a small chin, brows over the eyes, lidded eyes, big upright ears, and a ruff of long hair."""
    d = ellipsoid(h, (0.2, 0, 0.25), (2.3, 2.15, 2.0))
    d = smin(d, both(h, lambda q: ellipsoid(q, (-0.7, 1.45, -0.7), (1.5, 1.25, 1.25))), 0.6)
    d = smin(d, cone(h, (-1.0, 0, 0.75), (-2.42, 0, -0.32), 0.62, 0.4), 0.45)
    d = smin(d, both(h, lambda q: ellipsoid(q, (-2.1, 0.5, -0.95), (0.62, 0.66, 0.52))), 0.25)
    d = smin(d, ellipsoid(h, (-1.85, 0, -1.5), (0.6, 0.52, 0.42)), 0.3)
    d = smin(d, ellipsoid(h, (-2.5, 0, -0.45), (0.3, 0.36, 0.26)), 0.15)
    d = smin(d, both(h, lambda q: ellipsoid(q, (-1.3, 0.95, 0.74), (0.75, 0.72, 0.36))), 0.3)
    for centre, *_ in EYES:
        d = smin(d, sphere(h, centre, EYE_R + LID), 0.25)
    d = smin(d, np.minimum(ear(h, 1), ear(h, -1)), 0.3)
    # The ruff: long hair round the backs of the cheeks and under the chin, combed back and down.
    ruff = both(h, lambda q: np.minimum(ellipsoid(q, (0.3, 1.85, -1.0), (1.4, 1.0, 1.5)), ellipsoid(q, (1.2, 1.55, 0.1), (1.2, 0.9, 1.3))))
    ruff = np.minimum(ruff, ellipsoid(h, (-0.6, 0, -1.9), (1.4, 1.5, 0.9)))
    ruff = ruff - 0.07 * waves(h, 0.13, 21, across=(1, 0, 0)) - 0.1 * waves(h, 0.45, 22, across=(1, 0, 0))
    d = smin(d, ruff, 0.5)
    return d


def foreleg(q):
    upper = cone(q, (6.6, 1.75, 2.9), (5.3, 1.95, 0.95), 1.1, 0.82)
    lower = cone(q, (5.3, 1.95, 0.8), (1.7, 1.6, 0.55), 0.76, 0.56)
    paw = ellipsoid(q, (0.95, 1.55, 0.47), (0.95, 0.72, 0.47))
    toes = np.minimum.reduce([sphere(q, (x, 1.55 + o, 0.34), 0.27) for x, o in ((0.3, -0.45), (0.1, -0.15), (0.1, 0.15), (0.3, 0.45))])
    leg = smin(smin(upper, lower, 0.5), paw, 0.45)
    return smin(leg, toes, 0.12)


def hindleg(q):
    thigh = ellipsoid(q, (15.0, 2.05, 5.0), (2.4, 1.2, 2.5))
    shin = cone(q, (13.8, 2.3, 3.0), (16.6, 2.4, 1.5), 0.95, 0.55)
    foot = cone(q, (16.6, 2.4, 1.5), (15.9, 2.3, 0.5), 0.55, 0.5)
    paw = ellipsoid(q, (15.3, 2.3, 0.45), (0.95, 0.7, 0.45))
    toes = np.minimum.reduce([sphere(q, (x, 2.3 + o, 0.32), 0.25) for x, o in ((14.65, -0.4), (14.45, -0.13), (14.45, 0.13), (14.65, 0.4))])
    britches = ellipsoid(q, (16.6, 1.9, 3.6), (1.3, 1.1, 1.8))
    leg = smin(smin(smin(thigh, shin, 0.6), foot, 0.3), paw, 0.4)
    return smin(smin(leg, britches, 0.6), toes, 0.12)


def torso(p):
    """The chest low between the forelegs, the back rising to high haunches, the shoulder blades standing up
    where the forelegs reach forward, and the neck up into the turned head."""
    d = ellipsoid(p, (6.0, 0, 2.9), (2.4, 2.55, 2.3))
    d = smin(d, cone(p, (7.0, 0, 3.4), (14.0, 0, 6.0), 2.4, 2.7), 1.2)
    d = smin(d, ellipsoid(p, (15.4, 0, 6.4), (2.6, 2.7, 2.6)), 1.2)
    d = smin(d, both(p, lambda q: ellipsoid(q, (7.2, 1.35, 4.6), (1.5, 0.9, 1.0))), 0.8)
    nape = SKULL + TURNED @ np.array([1.0, 0, -0.9])
    d = smin(d, cone(p, nape, (6.2, 0, 3.6), 1.7, 2.1), 1.0)
    # Long hair, combed back along the body and down the flanks, everywhere but the legs below the elbows.
    hairy = soft(p[..., 2] - 1.6, 0, 1.2)
    d = d - hairy * (0.03 * waves(p, 0.09, 11, count=8, across=(1, 0, 0), squeeze=0.05) + 0.05 * waves(p, 0.35, 12, across=(1, 0, 0), squeeze=0.05) + 0.05)
    d = smin(d, both(p, foreleg), 0.9)
    return smin(d, both(p, hindleg), 1.0)


def tail_curve(samples=60):
    p0, p1, p2, p3 = (np.asarray(c, dtype=float) for c in TAIL)
    t = np.linspace(0, 1, samples)[:, None]
    points = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t**2 * p2 + t**3 * p3
    along = np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))))
    return points, along


def tail_frames(points):
    """A frame carried along the tail without twisting: its direction, and two axes round it."""
    ahead = np.diff(points, axis=0)
    ahead /= np.linalg.norm(ahead, axis=1, keepdims=True)
    normal = unit(np.cross(ahead[0], (0, 1, 0)))
    normals = []
    for t in ahead:
        normal = unit(normal - (normal @ t) * t)
        normals.append(normal)
    normals = np.array(normals)
    return ahead, normals, np.cross(ahead, normals)


def nearest_on_tail(p, samples=48):
    """For each point, its distance from the tail's line, how far along the tail it is (0 to 1), and its angle
    round it."""
    points, along = tail_curve(samples)
    _, normals, binormals = tail_frames(points)
    best = np.full(len(p), np.inf)
    s = np.zeros(len(p))
    angle = np.zeros(len(p))
    for i in range(len(points) - 1):
        a, ab = points[i], points[i + 1] - points[i]
        t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
        v = p - a - t[:, None] * ab
        dist = np.linalg.norm(v, axis=1)
        closer = dist < best
        best = np.where(closer, dist, best)
        s = np.where(closer, (along[i] + t * (along[i + 1] - along[i])) / along[-1], s)
        angle = np.where(closer, np.arctan2(v @ binormals[i], v @ normals[i]), angle)
    return best, s, angle


def tail(p):
    points, _ = tail_curve()
    lo, hi = points.min(axis=0) - 2.6, points.max(axis=0) + 2.6
    near = np.all((p > lo) & (p < hi), axis=-1)
    d = np.full(p.shape[:-1], 1e3)
    dist, s, angle = nearest_on_tail(p[near])
    radius = 0.95 + 0.85 * np.sin(np.pi * s) ** 0.7
    # Locks of hair along it, uneven and twisting a little, deepest where it is fullest.
    locks = np.zeros(len(s))
    rng = np.random.default_rng(31)
    for count, depth in ((4, 0.1), (7, 0.07), (13, 0.07), (23, 0.07), (37, 0.045)):
        twist, phase, uneven = rng.uniform(3, 8), rng.uniform(0, 6.3), rng.integers(2, 4)
        clumps = 0.6 + 0.4 * np.sin(uneven * angle + rng.uniform(9, 15) * s + phase)
        locks += depth * np.sin(count * angle + twist * s + phase) * clumps
    d[near] = dist - radius - locks * np.sin(np.pi * s) ** 0.6
    return d


def body(p):
    """The porcelain: the cat, without the lamp's head."""
    d = smin(torso(p), head(in_head(p)), 0.9)
    d = smin(d, tail(p), 0.7)
    h = in_head(p)
    for eye in EYES:
        d = smax(d, -opening(h, eye), 0.05)
    # It stands on a flat foot.
    return np.maximum(d, -p[..., 2])


def wobble(p, seed, scale=0.6, size=1.8):
    """A slow irregular wander, for the edges of brushed underglaze."""
    return scale * waves(p, size, seed, count=5)


def painted(verts, normals):
    """Where each colour goes, as she is marked in her photographs: how much ginger, pink, dark and lip line. The
    colours themselves are laid in the shader."""
    p = verts
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    h = in_head(p)
    n = normals @ TURNED
    hx, hy, hz = h[:, 0], h[:, 1], h[:, 2]
    side = np.abs(hy)
    eye_z = EYE_AT[2]
    face = soft(-n[:, 0] - 0.1, 0, 0.3)
    # The cap: the ginger comes down to just over the upper lids, to the outer corners of the eyes at the temples,
    # under the ears at the sides, and low round the back of the skull, where it ends on the upper neck.
    line = eye_z + 0.45 - 0.25 * soft(side - 1.05, 0, 0.7) - 1.8 * soft(hx - 1.7, 0, 1.0) + wobble(h, 1, 0.08, 0.6)
    cap = soft(hz - line, 0, 0.18) * soft(2.45 - hx + wobble(h, 7, 0.18, 0.8), 0, 0.35)
    # Only on the head: not on the shoulders the head is turned toward.
    cap *= soft(1.0 - np.linalg.norm((h - (0.4, 0, 0.4)) / (3.2, 3.0, 3.6), axis=1), 0, 0.12)
    # The blaze: white up the face, as wide at the eyes as the gap between them, narrowing to a point at the top of
    # the forehead, a little toward her right.
    up = np.clip((hz - eye_z + 0.1) / 2.1, 0, 1)
    half = 0.47 * (1 - up) ** 1.2
    blaze = soft(half - np.abs(hy - 0.2 * up) + wobble(h, 2, 0.04, 0.4), 0, 0.1) * soft(-0.3 - hx, 0, 0.6)
    ginger = cap * (1 - blaze)
    # Her moustache: ginger on her left upper lip, a smaller fleck on her right.
    lip_left = np.linalg.norm((h - (-2.45, -0.5, -0.88)) / (0.7, 0.42, 0.32), axis=1)
    lip_right = np.linalg.norm((h - (-2.6, 0.3, -0.72)) / (0.5, 0.17, 0.15), axis=1)
    ginger = np.maximum(ginger, face * soft(1 - lip_left + wobble(h, 3, 0.15, 0.3), 0, 0.25))
    ginger = np.maximum(ginger, face * soft(1 - lip_right, 0, 0.3))
    # The ears: ginger behind, pale pink in the cup, white round its edge and in the tufts at its foot.
    pink = np.zeros(len(p))
    for s_ in (1, -1):
        flat, w, thick, along = ear_coords(h, s_)
        on = soft(-flat + 0.05, 0, 0.1) * soft(along - 0.05, 0, 0.1)
        cup = on * soft(w, 0, 0.12)
        ginger = np.maximum(ginger, on * (1 - cup))
        ginger *= 1 - cup
        pink = np.maximum(pink, 0.75 * cup * soft(-flat - 0.3, 0, 0.25) * soft(along - 0.2, 0, 0.2))
    # The back, from above: four spots in two pairs either side of the spine, on the shoulders, measured from her
    # photograph against the width of her back. A small round pair almost touching just behind the withers, and
    # behind them a larger pair splayed outward like wings: each a petal from a point beside the spine, fanning
    # back and out over the top of the shoulder.
    top = soft(normals[:, 2] - 0.1, 0, 0.3) * soft(z - 3.5, 0, 0.5)
    for s_ in (1, -1):
        out = s_ * y
        front = np.hypot((x - 8.95) / 0.52, (out - 0.5) / 0.47)
        front = front * (1 + 0.15 * np.clip((8.95 - x) / 0.52, 0, 1))
        ginger = np.maximum(ginger, top * soft(1 - front + wobble(p, 4 + (s_ > 0), 0.1, 0.4), 0.05, 0.15))
        da, db = x - 9.6, out - 0.16
        fan = (np.arctan2(db, da) - math.radians(52 if s_ > 0 else 47)) / math.radians(44)
        reach = 2.3 * np.clip(np.cos(np.clip(fan, -1, 1) * np.pi / 2), 0, 1) ** 0.22 * (np.abs(fan) < 1)
        wing = (reach - np.hypot(da, db)) / 0.5
        ginger = np.maximum(ginger, top * soft(wing + wobble(p, 6 + (s_ > 0), 0.15, 0.4), 0.05, 0.25))
    # The tail, all of it, from its root.
    dist, s, _ = nearest_on_tail(p, 120)
    ginger = np.maximum(ginger, (dist < 2.8) * soft(s - 0.015, 0, 0.05))
    # The nose: a pink leather, broad at the top and coming to a point at the lip.
    narrow = 0.36 - 0.3 * np.clip(-(hz + 0.42) / 0.3, 0, 1)
    nose = np.linalg.norm((h - (-2.72, 0, -0.42)) / np.column_stack((np.full(len(p), 0.26), narrow, np.full(len(p), 0.24))), axis=1)
    pink = np.maximum(pink, face * soft(1 - nose, 0, 0.2))
    ginger *= 1 - face * soft(1 - nose, 0, 0.2)
    # The lids: a dark rim round each eye, where the lids part.
    dark = np.zeros(len(p))
    for eye in EYES:
        r = np.linalg.norm(h - eye[0], axis=1)
        rim = soft(EYE_R + LID + 0.04 - r, 0, 0.05) * soft(0.06 - opening(h, eye), 0, 0.07)
        dark = np.maximum(dark, rim)
    ginger *= 1 - dark
    # The nostrils, and the mouth: a short line down from the nose, parting each way under the whisker pads.
    nostril = np.minimum(*(np.linalg.norm((h - (-2.78, o, -0.5)) / (0.1, 0.07, 0.05), axis=1) for o in (0.12, -0.12)))
    dark = np.maximum(dark, 0.7 * face * soft(1 - nostril, 0, 0.4))
    face = face * soft(-1.7 - hx, 0, 0.3)
    lip = face * soft(0.05 - np.abs(hy), 0, 0.04) * soft(hz + 0.62, 0, 0.05) * soft(-0.95 - hz, 0, 0.05)
    for s_ in (1, -1):
        t = np.clip((s_ * hy) / 0.55, 0, 1)
        curve = -1.0 - 0.12 * np.sin(np.pi * t) - 0.08 * t
        lip = np.maximum(lip, face * (s_ * hy > 0) * (s_ * hy < 0.6) * soft(0.045 - np.abs(hz - curve), 0, 0.04))
    return np.column_stack((np.clip(ginger, 0, 1), np.clip(pink, 0, 1), np.clip(dark, 0, 1), np.clip(lip, 0, 1)))


def rgb(nodes, hex_):
    node = nodes.new("ShaderNodeRGB")
    node.outputs[0].default_value = (*linear(hex_), 1)
    return node.outputs[0]


def mix(nodes, links, factor, a, b):
    node = nodes.new("ShaderNodeMix")
    node.data_type = "RGBA"
    links.new(factor, node.inputs["Factor"])
    links.new(a, node.inputs["A"])
    links.new(b, node.inputs["B"])
    return node.outputs["Result"]


def math_node(nodes, links, operation, a, b=None, value=None):
    node = nodes.new("ShaderNodeMath")
    node.operation = operation
    links.new(a, node.inputs[0])
    if b is not None:
        links.new(b, node.inputs[1])
    elif value is not None:
        node.inputs[1].default_value = value
    return node.outputs[0]


def porcelain():
    """Glazed ceramic as the figurine is: a creamy white body under a thick, smooth, very glossy glaze, the ginger
    airbrushed on, deep in the middle of each patch and fading softly into the white at its edge. A little light
    goes into the ceramic and comes out warm."""
    material = bpy.data.materials.new("ceramic")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    marks = nodes.new("ShaderNodeVertexColor")
    marks.layer_name = "paint"
    split = nodes.new("ShaderNodeSeparateColor")
    links.new(marks.outputs["Color"], split.inputs[0])
    ginger = split.outputs["Red"]
    # Airbrushed: the colour builds up toward the middle of a patch, lighter where the spray thinned.
    depth = math_node(nodes, links, "POWER", ginger, value=2.5)
    paint = mix(nodes, links, depth, rgb(nodes, GINGER), rgb(nodes, DEEP))
    colour = mix(nodes, links, math_node(nodes, links, "POWER", ginger, value=0.7), rgb(nodes, WHITE), paint)
    colour = mix(nodes, links, split.outputs["Green"], colour, rgb(nodes, PINK))
    colour = mix(nodes, links, marks.outputs["Alpha"], colour, rgb(nodes, LIP))
    colour = mix(nodes, links, split.outputs["Blue"], colour, rgb(nodes, LINE))
    links.new(colour, shader.inputs["Base Color"])
    # The hair is drawn into the clay in fine strokes under the glaze: they shade the colour, not the glaze.
    coord = nodes.new("ShaderNodeTexCoord")
    along = nodes.new("ShaderNodeMapping")
    along.inputs["Scale"].default_value = (1.2, 14.0, 6.0)
    links.new(coord.outputs["Object"], along.inputs["Vector"])
    strands = nodes.new("ShaderNodeTexNoise")
    strands.inputs["Scale"].default_value = 1.0
    strands.inputs["Detail"].default_value = 6.0
    links.new(along.outputs["Vector"], strands.inputs["Vector"])
    combed = nodes.new("ShaderNodeBump")
    combed.inputs["Strength"].default_value = 0.3
    combed.inputs["Distance"].default_value = 0.05
    links.new(strands.outputs["Fac"], combed.inputs["Height"])
    links.new(combed.outputs["Normal"], shader.inputs["Normal"])
    shader.inputs["Roughness"].default_value = 0.4
    shader.inputs["Subsurface Weight"].default_value = 0.25
    shader.inputs["Subsurface Radius"].default_value = (1.0, 0.7, 0.45)
    shader.inputs["Subsurface Scale"].default_value = 0.15
    shader.inputs["Coat Weight"].default_value = 1.0
    shader.inputs["Coat IOR"].default_value = 1.52
    shader.inputs["Coat Roughness"].default_value = 0.04
    return material


def glass():
    """A glass eye, as a figurine maker sets one: the iris painted on the back of a clear dome, amber with fibres
    running out from the pupil, greener round it and ringed dark at its rim, the pupil a tall dark oval, all under
    a clear, glassy surface that holds a sharp reflection of the light."""
    material = bpy.data.materials.new("eye")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    coord = nodes.new("ShaderNodeTexCoord")
    xyz = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coord.outputs["Object"], xyz.inputs[0])
    flat = nodes.new("ShaderNodeCombineXYZ")
    links.new(xyz.outputs["X"], flat.inputs["X"])
    links.new(xyz.outputs["Y"], flat.inputs["Y"])
    length = nodes.new("ShaderNodeVectorMath")
    length.operation = "LENGTH"
    links.new(flat.outputs[0], length.inputs[0])
    out = math_node(nodes, links, "DIVIDE", length.outputs["Value"], value=EYE_R)
    # Fibres: noise round the pupil, stretched outward.
    round_ = nodes.new("ShaderNodeVectorMath")
    round_.operation = "NORMALIZE"
    links.new(flat.outputs[0], round_.inputs[0])
    spokes = nodes.new("ShaderNodeVectorMath")
    spokes.operation = "SCALE"
    spokes.inputs["Scale"].default_value = 7.0
    links.new(round_.outputs[0], spokes.inputs[0])
    fibres_at = nodes.new("ShaderNodeVectorMath")
    fibres_at.operation = "ADD"
    links.new(spokes.outputs[0], fibres_at.inputs[0])
    lift = nodes.new("ShaderNodeCombineXYZ")
    links.new(math_node(nodes, links, "MULTIPLY", out, value=2.5), lift.inputs["Z"])
    links.new(lift.outputs[0], fibres_at.inputs[1])
    fibres = nodes.new("ShaderNodeTexNoise")
    fibres.inputs["Scale"].default_value = 1.6
    fibres.inputs["Detail"].default_value = 8.0
    fibres.inputs["Roughness"].default_value = 0.65
    links.new(fibres_at.outputs[0], fibres.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    first = ramp.color_ramp.elements[0]
    first.position, first.color = IRIS[0][1], (*linear(IRIS[0][0]), 1)
    for hex_, at in IRIS[1:]:
        stop = ramp.color_ramp.elements.new(at)
        stop.color = (*linear(hex_), 1)
    links.new(out, ramp.inputs["Fac"])
    shade = math_node(nodes, links, "MULTIPLY_ADD", fibres.outputs["Fac"], value=0.9)
    shade.node.inputs[2].default_value = 0.55
    iris = nodes.new("ShaderNodeMix")
    iris.data_type = "RGBA"
    iris.blend_type = "MULTIPLY"
    iris.inputs["Factor"].default_value = 1.0
    links.new(ramp.outputs["Color"], iris.inputs["A"])
    grey = nodes.new("ShaderNodeCombineColor")
    for channel in ("Red", "Green", "Blue"):
        links.new(shade, grey.inputs[channel])
    links.new(grey.outputs[0], iris.inputs["B"])
    # The pupil, tall in the lamp's light.
    pupil = nodes.new("ShaderNodeCombineXYZ")
    links.new(math_node(nodes, links, "DIVIDE", xyz.outputs["X"], value=0.3 * EYE_R), pupil.inputs["X"])
    links.new(math_node(nodes, links, "DIVIDE", xyz.outputs["Y"], value=0.47 * EYE_R), pupil.inputs["Y"])
    pupil_r = nodes.new("ShaderNodeVectorMath")
    pupil_r.operation = "LENGTH"
    links.new(pupil.outputs[0], pupil_r.inputs[0])
    edge = nodes.new("ShaderNodeMapRange")
    edge.inputs["From Min"].default_value = 0.92
    edge.inputs["From Max"].default_value = 1.06
    links.new(pupil_r.outputs["Value"], edge.inputs["Value"])
    colour = mix(nodes, links, edge.outputs["Result"], rgb(nodes, "#060403"), iris.outputs["Result"])
    links.new(colour, shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = 0.45
    shader.inputs["Coat Weight"].default_value = 1.0
    shader.inputs["Coat IOR"].default_value = 1.5
    shader.inputs["Coat Roughness"].default_value = 0.0
    return material


def glass_eyes(stage):
    """The eyes, each a ball of glass set in its socket behind the lids, looking where the head looks."""
    material = glass()
    parts = []
    for i, (centre, gaze, across, up) in enumerate(EYES):
        ball = bmesh.new()
        bmesh.ops.create_uvsphere(ball, u_segments=64, v_segments=32, radius=EYE_R)
        data = bpy.data.meshes.new("eye")
        ball.to_mesh(data)
        ball.free()
        data.polygons.foreach_set("use_smooth", [True] * len(data.polygons))
        data.materials.append(material)
        eye = stage.add(f"eye-{'right' if i == 0 else 'left'}", data)
        # Its own z looks out of the pupil, and its y runs up the pupil.
        y_, z_ = TURNED @ up, TURNED @ gaze
        x_ = np.cross(y_, z_)
        eye.matrix_world = Matrix.Translation(SKULL + TURNED @ centre) @ Matrix(np.column_stack((x_, y_, z_)).tolist()).to_4x4()
        parts.append(eye)
    return parts


def lathed(stage, name, profile, material):
    """A solid turned about the upright through the lamp's head, from (height, radius) pairs."""
    obj = lathe(stage, name, profile, material, steps=96, axis="Z", caps=False)
    obj.data.polygons.foreach_set("use_smooth", [True] * len(obj.data.polygons))
    return obj


def shade(stage):
    """The lamp's head, after the arched floor lamp's: a dome of spun steel enamelled a glossy orange, gilded
    inside, on a short brass neck from the tail's tip, with a frosted bulb up inside it. Its light falls out of
    the open bottom onto the cat and the desk; the dome holds back all that goes up."""
    x, y, tip = HEAD
    rim = tip - NECK - SHADE_R
    orange = bpy.data.materials.new("enamel")
    orange.use_nodes = True
    o = orange.node_tree.nodes["Principled BSDF"]
    o.inputs["Base Color"].default_value = (*linear(ENAMEL), 1)
    o.inputs["Roughness"].default_value = 0.3
    o.inputs["Coat Weight"].default_value = 1.0
    o.inputs["Coat Roughness"].default_value = 0.03
    gold = bpy.data.materials.new("gilt")
    gold.use_nodes = True
    g = gold.node_tree.nodes["Principled BSDF"]
    g.inputs["Base Color"].default_value = (1.0, 0.78, 0.38, 1)
    g.inputs["Metallic"].default_value = 1.0
    g.inputs["Roughness"].default_value = 0.3
    brass = bpy.data.materials.new("brass")
    brass.use_nodes = True
    b = brass.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.86, 0.64, 0.3, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.22
    frosted = bpy.data.materials.new("frosted")
    frosted.use_nodes = True
    f = frosted.node_tree.nodes["Principled BSDF"]
    f.inputs["Base Color"].default_value = (1, 1, 1, 1)
    f.inputs["Transmission Weight"].default_value = 1.0
    f.inputs["Roughness"].default_value = 0.6
    t = SHADE_T
    arc = np.linspace(0, math.pi / 2, 40)
    outer = [(rim + SHADE_R * math.sin(a), SHADE_R * math.cos(a)) for a in arc[::-1]]
    inner = [(rim + (SHADE_R - t) * math.sin(a), (SHADE_R - t) * math.cos(a)) for a in arc]
    parts = [
        # The enamelled dome: its outside down to the rim, and the rim's edge.
        lathed(stage, "shade", [(rim + SHADE_R, 0.0)] + outer[1:] + [(rim, SHADE_R - t)] + [(rim + 0.001, SHADE_R - t)], orange),
        # The gilded inside.
        lathed(stage, "shade-inside", [(rim + 0.001, SHADE_R - t)] + inner[1:-1] + [(rim + SHADE_R - t, 0.0)], gold),
        # The neck: a collar on the dome, a knurled nut and a short stem up into the tail.
        lathed(stage, "neck", [(rim + SHADE_R - 0.05, 0.0), (rim + SHADE_R - 0.05, 0.55), (rim + SHADE_R + 0.15, 0.55), (rim + SHADE_R + 0.2, 0.36), (rim + SHADE_R + 0.45, 0.36), (rim + SHADE_R + 0.5, 0.42), (rim + SHADE_R + 0.7, 0.42), (rim + SHADE_R + 0.75, 0.24), (tip + 0.4, 0.24), (tip + 0.4, 0.0)], brass),
    ]
    bulb = bmesh.new()
    bmesh.ops.create_uvsphere(bulb, u_segments=48, v_segments=24, radius=BULB_R)
    data = bpy.data.meshes.new("bulb")
    bulb.to_mesh(data)
    bulb.free()
    data.polygons.foreach_set("use_smooth", [True] * len(data.polygons))
    data.materials.append(frosted)
    glass = stage.add("bulb-glass", data)
    glass.location = (x, y, rim + 0.25 * SHADE_R)
    # The bulb's own light is the lamp's; its glass lets it out.
    glass.visible_shadow = False
    parts.append(glass)
    source = bpy.data.lights.new("bulb", "POINT")
    source.color = BULB_COLOUR
    source.energy = 0.0
    source.shadow_soft_size = BULB_R * 0.8
    light = stage.add("bulb", source)
    light.location = (x, y, rim + 0.25 * SHADE_R)
    light["bulb"] = True
    parts.append(light)
    for part in parts[:3]:
        part.location = (x, y, 0)
    return parts


def build(stage):
    ox, oy = ORIGIN
    lo, hi = (-2.4, -10.2, -0.2), (25.5, 5.8, 22.8)
    cat, verts = mesh(stage, "cat", body, lo, hi, STEP, porcelain())
    normals = np.zeros_like(verts)
    for e, column in zip(np.eye(3) * 0.01, range(3)):
        normals[:, column] = body(verts + e) - body(verts - e)
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-9)
    layer = cat.data.color_attributes.new("paint", "FLOAT_COLOR", "POINT")
    layer.data.foreach_set("color", painted(verts, normals).ravel())
    for part in [cat] + glass_eyes(stage) + shade(stage):
        part.location = (part.location.x + ox, part.location.y - oy, part.location.z)
    stage.shoot("catlamp", (0, 0, W, H), lens=False)


SHOTS = {"catlamp": build}
