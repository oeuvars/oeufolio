"""The business card: 3.5 by 2 inches, risograph-printed on heavy uncoated stock. It lies front up, red with
the name in cream, two birds, and a car drawn over a strip of flowers, in a clear polypropylene card
sleeve, sealed on three sides and open at one end. The face is the card's own artwork, art/card.png, rasterised from the print file
(anurag-card-front.svg)."""

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
# The sleeve: how far it runs past the card on its three sealed sides and at its open end, and how wide the
# sealed seam is.
OVER = 0.3
OPEN = 0.16
SEAM = 0.12


def sheet_material(name, seam):
    """Clear polypropylene, as a card sleeve is: water clear and glossy. The sealed seam is the same film
    fused, a touch cloudier. Fingers have left faint marks that dull its gloss. Shadow rays pass through
    almost untouched, as the film is too thin to darken what lies under it."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1)
    shader.inputs["Transmission Weight"].default_value = 1.0
    shader.inputs["IOR"].default_value = 1.49
    base = 0.14 if seam else 0.025
    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1 / 7, 1 / 7, 1)
    marks = nodes.new("ShaderNodeTexImage")
    marks.image = bpy.data.images.load(os.path.join(ASSETS, "Fingerprints009", "Fingerprints009_1K-JPG_Color.jpg"))
    marks.image.colorspace_settings.name = "Non-Color"
    dull = nodes.new("ShaderNodeMath")
    dull.operation = "MULTIPLY_ADD"
    dull.inputs[1].default_value = 0.08
    dull.inputs[2].default_value = base
    links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], marks.inputs["Vector"])
    links.new(marks.outputs["Color"], dull.inputs[0])
    links.new(dull.outputs[0], shader.inputs["Roughness"])
    path = nodes.new("ShaderNodeLightPath")
    clear = nodes.new("ShaderNodeBsdfTransparent")
    clear.inputs["Color"].default_value = (0.97, 0.97, 0.97, 1)
    either = nodes.new("ShaderNodeMixShader")
    links.new(path.outputs["Is Shadow Ray"], either.inputs[0])
    links.new(shader.outputs[0], either.inputs[1])
    links.new(clear.outputs[0], either.inputs[2])
    links.new(either.outputs[0], nodes["Material Output"].inputs["Surface"])
    return material


def sleeve(stage, top, seed):
    """The film over the card. It lies on the card, a hair clear of it, and drops to the mat over the sealed
    edges on three sides. At the open end it stops just past the card and does not quite lie down. Film never
    lies flat: it has a slow wave in it and a few fine crinkles where it has been bent, which is what catches
    the light. top(x, y) is how high the card's face is there."""
    rng = np.random.default_rng(seed)
    step = 0.04
    xs = np.arange(-OVER, W + OPEN + step / 2, step)
    ys = np.arange(-OVER, H + OVER + step / 2, step)
    X, Y = np.meshgrid(xs, ys)
    face = np.vectorize(top)(np.clip(X, 0, W), np.clip(Y, 0, H))
    sealed = np.maximum(np.maximum(-X, -Y), Y - H)
    fall = 1 - ramp(0.0, OVER - SEAM * 0.5, sealed)
    Z = 0.02 + (face + 0.012) * fall
    # The open end lifts a little off the mat where it overhangs.
    Z += 0.03 * ramp(W, W + OPEN, X)
    wave = sum(
        rng.uniform(0.003, 0.008) * np.sin(rng.uniform(0, 6.3) + rng.uniform(0.3, 1.2) * X + rng.uniform(0.3, 1.2) * Y)
        for _ in range(6)
    )
    Z += wave
    # The crinkles: short sharp lines in the film, mostly near its edges, where it has been handled.
    for _ in range(9):
        x0 = rng.uniform(0, W)
        y0 = rng.choice((rng.uniform(0, 1.6), rng.uniform(H - 1.6, H), rng.uniform(0, H)))
        turn = rng.uniform(0, np.pi)
        half = rng.uniform(0.4, 1.4)
        dx, dy = np.cos(turn), np.sin(turn)
        t = np.clip((X - x0) * dx + (Y - y0) * dy, -half, half)
        d = np.hypot(X - x0 - t * dx, Y - y0 - t * dy)
        Z += rng.choice((-1, 1)) * 0.006 * np.exp(-d / 0.05) * (1 - (t / half) ** 2)
    rows, cols = X.shape
    verts = np.column_stack((X.ravel(), -Y.ravel(), Z.ravel()))
    i, k = np.meshgrid(np.arange(rows - 1), np.arange(cols - 1), indexing="ij")
    a = (i * cols + k).ravel()
    faces = np.column_stack((a, a + cols, a + cols + 1, a + 1))
    mesh = bpy.data.meshes.new("sleeve")
    mesh.from_pydata(verts.tolist(), [], faces.tolist())
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.materials.append(sheet_material("film", False))
    mesh.materials.append(sheet_material("seam", True))
    centres = np.array([poly.center for poly in mesh.polygons])
    edge = np.minimum.reduce((centres[:, 0] + OVER, -centres[:, 1] + OVER, H + OVER + centres[:, 1]))
    mesh.polygons.foreach_set("material_index", (edge < SEAM).astype(int).tolist())
    obj = stage.add("sleeve", mesh)
    film = obj.modifiers.new("film", "SOLIDIFY")
    film.thickness = 0.012
    film.offset = -1
    return obj


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
    shell = sleeve(stage, sheet.z, seed + 5)
    # A soft box over the top right of the card, which only reflections see. The film mirrors it as a broad
    # glare, broken up by its waves and crinkles, as an overhead photograph of a sleeved card shows.
    strip_light(stage, "glare", (W * 0.72, -H * 0.3, 30.0), 9.0, 5.0, 1.2, turn=math.radians(-30))
    stage.shoot("card", (0, 0, W, H), shadowless=(shell,), lens=False)


SHOTS = {"card": lambda stage: face(stage, 90)}
