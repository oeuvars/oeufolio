"""What is stuck on the folder tabs: five pieces, one on each page's paper tab, each for something I like and
carrying its maker's mark, the way stickers end up on everything a kid owns.

    tagheuer  the Carrera CBN2012's own strap: glossy dark brown alligator, padded and stitched in brown,
              through its steel folding clasp with the shield engraved in the cover
    proraso   Proraso's green under its own badge, clamped in the grip of a Merkur razor: chrome, knurled,
              with Merkur's mark struck into its collar
    lacoste   a cut off a burgundy knit polo, hemmed: the embroidered crocodile, and the collar's rib knit with ecru and
              gold tipping
    prs       a Blackstar Debut's tolex in a PRS Silver Sky's Sandglow Yellow, with four of the outline birds PRS
              inlays down its fretboards let into it one under another, mother-of-pearl in rosewood, and a band off the
              front of a Blackstar ID:Core in red round it: its black grille cloth between edges of its wine tolex,
              under Blackstar's badge
    teenage   a Mac Studio's bead-blasted aluminium, with teenage engineering's bolt and nut let into it over
              the case's drilled grille

Uses the copy stand in studio/desk. Run from the repository root:

    blender -b --factory-startup -P studio/tabs.py -- [tab ...] [--scale 0.5] [--samples 64] [--proofs DIR]

Writes public/objects/tab-<name>.avif for each tab named, or for all five. The render is four times as fine as the
page shows it, for the detail; bring it down to what the page can use after:

    uv run studio/fit.py --width 296 public/objects/tab-<name>.avif

The frame is the paper tab SiteShell cuts, in the page's own rem, so the render lies straight over it. A
piece is smaller than the paper, with paper left showing all round it, and it was stuck down by hand, so
none sits quite true. Each is a solid with a rounded edge, and the plastic ones are cut to the paper's
shape. A piece's colours, its marks and the texture of its surface are painted as a sheet and laid over
the solid from above.

The marks are the makers' own, from studio/assets/logos.
"""

import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "desk"))

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix  # noqa: E402

import stage as stage_module  # noqa: E402
from paint import blur, cloud, linear, ramp, segment, streaks  # noqa: E402
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


def nacre(sheet, mask):
    """Mother-of-pearl, as PRS cuts its outline birds from: a cream white with a faint grain running
    through it, and a sheen of pink and green where the light catches its layers."""
    shape = sheet.height.shape
    sheet.paint(mask, "#ece6d0")
    figure = np.clip(streaks(shape, 61, 18, 5) + 0.6 * streaks(shape, 62, 7, 12), -2, 2) / 2
    sheet.paint(mask * np.clip(figure, 0, 1) * 0.5, "#fbf8ec")
    sheet.paint(mask * np.clip(-figure, 0, 1) * 0.35, "#cfc6aa")
    for seed, tint, amount in ((81, "#e9d3d6", 0.35), (82, "#d3e4d6", 0.3)):
        sheet.paint(mask * np.clip(streaks(shape, seed, 12, 9), 0, 2) * amount, tint)
    sheet.finish(mask, rough=0.1, coat=1.0)
    # It is cut and let in, so a hairline shows all round it.
    seam = np.clip(1 - np.abs(mask - 0.5) * 2, 0, 1)
    sheet.press(blur(seam, 1.0), 0.004)
    sheet.rgb *= (1 - 0.25 * blur(seam, 0.7))[..., None]


def moulded(name, height, colour, rough, coat, dress, density=3, scan=("Plastic010", 7, 0.25, 0.15), relief=0.0, **surface):
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
    # The piece's relief is its own geometry: the crowned face, what is printed and let in, the scan's grain where it
    # has one worth seeing, and the top edge rounded as the moulding is. The surface over it carries none of it again.
    if relief:
        sheet.height += scanned(sheet, scan[0], scan[1], relief)
        scan = (scan[0], scan[1], scan[2] * 0.3, scan[3])
    sheet.height -= rounded(edge, EDGE)
    heights = sheet.height.copy()
    sheet.height[:] = 0.0
    plastic = skin(
        sheet,
        f"{name}-skin",
        scan=scan[0],
        scan_size=scan[1],
        scan_normal=scan[2],
        scan_rough=scan[3],
        wear=(("Scratches003", 5, 0.05, 0.0005), ("SurfaceImperfections003", 8, 0.03, 0)),
        specular=0.5,
        coat_rough=0.06,
        **surface,
    )
    sheet.height = heights
    return [displaced(name, sheet, edge, THICK, plastic, step=steps(sheet)), *fitted]


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
    sheet = Sheet(w, h, "#d6d6da", rough=0.03, density=4)
    X, Y = sheet.X, sheet.Y
    sheet.metal[:] = 1.0
    collar_edge = within(X, Y, fillet([(0, 0, 0.05), (w, 0, 0.05), (w, h, 0.05), (0, h, 0.05)], steps=6))
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
    # The knurl's pyramids, the grooves and the struck mark are the collar's own geometry, and its edges are rounded.
    sheet.height -= rounded(collar_edge, 0.045)
    heights = sheet.height.copy()
    sheet.height[:] = 0.0
    chrome = skin(
        sheet,
        f"{name}-chrome",
        wear=(("Scratches003", 3, 0.05, 0.0004), ("SurfaceImperfections003", 5, 0.05, 0)),
        specular=0.5,
    )
    sheet.height = heights
    return displaced(f"{name}-grip", sheet, collar_edge, THICK + 0.05, chrome, step=1, at=(x0, y0))


def proraso(name, height):
    def dress(sheet, edge):
        badge, colour = placed(sheet, artwork("logos/proraso"), MIDDLE - 1.04, 0.98, MIDDLE + 1.04, 4.82, turn=1)
        printed(sheet, badge, colour, rough=0.18, coat=0.7, proud=0.006)
        inlay(sheet, stripe(sheet, 5.2, 5.4), "#f2ecd9")
        inlay(sheet, stripe(sheet, 5.5, 5.59), "#c5222b")
        return [grip(name, 5.9, 8.56, artwork("logos/merkur"))]

    return {"card": 2.2}, moulded(name, height, "#0a7440", 0.1, 0.7, dress, density=5, subsurface=0.04)


def fill_holes(solid):
    """A mask with its holes filled: whatever of the clear part cannot be reached from the border is filled."""
    outside = np.zeros_like(solid)
    outside[0, :], outside[-1, :], outside[:, 0], outside[:, -1] = ~solid[0, :], ~solid[-1, :], ~solid[:, 0], ~solid[:, -1]
    while True:
        grown = outside.copy()
        grown[1:] |= outside[:-1]
        grown[:-1] |= outside[1:]
        grown[:, 1:] |= outside[:, :-1]
        grown[:, :-1] |= outside[:, 1:]
        grown &= ~solid
        if (grown == outside).all():
            return ~outside
        outside = grown


def scanned(sheet, asset, size, depth, kind="Displacement"):
    """A scanned material's own relief (its displacement map), repeating every size rem over the sheet, depth rem from
    its lowest to its highest, about zero."""
    disp = pixels_of(os.path.join(stage_module.ASSETS, asset, f"{asset}_1K-JPG_{kind}.jpg"))[..., :3].mean(axis=-1).astype(np.float64)
    rows, cols = disp.shape
    fy, fx = (sheet.Y / size * rows) % rows, (sheet.X / size * cols) % cols
    r0, c0 = np.floor(fy).astype(int), np.floor(fx).astype(int)
    r1, c1 = (r0 + 1) % rows, (c0 + 1) % cols
    ty, tx = fy - r0, fx - c0
    d = (disp[r0, c0] * (1 - tx) + disp[r0, c1] * tx) * (1 - ty) + (disp[r1, c0] * (1 - tx) + disp[r1, c1] * tx) * ty
    return depth * (d - d.mean())


def rounded(edge, radius):
    """How far a top edge rounded to radius falls, at each distance in from it: a quarter circle."""
    out = np.clip(1 - np.clip(-edge, 0, None) / radius, 0, 1)
    return radius * (1 - np.sqrt(np.clip(1 - out * out, 0, 1)))


def displaced(name, sheet, edge, top, material, step=2, at=(0.0, 0.0), base=0.0, plumb=False):
    """A solid whose top is the sheet's height map as real geometry, standing top rem high, cut to where edge is
    negative: its relief catches the light and throws its own small shadows, as a bump map laid on a flat face
    cannot. The sheet's height is spent on the geometry, so the surface that dresses it carries none of it again."""
    h = (top + sheet.height)[::step, ::step]
    inside = (edge < 0)[::step, ::step]
    X, Y = sheet.X[::step, ::step] + at[0], sheet.Y[::step, ::step] + at[1]
    rows, cols = h.shape
    index = np.arange(rows * cols).reshape(rows, cols)
    corners = (index[1:, :-1], index[1:, 1:], index[:-1, 1:], index[:-1, :-1])
    live = inside[1:, :-1] & inside[1:, 1:] & inside[:-1, 1:] & inside[:-1, :-1]
    faces = np.column_stack([corner[live] for corner in corners])
    used, faces = np.unique(faces, return_inverse=True)
    # The grid's own outline steps from square to square. The vertices along it are moved out onto the true outline,
    # down the slope of the distance to it, so the piece's edge runs smooth and not in stairs.
    gy, gx = np.gradient(edge, 1 / sheet.ppe)
    gx, gy = gx[::step, ::step].ravel(), gy[::step, ::step].ravel()
    d = edge[::step, ::step].ravel()
    near = d > -1.5 * step / sheet.ppe
    slope = np.maximum(gx * gx + gy * gy, 1e-9)
    xs, ys = X.ravel().copy(), Y.ravel().copy()
    xs[near] -= (d * gx / slope)[near]
    ys[near] -= (d * gy / slope)[near]
    verts = np.column_stack((xs, -ys, h.ravel()))[used]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts.tolist(), [], faces.reshape(-1, 4).tolist())
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.materials.append(material)
    body = STAGE.add(name, mesh)
    if plumb:
        # Walls straight down from the outline to base, for a top that falls steeply at its edge, where walls grown
        # along its normals would splay out sideways.
        bm = bmesh.new()
        bm.from_mesh(mesh)
        rim = [e for e in bm.edges if e.is_boundary]
        grown = bmesh.ops.extrude_edge_only(bm, edges=rim)
        for v in grown["geom"]:
            if isinstance(v, bmesh.types.BMVert):
                v.co.z = base
        bm.to_mesh(mesh)
        bm.free()
        return clad(body, at[0], at[1], sheet.w, sheet.h)
    # Walls down to the page.
    walls = body.modifiers.new("walls", "SOLIDIFY")
    walls.thickness = float(top - base)
    walls.offset = -1
    walls.use_even_offset = False
    return clad(body, at[0], at[1], sheet.w, sheet.h)


def steps(sheet):
    """How many of the sheet's pixels to a vertex, for a mesh of about a hundred and sixty vertices to the rem: fine enough for
    any relief here, light enough to render beside the other studio jobs on one card."""
    return max(1, round(sheet.ppe / 160))


# The knit's scan: rem to its tile, and the stitch columns and rows in a tile (measured from its relief).
RIB_KNIT, RIB_WALES, RIB_COURSES = 8.3, 139, 153


def lacoste(name, height):
    """A cut off a burgundy Lacoste polo, hemmed and stitched to the tab: the cloth is knit stitch by stitch, the same
    stitches all over; the crocodile is the embroidered badge sewn on at the chest, its thread raised and running
    across the body in satin stitch; and at its foot is the collar's rib, tipped in ecru and gold."""
    sheet = Sheet(WIDTH, height, BURGUNDY, rough=0.92, density=6)
    sheet.coat[:] = 0.0
    shape = outline(height)
    edge = within(sheet.X, sheet.Y, shape)
    X, Y = sheet.X, sheet.Y
    # The hem: the cloth turned under all round, so its edge is a soft roll, and a row of stitches holds it in.
    roll = 0.16
    sheet.height -= 0.05 * (1 - np.clip(-edge / roll, 0, 1)) ** 2
    stitch_line = np.abs(edge + 0.2) < 0.012
    along = np.arctan2(Y - height / 2, X - MIDDLE) * 40
    stitches = stitch_line & (np.sin(along) > -0.2)
    sheet.press(blur(stitches.astype(float), 1.2), 0.006)
    sheet.paint(blur(stitches.astype(float), 0.8) * 0.5, "#3a1219")

    # The knit, all over. Its stitches are a photograph's, a real knit's (Poly Haven's Knitted Fleece, CC0): its relief
    # and the light and dark of its yarn, at a fine gauge, a stitch column about six tenths of a millimetre across.
    stitch = scanned(sheet, "KnittedFleece", RIB_KNIT, 1.0)
    stitch /= max(stitch.std(), 1e-6)
    yarn = np.clip(1 + 0.22 * scanned(sheet, "KnittedFleece", RIB_KNIT, 1.0, kind="Color") / 0.12, 0.55, 1.4)
    sheet.height += 0.007 * np.clip(stitch, -2.5, 2.5)
    sheet.rough += 0.04 * np.clip(stitch, -1, 1)

    # The collar's rib at the foot: the same stitches, with every other column standing a little proud, as a 1x1 rib's
    # do. The tipping is the same stitches in other yarn: its rows run along the knit, so where a stripe starts and
    # stops the Vs of the two yarns interlock.
    rib0, rib1 = height - 2.4, height - 0.62
    rib = sheet.mask(np.abs(Y - (rib0 + rib1) / 2) - (rib1 - rib0) / 2)
    ribbing = np.cos(np.pi * X / (RIB_KNIT / RIB_WALES))
    sheet.height += rib * (0.006 * ribbing - 0.008)
    seam = np.clip(1 - np.abs(np.abs(Y - (rib0 + rib1) / 2) - (rib1 - rib0) / 2) / 0.03, 0, 1)
    sheet.press(blur(seam, 1.0), 0.012)
    course = RIB_KNIT / RIB_COURSES
    wobble = 0.35 * course * np.clip(stitch, -2, 2)
    for top, rows, colour in ((6, 3, ECRU), (11, 1, GOLD)):
        y0, y1 = rib0 + top * course, rib0 + (top + rows) * course
        tipped = rib * ramp(y0 - 0.15 * course, y0 + 0.15 * course, Y + wobble) * ramp(-y1 - 0.15 * course, -y1 + 0.15 * course, -(Y - wobble))
        sheet.paint(tipped, colour)
    # Every yarn is lit and shaded by its own stitches.
    sheet.rgb *= yarn[..., None]

    # The crocodile, embroidered on a badge of the same knit: raised thread, the satin stitch's lines running
    # across it at a slant, sheened where the thread catches the light.
    _, crocodile = parted(artwork("logos/lacoste"))
    croc, colour = placed(sheet, crocodile, MIDDLE - 1.0, 1.05, MIDDLE + 1.0, 2.55)
    # The mark's scales and teeth are see-through in the artwork; on the badge they are white thread.
    whole = blur(fill_holes(croc > 0.5).astype(float), 0.8)
    white = np.clip(whole - croc, 0, 1)
    satin = 0.5 + 0.5 * np.sin(2 * np.pi * (X * 0.5 + Y) / 0.035)
    thread = np.clip(blur(whole, 1.2) * 1.4, 0, 1)
    sheet.rgb += croc[..., None] * (colour - sheet.rgb)
    sheet.paint(white, "#f2efe6")
    sheet.rgb *= (1 - 0.12 * thread * (1 - satin))[..., None]
    sheet.height += 0.05 * thread + 0.006 * thread * satin
    sheet.finish(whole, rough=0.42)
    # Cloth never lies quite flat: it rises and sinks where it was pressed down by hand, and keeps a soft crease
    # across it where it was folded.
    sheet.height += 0.03 * np.clip(blur(cloud(sheet.height.shape, 41, falloff=2.6), 12.0), -2, 2)
    crease = np.exp(-(((Y - 0.42 * X - 4.6) / 0.35) ** 2))
    sheet.height += 0.06 * crease - 0.025 * np.exp(-(((Y - 0.42 * X - 4.25) / 0.2) ** 2))
    sheet.height -= rounded(edge, 0.05)
    relief = sheet.height.copy()
    sheet.height[:] = 0.0
    cloth = skin(sheet, f"{name}-knit", sheen=0.7, specular=0.3)
    sheet.height = relief
    return {"ceiling": False}, [displaced(name, sheet, edge, 0.1, cloth, step=steps(sheet))]


def relief(name, height, x0, y0, w, h, z0, material):
    """A solid raised from a height map, rows from the top, laid over x0..x0+w, y0..y0+h in rem and
    standing on z0. Only where the map stands up is there anything, so the map's outline is the solid's,
    and its slopes are the solid's walls."""
    rows, cols = height.shape
    gx, gy = np.meshgrid(x0 + (np.arange(cols) + 0.5) * w / cols, y0 + (np.arange(rows) + 0.5) * h / rows)
    verts = np.column_stack((gx.ravel(), -gy.ravel(), z0 + height.ravel()))
    index = np.arange(rows * cols).reshape(rows, cols)
    corners = (index[1:, :-1], index[1:, 1:], index[:-1, 1:], index[:-1, :-1])
    live = np.min([height[1:, :-1], height[1:, 1:], height[:-1, 1:], height[:-1, :-1]], axis=0) > 0.002
    faces = np.column_stack([corner[live] for corner in corners])
    used, faces = np.unique(faces, return_inverse=True)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts[used].tolist(), [], faces.reshape(-1, 4).tolist())
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.materials.append(material)
    return clad(STAGE.add(name, mesh), x0, y0, w, h)


def badge(name, mark, cx, cy, wide, z0):
    """Blackstar's badge as it is fixed to the amplifier's grille: the name in raised white letters on a black
    plate die-cut an even margin round them, standing proud of the cloth."""
    tall = wide * mark.shape[0] / mark.shape[1]
    pad = 0.07 * tall / 0.3
    w, h = wide + 2 * pad, tall + 2 * pad
    x0, y0 = cx - w / 2, cy - h / 2
    sheet = Sheet(w, h, "#0d0d0f", rough=0.22, density=5)
    letters, _ = placed(sheet, mark, pad, pad, w - pad, h - pad)
    # The plate is cut round the letters a fixed margin out, as a badge is die-cut: an even black outline round the
    # whole word, its counters and the gaps between letters filled, its edge crisp and square to the face.
    grown = fill_holes(blur(letters, 0.03 * sheet.ppe) > 0.025)
    plate = np.clip(blur(grown.astype(np.float64), 0.004 * sheet.ppe) * 1.6 - 0.3, 0, 1)
    face = np.clip(blur(letters, 0.004 * sheet.ppe), 0, 1)
    sheet.paint(face, "#efeeea")
    sheet.finish(face, rough=0.32, coat=0.25)
    # A satin black, so it reads as black under the open studio and does not mirror the room as a grey haze.
    sheet.finish(plate * (1 - face), rough=0.38, coat=0.2)
    # Only the shading of the solid itself: the map below is the solid, not a bump laid on it.
    sheet.height[:] = 0.0
    finish = skin(sheet, f"{name}-badge", specular=0.5)
    return relief(f"{name}-badge", 0.035 * plate + 0.03 * face, x0, y0, w, h, z0 - 0.001, finish)


def amp(name, y0, y1, mark):
    """A band off the front of a Blackstar ID:Core in red wrapped round the piece: its black grille cloth, from a
    photograph of the amplifier's own (studio/assets/blackstar/grille-black), between two edges of its wine tolex,
    with the maker's badge on it. It is one piece, following the piece's face and coming down over its sides."""
    # Exactly as wide as the piece, so it ends where the piece's rounded edge does and turns down its side unseen.
    x0, x1 = NEAR, WIDTH - FAR
    w, h = x1 - x0, y1 - y0
    sheet = Sheet(w, h, "#2c2a29", rough=0.85, density=6)
    X = sheet.X
    # The photograph at the amplifier's own scale, where its badge (305 pixels across there) is as wide as the one here.
    wide = 2.3
    per_rem = 305 / wide
    cloth = artwork("blackstar/grille-black")[..., :3]
    rows, cols = round(h * per_rem), round(w * per_rem)
    r0, c0 = (cloth.shape[0] - rows) // 2, (cloth.shape[1] - cols) // 2
    tone = np.clip(fit(cloth[r0 : r0 + rows, c0 : c0 + cols], *sheet.height.shape), 0, 1)
    sheet.rgb[:] = decoded(tone)
    # The threads stand where the photograph is light and the weave sinks where it is dark.
    lum = tone.mean(axis=-1)
    weave = lum - blur(lum, 0.06 * sheet.ppe)
    sheet.height += 0.012 * np.clip(weave / max(weave.std(), 1e-6), -2.5, 2.5) / 2.5
    sheet.rough += 0.08 * np.clip(-weave / max(weave.std(), 1e-6), 0, 2)
    Y = sheet.Y
    # The cabinet's tolex, a fine-grained vinyl in the ID:Core's wine red, folded over the cloth's top and foot. It is
    # a little thicker than the cloth and its folded lip is rounded, so it stands clean of the weave.
    edging = 0.26
    tolex = np.clip(ramp(edging + 0.004, edging - 0.004, Y) + ramp(h - edging - 0.004, h - edging + 0.004, Y), 0, 1)
    from_fold = np.minimum(np.abs(Y - edging), np.abs(Y - (h - edging)))
    sheet.rgb += tolex[..., None] * (linear(WINE) - sheet.rgb)
    sheet.finish(tolex, rough=0.5, coat=0.15)
    grain = 0.0015 * np.clip(scanned(sheet, "Leather025", 6, 1.0) / 0.05, -1, 1)
    sheet.height += tolex * (0.014 + grain - rounded(-from_fold, 0.012) - sheet.height)
    # It is wrapped round the piece: it follows the piece's face, crowned and rounded at its edges, a little thicker
    # than the cloth, and turns straight down the piece's sides where they do.
    inside = np.minimum(X, w - X)
    face = THICK - CROWN * (1 - np.clip(inside / SHOULDER, 0, 1)) ** 2 - rounded(-inside, EDGE)
    sheet.height += face + 0.03
    outline_ = within(X, Y, fillet([(0, 0, 0.03), (w, 0, 0.03), (w, h, 0.03), (0, h, 0.03)], steps=6))
    heights = sheet.height.copy()
    sheet.height[:] = 0.0
    fabric = skin(sheet, f"{name}-cloth", sheen=0.4, specular=0.3)
    sheet.height = heights
    top = THICK + 0.03
    band = displaced(f"{name}-amp", sheet, outline_, 0.0, fabric, step=steps(sheet), at=(x0, y0), plumb=True)
    return [band, badge(name, mark, (x0 + x1) / 2, (y0 + y1) / 2, wide, top + 0.006)]


def prs(name, height):
    def dress(sheet, edge):
        shape = sheet.height.shape
        # Four of PRS's outline birds, in the order the fretboard has them: the peregrine falcon at the
        # third fret, the harrier at the fifth, the tern at the ninth and Cooper's hawk at the twelfth.
        # Traced from photographs of a 513's neck (legallyblindbirding.net), all to one scale, the
        # strings' spacing in each photograph. Each is mother-of-pearl let into a piece of the neck's
        # rosewood cut to the bird's shape, so the wood shows inside the bird and in a hairline round it.
        # They run down the middle of the piece one under another, as they do down a neck.
        art = strewn(artwork("logos/prs-outline-birds"))
        top, foot, gap = 0.6, 5.92, 0.1
        scale = (foot - top - gap * (len(art) - 1)) / sum(bird.shape[0] for bird in art)
        birds, y = [], top
        for bird in art:
            h, w = bird.shape[0] * scale, bird.shape[1] * scale
            cover, colour = placed(sheet, bird, MIDDLE - w / 2, y, MIDDLE + w / 2, y + h)
            shell = cover * np.clip(colour[..., 0] * 1.6, 0, 1)
            birds.append((cover, shell, cover - shell))
            y += h + gap
        # The tolex's grain is the scan's (moulded's scan): only the inlays are smooth.
        inlaid = np.clip(blur(np.max([cover for cover, _, _ in birds], axis=0), 2.0) * 3, 0, 1)
        sheet.finish(inlaid, rough=0.3)
        figure = np.clip(streaks(shape, 71, 40, 2), -2, 2) / 2
        for cover, shell, wood in birds:
            # The rosewood, dark and oiled, its grain running down the neck.
            inlay(sheet, cover, "#2a1512", rough=0.34, coat=0.3)
            sheet.paint(wood * np.clip(figure, 0, 1) * 0.5, "#4a2a20")
            sheet.paint(wood * np.clip(-figure, 0, 1) * 0.6, "#140a08")
            nacre(sheet, shell)
        return amp(name, 6.1, 8.3, artwork("logos/blackstar"))

    # The birds' outlines are fine, so the sheet is drawn finer than the others.
    # The tolex is the Silver Sky's Sandglow Yellow, the colour of its satin body.
    # Tolex is an embossed vinyl, its pebbled grain the scan of a real pebbled hide (ambientCG Leather025), each
    # pebble a millimetre or two across: semi-matte, with a thin sheen on the tops of the pebbles.
    return {"card": 1.2, "ceiling": False}, moulded(name, height, SANDGLOW, 0.5, 0.08, dress, density=7, scan=("Leather025", 6, 1.1, 0.35), relief=0.01, subsurface=0.03)


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


def teenage(name, height):
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
    # The mark is teenage engineering's own, cut from the header of teenage.engineering, in their black.
    badge, colour = placed(sheet, artwork("logos/teenage-engineering"), MIDDLE - 1.05, 1.5, MIDDLE + 1.05, 4.3)
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


def decoded(tone):
    """A photograph's sRGB tones as linear light."""
    return np.where(tone <= 0.04045, tone / 12.92, ((tone + 0.055) / 1.055) ** 2.4)


def clasp(name, middle, wide, top):
    """The cover of TAG Heuer's folding clasp, laid over the strap where it closes. It is cut from TAG
    Heuer's own photograph of the FC6483's buckle (studio/assets/tagheuer/clasp), turned square to the
    lens and drawn out to the cover's outline: one piece of steel with its top polished, the shield cut
    into it, its sides chamfered and its foot drawn to a point. The photograph's steel is the colour of
    the steel here, so it takes the light the way the steel did when it was photographed. A push-button
    stands out of each side. Returns the solids and the cover's outline."""
    photo = artwork("tagheuer/clasp")
    tall, broad = photo.shape[:2]
    h = wide * tall / broad
    side = wide * np.flatnonzero(photo[:, 0, 3] > 0.5).max() / broad
    x0, x1 = middle - wide / 2, middle + wide / 2
    outline = [(x0, top), (x1, top), (x1, top + side), (middle, top + h), (x0, top + side)]
    sheet = Sheet(wide, h, "#d8d9da", rough=0.1, density=14)
    X = sheet.X
    tone = np.clip(fit(photo[..., :3], *sheet.height.shape), 0, 1)
    sheet.rgb[:] = decoded(tone)
    sheet.metal[:] = 1.0
    # The shield's cut and the chamfers' edges are the photograph's darkest lines. Pressed in, they turn
    # with the light as the cut does. The polish's faint grain is left in the colour alone.
    lum = tone.mean(axis=-1)
    detail = lum - blur(lum, 4.0)
    sheet.height += 0.004 * np.clip(detail / 0.12, -1, 0)
    # It is curved across a little, to sit round the wrist.
    sheet.height -= 0.03 * ((X - wide / 2) / (wide / 2)) ** 2
    steel = skin(sheet, f"{name}-steel", wear=(("Fingerprints009", 4, 0.015, 0),), specular=0.5)
    cover = clad(prism(STAGE, f"{name}-clasp", outline, 0.04, THICK + 0.1, steel, bevel=0.1, segments=3), x0, top, wide, h)
    # The buttons stand out of the cover's sides a little below its top, as long as a third of its side.
    pusher = principled(f"{name}-pusher", "#d4d5d6", rough=0.08, metal=1.0)
    near, far = top + 0.08 * wide / 3.4, top + 0.86 * wide / 3.4
    buttons = [
        prism(STAGE, f"{name}-pusher-{side}", rect(a, near, b, far, 0.08, 6), 0.1, THICK - 0.02, pusher, bevel=0.06, segments=4)
        for side, a, b in (("left", x0 - 0.16, x0 + 0.04), ("right", x1 - 0.04, x1 + 0.16))
    ]
    return [cover, *buttons], outline


def diffuser(name, over, x0, y0, x1, y1, z, strength):
    """A diffuser held close over polished steel, as a watch is lit for its photograph. Steel shows only
    what is round it, and here that is one even light across its top, falling off past its edges, where
    the chamfers look away from it to the dark room. The diffuser is linked to the steel alone, so nothing
    else sees it or is lit by it."""
    panel = bpy.data.meshes.new(f"{name}-diffuser")
    panel.from_pydata([(x0, -y0, 0), (x1, -y0, 0), (x1, -y1, 0), (x0, -y1, 0)], [], [(0, 3, 2, 1)])
    glow = bpy.data.materials.new(f"{name}-diffuser")
    glow.use_nodes = True
    nodes, links = glow.node_tree.nodes, glow.node_tree.links
    nodes.clear()
    emit = nodes.new("ShaderNodeEmission")
    # The stage warms what it develops, to take the room's cool cast out. This light has no cast to take
    # out, so it is given the room's, and the steel comes out as grey as it was photographed.
    cast = 1 / stage_module.GAIN
    emit.inputs["Color"].default_value = (*(cast / cast.max()), 1.0)
    emit.inputs["Strength"].default_value = strength
    clear = nodes.new("ShaderNodeBsdfTransparent")
    both = nodes.new("ShaderNodeAddShader")
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(emit.outputs[0], both.inputs[0])
    links.new(clear.outputs[0], both.inputs[1])
    links.new(both.outputs[0], out.inputs["Surface"])
    panel.materials.append(glow)
    sheet = STAGE.add(f"{name}-diffuser", panel)
    sheet["stand"] = "room"
    sheet.location.z = z
    for seen in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission", "visible_volume_scatter"):
        setattr(sheet, seen, False)
    steel = bpy.data.collections.new(f"{name}-steel")
    for obj in over:
        steel.objects.link(obj)
    sheet.light_linking.receiver_collection = steel


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
    sheet.rgb[rows, cols] = decoded(tone)
    # The photograph has the hide's relief in it: its creases are its darkest lines. Pressed in, they
    # catch this room's light as well as the one it was photographed in.
    lum = sheet.rgb.mean(axis=-1)
    detail = lum - blur(lum, 8.0)
    sheet.height += 0.006 * np.clip(detail / max(detail.std(), 1e-6), -3, 3) / 3
    # Padded: it stands highest down its middle and rolls down to its edges.
    sheet.height -= 0.1 * (1 - np.clip(-edge / 0.6, 0, 1)) ** 2
    sheet.rough[:] = 0.42
    sheet.coat[:] = 0.06
    # The padding and the scales are the strap's own geometry, its edge rounded over as the leather is folded.
    sheet.height -= rounded(edge, 0.1)
    heights = sheet.height.copy()
    sheet.height[:] = 0.0
    leather = skin(sheet, f"{name}-alligator", specular=0.15, coat_rough=0.2)
    sheet.height = heights
    strap = displaced(name, sheet, edge, THICK - 0.02, leather, step=steps(sheet))
    # The clasp closes over the first join in the hide. Its cover stands out past the strap's sides as
    # far as it does in the photograph.
    lock = top + 282 * stretch / per_em - 0.75
    steel, cover = clasp(name, MIDDLE, 1.13 * across, lock)
    xs, ys = [x for x, _ in cover], [y for _, y in cover]
    diffuser(name, steel, min(xs) - 0.3, min(ys) - 0.3, max(xs) + 0.3, max(ys) + 0.3, THICK + 1.2, 1.1)
    return {"card": 0.5}, [strap, *steel]


# A PRS Silver Sky in Sandglow Yellow, the warm, sandy vintage yellow of the John Mayer Defender, as its satin
# body shows it in the light.
SANDGLOW = "#dab65c"
# Lacoste's burgundy, and the ecru and muted gold its collar is tipped in.
BURGUNDY = "#6b1a26"
ECRU = "#ece4d2"
GOLD = "#c49a4a"
# A Blackstar ID:Core in red: its tolex, a dusky wine.
WINE = "#6e3438"

# Each tab: the height in rem of the paper tab (SiteShell's tabHeights), that paper's colour (the band of
# its strip), which lights the piece's edges from below, how the piece was set down (see stuck), and what
# builds it.
TABS = {
    "lacoste": (10, "#ede3a1", (0.9, 0.02, -0.03), lacoste),
    "proraso": (10, "#d9d4c2", (-0.7, -0.02, 0.02), proraso),
    "teenage": (10, "#1e2740", (0.5, 0.03, 0.03), teenage),
    "prs": (10, "#ece8df", (-1.0, 0.0, -0.02), prs),
    "tagheuer": (11.5, "#8a8b78", (0.5, 0.0, 0.02), tagheuer),
}


def lit_by_the_room(stage):
    """The stage takes its contact shadow under an even white sky, so it lies all round a piece. Here it is taken
    under the room's own light, the octabox up at the top left among the rest, so it falls away from the light as the
    rendered cut of the paper's does (studio/tabcut)."""
    build_room = stage._room

    def room(*args, **kwargs):
        floor = build_room(*args, **kwargs)
        nodes, links = bpy.context.scene.world.node_tree.nodes, bpy.context.scene.world.node_tree.links
        studio = next(node for node in nodes if node.type == "TEX_ENVIRONMENT")
        links.new(studio.outputs["Color"], nodes["even"].inputs[7])
        return floor

    stage._room = room


def tab(name):
    height, paper, askew, build = TABS[name]
    stage_module.MAT = paper
    shot, pieces = build(f"tab-{name}", height)
    for piece in pieces:
        stuck(piece, height, askew)
    # A matte piece has no flat shine to keep from the room, so it is lit by the whole studio.
    if shot.pop("ceiling", True):
        ceiling(height)
    STAGE.shoot(f"tab-{name}", (0, 0, WIDTH, height), bleed=MARGIN, shadow=0.9, sharp=4.0, **shot)


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
lit_by_the_room(STAGE)
for name in args.tabs or TABS:
    STAGE.clear()
    tab(name)
