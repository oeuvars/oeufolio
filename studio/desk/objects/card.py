"""The business card: 3.5 by 2 inches, risograph-printed on heavy uncoated stock. It lies front up, red with
the name in cream, two birds, and a car drawn over a strip of flowers, inside a clear cast
acrylic case, as a one-touch card holder is. The face is the card's own artwork, art/card.png, rasterised
from the print file (anurag-card-front.svg)."""

import math
import os

import bpy
import numpy as np

from paint import cloud, ramp
from solids import prism, rect, strip_light
from stage import ASSETS
from stock import Sheet, drift

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art")

W, H = 14.8, 8.46
CREAM = "#efe1c4"
# The case: a block of clear cast acrylic the card lies inside, as a one-touch card holder is. It runs this far
# past the card all round, stands this high off the mat and its top edge is rounded over this far.
OVER = 0.45
CASE_H = 0.5
ROUND = 0.2


def acrylic():
    """Clear cast acrylic as its makers measure it: about 92 per cent of light passes, about 4 per cent is
    reflected at each face seen straight on, rising steeply toward grazing angles, and haze is about one per
    cent. Face on it is all but invisible. It shows at its polished rounded edges, which see the room at a
    slant, and as a faint even sheen of what hangs over it, where fingermarks dull the polish. Light falling
    through its flat faces passes almost whole, but where it falls through the curved edges it is bent away,
    so its shadow is a dark rim round a clear middle."""
    material = bpy.data.materials.new("acrylic")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1)
    shader.inputs["Transmission Weight"].default_value = 1.0
    shader.inputs["IOR"].default_value = 1.49
    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1 / 7, 1 / 7, 1)
    marks = nodes.new("ShaderNodeTexImage")
    marks.image = bpy.data.images.load(os.path.join(ASSETS, "Fingerprints009", "Fingerprints009_1K-JPG_Color.jpg"))
    marks.image.colorspace_settings.name = "Non-Color"
    dull = nodes.new("ShaderNodeMath")
    dull.operation = "MULTIPLY_ADD"
    dull.inputs[1].default_value = 0.12
    dull.inputs[2].default_value = 0.004
    links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], marks.inputs["Vector"])
    links.new(marks.outputs["Color"], dull.inputs[0])
    # The face is polished. The rounded edges, where the case was cut and buffed, are a little less so, and
    # catch the lamp as a soft sheen along them rather than a hairline.
    facing = nodes.new("ShaderNodeLayerWeight")
    facing.inputs["Blend"].default_value = 0.3
    # How far the surface leans from flat: nothing on the top, a few degrees where the edge begins to round.
    shape = nodes.new("ShaderNodeNewGeometry")
    upright = nodes.new("ShaderNodeSeparateXYZ")
    links.new(shape.outputs["Normal"], upright.inputs[0])
    buffed = nodes.new("ShaderNodeMapRange")
    buffed.interpolation_type = "SMOOTHSTEP"
    buffed.inputs["From Min"].default_value = 0.9998
    buffed.inputs["From Max"].default_value = 0.99
    buffed.inputs["To Max"].default_value = 0.15
    links.new(upright.outputs["Z"], buffed.inputs["Value"])
    rough = nodes.new("ShaderNodeMath")
    links.new(dull.outputs[0], rough.inputs[0])
    links.new(buffed.outputs[0], rough.inputs[1])
    links.new(rough.outputs[0], shader.inputs["Roughness"])
    haze = nodes.new("ShaderNodeBsdfDiffuse")
    milky = nodes.new("ShaderNodeMixShader")
    milky.inputs[0].default_value = 0.01
    links.new(shader.outputs[0], milky.inputs[1])
    links.new(haze.outputs[0], milky.inputs[2])
    # The shadow: clear through the flat, darker where the surface turns away.
    rim = nodes.new("ShaderNodeMath")
    rim.operation = "MULTIPLY_ADD"
    rim.inputs[1].default_value = -0.75
    rim.inputs[2].default_value = 0.93
    links.new(facing.outputs["Facing"], rim.inputs[0])
    clear = nodes.new("ShaderNodeBsdfTransparent")
    links.new(rim.outputs[0], clear.inputs["Color"])
    # Seen from above, the rounded edges bend the view through them so far that it turns back inside the
    # block, onto the dark underside of the case: they outline it with a dark band all round, as a slab's
    # edges do in a photograph. The page shows through the rest.
    edge = nodes.new("ShaderNodeMapRange")
    edge.interpolation_type = "SMOOTHSTEP"
    edge.inputs["From Min"].default_value = 0.3
    edge.inputs["From Max"].default_value = 0.85
    edge.inputs["To Max"].default_value = 0.55
    links.new(facing.outputs["Facing"], edge.inputs["Value"])
    path = nodes.new("ShaderNodeLightPath")
    seen = nodes.new("ShaderNodeMath")
    seen.operation = "MULTIPLY"
    links.new(edge.outputs[0], seen.inputs[0])
    links.new(path.outputs["Is Camera Ray"], seen.inputs[1])
    dark = nodes.new("ShaderNodeBsdfDiffuse")
    dark.inputs["Color"].default_value = (0.03, 0.035, 0.032, 1)
    outline = nodes.new("ShaderNodeMixShader")
    links.new(seen.outputs[0], outline.inputs[0])
    links.new(milky.outputs[0], outline.inputs[1])
    links.new(dark.outputs[0], outline.inputs[2])
    # The sheen on the edges lies over the dark band, not under it.
    sheen = nodes.new("ShaderNodeBsdfGlossy")
    sheen.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1)
    links.new(rough.outputs[0], sheen.inputs["Roughness"])
    fresnel = nodes.new("ShaderNodeFresnel")
    fresnel.inputs["IOR"].default_value = 1.49
    over = nodes.new("ShaderNodeMath")
    over.operation = "MULTIPLY"
    links.new(fresnel.outputs[0], over.inputs[0])
    links.new(seen.outputs[0], over.inputs[1])
    edged = nodes.new("ShaderNodeAddShader")
    lit = nodes.new("ShaderNodeMixShader")
    links.new(over.outputs[0], lit.inputs[0])
    links.new(sheen.outputs[0], lit.inputs[2])
    links.new(outline.outputs[0], edged.inputs[0])
    links.new(lit.outputs[0], edged.inputs[1])
    either = nodes.new("ShaderNodeMixShader")
    links.new(path.outputs["Is Shadow Ray"], either.inputs[0])
    links.new(edged.outputs[0], either.inputs[1])
    links.new(clear.outputs[0], either.inputs[2])
    links.new(either.outputs[0], nodes["Material Output"].inputs["Surface"])
    return material


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
    case = prism(stage, "case", rect(-OVER, -OVER, W + OVER, H + OVER, 0.55, 12), 0.0, CASE_H, acrylic(), bevel=ROUND, segments=10)
    # The window over the desk, which only reflections see. It is many times brighter than the paper it lights,
    # so even the four per cent the face reflects of it lies across the case as a soft band of glare.
    window = strip_light(stage, "window", (W * 0.74, -H * 0.36, 40.0), 44.0, 3.2, 5.0, turn=math.radians(58))
    # Polished acrylic mirrors it with edges, softened only where fingermarks dull the polish.
    window.data.materials[0].node_tree.nodes["Map Range"].inputs["From Max"].default_value = 0.3
    stage.shoot("card", (0, 0, W, H), bleed=1.0, shadowless=(case,), lens=False)


SHOTS = {"card": lambda stage: face(stage, 90)}
