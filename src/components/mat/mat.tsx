import { useLayoutEffect, useRef, useState } from 'react'

import { cn } from '../../lib/utils'
import type { PlateId, PropId } from '../../types'
import { Rulers } from './rulers'
import { DIALS, PLATES, PORTRAITS } from './layout'
import { WatchHands } from './watch-hands'

type MatProps = {
  /** What on the mat the page needs to reach: links and the parts that move. Each marks its root with data-prop. */
  children: React.ReactNode
  className?: string
}

/** Which plate is showing, how many pixels an em of it is, and where its top left lies on the mat. */
type Geometry = {
  id: PlateId
  em: number
  x: number
  y: number
}

// A mat narrower than this shows the tall plate, as wide as the mat and as long as it runs.
const WIDE_FROM = 420
// An em of the plate is drawn at most this many pixels, where its render is still sharp.
const LARGEST = 22
// The plate and its light lie over the rulers, which are printed on the mat under everything on it.
const LAID = 'pointer-events-none absolute z-1 max-w-none'

/** Where a rectangle of the plate, given in its em, lies on the mat. */
const over = (geometry: Geometry, x: number, y: number, w: number, h: number): React.CSSProperties => {
  const { em } = geometry
  return { left: geometry.x + x * em, top: geometry.y + y * em, width: w * em, height: h * em }
}

/**
 * A cutting mat in teal leather, seen from overhead, with the things left on it as on a desk in use. All of
 * it is one photograph of one set, rendered in the studio under one light, so every object shades the others
 * and throws its own shadow. The page lays the plate over its own leather, as large as lets all of it show.
 * The desk is lit by one soft yellow lamp over it, on the side of the one at it. The plate is the objects in that
 * light, and with it comes the light on the mat, a map the leather, its rules and its rulers are multiplied by.
 * Where the lamp lights the leather brighter than it was photographed, a second map adds the rest. A prop the
 * plate's camera does not show, seen from a camera of its own (PORTRAITS), lies over the plate as its picture.
 */
export const Mat = ({ children, className }: MatProps) => {
  const [geometry, setGeometry] = useState<Geometry | null>(null)
  const root = useRef<HTMLDivElement>(null)
  const sheet = useRef<HTMLDivElement>(null)

  // The plate fits the mat, and the objects' boxes follow it. It is laid before it is first painted, so the
  // strip never uncovers a bare mat.
  useLayoutEffect(() => {
    const frame = root.current
    const board = sheet.current
    if (!frame || !board) return
    const compose = () => {
      const width = board.clientWidth
      const id: PlateId = width >= WIDE_FROM ? 'wide' : 'tall'
      const plate = PLATES[id]
      const [w, h] = plate.size
      let em: number
      let x = 0
      if (id === 'wide') {
        board.style.minHeight = ''
        // The wide plate keeps to the top of the mat.
        em = Math.min(width / w, board.clientHeight / h, LARGEST)
        x = (width - w * em) / 2
      } else {
        em = width / w
        board.style.minHeight = `${Math.ceil(h * em)}px`
      }
      frame.style.setProperty('--s', (em / 16).toFixed(4))
      board.querySelectorAll<HTMLElement>('[data-prop]').forEach((el) => {
        const prop = el.dataset.prop as PropId
        const seen = PORTRAITS[id]?.[prop]
        if (seen) {
          // A prop seen from its own camera is reached where it shows in its picture, upright, and as large.
          const [left, top, w, h] = seen.body
          el.style.setProperty('--x', (x + (left + w / 2) * em).toFixed(1))
          el.style.setProperty('--y', ((top + h / 2) * em).toFixed(1))
          el.style.setProperty('--r', '0')
          el.style.setProperty('--w', (w * em).toFixed(1))
          el.style.setProperty('--h', (h * em).toFixed(1))
          return
        }
        const at = plate.at[prop]
        if (!at) return
        el.style.setProperty('--x', (x + at[0] * em).toFixed(1))
        el.style.setProperty('--y', (at[1] * em).toFixed(1))
        el.style.setProperty('--r', String(at[2]))
      })
      setGeometry((was) => (was && was.id === id && was.em === em && was.x === x ? was : { id, em, x, y: 0 }))
    }
    compose()
    const watching = new ResizeObserver(compose)
    watching.observe(board)
    return () => watching.disconnect()
  }, [])

  // The folder tab the page hangs from is cut from this leather (SiteShell's Tab), so it takes the same light: the
  // map of it, laid where it lies over the mat.
  useLayoutEffect(() => {
    const frame = root.current
    const board = sheet.current
    const tabs = [...document.querySelectorAll<HTMLElement>('[data-mat-light]')]
    if (!frame || !board || !tabs.length || !geometry) return
    const plate = PLATES[geometry.id]
    const [w, h] = plate.size
    const [bx, by] = plate.bleed
    const { em } = geometry
    const place = () => {
      const mat = board.getBoundingClientRect()
      for (const tab of tabs) {
        const at = tab.getBoundingClientRect()
        tab.style.setProperty('--light-at', `${mat.left - at.left + geometry.x - bx * em}px ${mat.top - at.top + geometry.y - by * em}px`)
      }
    }
    for (const tab of tabs) {
      tab.style.setProperty('--light-rim', plate.rim)
      tab.style.setProperty('--light-image', `url(/objects/mat/desk-${geometry.id}-light.avif)`)
      tab.style.setProperty('--light-past', `url(/objects/mat/desk-${geometry.id}-light-past.avif)`)
      tab.style.setProperty('--light-size', `${(w + 2 * bx) * em}px ${(h + 2 * by) * em}px`)
    }
    place()
    // The strip slides open after the mat is laid, and the page scrolls under the tab.
    const moving = new ResizeObserver(place)
    moving.observe(board)
    const strip = tabs[0].closest('section')
    if (strip) moving.observe(strip)
    window.addEventListener('scroll', place, true)
    return () => {
      moving.disconnect()
      window.removeEventListener('scroll', place, true)
      for (const tab of tabs) for (const name of ['--light-rim', '--light-image', '--light-past', '--light-size', '--light-at']) tab.style.removeProperty(name)
    }
  }, [geometry])

  const plate = geometry && PLATES[geometry.id]

  return (
    <div
      ref={root}
      data-plate={geometry?.id}
      className={cn(
        'group/mat mat @container relative isolate flex flex-col [--s:1]',
        className,
      )}
    >
      <div
        ref={sheet}
        className="relative flex-1 overflow-hidden select-none before:pointer-events-none before:absolute before:inset-0 before:bg-mat-grain before:bg-size-[220px_220px] before:opacity-20 before:mix-blend-multiply"
      >
        <div aria-hidden className="mat-rules pointer-events-none absolute inset-[22px]" />
        <Rulers />
        <svg
          aria-hidden
          viewBox="0 0 400 400"
          className="pointer-events-none absolute bottom-[22px] left-[22px] w-[min(46cqw,520px)] overflow-visible fill-ink/55 font-mono text-[9px]/[normal] font-medium group-data-[plate=tall]/mat:hidden"
        >
          <path className="fill-none stroke-ink/26 stroke-1 [vector-effect:non-scaling-stroke]" d="M0 400 L400 169 M0 400 L400 0 M0 400 L231 0" />
          <text x="330" y="196">30°</text>
          <text x="330" y="58">45°</text>
          <text x="186" y="58">60°</text>
        </svg>

        {geometry && plate && (
          <>
            {/* The lamp's light on the mat, shadows and all, then the objects in it. */}
            <div
              aria-hidden
              className={`${LAID} inset-0 bg-no-repeat mix-blend-multiply`}
              style={{
                backgroundColor: plate.rim,
                backgroundImage: `url(/objects/mat/desk-${geometry.id}-light.avif)`,
                backgroundSize: `${(plate.size[0] + 2 * plate.bleed[0]) * geometry.em}px ${(plate.size[1] + 2 * plate.bleed[1]) * geometry.em}px`,
                backgroundPosition: `${geometry.x - plate.bleed[0] * geometry.em}px ${geometry.y - plate.bleed[1] * geometry.em}px`,
              }}
            />
            {/* Where the lamp lights the leather brighter than it was photographed, which multiplying cannot show,
                the rest of its light is added over it. */}
            <div
              aria-hidden
              className={`${LAID} inset-0 bg-no-repeat mix-blend-plus-lighter`}
              style={{
                backgroundImage: `url(/objects/mat/desk-${geometry.id}-light-past.avif)`,
                backgroundSize: `${(plate.size[0] + 2 * plate.bleed[0]) * geometry.em}px ${(plate.size[1] + 2 * plate.bleed[1]) * geometry.em}px`,
                backgroundPosition: `${geometry.x - plate.bleed[0] * geometry.em}px ${geometry.y - plate.bleed[1] * geometry.em}px`,
              }}
            />
            <img src={`/objects/mat/desk-${geometry.id}.avif`} alt="" draggable={false} className={LAID} style={over(geometry, 0, 0, ...plate.size)} />
            {/* The watch's dial again over the plate's, its hands at the viewer's time. */}
            {DIALS[geometry.id] && <WatchHands plate={geometry.id} em={geometry.em} className={LAID} style={over(geometry, ...DIALS[geometry.id]!.dial)} />}
            {/* The props seen from a camera of their own, over the plate where they stand on it. */}
            {Object.entries(PORTRAITS[geometry.id] ?? {}).map(([prop, seen]) => (
              <img
                key={prop}
                src={`/objects/mat/desk-${geometry.id}-${prop}.avif`}
                alt=""
                draggable={false}
                className={LAID}
                style={over(geometry, ...seen.picture)}
              />
            ))}
          </>
        )}

        {children}

      </div>
    </div>
  )
}
