"""Old 35 mm film on the leather of the contact page's folded strip, photographed on the copy stand under the same light as the
ticket. Run from the repository root, after studio/ticket/reel.py:

    blender -b --factory-startup -P studio/ticket/film.py -- [--scale 0.5] [--samples 64] [--proofs DIR]

Film is a thin strip of acetate that remembers the reel it was wound on, so a cut length never lies flat: its ends
curl back into rolls on their own, toward the emulsion, tighter the further in they go.

For the folded strip: a length lying down the leather, cupped a little across its width as film cups, each end
lifting off and rolling back over itself into a loose spiral, the head tighter and further round than the tail, and
neither square: each roll a little wider at one side than the other, its turns crept sideways as they wound.
Writes public/objects/ticket-film.avif.

The acetate is clear. Where the print has no silver the leather shows through it, a little dimmed; where the silver
is dense it is matte and nearly black; the perforations are holes. Over all of it is the thin shine of the base: the
lights are set so it throws little back where it lies flat, but where it turns it catches the studio's light as glass
does. The picture is reel.py's map of how much light the print lets through (art/reel.png) and its perforations
(art/reel-holes.png). Shapes are worked out step by step along the film. Set OEUSUME if that checkout is not in
~/Documents/oeusume.
"""

import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OEUSUME = os.environ.get("OEUSUME", os.path.expanduser("~/Documents/oeusume"))
sys.path.insert(0, os.path.join(OEUSUME, "studio"))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import stage as stage_module  # noqa: E402
from stage import Stage  # noqa: E402

ART = os.path.join(HERE, "art")
OUT = os.path.join(ROOT, "public", "objects")
PANEL = "#651415"  # the leather it lies on (leather.py), which lights it from below
WIDTH = 4.4  # 35 mm, in em, as reel.py has it
EXPOSURE = 0.3
STEP = 0.02  # along the film between two lines of the mesh, in em
ACROSS = 24  # lines across the film
BASE = (1.0, 0.985, 0.95)  # the acetate's faint warmth
SILVER = (0.005, 0.0047, 0.0045)  # dense silver, seen from above: nearly black, and matte
TINT = 0.72  # how much light the clear base lets through, as reel.py prints it
# Each end: how much film is in its roll, the roll's outer radius and the radius it winds down to, in em; how much
# wider the roll is at one side than the other, as a fraction; how far off square it starts, in em across the film;
# and how far its turns creep sideways, in em a turn.
HEAD = {"length": 10.6, "outer": 0.85, "inner": 0.5, "flare": 0.12, "skew": 0.07, "creep": 0.05}
TAIL = {"length": 8.4, "outer": 1.15, "inner": 0.85, "flare": -0.09, "skew": -0.11, "creep": -0.04}



def smooth(lo, hi, x):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def roll(end, u, sigma):
    """A roll's path, for the line across the film u of the way from its left edge: given the distances sigma into the
    roll from where it leaves the leather, how far back along the page it reaches, how high it stands, and how far
    it has crept sideways. It lifts gently over the first em, then winds round, the radius shrinking as it goes."""
    side = u - 0.5
    flare = 1 + end["flare"] * side * 2
    lift = smooth(0.0, 1.2, sigma)
    t = np.zeros_like(sigma)
    z = np.zeros_like(sigma)
    theta = np.zeros_like(sigma)
    for i in range(1, len(sigma)):
        turned = theta[i - 1] / (2 * math.pi)
        total = end["length"] / (math.pi * (end["outer"] + end["inner"]))
        radius = (end["outer"] + (end["inner"] - end["outer"]) * min(1.0, turned / max(total, 1e-6))) * flare
        ds = sigma[i] - sigma[i - 1]
        theta[i] = theta[i - 1] + ds * lift[i] / radius
        t[i] = t[i - 1] + ds * math.cos(theta[i])
        z[i] = z[i - 1] + ds * math.sin(theta[i])
    return t, z, end["creep"] * theta / (2 * math.pi)


def film_mesh(length):
    """The film as a grid, ACROSS lines across by one every STEP along, with its uv running down the print."""
    rows = ACROSS + 1
    flat = length - HEAD["length"] - TAIL["length"]
    cols = int(length / STEP) + 1
    s = np.linspace(0, length, cols)
    verts = np.zeros((rows, cols, 3))
    for r in range(rows):
        u = r / ACROSS
        x = u * WIDTH
        # Where each roll leaves the leather is not square across the film.
        head_at = HEAD["length"] + HEAD["skew"] * (u - 0.5) * 2
        tail_at = HEAD["length"] + flat + TAIL["skew"] * (u - 0.5) * 2
        page = np.zeros(cols)
        height = np.zeros(cols)
        sideways = np.zeros(cols)
        middle = (s >= head_at) & (s <= tail_at)
        page[middle] = s[middle]
        # The film cups across its width, its edges a little off the leather, and lies in slow waves along it.
        cup = 0.04 * ((u - 0.5) * 2) ** 2
        height[middle] = cup + 0.015 * np.sin(s[middle] * 2 * math.pi / 9 + u)
        head = s < head_at
        sigma = head_at - s[head][::-1]
        t, z, c = roll(HEAD, u, sigma)
        page[head] = (head_at - t)[::-1]
        height[head] = (z + cup)[::-1]
        sideways[head] = c[::-1]
        tail = s > tail_at
        sigma = s[tail] - tail_at
        t, z, c = roll(TAIL, u, sigma)
        page[tail] = tail_at + t
        height[tail] = z + cup
        sideways[tail] = c
        # A cut length of film lies in a long, slight bow.
        bow = 0.18 * np.sin(np.clip(page / length, 0, 1) * math.pi)
        verts[r, :, 0] = x + bow + sideways
        verts[r, :, 1] = page
        # Lying on the leather: never below it, the troughs of its waves just touching.
        verts[r, :, 2] = 0.02 + height
    return verts, s


def material():
    """Clear acetate carrying a black and white print: through it as much light as the print lets through, matte
    near-black silver where it is dense, and over both the thin shine of the base."""
    mat = bpy.data.materials.new("film")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()

    def image(name, colourspace="Non-Color"):
        node = nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(os.path.join(ART, name))
        node.image.colorspace_settings.name = colourspace
        node.interpolation = "Cubic"
        node.extension = "REPEAT"
        return node

    light, holes = image("reel.png"), image("reel-holes.png")
    tint = TINT
    # How much of a point is silver: none where the print is as clear as the base, all where nothing gets through.
    share = nodes.new("ShaderNodeMath")
    share.operation = "DIVIDE"
    share.inputs[1].default_value = tint
    silverness = nodes.new("ShaderNodeMath")
    silverness.operation = "SUBTRACT"
    silverness.inputs[0].default_value = 1.0
    silverness.use_clamp = True
    links.new(light.outputs["Color"], share.inputs[0])
    links.new(share.outputs[0], silverness.inputs[1])
    clear = nodes.new("ShaderNodeBsdfTransparent")
    clear.inputs["Color"].default_value = (BASE[0] * tint, BASE[1] * tint, BASE[2] * tint, 1)
    silver = nodes.new("ShaderNodeBsdfDiffuse")
    silver.inputs["Color"].default_value = (*SILVER, 1)
    body = nodes.new("ShaderNodeMixShader")
    links.new(silverness.outputs[0], body.inputs[0])
    links.new(clear.outputs[0], body.inputs[1])
    links.new(silver.outputs[0], body.inputs[2])
    # The base's shine: smooth on the base side, duller on the emulsion side, which faces in on the rolls.
    gloss = nodes.new("ShaderNodeBsdfGlossy")
    facing = nodes.new("ShaderNodeNewGeometry")
    rough = nodes.new("ShaderNodeMix")
    rough.data_type = "FLOAT"
    rough.inputs[2].default_value = 0.06
    rough.inputs[3].default_value = 0.22
    links.new(facing.outputs["Backfacing"], rough.inputs[0])
    links.new(rough.outputs[0], gloss.inputs["Roughness"])
    # The stand's lights are set off to the sides, so where the base faces the lens it throws back only a faint
    # sheen of the room, enough to tell the film from the leather and its perforations from the film; where it turns
    # away, on the rolls, its shine comes up as glass's does at a glance.
    fresnel = nodes.new("ShaderNodeFresnel")
    fresnel.inputs["IOR"].default_value = 1.48
    glance = nodes.new("ShaderNodeMapRange")
    glance.inputs["From Min"].default_value = 0.0
    glance.inputs["From Max"].default_value = 0.45
    links.new(fresnel.outputs[0], glance.inputs["Value"])
    surface = nodes.new("ShaderNodeMixShader")
    links.new(glance.outputs["Result"], surface.inputs[0])
    links.new(body.outputs[0], surface.inputs[1])
    links.new(gloss.outputs[0], surface.inputs[2])
    # The perforations are holes: nothing there at all.
    gone = nodes.new("ShaderNodeBsdfTransparent")
    cut = nodes.new("ShaderNodeMixShader")
    links.new(holes.outputs["Color"], cut.inputs[0])
    links.new(surface.outputs[0], cut.inputs[1])
    links.new(gone.outputs[0], cut.inputs[2])
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(cut.outputs[0], out.inputs["Surface"])
    return mat


def film(stage):
    length = bpy.data.images.load(os.path.join(ART, "reel.png")).size[1] / 96  # reel.py draws at 96 pixels to the em
    verts, s = film_mesh(length)
    nr, nc = verts.shape[:2]
    left, top = verts[..., 0].min(), verts[..., 1].min()
    world = np.stack((verts[..., 0], -verts[..., 1], verts[..., 2]), -1)
    index = np.arange(nr * nc).reshape(nr, nc)
    faces = np.stack((index[:-1, :-1], index[:-1, 1:], index[1:, 1:], index[1:, :-1]), -1).reshape(-1, 4)
    mesh = bpy.data.meshes.new("film")
    mesh.from_pydata(world.reshape(-1, 3).tolist(), [], faces.tolist())
    u = np.repeat(np.linspace(0, 1, nr)[:, None], nc, 1)
    v = np.repeat((1 - s / length)[None, :], nr, 0)  # beyond the print's length it repeats
    uv = np.stack((u, v), -1).reshape(-1, 2)
    loops = np.empty(len(mesh.loops), dtype=np.int32)
    mesh.loops.foreach_get("vertex_index", loops)
    mesh.uv_layers.new().data.foreach_set("uv", uv[loops].ravel())
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.materials.append(material())
    strip = stage.add("film", mesh)
    w = verts[..., 0].max() - left
    h = verts[..., 1].max() - top
    # Lying flat, clear acetate leaves no shadow to speak of: what of it stops light, the silver, is already as dark
    # as its shadow.
    return stage.shoot("ticket-film", (left, top, w, h), bleed=0.5, exposure=EXPOSURE, lens=False, mat_through_glass=False, shadowless=(strip,))


parser = argparse.ArgumentParser()
parser.add_argument("--scale", type=float, default=1.0)
parser.add_argument("--samples", type=int, default=160)
parser.add_argument("--proofs")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
if args.proofs:
    os.makedirs(args.proofs, exist_ok=True)
stage_module.MAT = PANEL
STAGE = Stage(OUT, args.proofs, scale=args.scale, samples=args.samples)
STAGE.clear()
film(STAGE)
