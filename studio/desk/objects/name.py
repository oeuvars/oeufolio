"""A bunch of keys. A stitched leather key tag, racing green lapped over a tan tab, has the name blind
stamped into the green, and the tab carries Lacoste's crocodile. A steel split ring leans through its brass
eyelet and round the brass bar of a Ferrari key fob in its frame: a red lacquered body in dark gunmetal, with
carbon fibre twill round it. The fob carries no maker's mark."""

import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

from paint import blur, box, cloud, cover, disc, linear, ramp, segment
from solids import finish, lathe, principled, prism, rect, worn
from stock import Sheet, fit, pixels_of

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

# The fob: a Ferrari key fob in its frame, as on the newer cars. A lacquered red body sits in a dark gunmetal
# frame with a gap of carbon fibre twill round it, and a brass bar spans a notch in the top of the frame for
# the ring. Measured off a photograph, in em, from the middle of the bar, the fob hanging along x.
FOB_TURN = 22.0
FRAME = (-0.25, 7.15, 2.8)  # from, to, half its width
WALL = 0.5
FRAME_H = 1.0
FRAME_R = 1.3
BODY_GAP = 0.18
BODY_TOP = 1.3
BAR_R, BAR_HALF = 0.14, 1.4
# The ring crosses the bar this high above the mat.
RING_Z = 0.6


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
    """The split ring, leaning through the eyelet. Returns where in the frame it crosses the fob's bar."""
    reach = RING * math.sin(LEAN)
    height = reach + WIRE * (1 + math.cos(LEAN))
    across = Vector((math.cos(LEVEL), -math.sin(LEVEL), 0))
    uphill = Vector((math.sin(LEVEL), math.cos(LEVEL), 0))
    up = uphill * math.cos(LEAN) + Vector((0, 0, math.sin(LEAN)))

    def on(turn):
        return RING * (math.cos(turn) * across + math.sin(turn) * up)

    # The leather hangs from the low side of the ring and the fob from the other end of its level diameter.
    at_tag = math.pi - math.asin((tag_z - height) / reach)
    at_key = math.asin((RING_Z - height) / reach)
    centre = Vector((EYE_AT[0], -EYE_AT[1], tag_z)) - on(at_tag)
    steel = worn(principled("steel", (0.76, 0.77, 0.79), rough=0.14, metal=1.0), "Scratches003", 4, 0.22)
    split_ring(stage, "ring", centre, across, up, RING, WIRE, steel, ends=math.radians(62))
    hole = centre + on(at_key)
    return hole.x, -hole.y


def solid(stage, name, outline, z0, z1, material, cut=(), bevel=0.0):
    """A prism on an outline, with other prisms cut out of it and its edges rounded, made real as one mesh."""
    obj = prism(stage, name, outline, z0, z1, material)
    cutters = []
    for i, (hole, h0, h1) in enumerate(cut):
        cutter = prism(stage, f"{name}-cut-{i}", hole, h0, h1, None)
        boolean = obj.modifiers.new(f"cut-{i}", "BOOLEAN")
        boolean.operation = "DIFFERENCE"
        boolean.object = cutter
        cutters.append(cutter)
    if bevel:
        rounded = obj.modifiers.new("round", "BEVEL")
        rounded.width = bevel
        rounded.segments = 5
        rounded.limit_method = "ANGLE"
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
    for modifier in list(obj.modifiers):
        obj.modifiers.remove(modifier)
    obj.data = mesh
    for cutter in cutters:
        bpy.data.objects.remove(cutter)
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    return obj


def carbon(stage, outline_box, r, z):
    """Carbon fibre twill, two by two, under a clear lacquer: tows a little over a millimetre wide, those
    running one way catching the light and those the other way dark, each rounded across its width."""
    x0, y0, x1, y1 = outline_box
    sheet = Sheet(x1 - x0, y1 - y0, "#1d1d20", rough=0.35, density=4)
    X, Y = sheet.X, sheet.Y
    tow = 0.2
    i, j = np.floor(X / tow), np.floor(Y / tow)
    along = ((i + j) % 4) < 2
    sheet.paint(along.astype(float), "#2e2e33")
    across = np.where(along, (Y / tow) % 1, (X / tow) % 1)
    sheet.height += 0.004 * np.sin(np.pi * across)
    sheet.coat[:] = 1.0
    sheet.cut(box(X, Y, 0, 0, x1 - x0, y1 - y0, r))
    return sheet.build(stage, "carbon", thickness=z, coat_rough=0.05, at=(x0, y0))


def fob(stage, bar_at):
    """The fob, built about the middle of its bar and laid with the bar where the ring crosses it."""
    root = stage.add("fob", None)
    lacquer = principled("fob", "#c8101a", rough=0.18, coat_weight=1.0, coat_roughness=0.03)
    worn(lacquer, "Fingerprints009", 4, 0.05)
    gunmetal = worn(principled("frame", (0.16, 0.16, 0.17), rough=0.24, metal=1.0), "Scratches003", 3, 0.12)
    brass = worn(principled("bar", (0.86, 0.64, 0.3), rough=0.26, metal=1.0), "Scratches003", 3, 0.15)

    f0, f1, half = FRAME
    outer = rect(f0, -half, f1, half, FRAME_R, 12)
    inner = rect(f0 + WALL, -half + WALL, f1 - WALL, half - WALL, FRAME_R - WALL, 12)
    notch = rect(f0 - 1, -BAR_HALF + 0.1, f0 + WALL + 0.05, BAR_HALF - 0.1)
    frame = solid(stage, "frame", outer, 0.0, FRAME_H, gunmetal, cut=((inner, -1, 3), (notch, -1, 3)), bevel=0.12)

    i0, i1, ih = f0 + WALL, f1 - WALL, half - WALL
    bed = carbon(stage, (i0, -ih, i1, ih), FRAME_R - WALL, 0.45)
    g = BODY_GAP
    body = solid(stage, "body", rect(i0 + g, -ih + g, i1 - g, ih - g, FRAME_R - WALL - g, 12), 0.1, BODY_TOP, lacquer, bevel=0.42)

    rod = bmesh.new()
    bmesh.ops.create_cone(rod, cap_ends=True, segments=48, radius1=BAR_R, radius2=BAR_R, depth=2 * BAR_HALF)
    bmesh.ops.rotate(rod, verts=rod.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    bar = finish(stage, "bar", rod, brass)
    bar.location = (0, 0, RING_Z)
    for part in (frame, bed, body, bar):
        part.parent = root
    lay(root, bar_at, FOB_TURN)


def bunch(stage):
    fob(stage, ring(stage, tag(stage)))
    stage.shoot("name", (0, 0, W, H), bleed=2.0, shadow=0.8, sharp=1.25)


SHOTS = {"name": bunch}
