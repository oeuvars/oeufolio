"""The business card: 3.5 by 2 inches, risograph-printed on heavy uncoated stock. It lies front up, red with
the name in cream, two birds, and a car drawn over a strip of flowers, in a clear vinyl sleeve: the vinyl of the
badge's holder on the first page, cut to the card (sleeve.py). The face is the card's own artwork, art/card.png,
rasterised from the print file (anurag-card-front.svg)."""

import math
import os

import bpy
import numpy as np

from paint import cloud, ramp
from solids import strip_light
from stage import ASSETS
from stock import Sheet, drift

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art")

W, H = 14.8, 8.46
CREAM = "#efe1c4"
# The sleeve: art/sleeve.png runs this far past the card all round (35 of the 684 pixels the card is across).
BAND = W * 35 / 684
# Its film over the card and down to the weld: how high it stands off the card, how high the weld lies, how
# high the rolled rim stands, and how much the film waves, in em.
AIR = 0.12
WELD = 0.02
RIM = 0.035
WAVE = 0.02
# The grey that the vinyl's welds, rolled edge and film scatter back, and the white of its brightest light, as
# sleeve.py measured them against white paper, here against the card's own stock.
GREY = 0.2
WHITE = 0.8
# PVC's index, so its gloss is as strong as vinyl's at every angle.
PVC = 1.54


def texture(nodes, name, scale, colour=False):
    """One of the studio's scanned surfaces, repeating every scale em."""
    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1 / scale, 1 / scale, 1)
    image = nodes.new("ShaderNodeTexImage")
    image.image = bpy.data.images.load(os.path.join(ASSETS, *name))
    image.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    nodes.id_data.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    nodes.id_data.links.new(mapping.outputs["Vector"], image.inputs["Vector"])
    return image


def vinyl():
    """Soft clear PVC. Its welds, rolled edge and film scatter a little light back, white and grey, as sleeve.py
    found the holder's to do, and it is otherwise clear. Over that it is glossy, and the gloss is what makes it
    vinyl: it mirrors the window by day and the lamp at night in the slow waves of the film, its polish dulled
    where it has been handled and lightly scratched, with the fine orange peel of calendered sheet. Light through
    it is held back where it is grey, so its welds throw faint shadows."""
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

    # The surface: orange peel and scratches in its relief, fingermarks and scuffs in its polish.
    peel = nodes.new("ShaderNodeTexNoise")
    peel.inputs["Scale"].default_value = 90.0
    peel.inputs["Detail"].default_value = 3.0
    links.new(coord.outputs["Object"], peel.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.025
    bump.inputs["Distance"].default_value = 0.002
    links.new(peel.outputs["Fac"], bump.inputs["Height"])
    scratches = texture(nodes, ("Scratches003", "Scratches003_1K-JPG_NormalGL.jpg"), 9)
    scratched = nodes.new("ShaderNodeNormalMap")
    scratched.inputs["Strength"].default_value = 0.1
    links.new(scratches.outputs["Color"], scratched.inputs["Color"])
    both = nodes.new("ShaderNodeVectorMath")
    both.operation = "ADD"
    links.new(bump.outputs["Normal"], both.inputs[0])
    links.new(scratched.outputs["Normal"], both.inputs[1])
    normal = nodes.new("ShaderNodeVectorMath")
    normal.operation = "NORMALIZE"
    links.new(both.outputs[0], normal.inputs[0])
    marks = texture(nodes, ("Fingerprints009", "Fingerprints009_1K-JPG_Roughness.jpg"), 8)
    scuffs = texture(nodes, ("SurfaceImperfections003", "SurfaceImperfections003_1K-JPG_Color.jpg"), 11)
    handled = nodes.new("ShaderNodeMath")
    handled.operation = "MAXIMUM"
    links.new(marks.outputs["Color"], handled.inputs[0])
    links.new(scuffs.outputs["Color"], handled.inputs[1])
    polish = nodes.new("ShaderNodeMapRange")
    polish.inputs["To Min"].default_value = 0.035
    polish.inputs["To Max"].default_value = 0.3
    links.new(handled.outputs[0], polish.inputs["Value"])
    gloss = nodes.new("ShaderNodeBsdfGlossy")
    gloss.distribution = "GGX"
    gloss.inputs["Color"].default_value = (1, 1, 1, 1)
    links.new(polish.outputs[0], gloss.inputs["Roughness"])
    links.new(normal.outputs[0], gloss.inputs["Normal"])
    fresnel = nodes.new("ShaderNodeFresnel")
    fresnel.inputs["IOR"].default_value = PVC
    links.new(normal.outputs[0], fresnel.inputs["Normal"])
    coated = nodes.new("ShaderNodeMixShader")
    links.new(fresnel.outputs[0], coated.inputs[0])
    links.new(whitened.outputs[0], coated.inputs[1])
    links.new(gloss.outputs[0], coated.inputs[2])

    # In the way of the light, the film passes what it neither reflects nor scatters back.
    held = nodes.new("ShaderNodeMath")
    held.operation = "MULTIPLY_ADD"
    held.inputs[1].default_value = -0.6
    held.inputs[2].default_value = 0.92
    links.new(split.outputs["Green"], held.inputs[0])
    shade = nodes.new("ShaderNodeBsdfTransparent")
    links.new(held.outputs[0], shade.inputs["Color"])
    path = nodes.new("ShaderNodeLightPath")
    either = nodes.new("ShaderNodeMixShader")
    links.new(path.outputs["Is Shadow Ray"], either.inputs[0])
    links.new(coated.outputs[0], either.inputs[1])
    links.new(shade.outputs[0], either.inputs[2])
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(either.outputs[0], out.inputs["Surface"])
    return material


def sleeve(stage, top, seed):
    """The sleeve's film, its picture spread from corner to corner. It lies on the card a hair clear of it,
    following its curl, falls away past the card's edges to the weld, and rises again at the rolled rim, and
    the whole sheet waves a little, as calendered PVC never lies flat."""
    step = 0.04
    xs = np.arange(-BAND, W + BAND + step / 2, step)
    ys = np.arange(-BAND, H + BAND + step / 2, step)
    X, Y = np.meshgrid(xs, ys)
    # How far outside the card, rounded at its corners.
    dx = np.maximum(np.maximum(-X, X - W), 0)
    dy = np.maximum(np.maximum(-Y, Y - H), 0)
    out = np.hypot(dx, dy)
    over = top(np.clip(X, 0, W), np.clip(Y, 0, H)) + AIR
    fall = np.clip(out / (0.55 * BAND), 0, 1)
    fall = fall * fall * (3 - 2 * fall)
    z = over * (1 - fall) + WELD * fall
    # The rolled rim, a little in from the sleeve's edge.
    z += RIM * np.exp(-(((BAND - out) - 0.12) / 0.07) ** 2) * (out > 0.5 * BAND)
    z += WAVE * cloud(X.shape, seed, falloff=3.2)
    rows, cols = X.shape
    verts = [(x, -y, h) for x, y, h in zip(X.ravel(), Y.ravel(), z.ravel())]
    faces = [(r * cols + c, r * cols + c + 1, (r + 1) * cols + c + 1, (r + 1) * cols + c) for r in range(rows - 1) for c in range(cols - 1)]
    mesh = bpy.data.meshes.new("sleeve")
    mesh.from_pydata(verts, [], faces)
    u = (X.ravel() + BAND) / (W + 2 * BAND)
    v = 1 - (Y.ravel() + BAND) / (H + 2 * BAND)
    uv = np.column_stack((u, v))
    loops = np.array([index for face in faces for index in face])
    mesh.uv_layers.new().data.foreach_set("uv", uv[loops].ravel())
    for polygon in mesh.polygons:
        polygon.use_smooth = True
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
    sleeve(stage, lambda x, y: 0.07 + wave(x, y) + 0.05 * (x / W) ** 2, seed + 5)
    # The window over the desk, which only reflections see: the film's gloss mirrors it across its waves.
    strip_light(stage, "window", (W * 0.7, -H * 0.3, 40.0), 40.0, 7.0, 12.0, turn=math.radians(58))
    stage.shoot("card", (0, 0, W, H), bleed=1.0, lens=False)


SHOTS = {"card": lambda stage: face(stage, 90)}
