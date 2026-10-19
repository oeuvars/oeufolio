"""The watch: a Seiko 7A28 quartz chronograph, as in the user's photographs of it (art/chrono-photo.jpg, face on,
and art/chrono-hand-photo.jpg, in the hand), lying face up on the desk with its bracelet shut under it.

A steel case, satin all over: round, about 38.6 mm across, drawn out at 12 and at 6 into broad flat shoulders as wide
as the bracelet, its edge rounded over all round. A slim raised bezel round a flat crystal, a polished step inside
it. Two pushers on the right, at 2 and at 4, and one on the left at 10, each a guard collar and a hexagonal head;
the crown at 8, knurled. Under the crystal, sunk below the bezel, the dial is the photograph itself, laid out square
on with the photograph's light taken out of it (art/chrono-dial.png, by art/chronophoto.py): its tachymeter scale,
its three subdials and SEIKO are the real ones. Its hands stand over it where the photograph has them: black hour
and minute hands striped with lume, the thin dark red seconds hand with its counterweight and pip, the small dials'
black hands on their hubs, and a polished cap over the middle; each throws its shadow on the dial.

The bracelet runs on out of the shoulders, as wide as them, narrowing to the clasp: broad flat links, their top
edges chamfered bright, each between two narrow round bars, a fine dark gap between every one. Taken off and put
down with its clasp shut, as in the user's pictures of watches lying so, it stands in a loop under the case and holds
it up: out of each end of the case it runs straight on, bends round and down to the desk, and runs back along it
under the case, the folding clasp, a long plain plate, lying face down there.

Built in millimetres, 12 o'clock up the page, the middle of the dial over the origin, and drawn MM em to the
millimetre, as the Alpinist (objects/watch.py) was, in the same box on the desk."""

import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

from objects.flutelamp import turned
from objects.watch import MM, H, W, polygon_prism, room, steel, sweep
from solids import worn
from stage import ASSETS

ART = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "art")
DIAL_ART = os.path.join(ART, "chrono-dial.png")
DIAL_ART_SIZE = 36.0

# Measured off the face-on photograph at 13.4 of its pixels to the mm. The case: round, this far out, its shoulders
# this wide either side of the middle and reaching this far up and down it, its corners rounded this much; its back
# this round and this thick, its body up to this height, its edge rounded over this much, and its shoulders falling
# this much toward their ends, from this far out.
CASE_R = 19.3
SHOULDER = (12.0, 21.0, 1.0)
BACK = (16.0, 0.9)
TOP = 7.4
ROUNDED = 1.4
FALL = (0.5, 16.0)
# The dial, out to the black ring round its scale, and the crystal over it, flat, this thick, its top this high; the
# crystal and the bezel round it stand this much higher than the dial, which sits down in the case under them, its
# edge in the shadow of the wall round it.
DIAL_R = 17.3
RISE = 1.0
CRYSTAL = (0.35, 8.3 + RISE)
# The bezel's sections, radius and height in mm, each a closed ring: a polished step up from the dial's edge, then
# the satin bezel, up over its crest and down into the case's top.
STEP = [(17.15, TOP), (17.15, 8.05 + RISE), (17.3, 8.12 + RISE), (17.7, 8.15 + RISE), (17.75, 8.0 + RISE), (17.75, TOP), (17.15, TOP)]
BEZEL = [(17.65, 7.9 + RISE), (17.7, 8.15 + RISE), (17.85, 8.32 + RISE), (18.05, 8.4 + RISE), (18.3, 8.36 + RISE), (18.5, 8.15 + RISE), (18.65, 7.7 + RISE), (18.75, TOP - 0.5), (17.65, TOP - 0.5), (17.65, 7.9 + RISE)]
# The hands, stood over the dial where the photograph has them (art/chrono-hands.json, by art/chronophoto.py): each
# this high over the dial and this thick, the small dials' first, then the hour, minute and seconds hands, the cap
# over them all. The hour and minute hands are black, a white strip of lume down them this wide, from this far out
# to this far, its point this much further; their bosses round the pivot this round. The seconds hand is the dark red
# of the photograph. The hands' paint: black this rough, the lume this white and this rough, the red this.
HANDS_ART = os.path.join(ART, "chrono-hands.json")
HEIGHTS = {"small": (0.15, 0.1), "hour": (0.35, 0.1), "minute": (0.55, 0.1), "chrono": (0.75, 0.08), "cap": (0.3, 0.65)}
LUME = {"hour": (0.32, 2.6, 6.9, 0.4), "minute": (0.32, 3.0, 10.2, 0.4)}
BOSS = {"hour": 0.65, "minute": 0.7}
BLACK = ((0.012, 0.012, 0.012), 0.25)
WHITE_LUME = ((0.8, 0.8, 0.76), 0.55)
RED = (0.045, 0.007, 0.006)
# The pushers and the crown, round the flank: at this angle from 3 o'clock, anticlockwise; at this height. Each pusher
# a guard collar this round and this long, a stem, and a hexagonal head this round and this long, standing out this
# far in all. The crown, this round, this long, its knurl this many teeth.
PUSHERS = (32.6, 147.4)
CROWN_AT = 210.0
FLANK_Z = 4.3
COLLAR = (1.7, 2.3)
HEAD = (1.5, 1.4)
REACH = 3.7
CROWN = (2.05, 3.6)
TEETH = 30
# The bracelet, from the case's ends: broad links this long, narrow round bars this long, a gap this wide between
# each; the broad links this thick, their top edges chamfered this much, the bars this thick, standing this far off
# the broad links' inside. This wide at the case, narrowing to this wide this far along. The half at 12 has this many
# broad links, the half at 6 this many and then the clasp, this long and this thick. Shut, the bracelet stands under
# the case, bent round this radius at either end, holding the case this high off the desk; each pin's play lets a
# link sit tipped up to this many degrees across. Under the gaps, the links' hinges: a core this
# much narrower than the links, this thick, this far from the broad links' inside.
LINK = (4.9, 1.5, 0.3)
BROAD = (3.4, 0.4)
BAR = (2.8, 0.35)
TAPER = (23.6, 18.0, 45.0)
COUNT = (9, 8)
CLASP = (26.0, 3.7)
BEND = 7.5
RAISE = 2 * BEND
TIP = 0.6
HINGE = (1.2, 1.8, 0.4)
# Brushed steel, as stainless steel is: it throws back this much of the light (the measured reflectance of steel,
# whatever its finish), its finish the scan of brushed metal (assets' BRUSHED), repeating every this many mm, its grain
# running across the bracelet; this rough about the scan's own unevenness, this much rougher along the grain than across
# it, and its grain this deep. Handled: hairline scratches, finger marks and dull patches, each repeating every this
# many mm and dulling it this much. Polished, as the pushers, crown and step are: this rough.
STEEL_F0 = (0.56, 0.57, 0.58)
BRUSHED = ("Metal009", 24.0)
GRAIN = (0.3, 0.1, 0.6, 0.004)
HANDLED = (("Scratches003", 22.0, 0.08), ("Fingerprints009", 18.0, 0.12), ("SurfaceImperfections003", 30.0, 0.06))
POLISHED = 0.08
# The crystal: mineral glass, uncoated, this index.
GLASS_IOR = 1.52


def satin(name, rough=None):
    """Brushed stainless steel: the scan of brushed metal laid on from all six sides in the part's own millimetres,
    its grain across the bracelet (the part's x), its highlights drawn out along the grain as a brushed surface draws
    them; handled."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*STEEL_F0, 1)
    shader.inputs["Metallic"].default_value = 1.0
    base, spread, stretch, depth = GRAIN
    base = base if rough is None else rough
    asset, size = BRUSHED
    coord = nodes.new("ShaderNodeTexCoord")
    place = nodes.new("ShaderNodeMapping")
    place.inputs["Scale"].default_value = (1 / size, 1 / size, 1 / size)
    links.new(coord.outputs["Object"], place.inputs["Vector"])

    def scan(kind):
        node = nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(os.path.join(ASSETS, asset, f"{asset}_1K-JPG_{kind}.jpg"), check_existing=True)
        node.image.colorspace_settings.name = "Non-Color"
        node.projection = "BOX"
        node.projection_blend = 0.2
        links.new(place.outputs["Vector"], node.inputs["Vector"])
        return node

    shine = nodes.new("ShaderNodeMapRange")
    shine.inputs["To Min"].default_value = base - spread
    shine.inputs["To Max"].default_value = base + spread
    links.new(scan("Roughness").outputs["Color"], shine.inputs["Value"])
    links.new(shine.outputs[0], shader.inputs["Roughness"])
    grain = nodes.new("ShaderNodeBump")
    grain.inputs["Strength"].default_value = 1.0
    grain.inputs["Distance"].default_value = depth
    links.new(scan("Displacement").outputs["Color"], grain.inputs["Height"])
    links.new(grain.outputs["Normal"], shader.inputs["Normal"])
    # The grain runs along the part's x, wherever the part is turned to.
    along = nodes.new("ShaderNodeVectorTransform")
    along.vector_type = "VECTOR"
    along.convert_from = "OBJECT"
    along.convert_to = "WORLD"
    along.inputs["Vector"].default_value = (1.0, 0.0, 0.0)
    links.new(along.outputs["Vector"], shader.inputs["Tangent"])
    shader.inputs["Anisotropic"].default_value = stretch
    for mark, every, dull in HANDLED:
        worn(material, mark, every, dull)
    return material


def mineral(name):
    """The crystal: mineral glass, uncoated, so it throws back the room as plain glass does; finger marked. Glass
    lets a shadow ray through in a render only if told: the dial under it is lit by the lamp."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (1, 1, 1, 1)
    shader.inputs["Transmission Weight"].default_value = 1.0
    shader.inputs["Roughness"].default_value = 0.0
    shader.inputs["IOR"].default_value = GLASS_IOR
    worn(material, "Fingerprints009", 14.0, 0.05)
    path = nodes.new("ShaderNodeLightPath")
    through = nodes.new("ShaderNodeBsdfTransparent")
    either = nodes.new("ShaderNodeMixShader")
    links.new(path.outputs["Is Shadow Ray"], either.inputs[0])
    links.new(shader.outputs[0], either.inputs[1])
    links.new(through.outputs[0], either.inputs[2])
    links.new(either.outputs[0], nodes["Material Output"].inputs["Surface"])
    return material


def printed(name):
    """The dial as photographed (DIAL_ART), laid on from straight over it, a satin finish."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Roughness"].default_value = 0.45
    coord = nodes.new("ShaderNodeTexCoord")
    place = nodes.new("ShaderNodeMapping")
    place.inputs["Scale"].default_value = (1 / DIAL_ART_SIZE, 1 / DIAL_ART_SIZE, 1)
    place.inputs["Location"].default_value = (0.5, 0.5, 0)
    links.new(coord.outputs["Object"], place.inputs["Vector"])
    art = nodes.new("ShaderNodeTexImage")
    art.image = bpy.data.images.load(DIAL_ART)
    art.interpolation = "Cubic"
    links.new(place.outputs["Vector"], art.inputs["Vector"])
    links.new(art.outputs["Color"], shader.inputs["Base Color"])
    return material


def hull(points):
    """The convex outline round points, counter-clockwise (Andrew's monotone chain)."""
    points = sorted(set(points))

    def turn(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in points:
        while len(lower) >= 2 and turn(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper) >= 2 and turn(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def outline():
    """The case seen from above: the round of it and the shoulders' rounded corners, drawn round together; points
    spread evenly along it."""
    wide, reach, corner = SHOULDER
    points = [(round(CASE_R * math.cos(a), 6), round(CASE_R * math.sin(a), 6)) for a in np.linspace(0, 2 * math.pi, 360, endpoint=False)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (wide - corner), sy * (reach - corner)
            points += [(round(cx + corner * math.cos(a), 6), round(cy + corner * math.sin(a), 6)) for a in np.linspace(0, 2 * math.pi, 48, endpoint=False)]
    loop = np.array(hull(points) + hull(points)[:1])
    run = np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(loop, axis=0), axis=1))))
    along = np.arange(0.0, run[-1], 0.25)
    return list(zip(np.interp(along, run, loop[:, 0]), np.interp(along, run, loop[:, 1])))


def case(stage, matte, polish):
    made = []
    radius, back = BACK
    shell = turned("chrono-back", [(0.0, 0.0), (radius - 0.6, 0.0), (radius, 0.4), (radius, back + 0.1), (0.0, back + 0.1)], around=256)
    shell.set_sharp_from_angle(angle=math.radians(30))
    shell.materials.append(matte)
    made.append(stage.add("chrono-back", shell))
    # The body, its outline stood up, its top edge rounded over; its shoulders falling toward their ends.
    body = polygon_prism("chrono-body", outline(), back, TOP, matte, bevel=ROUNDED)
    co = np.empty(len(body.vertices) * 3)
    body.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    drop, start = FALL
    falls = drop * np.clip((np.abs(co[:, 1]) - start) / (SHOULDER[1] - start), 0, 1) ** 1.5
    co[:, 2] -= falls * np.clip((co[:, 2] - back) / (TOP - back), 0, 1)
    body.vertices.foreach_set("co", co.ravel())
    body.polygons.foreach_set("use_smooth", [True] * len(body.polygons))
    body.set_sharp_from_angle(angle=math.radians(40))
    made.append(stage.add("chrono-body", body))
    for name, profile, material in (("chrono-step", STEP, polish), ("chrono-bezel", BEZEL, satin("chrono-bezel-steel", 0.22))):
        mesh = turned(name, profile, around=360)
        mesh.set_sharp_from_angle(angle=math.radians(30))
        mesh.materials.append(material)
        made.append(stage.add(name, mesh))
    # The pushers: a guard collar out of the flank, a stem, a hexagonal head.
    for angle in PUSHERS:
        round_, length = COLLAR
        parts = [
            turned(f"chrono-collar-{angle}", [(0.0, -1.5), (round_, -1.5), (round_, length - 0.15), (round_ - 0.15, length), (0.0, length)], around=64),
            turned(f"chrono-stem-{angle}", [(0.0, length - 0.1), (0.75, length - 0.1), (0.75, REACH - HEAD[1] + 0.1), (0.0, REACH - HEAD[1] + 0.1)], around=48),
            polygon_prism(f"chrono-head-{angle}", [(HEAD[0] * math.cos(a), HEAD[0] * math.sin(a)) for a in np.radians(np.arange(0, 360, 60) + 30)], REACH - HEAD[1], REACH, polish, bevel=0.2),
        ]
        made += placed(stage, parts, polish, angle)
    # The crown, knurled, on a short neck.
    radius, reach = CROWN
    teeth = []
    for k in range(TEETH * 4):
        a = 2 * math.pi * k / (TEETH * 4)
        r = radius - (0.16 if (k // 2) % 2 else 0.0)
        teeth.append((r * math.cos(a), r * math.sin(a)))
    parts = [
        polygon_prism("chrono-crown", teeth, 0.6, reach, polish, bevel=0.3),
        turned("chrono-crown-neck", [(0.0, -1.5), (1.2, -1.5), (1.2, 0.7), (0.0, 0.7)], around=48),
    ]
    made += placed(stage, parts, polish, CROWN_AT)
    return made


def placed(stage, meshes, material, angle):
    """Parts turned on their own axis, laid along the radius out of the flank at angle."""
    made = []
    a = math.radians(angle)
    for mesh in meshes:
        if not mesh.materials:
            mesh.materials.append(material)
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        mesh.set_sharp_from_angle(angle=math.radians(40))
        obj = stage.add(mesh.name, mesh)
        obj.matrix_world = Matrix.Translation(((CASE_R - 0.4) * math.cos(a), (CASE_R - 0.4) * math.sin(a), FLANK_Z)) @ Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y")
        made.append(obj)
    return made


def dial(stage, paper):
    disc = turned("chrono-dial", [(0.0, TOP + 0.1), (DIAL_R, TOP + 0.1), (DIAL_R, TOP - 0.2), (0.0, TOP - 0.2)], around=256)
    disc.materials.append(paper)
    thick, top = CRYSTAL
    glass = turned("chrono-crystal", [(0.0, top), (17.2, top), (17.25, top - 0.05), (17.25, top - thick), (0.0, top - thick)], around=256)
    # The crystal stands RISE over the dial: its rim sits on the step's wall.
    glass.materials.append(mineral("chrono-glass"))
    # Flat faces shaded flat, not bent toward their rims.
    for mesh in (disc, glass):
        mesh.set_sharp_from_angle(angle=math.radians(30))
    return [stage.add("chrono-dial", disc), stage.add("chrono-crystal", glass)]


def painted(name, colour, rough):
    """Paint on a hand: lacquer, glossy as such paint is."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*colour, 1)
    shader.inputs["Roughness"].default_value = rough
    return material


def tapered(back, forward, wide, narrow, point=0.0):
    """A hand's outline, pointing up its y from its pivot: from back behind the pivot to forward, narrowing from wide
    to narrow, then drawn to a point over point more."""
    outline = [(-wide / 2, -back), (wide / 2, -back), (narrow / 2, forward)]
    if point:
        outline.append((0.0, forward + point))
    outline.append((-narrow / 2, forward))
    return outline


def hands(stage, polish):
    """The hands over the dial, where the photograph has them, each throwing its shadow on the dial."""
    with open(HANDS_ART) as file:
        spec = json.load(file)
    black = painted("chrono-hand-black", *BLACK)
    lume = painted("chrono-hand-lume", *WHITE_LUME)
    red = painted("chrono-hand-red", RED, BLACK[1])
    dial = TOP + 0.1
    made = []

    def put(name, outline, height, thick, material, at, angle, bevel=0.03):
        mesh = polygon_prism(name, outline, dial + height, dial + height + thick, material, bevel=bevel)
        mesh.polygons.foreach_set("use_smooth", [False] * len(mesh.polygons))
        obj = stage.add(name, mesh)
        obj.matrix_world = Matrix.Translation((at[0], at[1], 0.0)) @ Matrix.Rotation(-math.radians(angle), 4, "Z")
        made.append(obj)

    def disc(radius, n=40):
        return [(radius * math.cos(a), radius * math.sin(a)) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]

    pivot = spec["pivot"]
    small = spec["small"]
    height, thick = HEIGHTS["small"]
    for k, (x, y, angle) in enumerate(small["at"]):
        put(f"chrono-small-{k}", tapered(0.8, small["length"], small["width"], small["width"] * 0.55, 0.1), height, thick, black, (x, y), angle)
        put(f"chrono-small-hub-{k}", disc(small["hub"]), 0.0, height + thick, black, (x, y), 0.0)
        put(f"chrono-small-pin-{k}", disc(0.18, 24), 0.0, height + thick + 0.08, polish, (x, y), 0.0)
    for name in ("hour", "minute"):
        hand = spec[name]
        height, thick = HEIGHTS[name]
        wide, narrow = hand["width"]
        put(f"chrono-{name}", tapered(0.0, hand["length"] - narrow, wide, narrow, narrow), height, thick, black, pivot, hand["angle"])
        put(f"chrono-{name}-boss", disc(BOSS[name]), height, thick, black, pivot, 0.0)
        width, start, end, point = LUME[name]
        strip = [(x, y + start) for x, y in tapered(0.0, end - start, width, width, point)]
        put(f"chrono-{name}-lume", strip, height + thick, 0.03, lume, pivot, hand["angle"], bevel=0.01)
    chrono = spec["chrono"]
    height, thick = HEIGHTS["chrono"]
    put("chrono-seconds", tapered(0.0, chrono["length"], chrono["width"], chrono["width"] * 0.4), height, thick, red, pivot, chrono["angle"], bevel=0.02)
    weight = chrono["counterweight"]
    put("chrono-counterweight", tapered(chrono["tail"], 0.3, weight * 0.7, weight), height, thick, red, pivot, chrono["angle"])
    out, long, wide = chrono["pip"]
    put("chrono-pip", [(0.0, out - long / 2), (wide / 2, out), (0.0, out + long / 2), (-wide / 2, out)], height, thick, red, pivot, chrono["angle"], bevel=0.02)
    put("chrono-pip-lume", [(0.0, out - long / 4), (wide / 4, out), (0.0, out + long / 4), (-wide / 4, out)], height + thick, 0.02, lume, pivot, chrono["angle"], bevel=0.005)
    # The cap over the pivot, polished, domed a little.
    height, thick = HEIGHTS["cap"]
    cap = turned("chrono-cap", [(0.0, dial + height + thick), (spec["cap"] * 0.7, dial + height + thick - 0.05), (spec["cap"], dial + height + thick - 0.25), (spec["cap"], dial + height), (0.0, dial + height)], around=64)
    cap.materials.append(polish)
    obj = stage.add("chrono-cap", cap)
    obj.location = (pivot[0], pivot[1], 0.0)
    made.append(obj)
    return made


def piece(bm, middle, ahead, up, wide, long, thick, crown, edge, tip=0.0):
    """A link: a bar straight across the bracelet, its middle at middle, lying along ahead with its outside toward up,
    wide across and long along it, thick, its section crowned and its edges rounded; tipped this many degrees across
    the bracelet, as it sits on its pins."""
    side = np.cross(ahead, up)
    centres = middle + np.outer(np.linspace(-wide / 2, wide / 2, 2), side)
    count = 2
    frame = (centres, np.repeat(side[None], count, 0), np.repeat(-ahead[None], count, 0), np.repeat(up[None], count, 0))
    mesh, *_ = sweep("chrono-link", frame, np.full(count, long / 2), np.full(count, thick), crown, edge)
    if tip:
        at = Matrix.Translation(Vector(middle))
        mesh.transform(at @ Matrix.Rotation(math.radians(tip), 4, Vector(ahead)) @ at.inverted())
    bm.from_mesh(mesh)
    bpy.data.meshes.remove(mesh)


def pieces():
    """The bracelet's pieces in order from the case's end at 12 round to its end at 6: the half at 12, the clasp, and
    the half at 6 from its far end back; each its length, thickness, how far its middle stands out from the
    bracelet's, its crown and its rounding, and how far it is from its own end of the case."""
    broad, bar, gap = LINK
    high, chamfer = BROAD
    bar_high, bar_lift = BAR
    pair = [(broad, high, 0.0, 0.08, chamfer), (bar, bar_high, bar_lift + bar_high / 2 - high / 2, 0.0, bar_high / 2 * 0.98)]
    twelve, six = (pair * count for count in COUNT)
    made, run = [], 0.0
    for long, *rest in twelve:
        made.append((long, *rest, run))
        run += long + gap
    clasp = (CLASP[0], CLASP[1], (high - CLASP[1]) / 2, 0.08, 0.6)
    six = list(six)
    back = sum(long + gap for long, *_ in six)
    made.append((*clasp, back + CLASP[0] / 2))
    for long, *rest in reversed(six):
        back -= long + gap
        made.append((long, *rest, back))
    return made


def loop(length, radius):
    """The bracelet's middle line, shut and stood under the case, as a fine line of (y, z) points: straight out of the
    case's end at 12, round a bend this round down to the desk, back along it under the case, and round the same bend
    at 6 up into the case's other end; as long as length, the bends as far out as that needs."""
    high = BROAD[0] / 2
    top = high + 2 * radius
    start = SHOULDER[1] + LINK[2]

    def side(out):
        angles = np.linspace(math.pi / 2, -math.pi / 2, 160)
        bend = np.column_stack((out + radius * np.cos(angles), high + radius + radius * np.sin(angles)))
        return np.vstack(([[start, top]], bend, [[0.0, high]]))

    def total(out):
        return 2 * np.linalg.norm(np.diff(side(out), axis=0), axis=1).sum()

    lo, hi = start, start + length
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if total(mid) < length else (lo, mid)
    half = side(lo)
    line = np.vstack((half, (half * [-1, 1])[::-1][1:]))
    run = np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(line, axis=0), axis=1))))
    return line, run


def bracelet(stage, matte):
    """The bracelet, shut: broad links and narrow round bars, narrowing away from the case, round the loop from its
    end at 12 to its end at 6, each piece lying on the chord of the line between its ends; under each gap a hinge."""
    gap = LINK[2]
    near, far, over = TAPER
    narrower, core, core_lift = HINGE
    order = pieces()
    length = sum(long + gap for long, *_ in order) - gap
    line, run = loop(length, BEND)
    rng = np.random.default_rng(23)
    bm = bmesh.new()
    s = 0.0

    def at(t):
        y, z = (np.interp(t, run, line[:, k]) for k in range(2))
        return np.array([0.0, y, z])

    for long, thick, out, crown, edge, home in order:
        a, b = at(s), at(s + long)
        ahead = (b - a) / np.linalg.norm(b - a)
        up = np.cross((1.0, 0.0, 0.0), ahead)
        middle = (a + b) / 2
        wide = near + (far - near) * min(home / over, 1.0)
        piece(bm, middle + up * out, ahead, up, wide, long, thick, crown, edge, rng.uniform(-1, 1) * TIP)
        # The hinge under it and the gap after it, dark in the gap's shadow.
        c = at(min(s + long + gap, length))
        span = c - a
        piece(bm, (a + c) / 2 + up * (core_lift + core / 2 - BROAD[0] / 2), span / np.linalg.norm(span), up, wide - narrower, np.linalg.norm(span) + gap, core, 0.0, 0.3)
        s += long + gap
    mesh = bpy.data.meshes.new("chrono-bracelet")
    bm.to_mesh(mesh)
    bm.free()
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.set_sharp_from_angle(angle=math.radians(50))
    mesh.materials.append(matte)
    return stage.add(mesh.name, mesh)


def parts(stage):
    matte = satin("chrono-steel")
    polish = steel("chrono-polish", POLISHED)
    made = case(stage, matte, polish) + dial(stage, printed("chrono-paper")) + hands(stage, polish)
    # Shut, the bracelet holds the case up off the desk.
    for part in made:
        part.location.z += RAISE
    made.append(bracelet(stage, matte))
    return made + room(stage)


def build(stage):
    made = parts(stage)
    # Parts placed by their rotation and location have their matrices only once the scene is updated.
    bpy.context.view_layer.update()
    for part in made:
        part.matrix_world = Matrix.Translation((W / 2, -H / 2, 0)) @ Matrix.Scale(MM, 4) @ part.matrix_world
    stage.shoot("chrono", (0, 0, W, H), lens=False)


SHOTS = {"chrono": build}
