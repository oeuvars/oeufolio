import { type AnimationPlaybackControls, animate, useReducedMotion } from 'motion/react'
import { useLayoutEffect, useRef } from 'react'

import type { PosterMarks } from '../types'
import { POSTER, POSTER_COLUMN, moveFrom, posterFold, slide } from './house'
import posterMarks from './poster.json'

/** The companies the passages name, each under a stroke of highlighter: studio/poster/type.mjs measures them. */
const { size: REFERENCE, marks: MARKS } = posterMarks as PosterMarks

/**
 * The work page: a poster of lit windows in a block of flats at night (studio/poster), with "human
 * experience" glowing across them and passages set between them. Its type is in the picture, not over it: only the
 * links lie over it, one on each company the passages name, where its highlighter stroke is. It
 * is printed on the page's own paper: the strip, its tab and the wall round the windows are all one material, the
 * poster's bare wall as a tile (SiteShell), and the picture is only the light on it, laid over the paper as a screen,
 * so where it is dark the paper shows. It covers the strip out to its torn edge; the strip opens only as wide as the
 * poster is at the window's height (SiteShell), so almost none of it is cropped. On a phone the strip is far narrower
 * than the poster, so it runs the strip's width instead, with the paper above and below it.
 *
 * It grows out of its folded strip (StripPoster): under it lies the strip's own column, and when the strip unfolds
 * the poster starts with that column where the strip's stood, and moves to its place on the strip's spring as the rest
 * of the poster comes up over it. As it goes it leaves where its column was, for the folded strip to start from.
 */
export function Poster() {
  const sheet = useRef<HTMLDivElement>(null)
  const column = useRef<HTMLImageElement>(null)
  const light = useRef<HTMLImageElement>(null)
  const still = useReducedMotion()

  useLayoutEffect(() => {
    const page = sheet.current
    const own = column.current
    const full = light.current
    const strip = page?.closest<HTMLElement>('.strip')
    if (!page || !own || !full || !strip) return

    page.style.transform = ''
    // The strip is still folded when the page first lays out, if it is unfolding: narrower than the page.
    const folded = strip.querySelector<HTMLElement>('[data-poster-column]')
    const unfolding = folded && strip.getBoundingClientRect().width < page.parentElement!.getBoundingClientRect().width - 40
    const place = folded?.getBoundingClientRect()
    if (folded) folded.style.visibility = 'hidden'
    const motions: AnimationPlaybackControls[] = []
    if (still) full.style.opacity = '1'
    else {
      if (unfolding && place) motions.push(animate(page, moveFrom(place, page, own.getBoundingClientRect()), slide))
      motions.push(animate(full, { opacity: [0, 1] }, { duration: unfolding ? 0.45 : 0.6, delay: unfolding ? 0 : 0.3, ease: [0.215, 0.61, 0.355, 1] }))
    }

    return () => {
      posterFold.column = own.getBoundingClientRect()
      if (folded) folded.style.visibility = ''
      for (const motion of motions) motion.stop()
    }
  }, [still])

  return (
    <div className="absolute inset-0 overflow-hidden mix-blend-screen [container-type:size]">
      <h2 className="sr-only">Experience</h2>
      {/* The poster as the page lays it: across the strip on a phone, else covering it, and centred. */}
      <div
        ref={sheet}
        className="absolute top-1/2 left-1/2 w-full origin-top-left -translate-x-1/2 -translate-y-1/2 [mask-image:linear-gradient(to_bottom,transparent,#000_6%,#000_94%,transparent)] md:w-[max(100cqw,calc(100cqh*2208/2943))] md:[mask-image:none]"
        style={{ aspectRatio: `${POSTER.width} / ${POSTER.height}` }}
      >
        <img
          ref={column}
          aria-hidden
          src="/objects/poster-strip.avif"
          alt=""
          draggable={false}
          className="absolute top-0 h-full max-w-none select-none"
          style={{ left: `${(100 * POSTER_COLUMN.left) / POSTER.width}%`, width: `${(100 * POSTER_COLUMN.width) / POSTER.width}%` }}
        />
        <img
          ref={light}
          src="/objects/poster.avif"
          alt="A poster of a block of flats at night, its lit windows each a different room with someone in silhouette: a saxophonist, a woman at a candle, two women at a yellow window, a child at a lilac curtain. The words human experience glow across it, and four italic passages are set between the windows."
          width={POSTER.width}
          height={POSTER.height}
          draggable={false}
          className="absolute inset-0 size-full select-none opacity-0"
        />
        {MARKS.map(({ label, href, left, right, baseline, size }) => (
          <a
            key={label}
            href={href}
            target="_blank"
            rel="noreferrer"
            draggable={false}
            aria-label={label}
            className="absolute rounded-[0.15em] outline-offset-2 focus-visible:outline-2 focus-visible:outline-white"
            style={{
              left: `${(100 * left) / REFERENCE[0]}%`,
              width: `${(100 * (right - left + 0.3 * size)) / REFERENCE[0]}%`,
              top: `${(100 * (baseline - 0.87 * size)) / REFERENCE[1]}%`,
              height: `${(100 * 1.1 * size) / REFERENCE[1]}%`,
            }}
          />
        ))}
      </div>
    </div>
  )
}
