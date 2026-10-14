"""The business card: 3.5 by 2 inches, risograph-printed on heavy uncoated stock. It lies front up, red with
the name in cream, two birds, and a car drawn over a strip of flowers, in a clear vinyl sleeve: the vinyl of the
badge's holder on the first page, cut to the card (sleeve.py). The face is the card's own artwork, art/card.png,
rasterised from the print file (anurag-card-front.svg)."""

import os

import bpy
import numpy as np

from paint import cloud, ramp
from stock import Sheet, drift

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art")

W, H = 14.8, 8.46
CREAM = "#efe1c4"
# The sleeve: art/sleeve.png runs this far past the card all round (35 of the 684 pixels the card is across),
# and lies this high, over the card's own curl.
BAND = W * 35 / 684
LIFT = 0.3
# The grey that the vinyl's welds, rolled edge and film scatter back, and the white of its brightest light, as
# sleeve.py measured them against white paper, here against the card's own stock.
GREY = 0.2
WHITE = 0.8


def vinyl():
    """A film that is, at each point, a little white and a little grey and otherwise clear, as sleeve.py found the
    holder's vinyl to be. It is lit as everything on the desk is, so the window shows in it by day and the lamp at
    night. Light through it is held back where it is grey, so its welds throw faint shadows."""
    material = bpy.data.materials.new("vinyl")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    coord = nodes.new("ShaderNodeTexCoord")
    film = nodes.new("ShaderNodeTexImage")
    film.image = bpy.data.images.load(os.path.join(ART, "sleeve.png"))
    film.image.colorspace_settings.name = "Non-Color"
    film.interpolation = "Cubic"
    links.new(coord.outputs["UV"], film.inputs["Vector"])
    split = nodes.new("ShaderNodeSeparateColor")
    links.new(film.outputs["Color"], split.inputs[0])
    clear = nodes.new("ShaderNodeBsdfTransparent")
    grey = nodes.new("ShaderNodeBsdfDiffuse")
    grey.inputs["Color"].default_value = (GREY, GREY, GREY, 1)
    white = nodes.new("ShaderNodeBsdfDiffuse")
    white.inputs["Color"].default_value = (WHITE, WHITE, WHITE, 1)
    greyed = nodes.new("ShaderNodeMixShader")
    links.new(split.outputs["Green"], greyed.inputs[0])
    links.new(clear.outputs[0], greyed.inputs[1])
    links.new(grey.outputs[0], greyed.inputs[2])
    whitened = nodes.new("ShaderNodeMixShader")
    links.new(split.outputs["Red"], whitened.inputs[0])
    links.new(greyed.outputs[0], whitened.inputs[1])
    links.new(white.outputs[0], whitened.inputs[2])
    # In the way of the light, the film passes what it does not scatter back.
    held = nodes.new("ShaderNodeMath")
    held.operation = "MULTIPLY_ADD"
    held.inputs[1].default_value = -0.6
    held.inputs[2].default_value = 1.0
    links.new(split.outputs["Green"], held.inputs[0])
    shade = nodes.new("ShaderNodeBsdfTransparent")
    links.new(held.outputs[0], shade.inputs["Color"])
    path = nodes.new("ShaderNodeLightPath")
    either = nodes.new("ShaderNodeMixShader")
    links.new(path.outputs["Is Shadow Ray"], either.inputs[0])
    links.new(whitened.outputs[0], either.inputs[1])
    links.new(shade.outputs[0], either.inputs[2])
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(either.outputs[0], out.inputs["Surface"])
    material.blend_method = "BLEND"
    return material


def sleeve(stage):
    """The sleeve as a sheet of film over the card, its picture spread from corner to corner."""
    x0, y0, x1, y1 = -BAND, -BAND, W + BAND, H + BAND
    mesh = bpy.data.meshes.new("sleeve")
    mesh.from_pydata([(x0, -y1, LIFT), (x1, -y1, LIFT), (x1, -y0, LIFT), (x0, -y0, LIFT)], [], [(0, 1, 2, 3)])
    mesh.uv_layers.new().data.foreach_set("uv", [0, 0, 1, 0, 1, 1, 0, 1])
    mesh.materials.append(vinyl())
    return stage.add("sleeve", mesh)


def face(stage, seed):
    sheet = Sheet(W, H, CREAM, rough=0.8)
    sheet.art(os.path.join(ART, "card.png"), 0, 0, W, H)
    shape = sheet.height.shape
    # Riso ink sits in the tooth of the paper and is never quite even, and a card carried about rubs at its edges.
    sheet.rgb *= (1 + 0.012 * cloud(shape, seed, falloff=1.2))[..., None]
    sheet.height += 0.0006 * cloud(shape, seed + 1, falloff=0.5)
    worn = (1 - ramp(0, 0.15, -sheet.sdf)) * np.clip(0.3 + 0.5 * cloud(shape, seed + 2, falloff=1.4), 0, 1)
    sheet.rgb += (worn * 0.1)[..., None] * (np.array([0.86, 0.8, 0.7]) - sheet.rgb)
    sheet.sdf += 0.006 * cloud(shape, seed + 3, falloff=1.0)
    sheet.soften(0.04, 0.02)
    wave = drift(W, H, 0.06, seed + 4)
    sheet.build(
        stage,
        "card",
        thickness=0.07,
        warp=lambda x, y: wave(x, y) + 0.05 * (x / W) ** 2,
        scan="Paper006",
        scan_size=7,
        scan_normal=0.7,
        scan_rough=0.8,
        scan_colour=0.25,
        wear=(("SurfaceImperfections003", 9, 0.1, 0),),
        sheen=0.25,
        specular=0.25,
    )
    sleeve(stage)
    stage.shoot("card", (0, 0, W, H), bleed=1.0, lens=False)


SHOTS = {"card": lambda stage: face(stage, 90)}
