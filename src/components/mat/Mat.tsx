import { useEffect, useRef, useState } from 'react'

import { cn } from '../../lib/utils'
import type { MatLayout, PropId, Size } from '../../types'
import { PendantLamp } from './PendantLamp'
import { Rulers } from './Rulers'
import { REF_HEIGHT, REF_WIDTH, mulberry, stacked, strewn } from './layout'
import { atKolkataMinute, lightAt } from './sun'

type MatProps = {
  /** The objects on the mat. Each marks its root with data-prop. */
  children: React.ReactNode
  className?: string
}

type Held = {
  el: HTMLElement
  dx: number
  dy: number
  x: number
  y: number
  r: number
  vx: number
  moved: number
}

// A mat narrower than this stacks its objects in rows, sized for a mat NARROW wide.
const WIDE_FROM = 420
const NARROW = 520
const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value))

// Light falls on the mat in layers above the objects. LIGHT covers the whole mat.
const LAYER = 'pointer-events-none absolute z-940'
const LIGHT = `${LAYER} inset-0 transition-opacity duration-500`
// Where the bulb hangs in the lamp's box, as fractions of it.
const BULB = { x: 0.5, y: 0.726 }

/**
 * A cutting mat in yellow leather, seen from overhead, with the objects left on it as on a desk in use. It
 * fills what it is put in, and the objects are sized so that all of them show at once. A mat too narrow for
 * that stacks them in rows and runs as long as they need. A mouse can drag them. The light is the sun over
 * Kolkata at the current minute, and after dark the lamp in the corner.
 */
export function Mat({ children, className }: MatProps) {
  const [lit, setLit] = useState(false)
  const root = useRef<HTMLDivElement>(null)
  const sheet = useRef<HTMLDivElement>(null)
  // The effect below reads the switch from here and leaves its own shading here, to be done over when it flips.
  const switched = useRef(lit)
  const reshade = useRef(() => {})

  useEffect(() => {
    const frame = root.current
    const board = sheet.current
    if (!frame || !board) return
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches
    const fine = matchMedia('(pointer: fine)')
    const pieces = new Map<PropId, HTMLElement>()
    board.querySelectorAll<HTMLElement>('[data-prop]').forEach((el) => pieces.set(el.dataset.prop as PropId, el))

    // ?minute=780 holds the mat at that minute of the Kolkata day, to look at it in another light.
    const pinned = new URLSearchParams(window.location.search).get('minute')
    const sunlight = () => lightAt(pinned === null ? new Date() : atKolkataMinute(new Date(), Number(pinned)))

    // Daylight comes from the sun over Kolkata. After dark the mat is as bright as the lamp makes it.
    let light = sunlight()
    let scale = 1
    const fixture = frame.querySelector<HTMLElement>('[data-lamp]')!
    const shade = () => {
      const vars = frame.style
      // The lamp stays in the corner of the frame, so its place on the mat moves as the mat scrolls under it.
      const outer = board.getBoundingClientRect()
      const box = fixture.getBoundingClientRect()
      const lamp = { x: box.left - outer.left + box.width * BULB.x, y: box.top - outer.top + box.height * BULB.y }
      const night = light.day < 0.5
      vars.setProperty('--day', light.day.toFixed(3))
      vars.setProperty('--warmth', light.warmth.toFixed(3))
      vars.setProperty('--shx', (light.dx * light.reach).toFixed(1))
      vars.setProperty('--shy', (light.dy * light.reach).toFixed(1))
      vars.setProperty('--shb', (2 + light.reach * 0.2).toFixed(1))
      // A dark room has no light to throw a shadow with.
      vars.setProperty('--sha', night ? '0.14' : '0.36')
      vars.setProperty('--glow-turn', light.dx > 0 ? '270' : '90')
      vars.setProperty('--lx', `${lamp.x.toFixed(0)}px`)
      vars.setProperty('--ly', `${lamp.y.toFixed(0)}px`)
      vars.setProperty('--lit', switched.current ? '1' : '0')
      const lampLit = night && switched.current
      for (const el of pieces.values()) {
        if (!lampLit) {
          for (const name of ['--shx', '--shy', '--shb', '--sha']) el.style.removeProperty(name)
          continue
        }
        const dx = Number(el.style.getPropertyValue('--x')) - lamp.x
        const dy = Number(el.style.getPropertyValue('--y')) - lamp.y
        const distance = Math.hypot(dx, dy) || 1
        // The shadows are drawn at the mat's scale, so the distance is taken at the mat's full size.
        const reach = clamp((distance / scale) * 0.07, 3, 44)
        el.style.setProperty('--shx', ((dx / distance) * reach).toFixed(1))
        el.style.setProperty('--shy', ((dy / distance) * reach).toFixed(1))
        el.style.setProperty('--shb', (2 + reach * 0.24).toFixed(1))
        el.style.setProperty('--sha', '0.5')
      }
    }
    reshade.current = shade

    const random = mulberry(Date.now())
    let stack = pieces.size

    const put = (el: HTMLElement, x: number, y: number, r: number) => {
      el.style.setProperty('--x', x.toFixed(1))
      el.style.setProperty('--y', y.toFixed(1))
      el.style.setProperty('--r', r.toFixed(2))
    }

    const place = (layout: MatLayout, stagger: boolean) => {
      let i = 0
      for (const [id, el] of pieces) {
        const slot = layout[id]
        if (!slot) continue
        el.style.transitionDelay = stagger ? `${i * 55}ms` : '0ms'
        put(el, slot.x, slot.y, slot.r)
        i += 1
      }
      shade()
    }

    const compose = (): MatLayout => {
      const width = board.clientWidth
      const wide = width >= WIDE_FROM
      frame.dataset.stacked = String(!wide)
      // Strewn, the mat is as tall as its frame and no taller, and the objects are as large as lets all of them show.
      if (wide) board.style.minHeight = ''
      const height = board.clientHeight
      scale = wide ? Math.min(width / REF_WIDTH, height / REF_HEIGHT, 1.7) : Math.min(width / NARROW, 1)
      frame.style.setProperty('--s', scale.toFixed(3))
      if (wide) return strewn(width, height)
      const sizes = new Map<PropId, Size>()
      for (const [id, el] of pieces) sizes.set(id, { w: el.offsetWidth, h: el.offsetHeight })
      const rows = stacked(sizes, width, 26 * scale, 64)
      board.style.minHeight = `${rows.height + 90}px`
      return rows.layout
    }

    // Deal the objects in from above the mat, then let them settle.
    const first = compose()
    for (const [id, el] of pieces) {
      const slot = first[id]!
      if (reduced) put(el, slot.x, slot.y, slot.r)
      else put(el, slot.x + (random() - 0.5) * 240, -260 - random() * 200, (random() - 0.5) * 70)
    }
    // The objects are renders. Hold the deal until they have loaded, or two seconds, whichever is first.
    const renders = new Set<string>()
    board.querySelectorAll<HTMLElement>('[data-prop], [data-prop] *').forEach((el) => {
      for (const [, url] of getComputedStyle(el).backgroundImage.matchAll(/url\("([^"]+)"\)/g)) renders.add(url)
    })
    const loaded = [...renders].map((url) => {
      const image = new Image()
      image.src = url
      return image.decode().catch(() => undefined)
    })
    let dealt = false
    let gone = false
    const deal = () => {
      if (dealt || gone) return
      dealt = true
      requestAnimationFrame(() =>
        requestAnimationFrame(() => {
          if (gone) return
          frame.dataset.ready = 'true'
          // The frame may have found its width since the objects were held above it.
          place(compose(), !reduced)
        }),
      )
    }
    Promise.all(loaded).then(deal)
    const dealing = window.setTimeout(deal, 2000)

    const ticking = window.setInterval(() => {
      light = sunlight()
      shade()
    }, 30_000)

    let scrolling = 0
    const onScroll = () => {
      if (scrolling) return
      scrolling = requestAnimationFrame(() => {
        scrolling = 0
        shade()
      })
    }

    let held: Held | null = null

    const point = (event: PointerEvent) => {
      const box = board.getBoundingClientRect()
      return { x: event.clientX - box.left, y: event.clientY - box.top }
    }

    const onDown = (event: PointerEvent) => {
      if (!fine.matches || event.button !== 0) return
      const el = (event.target as HTMLElement).closest<HTMLElement>('[data-prop]')
      if (!el) return
      const at = point(event)
      const x = Number(el.style.getPropertyValue('--x'))
      const y = Number(el.style.getPropertyValue('--y'))
      const r = Number(el.style.getPropertyValue('--r'))
      held = { el, dx: at.x - x, dy: at.y - y, x, y, r, vx: 0, moved: 0 }
      stack += 1
      el.style.zIndex = String(stack)
      el.style.transitionDelay = '0ms'
      el.dataset.held = 'true'
      el.setPointerCapture(event.pointerId)
    }

    const onMove = (event: PointerEvent) => {
      if (!held) return
      const at = point(event)
      const x = clamp(at.x - held.dx, 24, board.clientWidth - 24)
      const y = clamp(at.y - held.dy, 24, board.clientHeight - 24)
      held.moved += Math.abs(x - held.x) + Math.abs(y - held.y)
      held.vx = held.vx * 0.7 + (x - held.x) * 0.3
      held.x = x
      held.y = y
      put(held.el, x, y, held.r + clamp(held.vx * 0.5, -9, 9))
      shade()
    }

    const onUp = (event: PointerEvent) => {
      if (!held) return
      const { el, x, y, r, vx, moved } = held
      held = null
      delete el.dataset.held
      if (el.hasPointerCapture(event.pointerId)) el.releasePointerCapture(event.pointerId)
      if (moved < 5) return
      // A drag ends with a short glide and must not also follow a link.
      put(el, clamp(x + clamp(vx * 4, -60, 60), 24, board.clientWidth - 24), y, r + clamp(vx * 0.35, -6, 6))
      const swallow = (click: MouseEvent) => {
        click.preventDefault()
        click.stopPropagation()
      }
      el.addEventListener('click', swallow, { capture: true, once: true })
      window.setTimeout(() => el.removeEventListener('click', swallow, { capture: true }), 0)
    }

    // An object the pointer brushes finishes its move. data-linger is how long the move takes in milliseconds,
    // and the hover holds that long from the moment the pointer arrives, however soon it leaves.
    const lingering = new Map<HTMLElement, { since: number; leaving: number }>()
    const brushed = (event: PointerEvent) => {
      const el = (event.target as Element).closest<HTMLElement>('[data-linger]')
      return el && !el.contains(event.relatedTarget as Node | null) ? el : null
    }
    const onOver = (event: PointerEvent) => {
      const el = brushed(event)
      if (!el) return
      const stay = lingering.get(el)
      window.clearTimeout(stay?.leaving)
      lingering.set(el, { since: stay?.since ?? performance.now(), leaving: 0 })
      el.dataset.lingering = 'true'
    }
    const onOut = (event: PointerEvent) => {
      const el = brushed(event)
      const stay = el && lingering.get(el)
      if (!el || !stay) return
      stay.leaving = window.setTimeout(
        () => {
          lingering.delete(el)
          delete el.dataset.lingering
        },
        Math.max(0, Number(el.dataset.linger) - (performance.now() - stay.since)),
      )
    }

    // The frame changes size with the window, and once more when the page it is in has measured itself.
    let resizing = 0
    const onResize = () => {
      window.clearTimeout(resizing)
      resizing = window.setTimeout(() => {
        if (frame.dataset.ready) place(compose(), false)
      }, 120)
    }
    const watching = new ResizeObserver(onResize)
    watching.observe(frame)

    // Whatever the mat scrolls in, its scrolling is caught on the way down from the window.
    window.addEventListener('scroll', onScroll, { passive: true, capture: true })
    window.addEventListener('resize', onResize)
    board.addEventListener('pointerdown', onDown)
    board.addEventListener('pointermove', onMove)
    board.addEventListener('pointerup', onUp)
    board.addEventListener('pointercancel', onUp)
    board.addEventListener('pointerover', onOver)
    board.addEventListener('pointerout', onOut)

    return () => {
      gone = true
      watching.disconnect()
      window.clearTimeout(resizing)
      window.clearTimeout(dealing)
      window.clearInterval(ticking)
      cancelAnimationFrame(scrolling)
      for (const stay of lingering.values()) window.clearTimeout(stay.leaving)
      window.removeEventListener('scroll', onScroll, { capture: true })
      window.removeEventListener('resize', onResize)
      board.removeEventListener('pointerdown', onDown)
      board.removeEventListener('pointermove', onMove)
      board.removeEventListener('pointerup', onUp)
      board.removeEventListener('pointercancel', onUp)
      board.removeEventListener('pointerover', onOver)
      board.removeEventListener('pointerout', onOut)
    }
  }, [])

  useEffect(() => {
    switched.current = lit
    reshade.current()
  }, [lit])

  return (
    <div
      ref={root}
      className={cn(
        'group/mat mat @container relative isolate flex flex-col [--day:1] [--lit:0] [--lx:80%] [--ly:16%] [--s:1] [--sha:0.34] [--shb:7] [--shx:0] [--shy:7] [--warmth:0]',
        className,
      )}
    >
      {/* The lamp hangs from the top of whatever the mat scrolls in, and the mat goes by under it. */}
      <div className="sticky top-0 z-945 h-0">
        <PendantLamp lit={lit} onPull={() => setLit(!lit)} />
      </div>

      <div
        ref={sheet}
        className="relative flex-1 overflow-hidden select-none before:pointer-events-none before:absolute before:inset-0 before:bg-mat-grain before:bg-size-[220px_220px] before:opacity-20 before:mix-blend-multiply"
      >
        <Rulers />
        <svg
          aria-hidden
          viewBox="0 0 400 400"
          className="pointer-events-none absolute bottom-[22px] left-[22px] w-[min(46cqw,520px)] overflow-visible fill-ink/55 font-mono text-[9px]/[normal] font-medium stacked:hidden"
        >
          <path className="fill-none stroke-ink/26 stroke-1 [vector-effect:non-scaling-stroke]" d="M0 400 L400 169 M0 400 L400 0 M0 400 L231 0" />
          <text x="330" y="196">30°</text>
          <text x="330" y="58">45°</text>
          <text x="186" y="58">60°</text>
        </svg>

        {children}

        {/* The hour: gold near dusk and dark at night. Then the lamp: its pool of light in the dark, and its glow. */}
        <div aria-hidden className={`${LIGHT} bg-golden opacity-[calc(var(--warmth)*0.5)] mix-blend-multiply`} />
        <div aria-hidden className={`${LIGHT} bg-[rgb(10_14_40)] opacity-[calc((1-var(--day))*(1-var(--lit))*0.8)] mix-blend-multiply`} />
        <div aria-hidden className={`${LIGHT} bg-room opacity-[calc((1-var(--day))*var(--lit))] mix-blend-multiply`} />
        <div aria-hidden className={`${LIGHT} bg-glow opacity-[calc(var(--lit)*(1-0.6*var(--day)))] mix-blend-screen`} />
      </div>
    </div>
  )
}
