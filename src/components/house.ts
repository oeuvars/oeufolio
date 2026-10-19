/**
 * The measures the work page's two pictures share (studio/dollhouse.py), for growing one out of the other.
 * PAGE and STRIP are how many of the model's metres each picture is across. RAISE is how many metres up
 * from the foot of its frame the strip's house stands, where the page's stands on its foot.
 */
export const PAGE = 28.9
export const STRIP = 16.3
export const RAISE = 1

/** The spring SiteShell opens and folds a strip on. The house moves on the same one, so the two keep step. */
export const slide = { type: 'spring', stiffness: 150, damping: 21, mass: 1 } as const

/** The poster that is the work page (studio/poster), in pixels. Its strip opens no wider than it. */
export const POSTER = { width: 2208, height: 2943 } as const

/** The poster's middle column, which its folded strip shows (STRIP in studio/poster/poster.py), in its pixels. */
export const POSTER_COLUMN = { left: 900, width: 882 } as const

/**
 * Where the open poster's column was on the screen as its page went, for the folded strip to start from. The page
 * leaves it as it goes (Poster) and the strip takes it as it folds (StripPoster), in the same commit. The page also
 * hides the strip's column while it is there and shows it again as it goes, so one of the two is always showing.
 */
export const posterFold: { column: DOMRect | null } = { column: null }

/**
 * Moves an element so the part of it now at `at` stands at `place` instead, scaled about the element's top left, and
 * returns the keyframes from there back to where it lies. It is stood there at once, so the first frame painted
 * already has it there, before any animation of it has run.
 */
export const moveFrom = (place: DOMRect, element: HTMLElement, at: DOMRect) => {
  const box = element.getBoundingClientRect()
  const scale = place.width / at.width
  const x = place.left - box.left - scale * (at.left - box.left)
  const y = place.top - box.top - scale * (at.top - box.top)
  element.style.transform = `translateX(${x}px) translateY(${y}px) scale(${scale})`
  return { x: [x, 0], y: [y, 0], scale: [scale, 1] }
}
