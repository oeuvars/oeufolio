"""The contact page as one photograph: everything on the leather put down in one set and photographed at once, under
one lamp, so each thing shades the others and the hide under them as it would on a real table. Run from the
repository root, after the art the pieces print (see ticket.py):

    blender -b --factory-startup -P studio/ticket/scene.py -- [open | punch | strip] [--scale 0.5] [--samples 64] [--proofs DIR]

The hide is in the set, so it lights what lies on it and catches the shadows, but it is not in the photograph: the
page lays the hide itself, one texture across the strip and its tab (leather.py's square), and the photograph over it
holds only the pieces and their shadows.

open is the open page: the ticket on the hide, the strip of stamps beside it and the Leica lying
on its back at the top, over the ticket's corner. punch is the same set with the conductor's punch through the
ticket, photographed only round the hole, for the page to lay over open once the address is copied. strip is the
folded strip: a coil of the stamps running its length and the Leica lying across it.

Every piece is the one its own script builds (leather.py, ticket.py, leica.py), laid where the page has it, in the
spread's em (Ticket.tsx: the stamps' column from 0 to BESIDE across, the ticket's frame after it, FRAME_H down) or
the strip's (StripTicket.tsx: ACROSS em across, measured from its middle down). The light is the stand's room and
the key lamp (key.py), four times as bright, up to the left; the exposure is the one the white card needs, and the
hide's dye is dark enough to be its deep crimson at that exposure, as it would be in one photograph.

Writes public/objects/contact-<plate>.avif and src/components/ticket/contact.json, the box each covers, in the em of
the page that places it. Set OEUSUME if that checkout is not in ~/Documents/oeusume.
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OEUSUME = os.environ.get("OEUSUME", os.path.expanduser("~/Documents/oeusume"))
sys.path.insert(0, os.path.join(OEUSUME, "studio"))
sys.path.insert(0, HERE)

import key  # noqa: E402
import leather  # noqa: E402
import leica  # noqa: E402
import stage as stage_module  # noqa: E402
import ticket  # noqa: E402
from stage import Stage  # noqa: E402

OUT = os.path.join(ROOT, "public", "objects")
PLACES = os.path.join(ROOT, "src", "components", "ticket", "contact.json")
PANEL = leather.DYE
EXPOSURE = -2.0  # what the white card needs under the room and the key lamp

# The open page, in the spread's em. The stamps' column is the stamps' width and an em; the ticket's frame follows it,
# the card a bleed in from the frame.
STAMP_W, STAMP_H = ticket.TICKET["stamps"]["size"]
BESIDE = STAMP_W + 1.0
B = ticket.BLEED
FRAME_H = ticket.H + 2 * B
TICKET_AT = (BESIDE + B, B)
STAMPS_AT = (0.5, FRAME_H - STAMP_H * len(ticket.TICKET["stamps"]["views"]) - 1.0)
CAMERA_AT = (3.7, 1.7)
# What the photograph covers: the spread, and the hide round it as far as a window wider or taller than the spread
# shows of it.
OPEN = (-14.0, -8.0, 52.0, 46.0)
PUNCH = 1.6  # em either side of the punch's middle, for the photograph of the hole

# The folded strip, in its own em: ACROSS across, y from its middle down.
ACROSS = 8.4
COIL_AT = (1.25, -(STAMP_H * len(ticket.TICKET["coil"]["views"])) / 2 - 1.98)
STRIP_CAMERA_AT = (5.2, 8.8)
STRIP = (-0.4, -40.0, ACROSS + 0.8, 80.0)


def set_down(plate):
    """Everything for the plate on the stage. Returns the frame to photograph, in the plate's em."""
    if plate == "strip":
        x0, y0, w, h = STRIP
        floor = leather.hide(STAGE, x0 - 6, y0 - 6, w + 12, h + 12)
        ticket.lay_stamps("coil", COIL_AT)
        leica.AT = STRIP_CAMERA_AT
    else:
        x0, y0, w, h = OPEN
        floor = leather.hide(STAGE, x0 - 6, y0 - 6, w + 12, h + 12)
        ticket.lay_ticket(plate == "punch", TICKET_AT)
        ticket.lay_stamps("stamps", STAMPS_AT)
        leica.AT = CAMERA_AT
    # The hide is the page's own, one texture across the strip and its tab: the photograph keeps only what lies on it and
    # what that does to it, the shadows, which the hide catches. It still lights what is on it, red, from below. Through
    # the punch's hole, too small to show where its grain falls, the hide is photographed.
    if plate != "punch":
        floor.is_shadow_catcher = True
    holder = leica.camera()
    leica.softbox(holder)
    key.add((x0 + w / 2, -(y0 + h / 2)))
    if plate == "punch":
        px, py, _ = ticket.TICKET["punch"]
        cx, cy = TICKET_AT[0] + px, TICKET_AT[1] + py
        return (cx - PUNCH, cy - PUNCH, 2 * PUNCH, 2 * PUNCH)
    return (x0, y0, w, h)


def main():
    global STAGE
    parser = argparse.ArgumentParser()
    parser.add_argument("plates", nargs="*", choices=("open", "punch", "strip"))
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--samples", type=int, default=160)
    parser.add_argument("--proofs")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    if args.proofs:
        os.makedirs(args.proofs, exist_ok=True)
    stage_module.MAT = PANEL
    STAGE = Stage(OUT, args.proofs, scale=args.scale, samples=args.samples)
    ticket.STAGE = leica.STAGE = STAGE
    places = json.load(open(PLACES)) if os.path.exists(PLACES) else {}
    for plate in args.plates or ("open", "punch", "strip"):
        STAGE.clear()
        frame = set_down(plate)
        # The hide is in the photograph, so the stand's mat, which only reflections and shadows see, is taken away.
        STAGE.shoot(f"contact-{plate}", frame, exposure=EXPOSURE, lens=False, mat=False, sharp=1.0 if plate == "strip" else 1.5)
        places[plate] = [round(v, 4) for v in frame]
        with open(PLACES, "w") as out:
            json.dump(places, out)
            out.write("\n")


STAGE = None

if __name__ == "__main__":
    main()
