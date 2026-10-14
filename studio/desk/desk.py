"""The desk: everything on the mat put down in one set and photographed at once, under the one studio light, so
each object shades the others and throws its shadow on the mat as it would on a real desk. Run from the
repository root:

    blender -b --factory-startup -P studio/desk/desk.py -- [--plate wide] [--build shot ...] [--scale 0.25] [--samples 48] [--proofs DIR]

Every object is first built on its own stage, as the studio builds it for a shot of its own, and kept as a
.blend in studio/desk/sets. --build names the shots to build again, and any not kept yet are built anyway.
Then each object is put down where src/components/mat/desk.json places it on the plate, and the plate is
rendered to public/objects/mat/desk-<plate>.avif: the objects, and the shadows they throw on the mat, with
nothing of the mat itself, which the page lays under it. Parts that move on the page, the reel of the
recorder, are rendered on their own beside it."""

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
from mathutils import Vector  # noqa: E402

from objects import card, mat, name, pick, proraso, razor, record, recorder, ticket, wallet  # noqa: E402
from paint import blur  # noqa: E402
from stage import BOX_ON_STAND, GAIN, LENS_HEIGHT, MAT, SHADOW, Stage, shoulder  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
SETS = os.path.join(HERE, "sets")
OUT = os.path.join(ROOT, "public", "objects", "mat")
LAYOUT = os.path.join(ROOT, "src", "components", "mat", "desk.json")
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
}

# Each object on the page is a box this many em wide and tall, drawn k times its size, made of these shots.
# A shot's own top left lies at (x, y) in the box, lifted z em off the mat. The record's sleeve lies over the
# disc it holds, and the label on the disc.
PROPS = {
    "name": {"box": (30.0, 9.625), "shots": {"name": (0, 0, 0)}},
    "card": {"box": (14.8, 8.46), "k": 1.3, "shots": {"card": (0, 0, 0)}},
    "record": {"box": (20.0, 15.625), "k": 1.5, "shots": {"disc": (5.5, 0.5625, 0), "label": (10.0, 5.0625, 0.1), "sleeve": (0, 0, 0.1)}},
    "recorder": {"box": (11.875, 17.0), "shots": {"recorder": (0, 0, 0), "reel": (0, 0, 0)}},
    "ticket": {"box": (20.625, 9.375), "shots": {"ticket-stub": (0, 0, 0), "ticket-main": (3.4, 0, 0)}},
    "wallet": {"box": (14.8, 18.0), "shots": {"wallet": (0, 0, 0)}},
    "pick-fin": {"box": (3.145, 3.3), "k": 1.6, "shots": {"pick-fin": (0, 0, 0)}},
    "pick-wedge": {"box": (2.76, 3.125), "k": 1.6, "shots": {"pick-wedge": (0, 0, 0)}},
    "proraso": {"box": (25.5, 7.95), "shots": {"proraso": (0, 0, 0)}},
    "razor": {"box": (17.5, 7.3), "shots": {"razor": (0, 0, 0)}},
}
# Shots the page turns, rendered as layers of their own and left out of the plate. The reel's shot carries a
# stand-in for the reel under the hub, which the recorder's own shot has for real.
LAYERS = {"reel": "recorder"}
STAND_INS = {"reel": ("reel",)}
# The page shows an em of the plate at up to this many pixels.
DENSITY = 32
EXPOSURE = 0.1
# The lamp's plate: how bright the bulb is, in watts, and how much of the room's light is left at night.
BULB = 260000.0
NIGHT_ROOM = 0.02
LAMP_EXPOSURE = 0.0
# The window's share of the light on the mat by day, the rest being the room's. Its size and distance in em.
KEY_SHARE = 0.6
KEY_SIZE = 45.0
KEY_DISTANCE = 160.0


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
                target.objects = names
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
                if obj.type == "MESH" and not obj.visible_camera:
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
        """An overhead camera on the rectangle of the plate from (x0, y0), w by h em."""
        scene = bpy.context.scene
        camera = scene.camera
        if camera is None:
            optics = bpy.data.cameras.new("overhead")
            optics.type = "ORTHO"
            optics.clip_end = 300
            camera = scene.camera = self.stage.add("overhead", optics)
        camera.data.ortho_scale = max(w, h)
        camera.location = (x0 + w / 2, -(y0 + h / 2), 200)
        scene.render.resolution_x = round(w * density)
        scene.render.resolution_y = round(h * density)
        scene.render.resolution_percentage = 100
        self.view = (x0, y0, w, h)

    def crop(self, shot, prop):
        """Render only the square round a shot's frame, wherever the camera is."""
        scene = bpy.context.scene
        with open(os.path.join(SETS, f"{shot}.json")) as file:
            frame = json.load(file)["frame"]
        bpy.context.view_layer.update()
        middle = middle_of(bpy.data.objects[f"{prop}-{shot}"], frame)
        side = max(frame[2:]) * PROPS[prop].get("k", 1.0)
        vx, vy, vw, vh = self.view
        x0, y0 = middle.x - side / 2 - vx, -middle.y - side / 2 - vy
        scene.render.use_border = True
        scene.render.use_crop_to_border = True
        scene.render.border_min_x, scene.render.border_max_x = x0 / vw, (x0 + side) / vw
        scene.render.border_min_y, scene.render.border_max_y = 1 - (y0 + side) / vh, 1 - y0 / vh

    def key(self, power):
        """The window: a big soft disk up and to the top right of the desk, where the studio's octabox hangs.
        It gives every object a shadow with a direction and an edge, and metal a highlight to hold."""
        source = bpy.data.lights.new("key", "AREA")
        source.shape = "DISK"
        source.size = KEY_SIZE
        source.energy = power
        source.color = (0.99, 0.995, 1.0)
        light = self.stage.add("key", source)
        middle = Vector((self.w / 2, -self.h / 2, 0))
        light.location = middle + BOX_ON_STAND * KEY_DISTANCE
        light.rotation_euler = (-BOX_ON_STAND).to_track_quat("-Z", "Y").to_euler()
        return light

    def lamp(self, power):
        """The pendant over the top right of the plate: a bare bulb in a deep shade, so it throws a pool of
        light down onto the mat with a soft edge where the rim of the shade cuts it off."""
        x, y, height = self.layout["lamp"]
        source = bpy.data.lights.new("bulb", "SPOT")
        source.energy = power
        source.color = (1.0, 0.74, 0.46)
        source.spot_size = math.radians(124)
        source.spot_blend = 1.0
        source.shadow_soft_size = 2.5
        bulb = self.stage.add("bulb", source)
        bulb.location = (x, -y, height)
        # The shade hangs a little turned toward the middle of the desk.
        bulb.rotation_euler = (math.radians(-6), math.radians(-8), 0)
        return bulb


def middle_of(anchor, frame):
    """Where the middle of a shot's frame is on the plate."""
    fx, fy, fw, fh = frame
    return anchor.matrix_world @ Vector((fx + fw / 2, -(fy + fh / 2), 0))


def show(objects, seen):
    for obj in objects:
        obj.visible_camera = seen


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
    parser.add_argument("--passes", nargs="*", default=["day", "lamp"])
    parser.add_argument("--shot", help="photograph this one shot on a stand of its own, as a proof, and nothing else")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])

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
    wanted = [shot for spec in PROPS.values() for shot in spec["shots"]]
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
    layered = [obj for shot in LAYERS for obj in desk.parts.get(shot, [])]
    everything = [obj for _, _, objects in desk.props.values() for obj in objects]
    raw = os.path.join(tempfile.gettempdir(), "desk.exr")
    if args.proofs:
        os.makedirs(args.proofs, exist_ok=True)
    named = f"desk-{args.plate}"

    def layers(suffix, exposure):
        """Each layer on its own, cropped square round its object, with everything else still there to light it."""
        show(everything, False)
        for shot, prop in LAYERS.items():
            parts = desk.parts.get(shot)
            if not parts:
                continue
            show(parts, True)
            desk.crop(shot, prop)
            layer = stage._expose(raw)
            scene.render.use_border = False
            develop(layer, np.zeros(layer.shape[:2], dtype=np.float32), os.path.join(OUT, f"{named}-{shot}{suffix}.avif"), args.proofs, f"{named}-{shot}{suffix}", exposure)
            show(parts, False)
            print(f"LAYER {shot}{suffix} {layer.shape[1]}x{layer.shape[0]}")
        show([obj for obj in everything if obj not in layered], True)

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

    # The room is turned down and the window makes up the difference, so the mat is lit as brightly as the
    # leather the page lays under the plate, which was shot in the room alone.
    daylight = white_mat()
    room.default_value = 1 - KEY_SHARE
    window = desk.key(1e5)
    lit = white_mat()
    window.data.energy = 1e5 * KEY_SHARE * daylight.mean() / max(lit.mean() - (1 - KEY_SHARE) * daylight.mean(), 1e-6)
    print(f"KEY {window.data.energy:.0f}W")

    if "day" in args.passes:
        # The objects, the mat unseen but lighting them from below and showing in them.
        show(layered, False)
        pixels = stage._expose(raw)
        print(f"OBJECTS {time.time() - started:.0f}s")

        # The mat alone, catching the shadows of everything over it under the same light.
        show(everything, False)
        for obj in desk.shadowless:
            obj.hide_render = True
        floor.visible_camera = True
        floor.is_shadow_catcher = True
        rows, cols = pixels.shape[:2]
        soft = stage._expose(raw, 50, samples=max(32, args.samples // 2))[..., 3]
        soft = np.repeat(np.repeat(soft, 2, axis=0), 2, axis=1)
        soft = np.pad(soft, ((0, max(0, rows - soft.shape[0])), (0, max(0, cols - soft.shape[1]))), mode="edge")[:rows, :cols]
        develop(pixels, blur(soft, 1.0), os.path.join(OUT, f"{named}.avif"), args.proofs, named)
        print(f"PLATE {cols}x{rows} {time.time() - started:.0f}s")
        floor.visible_camera = False
        floor.is_shadow_catcher = False
        for obj in desk.shadowless:
            obj.hide_render = False
        layers("", EXPOSURE)

    if "lamp" in args.passes:
        # Night, the lamp on, the room all but dark and the studio's own lights off. The objects are
        # rendered in its light as the day's are, and the mat as a map of the light alone, which the page
        # multiplies its own leather, rules and rulers by: 1 is as bright as the mat is by day.
        window.hide_render = True
        for obj, _ in desk.gear:
            obj.hide_render = True
        room.default_value = NIGHT_ROOM
        desk.lamp(BULB)
        # The map: a white mat, with everything on it unseen but still in the way of the light.
        show(everything, False)
        floor.visible_camera = True
        paint.default_value = (0.8, 0.8, 0.8, 1)
        bx, by = desk.layout["bleed"]
        desk.camera(-bx, -by, desk.w + 2 * bx, desk.h + 2 * by, min(density, 8))
        light = stage._expose(raw, samples=max(64, args.samples // 2))[..., :3] / daylight
        light = np.clip(light * 2.0**LAMP_EXPOSURE, 0, 1)
        light = np.where(light <= 0.0031308, light * 12.92, 1.055 * light ** (1 / 2.4) - 0.055)
        light += (np.random.default_rng(1).random(light.shape, dtype=np.float32) - 0.5) / 255
        save(np.dstack((np.clip(light, 0, 1), np.ones(light.shape[:2]))).astype(np.float32), os.path.join(tempfile.gettempdir(), "desk-light.png"))
        subprocess.run(["uv", "run", "--quiet", os.path.join(HERE, "encode.py"), os.path.join(tempfile.gettempdir(), "desk-light.png"), os.path.join(OUT, f"{named}-light.avif")], check=True)
        rim = np.concatenate((light[0], light[-1], light[:, 0], light[:, -1])).mean(axis=0)
        print("LIGHT RIM #" + "".join(f"{round(float(c) * 255):02x}" for c in np.clip(rim, 0, 1)))
        if args.proofs:
            save(np.dstack((np.clip(light, 0, 1), np.ones(light.shape[:2]))).astype(np.float32), os.path.join(args.proofs, f"{named}-light.png"))

        floor.visible_camera = False
        paint.default_value = mat_colour
        show([obj for obj in everything if obj not in layered], True)
        desk.camera(0, 0, desk.w, desk.h, density)
        pixels = stage._expose(raw)
        develop(pixels, np.zeros(pixels.shape[:2], dtype=np.float32), os.path.join(OUT, f"{named}-lamp.avif"), args.proofs, f"{named}-lamp", LAMP_EXPOSURE)
        print(f"LAMP {pixels.shape[1]}x{pixels.shape[0]} {time.time() - started:.0f}s")
        layers("-lamp", LAMP_EXPOSURE)


main()
