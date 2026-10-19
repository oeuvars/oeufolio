"""The desk: everything on the mat put down in one set and photographed at once, under the one studio light, so
each object shades the others and throws its shadow on the mat as it would on a real desk. Run from the
repository root:

    blender -b --factory-startup -P studio/desk/desk.py -- [--plate wide] [--build shot ...] [--scale 0.25] [--samples 48] [--proofs DIR]

Every object is first built on its own stage, as the studio builds it for a shot of its own, and kept as a
.blend in studio/desk/sets. --build names the shots to build again, and any not kept yet are built anyway.
Then each object is put down where src/components/mat/desk.json places it on the plate, and the plate is
rendered to public/objects/mat/desk-<plate>.avif: the objects, and the shadows they throw on the mat, with
nothing of the mat itself, which the page lays under it. Parts that move on the page, the reel of the
recorder, are rendered on their own beside it, and any prop the page shows from a low camera of its own
(PORTRAITS), as it was photographed, by that camera."""

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

from objects import card, catlamp, chrono, donutlamp, flutelamp, ilolamp, lustrelamp, mat, mushroomlamp, name, pick, proraso, razor, record, recorder, ticket, wallet, watch  # noqa: E402
from paint import linear  # noqa: E402
from stage import GAIN, LENS_HEIGHT, MAT, SHADOW, Stage, shoulder  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
SETS = os.path.join(HERE, "sets")
OUT = os.path.join(ROOT, "public", "objects", "mat")
LAYOUT = os.path.join(ROOT, "src", "components", "mat", "desk.json")
# Where the lens shows each layer, against where its prop lies: written here, read by the page.
LEAN = os.path.join(ROOT, "src", "components", "mat", "lean.json")
# Where on the plate each portrait lies, in em: written here, read by the page.
PORTRAIT = os.path.join(ROOT, "src", "components", "mat", "portrait.json")
BUILDERS = {
    **mat.SHOTS,
    **card.SHOTS,
    **name.SHOTS,
    **record.SHOTS,
    **recorder.SHOTS,
    **ticket.SHOTS,
    **wallet.SHOTS,
    **pick.SHOTS,
    **proraso.SHOTS,
    **razor.SHOTS,
    **catlamp.SHOTS,
    **donutlamp.SHOTS,
    **ilolamp.SHOTS,
    **flutelamp.SHOTS,
    **lustrelamp.SHOTS,
    **mushroomlamp.SHOTS,
    **watch.SHOTS,
    **chrono.SHOTS,
}

# Each object on the page is a box this many em wide and tall, drawn k times its size, made of these shots.
# A shot's own top left lies at (x, y) in the box, lifted z em off the mat. The record's sleeve lies on the mat
# and drapes over the disc it holds (record.DISC_AT), and the label lies on the disc.
PROPS = {
    "name": {"box": (30.0, 9.625), "shots": {"name": (0, 0, 0)}},
    "card": {"box": (14.8, 8.46), "k": 1.3, "shots": {"card": (0, 0, 0)}},
    "record": {"box": (20.0, 15.625), "k": 1.5, "shots": {"disc": (5.5, 0.5625, 0), "label": (10.0, 5.0625, 0.1), "sleeve": (0, 0, 0)}},
    "recorder": {"box": (11.875, 17.0), "shots": {"recorder": (0, 0, 0), "reel": (0, 0, 0)}},
    "ticket": {"box": (20.625, 9.375), "shots": {"ticket-stub": (0, 0, 0), "ticket-main": (3.4, 0, 0)}},
    "wallet": {"box": (14.8, 18.0), "shots": {"wallet": (0, 0, 0)}},
    "pick-fin": {"box": (3.145, 3.3), "k": 1.6, "shots": {"pick-fin": (0, 0, 0)}},
    "pick-wedge": {"box": (2.76, 3.125), "k": 1.6, "shots": {"pick-wedge": (0, 0, 0)}},
    "proraso": {"box": (25.5, 7.95), "shots": {"proraso": (0, 0, 0)}},
    "razor": {"box": (17.5, 7.3), "shots": {"razor": (0, 0, 0)}},
    "catlamp": {"box": (27.0, 10.0), "k": 0.7, "shots": {"catlamp": (0, 0, 0)}},
    "donutlamp": {"box": (donutlamp.W, donutlamp.H), "shots": {"donutlamp": (0, 0, 0)}},
    "ilolamp": {"box": (ilolamp.W, ilolamp.H), "shots": {"ilolamp": (0, 0, 0)}},
    "flutelamp": {"box": (flutelamp.W, flutelamp.H), "shots": {"flutelamp": (0, 0, 0)}},
    "lustrelamp": {"box": (lustrelamp.W, lustrelamp.H), "shots": {"lustrelamp": (0, 0, 0)}},
    "mushroomlamp": {"box": (mushroomlamp.W, mushroomlamp.H), "k": 0.9, "shots": {"mushroomlamp": (0, 0, 0)}},
    "watch": {"box": (watch.W, watch.H), "shots": {"watch": (0, 0, 0)}},
    "chrono": {"box": (chrono.W, chrono.H), "shots": {"chrono": (0, 0, 0)}},
}
# Shots the page turns, rendered as layers of their own and left out of the plate. The reel's shot carries a
# stand-in for the reel under the hub, which the recorder's own shot has for real. A shot's parts are in the layer
# each is tagged for, in its "layer" property, or else in the one named for the shot.
LAYERS = {"reel": "recorder"}
# Layers that are round and stay put while those under and over them turn: a raised hub over a turning line. They
# stay in the plate too, to throw their shadow there, and are drawn again as a layer of their own over what turns
# under them. A spinning hub's shading and the side the lens sees of it do not turn with it.
STILL = ("hub",)
STAND_INS = {"reel": ("reel",)}
# Props the page shows from a camera of their own, and not from the plate's. The cat lamp is seen low beside her, as
# she was photographed, whose face looking down on her only shows the top of her head. The donut lamp is seen from
# straight over it, at the height the plate's camera is held: the plate's camera, off to one side of it, would draw
# the tall round glass leaning away from it, egg-shaped. So are the ILO lamp, its dock hidden under its ring, and
# the fluted copper lamp and the smoked lustre glass lamp, lying on their backs with their faces up, as their faces
# were photographed, and the lacquered mushroom lamp standing on its foot. Each is left out of the plate's camera
# but stays in the set, throwing its shadow and its light on the mat under it, and is rendered on its own by that camera, at the plate's own size, set where it stands. Each is its shot, and the module that built it, which knows the camera
# (photograph()) in the coordinates of its object (the mesh named BODY, or else the one carrying the photograph),
# the middle of the object (MIDDLE), and the point on the desk under that middle (STANDS).
PORTRAITS = {"catlamp": ("catlamp", catlamp), "donutlamp": ("donutlamp", donutlamp), "ilolamp": ("ilolamp", ilolamp), "flutelamp": ("flutelamp", flutelamp), "lustrelamp": ("lustrelamp", lustrelamp), "mushroomlamp": ("mushroomlamp", mushroomlamp)}
# The page shows an em of the plate at up to 22 pixels, 44 on a screen of two pixels to the point; this many leaves
# room to zoom in before the render runs out.
DENSITY = 64
EXPOSURE = 0.1
# The room is lit, from elsewhere, by this much of the light the leather was photographed in.
ROOM = 0.025
# The light: a pendant lamp hanging over the top right of the desk (desk.json's "lamp": where, in em, and how high),
# out of the picture. A bare bulb this bright, in watts, this warm, this many em across, in a deep shade: it throws a
# pool of light down onto the mat, this wide, with a soft edge where the rim of the shade cuts it off, and hangs a
# little turned toward the middle of the desk, by these angles. The room round it is all but dark.
BULB = 300000.0
BULB_COLOUR = (1.0, 0.74, 0.46)
BULB_SIZE = 5.0
SHADE = (138.0, 1.0)
SHADE_TURN = (-6.0, -8.0)
# The maps of the light on the mat are drawn this many pixels to the em, enough for a shadow's sharp edge where an
# object touches the mat.
MAP_DENSITY = 32


class Keeper(Stage):
    """A stage that keeps what is built on it, and photographs nothing."""

    def shoot(self, name, frame, card=0.0, lens=True, shadowless=(), **_):
        for image in bpy.data.images:
            if not image.filepath and not image.packed_file and image.has_data:
                image.pack()
        os.makedirs(SETS, exist_ok=True)
        with open(os.path.join(SETS, f"{name}.json"), "w") as file:
            json.dump({"frame": frame, "card": card, "lens": lens, "shadowless": [obj.name for obj in shadowless]}, file)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SETS, f"{name}.blend"), compress=True)
        print(f"KEPT {name}")


def build(stage, shots):
    for shot in shots:
        stage.clear()
        BUILDERS[shot](stage)


def lens(materials, cx, cy):
    """Lean the shading normals away from the middle of the object, as Stage does for a shot of its own."""
    lean = 1 / (2 * LENS_HEIGHT)
    for material in materials:
        tree = material.node_tree
        shader = tree.nodes.get("Principled BSDF") if tree else None
        if shader is None:
            continue
        nodes, links = tree.nodes, tree.links
        geometry = nodes.new("ShaderNodeNewGeometry")
        away = nodes.new("ShaderNodeVectorMath")
        away.operation = "SUBTRACT"
        away.inputs[1].default_value = (cx, cy, 0)
        flat = nodes.new("ShaderNodeVectorMath")
        flat.operation = "MULTIPLY"
        flat.inputs[1].default_value = (lean, lean, 0)
        links.new(geometry.outputs["Position"], away.inputs[0])
        links.new(away.outputs[0], flat.inputs[0])
        for socket_name in ("Normal", "Coat Normal"):
            socket = shader.inputs[socket_name]
            base = socket.links[0].from_socket if socket.is_linked else geometry.outputs["Normal"]
            tilted = nodes.new("ShaderNodeVectorMath")
            tilted.operation = "ADD"
            unit = nodes.new("ShaderNodeVectorMath")
            unit.operation = "NORMALIZE"
            links.new(base, tilted.inputs[0])
            links.new(flat.outputs[0], tilted.inputs[1])
            links.new(tilted.outputs[0], unit.inputs[0])
            links.new(unit.outputs[0], socket)


class Desk:
    """The set: the room, the mat, and every object put down on it."""

    def __init__(self, stage, plate):
        self.stage = stage
        with open(LAYOUT) as file:
            self.layout = json.load(file)[plate]
        self.w, self.h = self.layout["size"]
        # Every object, the parts of each shot, the studio gear each shot brought for itself, and what casts no shadow.
        self.props = {}
        self.parts = {}
        self.gear = []
        self.shadowless = []

    def lay(self):
        stage = self.stage
        stage.clear()
        # The whole desk at full size does not fit in the graphics card's memory at once.
        bpy.context.scene.cycles.use_auto_tile = True
        bpy.context.scene.cycles.tile_size = 2048
        # The passes render the same scene again and again. Keep what Cycles has built between them.
        bpy.context.scene.render.use_persistent_data = True
        floor = stage._room(self.w / 2, -self.h / 2)
        floor.scale = (2, 2, 1)
        # What lies under clear film or glass is the page's own leather, not this stand-in for it. Seen through
        # them the floor is left out and the render keeps only their reflections, so the page shows through.
        floor.visible_transmission = False
        bpy.context.scene.cycles.film_transparent_glass = True
        bpy.context.scene.cycles.film_transparent_roughness = 0.3
        for prop, (x, y, r) in self.layout["at"].items():
            self.put(prop, x, y, r)
        self.frame()

    def put(self, prop, x, y, r):
        spec = PROPS[prop]
        bw, bh = spec["box"]
        k = spec.get("k", 1.0)
        root = self.stage.add(prop, None)
        root.location = (x, -y, 0)
        root.rotation_euler = (0, 0, math.radians(-r))
        root.scale = (k, k, k)
        lit = bpy.data.collections.new(f"lit-{prop}")
        objects = []
        for shot, (ox, oy, oz) in spec["shots"].items():
            with open(os.path.join(SETS, f"{shot}.json")) as file:
                kept = json.load(file)
            with bpy.data.libraries.load(os.path.join(SETS, f"{shot}.blend"), link=False) as (source, target):
                names = list(source.objects)
                # Blender fills the list it is given with the objects in place, so it gets a copy and the names stay names.
                target.objects = list(names)
            anchor = self.stage.add(f"{prop}-{shot}", None)
            anchor.parent = root
            anchor.location = (ox - bw / 2, -oy + bh / 2, oz / k)
            parts = []
            for was, obj in zip(names, target.objects):
                if was in STAND_INS.get(shot, ()):
                    bpy.data.objects.remove(obj)
                    continue
                bpy.context.scene.collection.objects.link(obj)
                if obj.parent is None:
                    obj.parent = anchor
                if was in kept["shadowless"]:
                    self.shadowless.append(obj)
                if obj.type == "MESH" and not obj.visible_camera and not obj.get("bulb") and not obj.get("studio"):
                    # A shot's own lights shine on its object alone. Its flags and cards, which only
                    # reflections see, would show in everything else on the desk, and the room is light enough.
                    if any(node.type == "EMISSION" for slot in obj.material_slots if slot.material for node in slot.material.node_tree.nodes):
                        self.gear.append((obj, lit))
                    else:
                        bpy.data.objects.remove(obj)
                else:
                    parts.append(obj)
                    lit.objects.link(obj)
            self.parts[shot] = parts
            objects += parts
            bpy.context.view_layer.update()
            if kept["lens"]:
                materials = {slot.material for obj in parts if obj.type == "MESH" for slot in obj.material_slots if slot.material}
                middle = middle_of(anchor, kept["frame"])
                lens(materials, middle.x, middle.y)
            if kept["card"]:
                card = self.stage._card(x, -y, kept["card"])
                self.gear.append((card, lit))
        self.props[prop] = (root, lit, objects)

    def frame(self):
        """Light every piece of gear on only the object it came with."""
        for obj, lit in self.gear:
            obj.light_linking.receiver_collection = lit
            obj.light_linking.blocker_collection = lit

    def camera(self, x0, y0, w, h, density):
        """A camera held where someone at the desk holds a phone over it, at the plate's eye (x, y and height in
        em, the near side of the desk being down the page), framing the rectangle of the mat from (x0, y0), w by
        h em. Its back is kept level with the desk and the lens shifted onto the frame, as an architect's camera
        is: the mat and everything flat on it are drawn true, and anything standing on it shows its side toward
        the eye, the lamp its front."""
        scene = bpy.context.scene
        camera = getattr(self, "overhead", None)
        if camera is None:
            optics = bpy.data.cameras.new("overhead")
            optics.type = "PERSP"
            optics.sensor_fit = "AUTO"
            optics.sensor_width = 36.0
            optics.clip_end = 1000
            camera = self.overhead = self.stage.add("overhead", optics)
        scene.camera = camera
        ex, ey, height = self.layout["eye"]
        side = max(w, h)
        camera.data.lens = camera.data.sensor_width * height / side
        camera.data.shift_x = (x0 + w / 2 - ex) / side
        camera.data.shift_y = -(y0 + h / 2 - ey) / side
        camera.location = (ex, -ey, height)
        scene.render.resolution_x = round(w * density)
        scene.render.resolution_y = round(h * density)
        scene.render.resolution_percentage = 100
        self.view = (x0, y0, w, h)

    def crop(self, shot, prop, parts):
        """Render only the square round a shot's frame, as the lens sees it. The parts stand off the mat, so the
        lens shows them a little out from where they lie and a little larger. Returns where they show, against
        where they lie: the shift in em of the prop, turned and scaled as the prop is, and the scale."""
        scene = bpy.context.scene
        with open(os.path.join(SETS, f"{shot}.json")) as file:
            frame = json.load(file)["frame"]
        bpy.context.view_layer.update()
        middle = middle_of(bpy.data.objects[f"{prop}-{shot}"], frame)
        k = PROPS[prop].get("k", 1.0)
        heights = [(obj.matrix_world @ Vector(corner)).z for obj in parts for corner in obj.bound_box]
        # What shows of a layer is its top; that height is where the lens sees it.
        z = max(heights)
        eye = scene.camera.location
        grow = eye.z / (eye.z - z)
        seen = Vector((eye.x + (middle.x - eye.x) * grow, eye.y + (middle.y - eye.y) * grow, 0))
        side = max(frame[2:]) * k * grow
        vx, vy, vw, vh = self.view
        x0, y0 = seen.x - side / 2 - vx, -seen.y - side / 2 - vy
        scene.render.use_border = True
        scene.render.use_crop_to_border = True
        scene.render.border_min_x, scene.render.border_max_x = x0 / vw, (x0 + side) / vw
        scene.render.border_min_y, scene.render.border_max_y = 1 - (y0 + side) / vh, 1 - y0 / vh
        dx, dy = seen.x - middle.x, -(seen.y - middle.y)
        turn = math.radians(self.layout["at"][prop][2])
        local = (dx * math.cos(turn) + dy * math.sin(turn), -dx * math.sin(turn) + dy * math.cos(turn))
        return [round(local[0] / k, 4), round(local[1] / k, 4), round(grow, 4)]

    def portrait(self, held, parts, density):
        """Point the portrait camera at a shot's object as it was photographed: where that camera stood, in the
        object's own coordinates, carried to where the object lies on the desk, drawing it as large as the plate
        does round its middle. The picture is framed round the whole of the object. Returns where on the plate
        the picture lies, and the object in it, each as left, top, width and height in em, set so the point on
        the desk under her middle lies where the plate has it."""
        scene = bpy.context.scene
        centre, axes, _ = held.photograph()
        body = next(obj for obj in parts if obj.type == "MESH" and (obj.name == getattr(held, "BODY", None) or obj.data.uv_layers.get("photo")))
        placed = body.matrix_world
        turn = placed.to_quaternion().to_matrix()
        camera = getattr(self, "low", None)
        if camera is None:
            optics = bpy.data.cameras.new("portrait")
            optics.sensor_fit = "AUTO"
            optics.sensor_width = 36.0
            optics.clip_end = 1000
            camera = self.low = self.stage.add("portrait", optics)
        where = placed @ Vector(centre)
        looking = turn @ Matrix(axes).transposed()
        camera.matrix_world = Matrix.Translation(where) @ looking.to_4x4()
        into = looking.transposed()

        def seen(point):
            x, y, z = into @ (point - where)
            return x / -z, -y / -z, -z

        _, _, depth = seen(placed @ Vector(held.MIDDLE))
        focal = depth * density
        # The picture is framed round the object's own surface, not its boxes, which stand well off a curved thing.
        graph = bpy.context.evaluated_depsgraph_get()
        points = []
        for obj in parts:
            if obj.type not in ("MESH", "CURVE") or obj.get("unseen"):
                continue
            surface = obj.evaluated_get(graph).to_mesh()
            co = np.empty(len(surface.vertices) * 3)
            surface.vertices.foreach_get("co", co)
            obj.evaluated_get(graph).to_mesh_clear()
            world = np.asarray(obj.matrix_world)
            points.append(co.reshape(-1, 3) @ world[:3, :3].T + world[:3, 3])
        local = (np.concatenate(points) - np.asarray(where)) @ np.asarray(into).T
        u, v = local[:, 0] / -local[:, 2] * focal, -local[:, 1] / -local[:, 2] * focal
        # Room round it for the glow the lens spreads round the lit bulb, so it fades out inside the picture.
        margin = 8 * density
        left, right = u.min() - margin, u.max() + margin
        top, bottom = v.min() - margin, v.max() + margin
        w, h = math.ceil(right - left), math.ceil(bottom - top)
        side = max(w, h)
        camera.data.lens = camera.data.sensor_width * focal / side
        camera.data.shift_x = (left + w / 2) / side
        camera.data.shift_y = -(top + h / 2) / side
        scene.camera = camera
        scene.render.use_border = False
        scene.render.resolution_x, scene.render.resolution_y = w, h
        foot = placed @ Vector(held.STANDS)
        fu, fv, _ = seen(foot)
        gx, gy = fu * focal - left, fv * focal - top
        x0, y0 = foot.x - gx / density, -foot.y - gy / density
        picture = [x0, y0, w / density, h / density]
        body = [x0 + (u.min() - left) / density, y0 + (v.min() - top) / density, (u.max() - u.min()) / density, (v.max() - v.min()) / density]
        return {name: [round(float(value), 4) for value in rect] for name, rect in (("picture", picture), ("body", body))}

    def light(self):
        """The pendant over the top right of the desk: its bulb in its deep shade (BULB, SHADE)."""
        source = bpy.data.lights.new("bulb", "SPOT")
        source.energy = BULB
        source.color = BULB_COLOUR
        source.shadow_soft_size = BULB_SIZE / 2
        source.spot_size = math.radians(SHADE[0])
        source.spot_blend = SHADE[1]
        light = self.stage.add("bulb", source)
        x, y, height = self.layout["lamp"]
        light.location = (x, -y, height)
        light.rotation_euler = (math.radians(SHADE_TURN[0]), math.radians(SHADE_TURN[1]), 0)
        return light


def middle_of(anchor, frame):
    """Where the middle of a shot's frame is on the plate."""
    fx, fy, fw, fh = frame
    return anchor.matrix_world @ Vector((fx + fw / 2, -(fy + fh / 2), 0))


def cast(objects, there):
    """Whether objects are in the render at all. A layer the page turns is left out of the plate entirely: not
    only unseen, but throwing no shadow and showing in no reflection, or the plate would keep a ghost of it that
    stayed put while the layer turned over it. The layer brings its own shadow and reflections."""
    for obj in objects:
        obj.hide_render = not there


def show(objects, seen):
    """Whether cameras see objects. Parts marked "unseen" (a lamp's glowing stand-ins, a studio only its glass
    reflects) no camera ever sees."""
    for obj in objects:
        obj.visible_camera = seen and not obj.get("unseen")


def rolled(x, knee=0.72, brightest=6.0, soft=0.5):
    """Highlights as a phone camera keeps them in a dim room with a lamp in it: linear up to the knee, then
    compressed on a log scale, so that the lamp's glass, tens of times brighter than the desk it lights, still
    shows its shape instead of burning out flat."""
    over = np.maximum(x - knee, 0)
    return np.where(x <= knee, x, knee + (1 - knee) * np.minimum(np.log1p(over / soft) / np.log1p(brightest / soft), 1))


def encoded(colour):
    """Linear light as sRGB."""
    colour = np.maximum(colour, 0)
    return np.where(colour <= 0.0031308, colour * 12.92, 1.055 * colour ** (1 / 2.4) - 0.055)


def develop(pixels, cast, out, proofs, name, exposure=EXPOSURE):
    """The pixels as an AVIF with straight alpha, the shadow on the mat under them, as Stage.develop does it."""
    light = pixels[..., :3] * GAIN * 2.0**exposure
    cover = pixels[..., 3]
    alpha = np.clip(np.maximum(cover, light.max(axis=-1)), 0, 1)
    colour = shoulder(light / np.maximum(alpha, 1e-6)[..., None])
    under = np.clip(cast, 0, 1) * (1 - alpha)
    total = alpha + under
    colour = (colour * alpha[..., None] + SHADOW * under[..., None]) / np.maximum(total, 1e-6)[..., None]
    colour = np.clip(colour, 0, 1)
    colour = np.where(colour <= 0.0031308, colour * 12.92, 1.055 * colour ** (1 / 2.4) - 0.055)
    colour += (np.random.default_rng(0).random(colour.shape, dtype=np.float32) - 0.5) / 255
    encoded = np.dstack((np.clip(colour, 0, 1), total)).astype(np.float32)
    lossless = os.path.join(tempfile.gettempdir(), f"desk-{name}.png")
    save(encoded, lossless)
    subprocess.run(["uv", "run", "--quiet", os.path.join(HERE, "encode.py"), lossless, out], check=True)
    os.remove(lossless)
    if proofs:
        value = MAT.lstrip("#")
        mat = np.array([int(value[i : i + 2], 16) / 255 for i in (0, 2, 4)], dtype=np.float32)
        encoded[..., :3] = encoded[..., :3] * encoded[..., 3:] + mat * (1 - encoded[..., 3:])
        encoded[..., 3] = 1
        save(encoded, os.path.join(proofs, f"{name}.png"))


def save(encoded, path):
    rows, cols = encoded.shape[:2]
    image = bpy.data.images.new(os.path.basename(path), cols, rows, alpha=True)
    image.alpha_mode = "STRAIGHT"
    image.pixels.foreach_set(encoded[::-1].ravel())
    image.filepath_raw = path
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plate", default="wide")
    parser.add_argument("--build", nargs="*", default=[])
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument("--proofs")
    parser.add_argument("--layers", nargs="*", help="render only these layers the page lays over the plate, or all of them, and keep the plates")
    parser.add_argument("--shot", help="photograph this one shot on a stand of its own, as a proof, and nothing else")
    parser.add_argument("--layout", help="lay the desk out as this file has it, in desk.json's form, instead: a proof only")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    if args.scale != 1 or args.layout:
        # A proof at another scale, or of another layout, never takes the place of the page's plates, or the page
        # would show a plate of one render with a layer of another.
        global OUT, LEAN, PORTRAIT, LAYOUT
        LAYOUT = args.layout or LAYOUT
        OUT = args.proofs or tempfile.mkdtemp(prefix="desk-")
        LEAN = os.path.join(OUT, "lean.json")
        PORTRAIT = os.path.join(OUT, "portrait.json")
        os.makedirs(OUT, exist_ok=True)

    if args.shot:
        proofs = args.proofs or tempfile.gettempdir()
        os.makedirs(proofs, exist_ok=True)
        alone = Stage(proofs, proofs, args.scale, args.samples)
        alone.clear()
        BUILDERS[args.shot](alone)
        return

    stage = Keeper(OUT, samples=args.samples)
    # How long each render takes, to see where the time goes.
    expose = stage._expose

    def timed(path, percentage=100, samples=None):
        began = time.time()
        pixels = expose(path, percentage, samples)
        print(f"PASS {pixels.shape[1]}x{pixels.shape[0]} {samples or stage.samples} samples {time.time() - began:.0f}s")
        return pixels

    stage._expose = timed
    with open(LAYOUT) as file:
        placed = {prop for plate in json.load(file).values() for prop in plate["at"]}
    # Only the props some plate puts down are built: the cat lamp's builder is kept, but she is off the desk.
    wanted = [shot for prop, spec in PROPS.items() if prop in placed for shot in spec["shots"]]
    unknown = [shot for shot in args.build if shot not in BUILDERS]
    if unknown:
        sys.exit(f"Unknown shots: {', '.join(unknown)}")
    build(stage, [shot for shot in wanted if shot in args.build or not os.path.exists(os.path.join(SETS, f"{shot}.blend"))])

    started = time.time()
    desk = Desk(stage, args.plate)
    desk.lay()
    density = DENSITY * args.scale
    desk.camera(0, 0, desk.w, desk.h, density)
    scene = bpy.context.scene
    floor = next(obj for obj in scene.objects if obj.get("stand") == "mat")
    layered = [obj for shot in LAYERS for obj in desk.parts.get(shot, []) if obj.get("layer", shot) not in STILL]
    everything = [obj for _, _, objects in desk.props.values() for obj in objects]
    # A portrayed shot's parts marked "plated" (a lamp's cord across the desk) lie in the plate all the same.
    portrayed = [obj for shot, _ in PORTRAITS.values() for obj in desk.parts.get(shot, []) if not obj.get("plated")]
    # What the plate's camera sees: everything but the layers and the portraits, which the page lays over it.
    plated = [obj for obj in everything if obj not in layered and obj not in portrayed]
    studio = [obj for obj in everything if obj.get("studio")]
    cast(studio, False)
    raw = os.path.join(tempfile.gettempdir(), "desk.exr")
    if args.proofs:
        os.makedirs(args.proofs, exist_ok=True)
    named = f"desk-{args.plate}"

    def layers():
        """Each layer on its own, cropped square round its object, with everything else still there to light it.
        Where the lens shows each, against where its prop lies, goes to LEAN for the page."""
        show(everything, False)
        leans = {}
        for shot, prop in LAYERS.items():
            groups = {}
            for obj in desk.parts.get(shot, []):
                groups.setdefault(obj.get("layer", shot), []).append(obj)
            for name, parts in groups.items():
                if args.layers and name not in args.layers:
                    continue
                show(parts, True)
                cast(parts, True)
                leans[name] = desk.crop(shot, prop, parts)
                layer = stage._expose(raw)
                scene.render.use_border = False
                develop(layer, np.zeros(layer.shape[:2], dtype=np.float32), os.path.join(OUT, f"{named}-{name}.avif"), args.proofs, f"{named}-{name}")
                show(parts, False)
                if name not in STILL:
                    cast(parts, False)
                print(f"LAYER {name} {layer.shape[1]}x{layer.shape[0]}")
        known = json.load(open(LEAN)) if os.path.exists(LEAN) else {}
        known.setdefault(args.plate, {}).update(leans)
        with open(LEAN, "w") as file:
            file.write(json.dumps(known, indent=2) + "\n")
        show(plated, True)

    def portraits():
        """Each portrait on its own, by its own camera, with everything else still there to light it. Where on the
        plate each lies goes to PORTRAIT for the page."""
        show(everything, False)
        frames = {}
        for prop, (shot, held) in PORTRAITS.items():
            if shot not in desk.parts or (args.layers and prop not in args.layers):
                continue
            parts = [obj for obj in desk.parts[shot] if not obj.get("plated")]
            show(parts, True)
            frames[prop] = desk.portrait(held, parts, density)
            pixels = stage._expose(raw)
            develop(pixels, np.zeros(pixels.shape[:2], dtype=np.float32), os.path.join(OUT, f"{named}-{prop}.avif"), args.proofs, f"{named}-{prop}")
            show(parts, False)
            print(f"PORTRAIT {prop} {pixels.shape[1]}x{pixels.shape[0]} at {frames[prop]}")
        desk.camera(0, 0, desk.w, desk.h, density)
        known = json.load(open(PORTRAIT)) if os.path.exists(PORTRAIT) else {}
        # A portrait of a prop no longer on the plate goes with it, or the page would still draw it.
        known[args.plate] = {prop: frame for prop, frame in {**known.get(args.plate, {}), **frames}.items() if PORTRAITS[prop][0] in desk.parts}
        with open(PORTRAIT, "w") as file:
            file.write(json.dumps(known, indent=2) + "\n")
        show(plated, True)

    room = scene.world.node_tree.nodes["Background"].inputs["Strength"]
    paint = floor.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Base Color"]
    mat_colour = tuple(paint.default_value)

    def white_mat():
        """What the light puts on a white mat with nothing on it, as one grey."""
        hidden = [obj for obj in everything if not obj.hide_render]
        for obj in hidden:
            obj.hide_render = True
        floor.visible_camera = True
        paint.default_value = (0.8, 0.8, 0.8, 1)
        view = desk.view
        desk.camera(0, 0, desk.w, desk.h, 2)
        grey = stage._expose(raw, samples=32)[..., :3].reshape(-1, 3).mean(axis=0)
        desk.camera(*view, density)
        for obj in hidden:
            obj.hide_render = False
        floor.visible_camera = False
        paint.default_value = mat_colour
        return grey

    # The leather the page lays under the plate was photographed in the room at full strength: that is 1 on
    # the maps of the light. The room the desk is in is all but dark, and the pendant over it does the rest.
    daylight = white_mat()
    room.default_value = ROOM
    # A shot's studio cards stay out, but those it keeps ("kept"), which only its own polish throws back.
    for obj, _ in desk.gear:
        obj.hide_render = not obj.get("kept")
    desk.light()

    def light_map():
        """The light on the mat as a map, which the page multiplies its own leather, rules and rulers by: a white
        mat rendered with everything on it unseen but still in the way of the light, so their shadows, soft and
        hard, and the dark where they touch it, are the light's own. 1 is the light the leather was photographed
        in. Returns the colour round its edge, which the page carries on past it."""
        show(everything, False)
        floor.visible_camera = True
        was_paint = tuple(paint.default_value)
        paint.default_value = (0.8, 0.8, 0.8, 1)
        bx, by = desk.layout["bleed"]
        desk.camera(-bx, -by, desk.w + 2 * bx, desk.h + 2 * by, min(density, MAP_DENSITY))
        light = stage._expose(raw, samples=max(128, args.samples // 2))[..., :3] / daylight
        # The map multiplies the leather, so it holds the light up to what it was photographed in. Where the lamp
        # lights the leather brighter than that, and the rest goes to a second map, which the page adds over it: what
        # the camera sees of the leather there, rolled off as the objects' own highlights are in the same
        # photograph, less what the first map already shows of it.
        held = np.clip(light, 0, 1)
        leather = np.array(linear(MAT), dtype=np.float32)
        past = np.clip(encoded(rolled(light * leather)) - encoded(held * leather), 0, 1)
        dither = (np.random.default_rng(1).random(light.shape, dtype=np.float32) - 0.5) / 255
        maps = [("light", np.clip(encoded(held) + dither, 0, 1))]
        if past.max() > 2 / 255:
            maps.append(("light-past", np.where(past > 0, np.clip(past + dither, 0, 1), 0)))
        for name, colour in maps:
            mapped = np.dstack((colour, np.ones(light.shape[:2]))).astype(np.float32)
            save(mapped, os.path.join(tempfile.gettempdir(), "desk-light.png"))
            subprocess.run(["uv", "run", "--quiet", os.path.join(HERE, "encode.py"), os.path.join(tempfile.gettempdir(), "desk-light.png"), os.path.join(OUT, f"{named}-{name}.avif")], check=True)
            if args.proofs:
                save(mapped, os.path.join(args.proofs, f"{named}-{name}.png"))
        light = maps[0][1]
        floor.visible_camera = False
        paint.default_value = was_paint
        show(plated, True)
        desk.camera(0, 0, desk.w, desk.h, density)
        rim = np.concatenate((light[0], light[-1], light[:, 0], light[:, -1])).mean(axis=0)
        return "#" + "".join(f"{round(float(c) * 255):02x}" for c in np.clip(rim, 0, 1))

    plates = args.layers is None
    show(layered, False)
    cast(layered, False)
    show(portrayed, False)
    if plates:
        # The objects in the lamp's light, the mat unseen but lighting them from below and showing in them, and the
        # light on the mat as a map.
        pixels = stage._expose(raw)
        develop(pixels, np.zeros(pixels.shape[:2], dtype=np.float32), os.path.join(OUT, f"{named}.avif"), args.proofs, named)
        print(f"PLATE {pixels.shape[1]}x{pixels.shape[0]} {time.time() - started:.0f}s")
        print("RIM " + light_map())
    layers()
    portraits()

main()
