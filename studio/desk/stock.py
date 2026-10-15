"""Flat stock: paper, board, leather, sheet metal and moulded sheet.

The outline, relief and print are painted as arrays. The surface itself comes from a scanned material:
its normal map, its roughness and the unevenness of its colour. Type comes from a plate, which is the
page's own typesetting captured from the browser (see plates.mjs)."""

import os

import bpy
import numpy as np

from paint import box, cover, linear, ramp
from stage import ASSETS, PX_PER_EM

PLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plates")
# plates.mjs photographs the page at this many pixels to the em.
PLATE_PPE = 96


def drift(w, h, amount, seed):
    """A slow random wave across a sheet, so it never lies perfectly flat."""
    rng = np.random.default_rng(seed)
    waves = [(rng.uniform(0.4, 1.3), rng.uniform(0.4, 1.3), rng.uniform(0, 6.3), rng.uniform(0.4, 1)) for _ in range(4)]

    def warp(x, y):
        z = np.zeros_like(x)
        for fx, fy, phase, gain in waves:
            z += gain * np.sin(phase + 3.1416 * (fx * x / w + fy * y / h))
        return amount * z / 2

    return warp


def pixels_of(path):
    """An image file as rows from the top, values as stored."""
    image = bpy.data.images.load(path)
    cols, rows = image.size
    data = np.empty(cols * rows * 4, dtype=np.float32)
    image.pixels.foreach_get(data)
    bpy.data.images.remove(image)
    return data.reshape(rows, cols, 4)[::-1]


def fit(a, rows, cols):
    """Resample an array of rows, columns and channels to a new size, bilinear."""
    if a.shape[:2] == (rows, cols):
        return a
    ys = (np.arange(rows) + 0.5) * a.shape[0] / rows - 0.5
    xs = (np.arange(cols) + 0.5) * a.shape[1] / cols - 0.5
    y0 = np.clip(np.floor(ys).astype(int), 0, a.shape[0] - 2)
    x0 = np.clip(np.floor(xs).astype(int), 0, a.shape[1] - 2)
    fy = np.clip(ys - y0, 0, 1)[:, None, None]
    fx = np.clip(xs - x0, 0, 1)[None, :, None]
    top = a[y0][:, x0] * (1 - fx) + a[y0][:, x0 + 1] * fx
    bottom = a[y0 + 1][:, x0] * (1 - fx) + a[y0 + 1][:, x0 + 1] * fx
    return top * (1 - fy) + bottom * fy


def sample(a, xs, ys):
    """Read an array of rows, columns and channels at pixel positions that fall between its pixels, bilinear.
    Past its edges it reads as its edge."""
    xs = np.clip(np.asarray(xs, dtype=np.float64), 0, a.shape[1] - 1)
    ys = np.clip(np.asarray(ys, dtype=np.float64), 0, a.shape[0] - 1)
    x0 = np.clip(np.floor(xs).astype(int), 0, a.shape[1] - 2)
    y0 = np.clip(np.floor(ys).astype(int), 0, a.shape[0] - 2)
    fx, fy = (xs - x0)[..., None], (ys - y0)[..., None]
    top = a[y0, x0] * (1 - fx) + a[y0, x0 + 1] * fx
    bottom = a[y0 + 1, x0] * (1 - fx) + a[y0 + 1, x0 + 1] * fx
    return top * (1 - fy) + bottom * fy


class Sheet:
    def __init__(self, w, h, colour, rough=0.85, density=2):
        self.w, self.h = w, h
        self.ppe = PX_PER_EM * density
        cols, rows = round(w * self.ppe), round(h * self.ppe)
        self.X, self.Y = np.meshgrid((np.arange(cols) + 0.5) / self.ppe, (np.arange(rows) + 0.5) / self.ppe)
        self.aa = 1.5 / self.ppe
        self.sdf = box(self.X, self.Y, 0, 0, w, h)
        self.rgb = np.broadcast_to(linear(colour), (rows, cols, 3)).copy()
        self.height = np.zeros((rows, cols))
        self.rough = np.full((rows, cols), rough)
        self.metal = np.zeros((rows, cols))
        self.coat = np.zeros((rows, cols))
        self.opacity = np.ones((rows, cols))
        self.glow = np.zeros((rows, cols))

    def mask(self, d):
        return cover(d, self.aa)

    def plate(self, name, at=None, turn=0.0, pivot=(0.0, 0.0)):
        """The type for this sheet as three masks, one per ink, from studio/plates.
        A plate covers its sheet exactly, unless it was shot of a larger frame the sheet only lies in.
        Then `at` is where in that frame, in em, the sheet's own point `pivot` falls, and `turn` is how many
        degrees clockwise the sheet is turned about it."""
        inks = pixels_of(os.path.join(PLATES, f"{name}.png"))[..., :3].astype(np.float64)
        if at is None:
            inks = fit(inks, *self.height.shape)
        else:
            c, s = np.cos(np.radians(turn)), np.sin(np.radians(turn))
            dx, dy = self.X - pivot[0], self.Y - pivot[1]
            inks = sample(inks, (at[0] + dx * c - dy * s) * PLATE_PPE - 0.5, (at[1] + dx * s + dy * c) * PLATE_PPE - 0.5)
        return inks[..., 0], inks[..., 1], inks[..., 2]

    def cut(self, d):
        """Keep only what lies inside the shape."""
        self.sdf = np.maximum(self.sdf, d)

    def punch(self, d):
        """Remove the shape."""
        self.sdf = np.maximum(self.sdf, -d)

    def ink(self, m, colour, strength=1.0):
        """Print over the stock. Ink only ever darkens."""
        self.rgb *= 1 - (m * strength)[..., None] * (1 - linear(colour))

    def paint(self, m, colour):
        """Cover the stock with an opaque colour."""
        self.rgb += m[..., None] * (linear(colour) - self.rgb)

    def art(self, path, x0, y0, x1, y1, colour=None, strength=1.0, relief=0.0):
        """Print an image file inside a box given in em: in its own colours, or in one colour through its alpha.
        relief raises what is printed, for a badge that stands on the surface."""
        r0, r1, c0, c1 = (round(v * self.ppe) for v in (y0, y1, x0, x1))
        image = fit(pixels_of(path).astype(np.float64), r1 - r0, c1 - c0)
        own = np.where(image[..., :3] <= 0.04045, image[..., :3] / 12.92, ((image[..., :3] + 0.055) / 1.055) ** 2.4)
        patch = self.rgb[r0:r1, c0:c1]
        patch += image[..., 3:] * strength * ((linear(colour) if colour else own) - patch)
        self.height[r0:r1, c0:c1] += relief * image[..., 3]

    def press(self, m, depth):
        self.height -= m * depth

    def finish(self, m, rough=None, metal=None, coat=None):
        for layer, value in ((self.rough, rough), (self.metal, metal), (self.coat, coat)):
            if value is not None:
                layer += m * (value - layer)

    def soften(self, width, drop):
        """Round the cut edge over."""
        self.height -= drop * (1 - ramp(0, width, -self.sdf)) ** 2

    def chamfer(self, width, drop):
        """Cut the edge back at a flat angle, as a machine would."""
        self.height -= drop * (1 - np.clip(-self.sdf / width, 0, 1))

    def window(self, x0, y0, x1, y1):
        """Array slices covering a rectangle given in em, for work that only touches a small patch."""
        rows, cols = self.height.shape
        r0, r1 = max(0, int(y0 * self.ppe)), min(rows, int(y1 * self.ppe) + 1)
        c0, c1 = max(0, int(x0 * self.ppe)), min(cols, int(x1 * self.ppe) + 1)
        return slice(r0, r1), slice(c0, c1)

    def build(
        self,
        stage,
        name,
        thickness=0.02,
        warp=None,
        scan=None,
        scan_size=8.0,
        scan_normal=1.0,
        scan_rough=1.0,
        scan_colour=0.0,
        wear=(),
        fibre=0.0,
        fibre_scale=26.0,
        fibre_stretch=1.0,
        mottle=0.0,
        sheen=0.0,
        specular=0.5,
        coat_rough=0.08,
        subsurface=0.0,
        brushed=0.0,
        at=(0.0, 0.0),
        step=0.25,
        solid=True,
        edge=None,
    ):
        """Lay the sheet on the stage, its top left corner at `at`.
        scan names an ambientCG material; one tile of it covers scan_size em.
        wear is a list of (imperfection map, tile size in em, roughness added, depth of the mark).
        step is the pitch of the mesh in em. A sheet whose warp is a moulded shape wants it fine.
        solid gives the sheet its body: the mesh is cut to the sheet's outline, and walls and an underside take it
        down to the surface it lies on, so it rests on it and throws its shadow from where it touches.
        edge shapes those walls, as a dict:
          round: how far in from the outline the top and the underside turn over, in em. The wall bulges out
            to the outline halfway down, as a sanded and burnished leather edge does, or card folded over.
          square: above 1 the round flattens towards a wall with rounded corners.
          skive: (width, drop): the top thins down to the edge over the last width em, as leather skived for
            an edge does.
          paint: the colour of the edge, its roughness and its gloss coat, as (colour, rough, coat). Without it
            the edge carries the print, as a fold does."""
        rows, cols = self.height.shape
        alpha = cover(self.sdf, self.aa) * self.opacity

        def image(label, channels):
            data = np.dstack(channels)[::-1].astype(np.float32)
            img = bpy.data.images.new(f"{name}-{label}", cols, rows, alpha=True, float_buffer=True)
            img.colorspace_settings.name = "Non-Color"
            img.alpha_mode = "CHANNEL_PACKED"
            img.pixels.foreach_set(data.ravel())
            img.pack()
            return img

        colour = image("colour", (self.rgb[..., 0], self.rgb[..., 1], self.rgb[..., 2], alpha))
        data = image("data", (self.height, self.rough, self.metal, self.coat))

        nx, ny = max(2, round(self.w / step) + 1), max(2, round(self.h / step) + 1)
        gx, gy = np.meshgrid(np.linspace(0, self.w, nx), np.linspace(0, self.h, ny))
        gz = warp(gx, gy) if warp else np.zeros_like(gx)
        base = thickness - gz.min()
        # Height of the sheet at a point, for anything that has to sit on it.
        self.z = lambda x, y: float(warp(np.float64(x), np.float64(y)) + base) if warp else thickness
        index = np.arange(nx * ny).reshape(ny, nx)
        faces = np.column_stack(
            (index[1:, :-1].ravel(), index[1:, 1:].ravel(), index[:-1, 1:].ravel(), index[:-1, :-1].ravel())
        )
        px, py = gx.ravel().copy(), gy.ravel().copy()
        walls = np.zeros((0, 4), dtype=np.int64)
        edge = edge or {}
        inset = edge.get("round", 0.0)
        if solid and thickness > 0.005:
            px, py, faces, walls = self._outline(px, py, faces, step, inset)
        pz = (warp(px, py) if warp else np.zeros_like(px)) + base
        width, drop = edge.get("skive", (0.0, 0.0))
        if drop:
            pz -= drop * (1 - np.clip((-self._sdf_at(px, py) - inset) / width, 0, 1)) ** 2
        verts = np.column_stack((px + at[0], -(py + at[1]), pz))
        top = len(faces)
        # Where each vertex reads the sheet's maps.
        ux, uy = px, py
        if len(walls):
            # The underside lies on the surface, and the walls join it to the top along the outline.
            count = len(verts)
            verts = np.vstack((verts, np.column_stack((verts[:, :2], np.full(count, 0.002)))))
            ux, uy = np.concatenate((px, px)), np.concatenate((py, py))
            rings = [np.arange(count), np.arange(count) + count]
            if inset:
                # Rings of the wall between them, each a step further round the edge's profile.
                rim = np.unique(walls)
                e = 0.01
                nx_ = self._sdf_at(px[rim] + e, py[rim]) - self._sdf_at(px[rim] - e, py[rim])
                ny_ = self._sdf_at(px[rim], py[rim] + e) - self._sdf_at(px[rim], py[rim] - e)
                length = np.maximum(np.hypot(nx_, ny_), 1e-9)
                nx_, ny_ = nx_ / length, ny_ / length
                power = 2 / edge.get("square", 1.0)
                high, low = pz[rim], 0.002
                middle = []
                steps = 12
                for k in range(1, steps):
                    turn = np.pi * k / steps
                    out = inset * np.sin(turn) ** power
                    rise = np.sign(np.cos(turn)) * np.abs(np.cos(turn)) ** power
                    ring = np.full(count, -1)
                    ring[rim] = len(verts) + np.arange(len(rim))
                    x, y = px[rim] + out * nx_, py[rim] + out * ny_
                    z = low + (high - low) * (1 + rise) / 2
                    verts = np.vstack((verts, np.column_stack((x + at[0], -(y + at[1]), z))))
                    # The edge reads the maps just inside the outline, where the print is whole.
                    ux, uy = np.concatenate((ux, px[rim])), np.concatenate((uy, py[rim]))
                    middle.append(ring)
                rings = [rings[0], *middle, rings[1]]
            sides = [np.column_stack((a[walls[:, 1]], a[walls[:, 0]], b[walls[:, 0]], b[walls[:, 1]])) for a, b in zip(rings, rings[1:])]
            faces = np.vstack((faces, faces[:, ::-1] + count, *sides))
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(verts.tolist(), [], faces.tolist())
        uv = np.column_stack((np.clip(ux, 0, self.w) / self.w, 1 - np.clip(uy, 0, self.h) / self.h))
        loops = np.empty(len(mesh.loops), dtype=np.int32)
        mesh.loops.foreach_get("vertex_index", loops)
        mesh.uv_layers.new().data.foreach_set("uv", uv[loops].ravel())
        # The top is smooth. A square wall meets it and the underside at a sharp edge; a rounded one is smooth.
        under = top if len(walls) else 0
        smooth = [True] * top + [False] * under + [bool(inset)] * (len(faces) - top - under)
        mesh.polygons.foreach_set("use_smooth", smooth)

        material = bpy.data.materials.new(name)
        material.use_nodes = True
        nodes, links = material.node_tree.nodes, material.node_tree.links
        shader = nodes["Principled BSDF"]
        place = nodes.new("ShaderNodeTexCoord")

        def math(op, a, b=None):
            node = nodes.new("ShaderNodeMath")
            node.operation = op
            for socket, value in zip(node.inputs, (a, b)):
                if value is None:
                    continue
                if isinstance(value, (int, float)):
                    socket.default_value = value
                else:
                    links.new(value, socket)
            return node.outputs[0]

        def texture(img):
            node = nodes.new("ShaderNodeTexImage")
            node.image = img
            node.interpolation = "Cubic"
            node.extension = "EXTEND"
            return node

        def tiled(asset, kind, size, shift=0.0):
            """One map of a scanned material, repeating every `size` em. Returns the node and the map's mean value."""
            path = os.path.join(ASSETS, asset, f"{asset}_1K-JPG_{kind}.jpg")
            node = nodes.new("ShaderNodeTexImage")
            node.image = bpy.data.images.load(path)
            node.image.colorspace_settings.name = "Non-Color"
            mapping = nodes.new("ShaderNodeMapping")
            mapping.inputs["Scale"].default_value = (1 / size, 1 / size, 1)
            mapping.inputs["Location"].default_value = (shift, shift * 0.37, 0)
            links.new(place.outputs["Object"], mapping.inputs["Vector"])
            links.new(mapping.outputs["Vector"], node.inputs["Vector"])
            return node, float(pixels_of(path)[::8, ::8, 0].mean())

        def noise(scale, stretch=1.0, detail=4.0, roughness=0.6):
            mapping = nodes.new("ShaderNodeMapping")
            mapping.inputs["Scale"].default_value = (1 / stretch, 1, 1)
            node = nodes.new("ShaderNodeTexNoise")
            node.inputs["Scale"].default_value = scale
            node.inputs["Detail"].default_value = detail
            node.inputs["Roughness"].default_value = roughness
            links.new(place.outputs["Object"], mapping.inputs["Vector"])
            links.new(mapping.outputs["Vector"], node.inputs["Vector"])
            return node.outputs[0]

        inked, packed = texture(colour), texture(data)
        split = nodes.new("ShaderNodeSeparateColor")
        links.new(packed.outputs["Color"], split.inputs["Color"])
        tone = None
        rough = split.outputs["Green"]
        normal = None

        if scan:
            bumps, _ = tiled(scan, "NormalGL", scan_size)
            relief = nodes.new("ShaderNodeNormalMap")
            relief.inputs["Strength"].default_value = scan_normal
            links.new(bumps.outputs["Color"], relief.inputs["Color"])
            normal = relief.outputs["Normal"]
            grain, mean = tiled(scan, "Roughness", scan_size)
            rough = math("ADD", rough, math("MULTIPLY", math("SUBTRACT", grain.outputs["Color"], mean), scan_rough))
            if scan_colour:
                shade, mean = tiled(scan, "Color", scan_size)
                uneven = math("SUBTRACT", math("DIVIDE", shade.outputs["Color"], mean), 1.0)
                tone = math("ADD", math("MULTIPLY", uneven, scan_colour), 1.0)

        # Height: the painted relief, and fibre where the stock has it.
        height = split.outputs["Red"]
        if fibre:
            height = math("ADD", height, math("MULTIPLY", noise(fibre_scale, fibre_stretch), fibre))
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Distance"].default_value = 1.0
        links.new(height, bump.inputs["Height"])
        if normal:
            links.new(normal, bump.inputs["Normal"])
        normal = bump.outputs["Normal"]

        # Wear: hairline scratches and the dull patches hands leave. It changes the shine, never the colour.
        for i, (asset, size, dull, depth) in enumerate(wear):
            marks, _ = tiled(asset, "Color", size, shift=0.31 * (i + 1))
            rough = math("ADD", rough, math("MULTIPLY", marks.outputs["Color"], dull))
            if depth:
                scratch = nodes.new("ShaderNodeBump")
                scratch.inputs["Distance"].default_value = 1.0
                links.new(math("MULTIPLY", marks.outputs["Color"], -depth), scratch.inputs["Height"])
                links.new(normal, scratch.inputs["Normal"])
                normal = scratch.outputs["Normal"]

        if mottle:
            cloudy = math("ADD", math("MULTIPLY", math("SUBTRACT", noise(1.6, 1.0, 5.0, 0.7), 0.5), mottle), 1.0)
            tone = math("MULTIPLY", tone, cloudy) if tone else cloudy
        if tone:
            toned = nodes.new("ShaderNodeVectorMath")
            toned.operation = "SCALE"
            links.new(inked.outputs["Color"], toned.inputs[0])
            links.new(tone, toned.inputs["Scale"])
            links.new(toned.outputs[0], shader.inputs["Base Color"])
        else:
            links.new(inked.outputs["Color"], shader.inputs["Base Color"])

        links.new(inked.outputs["Alpha"], shader.inputs["Alpha"])
        links.new(math("MAXIMUM", math("MINIMUM", rough, 1.0), 0.03), shader.inputs["Roughness"])
        links.new(split.outputs["Blue"], shader.inputs["Metallic"])
        links.new(packed.outputs["Alpha"], shader.inputs["Coat Weight"])
        links.new(normal, shader.inputs["Normal"])
        links.new(normal, shader.inputs["Coat Normal"])
        shader.inputs["Coat Roughness"].default_value = coat_rough
        shader.inputs["Sheen Weight"].default_value = sheen
        shader.inputs["Sheen Roughness"].default_value = 0.5
        shader.inputs["Specular IOR Level"].default_value = specular
        shader.inputs["Subsurface Weight"].default_value = subsurface
        if self.glow.any():
            lit = texture(image("glow", (self.glow, self.glow, self.glow, np.ones_like(self.glow))))
            links.new(lit.outputs["Color"], shader.inputs["Emission Color"])
            shader.inputs["Emission Strength"].default_value = 1.0
        if brushed:
            # Brushing runs along the sheet, so the highlight smears across it.
            along = nodes.new("ShaderNodeTangent")
            along.direction_type = "UV_MAP"
            links.new(along.outputs[0], shader.inputs["Tangent"])
            shader.inputs["Anisotropic"].default_value = brushed
        mesh.materials.append(material)
        if len(faces) > top and not (inset and "paint" not in edge):
            # The walls and underside are the stock's cut edge: unless painted, its colour just inside the outline.
            if "paint" in edge:
                tint, finish, gloss = edge["paint"]
                tone = linear(tint)
            else:
                near = (self.sdf > -0.15) & (self.sdf < -0.03)
                tone = 0.8 * (np.median(self.rgb[near], axis=0) if near.any() else self.rgb.reshape(-1, 3).mean(axis=0))
                finish, gloss = 0.7, 0.0
            cut = bpy.data.materials.new(f"{name}-edge")
            cut.use_nodes = True
            tree = cut.node_tree
            body = tree.nodes["Principled BSDF"]
            body.inputs["Base Color"].default_value = (*tone, 1)
            body.inputs["Roughness"].default_value = finish
            body.inputs["Coat Weight"].default_value = gloss
            body.inputs["Coat Roughness"].default_value = 0.2
            if "paint" in edge:
                # Edge paint goes on in coats, each sanded back: it lies a little uneven along the edge.
                ripple = tree.nodes.new("ShaderNodeTexNoise")
                ripple.inputs["Scale"].default_value = 9.0
                ripple.inputs["Detail"].default_value = 6.0
                lumps = tree.nodes.new("ShaderNodeBump")
                lumps.inputs["Strength"].default_value = 0.25
                lumps.inputs["Distance"].default_value = 0.01
                tree.links.new(ripple.outputs[0], lumps.inputs["Height"])
                tree.links.new(lumps.outputs["Normal"], body.inputs["Normal"])
                tree.links.new(lumps.outputs["Normal"], body.inputs["Coat Normal"])
            mesh.materials.append(cut)
            mesh.polygons.foreach_set("material_index", [0] * top + [1] * (len(faces) - top))
        return stage.add(name, mesh)

    def _sdf_at(self, x, y):
        """The outline's distance field at points of the sheet, read between its pixels."""
        rows, cols = self.sdf.shape
        fx = np.clip(x * self.ppe - 0.5, 0, cols - 1.001)
        fy = np.clip(y * self.ppe - 0.5, 0, rows - 1.001)
        x0, y0 = fx.astype(int), fy.astype(int)
        tx, ty = fx - x0, fy - y0
        f = self.sdf
        return (f[y0, x0] * (1 - tx) + f[y0, x0 + 1] * tx) * (1 - ty) + (f[y0 + 1, x0] * (1 - tx) + f[y0 + 1, x0 + 1] * tx) * ty

    def _outline(self, px, py, faces, step, inset=0.0):
        """Cut the mesh to the outline, or to a line inset inside it: drop the faces wholly outside it and draw the
        vertices round its edge onto it. Returns the points, the faces kept, and the outline as edges, each wound
        with the sheet on its left."""
        d = self._sdf_at(px, py) + inset
        keep = (d[faces] < 0).any(axis=1)
        faces = faces[keep]
        edges = np.concatenate([faces[:, [i, (i + 1) % 4]] for i in range(4)])
        key = np.sort(edges, axis=1)
        _, first, counts = np.unique(key, axis=0, return_index=True, return_counts=True)
        walls = edges[first[counts == 1]]
        rim = np.unique(walls)
        x, y = px[rim].copy(), py[rim].copy()
        e = 0.01
        for _ in range(6):
            f = self._sdf_at(x, y) + inset
            gxd = (self._sdf_at(x + e, y) - self._sdf_at(x - e, y)) / (2 * e)
            gyd = (self._sdf_at(x, y + e) - self._sdf_at(x, y - e)) / (2 * e)
            g2 = np.maximum(gxd * gxd + gyd * gyd, 1e-6)
            mx, my = -f * gxd / g2, -f * gyd / g2
            reach = np.hypot(mx, my)
            scale = np.minimum(1.0, 0.75 * step / np.maximum(reach, 1e-9))
            x, y = x + mx * scale, y + my * scale
        px, py = px.copy(), py.copy()
        px[rim], py[rim] = np.clip(x, 0, self.w), np.clip(y, 0, self.h)
        used = np.unique(faces)
        remap = np.full(len(px), -1)
        remap[used] = np.arange(len(used))
        return px[used], py[used], remap[faces], remap[walls]
