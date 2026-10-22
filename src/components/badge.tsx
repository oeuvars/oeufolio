import { animate, motion, useMotionValue } from 'motion/react'
import { useEffect, useRef } from 'react'

import type { Badge as BadgeData } from '../types'

type BadgeProps = {
  badge: BadgeData
  /** The strip's width when it is unfolded. The badge is laid out on a page that wide. */
  page: number
  /** How much of the page's width the tabs at its two edges lie over. */
  margin: number
  /** Whether the strip is unfolded. Folded, the badge is decoration. */
  open: boolean
  /** How far the panel the sheet is pinned to runs on past the strip's right edge, under the strip's tab. */
  past: number
}

/** How much of the image's width the holder takes, and the image's width to its height. */
const HOLDER = 515 / 720
const SHAPE = 720 / 900
// How far the card's middle lies right of the image's, in its width: the card is a little off the holder's middle.
const CARD_OFF = (162 + 577) / 2 / 720 - 0.5
// How far either way, in degrees, the card swings on its ring when it is pulled.
const SWING = 20
// Let go, the card swings back through the middle a few times before it hangs still.
const SETTLE = { type: 'spring', stiffness: 34, damping: 4.5, mass: 1.6 } as const

/**
 * The ID badge (studio/badge.py) hanging in the middle of its page. The page is a sheet as wide as the
 * unfolded strip and fixed to the strip's right edge. A folded strip is that sheet slid in under the one
 * before it: what shows is the sheet's own right-hand margin, with the edge of the badge on it, and the
 * strip's tab stands on bare paper. Unfolding slides the sheet out. The badge's frame ends at the top of
 * the sheet, where its ring runs out of shot. Its vinyl is see-through, so the backdrop shows through.
 */
export const Badge = ({ badge, page, margin, open, past }: BadgeProps) => {
  const rotate = useMotionValue(2.4)
  const ring = useRef<HTMLDivElement>(null)
  // Where the ring is on the screen while the card is held, and the card's turn less the pointer's when it was taken.
  const held = useRef<{ x: number; y: number; from: number } | null>(null)

  useEffect(() => {
    const hanging = animate(rotate, 0, { ...SETTLE, delay: 0.25 })
    return () => hanging.stop()
  }, [rotate])

  // The pointer's turn about the ring, in degrees: the card turned this far has its foot under the pointer.
  const turn = (x: number, y: number, at: { x: number; y: number }) =>
    (Math.atan2(at.x - x, y - at.y) * 180) / Math.PI

  const take = (event: React.PointerEvent) => {
    if (!open || event.button !== 0 || !ring.current) return
    const box = ring.current.getBoundingClientRect()
    const at = { x: box.left + box.width / 2, y: box.top }
    rotate.stop()
    held.current = { ...at, from: rotate.get() - turn(event.clientX, event.clientY, at) }
    event.currentTarget.setPointerCapture(event.pointerId)
  }

  const pull = (event: React.PointerEvent) => {
    const hold = held.current
    if (!hold) return
    const angle = hold.from + turn(event.clientX, event.clientY, hold)
    rotate.set(Math.max(-SWING, Math.min(SWING, angle)))
  }

  const release = () => {
    if (!held.current) return
    held.current = null
    animate(rotate, 0, { ...SETTLE, velocity: rotate.getVelocity() })
  }

  return (
    <div
      className="absolute inset-y-0 right-0 flex justify-center bg-cover bg-center"
      // The page's own paper, grain and all, is the panel under it (SiteShell), so the sheet lays nothing of its own.
      style={{ width: page, right: past, backgroundImage: badge.backdrop.image && `url(${badge.backdrop.image})` }}
    >
      {/* Open, the card can be taken and swung on its ring; let go, it swings back and hangs still. It lies
          over the open page's frame, which SiteShell lays over the strip with nothing on it. */}
      <div
        ref={ring}
        // The card, not the holder, is centred on the page.
        style={{ translate: `${-CARD_OFF * 100}% 0` }}
        className={`relative z-1 block h-full origin-top ${open ? '' : 'pointer-events-none'}`}
      >
        <motion.img
          src={badge.src}
          alt={open ? badge.alt : ''}
          aria-hidden={!open}
          draggable={false}
          className={`w-auto max-w-none origin-top touch-pan-y select-none [filter:drop-shadow(0_10px_14px_rgb(0_0_0/0.3))] ${open ? 'cursor-grab active:cursor-grabbing' : ''}`}
          // As tall as the sheet, unless that would put the holder under the tabs.
          style={{ height: `min(100%, ${(page - 2 * margin) / HOLDER / SHAPE}px)`, rotate }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ ...SETTLE, delay: 0.25 }}
          onPointerDown={take}
          onPointerMove={pull}
          onPointerUp={release}
          onPointerCancel={release}
          onLostPointerCapture={release}
        />
      </div>
    </div>
  )
}
