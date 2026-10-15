"""The resume, lying on the desk to the right of the folders: the page printed, rolled up with the print outward, tied
round near its foot with red and white baker's twine, and the twine's ends threaded through a manila tag stamped
RÉSUMÉ in red. The page opens public/resume.pdf. Run from the repository root, after studio/resume/art.py:

    blender -b --factory-startup -P studio/resume/resume.py -- [--scale 0.5] [--samples 64] [--proofs DIR]

Writes public/objects/resume.avif. It uses the desk's copy stand (studio/desk), with the dark desk under it and the
contact page's key light (studio/ticket/key.py), so it is lit as the ticket beside it is.

Every measure is in the page's rem. The frame is the desk SiteShell leaves to the right of the folders, END wide,
whose first rem the last folder lies over. The roll and the tag keep to the rest of it.
"""

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "studio", "desk"))
sys.path.insert(0, os.path.join(ROOT, "studio", "ticket"))

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402

import key as key_light  # noqa: E402
import stage as stage_module  # noqa: E402
from paint import blur, box, cloud, disc, linear, ramp  # noqa: E402
from solids import principled  # noqa: E402
from stage import Stage  # noqa: E402
from stock import Sheet, fit, pixels_of  # noqa: E402

ART = os.path.join(HERE, "art")
OUT = os.path.join(ROOT, "public", "objects")

DESK = "#1f1e1b"  # SiteShell's desk
# The frame, which the page reads too: END is useStackMetrics' end, the first rem of it under the last folder.
FRAME = json.load(open(os.path.join(ROOT, "src", "components", "resume.json")))
(END, HEIGHT), BLEED = FRAME["size"], FRAME["bleed"]

# The roll: an A4 sheet, its 210 mm along the roll, at MM millimetres to the em.
MM = 210 / 16.0
LENGTH, PAGE = 210 / MM, 297 / MM
OUTER, INNER = 0.7, 0.25  # radius of the outside turn and of the hole down the middle
TELESCOPE = 0.12  # how far the outside turn has crept along past the inside one
ACROSS = 2.1  # the roll's middle, from the frame's left
HEAD = 0.5  # where its top end lies
NAME_AT = 1.3  # em down the page to the name, which faces up
FLAP, LIFT = 0.45, 0.05  # the last of the page springs off the roll this far over this much of its end
PAPER = "#f3f2ee"
TONER = "#1b1a19"

# The twine: cotton, red and white twisted, wound twice round the roll this far up from its foot.
TWINE = 0.055
TIE = 3.2
TWINE_WHITE, TWINE_RED = "#efece4", "#c4252b"

# The tag: a manila shipping tag, its head's corners cut off, a hole through a gummed card ring.
TAG_W, TAG_H = 1.95, 5.25
TAG_TOP = LENGTH + HEAD + 1.15
TAG_ACROSS = 2.1  # its middle
TAG_TURN = -3.0  # degrees clockwise
CLIP = 0.36  # the cut corners
HOLE, RING = 0.11, 0.3
HOLE_DOWN = 0.62
MANILA = "#d8bd86"
STAMP = "#d0232b"


def lie(points, turn, pivot):
    """Turn points (x, y on the frame) clockwise about a pivot by degrees."""
    c, s = math.cos(math.radians(turn)), math.sin(math.radians(turn))
    px, py = pivot
    return [(px + (x - px) * c - (y - py) * s, py + (x - px) * s + (y - py) * c) for x, y in points]


def page():
    """The printed sheet, the page's top at y = 0 and its left edge at x = 0: white bond with toner fused onto it,
    which is a little glossier than the paper."""
    sheet = Sheet(LENGTH, PAGE, PAPER, rough=0.62, density=2.6)
    shape = sheet.height.shape
    sheet.rgb *= (1 + 0.01 * cloud(shape, 3, falloff=1.2))[..., None]
    grey = pixels_of(os.path.join(ART, "page.png"))[..., 0].astype(np.float64)
    toner = 1 - fit(grey[..., None], *shape)[..., 0]
    toner = np.clip(toner * 1.08, 0, 1)
    sheet.ink(toner, TONER)
    sheet.finish(toner, rough=0.4)
    sheet.height += 0.0004 * toner
    # The roll has been handled at its ends more than its middle.
    X = sheet.X
    ends = np.minimum(X, LENGTH - X)
    sheet.rgb *= (1 - 0.035 * (1 - ramp(0, 1.2, ends)) * np.clip(1 + 0.5 * cloud(shape, 5, falloff=1.4), 0, 2))[..., None]
    return sheet


def roll(stage):
    """Lay the sheet out flat, then wind it: the page's top is the outside end, and the page's left edge is the
    roll's head, so the lines run down the desk and the name, near the top of the page, lies face up."""
    sheet = page()
    obj = sheet.build(
        stage,
        "roll",
        thickness=0.0,
        solid=False,
        step=0.04,
        scan="Paper001",
        scan_size=5,
        scan_normal=0.35,
        scan_rough=0.4,
        scan_colour=0.15,
        fibre=0.0006,
        sheen=0.2,
    )
    mesh = obj.data
    co = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    along, down = co[:, 0], -co[:, 1]  # along the page's width, and down its height from its top

    # An Archimedean spiral from the inner end, out: r = INNER + a theta, its arc length INNER theta + a theta^2 / 2.
    turns = 2 * PAGE / (INNER + OUTER)
    a = (OUTER - INNER) / turns
    inward = PAGE - down
    theta = (-INNER + np.sqrt(INNER**2 + 2 * a * inward)) / a
    r = INNER + a * theta + LIFT * (1 - np.clip(down / FLAP, 0, 1)) ** 2
    # Angle round the roll from the desk's right, up: the name's line faces straight up, and the lines further down the
    # page lie further round to the left, as the page winds in.
    psi = math.pi / 2 - NAME_AT / OUTER + (turns - theta)
    centre = OUTER + 0.01
    x = ACROSS + r * np.cos(psi)
    z = centre + r * np.sin(psi)
    y = HEAD + along + TELESCOPE * (theta / turns - 0.5)
    mesh.vertices.foreach_set("co", np.column_stack((x, -y, z)).ravel())
    mesh.update()
    # The print faces out.
    normals = np.empty(len(mesh.polygons) * 3)
    mesh.polygons.foreach_get("normal", normals)
    centres = np.empty(len(mesh.polygons) * 3)
    mesh.polygons.foreach_get("center", centres)
    normals, centres = normals.reshape(-1, 3), centres.reshape(-1, 3)
    outward = (centres[:, 0] - ACROSS) * normals[:, 0] + (centres[:, 2] - centre) * normals[:, 2]
    if np.mean(outward) < 0:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
        bm.to_mesh(mesh)
        bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def tube(stage, name, points, radius, material, twist=0.5, sides=10):
    """A cord along a polyline (x, y on the frame, z up), its two plies twisted round each other every `twist` em.
    The material reads the twist from the UV map: U along the cord in em, V round it."""
    points = np.asarray(points, dtype=np.float64)
    tangents = np.gradient(points, axis=0)
    tangents /= np.linalg.norm(tangents, axis=1)[:, None]
    # Frames carried along the cord without turning about it.
    up = np.array([0.0, 0.0, 1.0]) if abs(tangents[0, 2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    normal = np.cross(tangents[0], up)
    normal /= np.linalg.norm(normal)
    normals = [normal]
    for t in tangents[1:]:
        n = normals[-1] - t * np.dot(normals[-1], t)
        normals.append(n / np.linalg.norm(n))
    normals = np.array(normals)
    binormals = np.cross(tangents, normals)
    lengths = np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))))
    verts, uvs, faces = [], [], []
    for i, p in enumerate(points):
        for k in range(sides + 1):
            phi = 2 * math.pi * k / sides
            # Two plies: the cord's section is a little lobed, and the lobes turn with the twist.
            lobe = 1 + 0.12 * math.cos(2 * (phi - 2 * math.pi * lengths[i] / twist))
            v = p + radius * lobe * (math.cos(phi) * normals[i] + math.sin(phi) * binormals[i])
            verts.append((v[0], -v[1], v[2]))
            uvs.append((lengths[i], k / sides))
    ring = sides + 1
    for i in range(len(points) - 1):
        for k in range(sides):
            faces.append((i * ring + k, i * ring + k + 1, (i + 1) * ring + k + 1, (i + 1) * ring + k))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    layer = mesh.uv_layers.new()
    loops = np.empty(len(mesh.loops), dtype=np.int32)
    mesh.loops.foreach_get("vertex_index", loops)
    layer.data.foreach_set("uv", np.asarray(uvs)[loops].ravel())
    mesh.polygons.foreach_set("use_smooth", [True] * len(faces))
    mesh.materials.append(material)
    return stage.add(name, mesh)


def twine_material(twist):
    """Baker's twine: two plies, one red and one white, each a bundle of fibres, matt cotton with fuzz."""
    material = principled("twine", TWINE_WHITE, rough=0.85, sheen_weight=0.6, sheen_roughness=0.4)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    uv = nodes.new("ShaderNodeUVMap")
    split = nodes.new("ShaderNodeSeparateXYZ")
    links.new(uv.outputs["UV"], split.inputs["Vector"])
    # The plies' stripe runs round the cord as it goes along it: a phase of along / twist + round.
    along = nodes.new("ShaderNodeMath")
    along.operation = "MULTIPLY_ADD"
    along.inputs[1].default_value = 1 / twist
    links.new(split.outputs["X"], along.inputs[0])
    links.new(split.outputs["Y"], along.inputs[2])
    phase = nodes.new("ShaderNodeMath")
    phase.operation = "FRACT"
    links.new(along.outputs[0], phase.inputs[0])
    # Each ply takes half the turn, so the red and the white alternate twice round the cord.
    doubled = nodes.new("ShaderNodeMath")
    doubled.operation = "PINGPONG"
    doubled.inputs[1].default_value = 0.5
    scaled = nodes.new("ShaderNodeMath")
    scaled.operation = "MULTIPLY"
    scaled.inputs[1].default_value = 2.0
    links.new(phase.outputs[0], scaled.inputs[0])
    links.new(scaled.outputs[0], doubled.inputs[0])
    which = nodes.new("ShaderNodeMapRange")
    which.inputs["From Min"].default_value = 0.2
    which.inputs["From Max"].default_value = 0.3
    links.new(doubled.outputs[0], which.inputs["Value"])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (*linear(TWINE_WHITE), 1)
    mix.inputs[7].default_value = (*linear(TWINE_RED), 1)
    links.new(which.outputs[0], mix.inputs[0])
    links.new(mix.outputs[2], shader.inputs["Base Color"])
    # The fibres of each ply lie at a steeper angle than the ply does, and where the plies meet there is a groove.
    fibre = nodes.new("ShaderNodeTexWave")
    fibre.wave_type = "BANDS"
    fibre.bands_direction = "DIAGONAL"
    fibre.inputs["Scale"].default_value = 26.0
    fibre.inputs["Distortion"].default_value = 3.0
    fibre.inputs["Detail"].default_value = 4.0
    links.new(uv.outputs["UV"], fibre.inputs["Vector"])
    groove = nodes.new("ShaderNodeMath")
    groove.operation = "MULTIPLY"
    links.new(fibre.outputs["Color"], groove.inputs[0])
    links.new(doubled.outputs[0], groove.inputs[1])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.01
    bump.inputs["Strength"].default_value = 0.6
    links.new(groove.outputs[0], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return material


def twine(stage):
    """Two turns round the roll, crossed into a knot on its top, and the two ends run down off its foot onto the desk
    and through the tag's hole."""
    material = twine_material(0.42)
    centre = OUTER + 0.01
    around = OUTER + TWINE
    foot = HEAD + LENGTH
    tie = foot - TIE
    rng = np.random.default_rng(4)

    def onroll(y, psi):
        return (ACROSS + around * math.cos(psi), y, centre + around * math.sin(psi))

    pieces = []
    # The turns: each a full loop, a little apart, the second crossing the first at the knot.
    for y0, y1 in ((tie - 0.07, tie + 0.09), (tie + 0.11, tie - 0.05)):
        steps = 72
        loop = []
        for k in range(steps + 1):
            t = k / steps
            psi = math.pi / 2 + 0.18 + 2 * math.pi * t
            loop.append(onroll(y0 + (y1 - y0) * t, psi))
        pieces.append(loop)

    # The knot: the ends wrapped over each other once, standing a little proud of the turns.
    knot = []
    for k in range(40):
        t = k / 39
        psi = math.pi / 2 + 0.18 + 0.5 * math.sin(2 * math.pi * t)
        knot.append(
            (
                ACROSS + (around + TWINE * 1.2) * math.cos(psi),
                tie + 0.02 + 0.12 * math.cos(2 * math.pi * t),
                centre + (around + TWINE * 1.2) * math.sin(psi),
            )
        )
    pieces.append(knot)

    # The ends, from the knot down the top of the roll, off its foot and across the desk to the hole.
    hole = lie([(TAG_ACROSS, TAG_TOP + HOLE_DOWN)], TAG_TURN, (TAG_ACROSS, TAG_TOP + TAG_H / 2))[0]
    for side, spread in ((-1, 0.09), (1, 0.06)):
        psi = math.pi / 2 + 0.18 + side * 0.15
        start = onroll(tie + 0.1, psi)
        over = onroll(foot - 0.05, math.pi / 2 + 0.1 + side * 0.22)
        drop = (over[0] + side * 0.04, foot + 0.35, TWINE * 1.4)
        lying = (hole[0] + side * spread + 0.08 * rng.standard_normal(), (foot + hole[1]) / 2 + 0.1, TWINE)
        near = (hole[0] + side * 0.05, hole[1] - 0.2, 0.11)
        into = (hole[0] + side * 0.04, hole[1], -0.02)
        control = [start, over, drop, lying, near, into]
        # A smooth line through the points.
        pts = np.array(control)
        t = np.concatenate(([0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))))
        fine = np.linspace(0, t[-1], 160)
        path = np.column_stack([np.interp(fine, t, pts[:, i]) for i in range(3)])
        for _ in range(12):
            path[1:-1] = 0.25 * path[:-2] + 0.5 * path[1:-1] + 0.25 * path[2:]
        # The first stretch lies on the roll, not through it.
        x0 = path[:, 0] - ACROSS
        z0 = path[:, 2] - centre
        r = np.hypot(x0, z0)
        onto = path[:, 1] < foot - 0.02
        scale = np.where(onto, np.maximum(r, around) / np.maximum(r, 1e-6), 1)
        path[:, 0] = ACROSS + x0 * scale
        path[:, 2] = centre + z0 * scale
        pieces.append([tuple(p) for p in path])
    return [tube(stage, f"twine-{i}", piece, TWINE, material) for i, piece in enumerate(pieces)]


def tag(stage):
    """The manila tag, stamped, its hole punched through a ring of thicker card gummed on round it."""
    sheet = Sheet(TAG_W, TAG_H, MANILA, rough=0.78, density=3)
    X, Y = sheet.X, sheet.Y
    shape = sheet.height.shape
    # The head's corners cut off at forty-five degrees.
    cut = np.maximum(box(X, Y, 0, 0, TAG_W, TAG_H), np.maximum((CLIP - X - Y) / math.sqrt(2), (X - (TAG_W - CLIP) - Y) / math.sqrt(2)))
    sheet.cut(cut)
    sheet.rgb *= (1 + 0.04 * cloud(shape, 22, falloff=1.3))[..., None]
    # Kraft fibre flecks.
    sheet.ink(np.clip(cloud(shape, 23, falloff=0.2) - 2.2, 0, 1), "#8a6a3a", 0.5)
    ring = disc(X, Y, TAG_W / 2, HOLE_DOWN, RING)
    patch = sheet.mask(ring)
    sheet.paint(patch * 0.5, "#cfb27a")
    sheet.height += 0.008 * patch
    sheet.height -= 0.003 * sheet.mask(ring + 0.025) * (1 - patch)
    # The stamp, inked unevenly, pressed a little harder at one end, a touch off square.
    stamp = pixels_of(os.path.join(ART, "stamp.png"))
    sw = 1.24
    sh = sw * stamp.shape[0] / stamp.shape[1]
    x0, y0 = (TAG_W - sw) / 2 + 0.03, HOLE_DOWN + RING + 0.34
    r0, r1, c0, c1 = (round(v * sheet.ppe) for v in (y0, y0 + sh, x0, x0 + sw))
    face = fit(stamp[..., 3:].astype(np.float64), r1 - r0, c1 - c0)[..., 0]
    ink = np.zeros(shape)
    ink[r0:r1, c0:c1] = face
    ink = blur(ink, 0.6)
    pressure = np.clip(0.9 + 0.1 * cloud(shape, 24, falloff=1.6) + 0.08 * (Y - y0) / sh, 0, 1)
    voids = np.clip(2.2 + cloud(shape, 25, falloff=1.1), 0, 1)
    sheet.ink(ink * pressure * voids, STAMP, 1.0)
    sheet.punch(disc(X, Y, TAG_W / 2, HOLE_DOWN, HOLE))
    # Grime where it is held.
    grime = (1 - ramp(0, 0.5, -sheet.sdf)) * 0.06
    sheet.rgb *= (1 - grime)[..., None]
    sheet.soften(0.03, 0.006)
    corner = lie([(TAG_ACROSS - TAG_W / 2, TAG_TOP)], TAG_TURN, (TAG_ACROSS, TAG_TOP + TAG_H / 2))[0]
    obj = sheet.build(
        stage,
        "tag",
        thickness=0.03,
        step=0.12,
        warp=lambda x, y: 0.012 * np.sin(1.3 + 0.5 * y) + 0.008 * np.cos(0.9 * x),
        scan="Paper002",
        scan_size=4,
        scan_normal=0.5,
        scan_rough=0.6,
        scan_colour=0.25,
        sheen=0.2,
    )
    # Turn it about its own top left corner into place.
    obj.rotation_euler = (0, 0, math.radians(-TAG_TURN))
    obj.location = (corner[0], -corner[1], 0)
    return obj


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument("--proofs")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])

    stage_module.MAT = DESK
    stage_module.SHADOW = np.array([0.0035, 0.003, 0.0026])
    out = OUT if args.scale == 1 and not args.proofs else (args.proofs or "/tmp")
    stage = Stage(out, args.proofs, scale=args.scale, samples=args.samples)
    stage.clear()
    roll(stage)
    twine(stage)
    tag(stage)
    key_light.add((END / 2, -HEIGHT / 2))
    stage.shoot("resume", (0, 0, END, HEIGHT), bleed=BLEED, shadow=0.9, exposure=0.05 - 2.5)


main()
