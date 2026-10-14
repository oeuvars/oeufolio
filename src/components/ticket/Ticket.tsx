import { motion } from 'motion/react'
import { useState } from 'react'

import { profile } from '../../content'
import camera from './camera.json'
import { Print } from './Print'
import roll from './roll.json'
import ticket from './ticket.json'

const [W, H] = ticket.size
const B = ticket.bleed
const FRAME_W = W + 2 * B
const FRAME_H = H + 2 * B
// The stamps' photograph, in the ticket's em: the strip, with the margin the render leaves round it. It lies beside the
// ticket, as the small pieces of print do in the reference, low, under the camera.
const STAMPS_BLEED = 0.5
const [STAMP_W, STAMP_H] = ticket.stamps.size
const STAMPS_W = STAMP_W + 2 * STAMPS_BLEED
const STAMPS_H = STAMP_H * ticket.stamps.views.length + 2 * STAMPS_BLEED
const STAMPS_TOP = FRAME_H - STAMPS_H - 0.5
const GAP = 0
/**
 * What else lies on the leather, each photographed under the same light with its shadow, and placed by the box its
 * photograph covers in the spread's em: a Leica M3 on its back at the top (studio/ticket/leica.py), lying over the
 * ticket's edge, and a roll of the old film below, its end run out flat (studio/ticket/film.py roll).
 */
const PROPS = [
  { src: '/objects/ticket-camera.avif', box: camera.box },
  { src: '/objects/ticket-roll.avif', box: roll.box },
]
const SPREAD_W = STAMPS_W + GAP + FRAME_W

/**
 * The contact page: a risograph-printed cinema ticket lying on the page, photographed (studio/ticket/ticket.py), with what
 * is printed on it laid over the photograph in the same type and left clear, so the words can be selected and
 * followed where they are printed. It is as tall as the page lets it be and never wider than the page. Copying
 * the email address has the conductor punch it: a second photograph, taken under the same light with the hole
 * through it, takes the first one's place, and the leather shows through the hole. Beside it lies a strip of three Indian
 * stamps printed in the same inks, each its own picture of the same river; above them a camera, and below the ticket a
 * roll of old film.
 */
export function Ticket() {
  const [copied, setCopied] = useState(false)

  // A browser that refuses the clipboard leaves the ticket as it is. The address can still be selected.
  const copy = () =>
    navigator.clipboard.writeText(profile.email).then(
      () => setCopied(true),
      () => undefined,
    )

  return (
    <motion.div
      // The panel has no frame, so the spread takes the page's margins either side, all but a sliver: on the left the
      // room kept for the tab of the strip before, on the right the band, which this panel covers.
      className="@container -my-[4vh] w-full md:-mr-[calc(clamp(1rem,2.6vw,3rem)+var(--band-w)-12px)] md:-ml-[calc(var(--protrude)+6px)] md:w-auto"
      style={{ maxWidth: `calc(90vh * ${SPREAD_W / FRAME_H})` }}
      initial={{ y: '18vh', opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 120, damping: 20, mass: 1 }}
    >
      <div className="relative flex items-stretch select-none" style={{ fontSize: `calc(100cqw / ${SPREAD_W})`, gap: `${GAP}em` }}>
        <div aria-hidden className="relative shrink-0" style={{ width: `${STAMPS_W}em`, height: `${FRAME_H}em` }}>
          <img
            src="/objects/ticket-stamps.avif"
            alt=""
            draggable={false}
            className="absolute left-0 max-w-none"
            style={{ width: `${STAMPS_W}em`, height: `${STAMPS_H}em`, top: `${STAMPS_TOP}em` }}
          />
        </div>
        <div className="relative shrink-0" style={{ width: `${FRAME_W}em`, height: `${FRAME_H}em` }}>
          <img src="/objects/ticket.avif" alt="" draggable={false} className="absolute inset-0 size-full" style={{ opacity: copied ? 0 : 1 }} width={FRAME_W * 72} height={FRAME_H * 72} />
          <img src="/objects/ticket-punched.avif" alt="" draggable={false} className="absolute inset-0 size-full" style={{ opacity: copied ? 1 : 0 }} width={FRAME_W * 72} height={FRAME_H * 72} />
          <div
            data-plate="ticket"
            className="absolute text-transparent select-text [&_.ink-only]:invisible"
            style={{ left: `${B}em`, top: `${B}em`, width: `${W}em`, height: `${H}em` }}
          >
            <Print onCopy={copy} copied={copied} />
          </div>
        </div>
        {PROPS.map(({ src, box: [x, y, w, h] }) => (
          <img
            key={src}
            src={src}
            alt=""
            aria-hidden
            draggable={false}
            className="pointer-events-none absolute max-w-none"
            style={{ left: `${x}em`, top: `${y}em`, width: `${w}em`, height: `${h}em` }}
          />
        ))}
      </div>
    </motion.div>
  )
}
