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

/**
 * The contact page: a cinema ticket lying on the page, photographed (studio/ticket/ticket.py), with what
 * is printed on it laid over the photograph in the same type and left clear, so the words can be selected
 * and followed where they are printed. It is as tall as the page lets it be and never wider than the page.
 * Copying the email address punches the ticket and stamps it: a second photograph of that corner, taken
 * under the same light, comes up over the first.
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
      style={{ maxWidth: `calc(88vh * ${FRAME_W / FRAME_H})` }}
      initial={{ y: '18vh', opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 120, damping: 20, mass: 1 }}
    >
      <div className="relative select-none" style={{ aspectRatio: `${FRAME_W} / ${FRAME_H}`, fontSize: `calc(100cqw / ${FRAME_W})` }}>
        <img
          src="/objects/ticket.avif"
          alt=""
          draggable={false}
          className="absolute inset-0 size-full"
          width={FRAME_W * 72}
          height={FRAME_H * 72}
        />
        <img
          src="/objects/ticket-punched.avif"
          alt=""
          draggable={false}
          className="absolute transition-opacity duration-150"
          style={{ left: pct(B + PX, FRAME_W), top: pct(B + PY, FRAME_H), width: pct(PW, FRAME_W), height: pct(PH, FRAME_H), opacity: copied ? 1 : 0 }}
        />
        <div
          data-plate="ticket"
          className="absolute text-transparent select-text [&_.ink-only]:invisible"
          style={{ left: `${B}em`, top: `${B}em`, width: `${W}em`, height: `${H}em` }}
        >
          <Print onCopy={copy} copied={copied} />
        </div>
        <div
          data-plate="stamp"
          aria-hidden
          className="pointer-events-none invisible absolute"
          style={{ left: `${B}em`, top: `${B}em`, width: `${W}em`, height: `${H}em` }}
        >
          <Stamp />
        </div>
      </div>
    </motion.div>
  )
}

/**
 * The conductor's stamp, for the plate alone: a ring of rubber with the word across it, struck at a slant
 * beside the punch.
 */
function Stamp() {
  const [cx, cy, r, turn] = ticket.stamp

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="absolute inset-0 size-full fill-current"
      style={{ color: '#000' }}
    >
      <g transform={`rotate(${turn} ${cx} ${cy})`}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="currentColor" strokeWidth={0.13} />
        <circle cx={cx} cy={cy} r={r - 0.24} fill="none" stroke="currentColor" strokeWidth={0.05} />
        <rect x={cx - r - 0.15} y={cy - 0.42} width={2 * r + 0.3} height={0.84} />
        <text
          x={cx}
          y={cy + 0.27}
          textAnchor="middle"
          fill="#fff"
          style={{ font: '800 0.74px "JetBrains Mono Variable", monospace', letterSpacing: '0.08px' }}
        >
          COPIED
        </text>
        <text x={cx} y={cy - 0.72} textAnchor="middle" style={{ font: '700 0.32px "JetBrains Mono Variable", monospace', letterSpacing: '0.1px' }}>
          ★ ★ ★
        </text>
        <text x={cx} y={cy + 1.0} textAnchor="middle" style={{ font: '700 0.3px "JetBrains Mono Variable", monospace', letterSpacing: '0.08px' }}>
          ADMITTED
        </text>
      </g>
    </svg>
  )
}
