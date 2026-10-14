"""Match ticket, copied from the paper ticket Arsenal issued for the 2013-14 season: white card with a pale
blue photograph washed over the upper half, a red band and a blue band across the head with the crest over
both, the club's lettering reversed out of the red, the kit maker's and the shirt sponsor's marks down the
left, thermal print, a barcode along the foot, and a stub that carries a second barcode on its side."""

import os

import numpy as np

from paint import blur, box, cloud, disc, dots, ramp, streaks
from stock import Sheet, drift

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art")

H = 9.375
STUB_W, MAIN_W = 3.4, 17.225
NOTCH = 0.4
RED_BAND, BLUE_BAND = 1.28, 1.96
CARD = "#f6f6f2"
WASH = "#b7c8e3"
RED = "#dc0a14"
BLUE = "#1d3f9c"
MARK = "#d4202c"
FADED = "#8793ab"
PRINT = "#27211f"
BARS = "#3a2925"


def art(name):
    return os.path.join(ART, f"{name}.png")


def bars(X, Y, x0, y0, x1, y1, seed, upright=True, module=0.045):
    """Signed distance to a barcode: bars one to three modules wide, running along x, or along y when it lies on its side."""
    rng = np.random.default_rng(seed)
    start, end = (x0, x1) if upright else (y0, y1)
    at = start
    d = np.full(X.shape, 1.0)
    while at < end:
        width = module * rng.integers(1, 4)
        stop = min(at + width, end)
        d = np.minimum(d, box(X, Y, at, y0, stop, y1) if upright else box(X, Y, x0, at, x1, stop))
        at += width + module * rng.integers(1, 4)
    return d


def card(w, seed):
    """Ticket card before it is printed. The pulp shows as a faint cloudiness, a tooth and the odd stray fibre,
    and the guillotine leaves the edges a little ragged."""
    sheet = Sheet(w, H, CARD, rough=0.46)
    shape = sheet.height.shape
    sheet.rgb *= (1 + 0.014 * cloud(shape, seed, falloff=1.1))[..., None]
    sheet.height += 0.0005 * cloud(shape, seed + 1, falloff=0.5)
    fibres = np.maximum(ramp(2.7, 3.5, streaks(shape, seed + 2, 11, 0.6)), ramp(2.7, 3.5, streaks(shape[::-1], seed + 3, 11, 0.6).T))
    sheet.ink(fibres, "#5d554c", 0.3)
    sheet.sdf += 0.009 * cloud(shape, seed + 4, falloff=1.0)
    return sheet


def thermal(sheet, m, colour, seed):
    """Thermal print: a little soft at the edges and never evenly dark."""
    heat = np.clip(0.97 + 0.03 * cloud(sheet.height.shape, seed, falloff=1.3), 0.86, 1)
    sheet.ink(np.clip(blur(m, 0.7) * 1.1, 0, 1) * heat, colour)


def handled(sheet, seed):
    """A season in a drawer: the edges take up a little grey and the card is no longer one white."""
    shape = sheet.height.shape
    grime = (1 - ramp(0, 0.7, -sheet.sdf)) * 0.05 + 0.012 * np.clip(cloud(shape, seed, falloff=1.7), 0, 3)
    sheet.rgb *= (1 - grime)[..., None] * np.array([1.0, 0.992, 0.97])


def lie(w, amount, seed, corner):
    """How the card lies: a slow wave, and one corner that has lifted."""
    wave = drift(w, H, amount, seed)
    cx, cy = corner
    return lambda x, y: wave(x, y) + 0.14 * (1 - ramp(0, 2.4, np.hypot(x - cx, y - cy))) ** 2


def build(sheet, stage, name, warp):
    sheet.soften(0.05, 0.012)
    sheet.build(
        stage,
        name,
        thickness=0.045,
        warp=warp,
        scan="Paper002",
        scan_size=6,
        scan_normal=0.55,
        scan_rough=0.7,
        scan_colour=0.3,
        wear=(("SurfaceImperfections003", 11, 0.12, 0),),
        sheen=0.3,
    )


def main(stage):
    sheet = card(MAIN_W, 40)
    X, Y = sheet.X, sheet.Y
    shape = sheet.height.shape

    # The photograph of the ground, printed so pale it is only a blue cloud that thins out below the last line.
    photo = np.clip(0.6 + 0.2 * cloud(shape, 61, falloff=2.2), 0, 1) * (1 - ramp(5.0, 7.5, Y)) * (Y > BLUE_BAND)
    sheet.paint(np.clip(photo * (1 + 0.1 * cloud(shape, 62, falloff=0.3)), 0, 1) * 0.85, WASH)
    sheet.art(art("arsenal-cannon"), 14.0, 2.4, 16.64, 3.76, colour=FADED, strength=0.4)

    red = sheet.mask(box(X, Y, -1, -1, MAIN_W + 1, RED_BAND))
    blue = sheet.mask(box(X, Y, -1, RED_BAND, MAIN_W + 1, BLUE_BAND))
    sheet.paint(red, RED)
    sheet.paint(blue, BLUE)
    # Litho solids are never quite solid.
    solid = np.maximum(red, blue)
    sheet.rgb *= (1 - solid * 0.05 * np.clip(cloud(shape, 63, falloff=0.9), -2, 2))[..., None]
    sheet.finish(solid, rough=0.36)
    sheet.art(art("arsenal-wordmark"), 0.45, 0.22, 4.02, 1.05, colour="#ffffff")
    sheet.art(art("arsenal-crest"), 7.83, 0.2, 9.39, 2.02)
    sheet.art(art("nike"), 0.5, 4.4, 2.13, 4.98, colour=MARK)
    sheet.art(art("emirates"), 0.56, 5.52, 2.11, 6.6, colour=MARK)

    black, _, _ = sheet.plate("ticket-main")
    thermal(sheet, black, PRINT, 64)
    thermal(sheet, sheet.mask(bars(X, Y, 3.54, 7.71, 11.98, H - 0.2, 5)), BARS, 65)
    handled(sheet, 66)

    sheet.punch(disc(X, Y, 0, 0, NOTCH))
    sheet.punch(disc(X, Y, 0, H, NOTCH))
    sheet.punch(dots(X, Y, 0, NOTCH + 0.2, 0, H - NOTCH - 0.2, 0.2, 0.05))
    build(sheet, stage, "ticket-main", lie(MAIN_W, 0.08, 52, (MAIN_W, 0)))
    stage.shoot("ticket-main", (0, 0, MAIN_W, H))


def stub(stage):
    sheet = card(STUB_W, 50)
    X, Y = sheet.X, sheet.Y
    thermal(sheet, sheet.mask(bars(X, Y, 0.97, 0.3, 2.65, H - 0.4, 7, upright=False, module=0.06)), BARS, 67)
    black, _, _ = sheet.plate("ticket-stub")
    thermal(sheet, black, PRINT, 68)
    handled(sheet, 69)

    sheet.punch(disc(X, Y, STUB_W, 0, NOTCH))
    sheet.punch(disc(X, Y, STUB_W, H, NOTCH))
    sheet.punch(dots(X, Y, STUB_W, NOTCH + 0.2, STUB_W, H - NOTCH - 0.2, 0.2, 0.05))
    build(sheet, stage, "ticket-stub", lie(STUB_W, 0.04, 53, (0, H)))
    stage.shoot("ticket-stub", (0, 0, STUB_W, H))


SHOTS = {"ticket-stub": stub, "ticket-main": main}
