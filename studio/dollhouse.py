"""The work page's building: a dollhouse cut open at the front, three floors under a mansard roof.

    top      a parcel room: shelves of cake boxes tied with ribbon, a counter with a scale, and the lift
    middle   a banking hall: columns, tellers' grilles and a chequered floor, with the vault next door
    bottom   a dispatch room: trunks stacked and strapped, a trolley, and the stairs

Each floor is one long room and one narrow one, and they change sides from floor to floor. Over each floor
a painted board runs across the front, as over a shop, and is left blank: the page letters the company's
name on it. Run from the repository root:

    blender -b --factory-startup -P studio/dollhouse.py -- [--scale 0.5] [--samples 128]

Writes public/objects/dollhouse.webp, lit from the front and cut out from its background. The page
(src/components/Dollhouse.tsx) places its lettering by the measures below, so keep the two in step.
"""

import math
import os
import sys

import bmesh
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARGS = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


def option(name, default):
    return float(ARGS[ARGS.index(name) + 1]) if name in ARGS else default


SCALE = option("--scale", 1)
SAMPLES = int(option("--samples", 128))

# The building, in metres. A long room, a narrow one, and the walls and floors between them.
LONG, NARROW, WALL, HIGH, SLAB, DEEP = 9.4, 2.6, 0.3, 2.7, 0.3, 4.2
# Over each floor, across the whole front, is a painted board, as over a shop. The page letters them.
FASCIA = 1.05
HALF = (LONG + NARROW + 3 * WALL) / 2
TOP = SLAB + 3 * (HIGH + FASCIA)
EAVE, RIDGE = 0.3, 1.6
# What the camera frames: the building and a margin round it.
FRAME_W, FRAME_H = 2 * HALF + 1.0, TOP + EAVE + RIDGE + 1.3

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
materials = {}


def linear(code):
    channel = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(channel(int(code[i : i + 2], 16) / 255) for i in (1, 3, 5)) + (1,)


def paint(colour, rough=0.6, metal=0.0, glow=0.0):
    """A plain material. glow is how brightly it shines of itself."""
    key = (colour, rough, metal, glow)
    if key not in materials:
        material = bpy.data.materials.new(colour)
        material.use_nodes = True
        shader = material.node_tree.nodes["Principled BSDF"]
        shader.inputs["Base Color"].default_value = linear(colour)
        shader.inputs["Roughness"].default_value = rough
        shader.inputs["Metallic"].default_value = metal
        if glow:
            shader.inputs["Emission Color"].default_value = linear(colour)
            shader.inputs["Emission Strength"].default_value = glow
        else:
            worn(material, colour=linear(colour))
        materials[key] = material
    return materials[key]


def worn(material, colour=None, source=None, under=None, tooth_depth=0.22):
    """Nothing in a model is quite flat or quite one colour: give a material a fine tooth, and mottle it."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    tooth, bump = nodes.new("ShaderNodeTexNoise"), nodes.new("ShaderNodeBump")
    tooth.inputs["Scale"].default_value = 45
    tooth.inputs["Detail"].default_value = 6
    bump.inputs["Strength"].default_value = tooth_depth
    bump.inputs["Distance"].default_value = 0.02
    links.new(tooth.outputs["Fac"], bump.inputs["Height"])
    if under is not None:
        links.new(under.outputs["Normal"], bump.inputs["Normal"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    # Nor is it evenly smooth: it is duller in patches.
    patches, dull = nodes.new("ShaderNodeTexNoise"), nodes.new("ShaderNodeMapRange")
    patches.inputs["Scale"].default_value = 4
    base = shader.inputs["Roughness"].default_value
    dull.inputs["To Min"].default_value, dull.inputs["To Max"].default_value = max(base - 0.12, 0.05), min(base + 0.2, 1)
    links.new(patches.outputs["Fac"], dull.inputs["Value"])
    links.new(dull.outputs["Result"], shader.inputs["Roughness"])
    if colour is None and source is None:
        return
    mottle, shade, mix = nodes.new("ShaderNodeTexNoise"), nodes.new("ShaderNodeMapRange"), nodes.new("ShaderNodeMixRGB")
    mottle.inputs["Scale"].default_value = 1.6
    mottle.inputs["Detail"].default_value = 8
    shade.inputs["To Min"].default_value, shade.inputs["To Max"].default_value = 0.72, 1.12
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 1
    links.new(mottle.outputs["Fac"], shade.inputs["Value"])
    links.new(shade.outputs["Result"], mix.inputs["Color2"])
    if source is None:
        mix.inputs["Color1"].default_value = colour
    else:
        links.new(source, mix.inputs["Color1"])
    links.new(mix.outputs["Color"], shader.inputs["Base Color"])


def papered(one, two, width, chequer=False, rough=0.7):
    """Wallpaper in stripes of two colours, each this wide, or a floor chequered in them."""
    key = (one, two, width, chequer)
    if key not in materials:
        material = bpy.data.materials.new(one + two)
        material.use_nodes = True
        nodes, links = material.node_tree.nodes, material.node_tree.links
        shader = nodes["Principled BSDF"]
        shader.inputs["Roughness"].default_value = rough
        place = nodes.new("ShaderNodeNewGeometry")
        texture = nodes.new("ShaderNodeTexChecker")
        texture.inputs["Color1"].default_value = linear(one)
        texture.inputs["Color2"].default_value = linear(two)
        texture.inputs["Scale"].default_value = 1 / width
        if chequer:
            links.new(place.outputs["Position"], texture.inputs["Vector"])
        else:
            # Only how far along the wall counts, so the chequer's squares run on as stripes.
            apart, together = nodes.new("ShaderNodeSeparateXYZ"), nodes.new("ShaderNodeCombineXYZ")
            links.new(place.outputs["Position"], apart.inputs[0])
            links.new(apart.outputs["X"], together.inputs["X"])
            links.new(together.outputs[0], texture.inputs["Vector"])
        worn(material, source=texture.outputs["Color"])
        materials[key] = material
    return materials[key]


def laid(one, two, joint, across, down, lie="wall", rough=0.6, sunk=0.5):
    """A surface laid in courses: slates, bricks or boards. across and down are one piece's size, and lie
    is which way the surface faces: a wall, a floor, or a roof that leans back as it climbs."""
    key = (one, two, joint, across, down, lie)
    if key not in materials:
        material = bpy.data.materials.new(one + lie)
        material.use_nodes = True
        nodes, links = material.node_tree.nodes, material.node_tree.links
        shader = nodes["Principled BSDF"]
        shader.inputs["Roughness"].default_value = rough
        place, apart, together = nodes.new("ShaderNodeNewGeometry"), nodes.new("ShaderNodeSeparateXYZ"), nodes.new("ShaderNodeCombineXYZ")
        links.new(place.outputs["Position"], apart.inputs[0])
        links.new(apart.outputs["X"], together.inputs["X"])
        if lie == "floor":
            links.new(apart.outputs["Y"], together.inputs["Y"])
        else:
            climb = nodes.new("ShaderNodeMath")
            climb.operation = "ADD"
            links.new(apart.outputs["Z"], climb.inputs[0])
            links.new(apart.outputs["Y"], climb.inputs[1])
            links.new(climb.outputs[0], together.inputs["Y"])
        courses = nodes.new("ShaderNodeTexBrick")
        courses.inputs["Color1"].default_value, courses.inputs["Color2"].default_value = linear(one), linear(two)
        courses.inputs["Mortar"].default_value = linear(joint)
        courses.inputs["Scale"].default_value = 1
        courses.inputs["Mortar Size"].default_value = 0.012
        courses.inputs["Brick Width"].default_value, courses.inputs["Row Height"].default_value = across, down
        links.new(together.outputs[0], courses.inputs["Vector"])
        height, bump = nodes.new("ShaderNodeMath"), nodes.new("ShaderNodeBump")
        height.operation = "SUBTRACT"
        height.inputs[0].default_value = 1
        links.new(courses.outputs["Fac"], height.inputs[1])
        bump.inputs["Strength"].default_value = sunk
        bump.inputs["Distance"].default_value = 0.03
        links.new(height.outputs[0], bump.inputs["Height"])
        worn(material, source=courses.outputs["Color"], under=bump)
        materials[key] = material
    return materials[key]


def box(x0, x1, y0, y1, z0, z1, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    solid = bpy.context.object
    solid.scale = (x1 - x0, y1 - y0, z1 - z0)
    solid.data.materials.append(material)
    bpy.ops.object.transform_apply(scale=True)
    eased = solid.modifiers.new("eased", "BEVEL")
    eased.width, eased.segments = min(0.02, 0.2 * min(x1 - x0, y1 - y0, z1 - z0)), 2
    return solid


def rod(x, y, z, radius, length, material, along="Z", top=None):
    """A cylinder centred here, lying along an axis. top narrows or widens its far end into a cone."""
    turn = {"Z": (0, 0, 0), "Y": (math.pi / 2, 0, 0), "X": (0, math.pi / 2, 0)}[along]
    if top is None:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, location=(x, y, z), rotation=turn, vertices=40)
    else:
        bpy.ops.mesh.primitive_cone_add(radius1=radius, radius2=top, depth=length, location=(x, y, z), rotation=turn, vertices=40)
    solid = bpy.context.object
    solid.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return solid


def ball(x, y, z, radius, material):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=(x, y, z))
    bpy.context.object.data.materials.append(material)
    bpy.ops.object.shade_smooth()


def lamp(x, y, z, watts, across, colour="#ffd9a0"):
    bpy.ops.object.light_add(type="AREA", location=(x, y, z))
    light = bpy.context.object.data
    light.energy, light.size, light.color = watts, across, linear(colour)[:3]


PINK, PLASTER, CREAM, BRASS = paint("#e2939f", 0.75), paint("#eaa7b0", 0.75), paint("#f1e4c9", 0.7), paint("#c9982f", 0.3, 1.0)
WOOD, DARK, STEEL = paint("#7a4a2e"), paint("#3b1f1a"), paint("#aeb8b8", 0.35, 1.0)
BULB = paint("#ffe2a8", glow=30)
BOARDS = laid("#8a5a3c", "#6f4429", "#3a2416", 2.4, 0.22, "floor", 0.4, 0.35)
BRICK = laid("#b4532f", "#9a4326", "#d9cdb8", 0.42, 0.14, "wall", 0.8, 0.6)
SLATE = laid("#5e5a70", "#4a4760", "#2a2836", 0.46, 0.3, "roof", 0.5, 0.9)


def bulb(x, y, z, watts):
    bpy.ops.object.light_add(type="POINT", location=(x, y, z))
    light = bpy.context.object.data
    light.energy, light.shadow_soft_size, light.color = watts, 0.09, linear("#ffc98a")[:3]


def pendant(x, y, ceiling, shade):
    bulb(x, y, ceiling - 0.78, 420)
    rod(x, y, ceiling - 0.25, 0.012, 0.5, DARK)
    rod(x, y, ceiling - 0.6, 0.3, 0.24, shade, top=0.06)
    ball(x, y, ceiling - 0.68, 0.09, BULB)


def sconce(x, z):
    bulb(x, DEEP - 0.36, z + 0.06, 170)
    rod(x, DEEP - 0.08, z, 0.03, 0.16, BRASS, "Y")
    ball(x, DEEP - 0.2, z + 0.06, 0.11, BULB)


def room(x0, x1, z0, wall, floor, dado=None):
    """Line a room: its paper, its floor and its ceiling, and a dado along the foot of the walls."""
    box(x0, x1, DEEP - 0.02, DEEP, z0, z0 + HIGH, wall)
    box(x0, x0 + 0.02, 0, DEEP, z0, z0 + HIGH, wall)
    box(x1 - 0.02, x1, 0, DEEP, z0, z0 + HIGH, wall)
    box(x0, x1, 0, DEEP, z0, z0 + 0.02, floor)
    box(x0, x1, 0, DEEP, z0 + HIGH - 0.02, z0 + HIGH, CREAM)
    if dado:
        box(x0, x1, DEEP - 0.06, DEEP, z0, z0 + 1.0, dado)
        box(x0, x1, DEEP - 0.09, DEEP, z0 + 1.0, z0 + 1.07, CREAM)
    lamp((x0 + x1) / 2, DEEP * 0.45, z0 + HIGH - 0.1, 6 * (x1 - x0), min(x1 - x0, 5))
    # A skirting along the foot of the back wall, and a cornice under the ceiling.
    box(x0, x1, DEEP - 0.07, DEEP - 0.02, z0 + 0.02, z0 + 0.16, CREAM)
    box(x0, x1, DEEP - 0.12, DEEP - 0.02, z0 + HIGH - 0.14, z0 + HIGH - 0.02, CREAM)


def carton(x, y, z, w, d, h, body, ribbon):
    """A box tied up with ribbon, standing on z."""
    box(x - w / 2, x + w / 2, y - d / 2, y + d / 2, z, z + h, body)
    box(x - 0.03, x + 0.03, y - d / 2 - 0.006, y + d / 2 + 0.006, z, z + h + 0.006, ribbon)
    box(x - w / 2 - 0.006, x + w / 2 + 0.006, y - 0.03, y + 0.03, z, z + h + 0.006, ribbon)


def parcels(x0, x1, z0):
    """The top floor: cake boxes on shelves either side, a counter with a scale between, a clock over it."""
    middle = (x0 + x1) / 2
    box_pink, box_pale, ribbon = paint("#f2a3b0", 0.5), paint("#f8cdd2", 0.5), paint("#3f73a8", 0.4)
    room(x0, x1, z0, papered("#f1b9bd", "#f6cfd0", 0.22), BOARDS, paint("#d98a96"))
    for side in (-1, 1):
        near, far = middle + side * 1.9, (x0 if side < 0 else x1) - side * 0.25
        left, right = min(near, far), max(near, far)
        for upright in (left, (left + right) / 2, right):
            box(upright - 0.04, upright + 0.04, DEEP - 0.75, DEEP - 0.05, z0, z0 + 2.58, WOOD)
        for shelf, height in enumerate((0.4, 0.95, 1.5, 2.05)):
            box(left, right, DEEP - 0.75, DEEP - 0.05, z0 + height, z0 + height + 0.05, WOOD)
            count = int((right - left - 0.3) / 0.52)
            for i in range(count):
                x = left + 0.38 + i * (right - left - 0.76) / max(count - 1, 1)
                tall = 0.3 + 0.08 * ((i * 3 + shelf) % 3)
                carton(x, DEEP - 0.42, z0 + height + 0.05, 0.4, 0.42, tall, box_pink if (i + shelf) % 3 else box_pale, ribbon)
        # A pyramid of boxes out on the floor.
        for row, across in enumerate((3, 2, 1)):
            for i in range(across):
                carton(middle + side * (3.3 + (i - (across - 1) / 2) * 0.5), 1.3, z0 + 0.02 + row * 0.38, 0.46, 0.46, 0.38, box_pale if row % 2 else box_pink, ribbon)
        pendant(middle + side * 3.1, 1.9, z0 + HIGH, paint("#b3291b", 0.4))
    box(middle - 1.5, middle + 1.5, 2.3, 3.1, z0, z0 + 0.92, paint("#b3291b", 0.45))
    box(middle - 1.6, middle + 1.6, 2.2, 3.2, z0 + 0.92, z0 + 0.98, CREAM)
    # The scale stands at one end of the counter, with a bell in the middle of it and the clock over that.
    at = middle - 1.05
    rod(at, 2.6, z0 + 1.0, 0.14, 0.05, BRASS)
    rod(at, 2.6, z0 + 1.17, 0.018, 0.34, BRASS)
    box(at - 0.34, at + 0.34, 2.585, 2.615, z0 + 1.32, z0 + 1.35, BRASS)
    for side in (-1, 1):
        rod(at + side * 0.32, 2.6, z0 + 1.22, 0.12, 0.025, BRASS)
        rod(at + side * 0.32, 2.6, z0 + 1.27, 0.005, 0.1, BRASS)
    carton(middle + 1.05, 2.6, z0 + 0.98, 0.34, 0.34, 0.26, box_pink, ribbon)
    rod(middle, 2.6, z0 + 1.0, 0.09, 0.04, BRASS)
    ball(middle, 2.6, z0 + 1.02, 0.075, BRASS)
    rod(middle, DEEP - 0.06, z0 + 2.2, 0.29, 0.06, BRASS, "Y")
    rod(middle, DEEP - 0.1, z0 + 2.2, 0.25, 0.04, CREAM, "Y")
    box(middle - 0.01, middle + 0.01, DEEP - 0.13, DEEP - 0.12, z0 + 2.2, z0 + 2.4, DARK)
    box(middle, middle + 0.14, DEEP - 0.13, DEEP - 0.12, z0 + 2.19, z0 + 2.21, DARK)

def bank(x0, x1, z0):
    """The middle floor: marble columns, a long counter with brass grilles at either end, lamps on it."""
    middle = (x0 + x1) / 2
    marble, green = paint("#efe6d2", 0.3), paint("#1f5a4c", 0.5)
    room(x0, x1, z0, papered("#1f5a4c", "#236453", 0.3), papered("#2a1a17", "#efe6d2", 0.6, chequer=True, rough=0.25), marble)
    for x in (x0 + 0.5, middle - 2.2, middle + 2.2, x1 - 0.5):
        rod(x, DEEP - 0.55, z0 + HIGH / 2, 0.2, HIGH, marble)
        box(x - 0.3, x + 0.3, DEEP - 0.85, DEEP - 0.25, z0, z0 + 0.14, marble)
        box(x - 0.3, x + 0.3, DEEP - 0.85, DEEP - 0.25, z0 + HIGH - 0.16, z0 + HIGH - 0.02, marble)
    box(x0 + 0.2, x1 - 0.2, 2.2, 2.9, z0, z0 + 0.98, paint("#5a2a1c", 0.4))
    box(x0 + 0.1, x1 - 0.1, 2.1, 3.0, z0 + 0.98, z0 + 1.05, marble)
    for side in (-1, 1):
        near, far = middle + side * 2.6, (x0 if side < 0 else x1) - side * 0.9
        left, right = min(near, far), max(near, far)
        box(left, right, 2.5, 2.56, z0 + 2.2, z0 + 2.3, BRASS)
        box(left, right, 2.5, 2.56, z0 + 1.42, z0 + 1.47, BRASS)
        for i in range(int((right - left) / 0.13) + 1):
            rod(left + i * 0.13, 2.53, z0 + 1.86, 0.014, 0.8, BRASS)
        for post in (left, right):
            box(post - 0.04, post + 0.04, 2.48, 2.58, z0 + 1.05, z0 + 2.3, BRASS)
        # A banker's lamp, and gold on the counter.
        x = middle + side * 1.5
        rod(x, 2.5, z0 + 1.07, 0.1, 0.03, BRASS)
        rod(x, 2.5, z0 + 1.2, 0.012, 0.26, BRASS)
        rod(x, 2.5, z0 + 1.34, 0.07, 0.34, paint("#1f7a5c", 0.25), "X")
        ball(x, 2.5, z0 + 1.3, 0.05, BULB)
        for row, across in enumerate((3, 2, 1)):
            for i in range(across):
                bar = middle + side * 0.55 + (i - (across - 1) / 2) * 0.2
                box(bar - 0.085, bar + 0.085, 2.4, 2.72, z0 + 1.05 + row * 0.075, z0 + 1.12 + row * 0.075, paint("#e0b12f", 0.25, 1.0))
        sconce(middle + side * 3.4, z0 + 2.2)
        pendant(middle + side * 1.2, 1.4, z0 + HIGH, green)


def dispatch(x0, x1, z0):
    """The bottom floor: trunks stacked and strapped either side, and a trolley with one more."""
    middle = (x0 + x1) / 2
    hides = (paint("#b9783e", 0.5), paint("#8f4f2a", 0.5), paint("#d9a441", 0.5), paint("#a3301f", 0.5))
    strap = paint("#4a2c1c", 0.6)
    room(x0, x1, z0, papered("#e3a933", "#e9b647", 0.26), papered("#2f8f8a", "#efe6d2", 0.55, chequer=True, rough=0.3), paint("#2f8f8a", 0.5))

    def trunk(x, y, z, w, d, h, hide):
        box(x - w / 2, x + w / 2, y - d / 2, y + d / 2, z, z + h, hide)
        for across in (-0.28, 0.28):
            box(x + across * w - 0.035, x + across * w + 0.035, y - d / 2 - 0.008, y + d / 2 + 0.008, z, z + h + 0.008, strap)
        box(x - 0.09, x + 0.09, y - d / 2 - 0.03, y - d / 2, z + h * 0.62, z + h * 0.72, BRASS)

    for side in (-1, 1):
        for row, across in enumerate((3, 2, 1)):
            for i in range(across):
                x = middle + side * (3.15 + (i - (across - 1) / 2) * 1.02)
                trunk(x, DEEP - 0.7, z0 + 0.02 + row * 0.58, 0.96, 0.7, 0.56, hides[(row + i + (side > 0)) % 4])
        # Two cases stood on end, nearer the front.
        for i, lean in enumerate((0.0, 0.55)):
            x = middle + side * (1.75 + lean)
            trunk(x, 1.5 + i * 0.5, z0 + 0.02, 0.42, 0.3, 0.82 - i * 0.14, hides[(i + 2 + (side > 0)) % 4])
        sconce(middle + side * 1.9, z0 + 2.15)
        pendant(middle + side * 3.2, 1.7, z0 + HIGH, paint("#2f8f8a", 0.4))
    # The trolley.
    box(middle - 0.65, middle + 0.65, 1.0, 1.9, z0 + 0.2, z0 + 0.26, WOOD)
    for x in (middle - 0.5, middle + 0.5):
        for y in (1.12, 1.78):
            rod(x, y, z0 + 0.11, 0.09, 0.05, DARK, "X")
    for x in (middle - 0.6, middle + 0.6):
        rod(x, 1.86, z0 + 0.72, 0.02, 0.95, BRASS)
    rod(middle, 1.86, z0 + 1.19, 0.02, 1.2, BRASS, "X")
    trunk(middle, 1.4, z0 + 0.26, 0.98, 0.66, 0.5, hides[3])
    trunk(middle, 1.4, z0 + 0.77, 0.7, 0.5, 0.36, hides[2])


def lift(x0, x1, z0):
    middle = (x0 + x1) / 2
    room(x0, x1, z0, paint("#a3301f", 0.5), BOARDS)
    box(middle - 0.8, middle + 0.8, DEEP - 0.1, DEEP, z0, z0 + 2.35, BRASS)
    for side in (-1, 1):
        box(middle + side * 0.36 - 0.33, middle + side * 0.36 + 0.33, DEEP - 0.14, DEEP - 0.1, z0 + 0.04, z0 + 2.27, paint("#c4532a", 0.35))
    rod(middle, DEEP - 0.06, z0 + 2.52, 0.14, 0.05, BRASS, "Y")
    ball(middle, 2.0, z0 + HIGH - 0.3, 0.14, BULB)
    bulb(middle, 2.0, z0 + HIGH - 0.52, 160)


def vault(x0, x1, z0):
    middle = (x0 + x1) / 2
    room(x0, x1, z0, paint("#55606a", 0.5), papered("#2a1a17", "#efe6d2", 0.6, chequer=True, rough=0.25))
    rod(middle, DEEP - 0.12, z0 + 1.45, 1.05, 0.2, STEEL, "Y")
    rod(middle, DEEP - 0.25, z0 + 1.45, 0.82, 0.08, paint("#8e9a9a", 0.3, 1.0), "Y")
    for turn in range(4):
        spoke = rod(middle, DEEP - 0.36, z0 + 1.45, 0.025, 0.9, BRASS, "X")
        spoke.rotation_euler = (0, math.pi / 2 + turn * math.pi / 4, 0)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.36, minor_radius=0.03, location=(middle, DEEP - 0.36, z0 + 1.45), rotation=(math.pi / 2, 0, 0))
    bpy.context.object.data.materials.append(BRASS)
    bpy.ops.object.shade_smooth()
    ball(middle, 2.0, z0 + HIGH - 0.3, 0.14, BULB)
    bulb(middle, 2.0, z0 + HIGH - 0.52, 160)


def stairs(x0, x1, z0):
    room(x0, x1, z0, papered("#2f8f8a", "#3a9b95", 0.2), BOARDS)
    for step in range(9):
        box(x0 + 0.1 + step * 0.26, x1 - 0.02, DEEP - 1.3, DEEP - 0.02, z0 + step * 0.3, z0 + (step + 1) * 0.3, WOOD if step % 2 else paint("#8a5a3c", 0.45))
    ball((x0 + x1) / 2, 2.0, z0 + HIGH - 0.3, 0.14, BULB)
    bulb((x0 + x1) / 2, 2.0, z0 + HIGH - 0.52, 160)


# The shell: a base, the walls and the floors between, all plastered pink.
INNER = HALF - WALL
box(-INNER, INNER, 0, DEEP, 0, SLAB, PINK)
box(-HALF, HALF, DEEP, DEEP + WALL, 0, TOP, PINK)
for x in (-HALF, INNER):
    box(x, x + WALL, 0, DEEP, 0, TOP, PINK)
long_rooms, narrow_rooms = (dispatch, bank, parcels), (stairs, vault, lift)
for storey in range(3):
    z0 = SLAB + storey * (HIGH + FASCIA)
    box(-INNER, INNER, 0, DEEP, z0 + HIGH, z0 + HIGH + FASCIA, PINK)
    # The board over the floor, glossy with paint and edged in gilt, and a moulding under it.
    foot = z0 + HIGH
    box(-HALF + 0.08, HALF - 0.08, -0.07, 0, foot + 0.07, foot + FASCIA - 0.07, paint(("#143f33", "#16424a", "#6e1f24")[(storey + 1) % 3], 0.22))
    for z in (foot + 0.12, foot + FASCIA - 0.15):
        box(-HALF + 0.16, HALF - 0.16, -0.085, -0.07, z, z + 0.03, BRASS)
    box(-HALF - 0.04, HALF + 0.04, -0.1, 0.02, foot, foot + 0.07, CREAM)
    # The long room is on the left on the top and bottom floors, and on the right between them.
    left = LONG if storey != 1 else NARROW
    divide = -HALF + WALL + left
    box(divide, divide + WALL, 0, DEEP, z0, z0 + HIGH, PINK)
    rooms = (long_rooms[storey], narrow_rooms[storey])
    if storey == 1:
        rooms = rooms[::-1]
    rooms[0](-HALF + WALL, divide, z0)
    rooms[1](divide + WALL, HALF - WALL, z0)

# The cornice, and a mansard roof over it with dormers and chimneys.
box(-HALF - EAVE, HALF + EAVE, -EAVE, DEEP + WALL, TOP, TOP + EAVE, CREAM)
mesh = bpy.data.meshes.new("roof")
build = bmesh.new()
low, high, lean = TOP + EAVE, TOP + EAVE + RIDGE, 0.75
corners = [(-HALF - 0.2, -0.2, low), (HALF + 0.2, -0.2, low), (HALF + 0.2, DEEP + WALL, low), (-HALF - 0.2, DEEP + WALL, low)]
corners += [(-HALF + lean, lean, high), (HALF - lean, lean, high), (HALF - lean, DEEP, high), (-HALF + lean, DEEP, high)]
points = [build.verts.new(corner) for corner in corners]
for face in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (3, 2, 1, 0)):
    build.faces.new([points[i] for i in face])
build.to_mesh(mesh)
roof = bpy.data.objects.new("roof", mesh)
scene.collection.objects.link(roof)
roof.data.materials.append(SLATE)
LEAD, GLASS = paint("#6b6f78", 0.35, 0.9), paint("#1c2630", 0.04)
box(-HALF + lean - 0.08, HALF - lean + 0.08, lean - 0.08, DEEP, high, high + 0.09, LEAD)
rod(0, -EAVE - 0.07, TOP + EAVE - 0.02, 0.09, 2 * HALF + 2 * EAVE + 0.1, LEAD, "X")


def hood(x, z, half, front, back, rise):
    """A dormer's little pitched roof: a ridge running back from over its window."""
    mesh = bpy.data.meshes.new("hood")
    build = bmesh.new()
    points = [build.verts.new(p) for p in ((x - half, front, z), (x + half, front, z), (x, front, z + rise), (x - half, back, z), (x + half, back, z), (x, back, z + rise))]
    for face in ((0, 1, 2), (5, 4, 3), (0, 2, 5, 3), (1, 4, 5, 2), (0, 3, 4, 1)):
        build.faces.new([points[i] for i in face])
    build.to_mesh(mesh)
    solid = bpy.data.objects.new("hood", mesh)
    scene.collection.objects.link(solid)
    solid.data.materials.append(SLATE)


for i in range(5):
    x = (i - 2) * (2 * HALF - 2.6) / 4
    box(x - 0.5, x + 0.5, -0.1, 0.9, low, low + 1.1, PLASTER)
    hood(x, low + 1.1, 0.64, -0.22, 1.0, 0.42)
    box(x - 0.36, x + 0.36, -0.13, -0.09, low + 0.14, low + 0.98, CREAM)
    box(x - 0.3, x + 0.3, -0.145, -0.125, low + 0.2, low + 0.92, paint("#f6c75a", glow=3.5) if i % 2 else GLASS)
    box(x - 0.018, x + 0.018, -0.16, -0.13, low + 0.2, low + 0.92, CREAM)
    box(x - 0.3, x + 0.3, -0.16, -0.13, low + 0.545, low + 0.575, CREAM)
    box(x - 0.42, x + 0.42, -0.2, -0.08, low + 0.1, low + 0.15, CREAM)
for x in (-HALF + 2.2, HALF - 2.2):
    box(x - 0.35, x + 0.35, 1.6, 2.3, high - 0.3, high + 1.0, BRICK)
    box(x - 0.42, x + 0.42, 1.53, 2.37, high + 1.0, high + 1.1, CREAM)
    for pot in (-0.16, 0.16):
        rod(x + pot, 1.95, high + 1.27, 0.1, 0.34, paint("#a3401f", 0.7), top=0.08)

# A moulding along the front of every floor, and the cornice in three steps.
box(-HALF - 0.04, HALF + 0.04, -0.05, 0.02, SLAB - 0.07, SLAB, CREAM)
box(-HALF - 0.12, HALF + 0.12, -0.12, 0.02, TOP - 0.16, TOP, CREAM)
box(-HALF - 0.2, HALF + 0.2, -0.2, 0.02, TOP - 0.06, TOP + 0.04, CREAM)

# The light of a shop window: a low sun square on, and the sky to fill the shadows.
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-34)))
bpy.context.object.data.energy, bpy.context.object.data.angle = 2.5, math.radians(5)
# The table it stands on, which shows only as the shadow the building leaves there.
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
bpy.context.object.is_shadow_catcher = True
world = bpy.data.worlds.new("sky")
world.use_nodes = True
sky = world.node_tree.nodes.new("ShaderNodeTexSky")
try:
    sky.sun_disc = False
    sky.sun_elevation = math.radians(38)
except AttributeError:
    pass
world.node_tree.links.new(sky.outputs["Color"], world.node_tree.nodes["Background"].inputs["Color"])
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.13
scene.world = world

# A long lens from well back and square on, so the rooms keep their depth and nothing leans.
distance = 46
bpy.ops.object.camera_add(location=(0, -distance, FRAME_H / 2 - 0.5), rotation=(math.pi / 2, 0, 0))
scene.camera = bpy.context.object
scene.camera.data.sensor_width = 36
scene.camera.data.lens = 36 * distance / FRAME_W
# A model this small is never sharp from front to back.
scene.camera.data.dof.use_dof = True
scene.camera.data.dof.focus_distance = distance + 1.6
scene.camera.data.dof.aperture_fstop = 0.32
scene.render.resolution_x = int(1600 * SCALE)
scene.render.resolution_y = int(1600 * SCALE * FRAME_H / FRAME_W)
scene.render.film_transparent = True
scene.render.engine = "CYCLES"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
try:
    devices = bpy.context.preferences.addons["cycles"].preferences
    devices.compute_device_type = "METAL"
    devices.get_devices()
    for device in devices.devices:
        device.use = True
    scene.cycles.device = "GPU"
except Exception:
    pass
scene.view_settings.view_transform = "AgX"
try:
    scene.view_settings.look = "AgX - Punchy"
except TypeError:
    pass
scene.view_settings.exposure = 0.3
scene.render.image_settings.file_format = "WEBP"
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.quality = 90
scene.render.filepath = os.path.join(ROOT, "public", "objects", "dollhouse.webp")
bpy.ops.render.render(write_still=True)
print("frame", FRAME_W, FRAME_H, "half", HALF, "top", TOP)
