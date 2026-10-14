"""The key light the props on the contact page's leather share: a large soft lamp close by, up to the left, as a
table by a window is lit, so each prop is lit from that side and throws its shadow down and to the right. Because
the lamp is wide and near, the shadow is a real one: dark and crisp where the prop meets the leather, thinning and
blurring the further it falls from it, the parts that stand highest, the lens, throwing the softest and palest of
it. It is in the stand's shadow pass as much as in the photograph, so the shadow comes out with the prop."""

import bpy
from mathutils import Vector

# Where the light comes from, from the prop: up to the left of the page and well up over it.
FROM = Vector((-0.8, 0.9, 1.6)).normalized()  # about fifty degrees up: the shadow falls about the prop's height off it
DISTANCE = 34.0  # em from the prop to the lamp
SIZE = 14.0  # em across the lamp: at that distance about twenty-five degrees wide, a window a little way off
# Its power, for about four times the light on the leather that the stand's room gives: a lamp of power P lights a
# surface d off and facing it with about P / (pi d^2).
POWER = 4.0 * 3.14159 * 3.14159 * DISTANCE**2


def add(at):
    """The lamp, aimed at the point at on the leather (x, y in the stage's own axes)."""
    lamp = bpy.data.lights.new("key", "AREA")
    lamp.shape = "DISK"
    lamp.size = SIZE
    lamp.energy = POWER
    obj = bpy.data.objects.new("key", lamp)
    target = Vector((at[0], at[1], 0.0))
    obj.location = target + FROM * DISTANCE
    obj.rotation_euler = (-FROM).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(obj)
    return obj
