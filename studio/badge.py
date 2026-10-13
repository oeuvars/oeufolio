"""ID badge: a copy of the reference photograph, a printed card in a clear vinyl holder on a steel ring.

Every measurement is taken off the reference in its own pixels (720 x 900) and the frame is the
reference's frame, so the render can be laid over it. The card is the reference's own card: its
type, logo and handwriting are lifted from the photograph as an ink plate (studio/assets/plate.png),
and only the portrait is replaced.

Uses the copy stand and the glass from the oeusume studio, and its headless Chromium for
studio/assets/overlay.png (see studio/plate.html). Run from the repository root:

    blender -b --factory-startup -P studio/badge.py -- [--scale 0.5] [--samples 64]

Writes public/objects/badge.avif. Set OEUSUME if that checkout is not in ~/Documents/oeusume.
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
from mathutils import Matrix, Vector  # noqa: E402

import stage as stage_module  # noqa: E402
from objects.form import glass  # noqa: E402
from paint import blur, cloud, linear  # noqa: E402
from solids import principled, prism, rect, ring, torus, worn  # noqa: E402
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
RING_AT, RING_TALL, RING_WIDE, RING_WIRE = (393, 35), 45, 36, 8.0

# The mat stands in for the page. It is painted darker than the page because the stand lights it brighter
# than its albedo, and what shows through the vinyl has to land on the reference's greys.
MAT = "#dddddb"
PROP = 0.2  # the holder rides this far off the mat
SHEET = 0.07  # thickness of the vinyl
LIFT = 0.1  # how far the front sheet stands off the backing, with the card between
TINT = 0.962  # what one surface of the vinyl lets through


def em(value):
    return value / PX


def box(x0, y0, x1, y1, r=0.0, steps=10):
    return rect(em(x0), em(y0), em(x1), em(y1), em(r), steps)


def vinyl():
    """The studio's glass as clear vinyl. The studio lets light straight through its glass, so what lies
    under it is not left in the dark. Flat vinyl does the same here, but where the sheet turns, at a ridge,
    a bevel or a cut edge, the light is bent away and does not arrive underneath. Those turns are let cast
    their shadow, so every weld and edge lays a thin dark line on the side away from the lamp. What gets
    through by refraction alone is still traced, and that is the bright line beside it."""
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
    passes.inputs["To Max"].default_value = TINT
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
    seen.inputs["To Max"].default_value = TINT
    through = nodes.new("ShaderNodeCombineColor")
    links.new(level.outputs[0], seen.inputs["Value"])
    for channel in ("Red", "Green", "Blue"):
        links.new(seen.outputs["Result"], through.inputs[channel])
    for node in nodes:
        if node.bl_idname == "ShaderNodeBsdfRefraction":
            links.new(through.outputs["Color"], node.inputs["Color"])
            node.inputs["IOR"].default_value = 1.47
        if node.bl_idname == "ShaderNodeFresnel":
            node.inputs["IOR"].default_value = 1.47
    return material


def passes_light(material):
    """Let shadow rays through a Principled material, so a film of plastic does not sit in its own shadow."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    path = nodes.new("ShaderNodeLightPath")
    clear = nodes.new("ShaderNodeBsdfTransparent")
    either = nodes.new("ShaderNodeMixShader")
    links.new(path.outputs["Is Shadow Ray"], either.inputs[0])
    links.new(nodes["Principled BSDF"].outputs["BSDF"], either.inputs[1])
    links.new(clear.outputs[0], either.inputs[2])
    links.new(either.outputs[0], nodes["Material Output"].inputs["Surface"])
    return material


def uneven(material, scale, low, stretch=(1.0, 1.0, 1.0)):
    """Break up a material's opacity with noise. Nothing on real plastic is ruled: a line thins and
    thickens along its length, and a frosted patch is cloudier in places."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = stretch
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.65
    spread = nodes.new("ShaderNodeMapRange")
    spread.inputs["From Min"].default_value = 0.3
    spread.inputs["From Max"].default_value = 0.7
    spread.inputs["To Min"].default_value = low * shader.inputs["Alpha"].default_value
    spread.inputs["To Max"].default_value = shader.inputs["Alpha"].default_value
    links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], spread.inputs["Value"])
    links.new(spread.outputs["Result"], shader.inputs["Alpha"])
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
    """The two eyelet holes and the slot, as outlines."""
    return [ring(em(x), em(y), em(EYELET_HOLE), 64) for x, y in EYELETS] + [box(*SLOT, steps=14)]


def holder():
    """One piece of clear vinyl: the front sheet, the welded rim round it, the zip across the mouth and the
    pressed eyelets, with the holes punched through. The back sheet is left out: it lies flat on the mat
    and shows nothing."""
    clear = vinyl()
    outline = box(*HOLDER, steps=14)
    x0, y0, x1, y1, r = POCKET
    z0 = PROP
    top = z0 + LIFT
    end = top + SHEET

    sheet = prism(STAGE, "holder", outline, top, end, clear)
    # The weld is a low flat bead all the way round. Its top lets light through; its rounded edges turn it.
    parts = [rework(prism(STAGE, "rim", outline, z0, end + 0.09, clear), [box(x0, y0, x1, y1, r, 14)], bevel=0.075, segments=5)]
    # The header is the two sheets fused, so it is solid from the mat side up.
    parts.append(prism(STAGE, "header", box(x0 - 2, y0 - 2, x1 + 2, HEADER_END, r, 14), z0, top + 0.01, clear))
    for i, (ya, yb) in enumerate(ZIP):
        parts.append(rework(prism(STAGE, f"zip-{i}", box(x0 - 2, ya, x1 + 2, yb), end - 0.02, end + 0.14, clear), bevel=0.1, segments=5))
        parts.append(prism(STAGE, f"zip-under-{i}", box(x0 - 2, ya + 3, x1 + 2, yb + 3), top - 0.1, top + 0.02, clear))
    for i, (x, y) in enumerate(EYELETS):
        lip = prism(STAGE, f"eyelet-{i}", ring(em(x), em(y), em(EYELET_RIM + 3.2), 72), end - 0.02, end + 0.1, clear)
        parts.append(rework(lip, [ring(em(x), em(y), em(EYELET_RIM - 2.6), 72)], bevel=0.075, segments=5))
    rework(sheet, punches(), bevel=0.035, segments=3, join=parts)

    # Where the press came down it left hairline seams: inside the weld, round the outer edge, either side
    # of the zip and round the slot. Each is a narrow cut with steep walls, and steep vinyl turns light away,
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
            rework(prism(STAGE, "seam-zip-a", box(x0 + 2, ZIP[0][0] - 2.6, x1 - 2, ZIP[0][0] - 1.1), low, high, None), bevel=em(0.68), segments=2),
            rework(prism(STAGE, "seam-zip-b", box(x0 + 2, ZIP[-1][1] + 1.1, x1 - 2, ZIP[-1][1] + 2.6), low, high, None), bevel=em(0.68), segments=2),
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

    # Fused vinyl is cloudy: the header reads greyer than the pocket, and so does the bed of the zip.
    frost = uneven(passes_light(principled("frost", (0.5, 0.5, 0.51), rough=0.42, specular_ior_level=0.4, alpha=0.14)), 0.22, 0.8)
    header = rework(prism(STAGE, "frost", box(x0, y0, x1, HEADER_END, r, 14), end + 0.004, end + 0.016, frost), punches())
    bed = uneven(passes_light(principled("zip-bed", (0.36, 0.36, 0.37), rough=0.45, specular_ior_level=0.3, alpha=0.24)), 0.4, 0.75, (0.2, 1.0, 1.0))
    zip_bed = prism(STAGE, "zip-bed", box(x0, ZIP[0][0], x1, ZIP[-1][1]), top - 0.12, top - 0.11, bed)

    # A backing in the mat's own paint, just under the holder. The holder rides a little off the mat, and
    # without this the card's shadow would fall that far and spread; on the backing it stays the thin line
    # it is in the reference.
    paint = principled("backing", MAT, rough=0.8)
    backing = prism(STAGE, "backing", outline, z0 - 0.03, z0 - 0.015, paint)
    backing.visible_camera = False
    backing.visible_shadow = False
    backing["stand"] = "backing"
    return [sheet, header, zip_bed], end


def card_art(rows, cols):
    """The reference's card as linear colour: its ink lifted off the photograph, the portrait replaced."""

    def stored(path):
        image = bpy.data.images.load(path)
        image.colorspace_settings.name = "Non-Color"
        w, h = image.size
        data = np.empty(w * h * 4, dtype=np.float32)
        image.pixels.foreach_get(data)
        bpy.data.images.remove(image)
        return data.reshape(h, w, 4)[::-1, :, :3].astype(np.float64)

    def to_linear(v):
        return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)

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

    stock = np.clip(to_linear(paper) * np.array([1.1, 1.0, 0.925]), 0, 1)
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
    """A chrome ring hooked through the slot: its lowest point sits down in the slot and the rest rises
    toward the top of the frame, where it runs out of shot."""
    steel = worn(principled("steel", (0.78, 0.78, 0.79), rough=0.09, metal=1.0), "Scratches003", 4, 0.16)
    loop = torus(STAGE, "ring", em(RING_TALL), em(RING_WIRE), steel, steps=192, around=28)
    tip = math.radians(11)
    squeeze = Matrix.Diagonal((RING_WIDE / RING_TALL, 1 / math.cos(tip), 1, 1))
    rise = em(RING_TALL) * math.sin(tip)
    loop.matrix_world = Matrix.Translation((em(RING_AT[0]), -em(RING_AT[1]), z + rise)) @ Matrix.Rotation(tip, 4, "X") @ squeeze


def dim_room():
    """What the plastic and the ring reflect: a dark room with a few soft streaks of light in it, seen by
    reflections only. Flat vinyl then lays a faint, uneven sheen over what is under it and the ink stays black."""
    plane = bpy.data.meshes.new("room")
    plane.from_pydata([(-70, -70, 0), (70, -70, 0), (70, 70, 0), (-70, 70, 0)], [], [(0, 1, 2, 3)])
    obj = STAGE.add("room", plane)
    obj["stand"] = "room"
    obj.location = (em(FRAME[0]) / 2, -em(FRAME[1]) / 2, 36)
    for seen in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission"):
        setattr(obj, seen, False)
    material = bpy.data.materials.new("room")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    coord = nodes.new("ShaderNodeTexCoord")
    stretch = nodes.new("ShaderNodeMapping")
    stretch.inputs["Scale"].default_value = (0.3, 0.035, 1.0)
    stretch.inputs["Rotation"].default_value = (0, 0, math.radians(8))
    cloud = nodes.new("ShaderNodeTexNoise")
    cloud.inputs["Scale"].default_value = 1.0
    cloud.inputs["Detail"].default_value = 3.0
    lift = nodes.new("ShaderNodeMapRange")
    lift.inputs["From Min"].default_value = 0.45
    lift.inputs["From Max"].default_value = 0.75
    lift.inputs["To Min"].default_value = 0.0
    lift.inputs["To Max"].default_value = 1.1
    emit = nodes.new("ShaderNodeEmission")
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(coord.outputs["Object"], stretch.inputs["Vector"])
    links.new(stretch.outputs["Vector"], cloud.inputs["Vector"])
    links.new(cloud.outputs["Fac"], lift.inputs["Value"])
    links.new(lift.outputs["Result"], emit.inputs["Strength"])
    links.new(emit.outputs[0], out.inputs["Surface"])
    # Reflections find these by chance. Sampled as lights they would be picked and then thrown away,
    # since nothing diffuse may see them, and the set would lose that share of its light.
    material.cycles.emission_sampling = "NONE"
    plane.materials.append(material)

    # One long strip light. The camera is orthographic, so flat vinyl mirrors whatever hangs right over it.
    strip = bpy.data.meshes.new("strip")
    strip.from_pydata([(-0.55, -11, 0), (0.55, -11, 0), (0.55, 11, 0), (-0.55, 11, 0)], [], [(0, 1, 2, 3)])
    glow = bpy.data.materials.new("strip")
    glow.use_nodes = True
    gn, gl = glow.node_tree.nodes, glow.node_tree.links
    gn.clear()
    lamp = gn.new("ShaderNodeEmission")
    lamp.inputs["Strength"].default_value = 0.7
    end = gn.new("ShaderNodeOutputMaterial")
    gl.new(lamp.outputs[0], end.inputs["Surface"])
    glow.cycles.emission_sampling = "NONE"
    strip.materials.append(glow)
    light = STAGE.add("strip", strip)
    light["stand"] = "room"
    light.location = (em(141), -em(520), 30)
    for seen in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission"):
        setattr(light, seen, False)


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
    # A big bright box beside the key that only shiny things see. It lights nothing and casts nothing,
    # but every bead of vinyl that leans its way, and the ring, catch it as a white line.
    flash = bpy.data.lights.new("flash", "AREA")
    flash.size = 13
    flash.energy = 150000
    flash.color = (0.88, 0.91, 1.0)
    spark = STAGE.add("flash", flash)
    spark["stand"] = "key"
    spark.location = target + Vector((14, -32, 27))
    spark.rotation_euler = (target - spark.location).to_track_quat("-Z", "Y").to_euler()
    spark.visible_diffuse = False
    spark.visible_transmission = False
    plastic, end = holder()
    card(PROP + 0.07)
    steel_ring(PROP + LIFT + SHEET / 2)
    dim_room()
    cx, cy = em(FRAME[0]) / 2, -em(FRAME[1]) / 2
    STAGE.shoot(
        "badge",
        (0, 0, em(FRAME[0]), em(FRAME[1])),
        bleed=0.0,
        shadow=0.1,
        exposure=0.88,
        room=0.95,
        mat_through_glass=True,
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
