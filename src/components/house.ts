/**
 * The measures the work page's two pictures share (studio/dollhouse.py), for growing one out of the other.
 * PAGE and STRIP are how many of the model's metres each picture is across. RAISE is how many metres up
 * from the foot of its frame the strip's house stands, where the page's stands on its foot.
 */
export const PAGE = 28.9
export const STRIP = 16.3
export const RAISE = 1

/** The spring SiteShell opens and folds a strip on. The house moves on the same one, so the two keep step. */
export const slide = { type: 'spring', stiffness: 60, damping: 13.5, mass: 1 } as const

/** The poster that is the work page (studio/poster), in pixels. Its strip opens no wider than it. */
export const POSTER = { width: 2208, height: 2943 } as const

/** The poster's middle column, which its folded strip shows (STRIP in studio/poster/poster.py), in its pixels. */
export const POSTER_COLUMN = { left: 900, width: 882 } as const
