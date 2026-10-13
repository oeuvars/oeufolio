import { motion } from 'motion/react'

import type { Badge as BadgeData } from '../types'

type BadgeProps = {
  badge: BadgeData
}

/**
 * The ID badge, a Blender render (studio/badge.py). Its frame ends at the top of the panel, where the
 * ring runs out of shot, so the badge hangs from there and settles like something on a hook.
 */
export function Badge({ badge }: BadgeProps) {
  return (
    <div className="absolute inset-y-0 right-0 left-[var(--clear,0px)] flex justify-center overflow-hidden">
      <motion.img
        src={badge.src}
        alt={badge.alt}
        draggable={false}
        className="h-full w-auto max-w-none origin-top select-none"
        initial={{ rotate: 2.4, opacity: 0 }}
        animate={{ rotate: 0, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 34, damping: 4.5, mass: 1.6, delay: 0.25 }}
      />
    </div>
  )
}
