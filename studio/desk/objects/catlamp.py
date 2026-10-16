"""The desk lamp: a glazed porcelain cat figurine, stretched in a play bow, its tail rising from the rump and arching
forward over its back. From the tail's tip a short black cord goes into a white ceramic socket, and from the socket
hangs a frosted globe bulb, lighting the cat and the desk below.

It is a copy of one ceramic cat lamp, from its photograph (art/catlamp-photo.jpg): a smooth, plump ginger tabby and
white cat with a big round head, small ears, short thick legs and round paws, its face painted on, the eyes closed
arches, a small pink nose, a mouth and whiskers in fine brown lines, under a thick glossy glaze.

The body is one smooth solid, modelled as a signed distance field (sdf.py): the head in its own turned frame, the
chest and back, the legs and paws, and the tail along a curve, blended into each other as a figurine is modelled
in clay, and cut flat underneath where it stands. That shape is then fitted to the photograph's outline as its
camera saw it (art/fit.py), and painted with the photograph wherever the photograph sees it; elsewhere with
colours laid on the vertices after it.

Built in its own coordinates, in em: the head toward -x, her right toward +y, the tail toward +x, standing on z = 0.
The lamp is the light marked "bulb", at no power until desk.py turns it up."""

import functools
import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from paint import linear
from sdf import cone, ellipsoid, mesh, smax, smin
from solids import lathe

ART = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "art")
# The figurine's photograph, cut out, with the light it was taken in and its highlights taken out so only its paint is
# left (studio/desk/art/delight.py), its colours carried a little past its outline, and the camera it was taken
# with, solved from it, in the cat's own coordinates: where the camera stands, its axes and its lens in mm.
REFERENCE = os.path.join(ART, "catlamp-reference.png")
REFERENCE_CAMERA = os.path.join(ART, "catlamp-camera.json")
ROWS, COLS = 1104, 736
# Her middle, and the point on the desk under it, in her own coordinates: the desk's portrait of her is drawn as
# large as the desk round her middle, and set on the desk where she stands.
MIDDLE = (6.0, 0.0, 6.0)
STANDS = (6.0, 0.0, 0.0)
# How the photographed outline corrects the modelled shape (art/fit.py): for each pixel of the photograph, how far
# across and down the modelled shape is moved there, how far outside the figurine's outline it lies, and how far the
# moved shape still falls short of the outline round it.
FIT = os.path.join(ART, "catlamp-fit.npz")
# How hard the shape is drawn in where it goes past the outline, and how many pixels past it may still stand.
SHRINK, CUT = 2.5, 2.0

# The box the cat stands in, in em, and where the cat's own origin lies in it.
W, H = 27.0, 16.5
ORIGIN = (2.6, 5.5)
STEP = 0.06

# The porcelain, and the underglaze colours: her ginger, light and deep, the pink of her nose and the insides of her
# ears, the near-black of her closed eyes, and the brown of her mouth and whiskers.
WHITE = "#f6ebda"
GINGER = "#eaa034"
DEEP = "#c27414"
PINK = "#e9a3a0"
LINE = "#26170f"
LIP = "#8a4a32"
# The lamp: the same warm bulb as the pendant it replaces.
# The tabby's dark brown stripes, brushed over the ginger.
STRIPE = "#6f3712"
# The lamp: a warm bulb, a round frosted globe in a white ceramic socket, on a short black cord from the tail's tip.
BULB_COLOUR = (1.0, 0.74, 0.46)
BULB_R = 1.2
GLOBE_R = 2.35
SOCKET = "#e8dcc8"
# Which way the socket hangs from the cord, down and forward, toward her head and a little toward her left, and where
# the cord goes into it from the tail's tip: both solved from where the photograph shows the socket's two ends and the
# globe's middle, and the globe's size.
HANG = (-0.448, 0.27, -0.853)
CORD = (-1.18, 1.45, -1.14)

# The tail rises straight up from the top of the rump and hooks forward at the top, over her back, where the lamp
# hangs from it. It tapers a little from its root.
TAIL = ((14.3, 0.0, 12.0), (20.7, 0.0, 18.0), (19.3, 0.0, 26.4), (13.6, 0.0, 25.2))
# Her left foreleg, the near one, from its shoulder to its paw, measured out on her left: reaching further forward
# than her right.
NEAR_FORE = ((6.0, 1.75, 2.4), (-3.2, 6.0, 0.8))
# How far each hind foot, her right then her left (measured out on her left), stands from under its thigh: her left
# a little forward and in, as the photograph shows it.
HIND = ((0.0, 0.0, 0.0), (-0.35, -0.3, 0.0))
# Her right foreleg, the far one, as the photograph shows it: from its shoulder, raised, forward and in to its paw,
# toward the camera, tapering from this thick to this thick.
FAR_FORE = ((6.0, 1.75, 2.9), (-4.5, -0.5, 0.7), (1.15, 0.8))
TAIL_R = (1.3, 0.72)
HEAD = TAIL[-1]

# Her head: the middle of it, and how it is held: turned this many degrees to her right, lifted a little, and
# cocked, as the figurine's is.
SKULL = np.array([2.85, 0.0, 4.85])
TURN, LIFT, COCK = -16.0, 10.0, 1.0
# The head is modelled at this size and made this much bigger: as wide as her rump.
GROW = 1.1
# The round of the skull, in the head's frame: its middle and its radii, low between the ears as the photograph shows.
DOME = ((-0.2, 0.1, 0.35), (2.4, 2.7, 2.5))
# The tips of her ears in the head's frame: her right, the far one, tall and leaning out, then her left.
EARS = ((-1.05, 2.4, 3.95), (-0.85, -2.4, 3.0))
# How broad each ear is at its foot, either way from its middle.
EAR_HALF = 0.72


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
    return (p - SKULL) @ TURNED / GROW


@functools.cache
def photograph():
    """The camera the figurine was photographed with: where it stands, its axes, and its lens in pixels."""
    with open(REFERENCE_CAMERA) as file:
        solved = json.load(file)
    return np.asarray(solved["C"]), np.asarray(solved["R"]), solved["f"] / 36 * ROWS


def in_photograph(p):
    """Where points in the cat's own coordinates are in the photograph, in pixels across and down, and how far they
    are from its camera."""
    centre, axes, focal = photograph()
    seen = (p - centre) @ axes.T
    depth = -seen[..., 2]
    return COLS / 2 + focal * seen[..., 0] / depth, ROWS / 2 - focal * seen[..., 1] / depth, depth


@functools.cache
def fit():
    if not FIT or not os.path.exists(FIT):
        return {}
    with np.load(FIT) as fields:
        return {name: fields[name] for name in fields.files}


def at(field, x, y):
    """A field over the photograph's pixels, read between them, its edge carried on past the frame."""
    x = np.clip(x - 0.5, 0, COLS - 1.001)
    y = np.clip(y - 0.5, 0, ROWS - 1.001)
    i, j = np.floor(y).astype(int), np.floor(x).astype(int)
    a, b = y - i, x - j
    return (field[i, j] * (1 - a) + field[i + 1, j] * a) * (1 - b) + (field[i, j + 1] * (1 - a) + field[i + 1, j + 1] * a) * b


def framed(x, y):
    """How far within the photograph's frame each point is seen: 1 inside it, fading to 0 a little way past its edge,
    where the photograph says nothing of the shape."""
    past = np.maximum(np.maximum(-x, x - COLS), np.maximum(-y, y - ROWS))
    return np.clip(1 - past / 24, 0, 1)


def warped(p):
    """Where the modelled shape is read for each point: moved across the photograph's view, as far as carries the
    modelled outline onto the photographed one there. The move up and down fades out toward the desk, so her feet
    stay standing on it."""
    fields = fit()
    if "across" not in fields:
        return p
    x, y, depth = in_photograph(p)
    _, axes, focal = photograph()
    size = (depth / focal)[..., None]
    inside = framed(x, y)[..., None]
    across = at(fields["across"], x, y)[..., None] * inside
    down = at(fields["down"], x, y)[..., None] * soft(p[..., 2:3], 2.0, 2.0) * inside
    return p + size * (across * axes[0] - down * axes[1])


def fitted(p, d):
    """The moved shape made to fill the photographed outline and go no further than it: grown where it falls short,
    and drawn in where it goes past, by an amount that runs smoothly over the surface, so it keeps its rounded form
    seen from anywhere else. Only what still stands a few pixels past the outline is cut off by it."""
    fields = fit()
    if "grow" not in fields:
        return d
    outside, grow = fields["outside"], fields["grow"]
    x, y, depth = in_photograph(p)
    size = depth / photograph()[2]
    past = at(outside, x, y)
    inside = framed(x, y)
    d = d - (at(grow, x, y) - SHRINK * np.maximum(past, 0)) * inside * size
    return np.maximum(d, (past - CUT) * size - (1 - inside) * 100)


def unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def sphere(p, centre, r):
    return np.linalg.norm(p - np.asarray(centre), axis=-1) - r


def both(p, part):
    """A part the cat has on both sides, given for her right one (+y)."""
    return np.minimum(part(p), part(p * np.array([1, -1, 1])))


def soft(x, edge, width):
    t = np.clip((x - edge) / width + 0.5, 0, 1)
    return t * t * (3 - 2 * t)


def waves(p, size, seed, count=5):
    """A slow irregular wander, about -1 to 1."""
    rng = np.random.default_rng(seed)
    out = np.zeros(p.shape[:-1])
    for _ in range(count):
        k = rng.normal(size=3)
        k = k / np.linalg.norm(k) / size * rng.uniform(0.7, 1.3)
        out += np.sin(p @ k + rng.uniform(0, 6.3))
    return out / math.sqrt(count)


def ear_frame(side):
    """An ear's base, its length up to the tip, and its axes: across the base, up to the tip, and out of its cup."""
    base = np.array([-0.7, side * 1.95, 2.0])
    tip = np.asarray(EARS[0] if side > 0 else EARS[1])
    up = unit(tip - base)
    # Her far ear turns its hollow toward the camera, as the photograph shows its pink inside.
    front = unit((-1.0, -side * 0.15, 0.2)) if side < 0 else unit((-0.75, -0.65, 0.15))
    front = unit(front - (front @ up) * up)
    return base, np.linalg.norm(tip - base), np.cross(up, front), up, front


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
    """Where a point is against an ear: inside its outline or not, how far in front of the middle of its shell, how
    thick the shell is there, and how far up the ear."""
    base, length, across, up, front = ear_frame(side)
    q = h - base
    u, v, w = q @ across, q @ up, q @ front
    # A rounded triangle, broad at the foot.
    half = EAR_HALF
    flat = triangle(u, v, ((-half, -0.7), (half, -0.7), (0.0, length - 0.5))) - (0.42 if side < 0 else 0.34)
    along = np.clip(v / length, 0, 1)
    middle = 0.25 * (u / 1.0) ** 2
    return flat, w - middle, 0.45 + 0.4 * (1 - along) ** 2, along


def ear(h, side):
    flat, w, thick, _ = ear_coords(h, side)
    shell = smax(flat, np.abs(w + 0.05) - thick, 0.12)
    # The hollow in front, shallow, as a figurine's is.
    hollow = smax(flat + 0.28, -(w - 0.02), 0.08)
    return smax(shell, -hollow, 0.08)


def head(h):
    """The head in its own frame, looking along -x: big, round and broad, with full cheeks, a small round muzzle and
    chin, and small rounded ears set wide."""
    d = ellipsoid(h, DOME[0], DOME[1])
    d = smin(d, both(h, lambda q: ellipsoid(q, (-0.8, 1.5, -0.75), (1.6, 1.6, 1.35))), 0.9)
    d = smin(d, ellipsoid(h, (-1.75, 0, -0.55), (0.6, 1.0, 0.6)), 0.6)
    d = smin(d, ellipsoid(h, (-1.5, 0, -0.95), (0.55, 0.7, 0.4)), 0.5)
    d = smin(d, sphere(h, (-2.32, 0, -0.48), 0.2), 0.25)
    return smin(d, np.minimum(ear(h, 1), ear(h, -1)), 0.25)


def paw(q, centre, radii):
    """A round paw, its toes parted by two shallow grooves across its front."""
    x0, y0, z0 = centre
    body = ellipsoid(q, centre, radii)
    for o in (-0.33, 0.33):
        groove = np.maximum(np.abs(q[..., 1] - y0 - o * radii[1] / 1.0) - 0.06, x0 - 0.35 - q[..., 0])
        body = smax(body, -np.maximum(groove, 0.2 - q[..., 2]), 0.06)
    return body


def torso(p):
    """The chest low between the forelegs stretched flat in front, the back rising to a high round rump on short
    standing hind legs."""
    d = ellipsoid(p, (5.0, 0, 3.3), (3.0, 2.85, 2.9))
    d = smin(d, cone(p, (5.5, 0, 4.5), (13.0, 0, 7.8), 3.0, 3.4), 1.6)
    d = smin(d, ellipsoid(p, (14.8, 0, 9.0), (3.4, 2.95, 3.9)), 1.6)
    d = smin(d, ellipsoid(p, (16.4, 0, 6.6), (2.3, 2.5, 2.8)), 1.2)
    # The back rises steeply from behind the shoulders and stays high to the rump, as the figurine's does: its crest
    # runs through these heights, measured from the photograph.
    crest = ((6.8, 0, 4.2), (8.2, 0, 5.8), (9.8, 0, 8.4), (11.6, 0, 9.75), (13.8, 0, 10.9))
    for a_, b_ in zip(crest, crest[1:]):
        d = smin(d, cone(p, a_, b_, 2.7, 2.7), 1.2)
    d = smin(d, ellipsoid(p, (9.8, 0, 4.4), (4.2, 2.6, 2.3)), 1.5)
    d = smin(d, cone(p, SKULL + GROW * TURNED @ np.array([1.0, 0, -0.6]), (4.6, 0, 3.4), 2.1, 2.5), 1.0)

    def fore(q, shoulder, at, radii=(1.15, 0.95)):
        """A foreleg on her right (+y), from the shoulder to its paw, this thick at either end."""
        leg = cone(q, shoulder, np.asarray(at) + (0.4, -0.1, 0.05), *radii)
        return smin(leg, paw(q, at, (1.55, 1.2, 0.8)), 0.7)

    def hind(q, moved):
        """A hind leg on her right (+y), its foot moved this far from under the thigh."""
        moved = np.asarray(moved)
        thigh = ellipsoid(q, (14.8, 1.9, 6.4), (2.8, 1.45, 3.4))
        leg = cone(q, (15.0, 2.3, 6.0), np.array((14.9, 2.35, 0.9)) + moved, 1.55, 1.2)
        return smin(smin(thigh, leg, 1.6), paw(q, np.array((14.4, 2.35, 0.78)) + moved, (1.5, 1.2, 0.78)), 0.6)

    # She stretches them unevenly: her left paw, nearer the camera, reaches further out than her right.
    mirrored = p * np.array([1, -1, 1])
    d = smin(d, np.minimum(fore(p, *FAR_FORE), fore(mirrored, *NEAR_FORE)), 0.9)
    return smin(d, np.minimum(hind(p, HIND[0]), hind(mirrored, HIND[1])), 0.9)


def tail_curve(samples=60):
    p0, p1, p2, p3 = (np.asarray(c, dtype=float) for c in TAIL)
    t = np.linspace(0, 1, samples)[:, None]
    points = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t**2 * p2 + t**3 * p3
    along = np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))))
    return points, along


def nearest_on_tail(p, samples=60):
    """For each point, its distance from the tail's line and how far along the tail it is, 0 to 1."""
    points, along = tail_curve(samples)
    best = np.full(len(p), np.inf)
    s = np.zeros(len(p))
    for i in range(len(points) - 1):
        a, ab = points[i], points[i + 1] - points[i]
        t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
        dist = np.linalg.norm(p - a - t[:, None] * ab, axis=1)
        closer = dist < best
        best = np.where(closer, dist, best)
        s = np.where(closer, (along[i] + t * (along[i + 1] - along[i])) / along[-1], s)
    return best, s


def tail(p):
    points, _ = tail_curve()
    lo, hi = points.min(axis=0) - 2, points.max(axis=0) + 2
    near = np.all((p > lo) & (p < hi), axis=-1)
    d = np.full(p.shape[:-1], 1e3)
    dist, s = nearest_on_tail(p[near])
    d[near] = dist - (TAIL_R[0] + (TAIL_R[1] - TAIL_R[0]) * s**1.7)
    return d


def body(p):
    """The porcelain: the cat, without the lamp, fitted to the photograph."""
    q = warped(p)
    d = smin(torso(q), GROW * head(in_head(q)), 0.9)
    d = fitted(p, smin(d, tail(q), 1.0))
    # It stands on a flat foot.
    return np.maximum(d, -p[..., 2])


def line(distance, width):
    """A brushed line: how much of it covers a point this far from its middle."""
    return soft(width - np.abs(distance), 0, 0.03)


def stroke(u, v, a, b, width):
    """A brushed line from a to b in a plane, tapering at its ends: how much of it covers each point."""
    (ax, ay), (bx, by) = a, b
    ex, ey = bx - ax, by - ay
    t = np.clip(((u - ax) * ex + (v - ay) * ey) / (ex * ex + ey * ey), 0, 1)
    d = np.hypot(u - ax - ex * t, v - ay - ey * t)
    return soft(width * np.sqrt(np.clip(1 - (2 * t - 1) ** 2, 0, 1)) + 0.01 - d, 0, 0.03)


def painted(verts, normals):
    """Where each colour goes, as the figurine is painted: a ginger tabby and white. How much ginger, pink, near-black,
    brown line and dark stripe. The colours are laid in the shader."""
    p = verts
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    h = in_head(p)
    n = normals @ TURNED
    hx, hy, hz = h[:, 0], h[:, 1], h[:, 2]
    side = np.abs(hy)
    on_head = soft(1.0 - np.linalg.norm(h / (2.8, 3.1, 3.6), axis=1), 0, 0.1)
    face = soft(-n[:, 0] - 0.15, 0, 0.3) * soft(-0.8 - hx, 0, 0.4)
    stripe = np.zeros(len(p))
    # The head: ginger over the top and back and down the outer cheeks; a white blaze up the middle of the forehead,
    # and the muzzle, chin and inner cheeks white.
    edge = 0.32 - 0.15 * soft(side - 1.3, 0, 0.8) - 0.9 * soft(hx - 0.8, 0, 1.4) + 0.06 * waves(h, 0.5, 1)
    cap = soft(hz - edge, 0, 0.2) * soft(1.2 - hx + 0.15 * waves(h, 0.7, 7), 0, 0.35) * soft(1.0 - np.linalg.norm(h / (2.45, 2.75, 3.6), axis=1), 0, 0.08)
    up = np.clip((hz - 0.25) / 1.4, 0, 1)
    blaze = soft(0.55 * (1 - up) ** 1.5 - np.abs(hy - 0.05), 0, 0.1) * soft(-0.4 - hx, 0, 0.5)
    tight = soft(1.0 - np.linalg.norm(h / (2.35, 2.75, 2.9), axis=1), 0, 0.06)
    cheek = soft(side - 1.55 + 0.12 * waves(h, 0.4, 2), 0, 0.25) * soft(0.4 - hz, 0, 0.2) * soft(hz + 1.15, 0, 0.3) * soft(0.3 - hx, 0, 0.3) * tight
    ginger = np.maximum(cap * (1 - blaze), cheek)
    # Its stripes: lines up the forehead either side of the blaze and back over the crown, and two across each cheek.
    for c in (0.42, 0.75, 1.1, 1.45, -0.42, -0.75, -1.1, -1.45):
        bend = 0.2 * np.sign(c) * np.clip(hz - 0.5, 0, None)
        stripe = np.maximum(stripe, 0.85 * cap * soft(hz - 0.55, 0, 0.15) * soft(0.065 - np.abs(hy - c - bend + 0.04 * waves(h, 0.3, 30)), 0, 0.05))
    for z0 in (-0.1, -0.55):
        for s_ in (1, -1):
            stripe = np.maximum(stripe, cheek * stroke(s_ * hy, hz, (1.7, z0 + 0.1), (2.6, z0 - 0.15), 0.09))
    # The ears: ginger behind, pale pink in the hollow, and a dark brown rim.
    pink = np.zeros(len(p))
    for s_ in (1, -1):
        flat, w, thick, along = ear_coords(h, s_)
        on = soft(0.08 - flat, 0, 0.1) * soft(along - 0.02, 0, 0.1) * soft(thick + 0.25 - np.abs(w), 0, 0.1)
        hollow = on * soft(w - 0.0, 0, 0.1) * soft(-flat - 0.22, 0, 0.12)
        ginger = np.maximum(ginger, on * (1 - hollow))
        ginger *= 1 - hollow
        pink = np.maximum(pink, 0.85 * hollow)
        dark_rim = on * soft(0.14 - np.abs(flat + 0.12), 0, 0.05) * soft(along - 0.08, 0, 0.1)
        stripe = np.maximum(stripe, dark_rim)
    # The body, as the figurine's is painted: two big ginger patches over the back, one on the shoulders and one from
    # the middle of the back to the root of the tail, parted by white across the back, each brushed down the flank to
    # past halfway and crossed by two or three broad dark strokes that run down it; a round ginger spot on the back of
    # each haunch; the chest, belly and legs white.
    middle = np.interp(x, (5.5, 13.0, 15.0, 16.8), (3.9, 7.6, 9.4, 11.4))
    dist, s = nearest_on_tail(p, 120)
    on_tail = (dist < 2.1) * soft(s - 0.02, 0, 0.05)
    body_part = (1 - on_head) * (1 - on_tail)
    lean = x + 0.35 * (middle + 3.2 - z) + 0.22 * waves(p, 0.6, 42)
    shoulder = soft(lean - 5.9, 0, 0.5) * soft(8.9 - lean + 0.25 * waves(p, 0.6, 45), 0, 0.5) * soft(z - middle + 1.3 + 0.3 * waves(p, 0.8, 40), 0, 0.4)
    back = soft(lean - 10.3 + 0.25 * waves(p, 0.6, 46), 0, 0.5) * soft(z - np.interp(x, (9.0, 14.5, 16.4), (4.8, 8.6, 11.8)) + 0.3 * waves(p, 0.8, 41), 0, 0.45)
    patches = np.maximum(shoulder, back) * body_part * (z < 13.0)
    ginger = np.maximum(ginger, patches)
    # Each stroke is broad over the back and tapers as it runs down the flank, darkest along its middle.
    down = np.clip((middle + 3.2 - z) / 4.0, 0, 1)
    for c, width in ((6.6, 0.4), (7.8, 0.45), (11.4, 0.55), (13.1, 0.55), (14.9, 0.45)):
        reach = width * (1 - 0.5 * down)
        stripe = np.maximum(stripe, patches * soft(reach - np.abs(lean - c + 0.1 * waves(p, 0.5, 50)), 0, 0.3))
    for s_ in (1, -1):
        haunch = np.linalg.norm((p - (14.85, s_ * 3.95, 5.1)) / (0.85, 0.9, 1.25), axis=1)
        ginger = np.maximum(ginger, 0.85 * soft(1 - haunch + 0.15 * waves(p, 0.4, 43), 0, 0.35) * body_part)
    # The forelegs: a ginger band part way along each, with dark strokes across it.
    for s_ in (1, -1):
        out = s_ * y
        leg = (out > 1.2) * (out < 5.6) * (z < 2.3) * soft(z - 0.85 + 0.15 * waves(p, 0.4, 47), 0, 0.3)
        wash = leg * soft(x + 1.2 + 0.2 * waves(p, 0.4, 48), 0, 0.5) * soft(1.3 - x + 0.2 * waves(p, 0.4, 49), 0, 0.5)
        ginger = np.maximum(ginger, wash)
        across = x + 0.3 * (out - 2.8)
        for c in (-0.6, 0.1, 0.8):
            stripe = np.maximum(stripe, 0.9 * wash * soft(0.16 - np.abs(across - c + 0.06 * waves(p, 0.3, 44)), 0, 0.12))
    # The tail: ginger at the root, then cream and ginger in turn, each ginger band dark in its middle, and cream at
    # the tip.
    ring = np.zeros(len(p))
    core = np.zeros(len(p))
    for a, b in ((0.0, 0.2), (0.235, 0.38), (0.43, 0.61), (0.645, 0.76), (0.81, 0.92)):
        ring = np.maximum(ring, soft(s - a, 0, 0.03) * soft(b - s, 0, 0.03))
        core = np.maximum(core, soft(0.24 * (b - a) - np.abs(s - (a + b) / 2 - 0.03 + 0.015 * waves(p, 0.3, 51)), 0, 0.03))
    ginger = np.maximum(ginger, (0.3 * (s < 0.94) + 0.7 * ring) * on_tail)
    stripe = np.maximum(stripe, 0.9 * core * on_tail * (s > 0.15))
    # The face, painted on the front of the head, read across it (hy) and up it (hz).
    narrow = np.clip((hz + 0.64) / 0.32, 0, 1)
    nose = np.maximum(np.abs(hy) / (0.05 + 0.27 * narrow), np.abs(hz + 0.47) / 0.18)
    nose_at = face * soft(1 - nose, 0, 0.25)
    pink = np.maximum(pink, nose_at)
    ginger *= 1 - nose_at
    # The eyes, closed and content: two arches, thickest in the middle.
    dark = np.zeros(len(p))
    for s_ in (1, -1):
        t = (hy - s_ * 1.2) / 0.62
        arch = -0.08 + 0.24 * (1 - t**2)
        dark = np.maximum(dark, face * (np.abs(t) < 1) * line(hz - arch, 0.035 + 0.06 * np.sqrt(np.clip(1 - t**2, 0, 1))))
    # The mouth: a short line down from the nose, parting each way in a smile.
    lip = face * (np.abs(hy) < 0.045) * soft(hz + 0.68, 0, 0.03) * soft(-0.88 - hz, 0, 0.03)
    for s_ in (1, -1):
        t = np.clip(s_ * hy / 0.62, 0, 1)
        smile = -0.86 - 0.2 * np.sin(np.pi * t) + 0.14 * t
        lip = np.maximum(lip, face * (s_ * hy > 0) * (s_ * hy < 0.64) * line(hz - smile, 0.042))
    # The whiskers: three fine lines a side, fanning out over the cheeks.
    cheeks = soft(-n[:, 0] + 0.35, 0, 0.3) * soft(-0.3 - hx, 0, 0.4)
    for s_ in (1, -1):
        out = s_ * hy
        for z0, slope in ((-0.6, 0.18), (-0.72, 0.0), (-0.84, -0.18)):
            along = np.clip((out - 0.8) / 1.8, 0, 1)
            fade = (out > 0.8) * (out < 2.6) * (1 - along) ** 0.4
            lip = np.maximum(lip, cheeks * fade * line(hz - (z0 + slope * (out - 0.8)), 0.024))
    # The toes: two short brown lines down the front of each paw, as the figurine's are drawn.
    # Each paw's middle, measured out on its own side (her right is +y), and its size.
    paws = ((FAR_FORE[1], 1, (1.55, 1.2)), (NEAR_FORE[1], -1, (1.55, 1.2)), (np.add((14.4, 2.35, 0.78), HIND[0]), 1, (1.5, 1.2)), (np.add((14.4, 2.35, 0.78), HIND[1]), -1, (1.5, 1.2)))
    for (px, py, pz), s_, (rx, ry) in paws:
        for o in (-0.33, 0.33):
            toe = soft(0.035 - np.abs(s_ * y - py - o * ry), 0, 0.02) * soft(px - 0.45 * rx - x, 0, 0.1) * soft(z - 0.12, 0, 0.06) * soft(pz + 0.45 - z, 0, 0.1) * (np.abs(x - px) < rx + 0.2)
            lip = np.maximum(lip, toe)
    ginger *= 1 - np.maximum(dark, lip)
    stripe *= 1 - np.maximum(dark, lip)
    return np.column_stack((np.clip(ginger, 0, 1), np.clip(pink, 0, 1), np.clip(dark, 0, 1), np.clip(lip, 0, 1))), np.clip(stripe, 0, 1)


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
    airbrushed on, deep in the middle of each patch and fading softly into the white at its edge, the face drawn on
    in fine lines. A little light goes into the ceramic and comes out warm."""
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
    # Brushed on: the strokes run along the body and break up the edge of each patch.
    coord = nodes.new("ShaderNodeTexCoord")
    stretch = nodes.new("ShaderNodeMapping")
    stretch.inputs["Scale"].default_value = (1.2, 2.2, 2.2)
    links.new(coord.outputs["Object"], stretch.inputs["Vector"])
    strokes = nodes.new("ShaderNodeTexNoise")
    strokes.inputs["Scale"].default_value = 1.6
    strokes.inputs["Detail"].default_value = 4.0
    links.new(stretch.outputs["Vector"], strokes.inputs["Vector"])
    brush = math_node(nodes, links, "MULTIPLY_ADD", strokes.outputs["Fac"], value=0.3)
    brush.node.inputs[2].default_value = 0.95
    ginger = math_node(nodes, links, "MINIMUM", math_node(nodes, links, "MULTIPLY", ginger, brush), value=1.0)
    streak = math_node(nodes, links, "MULTIPLY_ADD", strokes.outputs["Fac"], value=0.6)
    streak.node.inputs[2].default_value = 0.2
    depth = math_node(nodes, links, "MULTIPLY", math_node(nodes, links, "POWER", ginger, value=2.0), streak)
    paint = mix(nodes, links, depth, rgb(nodes, GINGER), rgb(nodes, DEEP))
    colour = mix(nodes, links, math_node(nodes, links, "POWER", ginger, value=0.7), rgb(nodes, WHITE), paint)
    stripes = nodes.new("ShaderNodeVertexColor")
    stripes.layer_name = "stripes"
    split2 = nodes.new("ShaderNodeSeparateColor")
    links.new(stripes.outputs["Color"], split2.inputs[0])
    stripe = math_node(nodes, links, "MINIMUM", math_node(nodes, links, "MULTIPLY", split2.outputs["Red"], brush), value=1.0)
    colour = mix(nodes, links, stripe, colour, rgb(nodes, STRIPE))
    colour = mix(nodes, links, split.outputs["Green"], colour, rgb(nodes, PINK))
    colour = mix(nodes, links, marks.outputs["Alpha"], colour, rgb(nodes, LIP))
    colour = mix(nodes, links, split.outputs["Blue"], colour, rgb(nodes, LINE))
    links.new(colour, shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = 0.35
    shader.inputs["Subsurface Weight"].default_value = 0.08
    shader.inputs["Subsurface Radius"].default_value = (1.0, 0.85, 0.7)
    shader.inputs["Subsurface Scale"].default_value = 0.15
    shader.inputs["Coat Weight"].default_value = 1.0
    shader.inputs["Coat IOR"].default_value = 1.52
    shader.inputs["Coat Roughness"].default_value = 0.1
    return material


def lathed(stage, name, profile, material):
    """A solid turned about the upright through the lamp's head, from (height, radius) pairs."""
    obj = lathe(stage, name, profile, material, steps=96, axis="Z", caps=False)
    obj.data.polygons.foreach_set("use_smooth", [True] * len(obj.data.polygons))
    return obj


def turned_to(axis):
    """The turn that lays an object's own x along axis."""
    from mathutils import Vector

    return Vector((1, 0, 0)).rotation_difference(Vector(axis))


def turned_solid(stage, name, profile, material):
    """A solid turned about its own x, from (distance along, radius) pairs."""
    obj = lathe(stage, name, profile, material, steps=96, axis="X", caps=False)
    obj.data.polygons.foreach_set("use_smooth", [True] * len(obj.data.polygons))
    obj.rotation_mode = "QUATERNION"
    return obj


def glazed(name, hex_, roughness, coat=1.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*linear(hex_), 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Coat Weight"].default_value = coat
    shader.inputs["Coat Roughness"].default_value = 0.03
    return material


def lamp(stage):
    """The lamp, as the figurine's: from the tail's tip a short black cord bends down into a white ceramic socket, and
    from the socket hangs a round frosted globe, the bulb lit inside it, forward and down over her back."""
    tip = np.asarray(HEAD)
    hang = unit(HANG)
    top = tip + np.asarray(CORD)
    length = 3.66
    bottom = top + hang * length
    centre = bottom + hang * 2.9
    rubber = glazed("cord", "#0b0a09", 0.45, 0.2)
    ceramic = glazed("socket", SOCKET, 0.3)
    frosted = bpy.data.materials.new("frosted")
    frosted.use_nodes = True
    f = frosted.node_tree.nodes["Principled BSDF"]
    f.inputs["Base Color"].default_value = (1, 1, 1, 1)
    f.inputs["Transmission Weight"].default_value = 1.0
    f.inputs["Roughness"].default_value = 0.55
    # The glass glows when the lamp is on: desk.py turns this up with the bulb.
    f.inputs["Emission Color"].default_value = (*BULB_COLOUR, 1)
    f.inputs["Emission Strength"].default_value = 0.0
    parts = []
    # The cord: out of the tip along the tail, bending down into the top of the socket.
    curve = bpy.data.curves.new("cord", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.3
    curve.bevel_resolution = 6
    curve.resolution_u = 24
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(1)
    ahead = unit(tip - np.asarray(TAIL[2]))
    for point, at, out in ((spline.bezier_points[0], tip - ahead * 0.3, ahead), (spline.bezier_points[1], top + hang * 0.2, hang)):
        point.co = tuple(at)
        point.handle_left_type = point.handle_right_type = "FREE"
        point.handle_right = tuple(at + out * 0.8)
        point.handle_left = tuple(at - out * 0.8)
    curve.materials.append(rubber)
    parts.append(stage.add("cord", curve))
    # The socket: a white ceramic cup, rounded where the cord goes in, a lip where the globe comes out.
    socket = turned_solid(stage, "socket", [(0.0, 1.2), (0.02, 1.58), (0.32, 1.64), (0.42, 1.48), (2.9, 1.46), (3.1, 1.34), (3.25, 1.05), (3.27, 0.5), (3.6, 0.45), (3.65, 0.3), (3.66, 0.0)], ceramic)
    socket.rotation_quaternion = turned_to(-hang)
    socket.location = tuple(bottom)
    parts.append(socket)
    # The globe, and its neck up into the socket.
    # Round for most of the way, then drawing in smoothly toward the neck, as the photograph's globe does, and
    # meeting the socket's mouth just inside its lip.
    turn = math.radians(125)
    arc = np.linspace(0, turn, 44)
    profile = [(GLOBE_R - GLOBE_R * math.cos(a), GLOBE_R * math.sin(a)) for a in arc]
    x0, r0 = profile[-1]
    slope = math.cos(turn) / math.sin(turn)
    mouth = GLOBE_R + 2.9
    x1, r1 = mouth - 0.1, 1.18
    for t in np.linspace(0, 1, 13)[1:]:
        h10, h01 = t**3 - 2 * t**2 + t, -2 * t**3 + 3 * t**2
        profile.append((x0 + (x1 - x0) * t, r0 * (1 - h01) + r1 * h01 + h10 * (x1 - x0) * slope))
    profile = [(0.0, 0.0)] + profile[1:] + [(mouth + 0.35, 1.1), (mouth + 0.35, 0.0)]
    globe = turned_solid(stage, "bulb-glass", profile, frosted)
    globe.rotation_quaternion = turned_to(-hang)
    globe.location = tuple(centre + hang * GLOBE_R)
    # The bulb's own light is the lamp's; its glass lets it out.
    globe.visible_shadow = False
    parts.append(globe)
    source = bpy.data.lights.new("bulb", "POINT")
    source.color = BULB_COLOUR
    source.energy = 0.0
    source.shadow_soft_size = BULB_R
    light = stage.add("bulb", source)
    light.location = tuple(centre)
    light["bulb"] = True
    parts.append(light)
    return parts


def mirrored(p, n):
    """Each point and its normal on the cat's other side: across her middle for the body, and across the head's own
    turned middle for the head."""
    flip = np.array([1, -1, 1])
    h = in_head(p)
    head_p = SKULL + GROW * (h * flip) @ TURNED.T
    head_n = ((n @ TURNED) * flip) @ TURNED.T
    on = soft(1.0 - np.linalg.norm(h / (2.8, 3.1, 3.6), axis=1), 0, 0.2)[:, None]
    return p * flip * (1 - on) + head_p * on, n * flip * (1 - on) + head_n * on


def softened(image, reach=4, passes=3):
    """A copy of an image blurred by a few pixels."""
    w, h = image.size
    pixels = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    pixels = pixels.reshape(h, w, 4)
    for _ in range(passes):
        for axis in (0, 1):
            padded = np.concatenate([np.repeat(pixels.take([0], axis), reach + 1, axis), pixels, np.repeat(pixels.take([-1], axis), reach, axis)], axis)
            total = np.cumsum(padded, axis=axis, dtype=np.float64)
            n = pixels.shape[axis]
            ahead = total.take(range(2 * reach + 1, 2 * reach + 1 + n), axis)
            behind = total.take(range(0, n), axis)
            pixels = ((ahead - behind) / (2 * reach + 1)).astype(np.float32)
    out = bpy.data.images.new(image.name + "-soft", w, h, alpha=True)
    out.colorspace_settings.name = image.colorspace_settings.name
    out.pixels.foreach_set(pixels.ravel())
    return out


def photographed(cat, origin):
    """Paint the cat with its photograph wherever the photograph sees it: each corner of the mesh takes the colour
    where the solved camera shows it, faded out where the surface turns away from that camera, is hidden behind
    something, or falls outside the cut-out. Her far side, which the photograph never shows, takes the colour the
    photograph shows at the same place on her near side, the figurine being painted much alike on both. Elsewhere
    the painted colours stay."""
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    trees = [BVHTree.FromObject(obj, graph) for obj in bpy.context.scene.objects if obj.type == "MESH"]
    data = cat.data
    count = len(data.vertices)
    co = np.empty(count * 3)
    data.vertices.foreach_get("co", co)
    normal = np.empty(count * 3)
    data.vertices.foreach_get("normal", normal)
    world = np.asarray(cat.matrix_world)
    co = co.reshape(-1, 3) @ world[:3, :3].T + world[:3, 3]
    normal = normal.reshape(-1, 3) @ world[:3, :3].T
    normal /= np.linalg.norm(normal, axis=1, keepdims=True)
    origin = np.asarray(origin)
    centre = photograph()[0] + origin
    eye = Vector(centre)

    def seen(points, normals, slack):
        """Where the photograph shows these points, and how much of its colour they take."""
        x, y, _ = in_photograph(points - origin)
        u, v = x / COLS, y / ROWS
        toward = centre - points
        toward /= np.linalg.norm(toward, axis=1, keepdims=True)
        facing = (normals * toward).sum(1)
        weight = np.clip(facing / 0.04, 0, 1) * (u > 0) * (u < 1) * (v > 0) * (v < 1)
        for i in np.nonzero(weight > 0)[0]:
            ray = Vector(points[i]) - eye
            length = ray.length
            ray.normalize()
            nearest = min((tree.ray_cast(eye, ray, length + 1)[3] or 1e9) for tree in trees)
            if nearest < length - slack:
                weight[i] = 0
        return u, v, weight, np.clip(facing, 0, 1)

    u, v, weight, facing = seen(co, normal, 0.15)
    # The other side is not quite the mirror of this one, so its points need only lie near the surface seen.
    far_p, far_n = mirrored(co - origin, normal)
    mu, mv, other, far_facing = seen(far_p + origin, far_n, 0.4)
    other *= 1 - weight
    loops = np.empty(len(data.loops), dtype=np.int64)
    data.loops.foreach_get("vertex_index", loops)
    data.uv_layers.new(name="photo").data.foreach_set("uv", np.column_stack((u[loops], 1 - v[loops])).ravel())
    data.uv_layers.new(name="mirror").data.foreach_set("uv", np.column_stack((mu[loops], 1 - mv[loops])).ravel())
    data.color_attributes.new("seen", "FLOAT_COLOR", "POINT").data.foreach_set("color", np.column_stack((weight, other, facing, far_facing)).ravel())
    nodes, links = cat.active_material.node_tree.nodes, cat.active_material.node_tree.links
    shader = nodes["Principled BSDF"]
    colour = shader.inputs["Base Color"].links[0].from_socket
    picture = bpy.data.images.load(REFERENCE)
    blurred = softened(picture)
    share = nodes.new("ShaderNodeVertexColor")
    share.layer_name = "seen"
    split = nodes.new("ShaderNodeSeparateColor")
    links.new(share.outputs["Color"], split.inputs[0])
    for name, amount, facing in (("mirror", split.outputs["Green"], share.outputs["Alpha"]), ("photo", split.outputs["Red"], split.outputs["Blue"])):
        uv = nodes.new("ShaderNodeUVMap")
        uv.uv_map = name
        sharp, smooth = (nodes.new("ShaderNodeTexImage") for _ in range(2))
        for image, source in ((sharp, picture), (smooth, blurred)):
            image.image = source
            image.extension = "EXTEND"
            links.new(uv.outputs["UV"], image.inputs["Vector"])
        # Seen edge-on, the photograph's detail would be drawn out into streaks over the surface: there only its
        # colours, softened, are kept.
        edge_on = nodes.new("ShaderNodeMapRange")
        edge_on.inputs["From Min"].default_value = 0.08
        edge_on.inputs["From Max"].default_value = 0.4
        links.new(facing, edge_on.inputs["Value"])
        photo = mix(nodes, links, edge_on.outputs["Result"], smooth.outputs["Color"], sharp.outputs["Color"])
        colour = mix(nodes, links, math_node(nodes, links, "MULTIPLY", amount, sharp.outputs["Alpha"]), colour, photo)
    links.new(colour, shader.inputs["Base Color"])


def build(stage):
    ox, oy = ORIGIN
    lo, hi = (-8.0, -8.0, -0.2), (21.6, 8.0, 28.6)
    cat, verts = mesh(stage, "cat", body, lo, hi, STEP, porcelain())
    normals = np.zeros_like(verts)
    for e, column in zip(np.eye(3) * 0.01, range(3)):
        normals[:, column] = body(verts + e) - body(verts - e)
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-9)
    paint, stripe = painted(warped(verts), normals)
    layer = cat.data.color_attributes.new("paint", "FLOAT_COLOR", "POINT")
    layer.data.foreach_set("color", paint.ravel())
    layer = cat.data.color_attributes.new("stripes", "FLOAT_COLOR", "POINT")
    layer.data.foreach_set("color", np.column_stack((stripe, stripe, stripe, np.ones(len(stripe)))).ravel())
    for part in [cat] + lamp(stage):
        part.location = (part.location.x + ox, part.location.y - oy, part.location.z)
    photographed(cat, (ox, -oy, 0))
    stage.shoot("catlamp", (0, 0, W, H), lens=False)


SHOTS = {"catlamp": build}
