"""A Turkish Van cat for the desk, modelled and furred in Blender: the body as a signed distance field (studio/desk/sdf.py),
blended from a skull, cheeks, muzzle, ears, neck, trunk, legs and tail laid out on a pose, and covered in hair: a
quarter of a million strands, each grown from the skin along the way a cat's coat lies, longer on the ruff, the back
and the tail, short on the face and the paws, clumped as fur clumps, and shaded with Blender's hair shader by how much
of each pigment it carries. The van pattern is a white coat with colour on the head, parted by a white blaze up the
forehead, and on the tail. The eyes are glass over an iris with a slit pupil, the nose and the insides of the ears
bare pink skin, and there are whiskers.

Built in centimetres of a real cat, z up, the desk at z = 0, the head toward -x; the cat is scaled to the desk's em
when it is laid.
"""

import math

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

from paint import linear
from sdf import cone, ellipsoid, nets, smax, smin

STEP = 0.3  # cm between the samples the skin is meshed from
# Pigment, as Blender's hair shader takes it: (melanin, redness). The white of a Van has next to none.
WHITE = (0.025, 0.5)  # a Van's white is a warm, chalky cream
COATS = {
    "ginger": (0.3, 1.0),
    "cream": (0.17, 0.75),
    "black": (0.93, 0.1),
}
SKIN = "#d9b8ae"
PINK = "#c7a09a"
NOSE = "#c4706f"
LID = "#3b2b27"  # the bare rims of the eyelids
HEAD = 1.12  # the head, larger than life against the body: the mini cats are kittenish
# The eye's opening in the head's axes (a, b, c), and the eyeball set back behind it so the lids close round it.
EYE = (2.75, 1.75, 0.7)
OPENING = (1.0, 1.25, 0.85)
EYEBALL = (2.25, 1.05)


def frame(forward, up, roll=0.0):
    """A head's axes: forward, right and up, from where it looks and which way is the top of its head."""
    f = Vector(forward).normalized()
    u = (Vector(up) - Vector(up).dot(f) * f).normalized()
    u = Matrix.Rotation(math.radians(roll), 3, f) @ u
    r = f.cross(u).normalized()
    return np.array([f, r, u], dtype=float)


class Cat:
    """One cat in one pose. pose is a dict of the skeleton: the spine's points and radii, the legs, the tail's
    points and the head's centre and axes; coat names the colour of its markings; eyes says whether they are open,
    and their irises' colours, left and right; spots are extra patches on the back, and lip one at the left of the
    upper lip, as the household cat has."""

    def __init__(self, pose, coat="ginger", eyes=("#c79a2a", "#c79a2a"), spots=(), lip=False, seed=1):
        self.pose = pose
        self.coat = COATS[coat]
        self.irises = eyes
        self.open = pose.get("open", True)
        self.spots = spots
        self.lip = lip
        self.rng = np.random.default_rng(seed)
        self.head_at = np.asarray(pose["head"], dtype=float)
        self.axes = frame(*pose["look"])

    # The head, in its own axes: a along where it looks, b to its right, c up its crown.
    def local(self, p):
        return (p - self.head_at) @ self.axes.T

    def eye_centres(self):
        return [self.head_at + HEAD * np.array([EYEBALL[0], side * EYE[1], EYE[2]]) @ self.axes for side in (-1, 1)]

    def openings(self, p):
        """Inside the eyes' openings: negative there. Shut, an opening is only the crease where the lids meet."""
        q = self.local(p) / HEAD
        if self.open:
            return np.minimum(*(ellipsoid(q, (EYE[0], side * EYE[1], EYE[2]), OPENING) for side in (-1, 1)))
        return np.minimum(*(ellipsoid(q, (EYE[0] + 0.6, side * EYE[1], EYE[2] - 0.25), (0.5, OPENING[1] * 1.05, 0.12)) for side in (-1, 1)))

    def nose_at(self):
        return self.head_at + HEAD * np.array([4.75, 0, -0.45]) @ self.axes

    def head(self, p):
        return HEAD * self._head(p)

    def _head(self, p):
        q = self.local(p) / HEAD
        skull = ellipsoid(q, (0, 0, 0), (4.0, 4.5, 4.1))
        cheeks = np.minimum(ellipsoid(q, (1.0, 2.7, -1.6), (2.8, 2.4, 2.3)), ellipsoid(q, (1.0, -2.7, -1.6), (2.8, 2.4, 2.3)))
        muzzle = ellipsoid(q, (3.5, 0, -1.4), (1.6, 2.1, 1.45))
        pads = np.minimum(ellipsoid(q, (3.95, 1.0, -1.65), (1.1, 1.15, 1.05)), ellipsoid(q, (3.95, -1.0, -1.65), (1.1, 1.15, 1.05)))
        bridge = cone(q, (2.6, 0, 0.7), (4.6, 0, -0.35), 1.35, 0.75)
        chin = ellipsoid(q, (2.9, 0, -3.0), (1.3, 1.35, 0.95))
        d = smin(skull, cheeks, 1.2)
        d = smin(d, smin(muzzle, pads, 0.4), 0.9)
        d = smin(d, bridge, 0.8)
        d = smin(d, chin, 0.7)
        # The eyes' openings: almond shaped, wider than they are tall. Shut, the lids are only a crease.
        for side in (-1, 1):
            if self.open:
                d = smax(d, -ellipsoid(q, (EYE[0], side * EYE[1], EYE[2]), OPENING), 0.25)
            else:
                d = smax(d, -ellipsoid(q, (EYE[0] + 0.6, side * EYE[1], EYE[2] - 0.25), (0.5, OPENING[1] * 1.05, 0.12)), 0.1)
        return d

    def ears(self, p):
        q = self.local(p) / HEAD
        d = np.full(p.shape[:-1], 1e3)
        for side in (-1, 1):
            outer = cone(q, (-0.3, side * 2.5, 2.7), (-0.6, side * 3.4, 6.5), 1.9, 0.15)
            # Hollow toward where the head looks.
            inner = cone(q, (0.32, side * 2.45, 3.1), (-0.32, side * 3.32, 6.2), 1.4, 0.04)
            d = np.minimum(d, smax(outer, -inner, 0.2))
        return HEAD * d

    def spine(self, p):
        points, radii = self.pose["spine"]
        d = np.full(p.shape[:-1], 1e3)
        for a, b, ra, rb in zip(points, points[1:], radii, radii[1:]):
            d = smin(d, cone(p, a, b, ra, rb), 2.5)
        for centre, radii_ in self.pose.get("blades", ()):
            d = smin(d, ellipsoid(p, centre, radii_), 1.5)
        return d

    def legs(self, p):
        d = np.full(p.shape[:-1], 1e3)
        for leg in self.pose["legs"]:
            joints, radii = leg["joints"], leg["radii"]
            part = np.full(p.shape[:-1], 1e3)
            for a, b, ra, rb in zip(joints, joints[1:], radii, radii[1:]):
                part = smin(part, cone(p, a, b, ra, rb), 1.0)
            if "paw" in leg:
                centre, radii_ = leg["paw"]
                part = smin(part, ellipsoid(p, centre, radii_), 0.8)
            if "thigh" in leg:
                centre, radii_ = leg["thigh"]
                part = smin(part, ellipsoid(p, centre, radii_), 1.5)
            d = np.minimum(d, part)
        return d

    def tail(self, p):
        points, (r0, r1) = self.tail_curve(), self.pose["tail_r"]
        n = len(points)
        d = np.full(p.shape[:-1], 1e3)
        for i in range(n - 1):
            d = np.minimum(d, cone(p, points[i], points[i + 1], r0 + (r1 - r0) * i / (n - 1), r0 + (r1 - r0) * (i + 1) / (n - 1)))
        return d

    def tail_curve(self, samples=40):
        c = np.asarray(self.pose["tail"], dtype=float)
        # A Catmull-Rom spline through the tail's points.
        out = []
        for i in range(len(c) - 1):
            p0, p1, p2, p3 = c[max(i - 1, 0)], c[i], c[i + 1], c[min(i + 2, len(c) - 1)]
            for t in np.linspace(0, 1, samples // (len(c) - 1), endpoint=False):
                out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t**2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t**3))
        out.append(c[-1])
        return np.array(out)

    def parts(self, p):
        """Each part's distance, in the order PARTS names them."""
        neck_a, neck_b, neck_r = self.pose["neck"]
        neck = cone(p, neck_a, neck_b, *neck_r)
        return np.stack([self.head(p), self.ears(p), neck, self.spine(p), self.legs(p), self.tail(p)])

    def field(self, p):
        head, ears, neck, spine, legs, tail = self.parts(p)
        d = smin(spine, neck, 3.0)
        d = smin(d, head, 1.6)
        d = smin(d, ears, 0.5)
        d = smin(d, legs, 1.6)
        d = smin(d, tail, 1.2)
        # It lies on the desk: flat where it touches.
        return smax(d, -(p[..., 2] - 0.25), 0.6)

    # Where each part's hair lies, and how long it is, in cm.
    LENGTHS = {"head": 0.85, "ears": 0.45, "neck": 3.0, "spine": 2.4, "legs": 1.2, "tail": 3.6}

    def flow(self, part, p, n):
        """The way the hair runs over a part, before it is laid along the skin."""
        f, r, u = self.axes
        if part == "head":
            q = self.local(p)
            # Back from the nose over the crown, and out and back across the cheeks.
            side = np.sign(q[:, 1:2]) * r
            return -f + 0.6 * side * np.clip(np.abs(q[:, 1:2]) / 3.0, 0, 1) - 0.2 * u
        if part == "ears":
            return np.broadcast_to(u, p.shape).copy()
        if part == "neck":
            return np.broadcast_to(np.array([1.0, 0.0, -1.2]), p.shape).copy()
        if part == "spine":
            # Back along the spine, from the nearest stretch of it, and down the flanks.
            points = np.asarray(self.pose["spine"][0], dtype=float)
            nearest = np.argmin(np.linalg.norm(p[:, None, :] - points[None], axis=-1), axis=1)
            back = points[np.minimum(nearest + 1, len(points) - 1)] - points[np.maximum(nearest - 1, 0)]
            back /= np.linalg.norm(back, axis=1, keepdims=True)
            return back + np.array([0, 0, -0.7]) * (1 - np.abs(n[:, 2:3]))
        if part == "legs":
            # Down each leg to its paw: from the leg's nearest joint toward its last.
            out = np.zeros_like(p)
            best = np.full(len(p), 1e9)
            for leg in self.pose["legs"]:
                joints = np.asarray(leg["joints"], dtype=float)
                down = joints[-1] - joints[0]
                down /= np.linalg.norm(down)
                dist = np.min(np.linalg.norm(p[:, None, :] - joints[None], axis=-1), axis=1)
                take = dist < best
                out[take] = down
                best = np.minimum(best, dist)
            return out
        if part == "tail":
            curve = self.tail_curve()
            nearest = np.argmin(np.linalg.norm(p[:, None, :] - curve[None], axis=-1), axis=1)
            ahead = curve[np.minimum(nearest + 1, len(curve) - 1)] - curve[np.maximum(nearest - 1, 0)]
            ahead /= np.linalg.norm(ahead, axis=1, keepdims=True)
            # A plume: the hair splays out from the tail's line as it runs along it.
            off = p - curve[nearest]
            off /= np.maximum(np.linalg.norm(off, axis=1, keepdims=True), 1e-6)
            return ahead + 0.8 * off
        raise ValueError(part)

    def pigment(self, p, part):
        """How much colour each hair carries, 0 for white to 1 for the coat's colour."""
        q = self.local(p)
        colour = np.zeros(len(p))
        # The cap: over the crown and the ears and down to the eyes, parted by a blaze that narrows up the forehead.
        cap = (q[:, 2] > -0.6 + 0.25 * np.maximum(q[:, 0] - 1.5, 0)) & (q[:, 0] < 3.4)
        blaze = (np.abs(q[:, 1]) < 0.75 + 0.22 * np.maximum(q[:, 0] - 0.5, 0) - 0.05 * q[:, 2]) & (q[:, 0] > -0.8)
        on_head = np.isin(part, ("head", "ears"))
        colour[on_head & cap & ~blaze] = 1
        colour[part == "ears"] = 1
        colour[part == "tail"] = 1
        # The root of the tail is coloured a little way up the rump.
        rump = np.asarray(self.pose["tail"][0], dtype=float)
        colour[np.linalg.norm(p - rump, axis=1) < 4.0] = 1
        for centre, radius in self.spots:
            colour[np.linalg.norm(p - np.asarray(centre), axis=1) < radius] = 1
        if self.lip:
            # A patch at the left of the upper lip.
            colour[on_head & (np.linalg.norm(q / HEAD - np.array([3.9, -1.25, -1.55]), axis=1) < 0.85)] = 1
        return colour

    def build(self, stage, name, scale):
        """The skin, the coat, the eyes, the nose and the whiskers, scaled to the desk's em, as a list of objects."""
        lo = np.asarray(self.pose["bounds"][0])
        hi = np.asarray(self.pose["bounds"][1])
        verts, quads = nets(self.field, lo, hi, STEP)
        tris = np.concatenate([quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]])
        a, b, c = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
        normals = np.cross(b - a, c - a)
        area = np.linalg.norm(normals, axis=1) / 2
        normals /= np.maximum(2 * area[:, None], 1e-9)
        objects = [self._skin(stage, name, verts, quads, scale)]

        # Roots, spread over the skin by area.
        count = 260_000
        pick = self.rng.choice(len(tris), size=count, p=area / area.sum())
        w = self.rng.random((count, 2))
        flip = w.sum(1) > 1
        w[flip] = 1 - w[flip]
        roots = a[pick] + w[:, :1] * (b[pick] - a[pick]) + w[:, 1:] * (c[pick] - a[pick])
        n = normals[pick]
        # Make sure the normal points out.
        e = 0.05
        outward = self.field(roots + n * e) > self.field(roots - n * e)
        n[~outward] *= -1
        names = ("head", "ears", "neck", "spine", "legs", "tail")
        part = np.array(names)[np.argmin(self.parts(roots), axis=0)]
        # No hair on the eyes, the nose leather or the hollow of the ears.
        bare = np.zeros(count, dtype=bool)
        bare |= self.openings(roots) < (0.12 if self.open else 0.0)
        bare |= np.linalg.norm(roots - self.nose_at(), axis=1) < 0.7
        inside_ear = (part == "ears") & ((n @ self.axes[0]) > 0.35)
        bare |= inside_ear & (self.rng.random(count) > 0.45)
        keep = ~bare
        roots, n, part, inside_ear = roots[keep], n[keep], part[keep], inside_ear[keep]
        objects.append(self._coat(stage, name, roots, n, part, scale, inside_ear))
        if self.open:
            objects += self._eyes(stage, name, scale)
        objects += self._whiskers(stage, name, scale)
        return objects

    def _skin(self, stage, name, verts, quads, scale):
        data = bpy.data.meshes.new(f"{name}-skin")
        data.from_pydata(verts.tolist(), [], quads.tolist())
        data.validate()
        data.polygons.foreach_set("use_smooth", [True] * len(data.polygons))
        # Pink where it is bare: the nose, the insides of the ears; the rest under the coat a pale skin.
        centres = np.empty(len(data.polygons) * 3)
        data.polygons.foreach_get("center", centres)
        centres = centres.reshape(-1, 3)
        q = self.local(centres)
        pink = (np.linalg.norm(centres - self.nose_at(), axis=1) < 0.9) | ((q[:, 2] > 2.4 * HEAD) & (q[:, 0] > -1.2) & (np.abs(q[:, 1]) > 1.5 * HEAD))
        rim = self.openings(centres) < (0.25 if self.open else 0.06)
        skin = bpy.data.materials.new(f"{name}-skin")
        skin.use_nodes = True
        skin.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*linear(SKIN), 1)
        skin.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55
        skin.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.3
        bare = bpy.data.materials.new(f"{name}-bare")
        bare.use_nodes = True
        bare.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*linear(PINK), 1)
        bare.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.4
        bare.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.4
        lid = bpy.data.materials.new(f"{name}-lid")
        lid.use_nodes = True
        lid.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*linear(LID), 1)
        lid.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.3
        data.materials.append(skin)
        data.materials.append(bare)
        data.materials.append(lid)
        data.polygons.foreach_set("material_index", np.where(rim, 2, pink.astype(np.int32)).astype(np.int32))
        obj = stage.add(f"{name}-skin", data)
        obj.scale = (scale,) * 3
        # The nose leather, a little proud of the skin.
        nose = self._sphere(f"{name}-nose", self.nose_at() + 0.05 * self.axes[0], (0.3, 0.5, 0.32), NOSE, 0.35)
        nose.parent = obj
        return obj

    def _sphere(self, name, centre, radii, colour, rough, coat=0.0):
        data = bpy.data.meshes.new(name)
        import bmesh

        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
        bm.to_mesh(data)
        bm.free()
        data.polygons.foreach_set("use_smooth", [True] * len(data.polygons))
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        shader = material.node_tree.nodes["Principled BSDF"]
        shader.inputs["Base Color"].default_value = (*linear(colour), 1)
        shader.inputs["Roughness"].default_value = rough
        shader.inputs["Coat Weight"].default_value = coat
        data.materials.append(material)
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        basis = Matrix([Vector(row) for row in self.axes]).transposed()
        obj.matrix_world = Matrix.Translation(Vector(centre)) @ basis.to_4x4() @ Matrix.Diagonal((*radii, 1))
        return obj

    def _coat(self, stage, name, roots, n, part, scale, tufts):
        count = len(roots)
        length = np.array([self.LENGTHS[k] for k in part]) * (0.65 + 0.6 * self.rng.random(count))
        # The white furnishings inside the ears are long.
        length[tufts] = 1.2 * (0.6 + 0.6 * self.rng.random(tufts.sum()))
        flow = np.zeros_like(roots)
        for k in self.LENGTHS:
            pick = part == k
            if pick.any():
                flow[pick] = self.flow(k, roots[pick], n[pick])
        flow += 0.25 * self.rng.normal(size=flow.shape)
        along = flow - (flow * n).sum(1, keepdims=True) * n
        along /= np.maximum(np.linalg.norm(along, axis=1, keepdims=True), 1e-6)

        segments = 5
        points = np.empty((count, segments + 1, 3))
        points[:, 0] = roots - 0.05 * n
        lift = 0.55 + 0.25 * self.rng.random((count, 1))
        wave = self.rng.normal(size=(count, 3)) * 0.12
        for k in range(1, segments + 1):
            t = k / segments
            # Out of the skin, then lying down along the coat, and a touch of gravity.
            d = n * lift * (1 - t) ** 1.5 + along * (0.4 + t) + wave * math.sin(3 * t) + np.array([0, 0, -0.15]) * t
            d /= np.linalg.norm(d, axis=1, keepdims=True)
            points[:, k] = points[:, k - 1] + d * (length / segments)[:, None]

        # Clumps: each hair's tip drawn toward its clump's middle hair.
        tree = KDTree(count // 70)
        seeds = self.rng.choice(count, size=count // 70, replace=False)
        for i, s in enumerate(seeds):
            tree.insert(roots[s], i)
        tree.balance()
        guide = np.array([seeds[tree.find(r)[1]] for r in roots])
        share = (np.linspace(0, 1, segments + 1) ** 1.2)[None, :, None] * (0.6 + 0.3 * self.rng.random((count, 1, 1)))
        points = points + share * (points[guide] - points[guide][:, :1] + points[:, :1] - points)

        curves = bpy.data.hair_curves.new(f"{name}-coat")
        curves.add_curves([segments + 1] * count)
        curves.attributes["position"].data.foreach_set("vector", points.reshape(-1).astype(np.float32))
        radius = curves.attributes.new("radius", "FLOAT", "POINT")
        taper = np.linspace(1.0, 0.25, segments + 1)[None, :] * 0.02 * (0.8 + 0.4 * self.rng.random((count, 1)))
        radius.data.foreach_set("value", taper.reshape(-1).astype(np.float32))
        colour = self.pigment(roots, part)
        colour[tufts] = 0
        melanin = WHITE[0] + colour * (self.coat[0] - WHITE[0])
        redness = WHITE[1] + colour * (self.coat[1] - WHITE[1])
        # Each hair a little different, and the coloured ones paler at their tips toward the white.
        melanin *= 0.8 + 0.4 * self.rng.random(count)
        for key, values in (("melanin", melanin), ("redness", redness)):
            layer = curves.attributes.new(key, "FLOAT", "CURVE")
            layer.data.foreach_set("value", values.astype(np.float32))
        curves.materials.append(self._hair_material(name))
        obj = stage.add(f"{name}-coat", curves)
        obj.scale = (scale,) * 3
        return obj

    def _hair_material(self, name):
        material = bpy.data.materials.new(f"{name}-hair")
        material.use_nodes = True
        nodes, links = material.node_tree.nodes, material.node_tree.links
        nodes.clear()
        hair = nodes.new("ShaderNodeBsdfHairPrincipled")
        hair.parametrization = "MELANIN"
        hair.inputs["Roughness"].default_value = 0.32
        hair.inputs["Radial Roughness"].default_value = 0.35
        hair.inputs["Coat"].default_value = 0.15
        hair.inputs["Random Roughness"].default_value = 0.2
        hair.inputs["Random Color"].default_value = 0.08
        for key, socket in (("melanin", "Melanin"), ("redness", "Melanin Redness")):
            attribute = nodes.new("ShaderNodeAttribute")
            attribute.attribute_name = key
            links.new(attribute.outputs["Fac"], hair.inputs[socket])
        out = nodes.new("ShaderNodeOutputMaterial")
        links.new(hair.outputs[0], out.inputs["Surface"])
        return material

    def _eyes(self, stage, name, scale):
        objects = []
        f, r, u = self.axes
        for (centre, iris), side in zip(zip(self.eye_centres(), self.irises), (-1, 1)):
            # Each eye looks a little out to its own side.
            gaze = (f + 0.22 * side * r) / np.linalg.norm(f + 0.22 * side * r)
            right = np.cross(u, gaze)
            right /= np.linalg.norm(right)
            up = np.cross(gaze, right)
            data = bpy.data.meshes.new(f"{name}-eye")
            import bmesh

            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=EYEBALL[1] * HEAD)
            bm.to_mesh(data)
            bm.free()
            data.polygons.foreach_set("use_smooth", [True] * len(data.polygons))
            data.materials.append(self._eye_material(name, iris))
            obj = stage.add(f"{name}-eye", data)
            basis = Matrix([Vector(gaze), Vector(right), Vector(up)]).transposed().to_4x4()
            obj.matrix_world = Matrix.Diagonal((scale, scale, scale, 1)) @ Matrix.Translation(Vector(centre)) @ basis
            objects.append(obj)
        return objects

    def _eye_material(self, name, iris):
        """In the eye's own axes, x along its gaze, z up: an iris round the gaze with a slit pupil up it, rings of
        colour that darken to its rim, and the eye's clear front over it."""
        material = bpy.data.materials.new(f"{name}-iris")
        material.use_nodes = True
        nodes, links = material.node_tree.nodes, material.node_tree.links
        shader = nodes["Principled BSDF"]
        place = nodes.new("ShaderNodeTexCoord")
        split = nodes.new("ShaderNodeSeparateXYZ")
        links.new(place.outputs["Object"], split.inputs[0])

        def op(kind, a, b=None):
            node = nodes.new("ShaderNodeMath")
            node.operation = kind
            for socket, value in zip(node.inputs, (a, b)):
                if value is None:
                    continue
                if isinstance(value, (int, float)):
                    socket.default_value = value
                else:
                    links.new(value, socket)
            return node.outputs[0]

        y, z = op("MULTIPLY", split.outputs["Y"], 1 / (EYEBALL[1] * HEAD)), op("MULTIPLY", split.outputs["Z"], 1 / (EYEBALL[1] * HEAD))
        radial = op("SQRT", op("ADD", op("MULTIPLY", y, y), op("MULTIPLY", z, z)))
        # The slit: narrow across, long up and down, a soft edge.
        slit = op("ADD", op("MULTIPLY", op("ABSOLUTE", y), 1 / 0.13), op("MULTIPLY", op("ABSOLUTE", z), 1 / 0.75))
        pupil = op("SUBTRACT", 1.0, op("MINIMUM", op("MAXIMUM", op("MULTIPLY", op("SUBTRACT", slit, 0.85), 5.0), 0.0), 1.0))
        rim = op("MINIMUM", op("MAXIMUM", op("MULTIPLY", op("SUBTRACT", radial, 0.55), 6.0), 0.0), 1.0)
        streaks = nodes.new("ShaderNodeTexNoise")
        streaks.inputs["Scale"].default_value = 18.0
        streaks.inputs["Detail"].default_value = 6.0
        links.new(place.outputs["Object"], streaks.inputs["Vector"])
        colour = nodes.new("ShaderNodeMix")
        colour.data_type = "RGBA"
        colour.inputs[6].default_value = (*linear(iris), 1)
        colour.inputs[7].default_value = (*(0.35 * np.array(linear(iris))), 1)
        links.new(op("ADD", op("MULTIPLY", rim, 0.8), op("MULTIPLY", streaks.outputs["Fac"], 0.35)), colour.inputs[0])
        dark = nodes.new("ShaderNodeMix")
        dark.data_type = "RGBA"
        dark.inputs[7].default_value = (0.004, 0.003, 0.003, 1)
        links.new(colour.outputs[2], dark.inputs[6])
        links.new(pupil, dark.inputs[0])
        links.new(dark.outputs[2], shader.inputs["Base Color"])
        shader.inputs["Roughness"].default_value = 0.45
        shader.inputs["Coat Weight"].default_value = 1.0
        shader.inputs["Coat Roughness"].default_value = 0.02
        shader.inputs["Coat IOR"].default_value = 1.38
        return material

    def _whiskers(self, stage, name, scale):
        f, r, u = self.axes
        count = 0
        curves_points = []
        for side in (-1, 1):
            for i in range(9):
                base = self.head_at + HEAD * np.array([4.1, side * (0.8 + 0.12 * i), -1.4 - 0.12 * (i % 3)]) @ self.axes
                out = r * side * (0.9 + 0.1 * self.rng.random()) + f * (0.2 + 0.25 * self.rng.random()) - u * (0.1 + 0.2 * self.rng.random())
                out /= np.linalg.norm(out)
                droop = -u * 0.2 - f * 0.15
                length = 5.5 + 2.0 * self.rng.random()
                pts = [base + out * length * t + droop * length * t * t for t in np.linspace(0, 1, 6)]
                curves_points.append(pts)
                count += 1
        curves = bpy.data.hair_curves.new(f"{name}-whiskers")
        curves.add_curves([6] * count)
        curves.attributes["position"].data.foreach_set("vector", np.asarray(curves_points).reshape(-1).astype(np.float32))
        radius = curves.attributes.new("radius", "FLOAT", "POINT")
        radius.data.foreach_set("value", np.tile(np.linspace(0.03, 0.006, 6), count).astype(np.float32))
        for key, value in (("melanin", 0.0), ("redness", 0.0)):
            layer = curves.attributes.new(key, "FLOAT", "CURVE")
            layer.data.foreach_set("value", np.full(count, value, dtype=np.float32))
        curves.materials.append(self._hair_material(f"{name}-whisker"))
        obj = stage.add(f"{name}-whiskers", curves)
        obj.scale = (scale,) * 3
        return [obj]


# Poses, in cm. Each: the spine from the neck back to the rump with its radii, the neck, the head's centre and which way
# it looks and is up, the legs as joints and radii with paws and thighs, the tail's points and radii, and the box the
# cat lies in.
POSES = {
    # Lying as a sphinx, forepaws out in front, hind legs folded at its sides, the tail along its left flank, and its
    # head raised and turned up to look at the lens.
    "sphinx": {
        "spine": (((2, 0, 10.2), (7, 0, 9.2), (13, 0, 8.6), (18, 0, 8.2), (21.5, 0, 7.0)), (5.4, 6.2, 5.9, 6.1, 4.8)),
        "blades": (((5.0, 2.5, 13.2), (3.4, 2.1, 2.0)), ((5.0, -2.5, 13.2), (3.4, 2.1, 2.0))),
        "neck": ((2.5, 0, 10.8), (-2.5, 0, 14.8), (4.8, 4.0)),
        "head": (-4.0, 0, 18.0),
        "look": ((-0.42, 0.08, 0.9), (0.9, 0, 0.42), 9.0),
        "legs": [
            {"joints": ((2.5, s * 4.2, 6.5), (-2.5, s * 3.4, 2.6), (-5.2, s * 2.9, 1.8)), "radii": (2.5, 1.8, 1.45), "paw": ((-6.6, s * 2.7, 1.4), (2.3, 1.7, 1.3))}
            for s in (-1, 1)
        ]
        + [
            {"joints": ((18, s * 4.8, 6.8), (13.5, s * 6.2, 2.0)), "radii": (2.6, 1.6), "thigh": ((18.0, s * 5.4, 6.0), (5.0, 3.1, 4.8)), "paw": ((11.0, s * 6.4, 1.4), (3.0, 1.7, 1.35))}
            for s in (-1, 1)
        ],
        "tail": ((23.0, 0, 5.2), (25.5, -3.3, 1.8), (22.0, -8.0, 1.5), (14.0, -9.0, 1.4), (8.0, -8.0, 1.4)),
        "tail_r": (1.7, 1.2),
        "bounds": ((-16, -13, -1), (28, 13, 24)),
    },
    # Sitting up, forepaws together, the tail round its feet, looking straight up at the lens.
    "sit": {
        "spine": (((0, 0, 21), (1.5, 0, 16), (4, 0, 10), (6.5, 0, 5.5)), (4.6, 6.0, 6.6, 6.4)),
        "neck": ((0.5, 0, 20), (-0.5, 0, 24), (4.4, 3.8)),
        "head": (-1.0, 0, 27.5),
        "look": ((-0.25, 0.06, 0.97), (0.97, 0, 0.25), -6.0),
        "legs": [
            {"joints": ((0.5, s * 3.2, 15), (-1.2, s * 2.9, 7), (-2.3, s * 2.8, 1.8)), "radii": (2.4, 1.7, 1.45), "paw": ((-3.8, s * 2.7, 1.3), (2.3, 1.7, 1.3))}
            for s in (-1, 1)
        ]
        + [
            {"joints": ((5, s * 5.0, 5), (0, s * 4.6, 1.6)), "radii": (2.6, 1.6), "thigh": ((5.5, s * 5.2, 5.0), (5.5, 3.0, 5.0)), "paw": ((-1.5, s * 4.7, 1.3), (3.0, 1.7, 1.3))}
            for s in (-1, 1)
        ],
        "tail": ((8.0, 0, 2.5), (9.0, -5.0, 1.4), (4.0, -8.5, 1.4), (-2.0, -8.0, 1.4), (-6.0, -5.5, 1.4)),
        "tail_r": (1.7, 1.2),
        "bounds": ((-13, -12, -1), (15, 12, 35)),
    },
    # Curled up asleep on its side, its head on its forepaws, its eyes shut, the tail wrapped round to its nose.
    "curl": {
        "spine": (
            tuple((7.2 * math.cos(math.radians(a)), 7.2 * math.sin(math.radians(a)), z) for a, z in ((140, 5.6), (90, 6.0), (30, 6.2), (-30, 6.0), (-90, 5.2))),
            (5.0, 6.0, 6.3, 6.0, 5.0),
        ),
        "neck": ((-5.5, 4.6, 5.6), (-8.5, 1.5, 5.6), (4.6, 4.0)),
        "head": (-9.6, -1.6, 5.4),
        "look": ((0.25, -0.55, 0.8), (-0.85, 0.35, 0.3), 0.0),
        "open": False,
        "legs": [
            {"joints": ((-6.0, 3.0, 3.0), (-6.5, -3.0, 1.6)), "radii": (2.2, 1.5), "paw": ((-6.0, -5.6, 1.4), (2.2, 1.7, 1.3))},
            {"joints": ((-4.0, 4.0, 2.4), (-3.5, -2.0, 1.5)), "radii": (2.0, 1.4), "paw": ((-3.0, -4.6, 1.3), (2.1, 1.6, 1.2))},
            {"joints": ((4.0, -5.0, 5.5), (-1.5, -8.0, 1.6)), "radii": (2.6, 1.6), "thigh": ((3.6, -5.6, 5.2), (5.0, 3.3, 4.4)), "paw": ((-3.5, -8.6, 1.4), (3.0, 1.7, 1.3))},
        ],
        "tail": ((0.5, -8.0, 3.0), (-4.5, -11.0, 1.6), (-10.0, -9.5, 1.5), (-13.5, -5.5, 1.5), (-14.0, -1.0, 1.5)),
        "tail_r": (1.7, 1.2),
        "bounds": ((-19, -15, -1), (15, 15, 15)),
    },
}
