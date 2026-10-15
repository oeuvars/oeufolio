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

from objects import card, catlamp, mat, name, pick, proraso, razor, record, recorder, ticket, wallet  # noqa: E402
from paint import blur  # noqa: E402
from stage import GAIN, LENS_HEIGHT, MAT, SHADOW, Stage, shoulder  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
SETS = os.path.join(HERE, "sets")
OUT = os.path.join(ROOT, "public", "objects", "mat")
LAYOUT = os.path.join(ROOT, "src", "components", "mat", "desk.json")
# Where the lens shows each layer, against where its prop lies: written here, read by the page.
LEAN = os.path.join(ROOT, "src", "components", "mat", "lean.json")
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
}
# Shots the page turns, rendered as layers of their own and left out of the plate. The reel's shot carries a
# stand-in for the reel under the hub, which the recorder's own shot has for real.
LAYERS = {"reel": "recorder"}
# Parts of a layer's shot that are round and stay put while the rest turns: they stay in the plate, shadow and all,
# and only what turns is in the layer. A spinning hub's shading does not turn with it.
STILL = {"reel": ("hub",)}
STAND_INS = {"reel": ("reel",)}
# The page shows an em of the plate at up to 22 pixels, 44 on a screen of two pixels to the point; this many leaves
# room to zoom in before the render runs out.
DENSITY = 64
EXPOSURE = 0.1
# The room is lit dimly from elsewhere, by this much of the light the leather was photographed in, and each bulb
# in the cat lamp's head gives this many watts when it is on.
ROOM = 0.04
# Moonlight through the window: the moon is a small, far source, half a degree across, so it throws hard, dark
# shadows that only soften a little away from where an object touches the mat. It comes in over the top left of
# the desk, and adds this much of the leather's light to the mat; the night sky and the dark room add a little.
WINDOW = 0.16
WINDOW_FROM = (-0.55, 0.6, 0.58)
MOON = 0.55
# How much of the moon's light is left beside the lamp's, as the camera exposes for the lamp.
LAMP_MOON = 0.25
GLOW = 28000.0
# A lens spreads a little of a light too bright for it round it: this share, over this many em.
BLOOM = (0.05, 1.2)
LAMP_EXPOSURE = 0.0
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
                if was in STILL.get(shot, ()):
                    obj["still"] = True
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
        """A camera held where someone at the desk holds a phone over it, at the plate's eye (x, y and height in
        em, the near side of the desk being down the page), framing the rectangle of the mat from (x0, y0), w by
        h em. Its back is kept level with the desk and the lens shifted onto the frame, as an architect's camera
        is: the mat and everything flat on it are drawn true, and anything standing on it shows its side toward
        the eye, the lamp its front."""
        scene = bpy.context.scene
        camera = scene.camera
        if camera is None:
            optics = bpy.data.cameras.new("overhead")
            optics.type = "PERSP"
            optics.sensor_fit = "AUTO"
            optics.sensor_width = 36.0
            optics.clip_end = 1000
            camera = scene.camera = self.stage.add("overhead", optics)
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

    def window(self, power):
        """The moon, through the window over the top left of the desk: parallel light from a disk MOON degrees
        across, its colour the cool of moonlight. power is in watts to the square metre, as Blender's sun is."""
        source = bpy.data.lights.new("moon", "SUN")
        source.angle = math.radians(MOON)
        source.energy = power
        source.color = (0.8, 0.87, 1.0)
        light = self.stage.add("moon", source)
        towards = Vector(WINDOW_FROM).normalized()
        light.rotation_euler = (-towards).to_track_quat("-Z", "Y").to_euler()
        return light

    def glow(self, power):
        """Switch the cat lamp: each bulb in its head gives this many watts, or none."""
        for obj in bpy.context.scene.objects:
            if obj.get("bulb"):
                obj.data.energy = power


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
    for obj in objects:
        obj.visible_camera = seen


def rolled(x, knee=0.72, brightest=6.0, soft=0.5):
    """Highlights as a phone camera keeps them in a dim room with a lamp in it: linear up to the knee, then
    compressed on a log scale, so that the lamp's glass, tens of times brighter than the desk it lights, still
    shows its shape instead of burning out flat."""
    over = np.maximum(x - knee, 0)
    return np.where(x <= knee, x, knee + (1 - knee) * np.minimum(np.log1p(over / soft) / np.log1p(brightest / soft), 1))


def develop(pixels, cast, out, proofs, name, exposure=EXPOSURE, bloom=None):
    """The pixels as an AVIF with straight alpha, the shadow on the mat under them, as Stage.develop does it.
    bloom is (share, sigma in pixels): the light over white spread round where it is, as a lens spreads it.
    With it, the highlights are rolled off as a camera exposing for a lit room does."""
    light = pixels[..., :3] * GAIN * 2.0**exposure
    if bloom:
        share, sigma = bloom
        hot = np.maximum(light - 1.0, 0)
        light = light + share * np.dstack([blur(hot[..., c], sigma) for c in range(3)]) + 0.25 * share * np.dstack([blur(hot[..., c], 4 * sigma) for c in range(3)])
    cover = pixels[..., 3]
    alpha = np.clip(np.maximum(cover, light.max(axis=-1)), 0, 1)
    colour = (rolled if bloom else shoulder)(light / np.maximum(alpha, 1e-6)[..., None])
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
    parser.add_argument("--passes", nargs="*", default=["off", "lamp"])
    parser.add_argument("--shot", help="photograph this one shot on a stand of its own, as a proof, and nothing else")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    if args.scale != 1:
        # A proof at another scale never takes the place of the page's plates, or the page would show a plate of
        # one render with a layer of another.
        global OUT, LEAN
        OUT = args.proofs or tempfile.mkdtemp(prefix="desk-")
        LEAN = os.path.join(OUT, "lean.json")
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
    layered = [obj for shot in LAYERS for obj in desk.parts.get(shot, []) if not obj.get("still")]
    everything = [obj for _, _, objects in desk.props.values() for obj in objects]
    raw = os.path.join(tempfile.gettempdir(), "desk.exr")
    if args.proofs:
        os.makedirs(args.proofs, exist_ok=True)
    named = f"desk-{args.plate}"

    def layers(suffix, exposure):
        """Each layer on its own, cropped square round its object, with everything else still there to light it.
        Where the lens shows each, against where its prop lies, goes to LEAN for the page."""
        show(everything, False)
        leans = {}
        for shot, prop in LAYERS.items():
            parts = [obj for obj in desk.parts.get(shot, []) if not obj.get("still")]
            if not parts:
                continue
            show(parts, True)
            cast(parts, True)
            leans[shot] = desk.crop(shot, prop, parts)
            layer = stage._expose(raw)
            scene.render.use_border = False
            develop(layer, np.zeros(layer.shape[:2], dtype=np.float32), os.path.join(OUT, f"{named}-{shot}{suffix}.avif"), args.proofs, f"{named}-{shot}{suffix}", exposure)
            show(parts, False)
            cast(parts, False)
            print(f"LAYER {shot}{suffix} {layer.shape[1]}x{layer.shape[0]}")
        known = json.load(open(LEAN)) if os.path.exists(LEAN) else {}
        known.setdefault(args.plate, {}).update(leans)
        with open(LEAN, "w") as file:
            file.write(json.dumps(known, indent=2) + "\n")
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

    # The leather the page lays under the plate was photographed in the room at full strength: that is 1 on
    # the maps of the light. The room the desk is in is lit dimly, and the lamp does the rest.
    daylight = white_mat()
    room.default_value = ROOM
    for obj, _ in desk.gear:
        obj.hide_render = True
    dim = white_mat()
    window = desk.window(1.0)
    lit = white_mat()
    window.data.energy = WINDOW * daylight.mean() / max(lit.mean() - dim.mean(), 1e-6)
    print(f"MOON {window.data.energy:.3f}W/m2")
    off = white_mat() / daylight
    print("DARK #" + "".join(f"{round(float(c) * 255):02x}" for c in np.clip(np.where(off <= 0.0031308, off * 12.92, 1.055 * off ** (1 / 2.4) - 0.055), 0, 1)))

    def light_map(suffix):
        """The light on the mat as a map, which the page multiplies its own leather, rules and rulers by: a white
        mat rendered with everything on it unseen but still in the way of the light, so their shadows, soft and
        hard, and the dark where they touch it, are the light's own. 1 is the light the leather was photographed
        in. Returns the colour round its edge, which the page carries on past it."""
        show(everything, False)
        floor.visible_camera = True
        paint.default_value = (0.8, 0.8, 0.8, 1)
        bx, by = desk.layout["bleed"]
        desk.camera(-bx, -by, desk.w + 2 * bx, desk.h + 2 * by, min(density, MAP_DENSITY))
        light = stage._expose(raw, samples=max(128, args.samples // 2))[..., :3] / daylight
        # Where the light is brighter on the leather than it was photographed, it eases into that, as film does.
        light = shoulder(light * 2.0**LAMP_EXPOSURE)
        light = np.where(light <= 0.0031308, light * 12.92, 1.055 * light ** (1 / 2.4) - 0.055)
        light += (np.random.default_rng(1).random(light.shape, dtype=np.float32) - 0.5) / 255
        mapped = np.dstack((np.clip(light, 0, 1), np.ones(light.shape[:2]))).astype(np.float32)
        save(mapped, os.path.join(tempfile.gettempdir(), "desk-light.png"))
        subprocess.run(["uv", "run", "--quiet", os.path.join(HERE, "encode.py"), os.path.join(tempfile.gettempdir(), "desk-light.png"), os.path.join(OUT, f"{named}-{suffix}.avif")], check=True)
        if args.proofs:
            save(mapped, os.path.join(args.proofs, f"{named}-{suffix}.png"))
        floor.visible_camera = False
        paint.default_value = mat_colour
        show([obj for obj in everything if obj not in layered], True)
        desk.camera(0, 0, desk.w, desk.h, density)
        rim = np.concatenate((light[0], light[-1], light[:, 0], light[:, -1])).mean(axis=0)
        return "#" + "".join(f"{round(float(c) * 255):02x}" for c in np.clip(rim, 0, 1))

    if "off" in args.passes:
        # The lamp off: the dim room, lit mostly by the window. The objects in that light, the mat unseen but
        # lighting them from below and showing in them, and the light on the mat as a map.
        show(layered, False)
        cast(layered, False)
        pixels = stage._expose(raw)
        develop(pixels, np.zeros(pixels.shape[:2], dtype=np.float32), os.path.join(OUT, f"{named}.avif"), args.proofs, named)
        print(f"PLATE {pixels.shape[1]}x{pixels.shape[0]} {time.time() - started:.0f}s")
        print("DARK RIM " + light_map("dark"))
        layers("", EXPOSURE)

    if "lamp" in args.passes:
        # The lamp on, in the same dim room. The objects are rendered in its light, and the mat as a map of it.
        # The lamp, a few hand-widths from everything on the desk, outshines the moon there many times over:
        # the camera exposes for the lamp, and the moonlight is left a faint cool fill.
        desk.glow(GLOW)
        window.data.energy *= LAMP_MOON
        print("LIGHT RIM " + light_map("light"))
        pixels = stage._expose(raw)
        develop(pixels, np.zeros(pixels.shape[:2], dtype=np.float32), os.path.join(OUT, f"{named}-lamp.avif"), args.proofs, f"{named}-lamp", LAMP_EXPOSURE, (BLOOM[0], BLOOM[1] * density))
        print(f"LAMP {pixels.shape[1]}x{pixels.shape[0]} {time.time() - started:.0f}s")
        layers("-lamp", LAMP_EXPOSURE)


main()
