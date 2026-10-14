import { motion } from 'motion/react'
import { useState } from 'react'

import { profile } from '../../content'
import { Print } from './Print'
import ticket from './ticket.json'

const [W, H] = ticket.size
const B = ticket.bleed
const FRAME_W = W + 2 * B
const FRAME_H = H + 2 * B
const [PX, PY, PW, PH] = ticket.patch
const pct = (value: number, of: number) => `${(value / of) * 100}%`
// The roll's photograph, in the ticket's em: one small ticket wide, with the margin the render leaves round it, and as
// tall as the run of tickets it shows. It stands beside the ticket, as the small tickets do in the reference.
const ROLL_BLEED = 0.5
const ROLL_W = W * ticket.roll.scale + 2 * ROLL_BLEED
const ROLL_H = H * ticket.roll.scale * ticket.roll.shown + 2 * ROLL_BLEED
const GAP = 0.6
const SPREAD_W = ROLL_W + GAP + FRAME_W

/**
 * The contact page: a risograph-printed cinema ticket lying on the page, photographed (studio/ticket/ticket.py), with what
 * is printed on it laid over the photograph in the same type and left clear, so the words can be selected and
 * followed where they are printed. It is as tall as the page lets it be and never wider than the page. Copying
 * the email address has the conductor punch it: a second photograph of that corner, taken under the same light
 * with the hole through it, comes up over the first. Beside it stands a run of the small tickets off the same roll,
 * their own picture a look up the bridge's tower, cut off top and bottom by the page.
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
      className="@container mx-auto -my-[4vh] w-full"
      style={{ maxWidth: `calc(90vh * ${SPREAD_W / FRAME_H})` }}
      initial={{ y: '18vh', opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 120, damping: 20, mass: 1 }}
    >
      <div className="flex items-stretch select-none" style={{ fontSize: `calc(100cqw / ${SPREAD_W})`, gap: `${GAP}em` }}>
        <div aria-hidden className="relative shrink-0 overflow-hidden" style={{ width: `${ROLL_W}em`, height: `${FRAME_H}em` }}>
          <img
            src="/objects/ticket-roll.avif"
            alt=""
            draggable={false}
            className="absolute left-0 max-w-none"
            style={{ width: `${ROLL_W}em`, height: `${ROLL_H}em`, top: `${(FRAME_H - ROLL_H) / 2}em` }}
          />
        </div>
        <div className="relative shrink-0" style={{ width: `${FRAME_W}em`, height: `${FRAME_H}em` }}>
          <img src="/objects/ticket.avif" alt="" draggable={false} className="absolute inset-0 size-full" width={FRAME_W * 72} height={FRAME_H * 72} />
          <img
            src="/objects/ticket-punched.avif"
            alt=""
            draggable={false}
            className="absolute transition-opacity duration-100"
            style={{ left: pct(B + PX, FRAME_W), top: pct(B + PY, FRAME_H), width: pct(PW, FRAME_W), height: pct(PH, FRAME_H), opacity: copied ? 1 : 0 }}
          />
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
