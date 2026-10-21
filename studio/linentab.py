"""The linen strip's tab, cut from its cloth as the strip's edge is: the snipped cut, the yarn ends it leaves and the
shadow it all leaves on the letter's paper, for SiteShell to cut the tab with and lay past it. Run from the repository
root:

    blender -b --factory-startup -P studio/linentab.py -- [--samples 1024] [--proof DIR]

The strip's edge is linen.py's Fray. Its tab (SiteShell's slot 1) is cut out of the same cloth with the same
scissors: along its outline (SiteShell's tabOutline) the blades go in snips, each a little off the last, and every
yarn the cut crosses is left with its end tufting out of it, the wefts across its straight sides and the warps out
of its slanting top and foot, now and then one standing out further, with stray fibres lying off it. The outline
eases back into the strip's own cut where the tab's joins meet it, so the strip's fray runs on into the tab's.

It is rendered as linen.py's shadow() renders the strip's edge, over the tab and SPAN px of the strip's edge above
and below it, with the strip's own fray there too, so its render hands over to the strip's without a seam. Writes,
for each layout, public/objects/linen-tab-edge-<layout>.png, the mask the page cuts the tab with, and
linen-tab-<layout>.png, the yarns over the shadow, both in CSS px from the strip's edge mask's left (linen.py's
EDGE) and from FRAME's top.
"""

import argparse
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import linen  # noqa: E402
from linen import COLOURS, EDGE, EDGE_PITCH, GAIN, LAYERS, OPEN, PALE, PAPER, RADIUS, SHADOW_DENSITY, THICK, WARP_PITCH, Fray, linear, shoulder, yarn_material  # noqa: E402

OUT = linen.OUT
# The linen strip's tab (SiteShell's slot 1): its top and height in rem (tabTops, tabHeights over tabSpan), and each
# layout's band and how far the tab stands out (useStackMetrics).
TAB_TOP, TAB_TALL, TAB_SPAN = 9, 10, 4
LAYOUTS = {"wide": (1.9, 2.1), "phone": (1.4, 1.5)}
REM = 16
CUT = EDGE[0] - 9  # the strip's edge, in CSS px from its edge mask's left (SiteShell's FRAY_PAST)
SPAN = 40  # how far above and below the tab's joins the render runs down the strip's edge, in CSS px
PAST = 16  # how far past the tab the render runs, for its yarn ends and its shadow, in CSS px
DENSITY = 4  # pixels of the tab's mask to the CSS px, drawn finer and averaged down


def outline(layout):
    """The tab's cut, in CSS px from the strip's edge and down the strip, as points close enough to follow its
    curves: SiteShell's tabOutline, run on above and below its joins slanting back in under the strip's own cut, so
    that wherever the strip's cut lies the two meet without a step."""
    band, protrude = (v * REM for v in LAYOUTS[layout])
    top = TAB_TOP * REM
    height = TAB_TALL * (band + protrude) / TAB_SPAN
    rise, ease = protrude * 0.33, protrude * 0.2
    reach = 2 * ease
    corners = [(0, -reach), (0, 0), (protrude, rise), (protrude, height - rise), (0, height), (0, height + reach)]

    def toward(a, b):
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        return a[0] + (b[0] - a[0]) / length * ease, a[1] + (b[1] - a[1]) / length * ease

    points = [(-SPAN, -reach - SPAN), corners[0]]
    for i in range(1, len(corners) - 1):
        before, after = toward(corners[i], corners[i - 1]), toward(corners[i], corners[i + 1])
        points.append(before)
        for t in np.linspace(0, 1, 24)[1:]:
            points.append(tuple((1 - t) ** 2 * np.array(before) + 2 * (1 - t) * t * np.array(corners[i]) + t**2 * np.array(after)))
    points += [corners[-1], (-SPAN, height + reach + SPAN)]
    path = np.array(points, dtype=np.float64)
    path[:, 1] += top
    # Even steps along it.
    run = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(path, axis=0).T))])
    s = np.arange(0, run[-1], 0.1)
    path = np.stack([np.interp(s, run, path[:, 0]), np.interp(s, run, path[:, 1])], -1)
    return path, (math.floor(top - reach - SPAN), math.ceil(top + height + reach + SPAN)), protrude


def snipped(path, rng):
    """The cut as scissors leave it: in snips 12 to 30 px long, each a little off the outline and off the last."""
    run = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(path, axis=0).T))])
    corners = np.concatenate(([0.0], np.cumsum(rng.uniform(12, 30, int(run[-1] / 12) + 2))))
    off = np.clip(rng.normal(0, 0.35, len(corners)) + np.cumsum(rng.normal(0, 0.2, len(corners))) * 0.3, -0.7, 0.7)
    offset = np.interp(run, corners, off)
    tangent = np.gradient(path, axis=0)
    tangent /= np.linalg.norm(tangent, axis=1, keepdims=True)
    # Out of the cloth: right on the straight sides, up on the top slant, down on the foot.
    normal = np.stack([tangent[:, 1], -tangent[:, 0]], -1)
    return path + normal * offset[:, None], normal


def tab_strands(cut, normal, strip, rng):
    """The yarn ends the cut leaves, where the tab's cut lies past the strip's own: wefts out of its sides, warps out
    of its slants, each a tuft just past the cut and now and then one standing out further; and stray fibres."""
    out = []
    beyond = cut[:, 0] > strip(cut[:, 1]) + 0.6
    run = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(cut, axis=0).T))])

    def end(root, heading):
        """A yarn end from root, heading (unit, in the page's plane), as linen.py's Fray.strands lays a tuft."""
        if rng.random() < 0.06:
            tip = rng.uniform(1.5, 5)
            splay = min(rng.uniform(0.8, 1.8), 0.7 * tip)
        elif rng.random() < 0.55:
            tip = rng.uniform(0.1, 0.7)
            splay = tip + 0.6
        else:
            return
        s = np.arange(-1.5, tip + 1.2, 0.2)
        free = np.clip(s, 0, None)
        lean, bend = rng.normal(0, 0.08), rng.normal(0, 0.12)
        phase = rng.uniform(0, 2 * math.pi)
        top = 0.4 + THICK / 2
        z = RADIUS + (top - RADIUS) * np.exp(-free / 1.5) + 0.22 * np.sin(math.pi * free / WARP_PITCH + phase) * np.clip(free, 0, 1)
        side = np.array([-heading[1], heading[0]])
        across = lean * free + bend * free**2 / 4 + 0.12 * np.sin(math.pi * free / WARP_PITCH)
        xy = root[None, :] + s[:, None] * heading[None, :] + across[:, None] * side[None, :]
        centre = np.column_stack((xy, z))
        tone = int(rng.integers(len(COLOURS)))
        out.extend((p, r, tone) for p, r in Fray.yarn(centre, tip + 1.5, splay, rng))

    # The wefts, one a row, where the cut runs more down than across; the warps, one a column, where it runs across.
    for axis, pitch, heading_of in ((1, EDGE_PITCH, lambda n: np.array([1.0, 0.0])), (0, WARP_PITCH, lambda n: np.array([0.0, math.copysign(1.0, n[1])]))):
        crossing = beyond & (np.abs(normal[:, 1 - axis]) > 0.45)
        if not crossing.any():
            continue
        coord = cut[:, axis]
        for k in np.unique(np.floor(coord[crossing] / pitch)):
            at = (k + 0.5) * pitch + rng.normal(0, 0.12 * pitch)
            hits = np.nonzero(crossing[:-1] & ((coord[:-1] - at) * (coord[1:] - at) <= 0))[0]
            for h in hits:
                end(cut[h], heading_of(normal[h]))
    # Stray fibres off the cut, lying on the page.
    for _ in range(int((np.diff(run) * beyond[:-1]).sum() / 7)):
        i = rng.choice(np.nonzero(beyond)[0])
        x0, y0 = cut[i] - normal[i] * rng.uniform(0.3, 1.5)
        steps = np.linspace(0, 1, 30)
        angle = math.atan2(normal[i][1], normal[i][0]) + rng.normal(0, 0.7) + rng.normal(0, 1.2) * steps + np.cumsum(rng.normal(0, 0.08, 30))
        reach = rng.uniform(1.5, 6)
        px = x0 + np.cumsum(np.cos(angle)) * reach / 30
        py = y0 + np.cumsum(np.sin(angle)) * reach / 30
        pz = 0.08 + (THICK * 0.6) * np.exp(-np.hypot(px - x0, py - y0) / 0.8)
        out.append((np.column_stack((px, py, pz)), np.full(30, rng.uniform(0.04, 0.08)) * (1 - 0.5 * steps), int(rng.integers(len(COLOURS)))))
    return out


def render(layout, samples, proof):
    fray = Fray()
    rng = np.random.default_rng(91 if layout == "wide" else 93)
    path, (y0, y1), protrude = outline(layout)
    cut, normal = snipped(path, rng)
    # Into the strip's edge mask's frame: x from its left.
    cut[:, 0] += CUT
    # Down the strip, for looking the cut up row by row.
    order = np.argsort(cut[:, 1], kind="stable")
    by_row = cut[order]
    x0, x1 = -4.0, math.ceil(CUT + protrude + PAST)

    # The tab's cloth: in from its cut, finer and averaged down.
    over = 4
    d = DENSITY * over
    width = math.ceil(CUT + protrude + 2)
    X = (np.arange(width * d)[None, :] + 0.5) / d
    Y = y0 + (np.arange((y1 - y0) * DENSITY * over)[:, None] + 0.5) / d
    edge_at = np.interp(Y[:, 0], by_row[:, 1], by_row[:, 0])
    tab = (X < edge_at[:, None]).astype(np.float32)
    tab = tab.reshape(-1, over, width * DENSITY, over).mean(axis=(1, 3))
    rows = tab.shape[0]
    image = np.zeros((rows, width * DENSITY, 4), np.float32)
    image[..., :3] = 1
    image[..., 3] = tab
    write(image, f"linen-tab-edge-{layout}", proof)

    # The cloth the render casts its shadow with: the strip's and its tab's, a frame larger, as one mask.
    gy0, gy1 = y0 - 60, y1 + 60
    MX = (np.arange(round((x1 + 20) * DENSITY))[None, :] + 0.5) / DENSITY
    MY = gy0 + (np.arange(round((gy1 - gy0) * DENSITY))[:, None] + 0.5) / DENSITY
    strip = np.clip(0.5 + (fray.body(MY[:, 0])[:, None] - MX) * DENSITY, 0, 1)
    mine = np.clip(0.5 + (np.interp(MY[:, 0], by_row[:, 1], by_row[:, 0])[:, None] - MX) * DENSITY, 0, 1)
    mask = np.maximum(strip, mine).astype(np.float32)

    scene = linen.Stage(OUT, samples=samples).clear()
    scene.render.film_transparent = False
    scene.cycles.transparent_max_bounces = 4 * LAYERS
    scene.cycles.use_adaptive_sampling = False
    nodes, links = scene.world.node_tree.nodes, scene.world.node_tree.links
    coord = nodes.new("ShaderNodeTexCoord")
    turn = nodes.new("ShaderNodeMapping")
    aim = linen.BOX_ON_STAND.rotation_difference(linen.BOX_IN_ROOM) @ linen.Quaternion(linen.BOX_ON_STAND, linen.ROOM_ROLL)
    turn.inputs["Rotation"].default_value = aim.to_euler()
    room = nodes.new("ShaderNodeTexEnvironment")
    room.image = bpy.data.images.load(os.path.join(linen.ASSETS, linen.ROOM))
    links.new(coord.outputs["Generated"], turn.inputs["Vector"])
    links.new(turn.outputs["Vector"], room.inputs["Vector"])
    links.new(room.outputs["Color"], nodes["Background"].inputs["Color"])

    page = bpy.data.meshes.new("page")
    page.from_pydata([(-200, -gy0 + 200, 0), (300, -gy0 + 200, 0), (300, -gy1 - 200, 0), (-200, -gy1 - 200, 0)], [], [(0, 1, 2, 3)])
    sheet = bpy.data.materials.new("page")
    sheet.use_nodes = True
    paper = sheet.node_tree.nodes["Principled BSDF"]
    paper.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1)
    paper.inputs["Roughness"].default_value = 0.9
    paper.inputs["Specular IOR Level"].default_value = 0.2
    page.materials.append(sheet)
    page_obj = bpy.data.objects.new("page", page)
    scene.collection.objects.link(page_obj)

    # The cloth's sheets, as linen.py's shadow() lays them, the mask laid over the frame once.
    cols_m, rows_m = mask.shape[1], mask.shape[0]
    img = bpy.data.images.new("linen-tab-cut", cols_m, rows_m, alpha=True)
    img.colorspace_settings.name = "Non-Color"
    img.alpha_mode = "CHANNEL_PACKED"
    pixels = np.ones((rows_m, cols_m, 4), dtype=np.float32)
    pixels[..., 3] = mask
    img.pixels.foreach_set(pixels[::-1].ravel())
    img.pack()
    tone = np.mean([linear(c) for c in COLOURS], axis=0) ** PALE
    cloth, woven = yarn_material("cloth", tone)
    nodes, links = cloth.node_tree.nodes, cloth.node_tree.links
    where = nodes.new("ShaderNodeTexCoord")
    split = nodes.new("ShaderNodeSeparateXYZ")
    across = nodes.new("ShaderNodeMath")
    across.operation = "DIVIDE"
    across.inputs[1].default_value = cols_m / DENSITY
    down = nodes.new("ShaderNodeMath")
    down.operation = "MULTIPLY_ADD"
    down.inputs[1].default_value = 1 / (gy1 - gy0)
    down.inputs[2].default_value = gy1 / (gy1 - gy0)
    uv = nodes.new("ShaderNodeCombineXYZ")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = img
    texture.interpolation = "Linear"
    texture.extension = "EXTEND"
    facing = nodes.new("ShaderNodeLayerWeight")
    cosine = nodes.new("ShaderNodeMath")
    cosine.operation = "SUBTRACT"
    cosine.inputs[0].default_value = 1.0
    least = nodes.new("ShaderNodeMath")
    least.operation = "MAXIMUM"
    least.inputs[1].default_value = 0.02
    length = nodes.new("ShaderNodeMath")
    length.operation = "DIVIDE"
    length.inputs[0].default_value = 1.0
    passed = nodes.new("ShaderNodeMath")
    passed.operation = "POWER"
    passed.inputs[0].default_value = OPEN ** (1 / LAYERS)
    stopped = nodes.new("ShaderNodeMath")
    stopped.operation = "SUBTRACT"
    stopped.inputs[0].default_value = 1.0
    solid = nodes.new("ShaderNodeMath")
    solid.operation = "MULTIPLY"
    links.new(facing.outputs["Facing"], cosine.inputs[1])
    links.new(cosine.outputs[0], least.inputs[0])
    links.new(least.outputs[0], length.inputs[1])
    links.new(length.outputs[0], passed.inputs[1])
    links.new(passed.outputs[0], stopped.inputs[1])
    links.new(stopped.outputs[0], solid.inputs[1])
    clear = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(where.outputs["Object"], split.inputs["Vector"])
    links.new(split.outputs["X"], across.inputs[0])
    links.new(across.outputs[0], uv.inputs["X"])
    links.new(split.outputs["Y"], down.inputs[0])
    links.new(down.outputs[0], uv.inputs["Y"])
    links.new(uv.outputs["Vector"], texture.inputs["Vector"])
    links.new(texture.outputs["Alpha"], solid.inputs[0])
    links.new(solid.outputs[0], mix.inputs["Fac"])
    links.new(clear.outputs["BSDF"], mix.inputs[1])
    links.new(woven.outputs["Shader"], mix.inputs[2])
    links.new(mix.outputs["Shader"], nodes["Material Output"].inputs["Surface"])

    gx = np.arange(x0 - 60, x1 + 20, 0.5)
    gy = np.arange(gy0, gy1, 1.0)
    GX, GY = np.meshgrid(gx, gy)
    bottom = fray.lift(GX, GY)
    rows_g, cols_g = GX.shape
    index = np.arange(rows_g * cols_g).reshape(rows_g, cols_g)
    faces = np.column_stack((index[:-1, :-1].ravel(), index[:-1, 1:].ravel(), index[1:, 1:].ravel(), index[1:, :-1].ravel()))
    hidden = []
    for layer in range(LAYERS):
        verts = np.column_stack((GX.ravel(), -GY.ravel(), (bottom + THICK * (layer + 0.5) / LAYERS).ravel()))
        mesh = bpy.data.meshes.new(f"cloth-{layer}")
        mesh.vertices.add(len(verts))
        mesh.vertices.foreach_set("co", verts.astype(np.float32).ravel())
        mesh.loops.add(faces.size)
        mesh.loops.foreach_set("vertex_index", faces.astype(np.int32).ravel())
        mesh.polygons.add(len(faces))
        mesh.polygons.foreach_set("loop_start", np.arange(0, faces.size, 4, dtype=np.int32))
        mesh.update()
        mesh.materials.append(cloth)
        obj = bpy.data.objects.new(f"cloth-{layer}", mesh)
        obj.visible_camera = False
        scene.collection.objects.link(obj)
        hidden.append(obj)

    # The strip's own yarns about the frame, and the tab's.
    strip_cut = lambda y: fray.cut(y)  # noqa: E731
    near = [(p, r, t) for p, r, t in fray.strands() if (p[:, 1] > gy0).any() and (p[:, 1] < gy1).any()]
    mine = tab_strands(cut, normal, strip_cut, rng)
    strands = bpy.data.curves.new("fray", "CURVE")
    strands.dimensions = "3D"
    strands.bevel_depth = 1.0
    strands.bevel_resolution = 2
    strands.use_fill_caps = True
    for i, colour in enumerate(COLOURS):
        strands.materials.append(yarn_material(f"yarn-{i}", linear(colour) ** PALE)[0])
    for points, radii, shade in near + mine:
        spline = strands.splines.new("POLY")
        spline.points.add(len(points) - 1)
        co = np.column_stack((points[:, 0], -points[:, 1], points[:, 2], np.ones(len(points))))
        spline.points.foreach_set("co", co.astype(np.float32).ravel())
        spline.points.foreach_set("radius", np.asarray(radii, dtype=np.float32))
        spline.material_index = shade
        spline.use_smooth = True
    yarns = bpy.data.objects.new("fray", strands)
    scene.collection.objects.link(yarns)
    print(f"STRANDS {layout}: {len(near)} the strip's, {len(mine)} the tab's")

    optics = bpy.data.cameras.new("overhead")
    optics.type = "ORTHO"
    optics.ortho_scale = max(x1 - x0, y1 - y0)
    optics.clip_end = 1000
    camera = bpy.data.objects.new("overhead", optics)
    camera.location = ((x0 + x1) / 2, -(y0 + y1) / 2, 300)
    scene.collection.objects.link(camera)
    scene.camera = camera
    scene.render.resolution_x = round((x1 - x0) * SHADOW_DENSITY)
    scene.render.resolution_y = round((y1 - y0) * SHADOW_DENSITY)
    scene.render.resolution_percentage = 100
    raw = os.path.join(tempfile.gettempdir(), "linen-tab.exr")

    def expose():
        scene.render.filepath = raw
        bpy.ops.render.render(write_still=True)
        image = bpy.data.images.load(raw)
        out = np.empty(image.size[0] * image.size[1] * 4, dtype=np.float32)
        image.pixels.foreach_get(out)
        shape = (image.size[1], image.size[0], 4)
        bpy.data.images.remove(image)
        os.remove(raw)
        return out.reshape(shape)[::-1]

    for obj in hidden + [yarns]:
        obj.hide_render = True
    bare = expose()[..., :3]
    for obj in hidden + [yarns]:
        obj.hide_render = False
    yarns.visible_camera = False
    shade = expose()[..., :3]
    yarns.visible_camera = True
    page_obj.visible_camera = False
    paper.inputs["Base Color"].default_value = (*linear("#%02x%02x%02x" % tuple(round(c) for c in PAPER)), 1)
    scene.render.film_transparent = True
    lit = expose()

    # As linen.py's shadow() develops its render: the shadow colour by colour over PAPER, the yarns over it.
    ratio = np.clip(shade / np.maximum(bare, 1e-4), 0, 1)
    under = np.array(PAPER, dtype=np.float32) / 255
    under_linear = np.where(under <= 0.04045, under / 12.92, ((under + 0.055) / 1.055) ** 2.4)
    dimmed = under_linear * ratio
    target = np.where(dimmed <= 0.0031308, dimmed * 12.92, 1.055 * dimmed ** (1 / 2.4) - 0.055)
    dark = np.clip(((under - target) / under).max(axis=-1), 0, 1)
    tint = np.clip((target - under * (1 - dark[..., None])) / np.maximum(dark, 1e-4)[..., None], 0, 1)
    cover = np.clip(lit[..., 3], 0, 1)
    light = lit[..., :3] * GAIN * 2.0**linen.EXPOSURE
    colour = shoulder(light / np.maximum(cover, 1e-6)[..., None])
    colour = np.where(colour <= 0.0031308, colour * 12.92, 1.055 * np.clip(colour, 0, None) ** (1 / 2.4) - 0.055)
    total = cover + dark * (1 - cover)
    rgb = (colour * cover[..., None] + tint * (dark * (1 - cover))[..., None]) / np.maximum(total, 1e-6)[..., None]
    left = round(-x0 * SHADOW_DENSITY)
    tile = np.dstack((rgb, total))[:, left:]
    tile = np.clip(tile + (np.random.default_rng(0).random(tile.shape, dtype=np.float32) - 0.5) / 255, 0, 1)
    write(tile, f"linen-tab-{layout}", proof)
    print(f"TAB {layout}: mask {width}x{y1 - y0:.2f} CSS px, render {x1}x{y1 - y0:.2f} from x 0, y {y0:.2f}")


def write(pixels, name, proof):
    rows, cols = pixels.shape[:2]
    img = bpy.data.images.new(name, cols, rows, alpha=True)
    img.alpha_mode = "STRAIGHT"
    img.pixels.foreach_set(pixels[::-1].astype(np.float32).ravel())
    img.filepath_raw = os.path.join(proof or OUT, f"{name}.png")
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=1024)
    parser.add_argument("--proof")
    parser.add_argument("--layout", choices=tuple(LAYOUTS))
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    if args.proof:
        os.makedirs(args.proof, exist_ok=True)
    for layout in LAYOUTS:
        if args.layout in (None, layout):
            render(layout, args.samples, args.proof)


if __name__ == "__main__":
    main()
