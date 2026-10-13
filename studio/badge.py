"""ID badge: a copy of the reference photograph, a printed card in a clear vinyl holder on a steel ring.

Every measurement is taken off the reference in its own pixels (720 x 900) and the frame is the
reference's frame, so the render can be laid over it. The card is the reference's own card: its
type, logo and handwriting are lifted from the photograph as an ink plate (studio/assets/plate.png),
and only the portrait is replaced.

Uses the copy stand and the glass from the oeusume studio. Run from the repository root:

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

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import stage as stage_module  # noqa: E402
from objects.form import glass, window  # noqa: E402
from paint import blur, linear  # noqa: E402
from solids import annulus, finish, plate, principled, prism, rect, ring, torus, worn  # noqa: E402
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
RING_AT, RING_TALL, RING_WIDE, RING_WIRE = (393, 35), 45, 36, 8.0

# The mat stands in for the page. It is painted darker than the page because the stand lights it brighter
# than its albedo, and what shows through the vinyl has to land on the reference's greys.
MAT = "#dddddb"
PROP = 0.4  # the ring passes under the header, so the holder rides this far off the mat
SHEET = 0.06
GAP = 0.06
TINT = 0.986  # what one surface of the vinyl lets through


def em(value):
    return value / PX


def box(x0, y0, x1, y1, r=0.0, steps=10):
    return rect(em(x0), em(y0), em(x1), em(y1), em(r), steps)


def vinyl(name, tint=TINT, haze=0.0, wave=0.3):
    """The studio's glass as clear vinyl: no green cast, a grey tint per surface, and a slow wave in the
    normal, because thin sheet is never dead flat. haze frosts what is seen through it, as a weld does."""
    material = glass()
    material.name = name
    nodes, links = material.node_tree.nodes, material.node_tree.links
    coord = nodes.new("ShaderNodeTexCoord")
    scale = nodes.new("ShaderNodeMapping")
    scale.inputs["Scale"].default_value = (0.12, 0.05, 1.0)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.0
    noise.inputs["Detail"].default_value = 2.0
    bend = nodes.new("ShaderNodeBump")
    bend.inputs["Strength"].default_value = wave
    bend.inputs["Distance"].default_value = 0.3
    links.new(coord.outputs["Object"], scale.inputs["Vector"])
    links.new(scale.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], bend.inputs["Height"])
    for node in nodes:
        if node.bl_idname in ("ShaderNodeBsdfRefraction", "ShaderNodeBsdfTransparent"):
            node.inputs["Color"].default_value = (tint, tint * 0.9965, tint * 0.998, 1)
        if node.bl_idname == "ShaderNodeBsdfRefraction":
            node.inputs["Roughness"].default_value = haze
        if wave and node.bl_idname in ("ShaderNodeBsdfRefraction", "ShaderNodeBsdfGlossy"):
            links.new(bend.outputs["Normal"], node.inputs["Normal"])
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


def rework(obj, cutters=(), bevel=0.0, segments=3):
    """Cut outlines through a prism and round every hard edge left. Both need the bare mesh."""
    for name in [m.name for m in obj.modifiers]:
        obj.modifiers.remove(obj.modifiers[name])
    bpy.context.view_layer.objects.active = obj
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
    for face in obj.data.polygons:
        face.use_smooth = True
    weighted = obj.modifiers.new("normals", "WEIGHTED_NORMAL")
    weighted.keep_sharp = True
    weighted.weight = 100
    return obj


def band(name, outer, inner, z, material):
    """A flat strip between two outlines with the same number of points: a line that follows a contour."""
    bm = bmesh.new()
    a = [bm.verts.new((x, -y, z)) for x, y in outer]
    b = [bm.verts.new((x, -y, z)) for x, y in inner]
    for i in range(len(a)):
        j = (i + 1) % len(a)
        bm.faces.new((a[i], a[j], b[j], b[i]))
    return finish(STAGE, name, bm, material)


def contour(name, x0, y0, x1, y1, r, width, z, material, steps=14):
    """A line of the given width, in reference pixels, centred on a rounded rectangle."""
    h = width / 2
    return band(name, box(x0 - h, y0 - h, x1 + h, y1 + h, r + h, steps), box(x0 + h, y0 + h, x1 - h, y1 - h, max(r - h, 0.01), steps), z, material)


def punches():
    """The two eyelet holes and the slot, as outlines."""
    return [ring(em(x), em(y), em(EYELET_HOLE), 64) for x, y in EYELETS] + [box(*SLOT, steps=14)]


def holder():
    clear = vinyl("vinyl")
    weld = vinyl("weld", tint=0.95, haze=0.2, wave=0.5)
    outline = box(*HOLDER, steps=14)
    inside = box(*POCKET, steps=14)
    z0 = PROP
    top = z0 + SHEET + GAP
    end = top + SHEET
    made = []
    x0, y0, x1, y1, r = POCKET

    back = rework(prism(STAGE, "back", inside, z0, z0 + SHEET, clear), punches(), bevel=0.012, segments=2)
    front = rework(prism(STAGE, "front", inside, top, end, clear), punches(), bevel=0.012, segments=2)
    made += [back, front]

    # The rim is the two sheets fused: a low rounded ridge of solid plastic all the way round.
    rim = rework(prism(STAGE, "rim", outline, z0, end + 0.05, weld), [box(x0 - 0.3, y0 - 0.3, x1 + 0.3, y1 + 0.3, r, 14)], bevel=0.085, segments=4)
    made.append(rim)

    # The header is fused flat, which leaves it greyer than the pocket.
    frost = uneven(passes_light(principled("frost", (0.5, 0.5, 0.51), rough=0.42, specular_ior_level=0.4, alpha=0.27)), 0.22, 0.8)
    header = rework(prism(STAGE, "header", box(x0, y0, x1, HEADER_END, r, 14), end + 0.004, end + 0.016, frost), punches())
    made.append(header)

    # The zip sits on a fused strip, and the fold under it holds a little shade.
    bed = uneven(passes_light(principled("zip-bed", (0.36, 0.36, 0.37), rough=0.45, specular_ior_level=0.3, alpha=0.68)), 0.4, 0.75, (0.2, 1.0, 1.0))
    made.append(prism(STAGE, "zip-bed", box(x0, ZIP[0][0], x1, ZIP[-1][1]), end + 0.004, end + 0.014, bed))
    shade = uneven(passes_light(principled("shade", (0.2, 0.2, 0.21), rough=0.6, specular_ior_level=0.0, alpha=0.2)), 0.5, 0.6)
    made.append(plate(STAGE, "shade-mouth", box(x0, ZIP[-1][1], x1, ZIP[-1][1] + 12), end + 0.02, shade))

    # The zip: three ridges across the mouth of the pocket.
    for i, (ya, yb) in enumerate(ZIP):
        made.append(rework(prism(STAGE, f"zip-{i}", box(x0 + 1, ya, x1 - 1, yb), end + 0.004, end + 0.11, weld), bevel=0.05, segments=4))

    # Eyelets are pressed, which raises a ring round each hole.
    for i, (x, y) in enumerate(EYELETS):
        lip = torus(STAGE, f"eyelet-{i}", em(EYELET_RIM), 0.055, weld, steps=96, around=14)
        lip.location = (em(x), -em(y), end + 0.06)
        made.append(lip)

    # Where the sheet turns an edge it shows as a thin dark line, as the cut edge of any clear plastic does.
    dark = uneven(passes_light(principled("edge", (0.03, 0.033, 0.036), rough=0.5, specular_ior_level=0.0, alpha=0.92)), 1.4, 0.45)
    faint = uneven(passes_light(principled("edge-faint", (0.1, 0.105, 0.11), rough=0.5, specular_ior_level=0.0, alpha=0.62)), 1.1, 0.4)
    shine = uneven(passes_light(principled("edge-shine", (1.0, 1.0, 1.0), rough=0.3, specular_ior_level=0.0, alpha=0.95)), 2.2, 0.25, (0.25, 1.0, 1.0))
    hx0, hy0, hx1, hy1, hr = HOLDER
    made.append(contour("line-outer", hx0 + 1, hy0 + 1, hx1 - 1, hy1 - 1, hr - 1, 1.6, end + 0.075, faint))
    made.append(contour("line-inner", x0, y0, x1, y1, r, 1.8, end + 0.03, dark))
    made.append(contour("shine-rim", x0 - 3.2, y0 - 3.2, x1 + 3.2, y1 + 3.2, r + 3.2, 2.2, end + 0.08, shine))
    for i, y in enumerate((ZIP[0][0], ZIP[-1][1])):
        made.append(plate(STAGE, f"line-zip-{i}", box(x0, y - 0.8, x1, y + 0.8), end + 0.125, dark))
    for i, (ya, yb) in enumerate(ZIP):
        mid = (ya + yb) / 2
        made.append(plate(STAGE, f"shine-zip-{i}", box(x0 + 2, mid - 1.1, x1 - 2, mid + 1.1), end + 0.127, shine))
    for i, (ya, yb) in enumerate(ZIP[:-1]):
        mid = (yb + ZIP[i + 1][0]) / 2
        made.append(plate(STAGE, f"line-zip-mid-{i}", box(x0, mid - 0.45, x1, mid + 0.45), end + 0.02, faint))
    for i, (x, y) in enumerate(EYELETS):
        made.append(annulus(STAGE, f"line-eyelet-{i}", em(x), em(y), em(EYELET_HOLE - 0.7), em(EYELET_HOLE + 0.9), end + 0.03, dark))
    sx0, sy0, sx1, sy1, sr = SLOT
    made.append(contour("line-slot", sx0, sy0, sx1, sy1, sr, 1.6, end + 0.03, dark))

    # The light comes from the lower right. The left weld leans away from it and reads grey, the right one
    # shades the strip of pocket beside it, and both throw a hard line where they turn.
    deep = uneven(passes_light(principled("shade-deep", (0.2, 0.2, 0.21), rough=0.6, specular_ior_level=0.0, alpha=0.34)), 0.5, 0.7)
    made.append(plate(STAGE, "shade-left", box(hx0 + 1, y0 + 14, x0 - 1, y1 - 14), end + 0.078, deep))
    made.append(plate(STAGE, "shade-right", box(x1 - 11, y0 + 150, x1 - 2, y1 - 20), end + 0.02, shade))
    made.append(plate(STAGE, "line-left-outer", box(hx0 + 0.4, hy0 + 26, hx0 + 2.2, hy1 - 26), end + 0.08, dark))
    made.append(plate(STAGE, "line-right-outer", box(hx1 - 2.0, hy0 + 26, hx1 - 0.4, hy1 - 26), end + 0.08, dark))
    made.append(plate(STAGE, "line-left-inner", box(x0 - 0.3, y0 + 14, x0 + 1.9, y1 - 14), end + 0.035, dark))
    made.append(plate(STAGE, "shine-left-a", box(x0 - 3.2, y0 + 20, x0 - 1.2, y1 - 20), end + 0.082, shine))
    made.append(plate(STAGE, "shine-left-b", box(x0 + 2.4, y0 + 110, x0 + 6.0, y1 - 20), end + 0.036, shine))

    # A backing in the mat's own paint, just under the holder. The holder rides off the mat to let the ring
    # through, and without this the card's shadow would fall that far and spread; on the backing it stays
    # the thin line it is in the reference. It is cut away under the ring, which has to be seen beneath.
    paint = principled("backing", MAT, rough=0.8)
    backing = rework(prism(STAGE, "backing", outline, z0 - 0.03, z0 - 0.015, paint), [box(342, 12, 446, 99, 6)])
    backing.visible_camera = False
    backing.visible_shadow = False
    backing["stand"] = "backing"
    return made, end


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

    # Clear the old portrait and its box, then print the box again as a hairline.
    guide = box_distance(*GUIDE)
    ink[guide < 3 * sx] = 0
    ink = np.maximum(ink, 0.42 * np.clip(1.2 - np.abs(guide) / (0.55 * sx), 0, 1))
    # The reference's card sits a touch askew, so its own edge shadow strays onto the plate. This card casts its own.
    ink[:, : round(9 * sx)] = 0

    stock = np.clip(to_linear(paper) * np.array([1.1, 0.975, 0.855]), 0, 1)
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
    """A chrome ring through the slot, tipped so its left arc runs under the header and its right arc over."""
    steel = worn(principled("steel", (0.78, 0.78, 0.79), rough=0.09, metal=1.0), "Scratches003", 4, 0.16)
    loop = torus(STAGE, "ring", em(RING_TALL), em(RING_WIRE), steel, steps=192, around=28)
    tip = math.radians(15)
    squeeze = Matrix.Diagonal((RING_WIDE / RING_TALL / math.cos(tip), 1, 1, 1))
    loop.matrix_world = Matrix.Translation((em(RING_AT[0]), -em(RING_AT[1]), z)) @ Matrix.Rotation(-tip, 4, "Y") @ squeeze


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
    lift.inputs["To Max"].default_value = 0.55
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
    key.energy = 6500
    lamp = STAGE.add("key", key)
    lamp["stand"] = "key"
    target = Vector((em(FRAME[0]) / 2, -em(FRAME[1]) / 2, 0))
    lamp.location = target + Vector((15, -34, 26))
    lamp.rotation_euler = (target - lamp.location).to_track_quat("-Z", "Y").to_euler()
    plastic, end = holder()
    card(PROP + SHEET + 0.025)
    steel_ring(PROP + SHEET + GAP / 2)
    dim_room()
    cx, cy = em(FRAME[0]) / 2, -em(FRAME[1]) / 2
    STAGE.shoot(
        "badge",
        (0, 0, em(FRAME[0]), em(FRAME[1])),
        bleed=0.0,
        shadow=0.1,
        exposure=0.6,
        room=0.86,
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
