"""Real geometry for the things that are not flat: extruded outlines with a bevelled top edge."""

import math
import os

import bmesh
import bpy

from paint import linear
from stage import ASSETS


def principled(name, colour, rough=0.5, metal=0.0, **sockets):
    """A plain Principled material. Extra sockets are named with underscores, for example coat_weight=1."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    rgb = linear(colour) if isinstance(colour, str) else colour
    shader.inputs["Base Color"].default_value = (*rgb, 1)
    shader.inputs["Roughness"].default_value = rough
    shader.inputs["Metallic"].default_value = metal
    for socket, value in sockets.items():
        shader.inputs[socket.replace("_", " ").title().replace("Ior", "IOR")].default_value = value
    return material


def grain(material, scale, depth, stretch=(1, 1, 1)):
    """Fine surface noise as a bump, in object space."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = stretch
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 3
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = depth
    links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs[0], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], nodes["Principled BSDF"].inputs["Normal"])
    return material


def worn(material, asset, size, dull):
    """Handling marks from an ambientCG imperfection map: they dull the surface where they fall."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    socket = nodes["Principled BSDF"].inputs["Roughness"]
    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1 / size, 1 / size, 1 / size)
    marks = nodes.new("ShaderNodeTexImage")
    marks.image = bpy.data.images.load(os.path.join(ASSETS, asset, f"{asset}_1K-JPG_Color.jpg"))
    marks.image.colorspace_settings.name = "Non-Color"
    marks.projection = "BOX"
    added = nodes.new("ShaderNodeMath")
    added.operation = "MULTIPLY_ADD"
    added.inputs[1].default_value = dull
    if socket.is_linked:
        links.new(socket.links[0].from_socket, added.inputs[2])
    else:
        added.inputs[2].default_value = socket.default_value
    links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], marks.inputs["Vector"])
    links.new(marks.outputs["Color"], added.inputs[0])
    links.new(added.outputs[0], socket)
    return material


def scanned(material, asset, size, depth=0.01):
    """Colour, roughness and relief from an ambientCG scan, laid on the object from six sides."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1 / size, 1 / size, 1 / size)
    links.new(coord.outputs["Object"], mapping.inputs["Vector"])

    def tiled(kind, data):
        node = nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(os.path.join(ASSETS, asset, f"{asset}_1K-JPG_{kind}.jpg"))
        if data:
            node.image.colorspace_settings.name = "Non-Color"
        node.projection = "BOX"
        node.projection_blend = 0.3
        links.new(mapping.outputs["Vector"], node.inputs["Vector"])
        return node.outputs["Color"]

    links.new(tiled("Color", False), shader.inputs["Base Color"])
    links.new(tiled("Roughness", True), shader.inputs["Roughness"])
    relief = nodes.new("ShaderNodeBump")
    relief.inputs["Distance"].default_value = depth
    links.new(tiled("Displacement", True), relief.inputs["Height"])
    links.new(relief.outputs["Normal"], shader.inputs["Normal"])
    return material


def rect(x0, y0, x1, y1, r=0.0, steps=8):
    """Outline of a rounded rectangle, in page coordinates."""
    if r <= 0:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    points = []
    for cx, cy, start in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(steps + 1):
            a = math.radians(start + 90 * i / steps)
            points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return points


def fillet(corners, steps=8):
    """Outline of a polygon with rounded corners. Each corner is (x, y, radius)."""
    points = []
    for i, (cx, cy, r) in enumerate(corners):
        if r <= 0:
            points.append((cx, cy))
            continue
        px, py, _ = corners[i - 1]
        nx, ny, _ = corners[(i + 1) % len(corners)]
        ax, ay, bx, by = px - cx, py - cy, nx - cx, ny - cy
        la, lb = math.hypot(ax, ay), math.hypot(bx, by)
        ax, ay, bx, by = ax / la, ay / la, bx / lb, by / lb
        half = math.acos(max(-1, min(1, ax * bx + ay * by))) / 2
        reach = r / math.tan(half)
        mid = math.hypot(ax + bx, ay + by)
        ox, oy = cx + (ax + bx) / mid * r / math.sin(half), cy + (ay + by) / mid * r / math.sin(half)
        a0 = math.atan2(cy + ay * reach - oy, cx + ax * reach - ox)
        a1 = math.atan2(cy + by * reach - oy, cx + bx * reach - ox)
        sweep = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for k in range(steps + 1):
            a = a0 + sweep * k / steps
            points.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    return points


def capsule(ax, ay, bx, by, r, steps=24):
    """Outline of a stadium around the segment from a to b."""
    heading = math.atan2(by - ay, bx - ax)
    points = []
    for cx, cy, start in ((bx, by, heading - math.pi / 2), (ax, ay, heading + math.pi / 2)):
        for k in range(steps + 1):
            a = start + math.pi * k / steps
            points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return points


def spun(material, amount=0.7):
    """Lathe-turned metal: the highlight fans out from the object's centre."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    tangent = nodes.new("ShaderNodeTangent")
    tangent.direction_type = "RADIAL"
    tangent.axis = "Z"
    links.new(tangent.outputs[0], nodes["Principled BSDF"].inputs["Tangent"])
    nodes["Principled BSDF"].inputs["Anisotropic"].default_value = amount
    return material


def ring(cx, cy, r, steps=96):
    return [(cx + r * math.cos(2 * math.pi * i / steps), cy + r * math.sin(2 * math.pi * i / steps)) for i in range(steps)]


def finish(stage, name, bm, material):
    """Smooth shading that still keeps flat faces flat and hard edges hard."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for face in bm.faces:
        face.smooth = True
    for edge in bm.edges:
        if len(edge.link_faces) == 2 and edge.calc_face_angle() > math.radians(40):
            edge.smooth = False
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    if material:
        mesh.materials.append(material)
    obj = stage.add(name, mesh)
    weighted = obj.modifiers.new("normals", "WEIGHTED_NORMAL")
    weighted.keep_sharp = True
    weighted.weight = 100
    return obj


def prism(stage, name, outline, z0, z1, material, bevel=0.0, segments=3, slope=None, centre=None, sides=None):
    """Extrude a page outline from z0 up to z1 and round its top edge.
    slope is (dz/dx, dz/dy) in page axes, for a top face that leans.
    centre moves the object's origin there, which radial finishes need.
    sides is a second material for the walls."""
    ox, oy = centre or (0, 0)
    bm = bmesh.new()
    bottom = [bm.verts.new((x - ox, oy - y, z0)) for x, y in outline]
    top = [bm.verts.new((x - ox, oy - y, z1)) for x, y in outline]
    if slope:
        mx = (min(x for x, _ in outline) + max(x for x, _ in outline)) / 2
        my = (min(y for _, y in outline) + max(y for _, y in outline)) / 2
        for vert, (x, y) in zip(top, outline):
            vert.co.z += slope[0] * (x - mx) + slope[1] * (y - my)
    count = len(outline)
    bm.faces.new(bottom)
    lid = bm.faces.new(top)
    for i in range(count):
        j = (i + 1) % count
        bm.faces.new((bottom[i], bottom[j], top[j], top[i])).material_index = 1 if sides else 0
    if bevel > 0:
        # Bevel reads the face normals, and a mesh built by hand has none until asked.
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.normal_update()
        bmesh.ops.bevel(
            bm, geom=list(lid.edges), offset=bevel, segments=segments, profile=0.5, affect="EDGES", clamp_overlap=False
        )
    obj = finish(stage, name, bm, material)
    if sides:
        obj.data.materials.append(sides)
    obj.location = (ox, -oy, 0)
    return obj


def plate(stage, name, outline, z, material):
    """A flat mark lying on a surface: an engraved line, a printed glyph."""
    bm = bmesh.new()
    bm.faces.new([bm.verts.new((x, -y, z)) for x, y in outline])
    return finish(stage, name, bm, material)


def stroke(ax, ay, bx, by, width):
    """Outline of a straight line of the given width."""
    length = math.hypot(bx - ax, by - ay)
    nx, ny = -(by - ay) / length * width / 2, (bx - ax) / length * width / 2
    return [(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)]


def annulus(stage, name, cx, cy, inner, outer, z, material, steps=128):
    """A flat ring."""
    bm = bmesh.new()
    a = [bm.verts.new((x, -y, z)) for x, y in ring(cx, cy, inner, steps)]
    b = [bm.verts.new((x, -y, z)) for x, y in ring(cx, cy, outer, steps)]
    for i in range(steps):
        j = (i + 1) % steps
        bm.faces.new((a[i], a[j], b[j], b[i]))
    return finish(stage, name, bm, material)


def torus(stage, name, major, minor, material, steps=128, around=20):
    """A wire ring lying flat, centred on the object's origin."""
    bm = bmesh.new()
    loops = []
    for i in range(steps):
        a = 2 * math.pi * i / steps
        loop = []
        for j in range(around):
            b = 2 * math.pi * j / around
            reach = major + minor * math.cos(b)
            loop.append(bm.verts.new((reach * math.cos(a), reach * math.sin(a), minor * math.sin(b))))
        loops.append(loop)
    for i in range(steps):
        for j in range(around):
            a, b = loops[i], loops[(i + 1) % steps]
            bm.faces.new((a[j], b[j], b[(j + 1) % around], a[(j + 1) % around]))
    return finish(stage, name, bm, material)


def lathe(stage, name, profile, material, steps=64, axis="X", caps=True):
    """Spin a profile of (distance along the axis, radius) pairs about the axis.
    axis Y lays it down the page, axis Z stands it up off the mat."""
    bm = bmesh.new()
    rings = []
    for along, radius in profile:
        if radius <= 1e-6:
            rings.append([bm.verts.new((along, 0, 0))])
            continue
        rings.append(
            [
                bm.verts.new((along, radius * math.cos(2 * math.pi * i / steps), radius * math.sin(2 * math.pi * i / steps)))
                for i in range(steps)
            ]
        )
    for a, b in zip(rings, rings[1:]):
        for i in range(steps):
            j = (i + 1) % steps
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                bm.faces.new((a[0], b[i], b[j]))
            elif len(b) == 1:
                bm.faces.new((a[i], b[0], a[j]))
            else:
                bm.faces.new((a[i], b[i], b[j], a[j]))
    for end in (rings[0], rings[-1]):
        if caps and len(end) > 1:
            bm.faces.new(end)
    obj = finish(stage, name, bm, material)
    if axis == "Y":
        obj.rotation_euler = (0, 0, math.radians(-90))
    if axis == "Z":
        obj.rotation_euler = (0, math.radians(-90), 0)
    return obj


def strip_light(stage, name, at, length, width, strength, turn=0.0):
    """A strip softbox over the set: a long glowing panel, feathered across its width, that only reflections
    see. It draws the long highlight down a glossy tube or a chrome bar. at is its centre (x, y, height) in
    scene coordinates and turn its heading."""
    panel = bpy.data.meshes.new(name)
    panel.from_pydata([(-length / 2, -width / 2, 0), (length / 2, -width / 2, 0), (length / 2, width / 2, 0), (-length / 2, width / 2, 0)], [], [(0, 1, 2, 3)])
    panel.uv_layers.new().data.foreach_set("uv", [0, 0, 1, 0, 1, 1, 0, 1])
    light = stage.add(name, panel)
    # The stand takes its own lights away for the shadow pass.
    light["stand"] = "card"
    light.location = at
    light.rotation_euler = (0, 0, turn)
    light.visible_camera = False
    light.visible_shadow = False
    light.visible_diffuse = False
    glow = bpy.data.materials.new(name)
    glow.use_nodes = True
    nodes, links = glow.node_tree.nodes, glow.node_tree.links
    nodes.clear()
    coord = nodes.new("ShaderNodeTexCoord")
    split = nodes.new("ShaderNodeSeparateXYZ")
    across = nodes.new("ShaderNodeMath")
    across.operation = "PINGPONG"
    across.inputs[1].default_value = 0.5
    soft = nodes.new("ShaderNodeMapRange")
    soft.interpolation_type = "SMOOTHSTEP"
    soft.inputs["From Max"].default_value = 0.5
    level = nodes.new("ShaderNodeMath")
    level.operation = "MULTIPLY"
    level.inputs[1].default_value = strength
    emit = nodes.new("ShaderNodeEmission")
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(coord.outputs["UV"], split.inputs[0])
    links.new(split.outputs["Y"], across.inputs[0])
    links.new(across.outputs[0], soft.inputs["Value"])
    links.new(soft.outputs[0], level.inputs[0])
    links.new(level.outputs[0], emit.inputs["Strength"])
    links.new(emit.outputs[0], out.inputs["Surface"])
    panel.materials.append(glow)
    return light
