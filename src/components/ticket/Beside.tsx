import camera from './camera.json'
import ticket from './ticket.json'

const [, H] = ticket.size
const FRAME_H = H + 2 * ticket.bleed
// The stamps' photograph, in the ticket's em: the strip, with the margin the render leaves round it, low in the
// column, under the camera.
const STAMPS_BLEED = 1.6
const [STAMP_W, STAMP_H] = ticket.stamps.size
// The column is the stamps' width; their render's margin, room for the key lamp's shadow, runs out past it.
export const BESIDE_W = STAMP_W + 1.0
export const BESIDE_H = FRAME_H
const STAMPS_H = STAMP_H * ticket.stamps.views.length + 2 * STAMPS_BLEED
const STAMPS_TOP = FRAME_H - STAMPS_H + STAMPS_BLEED - 1.0
const [CX, CY, CW, CH] = camera.box

/**
 * What lies on the leather beside the ticket, in the spread's em, the column the ticket stands to the right of: the
 * strip of three Indian stamps printed in the ticket's inks (studio/ticket/ticket.py), and above them a Leica M3 on
 * its back (studio/ticket/leica.py), each photographed under the same light with its shadow. The camera reaches out
 * over the column's edge, onto the ticket.
 */
export function Beside() {
  return (
    <div aria-hidden className="pointer-events-none relative shrink-0 select-none" style={{ width: `${BESIDE_W}em`, height: `${BESIDE_H}em` }}>
      <img
        src="/objects/ticket-stamps.avif"
        alt=""
        draggable={false}
        className="absolute max-w-none"
        style={{ left: `${0.5 - STAMPS_BLEED}em`, width: `${STAMP_W + 2 * STAMPS_BLEED}em`, height: `${STAMPS_H}em`, top: `${STAMPS_TOP}em` }}
      />
      <img
        src="/objects/ticket-camera.avif"
        alt=""
        draggable={false}
        className="absolute z-10 max-w-none"
        style={{ left: `${CX}em`, top: `${CY}em`, width: `${CW}em`, height: `${CH}em` }}
      />
    </div>
  )
}
