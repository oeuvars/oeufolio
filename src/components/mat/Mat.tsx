import { useLayoutEffect, useRef, useState, useSyncExternalStore } from 'react'

import { cn } from '../../lib/utils'
import type { PlateId, PropId } from '../../types'
import { Rulers } from './Rulers'
import { lamp } from './lamp'
import { PLATES } from './layout'

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
// The plates and the lamp's light lie over the rulers, which are printed on the mat under everything on it.
const FADE = 'pointer-events-none absolute z-1 max-w-none transition-opacity duration-500'

/** Where a rectangle of the plate, given in its em, lies on the mat. */
function over(geometry: Geometry, x: number, y: number, w: number, h: number): React.CSSProperties {
  const { em } = geometry
  return { left: geometry.x + x * em, top: geometry.y + y * em, width: w * em, height: h * em }
}

/**
 * A cutting mat in teal leather, seen from overhead, with the things left on it as on a desk in use. All of
 * it is one photograph of one set, rendered in the studio under one light, so every object shades the others
 * and throws its own shadow. The page lays the plate over its own leather, as large as lets all of it show.
 * The room is dimly lit, and on the desk stands a lamp, a porcelain cat holding an orange dome up on its tail. Each state of
 * the lamp is its own plate of the same set: the objects in that light, and the light on the mat, which the
 * leather, its rules and its rulers are multiplied by: a map of the lamp's light with it on, the room's even
 * dimness with it off. Clicking the lamp switches it.
 */
export function Mat({ children, className }: MatProps) {
  const lit = useSyncExternalStore(lamp.subscribe, lamp.isOn, lamp.isOn)
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
        // The wide plate keeps to the top of the mat, so the lamp over it hangs from the top of the frame.
        em = Math.min(width / w, board.clientHeight / h, LARGEST)
        x = (width - w * em) / 2
      } else {
        em = width / w
        board.style.minHeight = `${Math.ceil(h * em)}px`
      }
      frame.style.setProperty('--s', (em / 16).toFixed(4))
      board.querySelectorAll<HTMLElement>('[data-prop]').forEach((el) => {
        const at = plate.at[el.dataset.prop as PropId]
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

  // The folder tab the page hangs from is cut from this leather (SiteShell's Tab), so it takes the same light:
  // the lamp, and the lamp's map laid where it lies over the mat.
  useLayoutEffect(() => {
    const frame = root.current
    const board = sheet.current
    const tab = document.querySelector<HTMLElement>('[data-mat-light]')
    if (!frame || !board || !tab || !geometry) return
    const plate = PLATES[geometry.id]
    const [w, h] = plate.size
    const [bx, by] = plate.bleed
    const { em } = geometry
    const place = () => {
      const mat = board.getBoundingClientRect()
      const at = tab.getBoundingClientRect()
      tab.style.setProperty('--light-at', `${mat.left - at.left + geometry.x - bx * em}px ${mat.top - at.top + geometry.y - by * em}px`)
    }
    tab.style.setProperty('--lit', lit ? '1' : '0')
    tab.style.setProperty('--light-rim', plate.rim)
    tab.style.setProperty('--light-dark', plate.dark)
    tab.style.setProperty('--light-image', `url(/objects/mat/desk-${geometry.id}-light.avif)`)
    tab.style.setProperty('--light-size', `${(w + 2 * bx) * em}px ${(h + 2 * by) * em}px`)
    place()
    // The strip slides open after the mat is laid, and the page scrolls under the tab.
    const moving = new ResizeObserver(place)
    moving.observe(board)
    const strip = tab.closest('section')
    if (strip) moving.observe(strip)
    window.addEventListener('scroll', place, true)
    return () => {
      moving.disconnect()
      window.removeEventListener('scroll', place, true)
      for (const name of ['--lit', '--light-rim', '--light-dark', '--light-image', '--light-size', '--light-at']) tab.style.removeProperty(name)
    }
  }, [geometry, lit])

  const plate = geometry && PLATES[geometry.id]

  return (
    <div
      ref={root}
      data-lit={lit}
      data-plate={geometry?.id}
      className={cn(
        'group/mat mat @container relative isolate flex flex-col [--lamp:var(--lit)] [--lit:0] [--s:1] data-[lit=true]:[--lit:1]',
        className,
      )}
    >
      <div
        ref={sheet}
        className="relative flex-1 overflow-hidden select-none before:pointer-events-none before:absolute before:inset-0 before:bg-mat-grain before:bg-size-[220px_220px] before:opacity-20 before:mix-blend-multiply"
      >
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
            {/* The lamp off: the room's dim light on the mat, then the objects in it and the shadows they throw. */}
            <div aria-hidden className={`${FADE} inset-0 opacity-[calc(1-var(--lamp))] mix-blend-multiply`} style={{ backgroundColor: plate.dark }} />
            <img
              src={`/objects/mat/desk-${geometry.id}.avif`}
              alt=""
              draggable={false}
              className={`${FADE} opacity-[calc(1-var(--lamp))]`}
              style={over(geometry, 0, 0, ...plate.size)}
            />
            {/* By the lamp: its light on the mat, shadows and all, then the objects in it. */}
            <div
              aria-hidden
              className={`${FADE} inset-0 bg-no-repeat opacity-[var(--lamp)] mix-blend-multiply`}
              style={{
                backgroundColor: plate.rim,
                backgroundImage: `url(/objects/mat/desk-${geometry.id}-light.avif)`,
                backgroundSize: `${(plate.size[0] + 2 * plate.bleed[0]) * geometry.em}px ${(plate.size[1] + 2 * plate.bleed[1]) * geometry.em}px`,
                backgroundPosition: `${geometry.x - plate.bleed[0] * geometry.em}px ${geometry.y - plate.bleed[1] * geometry.em}px`,
              }}
            />
            <img
              src={`/objects/mat/desk-${geometry.id}-lamp.avif`}
              alt=""
              draggable={false}
              className={`${FADE} opacity-[var(--lamp)]`}
              style={over(geometry, 0, 0, ...plate.size)}
            />
          </>
        )}

        {children}

      </div>
    </div>
  )
}
