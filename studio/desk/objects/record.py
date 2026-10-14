"""Seven-inch record: a gloss sleeve printed with the cover of his playlist, the vinyl that slides out of it
with three of its songs cut on the side that shows, and the label that turns."""

import os
import tempfile

import bpy
import numpy as np

from paint import blur, cloud, disc, ramp, segment, streaks
from stage import ASSETS, LENS_HEIGHT
from stock import Sheet, drift, fit, pixels_of

S = 15.625
DISC = 14.5
LABEL = 5.5
# The label takes the orange of the cover.
TINT = "#e2622f"
COVER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art", "two-x-3.jpg")
PAPER = "#f6eedb"
INK = "#1d1613"
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")
# The page shows the record at 1.8 times the size of the other objects, which is its true size beside them.
SHARP = 1.5
# The disc from the centre out, as radii in em: the spindle hole, the locked groove that ends the run-out,
# the last and the first turn of music, the foot of the bead and the rim.
HOLE, LOCK, LAST, FIRST, BEAD, EDGE = 0.3, 3.3, 3.72, 6.96, 7.1, DISC / 2 - 0.012
GAP = 0.085
# The groove's walls as a mirror: how far they throw light across the groove, how little along it, how much.
SPREAD, NARROW, SHINE = 0.31, 0.78, 0.1
# Side one is the first three songs of the playlist: title, artist, seconds.
SIDE = (
    ("Tous les garçons et les filles", "Françoise Hardy", 188),
    ("Haircut", "Ryan Beatty", 216),
    ("Persian Rugs", "PARTYNEXTDOOR", 174),
)
# The catalogue number with the side, and with the cut as it is scratched in the dead wax.
MATRIX = "TX3 001-A1"
RIGHTS = (
    "ALL RIGHTS OF THE PRODUCER AND OF THE OWNER OF THE WORK REPRODUCED RESERVED  ·  UNAUTHORISED COPYING, HIRING, "
    "LENDING, PUBLIC PERFORMANCE AND BROADCASTING OF THIS RECORD PROHIBITED"
)
# Strokes of the hand that scratched the matrix number, on a unit square.
HAND = {
    "2": (((0.05, 0.25), (0.35, 0.02), (0.75, 0.05), (0.95, 0.3), (0.05, 1), (1, 0.98)),),
    "3": (((0.05, 0.1), (0.6, 0), (0.95, 0.22), (0.45, 0.5), (0.95, 0.74), (0.55, 1), (0.05, 0.9)),),
    "X": (((0.05, 0), (0.95, 1)), ((0.95, 0), (0.05, 1))),
    "A": (((0, 1), (0.5, 0), (1, 1)), ((0.22, 0.62), (0.8, 0.62))),
    "1": (((0.25, 0.25), (0.55, 0), (0.55, 1)),),
    "0": (((0.5, 0), (0.9, 0.25), (0.9, 0.75), (0.5, 1), (0.1, 0.75), (0.1, 0.25), (0.5, 0)),),
    "T": (((0, 0), (1, 0)), ((0.5, 0), (0.5, 1))),
    " ": (),
    "-": (((0.15, 0.55), (0.85, 0.55)),),
}


def sleeve(stage):
    sheet = Sheet(S, S, TINT, rough=0.16)
    X, Y = sheet.X, sheet.Y
    # The sleeve is printed with the cover of his playlist, edge to edge. The file holds sRGB values.
    art = fit(pixels_of(COVER)[..., :3].astype(np.float64), *sheet.height.shape)
    sheet.rgb = np.where(art <= 0.04045, art / 12.92, ((art + 0.055) / 1.055) ** 2.4)
    sheet.punch(disc(X, Y, S + 0.3, S / 2, 1.05))
    # The record inside presses its rim through the card.
    reach = np.hypot(X - S / 2, Y - S / 2)
    sheet.height += 0.007 * np.exp(-(((reach - DISC / 2) / 0.1) ** 2))
    sheet.soften(0.07, 0.02)
    wave = drift(S, S, 0.03, 71)

    def bulge(x, y):
        r = np.hypot(x - S / 2, y - S / 2) / (S / 2)
        return 0.22 * np.clip(1 - r * r, 0, None) + wave(x, y)

    sheet.build(
        stage,
        "sleeve",
        thickness=0.14,
        warp=bulge,
        scan="Paper006",
        scan_size=12,
        scan_normal=0.12,
        scan_rough=0.15,
        wear=(("Scratches003", 10, 0.3, 0.001), ("SurfaceImperfections003", 14, 0.18, 0), ("Fingerprints009", 9, 0.12, 0)),
        mottle=0.02,
    )
    stage.shoot("sleeve", (0, 0, S, S), bleed=0.8, shadow=0.7, sharp=SHARP)


def wound(reach, turn, field):
    """A field kept as rows of radius and columns of angle, read at every point of the disc."""
    rows, cols = field.shape
    r = np.clip(reach / (DISC / 2) * rows - 0.5, 0, rows - 1.001)
    a = (turn / (2 * np.pi)) % 1 * cols
    r0, a0 = r.astype(int), a.astype(int) % cols
    a1 = (a0 + 1) % cols
    fr, fa = r - r0, a - np.floor(a)
    near = field[r0, a0] * (1 - fa) + field[r0, a1] * fa
    far = field[r0 + 1, a0] * (1 - fa) + field[r0 + 1, a1] * fa
    return near * (1 - fr) + far * fr


def spiral(reach, turn, start, pitch):
    """Distance to a groove that winds outward clockwise from `start`, one pitch a turn."""
    return np.abs(((reach - start) / pitch - turn / (2 * np.pi) + 0.5) % 1 - 0.5) * pitch


def scratched(X, Y, text, cx, cy, radius, at, height, rng):
    """Distance to a matrix number scratched by hand along an arc, its feet toward the rim."""
    d = np.full(X.shape, 9.0)
    step = height * 0.85 / radius
    for i, letter in enumerate(text):
        a = at - i * step
        ux, uy = np.sin(a), -np.cos(a)
        for line in HAND[letter]:
            points = []
            for px, py in line:
                px, py = px + rng.normal(0, 0.05), py + rng.normal(0, 0.05)
                along, out = (px - 0.5) * height * 0.6, radius + (py - 0.5) * height
                points.append((cx + np.cos(a) * out + ux * along, cy + np.sin(a) * out + uy * along))
            for (ax, ay), (bx, by) in zip(points, points[1:]):
                d = np.minimum(d, segment(X, Y, ax, ay, bx, by))
    return d


def cutting(material, cut):
    """Lay the shine of the groove over a material. cut holds, per point, how far the groove swings off its
    circle in radians, how brightly its walls shine and how much flat land is left between its turns.
    The walls scatter light across the groove and hardly at all along it, which fans the highlights out
    from the centre."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    lacquer = nodes.new("ShaderNodeTexImage")
    lacquer.image = cut
    lacquer.interpolation = "Linear"
    lacquer.extension = "EXTEND"
    split = nodes.new("ShaderNodeSeparateColor")
    links.new(lacquer.outputs["Color"], split.inputs["Color"])

    def vector(op, a, b=None, scale=None):
        node = nodes.new("ShaderNodeVectorMath")
        node.operation = op
        for socket, value in zip(node.inputs, (a, b)):
            if value is None:
                continue
            if isinstance(value, tuple):
                socket.default_value = value
            else:
                links.new(value, socket)
        if scale is not None:
            links.new(scale, node.inputs["Scale"])
        return node.outputs[0]

    coord = nodes.new("ShaderNodeTexCoord")
    centre = vector("MULTIPLY", vector("SUBTRACT", coord.outputs["Object"], (DISC / 2, -DISC / 2, 0)), (1, 1, 0))
    out = vector("NORMALIZE", centre)
    along = vector("CROSS_PRODUCT", (0, 0, 1), out)
    walls = nodes.new("ShaderNodeBsdfAnisotropic")
    walls.distribution = "GGX"
    walls.inputs["Roughness"].default_value = SPREAD
    walls.inputs["Anisotropy"].default_value = NARROW
    links.new(vector("ADD", along, vector("SCALE", out, scale=split.outputs["Red"])), walls.inputs["Tangent"])
    links.new(vector("SCALE", (1, 1, 1), scale=split.outputs["Green"]), walls.inputs["Color"])
    # The stage leans the normals of the material it knows. These walls lean the same way.
    lean = 1 / (2 * LENS_HEIGHT)
    tilted = vector("ADD", shader.inputs["Normal"].links[0].from_socket, vector("MULTIPLY", centre, (lean, lean, 0)))
    links.new(vector("NORMALIZE", tilted), walls.inputs["Normal"])
    links.new(split.outputs["Blue"], shader.inputs["Specular IOR Level"])
    both = nodes.new("ShaderNodeAddShader")
    links.new(shader.outputs[0], both.inputs[0])
    links.new(walls.outputs[0], both.inputs[1])
    links.new(both.outputs[0], nodes["Material Output"].inputs["Surface"])


def vinyl(stage):
    sheet = Sheet(DISC, DISC, "#0b0b0c", rough=0.06, density=3)
    X, Y = sheet.X, sheet.Y
    rows, cols = sheet.height.shape
    c = DISC / 2
    reach, turn = np.hypot(X - c, Y - c), np.arctan2(Y - c, X - c)
    sheet.cut(reach - EDGE)
    sheet.punch(reach - HOLE)
    rng = np.random.default_rng(45)

    # Three songs a side, each as wide as it is long, with a silent turn or two between them.
    room = FIRST - LAST - GAP * (len(SIDE) - 1)
    total = sum(seconds for _, _, seconds in SIDE)
    music = np.zeros((rows, cols))
    quiet = np.zeros((rows, cols))
    outer = FIRST
    for _, _, seconds in SIDE:
        inner = outer - room * seconds / total
        band = sheet.mask(np.abs(reach - (outer + inner) / 2) - (outer - inner) / 2)
        music += band
        # A song starts and ends quieter than its middle.
        quiet += band * (1 - ramp(0, 0.12, outer - reach) * ramp(0, 0.2, reach - inner))
        outer = inner - GAP
    silent = sheet.mask(np.abs(reach - (FIRST + LAST) / 2) - (FIRST - LAST) / 2) * (1 - music)
    lead = sheet.mask(np.abs(reach - (FIRST + BEAD) / 2) - (BEAD - FIRST) / 2 + 0.02)
    tail = sheet.mask(np.abs(reach - (LAST + LOCK) / 2) - (LAST - LOCK) / 2)
    lone = np.maximum.reduce(
        (
            silent * sheet.mask(spiral(reach, turn, LAST, GAP / 2.3) - 0.004),
            lead * sheet.mask(spiral(reach, turn, FIRST, 0.062) - 0.004),
            tail * sheet.mask(spiral(reach, turn, LOCK, 0.27) - 0.004),
            sheet.mask(np.abs(reach - LOCK) - 0.005),
        )
    )

    # How loud the cut is. It changes from turn to turn, which shows as rings, and along a turn, as arcs.
    polar = (1100, 8192)
    rings = sum(gain * streaks((polar[0], 2), 40 + i, 0, sigma)[:, 0] for i, (sigma, gain) in enumerate(((0.8, 0.5), (4, 0.8), (16, 1))))
    arcs = streaks((polar[0], 1024), 46, 40, 1.0) + streaks((polar[0], 1024), 47, 160, 2.5)
    loud = 0.5 + 0.14 * np.interp(reach, np.linspace(0, c, polar[0]), rings) + 0.16 * wound(reach, turn, arcs)
    loud = np.clip(loud, 0, 1)
    loud *= 1 - 0.6 * quiet
    # The swing of the groove itself: fine, and drawn out along the groove.
    swing = rng.standard_normal((rows, cols)) + wound(reach, turn, 0.5 * streaks(polar, 48, 10, 0.5) + 0.3 * streaks(polar, 49, 50, 0.5))
    glint = wound(reach, turn, streaks(polar, 51, 300, 0.45))

    cut = np.dstack(
        (
            music * (0.03 + 0.12 * loud) * swing + lone * 0.02 * swing,
            SHINE * (music * np.clip(0.75 + 0.5 * (loud - 0.5) + 0.22 * glint, 0, None) + lone),
            0.5 * (1 - 0.8 * music - 0.4 * lone),
            np.ones((rows, cols)),
        )
    )

    # The pressing: a bead round the rim, the label's seat and the ring the stamper leaves beside it.
    sheet.height += 0.014 * ramp(BEAD - 0.03, BEAD + 0.05, reach) - 0.022 * ramp(BEAD + 0.03, EDGE + 0.01, reach) ** 2
    sheet.height -= 0.004 * (1 - ramp(LABEL / 2 + 0.03, LABEL / 2 + 0.07, reach))
    sheet.height += 0.003 * np.exp(-(((reach - LABEL / 2 - 0.2) / 0.012) ** 2))
    sheet.height -= 0.02 * (1 - ramp(HOLE, HOLE + 0.04, reach)) ** 2
    sheet.height -= 0.0015 * lone

    # The matrix number in the dead wax.
    etched = sheet.mask(scratched(X, Y, MATRIX, c, c, 3.02, np.radians(124), 0.19, rng) - 0.004)
    sheet.height -= 0.002 * etched
    sheet.rough += 0.5 * etched
    sheet.rgb += etched[..., None] * 0.02

    # Dust, a few fibres and the hairlines a paper sleeve leaves.
    dust = np.zeros((rows, cols))
    for _ in range(90):
        r, a = c * np.sqrt(rng.uniform(0.01, 1)), rng.uniform(0, 2 * np.pi)
        x, y, size = c + r * np.cos(a), c + r * np.sin(a), rng.choice((0.004, 0.005, 0.007, 0.01))
        area = sheet.window(x - 3 * size, y - 3 * size, x + 3 * size, y + 3 * size)
        speck = rng.uniform(0.15, 0.8) * np.exp(-((X[area] - x) ** 2 + (Y[area] - y) ** 2) / (2 * size * size))
        dust[area] = np.maximum(dust[area], speck)
    for _ in range(7):
        r, a = c * np.sqrt(rng.uniform(0.05, 1)), rng.uniform(0, 2 * np.pi)
        x, y, heading = c + r * np.cos(a), c + r * np.sin(a), rng.uniform(0, 2 * np.pi)
        for _ in range(rng.integers(4, 9)):
            heading += rng.normal(0, 0.5)
            nx, ny = x + 0.035 * np.cos(heading), y + 0.035 * np.sin(heading)
            area = sheet.window(min(x, nx) - 0.03, min(y, ny) - 0.03, max(x, nx) + 0.03, max(y, ny) + 0.03)
            dust[area] = np.maximum(dust[area], 0.7 * sheet.mask(segment(X[area], Y[area], x, y, nx, ny, 0.003)))
            x, y = nx, ny
    scuff = np.zeros((rows, cols))
    for _ in range(16):
        r, a, heading = c * np.sqrt(rng.uniform(0.1, 1)), rng.uniform(0, 2 * np.pi), rng.uniform(0, np.pi)
        x, y, half = c + r * np.cos(a), c + r * np.sin(a), rng.uniform(0.3, 1.6)
        dx, dy = half * np.cos(heading), half * np.sin(heading)
        area = sheet.window(x - abs(dx) - 0.03, y - abs(dy) - 0.03, x + abs(dx) + 0.03, y + abs(dy) + 0.03)
        along = segment(X[area], Y[area], x - dx, y - dy, x + dx, y + dy, 0.0015)
        scuff[area] = np.maximum(scuff[area], rng.uniform(0.15, 0.5) * sheet.mask(along))
    # Where fingers took hold of it. Each is one print of the scan: its place on the disc, its place in the scan.
    prints = pixels_of(os.path.join(ASSETS, "Fingerprints009", "Fingerprints009_1K-JPG_Opacity.jpg"))[..., 0]
    grease = np.zeros((rows, cols))
    for x, y, u, v in ((12.5, 10.3, 0.142, 0.098), (11.2, 3.5, 0.376, 0.625), (3.4, 5.2, 0.49, 0.43)):
        tile = prints[(((Y - y) / 9 + v) % 1 * prints.shape[0]).astype(int), (((X - x) / 9 + u) % 1 * prints.shape[1]).astype(int)]
        grease += tile * np.exp(-(((X - x) ** 2 + (Y - y) ** 2) / 0.8) ** 2)
    sheet.rgb += dust[..., None] * (0.45 - sheet.rgb) + scuff[..., None] * 0.03 + grease[..., None] * 0.04
    sheet.rough += dust * 0.8 + scuff * 0.3 + grease * 0.3
    cut[..., 1] *= 1 - 0.6 * np.clip(grease * 1.3, 0, 1)
    cut[..., 1:3] *= ((1 - dust) * (1 - 0.5 * scuff))[..., None]

    record = sheet.build(
        stage,
        "vinyl",
        thickness=0.1,
        wear=(("Scratches003", 9, 0.1, 0.0002), ("SurfaceImperfections003", 12, 0.04, 0)),
    )
    image = bpy.data.images.new("vinyl-cut", cols, rows, alpha=True, float_buffer=True)
    image.colorspace_settings.name = "Non-Color"
    image.pixels.foreach_set(cut[::-1].astype(np.float32).ravel())
    image.pack()
    cutting(record.data.materials[0], image)
    stage.shoot("disc", (0, 0, DISC, DISC), exposure=0.6, sharp=SHARP)


def lettering(stage, text, face, cap, x, y, ink, arc=0.0):
    """A line of type as a mesh, centred on x with its baseline at y, capitals `cap` em tall.
    ink is the plate's colour channel. arc bends the baseline round the label's centre at that radius,
    so the line reads along the bottom of the label with its feet outward."""
    curve = bpy.data.curves.new("type", "FONT")
    curve.font = face
    curve.body = text
    curve.size = cap / 0.546
    curve.align_x = "CENTER"
    line = stage.add("type", curve)
    bpy.context.view_layer.update()
    mesh = bpy.data.meshes.new_from_object(line)
    bpy.data.objects.remove(line)
    points = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", points)
    points = points.reshape(-1, 3)
    if arc:
        turn, reach = -np.pi / 2 + points[:, 0] / arc, arc - points[:, 1]
        points[:, 0], points[:, 1] = LABEL / 2 + reach * np.cos(turn), -LABEL / 2 + reach * np.sin(turn)
    else:
        points[:, 0] += x
        points[:, 1] -= y
    mesh.vertices.foreach_set("co", points.ravel())
    paint = bpy.data.materials.new("ink")
    paint.use_nodes = True
    nodes, links = paint.node_tree.nodes, paint.node_tree.links
    nodes.clear()
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (ink == 0, ink == 1, ink == 2, 1)
    links.new(emit.outputs[0], nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    mesh.materials.append(paint)
    return stage.add("type", mesh)


def plate(stage, sheet, lines):
    """Photograph the lines of type from overhead at the sheet's own size. Returns one mask per ink."""
    scene = bpy.context.scene
    rows, cols = sheet.height.shape
    optics = bpy.data.cameras.new("plate")
    optics.type = "ORTHO"
    optics.ortho_scale = max(sheet.w, sheet.h)
    camera = stage.add("plate", optics)
    camera.location = (sheet.w / 2, -sheet.h / 2, 10)
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = cols, rows
    scene.cycles.use_denoising = False
    inks = stage._expose(os.path.join(tempfile.gettempdir(), "studio-plate.exr"), samples=24)
    scene.cycles.use_denoising = True
    for obj in (*lines, camera):
        bpy.data.objects.remove(obj)
    return [np.clip(inks[..., i].astype(np.float64), 0, 1) for i in range(3)]


def label(stage):
    sheet = Sheet(LABEL, LABEL, PAPER, rough=0.5, density=4)
    X, Y = sheet.X, sheet.Y
    rows, cols = sheet.height.shape
    c = LABEL / 2
    reach = np.hypot(X - c, Y - c)
    sheet.cut(reach - c)
    sheet.punch(reach - HOLE - 0.012)
    rng = np.random.default_rng(33)

    sans, serif, mono = (bpy.data.fonts.load(os.path.join(FONTS, f"{name}-vf.woff2")) for name in ("timeless-sans", "timeless-serif-italic", "paper-mono"))
    # Laid out as a compilation's label is: the title, who compiled it, the speed and the side beside the
    # hole, the songs with who sings them, and the rights notice round the rim.
    lines = [
        lettering(stage, "Two x 3.", serif, 0.47, c, 1.36, 1),
        lettering(stage, "VARIOUS  ARTISTS", sans, 0.115, c, 1.98, 0),
        lettering(stage, "A playlist compiled by Anurag Das", sans, 0.09, c, 2.2, 0),
        lettering(stage, "STEREO", sans, 0.125, 1.25, 2.7, 0),
        lettering(stage, "33⅓ RPM", sans, 0.125, 1.25, 2.95, 0),
        lettering(stage, "SIDE 1", sans, 0.125, 4.25, 2.7, 0),
        lettering(stage, MATRIX[:-1], mono, 0.1, 4.25, 2.95, 0),
        lettering(stage, RIGHTS, sans, 0.07, 0, 0, 0, arc=2.56),
    ]
    for i, (title, artist, seconds) in enumerate(SIDE):
        y = 3.56 + 0.4 * i
        lines.append(lettering(stage, f"{i + 1}. {title.upper()}  {seconds // 60}:{seconds % 60:02d}", sans, 0.115, c, y, 0))
        lines.append(lettering(stage, f"({artist})", sans, 0.09, c, y + 0.16, 0))
    black, white, _ = plate(stage, sheet, lines)

    # One flat colour over white paper, the ink a little uneven, then black over it. The title is left as paper.
    oval = np.hypot((X - c) / 1.62, (Y - 1.17) / 0.5)
    steep = np.hypot((X - c) / 1.62**2, (Y - 1.17) / 0.5**2) / np.maximum(oval, 1e-6)
    white = np.maximum(white, sheet.mask(np.abs((oval - 1) / steep) - 0.008))
    flood = np.clip(1 - 0.03 * np.abs(cloud((rows, cols), 34, 1.2)), 0, 1) * (1 - np.clip(blur(white, 0.6) * 1.5, 0, 1))
    sheet.ink(flood, TINT)
    sheet.ink(np.clip(blur(black, 0.7) * 1.7, 0, 1) * (0.94 + 0.03 * cloud((rows, cols), 35, 0.8)), INK)
    sheet.finish(flood, rough=0.42)

    # The stamper's ring round the hole, and where a spindle has missed the hole and rubbed the ink off.
    sheet.height -= 0.006 * np.exp(-(((reach - 0.98) / 0.02) ** 2)) + 0.002 * np.exp(-(((reach - 0.45) / 0.03) ** 2))
    for _ in range(6):
        a, heading = rng.uniform(0, 2 * np.pi), rng.uniform(0, 2 * np.pi)
        x, y, run = c + (HOLE + 0.02) * np.cos(a), c + (HOLE + 0.02) * np.sin(a), rng.uniform(0.12, 0.4)
        rub = sheet.mask(segment(X, Y, x, y, x + run * np.cos(heading), y + run * np.sin(heading), rng.uniform(0.002, 0.007)))
        sheet.paint(rub * rng.uniform(0.2, 0.55) * ramp(0, 0.1, reach - HOLE), PAPER)
    sheet.soften(0.03, 0.006)
    sheet.build(stage, "label", thickness=0.08, scan="Paper001", scan_size=5, scan_normal=0.5, scan_colour=0.22, sheen=0.3, specular=0.3)
    stage.shoot("label", (0, 0, LABEL, LABEL), lens=False, sharp=SHARP)


SHOTS = {"sleeve": sleeve, "disc": vinyl, "label": label}
