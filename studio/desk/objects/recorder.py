"""Industrial design: the front of a Teenage Engineering TP-7, measured off the maker's product photo.
The hub of the reel and the line engraved across it are shot on their own, so the page can turn them."""

import math

import numpy as np

from solids import annulus, capsule, fillet, lathe, plate, principled, prism, rect, ring, spun, stroke, worn
from stock import Sheet

W, H = 11.875, 17.0
TOP = 2.4  # height of the front face above the mat
REEL_X, REEL_Y, REEL_R = 5.885, 6.88, 5.44
HUB_R = 1.445
REEL_FRAME = (REEL_X - REEL_R, REEL_Y - REEL_R, REEL_R * 2, REEL_R * 2)


def knurled(material, radius, pitch):
    """Diamond knurling round a part turned about its own x axis."""
    nodes, links = material.node_tree.nodes, material.node_tree.links

    def math_node(op, a, b):
        node = nodes.new("ShaderNodeMath")
        node.operation = op
        for socket, value in zip(node.inputs, (a, b)):
            if isinstance(value, (int, float)):
                socket.default_value = value
            else:
                links.new(value, socket)
        return node.outputs[0]

    coord = nodes.new("ShaderNodeTexCoord")
    split = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coord.outputs["Object"], split.inputs[0])
    around = math_node("MULTIPLY", math_node("ARCTAN2", split.outputs["Y"], split.outputs["Z"]), radius)
    rate = 2 * math.pi / pitch
    one = math_node("SINE", math_node("MULTIPLY", math_node("ADD", around, split.outputs["X"]), rate), 0)
    two = math_node("SINE", math_node("MULTIPLY", math_node("SUBTRACT", around, split.outputs["X"]), rate), 0)
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.03
    links.new(math_node("MULTIPLY", one, two), bump.inputs["Height"])
    links.new(bump.outputs["Normal"], nodes["Principled BSDF"].inputs["Normal"])
    return material


def blasted(name, colour, rough):
    """Bead-blasted, clear-anodised aluminium, as the TP-7's case is: a fine even matte, the metal's grey with
    a soft sheen that broadens toward grazing light. The blasting leaves a tooth too fine to see, which shows
    as a faint sparkle and keeps the reflections from ever going glossy."""
    material = principled(name, colour, rough=rough, metal=1.0)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    coord = nodes.new("ShaderNodeTexCoord")
    tooth = nodes.new("ShaderNodeTexNoise")
    tooth.inputs["Scale"].default_value = 900
    tooth.inputs["Detail"].default_value = 2
    links.new(coord.outputs["Object"], tooth.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.0015
    bump.inputs["Strength"].default_value = 0.6
    links.new(tooth.outputs[0], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    # The anodising is a thin clear oxide: a faint second sheen over the metal.
    shader.inputs["Coat Weight"].default_value = 0.12
    shader.inputs["Coat Roughness"].default_value = 0.3
    return material


def turned_disc(name, colour):
    """The reel's face: aluminium spun on a lathe and left bright, its turning marks fine concentric grooves.
    They throw the light out along the radius, so a highlight lies across the disc as a bar through its
    centre, and the grooves catch as faint rings."""
    material = spun(principled(name, colour, rough=0.24, metal=1.0), 0.85)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    coord = nodes.new("ShaderNodeTexCoord")
    rings = nodes.new("ShaderNodeTexWave")
    rings.wave_type = "RINGS"
    rings.inputs["Scale"].default_value = 9.0
    rings.inputs["Distortion"].default_value = 0.6
    rings.inputs["Detail"].default_value = 3
    links.new(coord.outputs["Object"], rings.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.002
    bump.inputs["Strength"].default_value = 0.35
    links.new(rings.outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return material


def body(stage):
    alloy = blasted("body", (0.6, 0.6, 0.59), 0.42)
    worn(alloy, "SurfaceImperfections003", 9, 0.08)
    key = blasted("key", (0.64, 0.64, 0.63), 0.4)
    worn(key, "Fingerprints009", 6, 0.12)
    satin = blasted("satin", (0.56, 0.56, 0.55), 0.34)
    turned = turned_disc("reel", (0.72, 0.72, 0.71))
    dark = principled("shadow", (0.012, 0.012, 0.012), rough=0.7)
    ink = principled("ink", (0.03, 0.03, 0.03), rough=0.6)
    engraved = principled("engraved", (0.2, 0.2, 0.2), rough=0.6)
    glass = principled("glass", (0.003, 0.003, 0.004), rough=0.2, specular_ior_level=0.35)
    orange = principled("orange", "#f0611d", rough=0.45)
    mesh = principled("mesh", (0.27, 0.27, 0.26), rough=0.55, metal=1.0)
    face = TOP + 0.002

    # Everything sits on a dark chassis, so the gaps between parts read as gaps.
    prism(stage, "chassis", rect(0.06, 0.06, W - 0.06, H - 0.06, 0.3), 0, TOP - 0.7, dark)
    shell = fillet([(0, 0, 0.34), (W, 0, 0.34), (W, H, 0.34), (8.93, H, 0.08), (8.93, 12.7, 0.08), (0, 12.7, 0.08)])
    prism(stage, "shell", shell, 0, TOP, alloy, bevel=0.07, segments=4)

    # Record, play, stop. Each key leans a little towards the bottom edge.
    lean = (0, -0.02)
    rec = fillet([(0.03, 12.77, 0), (2.86, 12.77, 0), (2.86, H - 0.03, 0), (0.03, H - 0.03, 0.32)])
    prism(stage, "rec", rec, 0.4, TOP + 0.05, key, bevel=0.05, slope=lean)
    prism(stage, "play", rect(2.93, 12.77, 5.83, H - 0.03), 0.4, TOP + 0.05, key, bevel=0.05, slope=lean)
    prism(stage, "stop", rect(5.9, 12.77, 8.87, H - 0.03), 0.4, TOP + 0.05, key, bevel=0.05, slope=lean)
    legend = TOP + 0.08
    plate(stage, "rec-dot", ring(1.445, 13.77, 0.24, 48), legend, orange)
    plate(stage, "play-mark", [(4.14, 13.5), (4.6, 13.77), (4.14, 14.04)], legend, ink)
    plate(stage, "stop-mark", rect(7.22, 13.6, 7.56, 13.94), legend, ink)

    # The reel, a hair proud of the face, with a shadow line round it.
    annulus(stage, "reel-gap", REEL_X, REEL_Y, REEL_R - 0.01, REEL_R + 0.045, face, dark)
    prism(stage, "reel", ring(0, 0, REEL_R, 160), 0.4, TOP + 0.03, turned, bevel=0.035).location = (REEL_X, -REEL_Y, 0)

    # Display, microphones, memo key.
    prism(stage, "display", rect(8.67, 0.47, 11.4, 1.98, 0.2), 0.4, TOP + 0.006, glass, bevel=0.012, segments=2)
    plate(stage, "mic", ring(3.94, 1.09, 0.06, 24), face, dark)
    plate(stage, "mic-far", ring(5.885, 1.09, 0.06, 24), face, engraved)
    prism(stage, "memo", rect(10.92, 3.17, 11.39, 3.64, 0.06), 0.4, TOP + 0.05, orange, bevel=0.03)

    # Rocker down the left edge, on its pivot.
    prism(stage, "rocker", rect(-1.05, 2.4, -0.47, 11.31, 0.29), 0.6, TOP - 0.5, satin, bevel=0.1, segments=4)
    prism(stage, "pivot-arm", rect(-0.6, 6.56, 0.2, 7.1, 0.1), 0.6, TOP - 0.62, satin, bevel=0.04)
    prism(stage, "pivot", ring(-0.5, 6.83, 0.21, 40), 0.6, TOP - 0.44, satin, bevel=0.04)
    plate(stage, "pivot-slot", stroke(-0.64, 6.93, -0.36, 6.73, 0.045), TOP - 0.438, engraved)

    # Three buttons on the right edge and the pin at the top.
    for i, (y0, y1) in enumerate(((2.45, 4.54), (5.37, 6.23), (7.4, 8.32))):
        prism(stage, f"side-{i}", rect(W - 0.3, y0, W + 0.17, y1, 0.08), 0.6, TOP - 0.7, satin, bevel=0.05)
    prism(stage, "pin", rect(1.37, -1.02, 1.73, 0.3, 0.13), 0.6, TOP - 0.7, satin, bevel=0.05)

    # Speaker, and the volume pair in its slanted well.
    plate(stage, "speaker", ring(1.39, 11.65, 0.44, 48), face, mesh)
    plus, minus = (10.85, 10.84), (9.77, 11.83)
    plate(stage, "well-edge", capsule(*minus, *plus, 0.66), face, engraved)
    plate(stage, "well", capsule(*minus, *plus, 0.625), face + 0.001, alloy)
    for name, (x, y) in (("plus", plus), ("minus", minus)):
        prism(stage, name, ring(x, y, 0.52, 64), 0.4, TOP + 0.06, key, bevel=0.05)
        plate(stage, f"{name}-bar", stroke(x - 0.23, y, x + 0.23, y, 0.04), TOP + 0.063, engraved)
    plate(stage, "plus-post", stroke(plus[0], plus[1] - 0.23, plus[0], plus[1] + 0.23, 0.04), TOP + 0.063, engraved)

    # Slots and the cross line beside the keys.
    for i, x in enumerate((9.9, 10.56)):
        plate(stage, f"slot-{i}", rect(x - 0.055, 12.88, x + 0.055, 16.2, 0.05), face, dark)
    plate(stage, "cross", stroke(9.33, 13.74, 11.3, 13.74, 0.03), face, engraved)

    # The jack adaptor, knurled.
    brass = knurled(principled("jack", (0.6, 0.6, 0.59), rough=0.32, metal=1.0), 1.1, 0.2)
    collar = principled("collar", (0.7, 0.7, 0.69), rough=0.3, metal=1.0)
    profile = [(0, 0), (0, 1.1), (2.1, 1.1), (2.24, 0.96), (2.24, 0)]
    jack = lathe(stage, "jack", profile, brass, steps=96, axis="Y")
    jack.location = (10.365, -(H + 0.16), 1.2)
    neck = lathe(stage, "neck", [(0, 0), (0, 0.8), (0.3, 0.8), (0.3, 0)], collar, steps=64, axis="Y")
    neck.location = (10.365, -(H - 0.1), 1.2)

    # Printed name, the readout on the display and the letter on the memo key, from the page's own type.
    legend = Sheet(W, H, "#555653", rough=0.6)
    name, readout, letter = legend.plate("recorder")
    legend.paint(np.maximum(readout, letter), "#ffffff")
    legend.opacity = np.clip(name + readout + letter, 0, 1)
    legend.glow = readout * 1.5
    legend.build(stage, "legend", thickness=TOP + 0.056).visible_shadow = False
    stage.shoot("recorder", (0, 0, W, H), bleed=3.0, shadow=0.85)


def reel(stage):
    hub = turned_disc("hub", (0.62, 0.62, 0.61))
    pin = principled("pin", (0.36, 0.36, 0.35), rough=0.35, metal=1.0)
    engraved = principled("engraved", (0.2, 0.2, 0.2), rough=0.6)
    reach = (REEL_R - 0.12) * math.sqrt(0.5)
    # The reel itself is in the other shot. A stand-in keeps its tone in the hub's edge, where the mat would show.
    turned = turned_disc("reel", (0.72, 0.72, 0.71))
    stand_in = plate(stage, "reel", ring(0, 0, REEL_R, 96), TOP + 0.03, turned)
    stand_in.location = (REEL_X, -REEL_Y, 0)
    stand_in.visible_camera = False
    prism(stage, "hub", ring(0, 0, HUB_R, 96), TOP - 0.3, TOP + 0.07, hub, bevel=0.05).location = (REEL_X, -REEL_Y, 0)
    for turn in (103, 220.6, 347.5):
        x = REEL_X + math.cos(math.radians(turn))
        y = REEL_Y - math.sin(math.radians(turn))
        prism(stage, f"pin-{turn}", ring(x, y, 0.11, 24), TOP, TOP + 0.085, pin, bevel=0.02)
    line = stroke(REEL_X - reach, REEL_Y + reach, REEL_X + reach, REEL_Y - reach, 0.035)
    plate(stage, "line", line, TOP + 0.032, engraved)
    across = HUB_R * math.sqrt(0.5) * 0.96
    plate(stage, "hub-line", stroke(REEL_X - across, REEL_Y + across, REEL_X + across, REEL_Y - across, 0.035), TOP + 0.072, engraved)
    stage.shoot("reel", REEL_FRAME)


SHOTS = {"recorder": body, "reel": reel}
