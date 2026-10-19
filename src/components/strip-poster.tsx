import { animate, useReducedMotion } from 'motion/react'
import { useLayoutEffect, useRef, useState } from 'react'

import { POSTER, POSTER_COLUMN, moveFrom, posterFold, slide } from './house'

type StripPosterProps = {
  /** Whether the strip is unfolded, with the page's own poster over this one. */
  open: boolean
}

/**
 * The work page's poster folded into its strip (studio/poster): the middle column of its windows, the full height
 * of it, with the sign's light running in from either side but none of the passages, which come with the page.
 * Like the building, it has no frame, so it runs on under the tab to the strip's edge. It is light printed on the
 * strip's paper, as the page is, so it is laid over the paper as a screen.
 *
 * When the strip folds, the column starts where the page's stood (Poster), with the whole poster over it fading
 * away, and moves to its own place as the strip narrows: the page's poster growing out of it, played backwards.
 */
export const StripPoster = ({ open }: StripPosterProps) => {
  const column = useRef<HTMLDivElement>(null)
  const light = useRef<HTMLImageElement>(null)
  const was = useRef(open)
  // The whole poster is only laid here once its page has been open, so it is loaded by the time the strip folds.
  const [shown, setShown] = useState(open)
  const still = useReducedMotion()

  useLayoutEffect(() => {
    if (open) setShown(true)
    const folding = was.current && !open
    was.current = open
    const place = posterFold.column
    posterFold.column = null
    const own = column.current
    const full = light.current
    if (!folding || !place || !own || !full || still) return

    own.style.transform = ''
    full.style.opacity = '1'
    const motions = [
      animate(own, moveFrom(place, own, own.getBoundingClientRect()), slide),
      animate(full, { opacity: [1, 0] }, { duration: 0.45, ease: [0.215, 0.61, 0.355, 1] }),
    ]

    // Cut short, it is left where it lies folded, under the page that came back over it.
    return () => {
      for (const motion of motions) motion.stop()
      own.style.transform = ''
      full.style.opacity = ''
    }
  }, [open, still])

  return (
    <div aria-hidden className="absolute inset-0 mix-blend-screen [container-type:size]">
      {/* The column as a picture covering the strip, centred, and the whole poster round it where it stands. */}
      <div
        ref={column}
        data-poster-column
        className="absolute top-1/2 left-1/2 h-[max(100cqh,calc(100cqw*2943/882))] origin-top-left -translate-x-1/2 -translate-y-1/2"
        style={{ aspectRatio: `${POSTER_COLUMN.width} / ${POSTER.height}` }}
      >
        <img src="/objects/poster-strip.avif" alt="" draggable={false} className="size-full max-w-none select-none" />
        {shown && (
          <img
            ref={light}
            src="/objects/poster.avif"
            alt=""
            draggable={false}
            className="absolute top-0 h-full max-w-none select-none opacity-0"
            style={{ left: `${(-100 * POSTER_COLUMN.left) / POSTER_COLUMN.width}%`, width: `${(100 * POSTER.width) / POSTER_COLUMN.width}%` }}
          />
        )}
      </div>
    </div>
  )
}
