"""Shaving soap in a tube: Proraso's white Pelli Sensibili, with oatmeal and green tea, 150 ml, as the user's own,
used and crumpled, photographed from above (art/proraso-own.jpg). A lacquered aluminium tube lying on its back,
crimped end to the left: flattened and flared toward the crimp, narrowing to the shoulder, its whole length crumpled
into small sharp facets. Its outline is the photograph's, followed down both edges, and so is its print, unrolled
round it with the crumples' own light and glints in it (art/prorasophoto.py). The white shoulder and the ribbed
white cap screwed on its thread are clean. The lacquer is a hard gloss, lit by the room the rest of the desk is in."""

import json
import math
import os

import bmesh
import bpy
import numpy as np

from paint import blur, cloud, ramp
from solids import finish, grain, principled, worn
from stock import Sheet, pixels_of

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art")

# The tube's outline from the photograph: every 0.05 em from the crimped edge, its half width, its depth and how far
# its middle wanders off its axis, in em.
with open(os.path.join(ART, "proraso-shape.json")) as _file:
    SHAPE = json.load(_file)
# The print's width once round (as art/prorasophoto.py lays it out), the length from the crimped edge to the
# shoulder, and the diameter at the shoulder, where the tube is round.
FRONT = math.pi * 5.0 / 2
LENGTH = 22.31
D = 2 * SHAPE["half"][-1]
FOLD = 0.7
# How deep the crumples' relief is pressed into the lacquer, in em.
CRUMPLE = 0.012

BODY = "#e4e4df"
PLASTIC = "#e6e5e0"

# The shoulder domes in from the wall to the neck, and the cap covers the neck from where the dome is this wide.
DOME = 0.62
NECK = 0.72
CAP_R, CAP_H = 0.345 * D, 0.53 * D
RIBS = 84
W, H = 25.5, 7.95


def label():
    """The print, as the photograph unrolls it: once round the tube across, crimp to shoulder down."""
    sheet = Sheet(2 * FRONT, LENGTH, BODY, rough=0.3, density=3)
    Y = sheet.Y
    shape = sheet.height.shape
    sheet.art(os.path.join(ART, "proraso-print.png"), 0, 0, 2 * FRONT, LENGTH)
    rows, cols = shape
    relief = pixels_of(os.path.join(ART, "proraso-relief.png"))[..., 0].astype(np.float64)
    ys = (np.arange(rows) + 0.5) * relief.shape[0] / rows - 0.5
    xs = (np.arange(cols) + 0.5) * relief.shape[1] / cols - 0.5
    y0, x0 = np.clip(ys.astype(int), 0, relief.shape[0] - 1), np.clip(xs.astype(int), 0, relief.shape[1] - 1)
    # Only the creases' dark lines are pressed in, as grooves: the photograph's bright lines are its own glints, which
    # the gloss makes again where the grooves' walls catch the light.
    sheet.height += np.minimum(blur(relief[y0][:, x0], 1.5) - 0.5, 0) * 2 * CRUMPLE

    # The crimp: the end folded over three times and pressed, each fold a step down toward the wall, none of them
    # straight, and the jaws' teeth bitten into it.
    wavy = 0.03 * cloud((1, shape[1]), 2, falloff=1.6) + 0.012 * cloud((1, shape[1]), 12, falloff=0.9)
    folds = ((FOLD, 0.03), (FOLD * 0.68, 0.022), (FOLD * 0.33, 0.02))
    sheet.height += blur(sum(step * sheet.mask(Y - y - wavy * (1 + n)) for n, (y, step) in enumerate(folds)), 2)
    band = sheet.mask(Y - FOLD + 0.06 - wavy) * ramp(0.02, 0.1, Y)
    bitten = np.clip(0.6 + 0.5 * cloud(shape, 13, falloff=1.8), 0, 1) * band
    sheet.press((0.5 + 0.5 * np.cos(2 * np.pi * sheet.X / 0.085)) * bitten, 0.006)

    # The gold is a pale metallic ink, and the green a translucent lacquer over the aluminium: both found by colour.
    r, g, b = sheet.rgb[..., 0], sheet.rgb[..., 1], sheet.rgb[..., 2]
    gilt = np.clip(((r - b) / np.maximum(r, 1e-3) - 0.35) / 0.15, 0, 1) * np.clip((g / np.maximum(r, 1e-3) - 0.6) / 0.1, 0, 1) * np.clip((r - 0.08) / 0.05, 0, 1)
    sheet.finish(gilt, metal=0.35)
    green = np.clip(((g - np.maximum(r, b)) / np.maximum(g, 1e-3) - 0.3) / 0.15, 0, 1)
    sheet.finish(green, metal=0.4)

    # The whole print is under one clear varnish, a little duller in the broad patches where it is held.
    sheet.coat[:] = 0.8
    sheet.finish(np.clip(0.5 + 0.4 * cloud(shape, 7, falloff=2.6), 0, 1), rough=0.26)
    return sheet


def lacquer(sheet, name, wear=()):
    """A material from a painted sheet, to wrap on a mesh by its UV map."""
    rows, cols = sheet.height.shape

    def image(kind, channels):
        img = bpy.data.images.new(f"{name}-{kind}", cols, rows, alpha=True, float_buffer=True)
        img.colorspace_settings.name = "Non-Color"
        img.alpha_mode = "CHANNEL_PACKED"
        img.pixels.foreach_set(np.dstack(channels)[::-1].astype(np.float32).ravel())
        img.pack()
        node = nodes.new("ShaderNodeTexImage")
        node.image = img
        node.interpolation = "Cubic"
        return node

    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    inked = image("colour", (sheet.rgb[..., 0], sheet.rgb[..., 1], sheet.rgb[..., 2], np.ones((rows, cols))))
    packed = image("data", (sheet.height, sheet.rough, sheet.metal, sheet.coat))
    split = nodes.new("ShaderNodeSeparateColor")
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 1.0
    links.new(packed.outputs["Color"], split.inputs["Color"])
    links.new(split.outputs["Red"], bump.inputs["Height"])
    links.new(inked.outputs["Color"], shader.inputs["Base Color"])
    links.new(split.outputs["Green"], shader.inputs["Roughness"])
    links.new(split.outputs["Blue"], shader.inputs["Metallic"])
    links.new(packed.outputs["Alpha"], shader.inputs["Coat Weight"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(bump.outputs["Normal"], shader.inputs["Coat Normal"])
    # The shine is the varnish's alone: a hard gloss, which finger marks dull a little.
    shader.inputs["Specular IOR Level"].default_value = 0.1
    for asset, size, dull in wear:
        worn(material, asset, size, dull)
    varnish = nodes.new("ShaderNodeMath")
    varnish.operation = "MULTIPLY"
    varnish.inputs[1].default_value = 0.3
    links.new(shader.inputs["Roughness"].links[0].from_socket, varnish.inputs[0])
    links.new(varnish.outputs[0], shader.inputs["Coat Roughness"])
    return material


def body(stage, material):
    """The wall of the tube: every section an oval as wide as the photograph shows the tube there and as deep as
    the shape has it, its middle where the photograph's is."""
    rings, steps = 960, 480
    along = np.linspace(0, LENGTH, rings)
    a = np.interp(along, SHAPE["along"], SHAPE["half"])
    b = np.maximum(np.interp(along, SHAPE["along"], SHAPE["deep"]), 0.11)
    off = np.interp(along, SHAPE["along"], SHAPE["off"])

    # Points evenly spaced round each oval, as the print was unrolled.
    phi = np.linspace(-np.pi, np.pi, 4097)
    turn = np.empty((rings, steps))
    share = np.arange(steps) / steps
    for i in range(rings):
        ds = np.hypot(a[i] * np.cos(phi), b[i] * np.sin(phi))
        s = np.concatenate(([0], np.cumsum((ds[1:] + ds[:-1]) / 2)))
        turn[i] = np.interp(share * s[-1], s, phi)
    y, z = a[:, None] * np.sin(turn) + off[:, None], b[:, None] * np.cos(turn)

    # It lies on the mat. The crimped end has a wave in it, its edge is not cut quite straight, and one corner has
    # been bent a little up off the mat.
    x = np.broadcast_to(along[:, None], (rings, steps))
    round_ = (share[None, :] - 0.5) * 2 * FRONT
    z = np.maximum(z + b[:, None], 0.0) + 0.045 * (1 + np.sin(0.8 + 1.25 * round_)) * (1 - ramp(0, 3.0, x))
    z = z + 0.2 * np.clip(1 - np.hypot(x, y - a[0]) / 1.5, 0, 1) ** 2
    x = x + 0.05 * np.sin(0.6 + 0.9 * round_) * (1 - ramp(0, 1.4, x))

    verts = np.column_stack((x.ravel(), y.ravel(), z.ravel()))
    i, k = np.meshgrid(np.arange(rings - 1), np.arange(steps), indexing="ij")
    i, k = i.ravel(), k.ravel()
    near, far = k, (k + 1) % steps
    faces = np.column_stack((i * steps + near, (i + 1) * steps + near, (i + 1) * steps + far, i * steps + far))
    mesh = bpy.data.meshes.new("tube")
    mesh.from_pydata(verts.tolist(), [], faces.tolist() + [list(range(steps))])
    u = np.column_stack((k, k, k + 1, k + 1)) / steps
    v = 1 - np.column_stack((i, i + 1, i + 1, i)) / (rings - 1)
    uv = np.concatenate((np.dstack((u, v)).ravel(), np.tile((0.5, 1.0), steps)))
    mesh.uv_layers.new().data.foreach_set("uv", uv)
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.materials.append(material)
    return stage.add("tube", mesh)


def turned(stage, name, rings, material, steps, wave=None):
    """Spin rings of (height, radius, part) about the object's z axis. wave(part, height, angles) is added to
    the radius of the rings that name a part, for ribs and threads. A ring of no radius closes to a point."""
    bm = bmesh.new()
    angles = np.arange(steps) * 2 * np.pi / steps
    loops = []
    for height, radius, part in rings:
        if radius <= 1e-6:
            loops.append([bm.verts.new((0, 0, height))])
            continue
        r = radius + (wave(part, height, angles) if part else np.zeros(steps))
        loops.append([bm.verts.new((r[j] * math.cos(angles[j]), r[j] * math.sin(angles[j]), height)) for j in range(steps)])
    for lower, upper in zip(loops, loops[1:]):
        for j in range(steps):
            n = (j + 1) % steps
            if len(lower) == 1 and len(upper) == 1:
                continue
            if len(lower) == 1:
                bm.faces.new((lower[0], upper[j], upper[n]))
            elif len(upper) == 1:
                bm.faces.new((lower[j], upper[0], lower[n]))
            else:
                bm.faces.new((lower[j], upper[j], upper[n], lower[n]))
    return finish(stage, name, bm, material)


def shoulder(stage, enamel):
    """The stiff end of the tube: a dome in white enamel from the wall in to the neck."""
    r = D / 2
    k = r - CAP_R
    dome = [(-0.3, r - 0.04 * k), (0.0, r - 0.006 * k), (0.05, r - 0.03 * k), (0.14, r - 0.11 * k), (0.3, r - 0.38 * k), (0.45, r - 0.7 * k), (DOME, CAP_R + 0.02), (DOME + 0.12, CAP_R - 0.3), (DOME + 0.2, NECK), (DOME + 0.5, NECK)]
    part = turned(stage, "shoulder", [(h, radius, None) for h, radius in dome], enamel, 160)
    part.rotation_euler = (0, math.radians(90), 0)
    part.location = (LENGTH, 0, r)
    return part


def cap(stage, plastic):
    """The screw cap on its thread: a straight ribbed wall, a hair narrower toward its closed end, and a
    flat end with a tight round on its edge. It turns about its own z axis, open end down."""
    def wall(h):
        return CAP_R * (1 - 0.03 * h / CAP_H)

    rings = [(0.0, CAP_R - 0.22, None), (0.0, CAP_R - 0.07, None), (0.03, CAP_R - 0.02, None), (0.07, CAP_R, "ribs")]
    rings += [(h, wall(h), "ribs") for h in np.linspace(0.12, CAP_H - 0.12, 14)]
    rings += [(CAP_H - 0.05, wall(CAP_H) - 0.02, "ribs"), (CAP_H - 0.015, wall(CAP_H) - 0.05, None), (CAP_H, wall(CAP_H) - 0.1, None), (CAP_H, 0, None)]

    def ribs(part, height, angles):
        return -0.075 * (0.5 - 0.5 * np.cos(RIBS * angles)) ** 0.7 * ramp(0.05, 0.12, height)

    return turned(stage, "cap", rings, plastic, RIBS * 6, ribs)


def proraso(stage):
    paint = lacquer(label(), "lacquer", wear=(("Fingerprints009", 7, 0.05),))
    enamel = worn(principled("enamel", "#e2e2de", rough=0.28), "SurfaceImperfections003", 3, 0.15)
    plastic = worn(grain(principled("cap", PLASTIC, rough=0.4), 320, 0.0015), "SurfaceImperfections003", 3, 0.12)

    root = stage.add("proraso", None)
    root.location = (0.04, -H / 2, 0)
    lid = cap(stage, plastic)
    lid.rotation_mode = "ZYX"
    lid.rotation_euler = (0, math.radians(90), math.radians(23))
    lid.location = (LENGTH + DOME - 0.03, SHAPE["off"][-1], D / 2)
    tube_end = shoulder(stage, enamel)
    tube_end.location.y = SHAPE["off"][-1]
    for part in (body(stage, paint), tube_end, lid):
        part.parent = root

    stage.shoot("proraso", (0, 0, W, H), bleed=1.0, shadow=1.2)


SHOTS = {"proraso": proraso}
