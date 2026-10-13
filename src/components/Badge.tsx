import { motion } from 'motion/react'

import type { Badge as BadgeData } from '../types'

type BadgeProps = {
  badge: BadgeData
}

/**
 * The ID badge (studio/badge.py) on its backdrop. The badge's frame ends at the top of the panel, where
 * the ring runs out of shot, so it hangs from there and settles like something on a hook. Its vinyl is
 * see-through, so the backdrop shows through the holder.
 */
export function Badge({ badge }: BadgeProps) {
  return (
    <>
      <div
        aria-hidden
        className="absolute inset-0 rounded-[0.7rem] bg-cover bg-center"
        style={{
          backgroundColor: badge.backdrop.color,
          backgroundImage: badge.backdrop.image && `url(${badge.backdrop.image})`,
        }}
      />
      <div className="absolute inset-y-0 right-0 left-[var(--clear,0px)] flex justify-center overflow-hidden">
        <motion.img
          src={badge.src}
          alt={badge.alt}
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
