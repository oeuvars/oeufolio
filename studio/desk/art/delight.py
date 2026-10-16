# /// script
# dependencies = ["numpy", "pillow", "scipy"]
# ///
"""Take the light the figurine was photographed in out of its photograph, leaving its paint. The light is read off the
white glaze, the least saturated parts of the cut-out, smoothed, and divided out, so the white comes to the glaze's
own white everywhere and the paint keeps its colour against it. Then the colours are carried past the outline.
Also writes the figurine's own outline, without the lamp's cord, for fit.py.
    uv run delight.py catlamp-photo.jpg catlamp-cutout.png catlamp-reference.png catlamp-matte.png"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

ref, mask, out, outline = sys.argv[1:5]
rgb = np.asarray(Image.open(ref).convert("RGB"), dtype=np.float32) / 255
lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
m = np.asarray(Image.open(mask).convert("L"), dtype=np.float32) / 255
# The cut-out loses the pink inside of the far ear, inside its dark rim: close it there.
ear = np.zeros_like(m, dtype=bool)
ear[560:690, 120:300] = True
closed = ndimage.binary_closing(m > 0.5, structure=np.ones((3, 3)), iterations=10)
m = np.where(ear & closed, 1.0, m)
m = np.where(ear & ndimage.binary_fill_holes(ndimage.binary_closing(m > 0.05, iterations=4)), 1.0, m)
# It keeps the black cord where it goes into the tip of the tail: that is the lamp's, not the figurine's.
cord = np.zeros_like(m, dtype=bool)
cord[30:110, 480:590] = True
cord &= rgb.max(-1) < 0.3
cord = ndimage.binary_dilation(cord, iterations=2) & (np.indices(m.shape)[1] < 590)
m = np.where(cord, 0.0, m)
# Between her far foreleg and her near paw the table shows only as a hairline of shadow: the two touch there.
crease = np.zeros_like(m, dtype=bool)
crease[880:1010, 0:300] = True
photographed = m > 0.5
m = np.where(crease & ndimage.binary_closing(photographed, structure=np.ones((3, 3)), iterations=4), np.maximum(m, 1.0), m)
Image.fromarray((m * 255).astype(np.uint8), "L").save(outline)
# The shadow in it is the table's, not paint: the crease takes the paint either side of it.
inside = ndimage.binary_erosion(photographed, iterations=3)


def fill(values, known, widest=64):
    """Each unknown pixel takes the average of the known ones round it, from the smallest neighbourhood that has
    enough of them: smooth, with no seams where one source gives way to the next."""
    known = known.astype(np.float32)
    out = np.where(known[..., None] > 0, values, 0.0)
    left = known < 1
    sigma = 1.5
    while left.any() and sigma <= widest:
        weight = ndimage.gaussian_filter(known, sigma)
        blurred = np.dstack([ndimage.gaussian_filter(values[..., c] * known, sigma) for c in range(values.shape[-1])])
        ready = left & (weight > 0.15)
        out[ready] = blurred[ready] / weight[ready, None]
        left &= ~ready
        sigma *= 1.5
    if left.any():
        _, (iy, ix) = ndimage.distance_transform_edt(left, return_indices=True)
        out[left] = out[iy, ix][left]
    return out


hi, lo = lin.max(-1), lin.min(-1)
sat = (hi - lo) / np.maximum(hi, 1e-4)
white = inside & (sat < 0.32) & (hi > 0.12)
# The light, averaged over the white near each pixel: first over a wide neighbourhood, then over ever closer ones
# wherever they hold enough white, each blended in by how much, so it has no edge where one gives way to the next.
light = None
for sigma in (240, 120, 64, 40, 22):
    weight = ndimage.gaussian_filter(white.astype(np.float32), sigma)
    here = np.dstack([ndimage.gaussian_filter(lin[..., c] * white, sigma) for c in range(3)]) / np.maximum(weight, 1e-4)[..., None]
    share = 1.0 if light is None else np.clip(weight / 0.3, 0, 1)[..., None]
    light = here if light is None else light + (here - light) * share
# The glaze's own highlights are the room's, not the paint: fill them from the paint round them.
shine = inside & (lin.mean(-1) > 0.55) & (sat < 0.3)
shine = ndimage.binary_dilation(shine, iterations=3) & inside
glaze = np.array([0.92, 0.83, 0.70])  # the glaze's white, linear (#f6ebda)
albedo = np.clip(lin / np.maximum(light, 1e-3) * glaze, 0, 1)
albedo = fill(albedo, inside & ~shine)
# Past the outline the colours carry on as they were at its edge, a little blurred.
albedo = fill(albedo, inside)
srgb = np.where(albedo <= 0.0031308, albedo * 12.92, 1.055 * albedo ** (1 / 2.4) - 0.055)
grown = ndimage.binary_dilation(m > 0.5, iterations=24)
alpha = ndimage.gaussian_filter(grown.astype(np.float32), 4)
Image.fromarray((np.dstack((srgb, alpha)) * 255).clip(0, 255).astype(np.uint8), "RGBA").save(out)
