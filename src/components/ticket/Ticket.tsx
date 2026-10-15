import { motion } from 'motion/react'
import { useState } from 'react'

import { profile } from '../../content'
import contact from './contact.json'
import { Print } from './Print'
import ticket from './ticket.json'

const [W, H] = ticket.size
const B = ticket.bleed
const FRAME_W = W + 2 * B
const FRAME_H = H + 2 * B
// The stamps' column beside the ticket: the stamps' width and an em (studio/ticket/scene.py's BESIDE).
const BESIDE_W = ticket.stamps.size[0] + 1
const SPREAD_W = BESIDE_W + FRAME_W
// The photograph of the whole set and the one of the punched hole, each by the box it covers in the spread's em.
const [OX, OY, OW, OH] = contact.open
const [PX, PY, PW, PH] = contact.punch
// The photograph's own edge fades into the hide the page lays round it, a few em in.
const FADE = 5

/** Lays an image over the box it was photographed for, in the spread's em. */
const over = (x: number, y: number, w: number, h: number) => ({ left: `${x}em`, top: `${y}em`, width: `${w}em`, height: `${h}em` })

/**
 * The contact page: one photograph of the set (studio/ticket/scene.py), a risograph-printed cinema ticket on red
 * leather with a strip of Indian stamps beside it and a Leica lying on its back above them, all under one lamp. What
 * is printed on the ticket is laid over the photograph in the same type and left clear, so the words can be
 * selected and followed where they are printed. The spread is as tall as the page lets it be and never wider than
 * the page; the photograph runs on past it into the hide. Copying the email address has the conductor punch the
 * ticket: a photograph of the same set with the hole through it, of the hole alone, is laid over the first.
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
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
    >
      <div className="relative select-none" style={{ fontSize: `calc(100cqw / ${SPREAD_W})`, width: `${SPREAD_W}em`, height: `${FRAME_H}em` }}>
        <img
          src="/objects/contact-open.avif"
          alt=""
          aria-hidden
          draggable={false}
          className="pointer-events-none absolute max-w-none"
          style={{
            ...over(OX, OY, OW, OH),
            maskImage: `linear-gradient(to right, transparent, #000 ${FADE}em, #000 calc(100% - ${FADE}em), transparent), linear-gradient(transparent, #000 ${FADE}em, #000 calc(100% - ${FADE}em), transparent)`,
            maskComposite: 'intersect',
          }}
        />
        <img
          src="/objects/contact-punch.avif"
          alt=""
          aria-hidden
          draggable={false}
          className="pointer-events-none absolute max-w-none transition-opacity"
          style={{ ...over(PX, PY, PW, PH), opacity: copied ? 1 : 0 }}
        />
        <div
          data-plate="ticket"
          className="absolute text-transparent select-text [&_.ink-only]:invisible"
          style={{ left: `${BESIDE_W + B}em`, top: `${B}em`, width: `${W}em`, height: `${H}em` }}
        >
          <Print onCopy={copy} copied={copied} />
        </div>
      </div>
    </motion.div>
  )
}
