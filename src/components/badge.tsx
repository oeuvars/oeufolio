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

/** How much of the image's width the holder takes, and the photograph's width to its height. */
const HOLDER = 515 / 720
const SHAPE = 720 / 900
// The image runs on above the photograph to carry the ring out of shot, by this much of the photograph's height.
const HEAD = 76 / 900
// Where the ring hangs from, the inside of its arch, in the whole image's width and height.
const PIVOT = { x: 384.1 / 720, y: 26.8 / 976 }
// How far the card's middle lies right of the image's, in its width: the card is a little off the holder's middle.
const CARD_OFF = (162 + 577) / 2 / 720 - 0.5
// How far either way, in degrees, the card swings on its ring when it is pulled.
const SWING = 9
// The card turns this much of the way the pointer goes round the ring, as if it were heavy and stiff on it.
const FOLLOW = 0.45
// Hung up, the card swings through the middle a few times before it hangs still.
const SETTLE = { type: 'spring', stiffness: 34, damping: 4.5, mass: 1.6 } as const
// Let go, it swings back past the middle once, a little, and hangs still.
const RELEASE = { type: 'spring', stiffness: 60, damping: 11, mass: 1.6 } as const

/**
 * The ID badge (studio/badge.py) hanging in the middle of its page. The page is a sheet as wide as the
 * unfolded strip and fixed to the strip's right edge. A folded strip is that sheet slid in under the one
 * before it: what shows is the sheet's own right-hand margin, with the edge of the badge on it, and the
 * strip's tab stands on bare paper. Unfolding slides the sheet out. The badge's frame ends at the top of
 * the sheet, where its ring runs out of shot to the point it hangs from. Its vinyl is see-through, so the
 * backdrop shows through.
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
    // The box is as wide as the image, and its top is the photograph's: the image runs on above it.
    const box = ring.current.getBoundingClientRect()
    const tall = box.width / SHAPE
    const at = { x: box.left + box.width * PIVOT.x, y: box.top - tall * HEAD + tall * (1 + HEAD) * PIVOT.y }
    rotate.stop()
    // Taken mid-swing, it stays where it is: `from` is its turn as the pull that would put it there.
    const pulled = SWING * Math.atanh(Math.max(-0.99, Math.min(0.99, rotate.get() / SWING)))
    held.current = { ...at, from: pulled - FOLLOW * turn(event.clientX, event.clientY, at) }
    event.currentTarget.setPointerCapture(event.pointerId)
  }

  const pull = (event: React.PointerEvent) => {
    const hold = held.current
    if (!hold) return
    // It gives less the further it is pulled, up to SWING.
    const angle = hold.from + FOLLOW * turn(event.clientX, event.clientY, hold)
    rotate.set(SWING * Math.tanh(angle / SWING))
  }

  const release = () => {
    if (!held.current) return
    held.current = null
    animate(rotate, 0, { ...RELEASE, velocity: rotate.getVelocity() })
  }

  const photo = `min(100%, ${(page - 2 * margin) / HOLDER / SHAPE}px)`

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
        className={`relative z-1 block h-full ${open ? '' : 'pointer-events-none'}`}
      >
        <motion.img
          src={badge.src}
          alt={open ? badge.alt : ''}
          aria-hidden={!open}
          draggable={false}
          className={`relative block w-auto max-w-none touch-pan-y select-none will-change-transform [filter:drop-shadow(0_10px_14px_rgb(0_0_0/0.3))] ${open ? 'cursor-grab active:cursor-grabbing' : ''}`}
          // The photograph is as tall as the sheet, unless that would put the holder under the tabs. The ring above it
          // stands out over the sheet's top, which hides it until the card swings. It is a layer of its own, so its
          // shadow is drawn once and not again on every frame the strips slide or the card swings.
          style={{
            height: `calc(${photo} * ${1 + HEAD})`,
            top: `calc(${photo} * ${-HEAD})`,
            transformOrigin: `${PIVOT.x * 100}% ${PIVOT.y * 100}%`,
            rotate,
          }}
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
