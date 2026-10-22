import { motion } from 'motion/react'
import { useState } from 'react'

import { profile } from '../../content'
import { slide } from '../house'
import contact from './contact.json'
import { Print } from './print'
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

/** Lays an image over the box it was photographed for, in the spread's em. */
const over = (x: number, y: number, w: number, h: number) => ({ left: `${x}em`, top: `${y}em`, width: `${w}em`, height: `${h}em` })

/**
 * The contact page: one photograph of the set (studio/ticket/scene.py), a risograph-printed cinema ticket on red
 * leather with a strip of Indian stamps beside it and a Leica lying on its back above them, all under one lamp. What
 * is printed on the ticket is laid over the photograph in the same type and left clear, so the words can be
 * selected and followed where they are printed. The spread is as tall as the page lets it be and never wider than
 * the page. It is laid once and stays where it lies, the strip uncovering it as it opens (SiteShell). Copying the
 * email address has the conductor punch the ticket: a photograph of the same set with the hole through it, of the hole alone, is laid over the first.
 */
type TicketProps = {
  /** Whether the contact strip is open. Folded, the strip sees the ticket's edge a little nearer. */
  open: boolean
}

// How much nearer the folded strip sees the table than the open page does.
const NEAR = 1.08

export const Ticket = ({ open }: TicketProps) => {
  const [copied, setCopied] = useState(false)
  // A browser that refuses the clipboard leaves the ticket as it is. The address can still be selected.
  const copy = () =>
    navigator.clipboard.writeText(profile.email).then(
      () => setCopied(true),
      () => undefined,
    )

  return (
    <div
      // The panel has no frame, so the spread takes the page's margins either side, all but a sliver: on the left the
      // room kept for the tab of the strip before, on the right the band, which this panel covers.
      className="@container w-full max-md:justify-self-center md:-my-[4vh] md:-mr-[calc(clamp(1rem,2.6vw,3rem)+var(--band-w)-12px)] md:-ml-[calc(var(--protrude)+6px)] md:w-auto"
      style={{ maxWidth: `calc(min(90vh, var(--page-room, 90vh)) * ${SPREAD_W / FRAME_H})` }}
    >
      {/* The view's move, on the strip's own spring, so the two keep step: folded, the ticket's edge a little nearer;
          as the strip opens, the view pulls back to the whole table where it lies. */}
      <motion.div
        className="relative select-none"
        // Scaled about the ticket's right edge, which the folded strip shows beside its tab: that edge stays where it
        // is, with the hide between it and the tab, and only the rest grows and shrinks.
        style={{ fontSize: `calc(100cqw / ${SPREAD_W})`, width: `${SPREAD_W}em`, height: `${FRAME_H}em`, transformOrigin: `${((BESIDE_W + B + W) / SPREAD_W) * 100}% 40%` }}
        initial={false}
        animate={{ scale: open ? 1 : NEAR }}
        transition={slide}
      >
        <img
          src="/objects/contact-open.avif"
          alt=""
          aria-hidden
          draggable={false}
          className="pointer-events-none absolute max-w-none"
          style={over(OX, OY, OW, OH)}
        />
        <img
          src="/objects/contact-punch.avif"
          alt=""
          aria-hidden
          draggable={false}
          className="pointer-events-none absolute max-w-none transition-opacity"
          style={{ ...over(PX, PY, PW, PH), opacity: copied ? 1 : 0 }}
        />
        {/* Its type is clear, so it goes without the panel's ink filter, which would only be worked out again on every
            frame the strip slides. */}
        <div
          data-plate="ticket"
          className="absolute text-transparent select-text [&_*]:filter-none [&_.ink-only]:invisible"
          style={{ left: `${BESIDE_W + B}em`, top: `${B}em`, width: `${W}em`, height: `${H}em` }}
        >
          <Print onCopy={copy} copied={copied} />
        </div>
      </motion.div>
    </div>
  )
}
