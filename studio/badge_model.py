"""ID badge: a copy of the reference photograph, a printed card in a clear vinyl holder on a steel ring.

Every measurement is taken off the reference in its own pixels (720 x 900) and the frame is the
reference's frame, so the render can be laid over it. The card is the reference's own card: its
type, logo and handwriting are lifted from the photograph as an ink plate (studio/assets/plate.png),
and only the portrait is replaced.

Uses the copy stand in studio/desk, and the headless Chromium in studio/browser.mjs for
studio/assets/overlay.png (see studio/plate.html). Run from the repository root:

    blender -b --factory-startup -P studio/badge.py -- [--scale 0.5] [--samples 64]

Writes public/objects/badge.avif.
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
from mathutils import Matrix, Vector  # noqa: E402

import stage as stage_module  # noqa: E402
from paint import blur, cloud, linear  # noqa: E402
from solids import finish, principled, prism, rect, ring, worn  # noqa: E402
from stage import Stage  # noqa: E402
from stock import Sheet, fit  # noqa: E402

PX = 30.0  # reference pixels to one em
FRAME = (720, 900)
HOLDER = (105, 15, 620, 882, 22)
POCKET = (118, 28, 607, 869, 11)  # inside edge of the welded rim
HEADER_END = 122
ZIP = ((122, 133), (137, 146), (150, 160))
EYELETS = ((213, 77), (515, 77))
EYELET_HOLE, EYELET_RIM = 15, 19.5
SLOT = (308, 62, 420, 95, 16.5)
# The ring is an oval loop: its lower turn sits in the slot and its sides run up out of the frame.
RING_TURN, RING_BEND, RING_REACH, RING_WIRE = (393, 41), 32, 150, 7.0
CARD = (162, 195, 577, 850)
PHOTO = (273.5, 372.5, 456.7, 601.5)  # the print, before it is turned
PHOTO_TURN = 0.75  # degrees clockwise: it was stuck down by hand
GUIDE = (273.9, 371.0, 460.0, 602.2)  # the box printed on the card to place it in
# Parts of the reference's card that are set again from studio/plate.html: the drop number, the line under
# the title, the three rules and what is written on them.
REWRITTEN = (
    (448, 234, 520, 257),
    (190, 331, 560, 362),
    (190, 653, 565, 660),
    (190, 708.5, 565, 715),
    (190, 764.5, 565, 771),
    (240, 603, 565, 665),
    (282, 665, 565, 721),
    (242, 721, 565, 781),
)
HAND_FROM = 603  # below this line of the reference the new words are handwriting
# The mat stands in for the page: it bounces light and is never seen. Clear vinyl comes out of the render
# clear, so whatever the page puts behind the badge shows through it.
MAT = "#dddddb"
PROP = 0.62  # the holder rides this far off the page: the ring runs under its header
SHEET = 0.07  # thickness of the vinyl
LIFT = 0.1  # how far the front sheet stands off the backing, with the card between
CARD_TINT = 0.97  # what the vinyl lets through over the card
SHINE = 11.0  # how bright the reflected room has to be for vinyl, which mirrors about a fourteenth, to show it


def stored(path):
    """An image file as rows from the top, values as stored."""
    image = bpy.data.images.load(path)
    image.colorspace_settings.name = "Non-Color"
    w, h = image.size
    data = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(data)
    bpy.data.images.remove(image)
    return data.reshape(h, w, 4)[::-1, :, :3].astype(np.float64)


def to_linear(v):
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def as_image(name, values):
    """A float array, rows from the top, as an image a shader can read."""
    rows, cols = values.shape
    image = bpy.data.images.new(name, cols, rows, alpha=False, float_buffer=True)
    image.colorspace_settings.name = "Non-Color"
    rgba = np.dstack((values, values, values, np.ones_like(values)))[::-1].astype(np.float32)
    image.pixels.foreach_set(rgba.ravel())
    image.pack()
    return image


def widest(a, reach, pick):
    """The largest or smallest value within `reach` pixels of each point."""
    out = a
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            out = pick(out, np.roll(np.roll(a, dy, axis=0), dx, axis=1))
    return out


def measured_vinyl():
    """What the reference's vinyl does to the light, measured off the photograph where nothing but vinyl
    lies over the white page: how much it lets through, and how much it adds by reflecting the room.

    The thin dark lines are left out of the first, because the model's own seams and edges make those.
    Returns the transmission and the reflected light, both as arrays over the reference's frame."""
    ref = stored(os.path.join(HERE, "assets", "reference.jpg")).mean(axis=-1)
    rows, cols = ref.shape
    Y, X = np.mgrid[0:rows, 0:cols].astype(np.float64)
    # The bare page, with the slow fall-off the photograph has across it, fitted where nothing covers it.
    bare = (X < 92) | (X > 634) | (Y > 893)
    fit_ = np.linalg.lstsq(np.column_stack((np.ones(bare.sum()), X[bare], Y[bare])), ref[bare], rcond=None)[0]
    page = np.clip(fit_[0] + fit_[1] * X + fit_[2] * Y, 0, 1)

    # All of this is in the photograph's own stored values, not in light. A browser lays the render over
    # the page by those values, so vinyl that reads as nine tenths of the page there has to cover a tenth.
    soft = blur(ref, 0.8)
    closed = blur(widest(widest(soft, 3, np.maximum), 3, np.minimum), 2.0)
    # Beside the card the dark is the card's own shadow, which no seam will draw. Keep it.
    cx0, cy0, cx1, cy1 = CARD
    beside = ((X > cx0 - 12) & (X < cx0 + 2) & (Y > cy0 - 6) & (Y < cy1 + 4)) | ((Y > cy0 - 16) & (Y < cy0 + 2) & (X > cx0 - 6) & (X < cx1 + 6))
    through = np.where(beside, soft, closed) / page
    clear = float(np.median(through[300:800, 586:600]))
    # Where the vinyl is lighter than its clearest, it is reflecting. Up to the page's own white that
    # takes only as much light as the vinyl's cover; past it, a glint, it takes a lamp.
    cover = 1 - clear
    lift = np.clip((soft / page - clear) / cover, 0, 1)
    glint = np.clip((soft / page - 1.004) / 0.03, 0, 1)
    reflected = cover * to_linear(lift * page) + 2.6 * glint
    # The model's vinyl already loses about a fourteenth of the light to its own two reflections.
    through = np.clip(through, 0.2, clear) / 0.93

    hx0, hy0, hx1, hy1, _ = HOLDER
    on_card = (X > cx0) & (X < cx1) & (Y > cy0) & (Y < cy1)
    through[on_card] = CARD_TINT / 0.93
    # The ring hides the vinyl under it in the photograph. Put the header's own grey there.
    at_ring = (X > 345) & (X < 442) & (Y < 100)
    through[at_ring] = float(np.median(through[100:112, 150:300]))
    through = np.clip(through, 0, 1)
    off = ~((X > hx0 + 1) & (X < hx1 - 1) & (Y > hy0 + 1) & (Y < hy1 - 1)) | at_ring | ((X > cx0 - 2) & (X < cx1 + 2) & (Y > cy0 - 2) & (Y < cy1 + 2))
    reflected[off] = 0
    return through, reflected


def em(value):
    return value / PX


def box(x0, y0, x1, y1, r=0.0, steps=10):
    return rect(em(x0), em(y0), em(x1), em(y1), em(r), steps)


def glass():
    """The studio's glass: a mirror in its faces, by Fresnel, and clear through. The eye sees through it by
    refraction, but light from the lamps passes it straight, so it leaves no shadow of its own."""
    material = bpy.data.materials.new("glass")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    path = nodes.new("ShaderNodeLightPath")
    bent = nodes.new("ShaderNodeBsdfRefraction")
    bent.inputs["Roughness"].default_value = 0.0
    straight = nodes.new("ShaderNodeBsdfTransparent")
    through = nodes.new("ShaderNodeMixShader")
    links.new(path.outputs["Is Shadow Ray"], through.inputs["Fac"])
    links.new(bent.outputs[0], through.inputs[1])
    links.new(straight.outputs[0], through.inputs[2])
    shine = nodes.new("ShaderNodeBsdfGlossy")
    shine.inputs["Roughness"].default_value = 0.0
    fresnel = nodes.new("ShaderNodeFresnel")
    face = nodes.new("ShaderNodeMixShader")
    links.new(fresnel.outputs[0], face.inputs["Fac"])
    links.new(through.outputs[0], face.inputs[1])
    links.new(shine.outputs[0], face.inputs[2])
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(face.outputs[0], out.inputs["Surface"])
    return material


def vinyl(lets_through):
    """The studio's glass as clear vinyl. The studio lets light straight through its glass, so what lies
    under it is not left in the dark. Flat vinyl does the same here, but where the sheet turns, at a ridge,
    a bevel or a cut edge, the light is bent away and does not arrive underneath. Those turns are let cast
    their shadow, so every weld and edge lays a thin dark line on the side away from the lamp.
    lets_through is how clear the sheet is at each point of the frame, measured off the reference: fused
    vinyl is cloudier than the open pocket."""
    material = glass()
    material.name = "vinyl"
    nodes, links = material.node_tree.nodes, material.node_tree.links
    clear = next(node for node in nodes if node.bl_idname == "ShaderNodeBsdfTransparent")
    geometry = nodes.new("ShaderNodeNewGeometry")
    split = nodes.new("ShaderNodeSeparateXYZ")
    level = nodes.new("ShaderNodeMath")
    level.operation = "ABSOLUTE"
    passes = nodes.new("ShaderNodeMapRange")
    passes.interpolation_type = "SMOOTHSTEP"
    passes.inputs["From Min"].default_value = 0.78
    passes.inputs["From Max"].default_value = 0.99
    passes.inputs["To Min"].default_value = 0.0
    passes.inputs["To Max"].default_value = 1.0
    tint = nodes.new("ShaderNodeCombineColor")
    links.new(geometry.outputs["True Normal"], split.inputs[0])
    links.new(split.outputs["Z"], level.inputs[0])
    links.new(level.outputs[0], passes.inputs["Value"])
    for channel in ("Red", "Green", "Blue"):
        links.new(passes.outputs["Result"], tint.inputs[channel])
    links.new(tint.outputs["Color"], clear.inputs["Color"])
    # Seen from straight above, a face that turns steeply away sends the eye sideways along the sheet,
    # where there is only the dark of the room, piped in from the edges. So the steeper the face, the
    # darker it reads: every bevel, bead flank and seam wall draws itself.
    seen = nodes.new("ShaderNodeMapRange")
    seen.interpolation_type = "SMOOTHSTEP"
    seen.inputs["From Min"].default_value = 0.5
    seen.inputs["From Max"].default_value = 0.94
    seen.inputs["To Min"].default_value = 0.06
    seen.inputs["To Max"].default_value = 1.0
    # Light crosses two faces of the sheet, so each takes the root of what the whole lets through.
    over = nodes.new("ShaderNodeMapping")
    over.inputs["Scale"].default_value = (1 / em(FRAME[0]), 1 / em(FRAME[1]), 1.0)
    over.inputs["Location"].default_value = (0.0, 1.0, 0.0)
    cloudy = nodes.new("ShaderNodeTexImage")
    cloudy.image = as_image("vinyl-through", np.sqrt(lets_through))
    cloudy.extension = "EXTEND"
    both = nodes.new("ShaderNodeMath")
    both.operation = "MULTIPLY"
    through = nodes.new("ShaderNodeCombineColor")
    links.new(level.outputs[0], seen.inputs["Value"])
    links.new(geometry.outputs["Position"], over.inputs["Vector"])
    links.new(over.outputs["Vector"], cloudy.inputs["Vector"])
    links.new(seen.outputs["Result"], both.inputs[0])
    links.new(cloudy.outputs["Color"], both.inputs[1])
    for channel in ("Red", "Green", "Blue"):
        links.new(both.outputs[0], through.inputs[channel])
    # Thin sheet is never dead flat. A slow wave in the face it reflects with pulls what it mirrors about.
    place = nodes.new("ShaderNodeTexCoord")
    spread = nodes.new("ShaderNodeMapping")
    spread.inputs["Scale"].default_value = (0.2, 0.11, 1.0)
    swell = nodes.new("ShaderNodeTexNoise")
    swell.inputs["Scale"].default_value = 1.0
    swell.inputs["Detail"].default_value = 1.5
    wave = nodes.new("ShaderNodeBump")
    wave.inputs["Strength"].default_value = 0.3
    wave.inputs["Distance"].default_value = 0.6
    links.new(place.outputs["Object"], spread.inputs["Vector"])
    links.new(spread.outputs["Vector"], swell.inputs["Vector"])
    links.new(swell.outputs["Fac"], wave.inputs["Height"])
    for node in nodes:
        if node.bl_idname == "ShaderNodeBsdfGlossy":
            links.new(wave.outputs["Normal"], node.inputs["Normal"])
        if node.bl_idname == "ShaderNodeBsdfRefraction":
            links.new(through.outputs["Color"], node.inputs["Color"])
            node.inputs["IOR"].default_value = 1.47
        if node.bl_idname == "ShaderNodeFresnel":
            node.inputs["IOR"].default_value = 1.47
    return material


def rework(obj, cutters=(), bevel=0.0, segments=3, join=()):
    """Weld other solids into a prism, cut outlines through it and round every hard edge left.
    All three need the bare mesh."""
    for name in [m.name for m in obj.modifiers]:
        obj.modifiers.remove(obj.modifiers[name])
    bpy.context.view_layer.objects.active = obj
    for other in join:
        for name in [m.name for m in other.modifiers]:
            other.modifiers.remove(other.modifiers[name])
        weld = obj.modifiers.new("weld", "BOOLEAN")
        weld.operation = "UNION"
        weld.object = other
        weld.solver = "EXACT"
        bpy.ops.object.modifier_apply(modifier=weld.name)
        bpy.data.objects.remove(other, do_unlink=True)
    for i, outline in enumerate(cutters):
        tool = prism(STAGE, f"tool-{i}", outline, -5, 5, None)
        cut = obj.modifiers.new("cut", "BOOLEAN")
        cut.operation = "DIFFERENCE"
        cut.object = tool
        cut.solver = "EXACT"
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=cut.name)
        bpy.data.objects.remove(tool, do_unlink=True)
    if bevel:
        soft = obj.modifiers.new("bevel", "BEVEL")
        soft.width = bevel
        soft.segments = segments
        soft.limit_method = "ANGLE"
        soft.angle_limit = math.radians(40)
        bpy.ops.object.modifier_apply(modifier=soft.name)
    return shade(obj)


def shade(obj):
    """Smooth shading that keeps a hard turn hard."""
    for face in obj.data.polygons:
        face.use_smooth = True
    obj.data.set_sharp_from_angle(angle=math.radians(38))
    weighted = obj.modifiers.new("normals", "WEIGHTED_NORMAL")
    weighted.keep_sharp = True
    weighted.weight = 100
    return obj


def carve(obj, tools):
    """Cut solids out of another, after its edges have been rounded, so the cuts stay crisp."""
    for name in [m.name for m in obj.modifiers]:
        obj.modifiers.remove(obj.modifiers[name])
    bpy.context.view_layer.objects.active = obj
    for tool in tools:
        for name in [m.name for m in tool.modifiers]:
            tool.modifiers.remove(tool.modifiers[name])
        cut = obj.modifiers.new("carve", "BOOLEAN")
        cut.operation = "DIFFERENCE"
        cut.object = tool
        cut.solver = "EXACT"
        bpy.ops.object.modifier_apply(modifier=cut.name)
        bpy.data.objects.remove(tool, do_unlink=True)
    return shade(obj)


def seam(name, x0, y0, x1, y1, r, width, z0, z1, steps=14):
    """The tool for a pressed line that follows a rounded rectangle: a thin wall, in reference pixels."""
    h = width / 2
    wall = prism(STAGE, name, box(x0 - h, y0 - h, x1 + h, y1 + h, r + h, steps), z0, z1, None)
    # Its foot is rounded, so the cut it leaves has sloping walls for the lens to look down on.
    return rework(wall, [box(x0 + h, y0 + h, x1 - h, y1 - h, max(r - h, 0.5), steps)], bevel=em(width) * 0.46, segments=2)


def punches():
    """The slot, as an outline. The eyelets are pressed into the header and not cut through."""
    return [box(*SLOT, steps=14)]


def holder(lets_through):
    """One piece of clear vinyl: the front sheet, the welded rim round it, the zip across the mouth and the
    pressed eyelets, with the slot punched through. The back sheet is left out: it lies flat on the page
    and shows nothing."""
    clear = vinyl(lets_through)
    outline = box(*HOLDER, steps=14)
    x0, y0, x1, y1, r = POCKET
    z0 = PROP
    top = z0 + LIFT
    end = top + SHEET

    sheet = prism(STAGE, "holder", outline, top, end, clear)
    # The weld is a low flat bead all the way round. Its top lets light through; its rounded edges turn it.
    parts = [rework(prism(STAGE, "rim", outline, z0, end + 0.09, clear), [box(x0, y0, x1, y1, r, 14)], bevel=0.075, segments=5)]
    # The header is the two sheets fused into one thicker one.
    parts.append(prism(STAGE, "header", box(x0 - 2, y0 - 2, x1 + 2, HEADER_END, r, 14), top - 0.05, top + 0.01, clear))
    for i, (ya, yb) in enumerate(ZIP):
        parts.append(rework(prism(STAGE, f"zip-{i}", box(x0 - 2, ya, x1 + 2, yb), end - 0.02, end + 0.065, clear), bevel=0.08, segments=5))
        parts.append(prism(STAGE, f"zip-under-{i}", box(x0 - 2, ya + 3, x1 + 2, yb + 3), top - 0.1, top + 0.02, clear))
    for i, (x, y) in enumerate(EYELETS):
        lip = prism(STAGE, f"eyelet-{i}", ring(em(x), em(y), em(EYELET_RIM + 3.2), 72), end - 0.02, end + 0.1, clear)
        parts.append(rework(lip, [ring(em(x), em(y), em(EYELET_RIM - 2.6), 72)], bevel=0.075, segments=5))
    rework(sheet, punches(), bevel=0.035, segments=3, join=parts)

    # Where the press came down it left hairline seams: inside the weld, round the outer edge
    # and round the slot and the eyelets. Each is a narrow cut with steep walls, and steep vinyl turns light away,
    # so each shows as a dark line however it is lit.
    hx0, hy0, hx1, hy1, hr = HOLDER
    sx0, sy0, sx1, sy1, sr = SLOT
    low, high = end - 0.05, end + 1.0
    carve(
        sheet,
        [
            seam("seam-inner", x0 + 1.2, y0 + 1.2, x1 - 1.2, y1 - 1.2, r, 1.5, low, high),
            seam("seam-outer", hx0 + 2.2, hy0 + 2.2, hx1 - 2.2, hy1 - 2.2, hr - 2.2, 1.2, end + 0.02, high),
            seam("seam-slot", sx0 - 2.4, sy0 - 2.4, sx1 + 2.4, sy1 + 2.4, sr + 2.4, 1.2, low, high),
        ]
        + [
            rework(
                prism(STAGE, f"seam-eyelet-{i}", ring(em(x), em(y), em(EYELET_HOLE + 2.3), 72), low, high, None),
                [ring(em(x), em(y), em(EYELET_HOLE + 0.9), 72)],
                bevel=em(0.62),
                segments=2,
            )
            for i, (x, y) in enumerate(EYELETS)
        ],
    )

    return [sheet], end


def card_art(rows, cols):
    """The reference's card as linear colour: its ink lifted off the photograph, the portrait replaced."""

    plate = fit(stored(os.path.join(HERE, "assets", "plate.png")), rows, cols)
    lum = plate.mean(axis=-1)
    bare = lum > np.percentile(lum, 55)
    paper = np.median(plate[bare], axis=0)
    level = float(paper.mean())

    # Ink density, 0 on bare stock and 1 under solid black. The photograph is soft, so the edges are
    # sharpened; greys such as the dashed rules keep their weight.
    ink = np.clip((level - lum) / (level - 0.3), 0, 1)
    ink = np.clip((ink - 0.05) / 0.95, 0, 1)
    ink = np.clip(ink + 0.5 * (ink - blur(ink, 2.0)), 0, 1) ** 0.72

    cw, ch = CARD[2] - CARD[0], CARD[3] - CARD[1]
    sx, sy = cols / cw, rows / ch
    Y, X = np.mgrid[0:rows, 0:cols] + 0.5

    def box_distance(x0, y0, x1, y1):
        """Signed distance in card pixels to a rectangle given in reference pixels."""
        qx = np.abs(X - (x0 + x1 - 2 * CARD[0]) / 2 * sx) - (x1 - x0) / 2 * sx
        qy = np.abs(Y - (y0 + y1 - 2 * CARD[1]) / 2 * sy) - (y1 - y0) / 2 * sy
        return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0)

    # The words that are this card's own. The reference's are rubbed out and these are printed in their place:
    # mono type and the logo as sharp as the press left the rest, the hand in marker that runs a little dry.
    for x0, y0, x1, y1 in REWRITTEN:
        ink[box_distance(x0, y0, x1, y1) < 0] = 0
    words = 1 - fit(stored(os.path.join(HERE, "assets", "overlay.png")), rows, cols).mean(axis=-1)
    # The lifted type has spread a little, as ink does on card and a photograph does again. So does this.
    words = np.clip(blur(words, 1.3) * 1.75, 0, 1)
    marker = np.clip(0.965 + 0.03 * cloud((rows, cols), 5, falloff=1.1), 0.9, 1.0)
    by_hand = (Y > (HAND_FROM - CARD[1]) * sy) & (words > 0.5)
    ink = np.maximum(ink, np.where(by_hand, words * marker, words))

    # Clear the old portrait and its box, then print the box again as a hairline.
    guide = box_distance(*GUIDE)
    ink[guide < 3 * sx] = 0
    ink = np.maximum(ink, 0.42 * np.clip(1.2 - np.abs(guide) / (0.55 * sx), 0, 1))
    # The reference's card sits a touch askew, so its own edge shadow strays onto the plate. This card casts its own.
    ink[:, : round(9 * sx)] = 0

    stock = np.clip(to_linear(paper) * np.array([1.16, 1.06, 0.98]), 0, 1)
    art = stock * (1 - ink[..., None] * (1 - linear("#171614")))

    # The portrait is a small photographic print stuck down a little out of true, so the box shows beside it.
    px0, py0, px1, py1 = PHOTO
    pw, ph = (px1 - px0) * sx, (py1 - py0) * sy
    turn = math.radians(PHOTO_TURN)
    dx = X - ((px0 + px1) / 2 - CARD[0]) * sx
    dy = Y - ((py0 + py1) / 2 - CARD[1]) * sy
    u = dx * math.cos(turn) + dy * math.sin(turn)
    v = -dx * math.sin(turn) + dy * math.cos(turn)
    inside = np.maximum(np.abs(u) - pw / 2, np.abs(v) - ph / 2)
    cover = np.clip(0.5 - inside, 0, 1)

    face = stored(os.path.join(ROOT, "public", "photos", "face.jpg"))
    fh, fw = face.shape[:2]
    face = to_linear(face[round(fh * 0.13) : round(fh * 0.88), round(fw * 0.2) : round(fw * 0.8)]) * 1.02 + 0.03
    fy = np.clip((v / ph + 0.5) * face.shape[0] - 0.5, 0, face.shape[0] - 1.001)
    fx = np.clip((u / pw + 0.5) * face.shape[1] - 0.5, 0, face.shape[1] - 1.001)
    iy, ix = fy.astype(int), fx.astype(int)
    ty, tx = (fy - iy)[..., None], (fx - ix)[..., None]
    print_ = (face[iy, ix] * (1 - tx) + face[iy, ix + 1] * tx) * (1 - ty) + (face[iy + 1, ix] * (1 - tx) + face[iy + 1, ix + 1] * tx) * ty
    # The cut edge of photographic paper shows white.
    rim = np.clip((inside + 1.3 * sx) / (0.6 * sx), 0, 1)[..., None]
    print_ = print_ * (1 - rim) + to_linear(np.array([0.96, 0.95, 0.93])) * rim
    art = art * (1 - cover[..., None]) + print_ * cover[..., None]
    return np.clip(art, 0, 1)


def card(z):
    w, h = em(CARD[2] - CARD[0]), em(CARD[3] - CARD[1])
    sheet = Sheet(w, h, "#f5f0e2", rough=0.8)
    sheet.rgb = card_art(*sheet.height.shape)
    sheet.chamfer(0.04, 0.01)
    return sheet.build(
        STAGE,
        "card",
        thickness=z,
        scan="Paper001",
        scan_size=9,
        scan_normal=0.45,
        scan_colour=0.12,
        fibre=0.0012,
        fibre_scale=34,
        sheen=0.0,
        specular=0.1,
        at=(em(CARD[0]), em(CARD[1])),
    )


def steel_ring(z):
    """A steel loop threaded through the slot. It is tipped across the sheet, so its left side runs behind
    the header and its right side in front, and it crosses the sheet in the slot."""
    steel = worn(principled("steel", (0.86, 0.86, 0.87), rough=0.08, metal=1.0), "Scratches003", 3, 0.12)
    bend, reach, wire = em(RING_BEND), em(RING_REACH), em(RING_WIRE)
    steps = 48
    line = [(bend * math.cos(math.pi * i / steps), bend * math.sin(math.pi * i / steps)) for i in range(steps + 1)]
    line += [(-bend, -reach * i / 12) for i in range(1, 12)]
    line += [(bend * math.cos(math.pi + math.pi * i / steps), -reach + bend * math.sin(math.pi + math.pi * i / steps)) for i in range(steps + 1)]
    line += [(bend, -reach + reach * i / 12) for i in range(1, 12)]
    bm = bmesh.new()
    rings = []
    around = 28
    for i, (x, y) in enumerate(line):
        ax, ay = line[i - 1]
        bx, by = line[(i + 1) % len(line)]
        length = math.hypot(bx - ax, by - ay)
        nx, ny = (by - ay) / length, -(bx - ax) / length
        rings.append(
            [
                bm.verts.new((x + wire * math.cos(2 * math.pi * k / around) * nx, -(y + wire * math.cos(2 * math.pi * k / around) * ny), wire * math.sin(2 * math.pi * k / around)))
                for k in range(around)
            ]
        )
    for i, a in enumerate(rings):
        b = rings[(i + 1) % len(rings)]
        for k in range(around):
            bm.faces.new((a[k], b[k], b[(k + 1) % around], a[(k + 1) % around]))
    loop = finish(STAGE, "ring", bm, steel)
    tip = math.radians(16.5)
    widen = Matrix.Diagonal((1 / math.cos(tip), 1, 1, 1))
    loop.matrix_world = Matrix.Translation((em(RING_TURN[0]), -em(RING_TURN[1]), z)) @ Matrix.Rotation(-tip, 4, "Y") @ widen


def room(reflected):
    """What the vinyl and the ring mirror. The camera is orthographic, so the flat of the sheet mirrors
    whatever hangs straight over it, point for point. A sheet of light hangs just over the set, lit only
    where the reference's vinyl shines and by as much, and clear everywhere else. Straight above that is a
    black card, so the flat of the sheet mirrors nothing else; anything that curves or leans, the ring and
    the shoulders of the beads, looks past the card into the studio. Only reflections see either."""
    w, h = em(FRAME[0]), em(FRAME[1])
    sheet = bpy.data.meshes.new("shine")
    sheet.from_pydata([(0, -h, 0), (w, -h, 0), (w, 0, 0), (0, 0, 0)], [], [(0, 1, 2, 3)])
    sheet.uv_layers.new().data.foreach_set("uv", [0, 0, 1, 0, 1, 1, 0, 1])
    glow = bpy.data.materials.new("shine")
    glow.use_nodes = True
    nodes, links = glow.node_tree.nodes, glow.node_tree.links
    nodes.clear()
    coord = nodes.new("ShaderNodeTexCoord")
    lit = nodes.new("ShaderNodeTexImage")
    lit.image = as_image("vinyl-shine", reflected * SHINE)
    lit.interpolation = "Cubic"
    lit.extension = "CLIP"
    emit = nodes.new("ShaderNodeEmission")
    clear = nodes.new("ShaderNodeBsdfTransparent")
    both = nodes.new("ShaderNodeAddShader")
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(coord.outputs["UV"], lit.inputs["Vector"])
    links.new(lit.outputs["Color"], emit.inputs["Strength"])
    links.new(emit.outputs[0], both.inputs[0])
    links.new(clear.outputs[0], both.inputs[1])
    links.new(both.outputs[0], out.inputs["Surface"])
    # Reflections find it by chance. Sampled as a light it would be picked and then thrown away, since
    # nothing diffuse may see it, and the set would lose that share of its light.
    glow.cycles.emission_sampling = "NONE"
    sheet.materials.append(glow)
    shine = STAGE.add("shine", sheet)
    shine.location = (0, 0, 2.0)

    dark = bpy.data.meshes.new("room")
    dark.from_pydata([(-24, -27, 0), (24, -27, 0), (24, 27, 0), (-24, 27, 0)], [], [(0, 1, 2, 3)])
    dark.materials.append(principled("room", (0.004, 0.004, 0.004), rough=1.0, specular_ior_level=0.0))
    ceiling = STAGE.add("room", dark)
    ceiling.location = (w / 2, -h / 2, 130)
    for obj in (shine, ceiling):
        obj["stand"] = "room"
        for seen in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission"):
            setattr(obj, seen, False)


def badge():
    stage_module.MAT = MAT
    # The reference is lit from the lower right: shadows fall up and to the left, and the frame brightens
    # toward the bottom. The room's big box goes there, and a nearer key gives the fall-off.
    stage_module.BOX_ON_STAND = Vector((0.42, -0.3, 0.86)).normalized()
    key = bpy.data.lights.new("key", "AREA")
    key.size = 16
    key.energy = 3600
    # The stand's gain takes the room's cool cast out of everything, so a lamp has to start that much cooler.
    key.color = (0.88, 0.91, 1.0)
    lamp = STAGE.add("key", key)
    lamp["stand"] = "key"
    target = Vector((em(FRAME[0]) / 2, -em(FRAME[1]) / 2, 0))
    lamp.location = target + Vector((15, -34, 26))
    lamp.rotation_euler = (target - lamp.location).to_track_quat("-Z", "Y").to_euler()
    # What shines in the reference is a lamp close to the lens, a little below and to the right of it.
    # Only shiny things see this one: it lights nothing and casts nothing. Flat vinyl mirrors the dark
    # above it and stays clear; a face that leans ten degrees its way, the shoulder of a bead or the
    # crown of the wire, catches it white.
    flash = bpy.data.lights.new("flash", "AREA")
    flash.size = 22
    flash.energy = 480000
    flash.color = (0.88, 0.91, 1.0)
    spark = STAGE.add("flash", flash)
    spark["stand"] = "key"
    # It hangs well outside the frame: straight over it, the flat of the sheet would mirror it whole.
    spark.location = target + 120 * Vector((0.22, -0.28, 0.935)).normalized()
    spark.rotation_euler = (target - spark.location).to_track_quat("-Z", "Y").to_euler()
    spark.visible_diffuse = False
    spark.visible_transmission = False
    lets_through, reflected = measured_vinyl()
    plastic, end = holder(lets_through)
    card(PROP + 0.07)
    steel_ring(PROP + LIFT + 0.01)
    room(reflected)
    cx, cy = em(FRAME[0]) / 2, -em(FRAME[1]) / 2
    STAGE.shoot(
        "badge",
        (0, 0, em(FRAME[0]), em(FRAME[1])),
        bleed=0.0,
        shadow=0.0,
        exposure=0.88,
        room=0.95,
        mat_through_glass=False,
        shadowless=tuple(plastic),
        sharp=1.25,
    )


parser = argparse.ArgumentParser()
parser.add_argument("--scale", type=float, default=1.0)
parser.add_argument("--samples", type=int, default=160)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
out_dir = os.path.join(ROOT, "public", "objects")
os.makedirs(out_dir, exist_ok=True)
STAGE = Stage(out_dir, scale=args.scale, samples=args.samples)
STAGE.clear()
badge()
