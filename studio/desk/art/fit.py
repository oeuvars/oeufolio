# /// script
# dependencies = ["numpy", "pillow", "scipy"]
# ///
"""Fit the cat lamp's modelled shape to the figurine's outline in its photograph. The modelled cat is drawn through the
camera solved from the photograph (Blender runs this file for that), and compared with the outline delight.py wrote.
First a smooth move across the picture is found that carries the modelled outline onto the photographed one; then
the moved cat is drawn again, and for each pixel this keeps how far outside the photographed outline it lies, and how
far the moved shape still falls short of the outline round it, both in pixels. objects/catlamp.py moves the shape by
the first, then grows it by the one and draws it in to the other. Rerun after changing the modelled shape.
    uv run fit.py"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "catlamp-fit.npz")


def outline(path, moved):
    """In Blender: the modelled cat alone, unfitted or only moved, white on nothing, through the photograph's camera."""
    import json

    sys.path.insert(0, os.path.dirname(HERE))
    import bpy
    from mathutils import Matrix, Vector

    from objects import catlamp
    from stage import Stage

    if not moved:
        catlamp.FIT = None
    catlamp.photographed = lambda *_: None
    stage = Stage(tempfile.gettempdir(), tempfile.gettempdir(), 1, 1)
    stage.clear()
    stage.shoot = lambda *_, **__: None
    catlamp.build(stage)
    scene = bpy.context.scene
    for obj in scene.objects:
        obj.hide_render = obj.name != "cat"
    with open(catlamp.REFERENCE_CAMERA) as file:
        solved = json.load(file)
    ox, oy = catlamp.ORIGIN
    optics = bpy.data.cameras.new("photograph")
    optics.sensor_fit = "VERTICAL"
    optics.sensor_height = 36
    optics.lens = solved["f"]
    optics.clip_end = 1000
    camera = stage.add("photograph", optics)
    camera.matrix_world = Matrix.Translation(Vector(solved["C"]) + Vector((ox, -oy, 0))) @ Matrix(solved["R"]).transposed().to_4x4()
    scene.camera = camera
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.film_transparent = True
    scene.render.resolution_x, scene.render.resolution_y = catlamp.COLS, catlamp.ROWS
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def draw(moved):
    import numpy as np
    from PIL import Image

    with tempfile.TemporaryDirectory() as scratch:
        drawn = os.path.join(scratch, "outline.png")
        command = ["blender", "-b", "--factory-startup", "-P", __file__, "--", drawn] + (["moved"] if moved else [])
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
        return np.asarray(Image.open(drawn).convert("RGBA"))[..., 3] > 127


def photographed():
    import numpy as np
    from PIL import Image

    return np.asarray(Image.open(os.path.join(HERE, "catlamp-matte.png")).convert("L")) > 127


def signed(mask):
    from scipy import ndimage

    return ndimage.distance_transform_edt(~mask) - ndimage.distance_transform_edt(mask)


def overlap(photo, model):
    return round(float((photo & model).sum() / (photo | model).sum()), 4)


def move(photo, model):
    """The move, in pixels down and across, that the model's outline is read through to lie on the photograph's: each
    pixel is pushed along the model's outline toward where the photograph's is, and the whole is smoothed after every
    push, so it stays a slow, even move over the picture."""
    import numpy as np
    from scipy import ndimage

    target = np.clip(signed(photo), -40, 40)
    source = np.clip(signed(model), -40, 40)
    rows, cols = np.mgrid[: photo.shape[0], : photo.shape[1]].astype(np.float32)
    down = np.zeros_like(rows)
    across = np.zeros_like(rows)
    for _ in range(400):
        seen = ndimage.map_coordinates(source, [rows + down, cols + across], order=1, mode="nearest")
        gy, gx = np.gradient(seen)
        miss = seen - target
        norm = gx**2 + gy**2 + miss**2
        push = np.where(norm > 1e-6, miss / np.maximum(norm, 1e-6), 0.0)
        down = ndimage.gaussian_filter(down - push * gy, 4)
        across = ndimage.gaussian_filter(across - push * gx, 4)
    moved = ndimage.map_coordinates(source, [rows + down, cols + across], order=1, mode="nearest") < 0
    print("moved overlap", overlap(photo, moved), "most moved", round(float(np.hypot(down, across).max()), 1))
    return down.astype(np.float32), across.astype(np.float32)


def residual(photo, model):
    import numpy as np
    from scipy import ndimage

    # Where the photograph shows the figurine and the model does not, how far it is from the model's edge; spread back
    # to the model's edge, no further than that, so a part in front is not grown over what the photograph shows behind
    # it; smoothed, and a little over, since the shape is drawn in again past the photographed outline.
    short = np.where(photo & ~model, ndimage.distance_transform_edt(~model), 0.0)
    grow = np.zeros_like(short)
    low = 0.0
    for high in (3, 6, 12, 24, 48):
        reach = high + 3
        disc = np.hypot(*np.mgrid[-reach : reach + 1, -reach : reach + 1]) <= reach
        band = np.where((short > low) & (short <= high), short, 0.0)
        grow = np.maximum(grow, ndimage.grey_dilation(band, footprint=disc))
        low = high
    grow = ndimage.gaussian_filter(grow, 8)
    grow = np.where(grow > 0.5, grow * 1.3 + 1.0, 0.0)
    past = np.where(model & ~photo, ndimage.distance_transform_edt(model), 0.0)
    print("most short", round(float(short.max()), 1), "most past", round(float(past.max()), 1))
    # The cut-out's edge is a little ragged, pixel to pixel: drawing the shape in by it would ridge the glaze.
    return ndimage.gaussian_filter(signed(photo), 2).astype(np.float32), grow.astype(np.float32)


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
    except ImportError:
        import numpy as np

        photo = photographed()
        model = draw(moved=False)
        print("modelled overlap", overlap(photo, model))
        down, across = move(photo, model)
        np.savez_compressed(OUT, down=down, across=across)
        model = draw(moved=True)
        print("moved cat's overlap", overlap(photo, model))
        outside, grow = residual(photo, model)
        np.savez_compressed(OUT, down=down, across=across, outside=outside, grow=grow)
    else:
        args = sys.argv[sys.argv.index("--") + 1 :]
        outline(args[0], "moved" in args[1:])
