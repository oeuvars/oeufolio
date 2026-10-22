import { animate, useReducedMotion } from 'motion/react'
import { useLayoutEffect, useRef } from 'react'

import { PAGE, RAISE, STRIP, slide } from './house'

type StripHouseProps = {
  /** Whether the strip is unfolded, with the page's own picture over this one. */
  open: boolean
  /** On a phone the picture lies turned with its strip, under the upright page, so it does not shrink out of it. */
  turned?: boolean
}

/**
 * The work page's building from further back (studio/dollhouse.py --strip): the house small and lit at the
 * foot of a tall night, under the moon. Its page has no frame, so the picture runs on under the tab to the
 * strip's edge. When the strip folds, this picture starts where the page's stood, at its size, and shrinks
 * to its own place as the strip narrows: the page's picture growing out of this one, played backwards.
 */
export const StripHouse = ({ open, turned }: StripHouseProps) => {
  const picture = useRef<HTMLImageElement>(null)
  const was = useRef(open)
  const still = useReducedMotion()

  useLayoutEffect(() => {
    const folding = was.current && !open
    was.current = open
    const image = picture.current
    const strip = image?.closest<HTMLElement>('.strip')
    if (!folding || !image || !strip || still || turned) return

    // The strip is still unfolded when this lays out, and the page's picture was sized off it (Dollhouse).
    const unfolded = strip.getBoundingClientRect().width
    const metre = image.offsetWidth / STRIP
    const large = Math.min(1.87 * unfolded, 1.5 * window.innerHeight) / PAGE
    const across = unfolded / 2 - (image.offsetLeft + image.offsetParent!.getBoundingClientRect().left - strip.getBoundingClientRect().left + image.offsetWidth / 2)
    const shrinking = animate(image, { scale: [large / metre, 1], x: [across, 0], y: [RAISE * large, 0] }, slide)

    return () => shrinking.stop()
  }, [open, still, turned])

  return (
    <img
      ref={picture}
      aria-hidden
      src="/objects/dollhouse-strip.webp"
      alt=""
      className="absolute inset-y-0 left-0 h-full w-full max-w-none origin-bottom object-cover object-bottom"
    />
  )
}
