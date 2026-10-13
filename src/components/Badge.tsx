import { motion } from 'motion/react'

import type { Badge as BadgeData } from '../types'

type BadgeProps = {
  badge: BadgeData
  /** How far in from the panel's left edge the badge may start: the last strip's tab lies over that much. */
  clear: number
  /** Whether the strip is unfolded. Folded, the badge is decoration and the strip shows a slice of it. */
  open: boolean
}

/**
 * The ID badge (studio/badge.py) on its backdrop. It hangs in the middle of the strip whether the strip
 * is folded or not, so a folded strip shows a slice of it and unfolding uncovers the rest. Its frame ends
 * at the top of the panel, where the ring runs out of shot. Its vinyl is see-through, so the backdrop
 * shows through the holder.
 */
export function Badge({ badge, clear, open }: BadgeProps) {
  return (
    <>
      <div
        aria-hidden
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundColor: badge.backdrop.color,
          backgroundImage: badge.backdrop.image && `url(${badge.backdrop.image})`,
        }}
      />
      <div className="absolute inset-y-0 right-0 flex justify-center overflow-hidden" style={{ left: clear }}>
        <motion.img
          src={badge.src}
          alt={open ? badge.alt : ''}
          aria-hidden={!open}
          draggable={false}
          className="h-full w-auto max-w-none origin-top select-none [filter:drop-shadow(0_10px_14px_rgb(0_0_0/0.3))]"
          initial={{ rotate: 2.4, opacity: 0 }}
          animate={{ rotate: 0, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 34, damping: 4.5, mass: 1.6, delay: 0.25 }}
        />
      </div>
    </>
  )
}
