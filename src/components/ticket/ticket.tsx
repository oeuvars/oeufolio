import { useEffect, useRef, useState } from 'react'

import { profile } from '../../content'
import { paint } from '../../lib/paint'
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
// How far above the spread the Leica's top lies in the photograph, in the spread's em. On a phone the page is fitted
// to the set from there to the ticket's foot, so that the camera is not cut off and the set lies in the page's middle.
const ABOVE = 3.6
const SET_H = ABOVE + B + H
// The photograph of the whole set and the one of the punched hole, each by the box it covers in the spread's em.
const [OX, OY, OW, OH] = contact.open
const [PX, PY, PW, PH] = contact.punch

// The photograph of the set.
const PHOTO = '/objects/contact-open.avif'

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
export const Ticket = () => {
  const [copied, setCopied] = useState(false)
  const photo = useRef<HTMLCanvasElement>(null)
  const [painted, setPainted] = useState(false)

  // The photograph drawn again whenever its box changes size, the last drawing to start the one kept.
  useEffect(() => {
    const canvas = photo.current
    if (!canvas) return
    let going: AbortController | null = null
    let drawn = 0
    const draw = () => {
      const across = canvas.offsetWidth
      if (!across || Math.abs(across - drawn) < 1) return
      drawn = across
      going?.abort()
      going = new AbortController()
      paint(canvas, PHOTO, across, going.signal)
        .then(() => setPainted(true))
        .catch(() => {})
    }
    const watching = new ResizeObserver(draw)
    watching.observe(canvas)
    return () => {
      watching.disconnect()
      going?.abort()
    }
  }, [])

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
      style={{ maxWidth: `min(calc(90vh * ${SPREAD_W / FRAME_H}), calc((var(--page-room, 200vh) - 2rem) * ${SPREAD_W / SET_H}))` }}
    >
      {/* The set stays as it lies, open or folded: the strip only uncovers it, so the photographed hide never moves
          against the hide the strip is laid with. */}
      <div
        // On a phone the room above the spread is kept for the camera, and the bleed below the ticket is given up (ABOVE).
        className="relative select-none max-md:-mb-[1.2em] max-md:mt-[3.6em]"
        style={{ fontSize: `calc(100cqw / ${SPREAD_W})`, width: `${SPREAD_W}em`, height: `${FRAME_H}em` }}
      >
        {/* The photograph is drawn on a canvas (paint) as large as the open page shows it, and laid
            as a picture only until then. */}
        <canvas ref={photo} aria-hidden className="pointer-events-none absolute" style={over(OX, OY, OW, OH)} />
        {!painted && (
          <img src={PHOTO} alt="" aria-hidden draggable={false} className="pointer-events-none absolute max-w-none" style={over(OX, OY, OW, OH)} />
        )}
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
      </div>
    </div>
  )
}
