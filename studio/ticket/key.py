"""The key light the props on the contact page's leather share: a large soft lamp close by, up to the left, as a
table by a window is lit, so each prop is lit from that side and throws its shadow down and to the right. Because
the lamp is wide and near, the shadow is a real one: dark and crisp where the prop meets the leather, thinning and
blurring the further it falls from it, the parts that stand highest, the lens, throwing the softest and palest of
it. It is in the stand's shadow pass as much as in the photograph, so the shadow comes out with the prop."""

import math

import bpy
from mathutils import Vector

# Where the light comes from, from the prop: up to the left of the page and well up over it.
FROM = Vector((-0.8, 0.9, 1.6)).normalized()  # about fifty degrees up: the shadow falls about the prop's height off it
DISTANCE = 34.0  # em from the prop to the lamp
SIZE = 14.0  # em across the lamp: at that distance about twenty-five degrees wide, a window a little way off
# Its power, for about four times the light on the leather that the stand's room gives: a lamp of power P lights a
# surface d off and facing it with about P / (pi d^2).
POWER = 4.0 * 3.14159 * 3.14159 * DISTANCE**2


def window(lamp, area):
    """What glass and metal see of the lamp: a window, a frame and its glazing bars round six panes, as bright as the
    lamp is (a lamp of power P and area A is a surface of strength P / (A pi)). Only reflections see it; the lamp
    does the lighting."""
    w, h = SIZE * 1.05, SIZE * 0.8
    bar = 0.05 * SIZE
    panes = []
    cols, rows = 2, 3
    pw, ph = (w - (cols + 1) * bar) / cols, (h - (rows + 1) * bar) / rows
    for i in range(cols):
        for j in range(rows):
            x0 = -w / 2 + bar + i * (pw + bar)
            y0 = -h / 2 + bar + j * (ph + bar)
            panes.append([(x0, y0), (x0 + pw, y0), (x0 + pw, y0 + ph), (x0, y0 + ph)])
    verts, faces = [], []
    for quad in panes:
        faces.append(tuple(range(len(verts), len(verts) + 4)))
        verts += [(x, y, 0.0) for x, y in quad]
    mesh = bpy.data.meshes.new("window")
    mesh.from_pydata(verts, [], faces)
    glow = bpy.data.materials.new("window")
    glow.use_nodes = True
    nodes = glow.node_tree.nodes
    nodes.clear()
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = POWER / (area * math.pi)
    out = nodes.new("ShaderNodeOutputMaterial")
    glow.node_tree.links.new(emit.outputs[0], out.inputs["Surface"])
    mesh.materials.append(glow)
    pane = bpy.data.objects.new("window", mesh)
    pane["stand"] = "shadowless"
    for flag in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_volume_scatter"):
        setattr(pane, flag, False)
    pane.matrix_world = lamp.matrix_world.copy()
    bpy.context.scene.collection.objects.link(pane)
    return pane


def add(at):
    """The lamp, aimed at the point at on the leather (x, y in the stage's own axes), and its window."""
    lamp = bpy.data.lights.new("key", "AREA")
    lamp.shape = "DISK"
    lamp.size = SIZE
    lamp.energy = POWER
    obj = bpy.data.objects.new("key", lamp)
    target = Vector((at[0], at[1], 0.0))
    obj.location = target + FROM * DISTANCE
    obj.rotation_euler = (-FROM).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(obj)
    obj.visible_glossy = False
    obj.visible_transmission = False
    bpy.context.view_layer.update()
    window(obj, math.pi * (SIZE / 2) ** 2)
    return obj
