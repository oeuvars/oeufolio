import camera from './camera.json'
import ticket from './ticket.json'

const [STAMP_W, STAMP_H] = ticket.stamps.size
const BLEED = 1.6 // the margin the stamps' render leaves round them (studio/ticket/ticket.py)
const COIL_W = STAMP_W + 2 * BLEED
const COIL_H = STAMP_H * ticket.coil.views.length + 2 * BLEED
const ACROSS = 8.4 // em across the strip: the coil takes most of it, with leather either side
const [CX, CY, CW, CH] = camera.box
const [AX, AY] = camera.at

/**
 * The contact page on a folded strip, composed for the strip as the letter's and the house's are: a coil of the
 * page's Indian stamps, fourteen of them, running the strip's whole height and on past both ends, and the Leica from the
 * page lying across it low down, its strap trailing up over the stamps. Both are photographed under the page's one
 * key lamp (studio/ticket/key.py), so the camera's shadow falls across the stamps as it would. They are at the
 * page's own scale to one another.
 */
export function StripTicket() {
  return (
    // The leather has no band beside it: the strip is leather to its torn edge, so the coil is laid across all of it,
    // the band's width included, short of the tear.
    <div aria-hidden className="absolute inset-y-0 left-0 w-[calc(100%+var(--band-w)-12px)] overflow-hidden [container-type:size]">
      <div className="absolute inset-0" style={{ fontSize: `calc(100cqw / ${ACROSS})` }}>
        <img
          src="/objects/ticket-coil.avif"
          alt=""
          draggable={false}
          className="absolute max-w-none"
          style={{ left: `${(ACROSS - COIL_W) / 2 - 0.15}em`, top: `calc(50cqh - ${COIL_H / 2 + 6.6 * 0.3}em)`, width: `${COIL_W}em`, height: `${COIL_H}em` }}
        />
        <img
          src="/objects/ticket-camera-shadow.avif"
          alt=""
          draggable={false}
          className="absolute max-w-none mix-blend-multiply"
          style={{ left: `${0.62 * ACROSS - (AX - CX)}em`, top: `calc(66cqh - ${AY - CY}em)`, width: `${CW}em`, height: `${CH}em` }}
        />
        <img
          src="/objects/ticket-camera.avif"
          alt=""
          draggable={false}
          className="absolute max-w-none"
          // The middle of the body a little right of the strip's middle, two thirds of the way down.
          style={{ left: `${0.62 * ACROSS - (AX - CX)}em`, top: `calc(66cqh - ${AY - CY}em)`, width: `${CW}em`, height: `${CH}em` }}
        />
      </div>
    </div>
  )
}
