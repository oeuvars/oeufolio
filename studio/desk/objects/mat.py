"""The desk mat: leather. One square of it is shot from overhead and the page repeats that square.

The sheet is larger than the frame and the scan repeats exactly once across the frame, so the square meets
itself on every side. The lens is left out of this shot: it leans the light across the frame, which would
show as a step where two squares meet.

The mat is dyed a dark green teal, kept low in sheen so the colour stays rich. The yellow it was first dyed is kept beside it as leather-yellow."""

from stock import Sheet

# One tile of the scan covers this many em, and so does the square the page repeats.
TILE = 10.0
DYES = {"leather": "#006b55", "leather-yellow": "#f2b21c"}


def leather(shot):
    def shoot(stage):
        sheet = Sheet(TILE * 3, TILE * 3, DYES[shot], rough=0.5, density=1)
        sheet.build(stage, "mat", thickness=0.1, scan="Leather037", scan_size=TILE, scan_normal=2.1, scan_rough=1.0, scan_colour=0.3, sheen=0.08, specular=0.25, at=(-TILE, -TILE), solid=False)
        stage.shoot(shot, (0, 0, TILE, TILE), exposure=0.4, lens=False, sharp=1.5)

    return shoot


SHOTS = {shot: leather(shot) for shot in DYES}
