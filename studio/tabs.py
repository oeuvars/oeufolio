"""What is stuck on the folder tabs: six pieces, one on each paper tab, each for something I like and
carrying its maker's mark, the way stickers end up on everything a kid owns.

    hamilton  a watch strap: brown top grain leather, padded and saddle stitched, with Hamilton's mark
              stamped into it
    proraso   Proraso's green under its own badge, clamped in the grip of a Merkur razor: chrome, knurled,
              with Merkur's mark struck into its collar
    lacoste   the white piqué polo: the crocodile, the name, and tipping in its green and red
    prs       a PRS Silver Sky's Polar Blue, with PRS's mark and four of the birds it inlays down its
              fretboards, dark as they are in maple, and a band of Blackstar's black tolex and cream
              piping round it under its name in raised white
    apple     platinum, with the six-colour apple let into it over the drilled grille of a Mac Studio
    van       a Turkish Van's own: white, auburn at head and tail as the breed is, and her mark, the cat
              asleep on her back and stretched out

Uses the copy stand from the oeusume studio. Run from the repository root:

    blender -b --factory-startup -P studio/tabs.py -- [tab ...] [--scale 0.5] [--samples 64] [--proofs DIR]

Writes public/objects/tab-<name>.avif for each tab named, or for all six. Set OEUSUME if that checkout
is not in ~/Documents/oeusume.

The frame is the paper tab SiteShell cuts, in the page's own rem, so the render lies straight over it. A
piece is smaller than the paper, with paper left showing all round it, and it was stuck down by hand, so
none sits quite true. Each is a solid with a rounded edge, and the plastic ones are cut to the paper's
shape. A piece's colours, its marks and the texture of its surface are painted as a sheet and laid over
the solid from above.

The marks are the makers' own, from studio/assets/logos. The cat's is drawn in studio/cat.svg.
"""

import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OEUSUME = os.environ.get("OEUSUME", os.path.expanduser("~/Documents/oeusume"))
sys.path.insert(0, os.path.join(OEUSUME, "studio"))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix  # noqa: E402

import stage as stage_module  # noqa: E402
from paint import blur, box, cloud, linear, ramp, segment, streaks  # noqa: E402
from objects.fob import spaced, stitch  # noqa: E402
from paint import disc  # noqa: E402
from solids import fillet, principled, prism, rect  # noqa: E402
from stage import Stage  # noqa: E402
from stock import Sheet, fit, pixels_of  # noqa: E402

# All in the page's rem. BAND and PROTRUDE are useStackMetrics' band and protrude on a wide screen.
BAND, PROTRUDE = 1.9, 2.1
WIDTH = BAND + PROTRUDE
# How much paper shows round the plastic: on the panel's side, at its head and foot, and along the tab's cut edge.
NEAR, HEAD, FAR = 0.62, 0.5, 0.38
MIDDLE = (NEAR + WIDTH - FAR) / 2
THICK = 0.28
EDGE = 0.13  # the radius its top edge is rounded to
CROWN, SHOULDER = 0.08, 0.6  # the face is pillowed: it falls this far over this much of the way in from the edge
MARGIN = 0.3  # room round the paper tab, so the shadow the plastic leaves is never cut off
INK = "#161512"


def outline(height):
    """The plastic, cut as the page cuts the paper tab: square to the band, slanting out to a straight edge
    and back in."""
    rise = PROTRUDE * 0.33
    run = math.hypot(PROTRUDE, rise)
    slope = rise / PROTRUDE
    # The paper's slant, moved in by FAR, and where it meets the plastic's head and its straight edge.
    x0, y0 = BAND - FAR * rise / run, FAR * PROTRUDE / run
    far = WIDTH - FAR
    bend = x0 + (HEAD - y0) / slope
    drop = y0 + (far - x0) * slope
    reach = 0.3
    lean = math.atan2(rise, PROTRUDE)
    shallow = reach * math.tan((math.pi - lean) / 2)
    steep = reach * math.tan((math.pi / 2 + lean) / 2)
    return fillet(
        [
            (NEAR, HEAD, 0.22),
            (bend, HEAD, shallow),
            (far, drop, steep),
            (far, height - drop, steep),
            (bend, height - HEAD, shallow),
            (NEAR, height - HEAD, 0.22),
        ],
        steps=12,
    )


def stuck(obj, height, askew):
    """Set a piece down as a hand does: turned a little about its middle and a little off its place.
    askew is the turn in degrees and the slip across and down the page in rem."""
    turn, across, down = askew
    bpy.context.view_layer.update()
    middle = Matrix.Translation((WIDTH / 2, -height / 2, 0))
    slip = Matrix.Translation((across, -down, 0)) @ middle @ Matrix.Rotation(math.radians(-turn), 4, "Z") @ middle.inverted()
    obj.matrix_world = slip @ obj.matrix_world
    return obj


def within(X, Y, points):
    """Signed distance to an outline with no hollows, given clockwise on the page. Negative inside."""
    distance = np.full(X.shape, np.inf)
    inside = np.ones(X.shape, dtype=bool)
    for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
        if math.hypot(bx - ax, by - ay) < 1e-9:
            continue
        distance = np.minimum(distance, segment(X, Y, ax, ay, bx, by))
        inside &= (bx - ax) * (Y - ay) - (by - ay) * (X - ax) >= 0
    return np.where(inside, -distance, distance)


def skin(sheet, name, punched=False, **surface):
    """A sheet's painted surface as a material alone, for a solid to wear. punched keeps what was
    punched out of the sheet clear, for a solid with holes through it."""
    plane = sheet.build(STAGE, name, **surface)
    material = plane.data.materials[0]
    bpy.data.objects.remove(plane, do_unlink=True)
    # The solid has its own outline. The sheet's would fray it where the two meet.
    shader = material.node_tree.nodes["Principled BSDF"]
    for link in list(shader.inputs["Alpha"].links) if not punched else []:
        material.node_tree.links.remove(link)
    return material


def clad(obj, x0, y0, w, h):
    """Lay a sheet's maps over a solid from straight above, the sheet's top left corner at x0, y0."""
    mesh = obj.data
    layer = mesh.uv_layers.new()
    for loop in mesh.loops:
        x, y, _ = mesh.vertices[loop.vertex_index].co
        layer.data[loop.index].uv = ((x - x0) / w, 1 + (y + y0) / h)
    return obj


def pillow(sheet, edge):
    """Crown the face, so that it mirrors the room in a sweep and not as one flat tone."""
    sheet.height -= CROWN * (1 - np.clip(-edge / SHOULDER, 0, 1)) ** 2


def ceiling(height):
    """A black card straight over the plastic. A glossy face lying flat would mirror the bright room above
    it and go milky. With the card there the flat of the piece keeps its colour, and only what leans, the
    crown of its face and its rounded edge, looks past the card to the studio's lamps."""
    card = bpy.data.meshes.new("ceiling")
    card.from_pydata([(-11, -11, 0), (11, -11, 0), (11, 11, 0), (-11, 11, 0)], [], [(0, 1, 2, 3)])
    card.materials.append(principled("ceiling", (0.02, 0.02, 0.02), rough=1.0, specular_ior_level=0.0))
    over = STAGE.add("ceiling", card)
    over["stand"] = "room"
    over.location = (WIDTH / 2, -height / 2, 70)
    for seen in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission"):
        setattr(over, seen, False)


def trimmed(art):
    """Artwork cut close to what is drawn in it."""
    drawn = art[..., 3] > 0.02
    rows, cols = np.flatnonzero(drawn.any(axis=1)), np.flatnonzero(drawn.any(axis=0))
    return art[rows[0] : rows[-1] + 1, cols[0] : cols[-1] + 1]


def artwork(name):
    """A mark or a drawing from studio/assets, rows from the top: its colour as stored, and how much of
    each pixel it covers."""
    return trimmed(pixels_of(os.path.join(HERE, "assets", f"{name}.png")).astype(np.float64))


def parted(art):
    """A lockup split at the widest clear gap across it: the name, and the mark that stands beside it."""
    clear = np.flatnonzero(~(art[..., 3] > 0.02).any(axis=0))
    gap = max(np.split(clear, np.flatnonzero(np.diff(clear) > 1) + 1), key=len)
    return trimmed(art[:, : gap[0]]), trimmed(art[:, gap[-1] + 1 :])


def strewn(art):
    """Artwork that sets several marks in a row, as each mark alone."""
    drawn = (art[..., 3] > 0.02).any(axis=0).astype(np.int8)
    edges = np.flatnonzero(np.diff(np.concatenate(([0], drawn, [0]))))
    return [trimmed(art[:, a:b]) for a, b in zip(edges[::2], edges[1::2])]


def placed(sheet, art, x0, y0, x1, y1, turn=0):
    """Fit artwork inside a box on the sheet, as large as it goes without changing its shape, after `turn`
    quarter turns clockwise. Returns how much of each of the sheet's pixels it covers, and its colour
    there as light."""
    art = np.rot90(art, -turn)
    scale = min((x1 - x0) / art.shape[1], (y1 - y0) / art.shape[0])
    rows, cols = max(1, round(art.shape[0] * scale * sheet.ppe)), max(1, round(art.shape[1] * scale * sheet.ppe))
    # Colour is weighed by cover while it is made smaller, so nothing clear bleeds into an edge.
    weighed = art.copy()
    weighed[..., :3] *= weighed[..., 3:]
    by = art.shape[1] // cols
    if by > 1:
        h, w = art.shape[0] // by * by, art.shape[1] // by * by
        weighed = weighed[:h, :w].reshape(h // by, by, w // by, by, 4).mean(axis=(1, 3))
    weighed = fit(weighed, rows, cols)
    r0 = round(((y0 + y1) / 2) * sheet.ppe - rows / 2)
    c0 = round(((x0 + x1) / 2) * sheet.ppe - cols / 2)
    cover = np.zeros(sheet.height.shape)
    colour = np.zeros(sheet.rgb.shape)
    cover[r0 : r0 + rows, c0 : c0 + cols] = np.clip(weighed[..., 3], 0, 1)
    stored = np.clip(weighed[..., :3] / np.maximum(weighed[..., 3:], 1e-4), 0, 1)
    colour[r0 : r0 + rows, c0 : c0 + cols] = np.where(stored <= 0.04045, stored / 12.92, ((stored + 0.055) / 1.055) ** 2.4)
    return cover, colour


def printed(sheet, cover, colour, rough=0.2, coat=0.6, proud=0.004):
    """Print a mark on the plastic in its own colours, or in one. The ink stands a hair proud of the face."""
    tone = linear(colour) if isinstance(colour, str) else colour
    sheet.rgb += cover[..., None] * (tone - sheet.rgb)
    sheet.finish(cover, rough=rough, coat=coat)
    sheet.height += proud * blur(cover, 1.0)


def stripe(sheet, y0, y1):
    """A band straight across the piece."""
    return sheet.mask(np.abs(sheet.Y - (y0 + y1) / 2) - (y1 - y0) / 2)


def inlay(sheet, mask, colour, rough=0.16, coat=0.7):
    """A second plastic set flush into the first. The join between them shows as a hairline."""
    sheet.paint(mask, colour)
    sheet.finish(mask, rough=rough, coat=coat)
    seam = np.clip(1 - np.abs(mask - 0.5) * 2, 0, 1)
    sheet.press(blur(seam, 1.2), 0.004)
    sheet.rgb *= (1 - 0.18 * blur(seam, 0.8))[..., None]


def swirl(sheet, mask, seed, light, dark, amount=0.35, stretch=0.5):
    """Slow swirls of a lighter and a darker shade, as celluloid, acetate and fur have."""
    turn = cloud(sheet.height.shape, seed, falloff=2.2, stretch=stretch)
    sheet.paint(mask * np.clip(turn, 0, 1.6) * amount, light)
    sheet.paint(mask * np.clip(-turn, 0, 1.6) * amount, dark)


def pearl(sheet, mask):
    """Mother of pearl. It is laid down in patches, each catching the light or missing it, and each
    throws back a little colour of its own."""
    shape = sheet.height.shape
    figure = np.clip(streaks(shape, 61, 34, 13) + 0.7 * streaks(shape, 62, 12, 30), -2, 2) / 2
    sheet.paint(mask * np.clip(figure, 0, 1) * 0.9, "#ffffff")
    sheet.paint(mask * np.clip(-figure, 0, 1) * 0.5, "#a5a196")
    for seed, tint in ((63, "#eab4c4"), (64, "#a9dcc0"), (65, "#b3c9f0")):
        sheet.paint(mask * np.clip(streaks(shape, seed, 26, 20), 0, 2) * 0.2, tint)


def moulded(name, height, colour, rough, coat, dress, **surface):
    """A piece of plastic cut to the paper tab. dress paints what it carries on its sheet, given the
    sheet and the distance in from the plastic's edge, and returns whatever else is fixed to it."""
    sheet = Sheet(WIDTH, height, colour, rough=rough, density=3)
    sheet.coat[:] = coat
    shape = outline(height)
    edge = within(sheet.X, sheet.Y, shape)
    pillow(sheet, edge)
    fitted = dress(sheet, edge) or []
    # Moulded plastic is never one even shine: it flows a little as it cools, and it has been handled.
    sheet.rough += 0.025 * np.clip(cloud(sheet.height.shape, 5, falloff=2.0), -2, 2)
    sheet.height += 0.0012 * np.clip(cloud(sheet.height.shape, 6, falloff=2.4), -2, 2)
    plastic = skin(
        sheet,
        f"{name}-skin",
        scan="Plastic010",
        scan_size=7,
        scan_normal=0.25,
        scan_rough=0.15,
        wear=(("Scratches003", 5, 0.05, 0.0005), ("SurfaceImperfections003", 8, 0.03, 0)),
        specular=0.5,
        coat_rough=0.06,
        **surface,
    )
    body = prism(STAGE, name, shape, 0.0, THICK, plastic, bevel=EDGE, segments=7)
    return [clad(body, 0, 0, WIDTH, height), *fitted]


def knurl(X, Y, pitch):
    """Diamond knurling: two sets of grooves cut across each other leave rows of small pyramids."""
    a = (X * math.cos(math.radians(30)) + Y * math.sin(math.radians(30))) / pitch
    b = (X * math.cos(math.radians(30)) - Y * math.sin(math.radians(30))) / pitch
    return np.minimum(1 - np.abs(2 * (a % 1) - 1), 1 - np.abs(2 * (b % 1) - 1))


def grip(name, y0, y1, mark):
    """The handle of a Merkur razor, as a chromed collar clamped round the plastic. Most of it is the
    grip: a fine diamond knurl, satin where the plating has rounded every point. Below that is the
    polished band the razor has above its knob, and the maker's mark is struck into it there."""
    lap = 0.05
    x0, x1 = NEAR - lap, WIDTH - FAR + lap
    w, h = x1 - x0, y1 - y0
    lip, band = 0.28, 1.18
    sheet = Sheet(w, h, "#d6d6da", rough=0.03, density=3)
    X, Y = sheet.X, sheet.Y
    sheet.metal[:] = 1.0
    # It is bent round the piece: it bows a little across, and falls away at each side.
    sheet.height -= 0.05 * ((X - w / 2) / (w / 2)) ** 2
    sheet.height -= 0.09 * (1 - np.clip(np.minimum(X, w - X) / 0.5, 0, 1)) ** 2
    cut = ramp(lip - 0.015, lip + 0.015, Y) * ramp(band - 0.015, band + 0.015, h - Y)
    sheet.height += 0.016 * cut * blur(knurl(X, Y, 0.13), 1.2)
    sheet.rough += 0.24 * cut
    sheet.rgb *= (1 - 0.14 * cut)[..., None]
    # A groove is turned where the knurl stops, and one more near each end.
    for y in (lip, h - band, 0.1, h - 0.1):
        sheet.press(np.exp(-(((Y - y) / 0.026) ** 2)), 0.014)
    die, _ = placed(sheet, mark, 0.3, h - band + 0.17, w - 0.3, h - 0.21)
    # A die leaves what it strikes sunk and dull.
    sheet.press(blur(die, 1.0), 0.02)
    sheet.finish(die, rough=0.36)
    sheet.rgb *= (1 - 0.55 * die)[..., None]
    # Plating is never flawless, and a razor is handled every morning.
    sheet.rough += 0.012 * np.clip(cloud(sheet.height.shape, 9, falloff=1.8), -2, 2)
    chrome = skin(
        sheet,
        f"{name}-chrome",
        wear=(("Scratches003", 3, 0.05, 0.0004), ("SurfaceImperfections003", 5, 0.05, 0)),
        specular=0.5,
    )
    collar = prism(STAGE, f"{name}-grip", rect(x0, y0, x1, y1, 0.05, 4), 0.0, THICK + 0.05, chrome, bevel=0.045, segments=4)
    return clad(collar, x0, y0, w, h)


def proraso(name, height):
    def dress(sheet, edge):
        badge, colour = placed(sheet, artwork("logos/proraso"), MIDDLE - 1.04, 0.98, MIDDLE + 1.04, 4.82, turn=1)
        printed(sheet, badge, colour, rough=0.18, coat=0.7, proud=0.006)
        inlay(sheet, stripe(sheet, 5.2, 5.4), "#f2ecd9")
        inlay(sheet, stripe(sheet, 5.5, 5.59), "#c5222b")
        return [grip(name, 5.9, 8.56, artwork("logos/merkur"))]

    return {"card": 2.2}, moulded(name, height, "#0a7440", 0.1, 0.7, dress, subsurface=0.04)


def lacoste(name, height):
    def dress(sheet, edge):
        X, Y = sheet.X, sheet.Y
        word, crocodile = parted(artwork("logos/lacoste"))
        tipped = stripe(sheet, 7.42, 8.72)
        croc, colour = placed(sheet, crocodile, MIDDLE - 1.16, 1.0, MIDDLE + 1.16, 2.62)
        wordmark, _ = placed(sheet, word, MIDDLE - 0.5, 3.0, MIDDLE + 0.5, 7.05, turn=1)
        # Petit piqué: the knit's small raised cells, moulded into the face inside a plain border.
        pitch = 0.18
        row = np.floor(Y / (pitch * 0.866))
        u = (X / pitch + 0.5 * (row % 2)) % 1 - 0.5
        v = (Y / (pitch * 0.866)) % 1 - 0.5
        cell = np.clip(1 - (u * u + v * v) / 0.2, 0, 1)
        field = ramp(0.2, 0.3, -edge) * (1 - tipped) * (1 - np.clip(blur(croc, 4.0) * 3, 0, 1))
        sheet.height += 0.016 * field * cell
        sheet.rough += 0.14 * field
        # The crocodile is sewn on as a patch, so it stands off the knit.
        printed(sheet, croc, colour, rough=0.3, coat=0.3, proud=0.014)
        printed(sheet, wordmark, INK, rough=0.3, coat=0.2)
        inlay(sheet, stripe(sheet, 7.5, 8.12), "#004f2b", rough=0.1)
        inlay(sheet, stripe(sheet, 8.34, 8.64), "#cf2027")

    return {}, moulded(name, height, "#f1eee6", 0.3, 0.25, dress, subsurface=0.08)


def amp(name, y0, y1, mark):
    """A band of a Blackstar amplifier clamped round the piece: black tolex between two beads of cream
    piping, with the maker's name on it in raised white plastic, as it is on the front of the cabinets."""
    lap = 0.05
    x0, x1 = NEAR - lap, WIDTH - FAR + lap
    w, h = x1 - x0, y1 - y0
    sheet = Sheet(w, h, "#131212", rough=0.34, density=3)
    X, Y = sheet.X, sheet.Y
    shape = sheet.height.shape
    sheet.coat[:] = 0.15
    # It is bent round the piece, so it falls away at each side.
    sheet.height -= 0.08 * (1 - np.clip(np.minimum(X, w - X) / 0.5, 0, 1)) ** 2
    piping = np.minimum(np.abs(Y - 0.16), np.abs(Y - (h - 0.16)))
    word, _ = placed(sheet, mark, 0.26, 0.36, w - 0.26, h - 0.36)
    # Tolex: a pebbled grain pressed into the black, everywhere but the piping and the letters.
    grain = np.clip(blur(cloud(shape, 31, falloff=0.9), 1.6), -2, 2) + 0.5 * np.clip(cloud(shape, 32, falloff=1.5), -2, 2)
    bare = (1 - sheet.mask(piping - 0.07)) * (1 - np.clip(blur(word, 2.0) * 3, 0, 1))
    sheet.height += 0.005 * bare * grain
    sheet.rough += 0.05 * bare * np.clip(grain, -1, 1)
    sheet.paint(sheet.mask(piping - 0.05), "#e8dfc6")
    sheet.height += 0.022 * np.sqrt(np.clip(1 - (piping / 0.05) ** 2, 0, 1))
    sheet.finish(sheet.mask(piping - 0.05), rough=0.3, coat=0.3)
    printed(sheet, word, "#f3f0e6", rough=0.2, coat=0.6, proud=0.024)
    tolex = skin(sheet, f"{name}-tolex", wear=(("SurfaceImperfections003", 6, 0.05, 0),), specular=0.5)
    band = prism(STAGE, f"{name}-amp", rect(x0, y0, x1, y1, 0.06, 4), 0.0, THICK + 0.05, tolex, bevel=0.045, segments=4)
    return clad(band, x0, y0, w, h)


def prs(name, height):
    def dress(sheet, edge):
        # PRS's mark runs down one side. Down the other fly four of the birds, in the order the
        # fretboard has them. Both are let into the finish flush.
        mark, _ = placed(sheet, artwork("logos/prs"), 0.98, 1.2, 2.1, 5.7, turn=1)
        inlay(sheet, mark, INK, rough=0.2, coat=1.0)
        for i, bird in enumerate(strewn(artwork("logos/prs-birds"))[4:8]):
            flying, _ = placed(sheet, bird, 2.32, 1.12 + 1.18 * i, 3.3, 2.12 + 1.18 * i)
            inlay(sheet, flying, INK, rough=0.2, coat=1.0)
        return [amp(name, 6.1, 8.3, artwork("logos/blackstar"))]

    return {"card": 1.2}, moulded(name, height, "#a6cbe0", 0.08, 1.0, dress, subsurface=0.05)


def apple(name, height):
    def dress(sheet, edge):
        X, Y = sheet.X, sheet.Y
        badge, colour = placed(sheet, artwork("logos/apple"), MIDDLE - 0.98, 1.35, MIDDLE + 0.98, 3.75)
        sheet.rgb += badge[..., None] * (colour - sheet.rgb)
        sheet.finish(badge, rough=0.12, coat=0.9)
        # The badge is let into the case, and sits in a shallow well of its own.
        sheet.press(blur(np.clip(badge * 2, 0, 1), 2.0), 0.006)
        # The grille of a Mac Studio: round holes drilled close, each row half a step from the last.
        # Only whole holes are drilled, so the field stops clean inside the piece's edge.
        top, foot, pitch, bore = 4.75, 8.6, 0.2, 0.062
        row = np.round(Y / (pitch * 0.866))
        col = np.round(X / pitch - 0.5 * (row % 2))
        cx, cy = (col + 0.5 * (row % 2)) * pitch, row * pitch * 0.866
        rows = np.clip((cy * sheet.ppe).astype(int), 0, Y.shape[0] - 1)
        cols = np.clip((cx * sheet.ppe).astype(int), 0, Y.shape[1] - 1)
        drilled = (cy > top) & (cy < foot) & (edge[rows, cols] < -0.42)
        hole = sheet.mask(np.hypot(X - cx, Y - cy) - bore) * drilled
        # Each is countersunk a little, then goes down into the dark of the case.
        sheet.press(blur(hole, 2.2), 0.02)
        sheet.press(blur(hole, 0.7), 0.07)
        sheet.paint(hole, "#0b0b0b")
        sheet.finish(hole, rough=0.7, coat=0.0)

    return {}, moulded(name, height, "#dcdcd8", 0.1, 0.8, dress, subsurface=0.1)


def van(name, height):
    def dress(sheet, edge):
        # The breed's own pattern: colour on the head and on the tail, and white between.
        head, tail = stripe(sheet, 0.0, 2.2), stripe(sheet, height - 2.3, height)
        for seed, cap in ((17, head), (18, tail)):
            inlay(sheet, cap, "#a4552b")
            swirl(sheet, cap, seed, "#c9824c", "#6a2f15", amount=0.5, stretch=0.8)
        # A Van's tail is ringed in a darker auburn.
        for y in (height - 1.82, height - 1.38, height - 0.94):
            sheet.paint(stripe(sheet, y - 0.06, y + 0.06) * 0.75, "#5e2a13")
        mark, colour = placed(sheet, artwork("cat"), MIDDLE - 1.2, 2.5, MIDDLE + 1.2, height - 2.6)
        printed(sheet, mark, colour, rough=0.2, coat=0.6, proud=0.006)

    return {}, moulded(name, height, "#f3efe4", 0.18, 0.5, dress, subsurface=0.06)


def hamilton(name, height):
    """No plastic: the long end of a watch strap lying down the tab. Brown top grain leather, padded so
    it stands highest down its middle, its edges burnished dark, saddle stitched in ecru all round, with
    holes punched for the buckle's tongue and Hamilton's mark stamped into it blind."""
    left, right, head, foot = 0.82, 3.42, 0.9, height - 0.85
    middle, point, seam = (left + right) / 2, 1.05, 0.24
    shape = fillet([(left, head, 0.14), (right, head, 0.14), (right, foot - point, 0.9), (middle, foot, 0.5), (left, foot - point, 0.9)], steps=14)
    sewn = fillet(
        [
            (left + seam, head + seam, 0.06),
            (right - seam, head + seam, 0.06),
            (right - seam, foot - point - 0.06, 0.7),
            (middle, foot - 1.45 * seam, 0.32),
            (left + seam, foot - point - 0.06, 0.7),
        ],
        steps=12,
    )
    sheet = Sheet(WIDTH, height, "#71421f", rough=0.42, density=3)
    X, Y = sheet.X, sheet.Y
    edge = within(X, Y, shape)
    sheet.height -= 0.1 * (1 - np.clip(-edge / 0.75, 0, 1)) ** 2
    # The mark goes in before the stitching: pressed and burnished, with no colour of its own.
    mark, _ = placed(sheet, artwork("logos/hamilton"), middle - 0.5, 1.75, middle + 0.5, 5.75, turn=1)
    sheet.press(blur(mark, 1.2), 0.03)
    sheet.ink(mark, "#1d1916", 0.5)
    sheet.finish(mark, rough=0.26)
    sheet.ink(ramp(-0.1, -0.02, edge), "#1d1916", 0.55)
    # The stitch line is creased in before the thread goes through.
    sheet.press(np.exp(-((within(X, Y, sewn) / 0.07) ** 2)), 0.018)
    stitch(sheet, spaced(sewn, 0.27), thread="#e9dcba", length=0.2, width=0.07)
    for y in (6.55, 7.3, 8.05, 8.8):
        hole = disc(X, Y, middle, y, 0.115)
        sheet.punch(hole)
        # Round each hole the leather is crushed down, and darkened by the tongue.
        sheet.press(np.exp(-((hole / 0.09) ** 2)), 0.03)
        sheet.ink(np.exp(-((hole / 0.07) ** 2)), "#1d1916", 0.5)
    leather = skin(
        sheet,
        f"{name}-leather",
        punched=True,
        scan="Leather037",
        scan_size=5.5,
        scan_normal=1.5,
        scan_rough=1.0,
        wear=(("SurfaceImperfections003", 12, 0.1, 0),),
        mottle=0.08,
        sheen=0.15,
        specular=0.5,
        subsurface=0.03,
    )
    strap = prism(STAGE, name, shape, 0.0, THICK - 0.02, leather, bevel=0.1, segments=6)
    return {}, [clad(strap, 0, 0, WIDTH, height)]


# Each tab: the height in rem of the paper tab (SiteShell's tabHeights), that paper's colour (the band of
# its strip), which lights the piece's edges from below, how the piece was set down (see stuck), and what
# builds it.
TABS = {
    "hamilton": (11, "#bfa391", (0.5, 0.0, 0.02), hamilton),
    "lacoste": (10, "#e3d3c1", (0.9, 0.02, -0.03), lacoste),
    "proraso": (10, "#7a8597", (-0.7, -0.02, 0.02), proraso),
    "apple": (10, "#1e2740", (0.5, 0.03, 0.03), apple),
    "prs": (10, "#d9d4c2", (-1.0, 0.0, -0.02), prs),
    "van": (11.5, "#8a8b78", (0.6, -0.03, 0.0), van),
}


def tab(name):
    height, paper, askew, build = TABS[name]
    stage_module.MAT = paper
    shot, pieces = build(f"tab-{name}", height)
    for piece in pieces:
        stuck(piece, height, askew)
    ceiling(height)
    STAGE.shoot(f"tab-{name}", (0, 0, WIDTH, height), bleed=MARGIN, shadow=0.9, sharp=2.0, **shot)


parser = argparse.ArgumentParser()
parser.add_argument("tabs", nargs="*")
parser.add_argument("--scale", type=float, default=1.0)
parser.add_argument("--samples", type=int, default=160)
parser.add_argument("--proofs")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
unknown = [name for name in args.tabs if name not in TABS]
if unknown:
    sys.exit(f"Unknown tabs: {', '.join(unknown)}. Known: {', '.join(TABS)}")
out_dir = os.path.join(ROOT, "public", "objects")
os.makedirs(out_dir, exist_ok=True)
if args.proofs:
    os.makedirs(args.proofs, exist_ok=True)
STAGE = Stage(out_dir, args.proofs, scale=args.scale, samples=args.samples)
for name in args.tabs or TABS:
    STAGE.clear()
    tab(name)
