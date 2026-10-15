# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow>=11.3", "scipy"]
# ///
"""The cats lying about the desk beside the resume: real Turkish Vans, photographed from above as they lay (art/cats,
where they were found is in SOURCES.md), cut out and laid on the walnut as if they lay there under its lamp.

    uv run studio/resume/cats.py

Each cat is lifted from its photograph by macOS's own subject cut-out (mask.swift, so this needs a Mac), its soft
matte kept whole, so every wisp of fur at its edge stays. Where the fur is see-through at the edge it carries the
colour of what it lay on, a bedspread or a carpet; that is worked out from the photograph round it and taken back
out, so no fringe of it shows on the desk. Each photograph was taken in its own light: the white of each coat is set
to the white of the paper the resume is printed on as the desk's lamp lights it.

Then the cat's shadow, as the lamp throws it: the cat's height is reckoned from how far each point is inside its
outline, a lying cat being about as high as it is half wide, and the shadow is where that height stands between the
desk and the lamp, up to the left of it (studio/ticket/key.py), softening the further it falls; and the dark where the
fur meets the desk.

Writes public/objects/resume-cat-<name>.avif and the cats' places into src/components/resume.json.
"""

import json
import os
import subprocess
import tempfile

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ART = os.path.join(HERE, "art", "cats")
OUT = os.path.join(ROOT, "public", "objects")
FRAME = os.path.join(ROOT, "src", "components", "resume.json")
ENCODE = os.path.join(ROOT, "studio", "desk", "encode.py")

WORK = 1400  # pixels on the photograph's long side while it is worked on
PX = 96  # pixels to the em the cats are kept at: three to a pixel on the page's widest screens
BLEED = 0.5  # em round each cat for its shadow
# The paper's white under the desk's lamp, as the roll's photograph shows it (sRGB), which each coat's white is set to.
WHITE = np.array([0.79, 0.775, 0.73])
# The lamp, from the desk: up to the left of the page (key.py's FROM), about forty-four degrees up.
TOWARD = np.array([-0.8, -0.9]) / np.hypot(0.8, 0.9)  # on the page, y down
RISE = 1.15 / np.hypot(0.8, 0.9)  # the tangent of its height
SHADOW = np.array([0.025, 0.016, 0.012])  # the walnut in shade
DARK = 0.78  # how much of the light the cat keeps off the desk where it stands in the way

# The cats, in the order the page lays them: the first above the last folder's tab, the rest spread under the tag.
# Each: its photograph, how far it is turned (degrees, anticlockwise) and whether it is mirrored, the largest it may be
# across and down in em, and where its middle lies across the desk strip.
CATS = (
    ("gaze", 0, False, 1.7, 3.7, 2.15),
    ("curl", 0, False, 2.0, 2.6, 2.1),
    ("belly", 0, False, 2.0, 4.2, 2.1),
    ("ball", 0, False, 1.6, 1.6, 2.15),
    ("dream", 0, False, 2.0, 4.2, 2.1),
    ("donut", 0, False, 2.1, 2.4, 2.1),
    ("sprawl", 0, False, 2.0, 4.0, 2.15),
    ("upside", 180, False, 2.0, 4.2, 2.1),
)
ABOVE = 2.3  # em down the page to the middle of the cat above the tab


def srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def matte(source):
    """The subject mask the Mac lifts, the largest subject if it finds more than one."""
    with tempfile.TemporaryDirectory() as work:
        stem = os.path.join(work, "mask")
        subprocess.run(["xcrun", "swift", os.path.join(HERE, "mask.swift"), source, stem], check=True, capture_output=True)
        masks = [np.asarray(Image.open(os.path.join(work, f)).convert("L"), dtype=np.float32) / 255 for f in sorted(os.listdir(work))]
    return max(masks, key=lambda m: m.sum())


def soft_mean(values, weight, sigma):
    """The mean of values near each pixel, weighted, over sigma pixels."""
    w = ndimage.gaussian_filter(weight, sigma)
    return np.dstack([ndimage.gaussian_filter(values[..., c] * weight, sigma) for c in range(3)]) / np.maximum(w, 1e-6)[..., None]


def cut(name, turn, mirror, wide, tall):
    source = os.path.join(ART, f"{name}.jpg")
    image = Image.open(source).convert("RGB")
    alpha = matte(source)
    # Worked on at a size a little over what the page needs, so the blurs below stay quick.
    if alpha.shape != (image.height, image.width):
        alpha = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).resize(image.size, Image.BILINEAR), dtype=np.float32) / 255
    shrink = min(1.0, WORK / max(image.size))
    if shrink < 1:
        size = (round(image.width * shrink), round(image.height * shrink))
        image = image.resize(size, Image.LANCZOS)
        alpha = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).resize(size, Image.LANCZOS), dtype=np.float32) / 255
    rgb = np.asarray(image, dtype=np.float32) / 255
    if alpha.shape != rgb.shape[:2]:
        alpha = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).resize(image.size, Image.BILINEAR), dtype=np.float32) / 255
    # Only the cat: whatever the matte holds away from it is dropped.
    labels, count = ndimage.label(alpha > 0.5)
    if count > 1:
        sizes = ndimage.sum(np.ones_like(alpha), labels, range(1, count + 1))
        body = labels == (np.argmax(sizes) + 1)
        near = ndimage.binary_dilation(body, iterations=max(8, int(0.01 * max(alpha.shape))))
        alpha = alpha * near

    lin = srgb_to_linear(rgb)
    # What lay behind the cat, filled in under it from round it, and the cat's own colour at its edge: the observed
    # colour is the fur's over the ground's by the matte, so the fur's is what is left when the ground's is taken out.
    span = 0.004 * max(alpha.shape)
    ground = soft_mean(lin, (alpha < 0.02).astype(np.float32), 12 * span)
    solid = (alpha > 0.97).astype(np.float32)
    inner = soft_mean(lin, solid, 2 * span)
    fur = (lin - (1 - alpha[..., None]) * ground) / np.maximum(alpha[..., None], 1e-3)
    trust = np.clip((alpha - 0.15) / 0.6, 0, 1)[..., None]
    fur = np.clip(trust * fur + (1 - trust) * inner, 0, 1)
    fur = np.where(solid[..., None] > 0, lin, fur)

    # Each coat's white to the paper's: the brightest, least coloured fur is the coat's white.
    core = alpha > 0.97
    light = fur.mean(axis=2)
    spread = fur.max(axis=2) - fur.min(axis=2)
    whites = core & (light > np.percentile(light[core], 70)) & (spread < np.percentile(spread[core], 50))
    white = np.median(fur[whites], axis=0)
    fur = fur * (srgb_to_linear(WHITE) / white)

    rgba = np.dstack([linear_to_srgb(fur), alpha])
    im = Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
    if mirror:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if turn:
        im = im.rotate(turn, resample=Image.BICUBIC, expand=True)
    box = im.getchannel("A").point(lambda v: 255 if v > 5 else 0).getbbox()
    im = im.crop(box)
    scale = min(wide * PX / im.width, tall * PX / im.height)
    size = (round(im.width * scale), round(im.height * scale))
    # Downsized premultiplied, so the fur's edge does not darken.
    pre = np.asarray(im, dtype=np.float32) / 255
    pre[..., :3] *= pre[..., 3:]
    small = np.dstack([np.asarray(Image.fromarray((pre[..., c] * 65535).astype(np.uint16)).resize(size, Image.LANCZOS), dtype=np.float32) / 65535 for c in range(4)])
    small = np.clip(small, 0, 1)
    a = small[..., 3]
    colour = small[..., :3] / np.maximum(a, 1e-4)[..., None]

    # Laid on the desk, with room round it for its shadow.
    pad = round(BLEED * PX)
    a = np.pad(a, pad)
    colour = np.pad(colour, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
    body = a > 0.5
    inside = ndimage.distance_transform_edt(body)
    reach = inside.max()
    # A lying cat is about as high as it is half wide: a dome over its outline.
    height = np.sqrt(np.clip(inside * (2 * reach - inside), 0, None)) * 0.85
    # Where the cat stands between the desk and the lamp: march toward the lamp, and see if the cat rises above the
    # line to it.
    over = np.full(a.shape, -1e9, dtype=np.float32)
    for t in range(1, int(reach * 1.2 / RISE) + 2):
        moved = ndimage.shift(height, (-TOWARD[1] * t, -TOWARD[0] * t), order=1, cval=0.0)
        over = np.maximum(over, moved - t * RISE)
    cast = np.clip(over / 2.0 + 0.5, 0, 1)
    # A wide lamp: the shadow is crisp under the cat and softens as it falls away.
    near_ = ndimage.gaussian_filter(cast, 0.03 * PX)
    far_ = ndimage.gaussian_filter(cast, 0.12 * PX)
    reach_ = np.clip(ndimage.distance_transform_edt(~body) / (0.25 * PX), 0, 1)
    shade = DARK * (near_ * (1 - reach_) + far_ * reach_)
    # And the dark where the fur meets the desk, which no light reaches.
    contact = ndimage.gaussian_filter(body.astype(np.float32), 0.05 * PX)
    shade = np.clip(np.maximum(shade, 0.85 * contact), 0, 0.92)

    total = a + shade * (1 - a)
    out = (colour * a[..., None] + SHADOW * (shade * (1 - a))[..., None]) / np.maximum(total, 1e-6)[..., None]
    rgba = np.dstack([np.clip(out, 0, 1), np.clip(total, 0, 1)])
    png = os.path.join(tempfile.gettempdir(), f"resume-cat-{name}.png")
    Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), "RGBA").save(png)
    subprocess.run(["uv", "run", "--quiet", ENCODE, png, os.path.join(OUT, f"resume-cat-{name}.avif")], check=True)
    print(name, size[0] / PX, "x", size[1] / PX, "em")
    return png, (size[0] / PX, size[1] / PX)


def main():
    laid = []
    for name, turn, mirror, wide, tall, across in CATS:
        _, (w, h) = cut(name, turn, mirror, wide, tall)
        laid.append({"src": f"/objects/resume-cat-{name}.avif", "x": across, "size": [round(w, 3), round(h, 3)]})
    frame = json.load(open(FRAME))
    frame["cats"] = {"above": ABOVE, "bleed": BLEED, "laid": laid}
    with open(FRAME, "w") as file:
        json.dump(frame, file)
        file.write("\n")


main()
