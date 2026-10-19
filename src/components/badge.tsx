import { Link } from '@tanstack/react-router'
import { motion } from 'motion/react'

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

/**
 * The ID badge (studio/badge.py) hanging in the middle of its page. The page is a sheet as wide as the
 * unfolded strip and fixed to the strip's right edge. A folded strip is that sheet slid in under the one
 * before it: what shows is the sheet's own right-hand margin, with the edge of the badge on it, and the
 * strip's tab stands on bare paper. Unfolding slides the sheet out. The badge's frame ends at the top of
 * the sheet, where its ring runs out of shot. Its vinyl is see-through, so the backdrop shows through.
 */
export const Badge = ({ badge, page, margin, open, past }: BadgeProps) => {
  return (
    <div
      className="absolute inset-y-0 right-0 flex justify-center bg-cover bg-center"
      // The page's own paper, grain and all, is the panel under it (SiteShell), so the sheet lays nothing of its own.
      style={{ width: page, right: past, backgroundImage: badge.backdrop.image && `url(${badge.backdrop.image})` }}
    >
      {/* Open, the card is the way to the résumé as a page of text. It tips on its ring as the pointer comes to it. It
          lies over the open page's frame, which SiteShell lays over the strip with nothing on it. */}
      <Link
        to="/resume"
        aria-label="Résumé"
        tabIndex={open ? undefined : -1}
        aria-hidden={!open || undefined}
        // The card, not the holder, is centred on the page.
        style={{ translate: `${-CARD_OFF * 100}% 0` }}
        className={`relative z-1 block h-full origin-top rounded-sm focus-visible:outline-2 focus-visible:outline-offset-[-6px] focus-visible:outline-[#3a281c] ${open ? '' : 'pointer-events-none'}`}
      >
        <motion.img
          src={badge.src}
          alt={open ? badge.alt : ''}
          aria-hidden={!open}
          draggable={false}
          className="w-auto max-w-none origin-top select-none [filter:drop-shadow(0_10px_14px_rgb(0_0_0/0.3))]"
          // As tall as the sheet, unless that would put the holder under the tabs.
          style={{ height: `min(100%, ${(page - 2 * margin) / HOLDER / SHAPE}px)` }}
          initial={{ rotate: 2.4, opacity: 0 }}
          animate={{ rotate: 0, opacity: 1 }}
          whileHover={open ? { rotate: -1.2, transition: { type: 'spring', stiffness: 90, damping: 10 } } : undefined}
          transition={{ type: 'spring', stiffness: 34, damping: 4.5, mass: 1.6, delay: 0.25 }}
        />
      </Link>
    </div>
  )
}
