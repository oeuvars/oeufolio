"""The copy stand: an overhead camera in a photo studio. One set-up lights every object, so they read as one photograph.

The room is an HDRI of a real studio, turned so its big octabox hangs over the top right of the frame,
the side the page hangs its lamp on.
A second pass under even light records the soft shadow an object leaves where it meets the mat.
A set can be saved as a .blend, changed by hand in Blender and rendered from that file."""

import math
import os
import subprocess
import sys
import tempfile
import time

import bpy
import numpy as np
from mathutils import Quaternion, Vector

from paint import blur, linear

PX_PER_EM = 48
MAT = "#236653"
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
ROOM = "studio_small_08.hdr"
# Where the octabox sits in the HDRI, and where the stand wants it: up and to the top right of the page.
BOX_IN_ROOM = Vector((-0.618, -0.747, 0.242)).normalized()
BOX_ON_STAND = Vector((0.375, 0.375, 0.848)).normalized()
ROOM_ROLL = math.radians(0)
ROOM_STRENGTH = 1.0
# Gain per channel that puts a flat white card under this room at 0.9 and takes the cool cast out of it.
# Measured with the meter shot.
GAIN = np.array([0.702, 0.678, 0.617], dtype=np.float32)
# The camera is orthographic, which would make every flat glossy surface reflect a single point of the room.
# Shading normals lean as if the lens were this far above the object, so reflections sweep across it.
LENS_HEIGHT = 55.0
SHADOW = np.array([0.008, 0.014, 0.014])


def shoulder(x, knee=0.72):
    """Film-like highlights: linear up to the knee, then easing into white instead of clipping."""
    over = np.maximum(x - knee, 0)
    return np.where(x <= knee, x, knee + (1 - knee) * (1 - np.exp(-over / (1 - knee))))


class Stage:
    def __init__(self, out_dir, proof_dir=None, scale=1.0, samples=160, scene_dir=None):
        self.out_dir = out_dir
        self.proof_dir = proof_dir
        self.scale = scale
        self.samples = samples
        self.scene_dir = scene_dir

    def _device(self):
        """The graphics card is a preference, so no .blend carries it."""
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for device in prefs.devices:
            device.use = device.type == "METAL"

    def clear(self):
        """Empty scene with the renderer set up. Everything from the last shot is gone."""
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self._device()
        scene = bpy.context.scene
        scene.render.engine = "CYCLES"
        scene.cycles.device = "GPU"
        scene.cycles.samples = self.samples
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.adaptive_threshold = 0.008
        scene.cycles.use_denoising = True
        scene.cycles.max_bounces = 8
        scene.cycles.transparent_max_bounces = 12
        scene.cycles.sample_clamp_indirect = 6.0
        scene.render.film_transparent = True
        scene.cycles.film_transparent_glass = True
        scene.view_settings.view_transform = "Standard"
        scene.view_settings.look = "None"
        scene.render.image_settings.file_format = "OPEN_EXR"
        scene.render.image_settings.color_mode = "RGBA"
        scene.render.image_settings.color_depth = "32"
        scene.world = bpy.data.worlds.new("room")
        scene.world.use_nodes = True
        return scene

    def open(self, path):
        """A set saved by an earlier run, with whatever has been changed in it by hand since."""
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(path))
        self._device()
        if "shot" not in bpy.context.scene:
            sys.exit(f"{path} is not a set saved with --scenes")

    def add(self, name, data):
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        return obj

    def _room(self, cx, cy, strength=1.0, mat=True):
        scene = bpy.context.scene
        nodes, links = scene.world.node_tree.nodes, scene.world.node_tree.links
        background = nodes["Background"]
        coord = nodes.new("ShaderNodeTexCoord")
        turn = nodes.new("ShaderNodeMapping")
        aim = BOX_ON_STAND.rotation_difference(BOX_IN_ROOM) @ Quaternion(BOX_ON_STAND, ROOM_ROLL)
        turn.inputs["Rotation"].default_value = aim.to_euler()
        room = nodes.new("ShaderNodeTexEnvironment")
        room.image = bpy.data.images.load(os.path.join(ASSETS, ROOM))
        # A second, even room for the shadow pass. The switch picks between them.
        switch = nodes.new("ShaderNodeMix")
        switch.name = "even"
        switch.data_type = "RGBA"
        switch.inputs[0].default_value = 0.0
        switch.inputs[7].default_value = (1, 1, 1, 1)
        links.new(coord.outputs["Generated"], turn.inputs["Vector"])
        links.new(turn.outputs["Vector"], room.inputs["Vector"])
        links.new(room.outputs["Color"], switch.inputs[6])
        links.new(switch.outputs[2], background.inputs["Color"])
        background.inputs["Strength"].default_value = ROOM_STRENGTH * strength

        # The mat: seen by reflections and bounce light, and by the camera only as a shadow.
        ground = bpy.data.meshes.new("mat")
        ground.from_pydata([(-90, -90, 0), (90, -90, 0), (90, 90, 0), (-90, 90, 0)], [], [(0, 1, 2, 3)])
        floor = self.add("mat", ground)
        floor["stand"] = "mat"
        floor.location = (cx, cy, 0)
        floor.visible_camera = False
        floor.hide_render = not mat
        paint = bpy.data.materials.new("mat")
        paint.use_nodes = True
        shader = paint.node_tree.nodes["Principled BSDF"]
        shader.inputs["Base Color"].default_value = (*linear(MAT), 1)
        shader.inputs["Roughness"].default_value = 0.8
        ground.materials.append(paint)
        return floor

    def _lens(self, cx, cy):
        """Lean every shading normal away from the centre of the frame, as a real lens would see it."""
        lean = 1 / (2 * LENS_HEIGHT)
        for material in bpy.data.materials:
            tree = material.node_tree
            shader = tree.nodes.get("Principled BSDF") if tree else None
            if shader is None or material.name == "mat":
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
            for name in ("Normal", "Coat Normal"):
                socket = shader.inputs[name]
                base = socket.links[0].from_socket if socket.is_linked else geometry.outputs["Normal"]
                tilted = nodes.new("ShaderNodeVectorMath")
                tilted.operation = "ADD"
                unit = nodes.new("ShaderNodeVectorMath")
                unit.operation = "NORMALIZE"
                links.new(base, tilted.inputs[0])
                links.new(flat.outputs[0], tilted.inputs[1])
                links.new(tilted.outputs[0], unit.inputs[0])
                links.new(unit.outputs[0], socket)

    def _expose(self, path, percentage=100, samples=None):
        """Render to a float file and return its pixels, rows from the top, premultiplied and scene linear."""
        scene = bpy.context.scene
        scene.render.resolution_percentage = percentage
        scene.cycles.samples = samples or self.samples
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        image = bpy.data.images.load(path)
        cols, rows = image.size
        pixels = np.empty(cols * rows * 4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        bpy.data.images.remove(image)
        os.remove(path)
        return pixels.reshape(rows, cols, 4)[::-1]

    def _card(self, cx, cy, strength):
        """A big white card over the set, feathered at its edges. Bare metal has nothing to shine with otherwise."""
        panel = bpy.data.meshes.new("card")
        panel.from_pydata([(-26, -26, 0), (26, -26, 0), (26, 26, 0), (-26, 26, 0)], [], [(0, 1, 2, 3)])
        panel.uv_layers.new().data.foreach_set("uv", [0, 0, 1, 0, 1, 1, 0, 1])
        card = self.add("card", panel)
        card["stand"] = "card"
        card.location = (cx + 7, cy + 5, 32)
        card.visible_camera = False
        card.visible_shadow = False
        glow = bpy.data.materials.new("card")
        glow.use_nodes = True
        nodes, links = glow.node_tree.nodes, glow.node_tree.links
        nodes.clear()
        coord = nodes.new("ShaderNodeTexCoord")
        centre = nodes.new("ShaderNodeMapping")
        centre.inputs["Location"].default_value = (-1, -1, 0)
        centre.inputs["Scale"].default_value = (2, 2, 1)
        fade = nodes.new("ShaderNodeTexGradient")
        fade.gradient_type = "QUADRATIC_SPHERE"
        level = nodes.new("ShaderNodeMath")
        level.operation = "MULTIPLY"
        level.inputs[1].default_value = strength
        emit = nodes.new("ShaderNodeEmission")
        clear = nodes.new("ShaderNodeBsdfTransparent")
        both = nodes.new("ShaderNodeAddShader")
        out = nodes.new("ShaderNodeOutputMaterial")
        links.new(coord.outputs["UV"], centre.inputs["Vector"])
        links.new(centre.outputs["Vector"], fade.inputs["Vector"])
        links.new(fade.outputs[0], level.inputs[0])
        links.new(level.outputs[0], emit.inputs["Strength"])
        links.new(emit.outputs[0], both.inputs[0])
        links.new(clear.outputs[0], both.inputs[1])
        links.new(both.outputs[0], out.inputs["Surface"])
        panel.materials.append(glow)
        return card

    def shoot(
        self,
        name,
        frame,
        bleed=0.0,
        shadow=0.0,
        exposure=0.0,
        lens=True,
        card=0.0,
        sharp=1.0,
        mat_through_glass=True,
        shadowless=(),
        room=1.0,
        mat=True,
        eye=None,
        level=0.0,
        bloom=0.0,
    ):
        """Build the stand around what is on it and render the frame (x, y, width, height in em, y down from
        the object's top left) to an AVIF. With a scene directory the set is saved there and not rendered.
        bleed widens the frame on every side. shadow is how dark the contact shadow in that margin gets.
        card hangs a white card overhead for bare metal to reflect.
        sharp multiplies the resolution, for objects the page shows larger than one em to sixteen pixels.
        shadowless lists objects that leave no contact shadow, such as glass.
        room scales the light of the studio, down to none for something that lights itself.
        mat=False takes the mat away, for something that hangs in the air and not over the desk.
        eye swaps the copy lens for a real one that many em above the plane at height level, where the frame
        is measured, so whatever is nearer the lens is larger. Such a shot wants lens=False.
        bloom is the share of the light a lens scatters round a source bright enough to burn out."""
        x, y, w, h = frame
        x, y, w, h = x - bleed, y - bleed, w + 2 * bleed, h + 2 * bleed
        cx, cy = x + w / 2, -(y + h / 2)
        scene = bpy.context.scene
        floor = self._room(cx, cy, room, mat)
        floor.visible_transmission = mat_through_glass
        if lens:
            self._lens(cx, cy)
        if card:
            self._card(cx, cy, card)
        for obj in shadowless:
            obj["stand"] = "shadowless"

        optics = bpy.data.cameras.new("overhead")
        if eye:
            optics.type = "PERSP"
            optics.angle = 2 * math.atan(max(w, h) / 2 / eye)
        else:
            optics.type = "ORTHO"
            optics.ortho_scale = max(w, h)
        optics.clip_end = 300
        camera = self.add("overhead", optics)
        camera.location = (cx, cy, level + eye if eye else 120)
        scene.camera = camera
        density = PX_PER_EM * sharp
        scene.render.resolution_x = round(w * density)
        scene.render.resolution_y = round(h * density)
        # What develop needs to know about the shot travels on the scene, so a saved set carries it.
        scene["shot"], scene["density"], scene["bleed"], scene["shadow"], scene["exposure"] = name, density, bleed, shadow, exposure
        scene["bloom"] = bloom
        if self.scene_dir:
            return self._keep(name)
        return self.develop()

    def _keep(self, name):
        """Save the set as a .blend. The painted maps are packed in it. The scans and the room stay in assets."""
        for image in bpy.data.images:
            if image.filepath and not image.packed_file:
                image.filepath = bpy.path.relpath(image.filepath, start=self.scene_dir)
        path = os.path.join(self.scene_dir, f"{name}.blend")
        bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
        print(f"SCENE {name} {os.path.getsize(path) / 1e6:.1f} MB")

    def develop(self):
        """Render the set as it stands, write its AVIF and return the raw pixels."""
        scene = bpy.context.scene
        name, bleed, shadow, exposure = scene["shot"], scene["bleed"], scene["shadow"], scene["exposure"]
        density = scene["density"] * self.scale

        started = time.time()
        raw = os.path.join(tempfile.gettempdir(), f"studio-{name}.exr")
        pixels = self._expose(raw, round(100 * self.scale))
        rows, cols = pixels.shape[:2]
        light = pixels[..., :3] * GAIN * 2.0**exposure
        cover = pixels[..., 3]
        bloom = scene.get("bloom", 0.0)
        if bloom:
            # Glare: three halos from tight to wide, in em. Only a light source is bright enough for them to show.
            spread = sum(
                share * np.dstack([blur(light[..., c], reach * density) for c in range(3)])
                for reach, share in ((0.05, 0.45), (0.2, 0.35), (0.7, 0.2))
            )
            light = light + bloom * np.clip(spread, 0, None)

        cast = np.zeros((rows, cols), dtype=np.float32)
        if shadow:
            # Even light, objects hidden from the lens, the mat catching what they block.
            scene.world.node_tree.nodes["even"].inputs[0].default_value = 1.0
            scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
            for obj in scene.objects:
                if obj.get("stand") == "mat":
                    obj.visible_camera = True
                    obj.is_shadow_catcher = True
                elif obj.get("stand"):
                    obj.hide_render = True
                elif obj.type in ("MESH", "CURVES"):
                    obj.visible_camera = False
            soft = self._expose(raw, round(50 * self.scale), samples=96)[..., 3]
            soft = np.repeat(np.repeat(soft, 2, axis=0), 2, axis=1)
            soft = np.pad(soft, ((0, max(0, rows - soft.shape[0])), (0, max(0, cols - soft.shape[1]))), mode="edge")
            soft = blur(soft[:rows, :cols], 1.5)
            # The shadow has to be gone by the edge of the frame, or the frame shows as a box on the mat.
            rim = np.concatenate((soft[0], soft[-1], soft[:, 0], soft[:, -1])).mean()
            inset = np.minimum.outer(
                np.minimum(np.arange(rows), np.arange(rows)[::-1]), np.minimum(np.arange(cols), np.arange(cols)[::-1])
            )
            fade = np.clip(inset / max(1.0, bleed * density * 0.6), 0, 1)
            cast = np.clip(soft - rim, 0, None) / max(1e-6, 1 - rim) * fade * fade * (3 - 2 * fade) * shadow

        # The image holds straight alpha. Anything brighter than its own coverage, such as a reflection
        # on clear glass, has to bring its coverage up with it or it is clipped away.
        alpha = np.clip(np.maximum(cover, light.max(axis=-1)), 0, 1)
        colour = shoulder(light / np.maximum(alpha, 1e-6)[..., None])
        under = np.clip(cast, 0, 1) * (1 - alpha)
        total = alpha + under
        colour = (colour * alpha[..., None] + SHADOW * under[..., None]) / np.maximum(total, 1e-6)[..., None]
        colour = np.clip(colour, 0, 1)
        colour = np.where(colour <= 0.0031308, colour * 12.92, 1.055 * colour ** (1 / 2.4) - 0.055)
        colour += (np.random.default_rng(0).random(colour.shape, dtype=np.float32) - 0.5) / 255
        encoded = np.dstack((np.clip(colour, 0, 1), total)).astype(np.float32)

        lossless = os.path.join(tempfile.gettempdir(), f"studio-{name}.png")
        self._save(name, encoded, lossless, "PNG")
        encoder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "encode.py")
        subprocess.run(["uv", "run", "--quiet", encoder, lossless, os.path.join(self.out_dir, f"{name}.avif")], check=True)
        os.remove(lossless)
        print(f"SHOT {name} {cols}x{rows} {time.time() - started:.1f}s")
        if self.proof_dir:
            value = MAT.lstrip("#")
            mat = np.array([int(value[i : i + 2], 16) / 255 for i in (0, 2, 4)], dtype=np.float32)
            encoded[..., :3] = encoded[..., :3] * encoded[..., 3:] + mat * (1 - encoded[..., 3:])
            encoded[..., 3] = 1
            self._save(f"{name}-proof", encoded, os.path.join(self.proof_dir, f"{name}.png"), "PNG")
        return pixels

    def _save(self, name, encoded, path, file_format):
        rows, cols = encoded.shape[:2]
        image = bpy.data.images.new(name, cols, rows, alpha=True)
        image.alpha_mode = "STRAIGHT"
        image.pixels.foreach_set(encoded[::-1].ravel())
        image.filepath_raw = path
        image.file_format = file_format
        image.save(quality=90)
        bpy.data.images.remove(image)
