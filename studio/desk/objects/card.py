"""The business card: 3.5 by 2 inches, risograph-printed on heavy uncoated stock. It lies front up, red with
the name in cream, two birds, and a car drawn over a strip of flowers, in a soft clear vinyl sleeve like the badge
holder on the first page. The face is the card's own artwork, art/card.png, rasterised from the print file
(anurag-card-front.svg)."""

import os

import bpy
import numpy as np

from paint import cloud, ramp
from stage import ASSETS
from stock import Sheet, drift

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art")

W, H = 14.8, 8.46
CREAM = "#efe1c4"
# The sleeve: how far it runs past the card on every side, and the welded seam round its edge.
OVER = 0.5
WELD = 0.32


def vinyl(name, frosted):
    """Soft clear PVC, as card sleeves and badge holders are: water clear with a faint grey, glossy but never
    quite smooth, so its reflections waver. The weld is the same plastic pressed matt. It lets most of the
    light through, so the card under it is not in its shadow."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0.93, 0.95, 0.95, 1)
    shader.inputs["Transmission Weight"].default_value = 1.0
    shader.inputs["IOR"].default_value = 1.53
    shader.inputs["Roughness"].default_value = 0.22 if frosted else 0.03
    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1 / 8, 1 / 8, 1)
    marks = nodes.new("ShaderNodeTexImage")
    marks.image = bpy.data.images.load(os.path.join(ASSETS, "Fingerprints009", "Fingerprints009_1K-JPG_Color.jpg"))
    marks.image.colorspace_settings.name = "Non-Color"
    dull = nodes.new("ShaderNodeMath")
    dull.operation = "MULTIPLY_ADD"
    dull.inputs[1].default_value = 0.12
    dull.inputs[2].default_value = shader.inputs["Roughness"].default_value
    links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], marks.inputs["Vector"])
    links.new(marks.outputs["Color"], dull.inputs[0])
    links.new(dull.outputs[0], shader.inputs["Roughness"])
    # The sheet is never flat: a slow ripple in it, which only its reflections show.
    ripple = nodes.new("ShaderNodeTexNoise")
    ripple.inputs["Scale"].default_value = 0.6
    ripple.inputs["Detail"].default_value = 2
    links.new(coord.outputs["Object"], ripple.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.02
    bump.inputs["Strength"].default_value = 0.4
    links.new(ripple.outputs[0], bump.inputs["Height"])
    if frosted:
        # The weld's ribbing, pressed in by the sealing bar.
        ribs = nodes.new("ShaderNodeTexWave")
        ribs.wave_type = "BANDS"
        ribs.inputs["Scale"].default_value = 40
        links.new(coord.outputs["Object"], ribs.inputs["Vector"])
        both = nodes.new("ShaderNodeMath")
        both.operation = "ADD"
        links.new(ripple.outputs[0], both.inputs[0])
        links.new(ribs.outputs["Fac"], both.inputs[1])
        links.new(both.outputs[0], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    # Shadows: the plastic only dims the light a little.
    out = nodes["Material Output"]
    path = nodes.new("ShaderNodeLightPath")
    clear = nodes.new("ShaderNodeBsdfTransparent")
    clear.inputs["Color"].default_value = (0.93, 0.94, 0.94, 1)
    either = nodes.new("ShaderNodeMixShader")
    links.new(path.outputs["Is Shadow Ray"], either.inputs[0])
    links.new(shader.outputs[0], either.inputs[1])
    links.new(clear.outputs[0], either.inputs[2])
    links.new(either.outputs[0], out.inputs["Surface"])
    return material


def sleeve(stage, top):
    """The sleeve over the card: a thin sheet that lies on the card and drops to the mat round it in a soft
    fold, and the flat welded seam at its edge. top(x, y) is how high the card's face is there."""
    step = 0.06
    xs = np.arange(-OVER, W + OVER + step / 2, step)
    ys = np.arange(-OVER, H + OVER + step / 2, step)
    X, Y = np.meshgrid(xs, ys)
    # Outside the card the sheet falls from the card's edge to the weld, which lies on the mat.
    out = np.maximum(np.maximum(-X, X - W), np.maximum(-Y, Y - H))
    face = np.vectorize(top)(np.clip(X, 0, W), np.clip(Y, 0, H))
    Z = 0.025 + (face + 0.015) * (1 - ramp(0.0, OVER - WELD, out))
    # A pillow of air where the sheet stands off the card toward its middle.
    Z += 0.03 * np.sin(np.pi * np.clip(X / W, 0, 1)) * np.sin(np.pi * np.clip(Y / H, 0, 1))
    rows, cols = X.shape
    verts = np.column_stack((X.ravel(), -Y.ravel(), Z.ravel()))
    i, k = np.meshgrid(np.arange(rows - 1), np.arange(cols - 1), indexing="ij")
    a = (i * cols + k).ravel()
    faces = np.column_stack((a, a + cols, a + cols + 1, a + 1))
    mesh = bpy.data.meshes.new("sleeve")
    mesh.from_pydata(verts.tolist(), [], faces.tolist())
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.materials.append(vinyl("vinyl", False))
    mesh.materials.append(vinyl("weld", True))
    # The seam is the band within WELD of the edge.
    centres = np.array([poly.center for poly in mesh.polygons])
    edge = np.minimum.reduce((centres[:, 0] + OVER, W + OVER - centres[:, 0], -centres[:, 1] + OVER, H + OVER + centres[:, 1]))
    mesh.polygons.foreach_set("material_index", (edge < WELD).astype(int).tolist())
    obj = stage.add("sleeve", mesh)
    thick = obj.modifiers.new("sheet", "SOLIDIFY")
    thick.thickness = 0.02
    thick.offset = -1
    return obj


def face(stage, seed):
    sheet = Sheet(W, H, CREAM, rough=0.8)
    sheet.art(os.path.join(ART, "card.png"), 0, 0, W, H)
    shape = sheet.height.shape
    # Riso ink sits in the tooth of the paper and is never quite even, and a card carried about rubs at its edges.
    sheet.rgb *= (1 + 0.012 * cloud(shape, seed, falloff=1.2))[..., None]
    sheet.height += 0.0006 * cloud(shape, seed + 1, falloff=0.5)
    worn = (1 - ramp(0, 0.35, -sheet.sdf)) * np.clip(0.4 + 0.5 * cloud(shape, seed + 2, falloff=1.4), 0, 1)
    sheet.rgb += (worn * 0.25)[..., None] * (np.array([0.86, 0.8, 0.7]) - sheet.rgb)
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
    shell = sleeve(stage, sheet.z)
    stage.shoot("card", (0, 0, W, H), shadowless=(shell,), lens=False)


SHOTS = {"card": lambda stage: face(stage, 90)}
