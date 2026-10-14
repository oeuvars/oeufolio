"""What is stuck on the folder tabs: six pieces, one on each paper tab, each for something I like and
carrying its maker's mark, the way stickers end up on everything a kid owns.

    tagheuer  the Carrera CBN2012's own strap: glossy dark brown alligator, padded and stitched in brown,
              through its steel folding clasp with the shield engraved in the cover
    proraso   Proraso's green under its own badge, clamped in the grip of a Merkur razor: chrome, knurled,
              with Merkur's mark struck into its collar
    lacoste   the white piqué polo: the crocodile, the name, and tipping in its green and red
    prs       a Blackstar Debut's colours: its cream tolex, with four of the outline birds PRS inlays down
              its fretboards let into it, abalone round rosewood, and a band of the amplifier's red grille
              cloth round it under Blackstar's badge
    apple     a Mac Studio's bead-blasted aluminium, with the six-colour apple let into it over the case's
              drilled grille
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

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix  # noqa: E402

import stage as stage_module  # noqa: E402
from paint import blur, box, cloud, linear, ramp, segment, streaks  # noqa: E402
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


def abalone(sheet, mask):
    """Abalone shell, as PRS cuts its birds from, at its darkest: the sea's green and blue in patches,
    lit and shadowed, with a little purple where they turn."""
    shape = sheet.height.shape
    sheet.paint(mask, "#4f9f92")
    figure = np.clip(streaks(shape, 61, 34, 13) + 0.7 * streaks(shape, 62, 12, 30), -2, 2) / 2
    sheet.paint(mask * np.clip(figure, 0, 1) * 0.55, "#a9e3d3")
    sheet.paint(mask * np.clip(-figure, 0, 1) * 0.6, "#174f55")
    for seed, tint, amount in ((81, "#0f7f6c", 0.7), (82, "#2c50b6", 0.6), (83, "#b24a8e", 0.4)):
        sheet.paint(mask * np.clip(streaks(shape, seed, 22, 14), 0, 2) * amount, tint)
    sheet.finish(mask, rough=0.08, coat=1.0)
    # It is cut and let in, so a hairline shows all round it.
    seam = np.clip(1 - np.abs(mask - 0.5) * 2, 0, 1)
    sheet.press(blur(seam, 1.2), 0.005)
    sheet.rgb *= (1 - 0.2 * blur(seam, 0.8))[..., None]


def moulded(name, height, colour, rough, coat, dress, density=3, **surface):
    """A piece of plastic cut to the paper tab. dress paints what it carries on its sheet, given the
    sheet and the distance in from the plastic's edge, and returns whatever else is fixed to it."""
    sheet = Sheet(WIDTH, height, colour, rough=rough, density=density)
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
    """A band off the front of a Blackstar Debut clamped round the piece: its oxblood grille cloth between
    two beads of cream piping, with the maker's badge on it, white letters on a black plate."""
    lap = 0.05
    x0, x1 = NEAR - lap, WIDTH - FAR + lap
    w, h = x1 - x0, y1 - y0
    sheet = Sheet(w, h, "#4a1612", rough=0.78, density=3)
    X, Y = sheet.X, sheet.Y
    # It is bent round the piece, so it falls away at each side.
    sheet.height -= 0.08 * (1 - np.clip(np.minimum(X, w - X) / 0.5, 0, 1)) ** 2
    piping = np.minimum(np.abs(Y - 0.16), np.abs(Y - (h - 0.16)))
    word, _ = placed(sheet, mark, 0.4, 0.5, w - 0.4, h - 0.5)
    lettered = np.argwhere(word > 0.1)
    (r0, c0), (r1, c1) = lettered.min(axis=0) / sheet.ppe, lettered.max(axis=0) / sheet.ppe
    badge = sheet.mask(box(X, Y, c0 - 0.15, r0 - 0.13, c1 + 0.15, r1 + 0.13, 0.07))
    # Grille cloth: threads woven over and under each other, the ones lying across a shade lighter.
    pitch = 0.095
    u, v = X / pitch, Y / pitch
    across = (np.floor(u) + np.floor(v)) % 2 == 0
    thread = np.where(across, np.cos(np.pi * (v % 1 - 0.5)), np.cos(np.pi * (u % 1 - 0.5)))
    woven = (1 - sheet.mask(piping - 0.07)) * (1 - np.clip(blur(badge, 1.5) * 2, 0, 1))
    sheet.paint(woven * across * thread * 0.9, "#b0625a")
    sheet.paint(woven * ~across * thread * 0.85, "#8a3f37")
    sheet.height += 0.013 * woven * thread
    sheet.paint(sheet.mask(piping - 0.05), "#f0dfc8")
    sheet.height += 0.022 * np.sqrt(np.clip(1 - (piping / 0.05) ** 2, 0, 1))
    sheet.finish(sheet.mask(piping - 0.05), rough=0.3, coat=0.3)
    printed(sheet, badge, "#17171a", rough=0.14, coat=0.8, proud=0.02)
    printed(sheet, word, "#f4f2ec", rough=0.2, coat=0.6, proud=0.012)
    cloth = skin(sheet, f"{name}-cloth", wear=(("SurfaceImperfections003", 6, 0.05, 0),), specular=0.4)
    band = prism(STAGE, f"{name}-amp", rect(x0, y0, x1, y1, 0.06, 4), 0.0, THICK + 0.05, cloth, bevel=0.045, segments=4)
    return clad(band, x0, y0, w, h)


def prs(name, height):
    def dress(sheet, edge):
        shape = sheet.height.shape
        # Four of PRS's outline birds, in the order the fretboard has them: the falcon at the third fret,
        # the harrier at the fifth, the tern at the ninth and Cooper's hawk at the twelfth. Each is cut as
        # an outline of shell, and the rosewood shows through the middle of it. Traced from photographs
        # of a 513's neck (legallyblindbirding.net), where the shell is white; here it is abalone.
        art = strewn(artwork("logos/prs-outline-birds"))
        birds = []
        for i, bird in enumerate(art):
            x = MIDDLE + (-0.55 if i % 2 == 0 else 0.55)
            y = 1.55 + 1.13 * i
            cover, colour = placed(sheet, bird, x - 0.8, y - 0.8, x + 0.8, y + 0.8)
            shell = cover * np.clip(colour[..., 0] * 1.6, 0, 1)
            birds.append((cover, shell, cover - shell))
        # Tolex: a fine leather grain pressed into the cream, everywhere but what is let into it.
        grain = np.clip(blur(cloud(shape, 31, falloff=0.9), 1.6), -2, 2) + 0.5 * np.clip(cloud(shape, 32, falloff=1.5), -2, 2)
        bare = 1 - np.clip(blur(np.max([cover for cover, _, _ in birds], axis=0), 2.0) * 3, 0, 1)
        sheet.height += 0.0045 * bare * grain
        sheet.rough += 0.05 * bare * np.clip(grain, -1, 1)
        sheet.rgb *= (1 - 0.03 * bare * np.clip(grain, -1, 1))[..., None]
        figure = np.clip(streaks(shape, 71, 40, 2), -2, 2) / 2
        for cover, shell, wood in birds:
            # The rosewood, dark and oiled, its grain running down the neck.
            inlay(sheet, wood, "#2c1713", rough=0.34, coat=0.3)
            sheet.paint(wood * np.clip(figure, 0, 1) * 0.5, "#4a2a20")
            sheet.paint(wood * np.clip(-figure, 0, 1) * 0.6, "#140a08")
            abalone(sheet, shell)
        return [amp(name, 6.1, 8.3, artwork("logos/blackstar"))]

    # The birds' outlines are fine, so the sheet is drawn finer than the others.
    return {"card": 1.2}, moulded(name, height, "#e6cdab", 0.4, 0.12, dress, density=7, subsurface=0.03)


def drill(case, centres, bore, sink, depth, material):
    """Drill real holes into a solid from above: each one countersunk, then bored down to a floor.
    The case keeps the cutter as a live boolean, so the holes go wherever the case is moved."""
    steps, top = 20, THICK
    bm = bmesh.new()
    profile = ((bore + sink + 0.05, top + 0.05), (bore, top - sink), (bore, top - depth))
    for cx, cy in centres:
        rings = [
            [bm.verts.new((cx + r * math.cos(2 * math.pi * i / steps), -cy + r * math.sin(2 * math.pi * i / steps), z)) for i in range(steps)]
            for r, z in profile
        ]
        for upper, lower in zip(rings, rings[1:]):
            for i in range(steps):
                j = (i + 1) % steps
                bm.faces.new((upper[i], upper[j], lower[j], lower[i]))
        bm.faces.new(rings[0])
        bm.faces.new(rings[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for face in bm.faces:
        face.smooth = True
    mesh = bpy.data.meshes.new(f"{case.name}-drill")
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    cutter = STAGE.add(f"{case.name}-drill", mesh)
    cutter.hide_render = True
    cutter.parent = case
    cut = case.modifiers.new("drill", "BOOLEAN")
    cut.operation = "DIFFERENCE"
    cut.object = cutter
    cut.solver = "EXACT"
    case.modifiers.move(len(case.modifiers) - 1, 0)
    return cutter


def apple(name, height):
    """A slab of a Mac Studio's case. It is milled from one block of aluminium, bead blasted to a fine
    even satin and anodised clear, so it shines softly and all of a piece. The milling leaves a chamfer
    round the top that is cut with a diamond, and that alone is bright as a mirror."""
    # Aluminium's own reflectance, a little dulled by the anodising.
    sheet = Sheet(WIDTH, height, "#e4e5e7", rough=0.3, density=8)
    X, Y = sheet.X, sheet.Y
    sheet.metal[:] = 1.0
    shape = outline(height)
    edge = within(X, Y, shape)
    # The face is milled flat. The chamfer is cut shallow, so it looks up at the light over the desk.
    chamfer = 0.11
    sheet.height -= 0.028 * np.clip(1 + edge / chamfer, 0, 1)
    sheet.finish(ramp(-chamfer - 0.012, -chamfer + 0.004, edge), rough=0.05)
    # The badge is enamel, fired in a pocket milled for it. It sets proud and a little domed, and glazed.
    badge, colour = placed(sheet, artwork("logos/apple"), MIDDLE - 0.98, 1.35, MIDDLE + 0.98, 3.75)
    sheet.rgb += badge[..., None] * (colour - sheet.rgb)
    sheet.finish(badge, rough=0.18, metal=0.0, coat=1.0)
    sheet.height += 0.012 * blur(badge, 6.0) * badge
    seam = np.clip(1 - np.abs(badge - 0.5) * 2, 0, 1)
    sheet.press(blur(seam, 1.0), 0.006)
    # The grille of a Mac Studio: round holes drilled close, each row half a step from the last.
    # Only whole holes are drilled, so the field stops clean inside the piece's edge.
    top, foot, pitch, bore, sink = 4.75, 8.6, 0.2, 0.062, 0.011
    centres = []
    for row in range(int(top / (pitch * 0.866)) + 1, int(foot / (pitch * 0.866)) + 1):
        for col in range(int(WIDTH / pitch) + 1):
            cx, cy = (col + 0.5 * (row % 2)) * pitch, row * pitch * 0.866
            if top < cy < foot and within(np.array([cx]), np.array([cy]), shape)[0] < -0.42:
                centres.append((cx, cy))
    for cx, cy in centres:
        rows, cols = sheet.window(cx - 0.12, cy - 0.12, cx + 0.12, cy + 0.12)
        reach = np.hypot(X[rows, cols] - cx, Y[rows, cols] - cy)
        # The drill leaves only a hairline of bright chamfer. Down the bore is the dark inside of the case.
        lip = sheet.mask(reach - bore - sink - 0.003) - sheet.mask(reach - bore - 0.002)
        sheet.rough[rows, cols] += lip * (0.08 - sheet.rough[rows, cols])
        floor = sheet.mask(reach - bore + 0.003)
        sheet.rgb[rows, cols] += floor[..., None] * (linear("#030303") - sheet.rgb[rows, cols])
        sheet.metal[rows, cols] *= 1 - floor
        sheet.rough[rows, cols] += floor * (0.95 - sheet.rough[rows, cols])
    # Bead blasting is even, but never perfectly: the satin drifts a touch, and a hand has held it.
    sheet.rough += 0.025 * np.clip(cloud(sheet.height.shape, 7, falloff=2.0), -2, 2)
    aluminium = skin(
        sheet,
        f"{name}-aluminium",
        wear=(("Fingerprints009", 6, 0.08, 0), ("SurfaceImperfections003", 7, 0.04, 0), ("Scratches003", 5, 0.03, 0.0002)),
        # The blasting's grain, each bead a dent too small to see alone, and seen all together as satin.
        fibre=0.001,
        fibre_scale=110,
        specular=0.5,
        coat_rough=0.04,
    )
    case = clad(prism(STAGE, name, shape, 0.0, THICK, aluminium, bevel=0.035, segments=3), 0, 0, WIDTH, height)
    clad(drill(case, centres, bore, sink, 0.16, aluminium), 0, 0, WIDTH, height)
    return {"card": 1.4}, [case]


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


def shield(X, Y, cx, top, w):
    """TAG Heuer's shield, as it is engraved on the brand's steel: square shoulders, sides that run down
    and then close to a shallow point, and a rule across it where the name's two words divide. Returns
    the depth of the cut at each point, deepest on the lines."""
    h = 1.08 * w
    left, right, waist = cx - w / 2, cx + w / 2, top + 0.66 * h
    outline = [(left, top), (right, top), (right, waist), (cx, top + h), (left, waist)]
    line = np.exp(-((within(X, Y, outline) / (0.018 * w / 0.9)) ** 2))
    rule = top + 0.4 * h
    across = segment(X, Y, left + 0.06 * w, rule + 0.02 * w, right - 0.06 * w, rule - 0.02 * w)
    return np.maximum(line, np.exp(-((across / (0.016 * w / 0.9)) ** 2)) * (within(X, Y, outline) < 0))


def clasp(name, left, right, top, bottom, point):
    """The cover of TAG Heuer's folding clasp, laid over the strap where it closes: one piece of steel,
    its top polished, its sides chamfered and brushed, its foot cut to a point like the shield it carries.
    A push-button stands out of each side."""
    x0, x1 = left - 0.1, right + 0.1
    w, h = x1 - x0, point - top
    middle = (x0 + x1) / 2
    outline = [(x0, top), (x1, top), (x1, bottom), (middle, point), (x0, bottom)]
    sheet = Sheet(w, h, "#e9eaeb", rough=0.035, density=8)
    X, Y = sheet.X, sheet.Y
    shape = sheet.height.shape
    sheet.metal[:] = 1.0
    local = [(x - x0, y - top) for x, y in outline]
    edge = within(X, Y, local)
    # The top is polished to a mirror, and crowned enough that what it mirrors sweeps across it.
    sheet.height -= 0.06 * ((X - w / 2) / (w / 2)) ** 2
    # The chamfers are brushed along their length, so each one is a satin band of fine parallel lines.
    chamfer = ramp(-0.16, -0.12, edge)
    gy, gx = np.gradient(edge)
    across = np.abs(gy) / np.maximum(np.hypot(gx, gy), 1e-9)
    lines = across * streaks(shape, 43, 60, 0.5) + (1 - across) * streaks(shape[::-1], 44, 60, 0.5).T
    lines = np.clip(lines / max(lines.std(), 1e-9), -2.5, 2.5)
    sheet.finish(chamfer, rough=0.2)
    sheet.rough += chamfer * 0.06 * lines
    sheet.height += chamfer * 0.0006 * lines
    sheet.rgb *= (1 + chamfer * 0.04 * lines)[..., None]
    cut = shield(X, Y, w / 2, 0.3, 0.92)
    sheet.press(cut, 0.016)
    sheet.finish(cut, rough=0.35)
    sheet.rgb *= (1 - 0.4 * cut)[..., None]
    # Polish is never perfect: a faint haze in places, and the hairlines of being worn.
    sheet.rough += 0.01 * np.clip(cloud(shape, 41, falloff=1.4), 0, 2) * (1 - chamfer)
    steel = skin(
        sheet,
        f"{name}-steel",
        wear=(("Fingerprints009", 4, 0.02, 0),),
        specular=0.5,
    )
    cover = clad(prism(STAGE, f"{name}-clasp", outline, 0.04, THICK + 0.1, steel, bevel=0.14, segments=2), x0, top, w, h)
    pusher = principled(f"{name}-pusher", "#e2e3e4", rough=0.06, metal=1.0)
    buttons = [
        prism(STAGE, f"{name}-pusher-{side}", rect(x - 0.1, top + 0.32, x + 0.1, top + 0.86, 0.08, 6), 0.08, THICK - 0.02, pusher, bevel=0.05, segments=3)
        for side, x in (("left", x0 - 0.03), ("right", x1 + 0.03))
    ]
    return [cover, *buttons]


def lit(cx, cy, bands):
    """Strip lights over the set that only a reflection sees: no light from them falls on anything, and
    the camera cannot see them. Polished steel shows what is round it, and under one even card it can
    only be one even grey. A watch is lit for its photograph with long strips, so its steel carries
    bright bands with dark between them, and so does this. bands is (offset across, width, strength)."""
    for i, (across, width, strength) in enumerate(bands):
        panel = bpy.data.meshes.new(f"strip-{i}")
        panel.from_pydata([(-width / 2, -30, 0), (width / 2, -30, 0), (width / 2, 30, 0), (-width / 2, 30, 0)], [], [(0, 1, 2, 3)])
        glow = bpy.data.materials.new(f"strip-{i}")
        glow.use_nodes = True
        nodes = glow.node_tree.nodes
        nodes.clear()
        emit = nodes.new("ShaderNodeEmission")
        emit.inputs["Strength"].default_value = strength
        out = nodes.new("ShaderNodeOutputMaterial")
        glow.node_tree.links.new(emit.outputs[0], out.inputs["Surface"])
        panel.materials.append(glow)
        strip = STAGE.add(f"strip-{i}", panel)
        strip["stand"] = "room"
        strip.location = (cx + across, cy, 30)
        for seen in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission", "visible_volume_scatter"):
            setattr(strip, seen, False)


def hide(rows):
    """A length of the FC6483's hide, from TAG Heuer's own photograph of the strap, taken square on above
    and below the watch's case (studio/assets/tagheuer, each drawn out to the strap's width row by row).
    The photograph holds less strap than the tab does, so the two pieces are laid end to end and then
    again turned over side to side, each join feathered."""
    top, bottom = artwork("tagheuer/strap-top")[..., :3], artwork("tagheuer/strap-bottom")[..., :3]
    pieces = [top, bottom, top[:, ::-1], bottom[:, ::-1]]
    feather = 24
    out = pieces[0]
    for piece in pieces[1:]:
        if out.shape[0] >= rows:
            break
        fade = np.linspace(0, 1, feather)[:, None, None]
        joined = out[-feather:] * (1 - fade) + piece[:feather] * fade
        out = np.concatenate([out[:-feather], joined, piece[feather:]])
    return out[:rows]


def tagheuer(name, height):
    """TAG Heuer's own strap for the Carrera chronograph CBN2012 (FC6483): dark brown alligator, its big
    scales down the middle and smaller ones at the sides, polished to a gloss, padded high, stitched in a
    brown only a little lighter than the hide. Cut to the paper tab's shape, as the plastic pieces are,
    and closed across by the steel folding clasp it is sold with."""
    shape = outline(height)
    across, stretch = WIDTH - FAR - NEAR, 1.25
    top, foot = HEAD, height - HEAD
    sheet = Sheet(WIDTH, height, "#3a1d17", rough=0.3, density=6)
    X, Y = sheet.X, sheet.Y
    edge = within(X, Y, shape)
    rows, cols = sheet.window(NEAR, top, WIDTH - FAR, foot)
    h, w = sheet.rgb[rows, cols].shape[:2]
    per_em = 420 / across
    photo = hide(round((foot - top) * per_em / stretch))
    tone = np.clip(fit(photo, h, w), 0, 1)
    sheet.rgb[rows, cols] = np.where(tone <= 0.04045, tone / 12.92, ((tone + 0.055) / 1.055) ** 2.4)
    # The photograph has the hide's relief in it: its creases are its darkest lines. Pressed in, they
    # catch this room's light as well as the one it was photographed in.
    lum = sheet.rgb.mean(axis=-1)
    detail = lum - blur(lum, 8.0)
    sheet.height += 0.006 * np.clip(detail / max(detail.std(), 1e-6), -3, 3) / 3
    # Padded: it stands highest down its middle and rolls down to its edges.
    sheet.height -= 0.1 * (1 - np.clip(-edge / 0.6, 0, 1)) ** 2
    sheet.rough[:] = 0.42
    sheet.coat[:] = 0.06
    leather = skin(sheet, f"{name}-alligator", specular=0.15, coat_rough=0.2)
    strap = clad(prism(STAGE, name, shape, 0.0, THICK - 0.02, leather, bevel=0.1, segments=6), 0, 0, WIDTH, height)
    # The clasp closes over the first join in the hide.
    lock = top + 282 * stretch / per_em - 0.75
    lit(WIDTH / 2, -height / 2, ((-3.2, 1.6, 7.0), (-1.2, 0.35, 3.0), (2.6, 0.9, 4.0)))
    return {"card": 0.5}, [strap, *clasp(name, NEAR + 0.12, WIDTH - FAR - 0.12, lock, lock + 1.85, lock + 2.35)]


# Each tab: the height in rem of the paper tab (SiteShell's tabHeights), that paper's colour (the band of
# its strip), which lights the piece's edges from below, how the piece was set down (see stuck), and what
# builds it.
TABS = {
    "tagheuer": (11, "#bfa391", (0.5, 0.0, 0.02), tagheuer),
    "lacoste": (10, "#e3d3c1", (0.9, 0.02, -0.03), lacoste),
    "proraso": (10, "#d9d4c2", (-0.7, -0.02, 0.02), proraso),
    "apple": (10, "#1e2740", (0.5, 0.03, 0.03), apple),
    "prs": (10, "#7a8597", (-1.0, 0.0, -0.02), prs),
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
