"""Turkish Vans for the signal's post (render.py), modelled and furred in the signal's own scene, so the one sun and
sky light them, they throw their shadows on the post, and they are seen from where the signal is seen.

A Van is a white cat with its colour only on its head and its tail: two patches over the ears, parted by a white
blaze down the forehead, and a bushy tail in the same colour, auburn as the breed's own, or black or cream. Each cat
is built in its own frame, x toward its nose, y to its left and z up from the floor it stands on, as soft forms that
run together (a metaball for each part), then given fur: strands combed back and down over the body, short on the
face and legs and long on the tail. render.py stands it on the post with its floor on the post's side.
"""

import math

import bmesh
import bpy
from mathutils import Matrix, Vector

# A coat's colour as hair holds it: how much melanin, and how red the melanin is.
COATS = {"auburn": (0.4, 1.0), "black": (0.96, 0.12), "cream": (0.22, 0.75)}
WHITE = (0.035, 0.45)
# Each coat's colour as the skin under the fur shows it, where the fur parts.
SKIN = {"auburn": (0.6, 0.22, 0.06), "black": (0.02, 0.018, 0.018), "cream": (0.62, 0.42, 0.24), "white": (0.85, 0.83, 0.8)}
EYES = [(0.75, 0.42, 0.05), (0.18, 0.42, 0.8), (0.55, 0.6, 0.12)]


def legs(front, hind, y_front=0.024, y_hind=0.04):
    """A pair of front legs and a pair of hind legs, each leg given for the cat's left side as (x, z, r) points from
    the shoulder or hip down to the paw, or a second list for the right side when the two differ."""
    out = []
    for leg, y in ((front, y_front), (hind, y_hind)):
        left, right = (leg, leg) if not isinstance(leg[0], list) else leg
        out.append(("leg", [(x, y, z, r) for x, z, r in left]))
        out.append(("leg", [(x, -y, z, r) for x, z, r in right]))
    return out


# Each pose: its parts as chains of (x, y, z, radius) through the middle of the part, the head's middle, the ears
# as (base, tip), where the eyes are (none when they are shut), and how far it runs along the floor, back to front.
POSES = {
    "sit": dict(
        parts=[
            ("body", [(-0.06, 0, 0.075, 0.09), (-0.03, 0, 0.12, 0.078), (0.02, 0, 0.165, 0.066), (0.05, 0, 0.21, 0.052)]),
            ("tail", [(-0.11, 0, 0.025, 0.026), (-0.09, 0.065, 0.016, 0.028), (0.0, 0.088, 0.016, 0.028), (0.07, 0.07, 0.016, 0.024), (0.1, 0.04, 0.016, 0.02)]),
            *legs([(0.055, 0.15, 0.026), (0.07, 0.08, 0.019), (0.074, 0.02, 0.016), (0.088, 0.012, 0.018)],
                  [(-0.06, 0.075, 0.055), (-0.02, 0.04, 0.038), (0.0, 0.016, 0.02), (0.04, 0.012, 0.018)]),
        ],
        head=(0.075, 0, 0.27),
        span=(-0.13, 0.12),
    ),
    "hang": dict(
        parts=[
            ("body", [(-0.06, 0, 0.075, 0.09), (-0.03, 0, 0.12, 0.078), (0.02, 0, 0.165, 0.066), (0.05, 0, 0.21, 0.052)]),
            # Hung off the side of the post and down past it.
            ("tail", [(-0.1, 0.02, 0.03, 0.026), (-0.1, 0.085, 0.0, 0.028), (-0.085, 0.095, -0.08, 0.028), (-0.065, 0.088, -0.16, 0.025), (-0.05, 0.075, -0.22, 0.02)]),
            *legs([(0.055, 0.15, 0.026), (0.07, 0.08, 0.019), (0.074, 0.02, 0.016), (0.088, 0.012, 0.018)],
                  [(-0.06, 0.075, 0.055), (-0.02, 0.04, 0.038), (0.0, 0.016, 0.02), (0.04, 0.012, 0.018)]),
        ],
        head=(0.075, 0, 0.27),
        span=(-0.13, 0.11),
    ),
    "loaf": dict(
        parts=[
            ("body", [(-0.15, 0, 0.068, 0.072), (-0.07, 0, 0.082, 0.084), (0.02, 0, 0.084, 0.08), (0.08, 0, 0.1, 0.06)]),
            ("tail", [(-0.2, 0.0, 0.04, 0.026), (-0.2, 0.07, 0.02, 0.027), (-0.1, 0.098, 0.016, 0.026), (0.0, 0.09, 0.016, 0.022)]),
            ("leg", [(0.1, 0.03, 0.016, 0.02)]),
            ("leg", [(0.1, -0.03, 0.016, 0.02)]),
        ],
        head=(0.13, 0, 0.152),
        span=(-0.24, 0.19),
    ),
    "sleep": dict(
        parts=[
            ("body", [(-0.11, 0.0, 0.06, 0.07), (-0.06, -0.05, 0.07, 0.08), (0.03, -0.06, 0.07, 0.076), (0.09, 0.0, 0.064, 0.064)]),
            ("tail", [(-0.13, 0.02, 0.03, 0.026), (-0.09, 0.085, 0.026, 0.027), (0.0, 0.105, 0.026, 0.025), (0.06, 0.09, 0.03, 0.02)]),
        ],
        # Curled with its face and tail on its left, which is the side the camera sees.
        head=(0.075, 0.055, 0.075),
        nose=(-1, -0.25, -0.15),
        shut=True,
        span=(-0.19, 0.16),
    ),
    "walk": dict(
        parts=[
            ("body", [(-0.16, 0, 0.2, 0.068), (-0.09, 0, 0.2, 0.074), (0.0, 0, 0.2, 0.074), (0.08, 0, 0.21, 0.066), (0.13, 0, 0.25, 0.048)]),
            ("tail", [(-0.2, 0, 0.21, 0.027), (-0.26, 0, 0.27, 0.029), (-0.27, 0, 0.36, 0.029), (-0.23, 0, 0.42, 0.025)]),
            *legs(
                [[(0.08, 0.17, 0.03), (0.09, 0.09, 0.02), (0.09, 0.02, 0.016), (0.1, 0.012, 0.018)],
                 [(0.07, 0.17, 0.03), (0.11, 0.1, 0.02), (0.135, 0.055, 0.016), (0.15, 0.045, 0.017)]],
                [[(-0.15, 0.18, 0.05), (-0.12, 0.11, 0.03), (-0.17, 0.06, 0.018), (-0.15, 0.012, 0.017)],
                 [(-0.15, 0.18, 0.05), (-0.1, 0.12, 0.03), (-0.14, 0.06, 0.018), (-0.11, 0.012, 0.017)]],
                y_front=0.03, y_hind=0.036,
            ),
        ],
        head=(0.175, 0, 0.29),
        span=(-0.3, 0.24),
    ),
    "stretch": dict(
        parts=[
            ("body", [(-0.16, 0, 0.2, 0.068), (-0.09, 0, 0.17, 0.072), (0.0, 0, 0.12, 0.07), (0.07, 0, 0.09, 0.06)]),
            ("tail", [(-0.21, 0, 0.22, 0.027), (-0.27, 0, 0.3, 0.029), (-0.3, 0, 0.38, 0.027)]),
            *legs([(0.07, 0.07, 0.028), (0.15, 0.03, 0.02), (0.22, 0.016, 0.017), (0.245, 0.012, 0.018)],
                  [(-0.15, 0.18, 0.05), (-0.145, 0.1, 0.03), (-0.17, 0.05, 0.018), (-0.15, 0.012, 0.017)],
                  y_front=0.03, y_hind=0.036),
        ],
        head=(0.15, 0, 0.11),
        span=(-0.32, 0.28),
    ),
}

# A metaball's surface lies well inside its radius, so each is grown to bring its surface out to the radius the part
# is given: a lone ball a long way, a ball in a chain, held up by its neighbours, less.
GROW = {"chain": 1.18, "head": 1.62}


def ball_chain(points, step=0.3):
    """Balls along a chain of (x, y, z, r), close enough that they run together into one smooth part."""
    out = []
    for a, b in zip(points, points[1:]):
        pa, pb = Vector(a[:3]), Vector(b[:3])
        n = max(1, math.ceil((pb - pa).length / (step * min(a[3], b[3]))))
        out += [(pa.lerp(pb, i / n), a[3] + (b[3] - a[3]) * i / n) for i in range(n)]
    out.append((Vector(points[-1][:3]), points[-1][3]))
    return out


def head_parts(head, nose_dir, mirror):
    """The head: a skull, cheeks, the muzzle and chin, the way nose_dir points (x, y, z, in the cat's frame)."""
    c = Vector(head)
    ahead = Vector(nose_dir).normalized()
    side = Vector((0, 0, 1)).cross(ahead).normalized()
    up = ahead.cross(side).normalized()
    return [
        ("skull", c, 0.056),
        ("cheek", c + ahead * 0.022 + side * 0.03 - up * 0.016, 0.034),
        ("cheek", c + ahead * 0.022 - side * 0.03 - up * 0.016, 0.034),
        ("muzzle", c + ahead * 0.05 - up * 0.018, 0.025),
        ("chin", c + ahead * 0.04 - up * 0.036, 0.017),
    ], (c, ahead, side, up)


HEAD = {"skull", "cheek", "muzzle", "chin"}


def smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def build(name, pose, coat, mirror=False, eye=0):
    """One cat, in its own frame, as a furred mesh with its ears, eyes and nose parented to it."""
    spec = POSES[pose]
    flip = -1 if mirror else 1
    nose_dir = spec.get("nose", (1, 0, -0.15))
    nose_dir = (nose_dir[0], nose_dir[1] * flip, nose_dir[2])
    head = (spec["head"][0], spec["head"][1] * flip, spec["head"][2])

    balls = []
    for kind, chain in spec["parts"]:
        for at, r in ball_chain([(x, y * flip, z, r) for x, y, z, r in chain]):
            balls.append((kind, at, r))
    parts, (hc, ahead, side, up) = head_parts(head, nose_dir, mirror)
    balls += parts
    # The neck, from the head down into the body.
    balls += [("body", at, r) for at, r in ball_chain([(*(hc - ahead * 0.02 - up * 0.03), 0.042), (*(hc - ahead * 0.05 - up * 0.07), 0.05)])]

    meta = bpy.data.metaballs.new(name)
    meta.resolution = meta.render_resolution = 0.005
    meta.threshold = 0.6
    for kind, at, r in balls:
        e = meta.elements.new()
        e.co = at
        e.radius = r * GROW["head" if kind in HEAD else "chain"]
        e.stiffness = 2.0
    blob = bpy.data.objects.new(name, meta)
    bpy.context.collection.objects.link(blob)
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    bpy.context.view_layer.objects.active = blob
    blob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    cat = bpy.context.active_object
    cat.name = name
    mesh = cat.data
    for poly in mesh.polygons:
        poly.use_smooth = True

    # Where the coat's colour is: all of the tail, and the head over the ears, parted by the blaze.
    centres = [(kind, at, r) for kind, at, r in balls]
    uv = mesh.uv_layers.new(name="coat")
    long = cat.vertex_groups.new(name="long")
    colour = []
    for v in mesh.vertices:
        p = v.co
        kind, at, r = min(centres, key=lambda b: (p - b[1]).length / b[2])
        amount = 0.0
        length = {"tail": 1.0, "body": 0.62, "leg": 0.3}.get(kind, 0.16)
        if kind == "tail":
            amount = 1.0
        elif kind == "skull":
            d = p - hc
            over = d.dot(up) / 0.05
            blaze = abs(d.dot(side)) / 0.05
            back = -d.dot(ahead) / 0.05
            amount = smooth(-0.15, 0.25, over + 0.3 * back) * smooth(0.12, 0.3, blaze)
        colour.append(amount)
        long.add([v.index], length, "REPLACE")
    for loop in mesh.loops:
        uv.data[loop.index].uv = (colour[loop.vertex_index], 0.5)

    cat.data.materials.append(skin_material(name, coat))
    cat.data.materials.append(fur_material(name, coat))
    fur(cat, name)

    for base, tip in ears(hc, ahead, side, up):
        ear(name, base, tip, ahead, coat, cat)
    if not spec.get("shut"):
        for s in (1, -1):
            at = hc + ahead * 0.048 + side * s * 0.024 + up * 0.01
            jewel(f"{name}-eye", at, 0.0095, eye_material(eye), cat)
    jewel(f"{name}-nose", hc + ahead * 0.076 - up * 0.01, 0.0065, nose_material(), cat)
    return cat


def ears(hc, ahead, side, up):
    return [(hc + up * 0.032 + side * s * 0.03 - ahead * 0.006, hc + up * 0.074 + side * s * 0.052 + ahead * 0.002) for s in (1, -1)]


def ear(name, base, tip, ahead, coat, parent):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.031, radius2=0.005, depth=1.0)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.5))
    mesh = bpy.data.meshes.new(f"{name}-ear")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(f"{name}-ear", mesh)
    bpy.context.collection.objects.link(obj)
    axis = (tip - base).normalized()
    rot = axis.to_track_quat("Z", "X").to_matrix().to_4x4()
    # Thin from front to back, as an ear is, and as long as from base to tip.
    obj.matrix_world = Matrix.Translation(base) @ rot @ Matrix.Diagonal((0.35, 1.0, (tip - base).length, 1.0))
    obj.data.materials.append(bpy.data.materials[f"{name}-skin-ear"] if f"{name}-skin-ear" in bpy.data.materials else ear_material(name, coat))
    for poly in mesh.polygons:
        poly.use_smooth = True
    obj.parent = parent
    return obj


def jewel(name, at, radius, material, parent):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=radius)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = at
    obj.data.materials.append(material)
    for poly in mesh.polygons:
        poly.use_smooth = True
    obj.parent = parent


def fur(cat, name):
    """Strands over the whole cat, combed back toward the tail and down, longer where the vertex group says."""
    area = sum(p.area for p in cat.data.polygons)
    mod = cat.modifiers.new("fur", "PARTICLE_SYSTEM")
    system = cat.particle_systems[0]
    s = system.settings
    s.name = f"{name}-fur"
    s.type = "HAIR"
    s.count = int(area * 26000)
    # With the direction set by hand, these are the strand itself in metres: out from the skin, then back and down.
    s.use_advanced_hair = True
    s.normal_factor = 0.005
    s.object_align_factor = (-0.0042, 0.0, -0.003)
    s.factor_random = 0.0008
    s.child_type = "INTERPOLATED"
    s.child_percent = 2
    s.rendered_child_count = 14
    s.child_length = 1.0
    s.clump_factor = 0.25
    s.roughness_1 = 0.0025
    s.roughness_endpoint = 0.004
    s.root_radius = 1.0
    s.tip_radius = 0.15
    s.radius_scale = 0.0011
    s.display_step = 3
    s.render_step = 4
    s.material_slot = f"{name}-fur"
    system.vertex_group_length = "long"
    system.vertex_group_density = ""
    mod.show_viewport = True
    return mod


def coat_mix(nodes, links):
    coord = nodes.new("ShaderNodeUVMap")
    coord.uv_map = "coat"
    split = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coord.outputs["UV"], split.inputs["Vector"])
    return split.outputs["X"]


def fur_material(name, coat):
    mat = bpy.data.materials.new(f"{name}-fur")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.remove(nodes["Principled BSDF"])
    out = nodes["Material Output"]
    hairs = []
    for melanin, red in (WHITE, COATS[coat]):
        h = nodes.new("ShaderNodeBsdfHairPrincipled")
        h.parametrization = "MELANIN"
        h.inputs["Melanin"].default_value = melanin
        h.inputs["Melanin Redness"].default_value = red
        h.inputs["Roughness"].default_value = 0.38
        h.inputs["Radial Roughness"].default_value = 0.5
        h.inputs["Coat"].default_value = 0.15
        h.inputs["Random Color"].default_value = 0.12
        h.inputs["Random Roughness"].default_value = 0.2
        hairs.append(h)
    mix = nodes.new("ShaderNodeMixShader")
    links.new(coat_mix(nodes, links), mix.inputs["Fac"])
    links.new(hairs[0].outputs[0], mix.inputs[1])
    links.new(hairs[1].outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs["Surface"])
    return mat


def skin_material(name, coat):
    mat = bpy.data.materials.new(f"{name}-skin")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    links.new(coat_mix(nodes, links), mix.inputs[0])
    mix.inputs[6].default_value = (*SKIN["white"], 1)
    mix.inputs[7].default_value = (*SKIN[coat], 1)
    links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.7
    bsdf.inputs["Sheen Weight"].default_value = 0.8
    bsdf.inputs["Sheen Roughness"].default_value = 0.5
    return mat


def ear_material(name, coat):
    mat = bpy.data.materials.new(f"{name}-skin-ear")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*SKIN[coat], 1)
    bsdf.inputs["Roughness"].default_value = 0.75
    bsdf.inputs["Sheen Weight"].default_value = 0.5
    bsdf.inputs["Sheen Tint"].default_value = (*SKIN[coat], 1)
    bsdf.inputs["Subsurface Weight"].default_value = 0.3
    bsdf.inputs["Subsurface Radius"].default_value = (0.9, 0.3, 0.2)
    bsdf.inputs["Subsurface Scale"].default_value = 0.003
    return mat


def eye_material(i):
    name = f"eye-{i}"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*EYES[i], 1)
    bsdf.inputs["Roughness"].default_value = 0.05
    bsdf.inputs["Coat Weight"].default_value = 1.0
    return mat


def nose_material():
    if "nose" in bpy.data.materials:
        return bpy.data.materials["nose"]
    mat = bpy.data.materials.new("nose")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.75, 0.32, 0.33, 1)
    bsdf.inputs["Roughness"].default_value = 0.35
    return mat
