"""The picture on the ticket, before it is inked: Howrah Bridge seen from the Hooghly in the rain, a country boat
in front with someone standing in it under an umbrella, and the low line of the city behind. Run from the
repository root:

    blender -b --factory-startup -P studio/ticket/river.py -- [--view main|tower|boat|span] [--size 1600] [--samples 64]

Writes studio/ticket/art/river.exr, a multilayer EXR with the light, the normals, the depth and which kind of thing
each pixel is, and studio/ticket/art/river.json, where the horizon falls. studio/ticket/ink.py draws from them.
--view tower writes river-tower.exr and river-tower.json instead: the picture on the small tickets of the strip, a
look up the near tower from the water by its pier. --view boat and --view span are two of the stamps' pictures:
the boat close to, and the suspended span from far down the river.

Metres. x runs along the bridge, y across the river away from the camera, z up. The bridge is a balanced cantilever,
as the real one is: two towers 82 m above the piers, anchor arms back to the banks, cantilever arms reaching out
over the river, and a suspended span hung between their ends. Its trusses are 23 m apart. Each anchor arm comes down
on an anchor pier at the water's edge, and the road runs on onto the bank, between godowns and houses.
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
ART = os.path.join(HERE, "art")

# What each kind of thing is, in the object index pass. ink.py draws each its own way.
KIND = {"sky": 0, "steel": 1, "water": 2, "boat": 3, "figure": 4, "city": 5, "pier": 6, "deck": 7}

TOWER = 82.0  # height of each tower above its pier
DECK = 9.0  # the roadway, above the water
TRUSS = 11.5  # half the distance between the two trusses
SPAN = 457.0  # tower to tower
ANCHOR = 99.0  # tower to the end of each anchor arm
HUNG = 172.0  # the suspended span in the middle
ARM_END = 24.0  # how high the top chord comes down to at the end of an arm
ROAD = 1500.0  # how far the roadway runs on onto each bank past the anchor arm


class Parts:
    """Beams and boxes gathered into one mesh, for one material."""

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

    def lathe(self, profile, centre, sides=16, squash=1.0):
        """A solid of revolution about a vertical axis: profile is (radius, height) pairs from the bottom up."""
        cx, cy, cz = centre
        n = len(self.verts)
        for r, z in profile:
            for k in range(sides):
                a = 2 * math.pi * k / sides
                self.verts.append((cx + r * math.cos(a), cy + r * squash * math.sin(a), cz + z))
        for i in range(len(profile) - 1):
            for k in range(sides):
                j = (k + 1) % sides
                self.faces.append((n + i * sides + k, n + i * sides + j, n + (i + 1) * sides + j, n + (i + 1) * sides + k))
        self.faces.append(tuple(n + k for k in reversed(range(sides))))
        top = n + (len(profile) - 1) * sides
        self.faces.append(tuple(top + k for k in range(sides)))

    def build(self, name, material, kind, smooth=False):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.verts, [], self.faces)
        mesh.validate()
        if smooth:
            mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        mesh.materials.append(material)
        obj = bpy.data.objects.new(name, mesh)
        obj.pass_index = KIND[kind]
        bpy.context.scene.collection.objects.link(obj)
        return obj


def material(name, colour, rough=0.7, metal=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*colour, 1)
    shader.inputs["Roughness"].default_value = rough
    shader.inputs["Metallic"].default_value = metal
    return mat


def water_material():
    """The river in the rain: brown, flat, broken into long low swells and pocked by drops."""
    mat = bpy.data.materials.new("water")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0.05, 0.045, 0.035, 1)
    shader.inputs["Roughness"].default_value = 0.08
    coord = nodes.new("ShaderNodeTexCoord")
    stretch = nodes.new("ShaderNodeMapping")
    stretch.inputs["Scale"].default_value = (0.05, 0.4, 1)
    links.new(coord.outputs["Object"], stretch.inputs["Vector"])
    swell = nodes.new("ShaderNodeTexWave")
    swell.wave_type = "BANDS"
    swell.bands_direction = "Y"
    swell.inputs["Scale"].default_value = 2.2
    swell.inputs["Distortion"].default_value = 6.0
    swell.inputs["Detail"].default_value = 3.0
    links.new(stretch.outputs["Vector"], swell.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    links.new(swell.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return mat


def truss(steel, x0, x1, top0, top1, panels, k=True):
    """One side of a truss on each plane y = +-TRUSS: a bottom chord at the deck, a top chord from top0 to top1
    in height, verticals at every panel point and K bracing between them, as the Howrah trusses are laced."""
    for y in (-TRUSS, TRUSS):
        steel.beam((x0, y, DECK), (x1, y, DECK), 1.6, 2.2)
        steel.beam((x0, y, top0), (x1, y, top1), 1.5, 2.0)
        for i in range(panels + 1):
            t = i / panels
            x = x0 + (x1 - x0) * t
            top = top0 + (top1 - top0) * t
            steel.beam((x, y, DECK), (x, y, top), 0.9)
            if i < panels:
                xn = x0 + (x1 - x0) * (i + 1) / panels
                topn = top0 + (top1 - top0) * (i + 1) / panels
                mid = (DECK + top) / 2, (DECK + topn) / 2
                if k:
                    # A K: from the middle of each vertical to the two ends of the next.
                    steel.beam((x, y, mid[0]), (xn, y, DECK), 0.6)
                    steel.beam((x, y, mid[0]), (xn, y, topn), 0.6)
                else:
                    steel.beam((x, y, DECK), (xn, y, topn), 0.6)
    # Overhead bracing between the two trusses, and cross girders under the deck.
    for i in range(panels + 1):
        t = i / panels
        x = x0 + (x1 - x0) * t
        top = top0 + (top1 - top0) * t
        steel.beam((x, -TRUSS, top), (x, TRUSS, top), 0.7)
        if i < panels:
            xn = x0 + (x1 - x0) * (i + 1) / panels
            topn = top0 + (top1 - top0) * (i + 1) / panels
            steel.beam((x, -TRUSS, top), (xn, TRUSS, topn), 0.4)


def tower(steel, piers, x):
    """A tower: four legs from the pier to the top, battered in toward the head, laced on every face, with a
    deep portal across the roadway and a cap over all."""
    foot, head = 6.5, 3.5
    for dy in (-TRUSS, TRUSS):
        for dx in (-1, 1):
            steel.beam((x + dx * foot, dy, DECK - 1.5), (x + dx * head, dy, DECK + TOWER), 2.0)
        z = DECK
        step = 8.0
        while z < DECK + TOWER - 2:
            t0 = (z - DECK) / TOWER
            t1 = min(1.0, (z + step - DECK) / TOWER)
            w0 = foot + (head - foot) * t0
            w1 = foot + (head - foot) * t1
            steel.beam((x - w0, dy, z), (x + w1, dy, z + step), 0.7)
            steel.beam((x + w0, dy, z), (x - w1, dy, z + step), 0.7)
            steel.beam((x - w1, dy, z + step), (x + w1, dy, z + step), 0.8)
            z += step
        steel.box(x - head - 1.2, x + head + 1.2, dy - 1.4, dy + 1.4, DECK + TOWER, DECK + TOWER + 3.0)
    # The portal over the road and the bracing above it, between the two trusses.
    for z0, z1 in ((DECK + 34, DECK + 46), (DECK + 58, DECK + 72)):
        for dx in (-head - 1, head + 1):
            steel.beam((x + dx, -TRUSS, z0), (x + dx, TRUSS, z0), 1.1)
            steel.beam((x + dx, -TRUSS, z1), (x + dx, TRUSS, z1), 1.1)
            steel.beam((x + dx, -TRUSS, z0), (x + dx, TRUSS, z1), 0.6)
            steel.beam((x + dx, -TRUSS, z1), (x + dx, TRUSS, z0), 0.6)
    # The pier: a block of masonry standing in the river.
    piers.box(x - 9, x + 9, -TRUSS - 4, TRUSS + 4, -3, DECK - 1.5)


def bridge(steel, piers, deck, x_left):
    """The whole bridge, its left tower at x_left."""
    x_right = x_left + SPAN
    tower(steel, piers, x_left)
    tower(steel, piers, x_right)
    arm = (SPAN - HUNG) / 2
    top = DECK + TOWER
    # Anchor arms back to the banks, and the cantilever arms out over the water.
    truss(steel, x_left - ANCHOR, x_left, DECK + ARM_END, top, 7)
    truss(steel, x_left, x_left + arm, top, DECK + ARM_END, 10)
    truss(steel, x_right - arm, x_right, DECK + ARM_END, top, 10)
    truss(steel, x_right, x_right + ANCHOR, top, DECK + ARM_END, 7)
    # The suspended span: a lower truss hung from the ends of the cantilever arms, its top chord starting at the
    # height the arms come down to, so the chords meet at the hinge, and bowed a little between.
    panels = 12
    for i in range(panels):
        xa = x_left + arm + HUNG * i / panels
        xb = x_left + arm + HUNG * (i + 1) / panels
        ha = DECK + ARM_END + 8 * math.sin(math.pi * i / panels)
        hb = DECK + ARM_END + 8 * math.sin(math.pi * (i + 1) / panels)
        truss(steel, xa, xb, ha, hb, 1)
    # The roadway, and the footpaths cantilevered out either side, running on past the anchor arms onto the banks.
    deck.box(x_left - ANCHOR - ROAD, x_right + ANCHOR + ROAD, -TRUSS - 3.5, TRUSS + 3.5, DECK - 1.6, DECK - 0.3)
    deck.box(x_left - ANCHOR - ROAD, x_right + ANCHOR + ROAD, -TRUSS - 3.6, -TRUSS - 3.3, DECK - 0.3, DECK + 1.1)


def banks(piers, land, x_left):
    """The banks the anchor arms come down onto: the end of each arm sits on an anchor pier at the water's edge, the
    roadway runs on onto the bank, and a row of godowns and houses stands along the bank either side of the road.
    Downstream of the bridge the banks fall away from the river a little past the road, so the water the boat and
    the lens are on stays open."""
    import random

    rng = random.Random(5)
    front = TRUSS + 30  # how far downstream of the bridge each bank runs
    for end, out in ((x_left - ANCHOR, -1), (x_left + SPAN + ANCHOR, 1)):
        piers.box(end - 8, end + 8, -TRUSS - 4, TRUSS + 4, -3, DECK - 1.5)
        shore = end + out * 4
        land.box(min(shore, shore + out * ROAD), max(shore, shore + out * ROAD), -front, 2000, -1, DECK - 1.6)
        for side, reach in ((-1, front), (1, 700)):
            y = side * (TRUSS + 8)
            while abs(y) < reach:
                w = rng.uniform(10, 28)
                h = rng.choice((8, 10, 12, 14, 18)) * rng.uniform(0.85, 1.2)
                x0 = shore + out * rng.uniform(4, 10)
                depth = rng.uniform(12, 24)
                y1 = y + side * min(w, reach - abs(y))
                land.box(min(x0, x0 + out * depth), max(x0, x0 + out * depth), min(y, y1), max(y, y1), DECK - 1.6, DECK - 1.6 + h)
                y = y1 + side * rng.uniform(0, 2)


def city(parts):
    """The far bank: a low line of old houses, a few taller blocks, a temple's spire, the odd chimney and
    water tank, all standing in the haze behind the bridge."""
    import random

    rng = random.Random(7)
    x = -700.0
    while x < 900:
        w = rng.uniform(10, 34)
        h = rng.choice((8, 10, 12, 14, 16, 20, 26, 34)) * rng.uniform(0.8, 1.2)
        y = 420 + rng.uniform(0, 80)
        parts.box(x, x + w, y, y + 14, 0, h)
        if rng.random() < 0.18:
            parts.lathe([(1.6, 0), (1.6, 6), (2.4, 6), (2.4, 8), (0.1, 8.2)], (x + w / 2, y + 7, h))
        if rng.random() < 0.08:
            parts.box(x + w * 0.4, x + w * 0.4 + 2, y + 6, y + 8, h, h + 22)
        x += w + rng.uniform(0, 6)
    # Godowns end to end along the quay in front of them, up to the right bank, so the far bank shows under the bridge
    # as one unbroken line and not as houses with the sky between them.
    quay = random.Random(9)
    x = -700.0
    while x < 500:
        w = quay.uniform(14, 40)
        parts.box(x, min(x + w, 500), 404, 418, 0, quay.uniform(14, 20))
        x += w
    # A temple spire, rising out of the roofs on the left.
    parts.lathe([(9, 0), (8, 14), (6, 24), (3.5, 34), (1.2, 42), (0.2, 46)], (-180, 470, 10), sides=12)
    # A clock tower behind the far end of the bridge.
    parts.box(560, 572, 450, 462, 0, 54)
    parts.lathe([(7, 0), (0.3, 10)], (566, 456, 54), sides=4)


def boat(hull, figure, at, turn):
    """A country boat, a nouka: long, low, its ends swept up into points, a curved hood of matting over the
    middle, a steering oar at the stern. Someone stands in the bow under a black umbrella."""
    cx, cy = at
    ca, sa = math.cos(turn), math.sin(turn)

    def p(x, y, z):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca, z)

    length, beam, steps = 9.0, 1.15, 18
    n = len(hull.verts)
    rings = []
    for i in range(steps + 1):
        t = i / steps
        x = -length / 2 + length * t
        rise = 0.35 + 1.25 * (abs(2 * t - 1) ** 3)
        half = beam * math.sqrt(max(0.0, 1 - (2 * t - 1) ** 2)) + 0.03
        rings.append([p(x, -half, rise), p(x, -half * 0.75, -0.25), p(x, half * 0.75, -0.25), p(x, half, rise)])
    for ring in rings:
        hull.verts += ring
    for i in range(steps):
        a, b = n + i * 4, n + (i + 1) * 4
        hull.faces += [(a, b, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2), (a + 2, b + 2, b + 3, a + 3), (a + 3, b + 3, b, a)]
    # The hood: a half barrel of matting over the middle third.
    m = len(hull.verts)
    arc = 10
    for i in range(arc + 1):
        a = math.pi * i / arc
        for x in (-1.3, 1.3):
            hull.verts.append(p(x, -beam * 0.95 * math.cos(a), 0.35 + 1.1 * math.sin(a)))
    for i in range(arc):
        a, b = m + i * 2, m + (i + 1) * 2
        hull.faces += [(a, a + 1, b + 1, b)]
    # The steering oar, trailing from the stern.
    hull.beam(p(-length / 2 + 0.6, 0.2, 1.4), p(-length / 2 - 2.2, 0.6, -0.4), 0.09)
    hull.beam(p(-length / 2 - 2.2, 0.6, -0.4), p(-length / 2 - 2.9, 0.75, -0.55), 0.3, 0.05)

    # The figure in the bow, facing the bridge: legs, a long kurta to the knee, shoulders, head, the arm up to
    # the umbrella's handle, and the umbrella, eight panels sagging between their ribs.
    fx, fy = length / 2 - 1.9, 0.0
    base = 0.05
    figure.beam(p(fx - 0.08, fy - 0.12, base), p(fx - 0.06, fy - 0.1, base + 0.85), 0.14)
    figure.beam(p(fx + 0.08, fy + 0.12, base), p(fx + 0.06, fy + 0.1, base + 0.85), 0.14)
    figure.lathe([(0.26, 0.55), (0.24, 0.9), (0.21, 1.2), (0.25, 1.38), (0.23, 1.48), (0.1, 1.55)], p(fx, fy, base)[:2] + (base,), sides=14, squash=0.7)
    figure.lathe([(0.04, 0), (0.1, 0.05), (0.115, 0.14), (0.1, 0.24), (0.04, 0.29)], p(fx, fy, base + 1.53)[:2] + (base + 1.53,), sides=12)
    hand = p(fx + 0.12, fy - 0.05, base + 1.35)
    figure.beam(p(fx + 0.2, fy - 0.12, base + 1.42), p(fx + 0.3, fy - 0.2, base + 1.15), 0.09)
    figure.beam(p(fx + 0.3, fy - 0.2, base + 1.15), hand, 0.08)
    apex = Vector(p(fx + 0.1, fy - 0.08, base + 2.25))
    ribs, per, radius = 8, 5, 0.68
    u = len(figure.verts)
    figure.verts.append(tuple(apex))
    for k in range(ribs * per):
        a = 2 * math.pi * k / (ribs * per)
        sag = math.sin(math.pi * (k % per) / per)
        r = radius * (1 - 0.07 * sag)
        figure.verts.append((apex.x + r * math.cos(a), apex.y + r * math.sin(a), apex.z - 0.33 + 0.06 * sag))
    for k in range(ribs * per):
        j = (k + 1) % (ribs * per)
        figure.faces.append((u, u + 1 + k, u + 1 + j))
    figure.beam((apex.x, apex.y, apex.z + 0.1), hand, 0.025)


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=1600)
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--view", choices=("main", "tower", "boat", "span"), default="main")
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

    # A grey monsoon sky, brightest low behind the bridge, and haze that greys the far bank.
    world = bpy.data.worlds.new("sky")
    world.use_nodes = True
    scene.world = world
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.8, 0.8, 0.8, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    world.mist_settings.start = 30
    world.mist_settings.depth = 900
    world.mist_settings.falloff = "LINEAR"
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 1.2
    sun.angle = math.radians(25)
    lamp = bpy.data.objects.new("sun", sun)
    lamp.rotation_euler = (math.radians(55), 0, math.radians(200))
    scene.collection.objects.link(lamp)

    mats = {
        "steel": material("steel", (0.18, 0.18, 0.18), 0.6),
        "pier": material("pier", (0.4, 0.38, 0.34), 0.9),
        "deck": material("deck", (0.12, 0.12, 0.12), 0.8),
        "water": water_material(),
        "city": material("city", (0.45, 0.45, 0.44), 0.9),
        "boat": material("boat", (0.12, 0.09, 0.06), 0.8),
        "figure": material("figure", (0.02, 0.02, 0.02), 0.85),
    }
    parts = {name: Parts() for name in mats}
    bridge(parts["steel"], parts["pier"], parts["deck"], -60.0)
    banks(parts["pier"], parts["city"], -60.0)
    city(parts["city"])
    # From a boat on the water, low, downstream and off to the left, so the bridge stands three quarters on: the near
    # tower large on the left, the suspended span in the middle, the far tower small on the right.
    optics = bpy.data.cameras.new("eye")
    optics.lens = 38
    optics.sensor_width = 36
    optics.clip_end = 5000
    camera = bpy.data.objects.new("eye", optics)
    camera.location = (-215.0, -390.0, 2.6)
    target = Vector((92.0, 0.0, 52.0))
    forward = (target - camera.location).normalized()
    camera.rotation_euler = forward.to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(camera)
    scene.camera = camera
    # The country boat, a little way off the lens and to the right, sitting across the view.
    right = forward.cross(Vector((0, 0, 1))).normalized()
    at = camera.location + Vector((forward.x, forward.y, 0)).normalized() * 13 + right * 0.6
    heading = math.atan2(forward.y, forward.x) + math.radians(70)
    boat(parts["boat"], parts["figure"], (at.x, at.y), heading)
    parts["water"].box(-3000, 3000, -900, 3000, -0.5, 0)
    for name, p in parts.items():
        p.build(name, mats[name], name, smooth=name in ("figure",))
    if args.view == "tower":
        # The strip's picture: from the water by the near pier, looking up the tower into the rain, wide.
        optics.lens = 22
        camera.location = (-30.0, -95.0, 3.0)
        up = (Vector((-60.0, 0.0, 62.0)) - camera.location).normalized()
        camera.rotation_euler = up.to_track_quat("-Z", "Y").to_euler()
    elif args.view == "boat":
        # A stamp's: behind the boat and off to its side, low on the water, the one under the umbrella standing
        # against the bridge far off.
        optics.lens = 50
        back = Vector((forward.x, forward.y, 0)).normalized()
        camera.location = at - back * 17 - right * 4 + Vector((0, 0, 1.8 - at.z))
        look = Vector((at.x, at.y, 3.2)) + back * 40 - camera.location
        camera.rotation_euler = look.normalized().to_track_quat("-Z", "Y").to_euler()
    elif args.view == "span":
        # A stamp's: from far down the river with a long lens, the suspended span bowed across the middle.
        optics.lens = 135
        mid = -60.0 + SPAN / 2
        camera.location = (mid - 40, -620.0, 2.4)
        look = Vector((mid, 0.0, DECK + 16)) - Vector(camera.location)
        camera.rotation_euler = look.normalized().to_track_quat("-Z", "Y").to_euler()

    name = "river" if args.view == "main" else f"river-{args.view}"
    os.makedirs(ART, exist_ok=True)
    bpy.context.view_layer.update()
    far = camera.location + Vector((0, 100000, 0))
    horizon = world_to_camera_view(scene, camera, far)
    with open(os.path.join(ART, f"{name}.json"), "w") as out:
        json.dump({"horizon": 1 - horizon.y}, out)
    scene.render.filepath = os.path.join(ART, f"{name}.exr")
    bpy.ops.render.render(write_still=True)
    print("WROTE", scene.render.filepath)


main()
