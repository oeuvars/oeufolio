"""The picture on the ticket, before it is cut into a block: a wet street in Kolkata in the rain, a tram
coming down it toward us, and at its end the towers of Howrah Bridge standing up out of the haze. Someone
under a black umbrella walks away from us at the side of the road. Run from the repository root:

    blender -b --factory-startup -P studio/ticket/street.py -- [--size 1400] [--samples 96]

Writes studio/ticket/art/street.exr, a multilayer EXR with the light, the haze, the normals, the depth and
which kind of thing each pixel is. studio/ticket/engrave.py cuts that into one ink.

Metres, x across the street, y down it away from the camera, z up. The traffic keeps left, so the tram
coming toward us is on the right of the road.
"""

import argparse
import json
import math
import os
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "art", "street.exr")

# What each kind of thing is, in the object index pass. engrave.py cuts each its own way.
KIND = {"facade": 1, "dark": 2, "road": 3, "tram": 4, "bridge": 5, "figure": 6, "wire": 7, "trim": 8, "glass": 9, "pavement": 10}

ROAD = 7.0  # half the width of the carriageway
WALK = 2.6  # the pavement's width
FLOOR = 3.6
STOREY_COUNTS = (3, 4, 4, 3, 5, 4, 3, 4, 4, 3, 4, 5, 3, 4)


class Parts:
    """Boxes and beams gathered into one mesh, for one material."""

    def __init__(self):
        self.verts, self.faces = [], []

    def box(self, x0, x1, y0, y1, z0, z1):
        n = len(self.verts)
        self.verts += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        self.faces += [(n, n + 3, n + 2, n + 1), (n + 4, n + 5, n + 6, n + 7), (n, n + 1, n + 5, n + 4), (n + 1, n + 2, n + 6, n + 5), (n + 2, n + 3, n + 7, n + 6), (n + 3, n, n + 4, n + 7)]

    def beam(self, a, b, w, d=None):
        """A square beam from a to b, w across and d deep."""
        a, b = Vector(a), Vector(b)
        axis = (b - a).normalized()
        side = axis.cross(Vector((0, 0, 1)) if abs(axis.z) < 0.95 else Vector((1, 0, 0))).normalized()
        up = side.cross(axis).normalized()
        d = w if d is None else d
        n = len(self.verts)
        for end in (a, b):
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                self.verts.append(tuple(end + side * (sx * w / 2) + up * (sy * d / 2)))
        self.faces += [(n, n + 1, n + 2, n + 3), (n + 7, n + 6, n + 5, n + 4)]
        for i in range(4):
            j = (i + 1) % 4
            self.faces.append((n + i, n + 4 + i, n + 4 + j, n + j))

    def build(self, name, material, kind):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.verts, [], self.faces)
        mesh.validate()
        mesh.materials.append(material)
        obj = bpy.data.objects.new(name, mesh)
        obj.pass_index = KIND[kind]
        bpy.context.scene.collection.objects.link(obj)
        return obj


def material(name, colour, rough=0.8, metal=0.0, emit=0.0, noise=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*colour, 1)
    shader.inputs["Roughness"].default_value = rough
    shader.inputs["Metallic"].default_value = metal
    if emit:
        shader.inputs["Emission Color"].default_value = (*colour, 1)
        shader.inputs["Emission Strength"].default_value = emit
    if noise:
        # Weathered plaster: patches of damp darken it.
        coord = nodes.new("ShaderNodeTexCoord")
        tex = nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = 0.35
        tex.inputs["Detail"].default_value = 6
        links.new(coord.outputs["Object"], tex.inputs["Vector"])
        ramp = nodes.new("ShaderNodeMapRange")
        ramp.inputs["From Min"].default_value = 0.35
        ramp.inputs["From Max"].default_value = 0.75
        ramp.inputs["To Min"].default_value = 1.0 - noise
        ramp.inputs["To Max"].default_value = 1.0
        links.new(tex.outputs["Fac"], ramp.inputs["Value"])
        mix = nodes.new("ShaderNodeVectorMath")
        mix.operation = "SCALE"
        mix.inputs[0].default_value = colour
        links.new(ramp.outputs["Result"], mix.inputs["Scale"])
        links.new(mix.outputs[0], shader.inputs["Base Color"])
    return mat


def road_material():
    """Wet asphalt: dark, and glassy where water stands in it."""
    mat = bpy.data.materials.new("road")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0.035, 0.035, 0.037, 1)
    coord = nodes.new("ShaderNodeTexCoord")
    puddles = nodes.new("ShaderNodeTexNoise")
    puddles.inputs["Scale"].default_value = 0.09
    puddles.inputs["Detail"].default_value = 5
    links.new(coord.outputs["Object"], puddles.inputs["Vector"])
    wet = nodes.new("ShaderNodeMapRange")
    wet.inputs["From Min"].default_value = 0.42
    wet.inputs["From Max"].default_value = 0.56
    wet.inputs["To Min"].default_value = 0.55
    wet.inputs["To Max"].default_value = 0.02
    links.new(puddles.outputs["Fac"], wet.inputs["Value"])
    links.new(wet.outputs["Result"], shader.inputs["Roughness"])
    # Rain falling into the puddles breaks their mirror into rings.
    rings = nodes.new("ShaderNodeTexVoronoi")
    rings.inputs["Scale"].default_value = 3.0
    links.new(coord.outputs["Object"], rings.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    links.new(rings.outputs["Distance"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return mat


def building(side, y0, y1, storeys, seed, parts):
    """One house on the street: plaster, a cornice at every floor, shuttered windows, a balcony or two,
    a shop on the ground floor with its shutter half down, and a parapet. side is -1 for the left of the
    street and 1 for the right."""
    facade = parts[("facade", "plaster-warm", "plaster-pale")[seed % 3]]
    dark, trim, glass = parts["dark"], parts["trim"], parts["glass"]
    face = side * (ROAD + WALK)
    setback = ((seed * 37) % 5) * 0.12
    face += side * setback
    height = storeys * FLOOR + 1.2
    deep = face + side * 12
    lo, hi = sorted((face, deep))
    facade.box(lo, hi, y0, y1, 0, height)

    def out(d):
        """A depth measured out from the facade toward the street, as an x range."""
        return sorted((face, face - side * d))

    # A cornice at each floor and a heavier one under the parapet.
    for f in range(1, storeys + 1):
        z = f * FLOOR
        a, b = out(0.32 if f < storeys else 0.55)
        trim.box(a, b, y0 - 0.15, y1 + 0.15, z - 0.12, z + 0.16)
    # The parapet, with its rail of short pillars.
    a, b = out(0.2)
    trim.box(a, b, y0, y1, height - 0.05, height + 0.12)
    trim.box(a, b, y0, y1, height + 0.85, height + 1.0)
    y = y0 + 0.4
    while y < y1 - 0.4:
        trim.box(a, b, y, y + 0.14, height + 0.12, height + 0.85)
        y += 0.42

    # Windows: tall and narrow, with louvred shutters folded back either side and the room dark behind.
    width = y1 - y0
    count = max(2, int(width / 2.3))
    pitch = width / count
    for f in range(1, storeys):
        z = f * FLOOR + 0.7
        balcony = (seed + f) % 3 == 0
        for i in range(count):
            cy = y0 + pitch * (i + 0.5)
            w, h = 0.95, 2.1
            a, b = out(0.03)
            dark.box(a, b, cy - w / 2, cy + w / 2, z, z + h)
            # The frame round it, and the arch-like hood over it.
            a, b = out(0.12)
            trim.box(a, b, cy - w / 2 - 0.12, cy + w / 2 + 0.12, z + h, z + h + 0.18)
            trim.box(a, b, cy - w / 2 - 0.16, cy + w / 2 + 0.16, z - 0.14, z)
            # Shutters: open on some windows, shut on others.
            shut = (seed * 7 + f * 3 + i * 5) % 4 == 0
            leaves = ((cy - w / 2, cy), (cy, cy + w / 2)) if shut else ((cy - w / 2 - 0.5, cy - w / 2), (cy + w / 2, cy + w / 2 + 0.5))
            for s0, s1 in leaves:
                a, b = out(0.07 if shut else 0.05)
                glass.box(a, b, s0 + 0.02, s1 - 0.02, z, z + h)
                # Louvres: thin slats across each leaf.
                a, b = out(0.1 if shut else 0.08)
                slat = z + 0.12
                while slat < z + h - 0.1:
                    trim.box(a, b, s0 + 0.05, s1 - 0.05, slat, slat + 0.035)
                    slat += 0.11
        if balcony:
            # A slab on brackets and a cast-iron rail of close balusters.
            a, b = out(1.05)
            trim.box(a, b, y0 + 0.3, y1 - 0.3, z - 0.32, z - 0.18)
            edge = face - side * 1.0
            trim.box(min(edge, edge - side * 0.05), max(edge, edge - side * 0.05), y0 + 0.3, y1 - 0.3, z + 0.82, z + 0.9)
            yb = y0 + 0.35
            while yb < y1 - 0.35:
                trim.box(min(edge, edge - side * 0.03), max(edge, edge - side * 0.03), yb, yb + 0.03, z - 0.18, z + 0.82)
                yb += 0.13

    # The shop: an opening, its shutter partly rolled down, a sign board over it, an awning on some.
    for i in range(max(1, int(width / 4.5))):
        span = width / max(1, int(width / 4.5))
        sy0, sy1 = y0 + span * i + 0.3, y0 + span * (i + 1) - 0.3
        a, b = out(0.02)
        dark.box(a, b, sy0, sy1, 0.2, 2.9)
        down = 0.6 + ((seed + i) % 3) * 0.5
        a, b = out(0.06)
        z = 2.9
        while z > 2.9 - down:
            glass.box(a, b, sy0, sy1, z - 0.07, z)
            z -= 0.09
        a, b = out(0.15)
        glass.box(a, b, sy0 - 0.1, sy1 + 0.1, 3.0, 3.5)
        if (seed + i) % 2 == 0:
            # A canvas awning, sloping out over the pavement.
            n = len(parts["trim"].verts)
            outer = face - side * 1.6
            parts["trim"].verts += [(face, sy0, 3.55), (face, sy1, 3.55), (outer, sy1, 3.0), (outer, sy0, 3.0)]
            parts["trim"].faces += [(n, n + 1, n + 2, n + 3)]


def tram(parts, at_y, x):
    """A Kolkata tram: two cars, square and upright, a cab at each end with three big panes, the route
    board over them, a single lamp, the roof's rain strips, and the trolley pole up to the wire."""
    body, dark, trim, glass = parts["tram"], parts["dark"], parts["trim"], parts["glass"]
    half = 1.12
    for car in range(2):
        y0 = at_y + car * 11.0
        y1 = y0 + 10.4
        # Lower body, window band, letterboard and roof.
        body.box(x - half, x + half, y0, y1, 0.55, 1.6)
        body.box(x - half, x + half, y0, y1, 2.45, 2.8)
        trim.box(x - half - 0.02, x + half + 0.02, y0, y1, 1.6, 1.68)
        trim.box(x - half + 0.08, x + half - 0.08, y0 + 0.1, y1 - 0.1, 2.8, 3.0)
        trim.box(x - half + 0.3, x + half - 0.3, y0 + 0.4, y1 - 0.4, 3.0, 3.07)
        # Side windows, with the pillars between.
        n = 7
        for i in range(n + 1):
            py = y0 + 0.3 + i * (10.4 - 0.6) / n
            for s in (-1, 1):
                body.box(x + s * half - 0.04, x + s * half + 0.04, py - 0.09, py + 0.09, 1.68, 2.45)
        for s in (-1, 1):
            glass.box(x + s * (half - 0.02) - 0.03, x + s * (half - 0.02) + 0.03, y0 + 0.3, y1 - 0.3, 1.68, 2.45)
        # The skirt and wheels in shadow beneath.
        dark.box(x - half + 0.15, x + half - 0.15, y0 + 0.5, y1 - 0.5, 0.12, 0.55)
        # The cab end facing us.
        if car == 0:
            f = y0
            body.box(x - half, x + half, f - 0.05, f + 0.01, 0.55, 1.6)
            for i, (a, b) in enumerate(((-half + 0.08, -0.38), (-0.3, 0.3), (0.38, half - 0.08))):
                glass.box(x + a, x + b, f - 0.07, f - 0.02, 1.7, 2.42)
            body.box(x - half, x + half, f - 0.06, f, 1.6, 1.7)
            body.box(x - half, x + half, f - 0.06, f, 2.42, 2.8)
            # Route board, white, framed.
            trim.box(x - 0.7, x + 0.7, f - 0.1, f - 0.05, 2.5, 2.74)
            # Bumper and lamp.
            trim.box(x - half - 0.05, x + half + 0.05, f - 0.25, f - 0.05, 0.55, 0.72)
            parts["lamp"].box(x - 0.13, x + 0.13, f - 0.12, f - 0.06, 1.05, 1.31)
    # The gangway between the cars.
    dark.box(x - 0.6, x + 0.6, at_y + 10.4, at_y + 11.0, 0.6, 2.6)
    # Trolley pole: from the roof of the back car, leaning forward up to the wire over this track.
    base = Vector((x, at_y + 15.0, 3.07))
    head = Vector((x, at_y + 9.0, 6.2))
    parts["wire"].beam(base, head, 0.06)
    parts["wire"].box(x - 0.18, x + 0.18, at_y + 14.6, at_y + 15.4, 3.07, 3.25)


def figure(parts, x, y):
    """Someone walking away from us under a black umbrella, in a dark coat, one heel lifted."""
    coat, umbrella = parts["figure"], parts["umbrella"]
    # Legs, one forward, one back with the heel up.
    coat.beam((x - 0.09, y + 0.12, 0.05), (x - 0.08, y, 0.88), 0.13)
    coat.beam((x + 0.09, y - 0.18, 0.12), (x + 0.08, y, 0.88), 0.13)
    coat.box(x - 0.15, x - 0.02, y + 0.06, y + 0.3, 0.0, 0.08)
    coat.beam((x + 0.05, y - 0.32, 0.04), (x + 0.15, y - 0.12, 0.13), 0.1)
    # The coat: a tapered block from hem to shoulders.
    rings = [(0.6, 0.27, 0.19), (0.9, 0.23, 0.16), (1.18, 0.2, 0.13), (1.36, 0.24, 0.14), (1.47, 0.21, 0.12), (1.53, 0.09, 0.08)]
    n = len(coat.verts)
    sides = 12
    for z, rx, ry in rings:
        for k in range(sides):
            a = 2 * math.pi * k / sides
            coat.verts.append((x + rx * math.cos(a), y + ry * math.sin(a), z))
    for r in range(len(rings) - 1):
        for k in range(sides):
            j = (k + 1) % sides
            coat.faces.append((n + r * sides + k, n + r * sides + j, n + (r + 1) * sides + j, n + (r + 1) * sides + k))
    coat.faces.append(tuple(n + (len(rings) - 1) * sides + k for k in range(sides)))
    coat.faces.append(tuple(n + k for k in reversed(range(sides))))
    # Head, and the arm up to the handle.
    head = len(coat.verts)
    coat.verts.append((x, y, 1.79))
    for r in range(1, 6):
        polar = math.pi * r / 6
        for k in range(sides):
            a = 2 * math.pi * k / sides
            coat.verts.append((x + 0.1 * math.sin(polar) * math.cos(a), y + 0.11 * math.sin(polar) * math.sin(a), 1.67 + 0.12 * math.cos(polar)))
    coat.verts.append((x, y, 1.55))
    for k in range(sides):
        j = (k + 1) % sides
        coat.faces.append((head, head + 1 + j, head + 1 + k))
        for r in range(4):
            a0, b0 = head + 1 + r * sides, head + 1 + (r + 1) * sides
            coat.faces.append((a0 + k, a0 + j, b0 + j, b0 + k))
        coat.faces.append((head + 1 + 4 * sides + k, head + 1 + 4 * sides + j, head + 1 + 5 * sides))
    coat.beam((x + 0.2, y, 1.42), (x + 0.12, y - 0.12, 1.25), 0.09)
    coat.beam((x + 0.12, y - 0.12, 1.25), (x + 0.03, y - 0.08, 1.5), 0.08)
    # The umbrella: eight panels between ribs, each sagging between them, scalloped at the rim.
    apex = Vector((x + 0.02, y - 0.05, 2.12))
    ribs = 8
    radius = 0.62
    n = len(umbrella.verts)
    umbrella.verts.append(tuple(apex))
    steps = 5
    for k in range(ribs * steps):
        a = 2 * math.pi * k / (ribs * steps)
        t = (k % steps) / steps
        sag = math.sin(math.pi * t)
        r = radius * (1 - 0.06 * sag)
        z = 1.82 + 0.05 * sag
        umbrella.verts.append((apex.x + r * math.cos(a), apex.y + r * math.sin(a), z))
    for k in range(ribs * steps):
        j = (k + 1) % (ribs * steps)
        umbrella.faces.append((n, n + 1 + k, n + 1 + j))
    umbrella.beam((apex.x, apex.y, 2.22), (apex.x, apex.y, 1.35), 0.025)
    # Rib tips.
    for k in range(ribs):
        a = 2 * math.pi * k / ribs
        tip = (apex.x + radius * 1.02 * math.cos(a), apex.y + radius * 1.02 * math.sin(a), 1.8)
        umbrella.beam(tip, (tip[0], tip[1], tip[2] - 0.05), 0.02)


def bridge(parts, y):
    """Howrah Bridge, seen from its approach: the two towers of the cantilever, lattice from foot to head,
    the portal braced across between them overhead, and the arms running back from their heads."""
    steel = parts["bridge"]
    gap = 12.0  # half the distance between the two trusses
    deck = 9.0
    top = 82.0
    w = 1.3
    for s in (-1, 1):
        # Each tower is four chords, leaning in a little, laced on the face toward us.
        foot, head = 3.6, 2.2
        for dx in (-1, 1):
            for dy in (-1, 1):
                a = (s * gap + dx * foot, y + dy * foot, 0)
                b = (s * gap + dx * head, y + dy * head, top)
                steel.beam(a, b, w)
        z = 0.0
        step = 6.5
        while z < top - 1:
            k0, k1 = z / top, min(z + step, top) / top
            h0 = foot + (head - foot) * k0
            h1 = foot + (head - foot) * k1
            for face_y in (-1, 1):
                fy = y + face_y * h0
                steel.beam((s * gap - h0, fy, z), (s * gap + h1, y + face_y * h1, z + step), 0.45)
                steel.beam((s * gap + h0, fy, z), (s * gap - h1, y + face_y * h1, z + step), 0.45)
                steel.beam((s * gap - h1, y + face_y * h1, z + step), (s * gap + h1, y + face_y * h1, z + step), 0.5)
            z += step
        # The cap on each tower.
        steel.box(s * gap - head - 0.6, s * gap + head + 0.6, y - head - 0.6, y + head + 0.6, top, top + 2.2)
        steel.beam((s * gap - head, y, top + 2.2), (s * gap, y, top + 6.5), 0.5)
        steel.beam((s * gap + head, y, top + 2.2), (s * gap, y, top + 6.5), 0.5)
        # The arms: top chord running back over the anchor span and forward over the river, down to the deck
        # ends, laced in big triangles.
        for direction in (-1, 1):
            end_y = y + direction * 140
            steel.beam((s * gap, y, top), (s * gap, end_y, 30), 1.1)
            steel.beam((s * gap, y, deck), (s * gap, end_y, deck), 1.1)
            for k in range(1, 9):
                py = y + direction * 140 * k / 9
                pz = top + (30 - top) * k / 9
                steel.beam((s * gap, py, deck), (s * gap, py, pz), 0.5)
                qy = y + direction * 140 * (k - 1) / 9
                qz = top + (30 - top) * (k - 1) / 9
                steel.beam((s * gap, py, deck), (s * gap, qy, qz), 0.45)
    # The portal overhead: two deep girders across, with a lattice between.
    for z0, z1 in ((60.0, 78.0), (34.0, 40.0)):
        steel.beam((-gap, y - 1.8, z0), (gap, y - 1.8, z0), 1.0)
        steel.beam((-gap, y - 1.8, z1), (gap, y - 1.8, z1), 1.0)
        n = 6
        for k in range(n):
            xa, xb = -gap + 2 * gap * k / n, -gap + 2 * gap * (k + 1) / n
            steel.beam((xa, y - 1.8, z0), (xb, y - 1.8, z1), 0.42)
            steel.beam((xa, y - 1.8, z1), (xb, y - 1.8, z0), 0.42)
    # The deck and its railings running away across the river.
    steel.box(-gap - 1, gap + 1, y - 10, y + 300, deck - 0.8, deck)


def wires(parts):
    """The overhead line over each track, the spans that carry it from the houses, and the tangle of
    cables Kolkata strings between its poles."""
    cable = parts["wire"]
    for x in (-1.9, 1.9):
        cable.beam((x, -10, 6.2), (x, 260, 6.2), 0.035)
    y = 6.0
    while y < 240:
        cable.beam((-(ROAD + WALK), y, 7.4), (ROAD + WALK, y, 7.4), 0.03)
        for x in (-1.9, 1.9):
            cable.beam((x, y, 7.4), (x, y, 6.2), 0.02)
        y += 26.0
    # Poles on the pavement edge, with cables slung between them, each one sagging.
    for side in (-1, 1):
        y = 3.0 + (2.0 if side > 0 else 0)
        while y < 200:
            px = side * (ROAD + 0.4)
            cable.beam((px, y, 0), (px, y, 8.5), 0.18)
            cable.beam((px, y, 7.9), (px - side * 0.8, y, 7.9), 0.08)
            y += 22.0
    for k in range(10):
        side = 1 if k % 2 else -1
        ya = 4 + k * 9.0
        yb = ya + 22.0
        za, zb = 7.4 + (k % 3) * 0.3, 7.6 + (k % 2) * 0.4
        sag = 0.6 + (k % 4) * 0.25
        steps = 10
        prev = None
        for i in range(steps + 1):
            t = i / steps
            p = (side * (ROAD + 0.4), ya + (yb - ya) * t, za + (zb - za) * t - sag * 4 * t * (1 - t))
            if prev:
                cable.beam(prev, p, 0.03)
            prev = p
        # A few cross the street.
        if k % 3 == 0:
            prev = None
            for i in range(steps + 1):
                t = i / steps
                p = (-(ROAD + 0.4) + 2 * (ROAD + 0.4) * t, ya + 2 * t, 7.6 - 1.1 * 4 * t * (1 - t))
                if prev:
                    cable.beam(prev, p, 0.03)
                prev = p


def ground(parts):
    road = parts["road"]
    road.box(-ROAD, ROAD, -20, 300, -0.1, 0)
    for side in (-1, 1):
        lo, hi = sorted((side * ROAD, side * (ROAD + WALK + 1)))
        parts["pavement"].box(lo, hi, -20, 300, -0.1, 0.16)
        a, b = sorted((side * ROAD, side * (ROAD + 0.22)))
        parts["trim"].box(a, b, -20, 300, 0, 0.17)
    # The tram rails: two steel strips per track, let into the road.
    for x in (-1.9, 1.9):
        for g in (-0.72, 0.72):
            parts["rail"].box(x + g - 0.04, x + g + 0.04, -20, 300, 0, 0.012)


def street(parts):
    for side in (-1, 1):
        y = -24.0 + (3.5 if side > 0 else 0)
        k = 0 if side < 0 else 5
        while y < 205:
            width = 7.5 + ((k * 13) % 7)
            storeys = STOREY_COUNTS[k % len(STOREY_COUNTS)]
            building(side, y, y + width, storeys, k, parts)
            y += width
            if k % 6 == 5:
                y += 6.0  # a lane between houses
            k += 1


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=1400)
    parser.add_argument("--samples", type=int, default=96)
    args = parser.parse_args(argv)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for device in prefs.devices:
        device.use = device.type == "METAL"
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "GPU"
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    scene.cycles.use_auto_tile = True
    scene.cycles.tile_size = 1024
    scene.render.resolution_x = scene.render.resolution_y = args.size
    scene.view_settings.view_transform = "Standard"
    layer = scene.view_layers[0]
    layer.use_pass_mist = True
    layer.use_pass_normal = True
    layer.use_pass_object_index = True
    layer.use_pass_z = True
    scene.render.image_settings.media_type = "MULTI_LAYER_IMAGE"
    scene.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"
    scene.render.image_settings.color_depth = "32"

    # An overcast sky, brighter overhead, and haze that swallows the far end of the street.
    world = bpy.data.worlds.new("sky")
    world.use_nodes = True
    scene.world = world
    nodes, links = world.node_tree.nodes, world.node_tree.links
    sky = nodes.new("ShaderNodeTexGradient")
    coord = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coord.outputs["Generated"], sep.inputs["Vector"])
    ramp = nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 0.0
    ramp.inputs["From Max"].default_value = 1.0
    ramp.inputs["To Min"].default_value = 0.6
    ramp.inputs["To Max"].default_value = 1.4
    links.new(sep.outputs["Z"], ramp.inputs["Value"])
    links.new(ramp.outputs["Result"], nodes["Background"].inputs["Strength"])
    nodes["Background"].inputs["Color"].default_value = (0.82, 0.84, 0.86, 1)
    del sky
    world.mist_settings.start = 12
    world.mist_settings.depth = 260
    world.mist_settings.falloff = "QUADRATIC"
    # A low, weak sun behind the bridge, so its lattice reads against the brighter sky.
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 0.6
    sun.angle = math.radians(12)
    lamp = bpy.data.objects.new("sun", sun)
    lamp.rotation_euler = (math.radians(70), 0, math.radians(160))
    scene.collection.objects.link(lamp)

    mats = {
        "facade": material("plaster", (0.62, 0.58, 0.5), 0.9, noise=0.35),
        "plaster-warm": material("plaster-warm", (0.5, 0.4, 0.3), 0.9, noise=0.4),
        "plaster-pale": material("plaster-pale", (0.75, 0.73, 0.68), 0.9, noise=0.3),
        "dark": material("dark", (0.01, 0.01, 0.01), 0.9),
        "trim": material("trim", (0.72, 0.7, 0.64), 0.8),
        "glass": material("shutter", (0.12, 0.16, 0.13), 0.5),
        "road": road_material(),
        "pavement": material("pavement", (0.2, 0.2, 0.19), 0.35),
        "rail": material("rail", (0.5, 0.5, 0.5), 0.45, metal=1.0),
        "tram": material("tram", (0.1, 0.18, 0.4), 0.35),
        "lamp": material("lamp", (1.0, 0.92, 0.75), 0.3, emit=25.0),
        "bridge": material("steel", (0.25, 0.25, 0.25), 0.7),
        "wire": material("wire", (0.02, 0.02, 0.02), 0.6),
        "figure": material("coat", (0.02, 0.02, 0.022), 0.85),
        "umbrella": material("umbrella", (0.01, 0.01, 0.012), 0.85),
    }
    kinds = {"facade": "facade", "plaster-warm": "facade", "plaster-pale": "facade", "dark": "dark", "trim": "trim", "glass": "glass", "road": "road", "pavement": "pavement", "rail": "road", "tram": "tram", "lamp": "trim", "bridge": "bridge", "wire": "wire", "figure": "figure", "umbrella": "figure"}
    parts = {name: Parts() for name in mats}

    ground(parts)
    street(parts)
    tram(parts, 9.0, 1.9)
    figure(parts, -2.5, -8.6)
    bridge(parts, 240.0)
    wires(parts)
    for name, p in parts.items():
        if p.verts:
            p.build(name, mats[name], kinds[name])

    optics = bpy.data.cameras.new("eye")
    optics.lens = 40
    optics.sensor_width = 36
    optics.clip_end = 1000
    camera = bpy.data.objects.new("eye", optics)
    camera.location = (-1.0, -15.0, 2.45)
    camera.rotation_euler = (math.radians(95.5), 0, math.radians(-1.5))
    scene.collection.objects.link(camera)
    scene.camera = camera

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    # Where the street's lines meet, for the engraving to run its hatching toward.
    bpy.context.view_layer.update()
    far = camera.location + Vector((0, 100000, 0))
    vp = world_to_camera_view(scene, camera, far)
    with open(os.path.join(HERE, "art", "street.json"), "w") as out:
        json.dump({"vanishing": [vp.x, 1 - vp.y], "lens": optics.lens}, out)
    scene.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("WROTE", OUT)


main()
