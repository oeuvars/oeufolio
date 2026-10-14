import { motion } from 'motion/react'
import { useState } from 'react'

import { profile } from '../../content'
import { BESIDE_W, Beside } from './Beside'
import { Print } from './Print'
import ticket from './ticket.json'

const [W, H] = ticket.size
const B = ticket.bleed
const FRAME_W = W + 2 * B
const FRAME_H = H + 2 * B
const SPREAD_W = BESIDE_W + FRAME_W

/**
 * The contact page: a risograph-printed cinema ticket lying on the page, photographed (studio/ticket/ticket.py), with what
 * is printed on it laid over the photograph in the same type and left clear, so the words can be selected and
 * followed where they are printed. It is as tall as the page lets it be and never wider than the page. Copying
 * the email address has the conductor punch it: a second photograph, taken under the same light with the hole
 * through it, takes the first one's place, and the leather shows through the hole. Beside it lie a strip of stamps and a
 * camera (Beside).
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
      <div className="relative flex items-stretch select-none" style={{ fontSize: `calc(100cqw / ${SPREAD_W})` }}>
        <Beside />
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
      </div>
    </motion.div>
  )
}
