"""The key light the props on the contact page's leather share: one lamp up to the left, as a table by a window or
under a desk lamp is lit, so each prop is lit from that side and throws its shadow down and to the right, the same
way for all of them. A sun, so the shadow's direction and softness do not depend on where on the leather a prop
lies: the shadow is sharp where a prop touches the leather and softens the further it falls, as a lamp a metre off
leaves it. It is in the stand's shadow pass as much as in the photograph, so the shadow comes out with the prop."""

import math

import bpy
from mathutils import Vector

# Where the light comes from: up to the left of the page and well up over it.
TOWARD = Vector((1.0, -1.15, -1.9)).normalized()
STRENGTH = 9.0  # against the stand's room, which gives about pi: the lamp is most of the light
SOFT = 12.0  # degrees across the lamp, as seen from the leather


def add():
    lamp = bpy.data.lights.new("key", "SUN")
    lamp.energy = STRENGTH
    lamp.angle = math.radians(SOFT)
    obj = bpy.data.objects.new("key", lamp)
    obj.rotation_euler = TOWARD.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(obj)
    return obj
