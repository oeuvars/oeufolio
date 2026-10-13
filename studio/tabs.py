"""The folder tabs' plastic: five moulded pieces, one stuck on each paper tab, each for something I like
and carrying its maker's mark, the way stickers end up on everything a kid owns.

    proraso   Proraso's green under its own badge, and a chromed plate struck with Merkur's name as the
              foot of a Merkur razor is
    lacoste   the white piqué polo: the crocodile, the name, and tipping in its green and red
    prs       Blackstar's black tolex and cream piping, its name in raised white as on the amplifiers,
              and a pearl plate off a PRS fretboard with PRS's mark on it
    apple     platinum, with the six-colour apple let into it and the fine grooves of the cases of its time
    hamilton  Hamilton's khaki and its name, and a sticker over it of a Turkish Van asleep on her back

Uses the copy stand from the oeusume studio. Run from the repository root:

    blender -b --factory-startup -P studio/tabs.py -- [tab ...] [--scale 0.5] [--samples 64] [--proofs DIR]

Writes public/objects/tab-<name>.avif for each tab named, or for all five. Set OEUSUME if that checkout
is not in ~/Documents/oeusume.

The frame is the paper tab SiteShell cuts, in the page's own rem, so the render lies straight over it. The
plastic is cut to the paper's shape and is smaller, with paper left showing all round it, and it was
stuck down by hand, so none sits quite true. Each piece is a solid with a rounded edge. Its colours, its
marks and the texture moulded into it are painted as a sheet and laid over the solid from above.

The marks are the makers' own, from studio/assets/logos. The cat is drawn in studio/cat.svg.
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


def skin(sheet, name, **surface):
    """A sheet's painted surface as a material alone, for a solid to wear."""
    plane = sheet.build(STAGE, name, **surface)
    material = plane.data.materials[0]
    bpy.data.objects.remove(plane, do_unlink=True)
    # The solid has its own outline. The sheet's would fray it where the two meet.
    shader = material.node_tree.nodes["Principled BSDF"]
    for link in list(shader.inputs["Alpha"].links):
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


def struck(name, x0, y0, x1, y1, mark):
    """A chromed plate let into the plastic and standing a little proud of it. It is crowned like the cap
    of a razor, so it mirrors the room in a sweep, and the maker's name is struck into it as Merkur
    strikes its own into the foot of a razor: the letters are sunk, and the die leaves them dull."""
    w, h = x1 - x0, y1 - y0
    corner = 0.24
    sheet = Sheet(w, h, "#d6d6da", rough=0.03, density=3)
    X, Y = sheet.X, sheet.Y
    sheet.metal[:] = 1.0
    sheet.height -= 0.11 * ((X - w / 2) / (w / 2)) ** 2
    sheet.height -= 0.07 * (1 - np.clip(-box(X, Y, 0, 0, w, h, corner) / 0.45, 0, 1)) ** 2
    cover, _ = placed(sheet, mark, 0.34, 0.34, w - 0.34, h - 0.34, turn=1)
    # A die has clean edges, whatever the drawing of the mark was like.
    cover = ramp(0.3, 0.7, blur(cover, 2.2))
    sheet.press(blur(cover, 1.8), 0.026)
    sheet.finish(cover, rough=0.34)
    sheet.rgb *= (1 - 0.5 * cover)[..., None]
    # Plating is never flawless, and a razor is handled every morning.
    sheet.rough += 0.012 * np.clip(cloud(sheet.height.shape, 9, falloff=1.8), -2, 2)
    chrome = skin(
        sheet,
        f"{name}-chrome",
        wear=(("Scratches003", 3, 0.05, 0.0004), ("SurfaceImperfections003", 5, 0.05, 0)),
        specular=0.5,
    )
    plate = prism(STAGE, f"{name}-plate", rect(x0, y0, x1, y1, corner, 10), THICK - 0.08, THICK + 0.055, chrome, bevel=0.05, segments=5)
    return clad(plate, x0, y0, w, h)


def sticker(name, art, cx, cy, length, turn):
    """A vinyl sticker cut close round a drawing and pressed onto the plastic, its middle at cx, cy, the
    drawing `length` rem long and turned by `turn` degrees."""
    w, h = length * art.shape[1] / art.shape[0], length
    sheet = Sheet(w, h, "#fbf8f1", rough=0.2, density=3)
    cover, colour = placed(sheet, art, 0, 0, w, h)
    sheet.rgb += np.clip(cover * 4, 0, 1)[..., None] * (colour - sheet.rgb)
    sheet.opacity = cover
    sheet.coat[:] = 0.6
    # Vinyl has a thickness, and its cut edge rounds over.
    sheet.height += 0.014 * ramp(0.1, 0.9, blur(cover, 3.0))
    plane = sheet.build(
        STAGE,
        name,
        thickness=THICK + 0.02,
        wear=(("Scratches003", 4, 0.05, 0.0003), ("SurfaceImperfections003", 6, 0.06, 0)),
        specular=0.5,
        coat_rough=0.08,
        at=(cx - w / 2, cy - h / 2),
    )
    middle = Matrix.Translation((cx, -cy, 0))
    plane.matrix_world = middle @ Matrix.Rotation(math.radians(-turn), 4, "Z") @ middle.inverted()
    return plane


def proraso(name, sheet, edge, height):
    badge, colour = placed(sheet, artwork("logos/proraso"), MIDDLE - 1.24, 0.98, MIDDLE + 1.24, 5.3, turn=1)
    printed(sheet, badge, colour, rough=0.18, coat=0.7, proud=0.006)
    plate = struck(name, MIDDLE - 1.2, 5.72, MIDDLE + 1.2, 8.88, artwork("logos/merkur"))
    return {"card": 2.2}, [plate]


def lacoste(name, sheet, edge, height):
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
    return {}, []


def prs(name, sheet, edge, height):
    shape = sheet.height.shape
    top, foot = 5.0, 8.3
    piping = np.abs(edge + 0.3)
    plate = stripe(sheet, top, foot) * sheet.mask(0.47 + edge)
    rule = np.clip(stripe(sheet, top, top + 0.15) + stripe(sheet, foot - 0.15, foot), 0, 1) * plate
    bead = np.clip(1 - (piping / 0.045) ** 2, 0, 1)
    star, _ = placed(sheet, artwork("logos/blackstar"), MIDDLE - 0.36, 1.3, MIDDLE + 0.36, 4.62, turn=1)
    mark, _ = placed(sheet, artwork("logos/prs"), MIDDLE - 0.56, top + 0.36, MIDDLE + 0.56, foot - 0.36, turn=1)
    # Tolex: a pebbled grain pressed into the black, everywhere but the piping, the plate and the letters.
    grain = np.clip(blur(cloud(shape, 31, falloff=0.9), 1.6), -2, 2) + 0.5 * np.clip(cloud(shape, 32, falloff=1.5), -2, 2)
    bare = (1 - plate) * (1 - sheet.mask(piping - 0.065)) * (1 - np.clip(blur(star, 2.0) * 3, 0, 1))
    sheet.height += 0.006 * bare * grain
    sheet.rough += 0.05 * bare * np.clip(grain, -1, 1)
    # The piping stands proud as a rounded bead.
    sheet.paint(sheet.mask(piping - 0.045), "#e8dfc6")
    sheet.height += 0.02 * np.sqrt(bead)
    sheet.finish(sheet.mask(piping - 0.045), rough=0.3, coat=0.3)
    # Blackstar's name is moulded in white plastic and fixed to the front of the cabinet.
    printed(sheet, star, "#f1eee4", rough=0.22, coat=0.5, proud=0.022)
    # The plate is mother of pearl between two gold rules.
    inlay(sheet, plate, "#ece6d6", rough=0.1, coat=1.0)
    pearl = plate * (1 - rule)
    # Pearl is laid down in patches, each catching the light or missing it, and each throws back a
    # little colour of its own.
    figure = np.clip(streaks(shape, 61, 34, 13) + 0.7 * streaks(shape, 62, 12, 30), -2, 2) / 2
    sheet.paint(pearl * np.clip(figure, 0, 1) * 0.9, "#ffffff")
    sheet.paint(pearl * np.clip(-figure, 0, 1) * 0.55, "#a5a196")
    for seed, tint in ((63, "#eab4c4"), (64, "#a9dcc0"), (65, "#b3c9f0")):
        sheet.paint(pearl * np.clip(streaks(shape, seed, 26, 20), 0, 2) * 0.2, tint)
    sheet.paint(rule, "#d3a548")
    sheet.finish(rule, rough=0.22, metal=1.0, coat=0.0)
    # PRS's mark is cut into the pearl and filled with black.
    sheet.press(blur(mark, 1.0), 0.004)
    sheet.paint(mark, INK)
    sheet.finish(mark, rough=0.3, coat=0.4)
    return {"card": 1.6}, []


def apple(name, sheet, edge, height):
    Y = sheet.Y
    badge, colour = placed(sheet, artwork("logos/apple"), MIDDLE - 0.98, 1.35, MIDDLE + 0.98, 3.75)
    sheet.rgb += badge[..., None] * (colour - sheet.rgb)
    sheet.finish(badge, rough=0.12, coat=0.9)
    # The badge is let into the case, and sits in a shallow well of its own.
    sheet.press(blur(np.clip(badge * 2, 0, 1), 2.0), 0.006)
    # The fine parallel grooves that ran across the cases of its time.
    top, foot, pitch = 4.9, 8.5, 0.3
    line = ((Y - top) / pitch) % 1 - 0.5
    groove = np.exp(-((line * pitch / 0.045) ** 2))
    zone = stripe(sheet, top, foot) * ramp(0.32, 0.44, -edge)
    sheet.press(groove * zone, 0.03)
    sheet.rgb *= (1 - 0.12 * groove * zone)[..., None]
    return {}, []


def hamilton(name, sheet, edge, height):
    mark, _ = placed(sheet, artwork("logos/hamilton"), MIDDLE - 0.58, 1.1, MIDDLE + 0.58, 5.25, turn=1)
    printed(sheet, mark, INK, rough=0.3, coat=0.3)
    cat = sticker(f"{name}-cat", artwork("cat"), MIDDLE + 0.02, 7.95, 5.1, 4.0)
    return {}, [cat]


# Each piece: the height in rem of the paper tab it is stuck on (SiteShell's tabHeights) and that paper's
# colour (the band of its strip), which lights its edges from below; how it was set down (see stuck); the
# plastic's colour and roughness and how much clear gloss lies over it; what it carries; and how the
# plastic itself is finished.
TABS = {
    "proraso": (10, "#e3d3c1", (0.9, 0.02, -0.03), "#0a7440", 0.1, 0.7, proraso, {"subsurface": 0.04}),
    "lacoste": (10, "#7a8597", (-0.7, -0.02, 0.02), "#f1eee6", 0.3, 0.25, lacoste, {"subsurface": 0.08}),
    "prs": (10, "#b8946a", (0.5, 0.03, 0.03), "#121111", 0.3, 0.2, prs, {}),
    "apple": (10, "#d9d4c2", (-1.0, 0.0, -0.02), "#dcdcd8", 0.1, 0.8, apple, {"subsurface": 0.1}),
    "hamilton": (11.5, "#8a8b78", (0.6, -0.03, 0.0), "#978758", 0.26, 0.3, hamilton, {"subsurface": 0.03}),
}


def tab(name):
    height, paper, askew, colour, rough, coat, dress, surface = TABS[name]
    stage_module.MAT = paper
    sheet = Sheet(WIDTH, height, colour, rough=rough, density=3)
    sheet.coat[:] = coat
    shape = outline(height)
    edge = within(sheet.X, sheet.Y, shape)
    pillow(sheet, edge)
    shot, fitted = dress(f"tab-{name}", sheet, edge, height)
    # Moulded plastic is never one even shine: it flows a little as it cools, and it has been handled.
    sheet.rough += 0.025 * np.clip(cloud(sheet.height.shape, 5, falloff=2.0), -2, 2)
    sheet.height += 0.0012 * np.clip(cloud(sheet.height.shape, 6, falloff=2.4), -2, 2)
    plastic = skin(
        sheet,
        f"tab-{name}-skin",
        scan="Plastic010",
        scan_size=7,
        scan_normal=0.25,
        scan_rough=0.15,
        wear=(("Scratches003", 5, 0.05, 0.0005), ("SurfaceImperfections003", 8, 0.03, 0)),
        specular=0.5,
        coat_rough=0.06,
        **surface,
    )
    body = prism(STAGE, f"tab-{name}", shape, 0.0, THICK, plastic, bevel=EDGE, segments=7)
    clad(body, 0, 0, WIDTH, height)
    for piece in (body, *fitted):
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
