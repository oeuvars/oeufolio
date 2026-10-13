import { animate, useReducedMotion } from 'motion/react'
import { useLayoutEffect, useRef } from 'react'

import type { Role } from '../types'
import { PAGE, RAISE, STRIP, slide } from './house'

type DollhouseProps = {
  roles: Role[]
}

/** The render's size in pixels. */
const WIDTH = 2600
const HEIGHT = 1578

/**
 * The building (studio/dollhouse.py): a model of a house cut open at the front, standing at night in the
 * snow among pines, with mountains behind. There is a floor for each job, newest at the top, and over each
 * a painted board with the company on it in a lit sign. The picture is far wider than the sheet, which is
 * about the house's width, and the page shows as much of the country either side as it has room for: the
 * panel's own edges are where the picture stops. It has no sky of its own, so the page's night shows there,
 * and it comes up behind the masthead, as a poster's picture does. The lettering is in the picture, so the
 * jobs are listed again here for whoever cannot see it.
 *
 * The folded strip shows the same house from further back, small at the foot of its frame. When the strip
 * opens, the picture starts at that size and in that place, over the small one, and grows to its own as
 * the strip widens: the house is the thing that opens.
 */
export function Dollhouse({ roles }: DollhouseProps) {
  const picture = useRef<HTMLImageElement>(null)
  const still = useReducedMotion()

  useLayoutEffect(() => {
    const image = picture.current
    const strip = image?.closest<HTMLElement>('.strip')
    const page = image?.parentElement
    if (!image || !strip || !page || still) return

    const rem = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16
    // The strip is still folded when the page first lays out. Its picture starts a rem in, under the strip before it.
    const folded = strip.getBoundingClientRect().width
    if (folded > page.offsetWidth / 2) return

    const metre = (folded - rem) / STRIP
    const small = metre / (image.offsetWidth / PAGE)
    const across = rem + (folded - rem) / 2 - page.offsetWidth / 2
    const growing = animate(image, { scale: [small, 1], x: [across, 0], y: [-RAISE * metre, 0] }, slide)

    return () => growing.stop()
  }, [still])

  return (
    <>
      <img
        ref={picture}
        src="/objects/dollhouse.webp"
        alt="A doll's house with its front off, lit up at night in the snow, with pines either side and mountains behind. It has three floors under a slate roof: a parcel room shelved with pink cake boxes, a banking hall with marble columns and a vault, and a dispatch room stacked with trunks. A lit sign over each floor names a company."
        width={WIDTH}
        height={HEIGHT}
        draggable={false}
        className="relative left-1/2 -mt-[15.8cqw] block h-auto w-[187cqw] max-w-none origin-bottom -translate-x-1/2 select-none md:-mt-[min(15.8cqw,12.6vh)] md:w-[min(187cqw,150vh)]"
      />
      <ol className="sr-only">
        {roles.map((role) => (
          <li key={`${role.org}-${role.period}`}>
            {role.org}, {role.period}
          </li>
        ))}
      </ol>
    </>
  )
}
