import { useLayoutEffect, useRef, useState, useSyncExternalStore } from 'react'

import { cn } from '../../lib/utils'
import type { PlateId, PropId } from '../../types'
import { PendantLamp } from './PendantLamp'
import { Rulers } from './Rulers'
import { lamp } from './lamp'
import { BULB, PLATES } from './layout'
import { atKolkataMinute, lightAt } from './sun'

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
// Layers of light over the mat, the plate and what is on it.
const LIGHT = 'pointer-events-none absolute inset-0 z-940 transition-opacity duration-500'
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
 * The light is the sun over Kolkata at the current minute. After dark the mat goes dark unless the lamp in the
 * corner is on, and then it is lit by a second plate of the same set under the lamp alone: the objects, and a
 * map of the lamp's light that the leather, its rules and its rulers are multiplied by.
 */
export function Mat({ children, className }: MatProps) {
  // The lamp only shows once the sun is down.
  const lit = useSyncExternalStore(lamp.subscribe, lamp.isOn, lamp.isOn)
  const [geometry, setGeometry] = useState<Geometry | null>(null)
  const root = useRef<HTMLDivElement>(null)
  const sheet = useRef<HTMLDivElement>(null)

  // The desk is laid and lit before it is first painted: the folded strip and the page swap copies of it
  // mid-slide, and neither may show a bare mat.
  // The hour, and whether it is dark.
  useLayoutEffect(() => {
    const frame = root.current
    if (!frame) return
    // ?minute=780 holds the mat at that minute of the Kolkata day, to look at it in another light.
    const pinned = new URLSearchParams(window.location.search).get('minute')
    const shade = () => {
      const light = lightAt(pinned === null ? new Date() : atKolkataMinute(new Date(), Number(pinned)))
      frame.style.setProperty('--day', light.day.toFixed(3))
      frame.style.setProperty('--warmth', light.warmth.toFixed(3))
    }
    shade()
    const ticking = window.setInterval(shade, 30_000)
    return () => window.clearInterval(ticking)
  }, [])

  // The plate fits the mat, and the objects' boxes follow it.
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
  // the hour, the lamp, and the lamp's map laid where it lies over the mat.
  useLayoutEffect(() => {
    const frame = root.current
    const board = sheet.current
    const tab = document.querySelector<HTMLElement>('[data-mat-light]')
    if (!frame || !board || !tab || !geometry) return
    const plate = PLATES[geometry.id]
    const [w, h] = plate.size
    const [bx, by] = plate.bleed
    const { em } = geometry
    const hour = () => {
      tab.style.setProperty('--day', frame.style.getPropertyValue('--day'))
      tab.style.setProperty('--warmth', frame.style.getPropertyValue('--warmth'))
    }
    const place = () => {
      const mat = board.getBoundingClientRect()
      const at = tab.getBoundingClientRect()
      tab.style.setProperty('--light-at', `${mat.left - at.left + geometry.x - bx * em}px ${mat.top - at.top + geometry.y - by * em}px`)
    }
    tab.style.setProperty('--lit', lit ? '1' : '0')
    tab.style.setProperty('--light-rim', plate.rim)
    tab.style.setProperty('--light-image', `url(/objects/mat/desk-${geometry.id}-light.avif)`)
    tab.style.setProperty('--light-size', `${(w + 2 * bx) * em}px ${(h + 2 * by) * em}px`)
    hour()
    place()
    const ticking = new MutationObserver(hour)
    ticking.observe(frame, { attributes: true, attributeFilter: ['style'] })
    // The strip slides open after the mat is laid, and the page scrolls under the tab.
    const moving = new ResizeObserver(place)
    moving.observe(board)
    const strip = tab.closest('section')
    if (strip) moving.observe(strip)
    window.addEventListener('scroll', place, true)
    return () => {
      ticking.disconnect()
      moving.disconnect()
      window.removeEventListener('scroll', place, true)
      for (const name of ['--day', '--warmth', '--lit', '--light-rim', '--light-image', '--light-size', '--light-at']) tab.style.removeProperty(name)
    }
  }, [geometry, lit])

  const plate = geometry && PLATES[geometry.id]

  return (
    <div
      ref={root}
      data-lit={lit}
      data-plate={geometry?.id}
      className={cn(
        'group/mat mat @container relative isolate flex flex-col [--day:1] [--lamp:calc(var(--lit)*(1-var(--day)))] [--lit:0] [--s:1] [--warmth:0] data-[lit=true]:[--lit:1]',
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
            {/* By day: the objects and the shadows they throw on the mat. */}
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

        {/* The hour: gold near dusk, and dark at night with the lamp off. */}
        <div aria-hidden className={`${LIGHT} bg-golden opacity-[calc(var(--warmth)*0.5)] mix-blend-multiply`} />
        <div aria-hidden className={`${LIGHT} bg-[rgb(10_14_24)] opacity-[calc((1-var(--day))*(1-var(--lit))*0.82)] mix-blend-multiply`} />

        {geometry && plate && (
          <div
            className="absolute z-945"
            style={{
              left: geometry.x + plate.lamp[0] * geometry.em - BULB.x * plate.lampSize * geometry.em,
              top: geometry.y + plate.lamp[1] * geometry.em - BULB.y * plate.lampSize * geometry.em,
              fontSize: plate.lampSize * geometry.em,
            }}
          >
            <PendantLamp lit={lit} onPull={lamp.pull} />
          </div>
        )}
      </div>
    </div>
  )
}
