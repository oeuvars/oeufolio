"""Two Dunlop Tortex picks that have been played, after the photographs on Dunlop's own pages.

The Fin, .60 mm: orange, a shark's fin with a point, a round shoulder and a scalloped edge, printed in black.
The Wedge, 1.0 mm: white, the standard outline with a bevel ground all round it, the tortoise filled in blue.

Each is a slab of matte Delrin with a real edge. Its outline, its print and the tooth of its surface (the
pale fibres the tumbler leaves) are lifted from the photograph. The wear is a player's: a tip the strings have
ground a flat on and scuffed, hairlines running up from it, and print rubbed thin where the thumb sits."""

import json
import os

import bmesh
import bpy
import numpy as np

from paint import cloud, ramp, segment
from solids import finish
from stock import Sheet, fit, pixels_of

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art")
# One em of a pick is 9.6 mm of desk, because the page shows the picks at 1.6 times an em of six.
MM = 1 / 9.6


def art(name):
    return os.path.join(ART, name)


def arcs(height, rounds):
    """A symmetric outline as a polygon: one side from the middle of the top round to the tip is a run of arcs
    that meet smoothly, each a radius in shares of the height and the angle it turns through."""
    side, (px, py, heading) = [], (0.0, 0.0, 0.0)
    for radius, turn in rounds:
        cx, cy = px - radius * np.sin(heading), py + radius * np.cos(heading)
        for a in heading + np.radians(turn) * np.arange(1, 61) / 60:
            side.append((cx + radius * np.sin(a), cy - radius * np.cos(a)))
        heading += np.radians(turn)
        px, py = side[-1]
    side = np.array(side)
    half = side[:, 0].max()
    mirrored = side[-2::-1] * (-1, 1)
    return (np.vstack(((0.0, 0.0), side, mirrored)) + (half, 0)) * height


def spaced(points):
    """The same closed outline with its points at even steps."""
    closed = np.vstack((points, points[:1]))
    run = np.concatenate(([0], np.cumsum(np.hypot(*np.diff(closed, axis=0).T))))
    at = np.arange(len(points)) * run[-1] / len(points)
    return np.column_stack((np.interp(at, run, closed[:, 0]), np.interp(at, run, closed[:, 1])))


def blunted(points, lean, depth, rounded=0.035):
    """The outline after the strings have ground a flat across its lowest point, leaning by `lean` degrees and
    `depth` em deep, the ends of the flat worn round. Returns it with where the tip was."""
    tip = points[points[:, 1].argmax()].copy()
    across = np.array((np.sin(np.radians(lean)), np.cos(np.radians(lean))))
    over = (points - tip + (0, depth)) @ across
    over = (over + np.sqrt(over**2 + rounded**2)) / 2 * (over > -0.3)
    return spaced(points - over[:, None] * across), tip


def within(sheet, points):
    """How far inside the outline each point of the sheet lies, in em. Negative outside."""
    step = 4
    X, Y = sheet.X[::step, ::step], sheet.Y[::step, ::step]
    nearest, inside = np.full(X.shape, np.inf), np.zeros(X.shape, dtype=bool)
    for (ax, ay), (bx, by) in zip(points, np.roll(points, -1, axis=0)):
        if (ax, ay) == (bx, by):
            continue
        nearest = np.minimum(nearest, segment(X, Y, ax, ay, bx, by))
        if ay != by:
            inside ^= ((ay > Y) != (by > Y)) & (X < ax + (bx - ax) * (Y - ay) / (by - ay))
    return fit(np.where(inside, nearest, -nearest)[..., None], *sheet.height.shape)[..., 0]


def slab(stage, name, sheet, points, thickness, rounded, bevel=None, lift=(0.0, 0.0)):
    """The pick itself: the outline extruded to its thickness, its top edge tumbled round, wearing the sheet's
    painted surface. bevel is the width and the drop of a bevel ground inside that edge. lift is how much the
    pick rises per em across and down the page: a played pick is bent, and rests on one edge."""
    bm = bmesh.new()
    foot = [bm.verts.new((x, -y, 0)) for x, y in points]
    top = [bm.verts.new((x, -y, thickness)) for x, y in points]
    bm.faces.new(foot)
    lid = bm.faces.new(top)
    count = len(points)
    for i in range(count):
        bm.faces.new((foot[i], foot[(i + 1) % count], top[(i + 1) % count], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    edge = set(top)
    if bevel:
        # The inset keeps the lid's own corners and gives the outline new ones, which are the ones to lower.
        bmesh.ops.inset_region(bm, faces=[lid], thickness=bevel[0], use_even_offset=True)
        edge = {vert for vert in bm.verts if vert.co.z > 0} - set(lid.verts)
        for vert in edge:
            vert.co.z -= bevel[1]
        bm.normal_update()
    rim = [side for side in bm.edges if side.verts[0] in edge and side.verts[1] in edge]
    bmesh.ops.bevel(bm, geom=rim, offset=rounded, segments=4, profile=0.5, affect="EDGES", clamp_overlap=False)
    place = bm.loops.layers.uv.new()
    for face in bm.faces:
        for loop in face.loops:
            loop[place].uv = (loop.vert.co.x / sheet.w, 1 + loop.vert.co.y / sheet.h)
    rise = points @ lift
    for vert in bm.verts:
        vert.co.z += lift[0] * vert.co.x - lift[1] * vert.co.y - rise.min()
    return finish(stage, name, bm, sheet.material)


def played(
    stage, name, size, outline, plastic, chalk, scuff, tooth, printed, thumb, lean, grime, seed, shape, exposure
):
    """Paint one pick and stand it on the stage.
    tooth is the art file and how far its greys were stretched. printed is the art file and the box it fills,
    in shares of the pick's width and height. scuff is the colour the strings leave. shape is the thickness,
    the radius of the tumbled edge, the ground bevel, if any, and how the pick lifts off the mat."""
    w, h = size
    sheet = Sheet(w, h, plastic, rough=0.76, density=8)
    X, Y = sheet.X, sheet.Y
    area = sheet.height.shape
    sheet.sdf = np.full(area, -1.0)
    worn, tip = blunted(outline, lean, 0.01)
    inside = within(sheet, worn)

    # Tooth: the photographed surface, paler where it is chalky or a fibre crosses it.
    file, stretch = tooth
    marks = (fit(pixels_of(art(file))[..., :1].astype(np.float64), *area)[..., 0] - 0.5) / stretch
    sheet.rgb *= (1 + np.clip(marks, -0.5, 0))[..., None] ** 2.2
    sheet.paint(np.clip(marks * 1.2, 0, 0.75), chalk)
    sheet.height += 0.005 * np.clip(marks * 2 / stretch, -0.1, 0.25)

    # Where the thumb and finger hold it the plastic has taken skin and gone a little smoother.
    held = np.exp(-(((X - thumb[0] * w) / 0.85) ** 2 + ((Y - thumb[1] * h) / 0.8) ** 2))
    held *= np.clip(0.75 + 0.35 * cloud(area, seed, falloff=2.4), 0, 1)
    sheet.paint(held * grime[1], grime[0])
    sheet.finish(held * 0.4, rough=0.62)

    # The print, in its own inks, rubbed thinner under the thumb. Chalk and fibres show through it.
    file, (x0, y0, x1, y1) = printed
    r0, r1, c0, c1 = (round(v * sheet.ppe) for v in (y0 * h, y1 * h, x0 * w, x1 * w))
    stamp = fit(pixels_of(art(file)).astype(np.float64), r1 - r0, c1 - c0)
    inks = np.where(stamp[..., :3] <= 0.04045, stamp[..., :3] / 12.92, ((stamp[..., :3] + 0.055) / 1.055) ** 2.4)
    # The photograph's inks carry the shine of its own lights, and the stage adds its own again.
    inks = np.clip(inks * 0.85 - 0.012, 0, 1)
    ink = np.zeros(area)
    ink[r0:r1, c0:c1] = stamp[..., 3]
    rubbed = np.clip(held * np.clip(cloud(area, seed + 1, falloff=1.9) - 0.1, 0, 1.2), 0, 1)
    ink *= (1 - 0.5 * rubbed) * (1 - np.clip(marks * 2.0, 0, 0.4))
    patch = sheet.rgb[r0:r1, c0:c1]
    patch += 0.98 * ink[r0:r1, c0:c1, None] * (inks - patch)
    sheet.finish(ink, rough=0.7)
    sheet.height += 0.003 * ink

    # Scratches: the strings drag grit up from the tip and leave a few hairlines, none of them straight.
    rng = np.random.default_rng(seed)
    lines = np.zeros(area)
    for _ in range(8):
        along, aside = rng.uniform(0.25, 1.5), rng.normal(0, 0.28)
        x, y = tip[0] + aside + 0.25 * along * np.sin(np.radians(lean)), tip[1] - along
        turn, bend, half = np.radians(rng.normal(-52, 20)), np.radians(rng.normal(0, 7)), rng.uniform(0.08, 0.34)
        width, weight = rng.uniform(0.0015, 0.004), rng.uniform(0.4, 1.0)
        for way, angle in ((-1, turn - bend), (1, turn + bend)):
            d = segment(X, Y, x, y, x + way * half * np.cos(angle), y + way * half * np.sin(angle), width)
            lines = np.maximum(lines, sheet.mask(d) * weight)
    lines *= np.clip(0.55 + 0.6 * cloud(area, seed + 2, falloff=1.2), 0, 1)
    sheet.paint(lines * 0.55, scuff)
    sheet.press(lines, 0.003)

    # The tip: the flat and the edge either side of it are scuffed and furred, most on the worn flank.
    reach = np.hypot(X - tip[0] - 0.12 * np.sign(lean), Y - tip[1] + 0.05)
    near = 1 - ramp(0.2, 1.0, reach)
    edge = near * (1 - ramp(0.0, 0.14, inside))
    scuffed = np.clip(edge + 0.12 * near**2, 0, 1)
    scuffed *= np.clip(0.8 + 0.3 * cloud(area, seed + 3, falloff=1.0), 0, 1)
    sheet.paint(scuffed * 0.75, scuff)
    sheet.finish(scuffed, rough=0.62)

    # The cut edge was tumbled round, and is a shade chalkier than the face all the way along.
    sheet.paint((1 - ramp(0.0, 0.05, inside)) * 0.22, chalk)

    thickness, rounded, bevel, lift = shape
    sheet.material = sheet.build(
        stage,
        f"{name}-sheet",
        scan="Rubber004",
        scan_size=1.6,
        scan_normal=0.5,
        scan_rough=0.4,
        wear=(("Scratches003", 2.4, 0.1, 0.0015), ("SurfaceImperfections003", 4, 0.1, 0)),
        specular=0.15,
    ).data.materials[0]
    bpy.data.objects.remove(bpy.data.objects[f"{name}-sheet"])
    slab(stage, name, sheet, worn, thickness, rounded, bevel, lift)
    stage.shoot(name, (0, 0, w, h), bleed=0.6, shadow=1.5, exposure=exposure, sharp=3.0)


def fin(stage):
    w, h = 3.145, 3.3
    with open(art("tortex-fin-outline.json")) as file:
        outline = np.array(json.load(file)) * h
    played(
        stage,
        "pick-fin",
        (w, h),
        outline,
        plastic="#ff5208",
        chalk="#ffb78c",
        scuff="#ffd0b0",
        tooth=("tortex-fin-tooth.png", 2.0),
        printed=("tortex-fin-print.png", (0.2426, 0.2224, 0.7292, 0.7037)),
        thumb=(0.5, 0.46),
        lean=13.0,
        grime=("#8a2f0c", 0.1),
        seed=60,
        shape=(0.6 * MM, 0.026, None, (-0.02, 0.02)),
        exposure=0.3,
    )


def wedge(stage):
    w, h = 2.76, 3.125
    outline = arcs(h, ((0.7767, 22.57), (0.2328, 82.27), (1.4489, 29.01), (0.1083, 46.15)))
    played(
        stage,
        "pick-wedge",
        (w, h),
        outline,
        plastic="#f5f4ef",
        chalk="#ffffff",
        scuff="#9d9a94",
        tooth=("tortex-wedge-tooth.png", 5.0),
        printed=("tortex-wedge-print.png", (0.1408, 0.0707, 0.799, 0.8274)),
        thumb=(0.5, 0.42),
        lean=-12.0,
        grime=("#a8997d", 0.12),
        seed=100,
        shape=(1.0 * MM, 0.02, (0.11, 0.5 * MM), (-0.014, 0.014)),
        exposure=0.45,
    )


SHOTS = {"pick-fin": fin, "pick-wedge": wedge}
