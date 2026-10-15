"""The surface the contact page's ticket lies on: red top-grain leather, photographed on the same copy stand as the
ticket, under the same light. Run from the repository root:

    blender -b --factory-startup -P studio/ticket/leather.py -- [--scale 0.5] [--samples 64]

Top grain is the outer face of the hide with its natural grain left on: a field of irregular pebbles of every size,
packed close, with narrow creases between them, and here and there a long crease running across where the hide
flexed on the animal. The relief, the shine and the unevenness of the tone are taken from a scan of real pebbled
hide (SCAN, ambientCG), not grown, and the hide is dyed DYE. The scan repeats seamlessly, one to every TILE em.

Writes public/objects/leather.avif, one square of the hide, which the page repeats across the contact strip and its
tab, TILE em across. scene.py lays the same hide under the ticket. Set OEUSUME if that checkout is not in
~/Documents/oeusume.
"""

import argparse
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OEUSUME = os.environ.get("OEUSUME", os.path.expanduser("~/Documents/oeusume"))
sys.path.insert(0, os.path.join(OEUSUME, "studio"))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

import key  # noqa: E402
import stage as stage_module  # noqa: E402
from stage import Stage  # noqa: E402
from stock import Sheet  # noqa: E402

OUT = os.path.join(ROOT, "public", "objects")
# The scan of real hide: ambientCG's Leather030, pebbled top grain, its pebbles about 1.5 mm across, some 80 of them
# across the scan, so the scan is about 120 mm of hide: 30 em at the ticket's 4 em to the centimetre.
SCAN = "Leather030"
TILE = 30.0  # em to one scan, and the square the page repeats
DYE = "#6c0407"  # the hide's colour as it reflects light: an oxblood crimson, the scan's own tone laid over it
ROUGH = 0.62  # a satin wax finish; the scan's roughness varies it
RELIEF = 2.2  # the scan's relief, raised to read at the size the page shows it
SOFT = 0.5  # the sun's share of the key lamp's light: enough to rake the pebbles, not to glare
SHARP = 0.75  # pixels to the page's: the page shows about 27 pixels to the em
QUALITY = 86
EXPOSURE = -1.6


def skin(stage, name, w, h):
    """A stretch of the hide w by h em, its top left at the origin: the scan of real pebbled top grain (SCAN) for its
    relief, its shine and the unevenness of its tone, one scan to every TILE em, re-dyed to DYE. Returns the object."""
    # Everything that varies comes from the scan, so the painted sheet under it is one flat colour, drawn coarse.
    sheet = Sheet(w, h, DYE, rough=ROUGH, density=0.25)
    sheet.build(stage, name, thickness=0.0, scan=SCAN, scan_size=TILE, scan_normal=RELIEF, scan_rough=1.0, scan_colour=1.0, specular=0.28)
    return bpy.data.objects[name]


def hide(stage, x0, y0, w, h):
    """A stretch of the hide w by h em with its top left at (x0, y0) on the page, lying at the height of the mat, for
    something to lie on. The scan repeats from the page's origin, a TILE at a time, as the page's own does."""
    obj = skin(stage, "hide", w, h)
    obj.location = (x0, -y0, 0)
    return obj


def leather(stage):
    """The square the page repeats under the contact strip: three squares across, the frame the middle one, so the
    square meets itself on every side. The lens is left out: it leans the light across the frame, which would show
    as a step where two squares meet."""
    hide(stage, -TILE, -TILE, 3 * TILE, 3 * TILE)
    # Lit as the contact scene lights the hide: the stand's room, and the key lamp up to the left (key.py), which rakes
    # across the pebbles a little, lighting the side of each that faces it. Here the lamp is a sun from the same
    # direction, as wide as the lamp looks from the table, so it lights every point of the square alike and the square
    # still meets itself on every side; softer than the lamp, so the hide is not glaring.
    sun = bpy.data.lights.new("key", "SUN")
    sun.angle = 2 * math.atan(key.SIZE / 2 / key.DISTANCE)
    sun.energy = SOFT * key.POWER / (math.pi * key.DISTANCE**2)
    lamp = bpy.data.objects.new("key", sun)
    lamp.rotation_euler = (-key.FROM).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(lamp)
    # The hide lies at the stand's mat's height, so the mat, which would shade it, is taken away.
    stage.shoot("leather", (0, 0, TILE, TILE), exposure=EXPOSURE, lens=False, sharp=SHARP, mat=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--samples", type=int, default=96)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    stage_module.MAT = DYE
    stage = Stage(OUT, None, scale=args.scale, samples=args.samples)
    stage.clear()
    leather(stage)
    # Again, smaller: the stage encodes every shot as it does the objects, near lossless.
    script = f"""
from PIL import Image
path = {os.path.join(OUT, "leather.avif")!r}
Image.open(path).convert("RGB").save(path, quality={QUALITY}, subsampling="4:2:0", speed=2)
"""
    subprocess.run(["uv", "run", "--quiet", "--with", "pillow>=11.3", "python", "-I", "-c", script], check=True)


if __name__ == "__main__":
    main()
