import type { CSSProperties, ReactNode } from 'react'
import { useLayoutEffect, useRef } from 'react'

import type { FoldKind } from '../types'

// The letter and the poster have no pieces: the folded picture fades out over the first part of the opening and the
// page fades in over the rest, overlapping in the middle.
const FADE = { band: [0, 0.6], page: [0.25, 1] }

const ramp = ([from, to]: number[], p: number) => {
  const t = Math.min(1, Math.max(0, (p - from) / (to - from)))
  return t * t * (3 - 2 * t)
}

type FoldProps = {
  kind: FoldKind
  /** Whether the strip's page is the one open. */
  open: boolean
  /** How wide the strip is folded and open, in px: how far it is open is read off how wide it is. */
  folded: number
  opened: number
  /** Where the page lies on the strip, upright (SiteShell's uprightOf). */
  style: CSSProperties
  /** The page's picture, laid as the page lays it, to fade in: the letter's and the poster's, whose pages are only
   * there while they are open. */
  children?: ReactNode
}

/**
 * A folded strip growing into its page and back. Folded, the strip shows its band ([data-fold-band]); open, its page
 * ([data-fold-page]). In between it goes as far as the strip is open, whether a spring or a finger moves it, and back
 * the same way. The card's band is its own page laid smaller, so the page itself goes there and back. The letter and
 * the poster only fade from their band to their page (FADE).
 */
export const Fold = ({ kind, open, folded, opened, style, children }: FoldProps) => {
  const layer = useRef<HTMLDivElement>(null)
  // The poster's picture is light, screened over the paper.
  const light = kind === 'poster'

  useLayoutEffect(() => {
    const root = layer.current
    const strip = root?.closest<HTMLElement>('section')
    if (!root || !strip) return
    const rest = root.querySelector<HTMLElement>('[data-fold-rest]')
    let badge: { from: [number, number]; to: [number, number]; grow: number } | null = null
    let was = ''

    // Where the card lies on its band and on its page, measured once the strip starts to move: both lie still on the
    // strip as it opens, from its edge, so they stay where they were measured.
    const measure = (band: HTMLElement | null, page: HTMLElement | null) => {
      const inner = page?.querySelector<HTMLElement>('[data-page]')
      const there = band?.querySelector<HTMLElement>('[data-morph]')
      const here = inner?.querySelector<HTMLElement>('[data-morph]')
      if (!inner || !there || !here) return false
      inner.style.transform = ''
      const box = inner.getBoundingClientRect()
      const a = there.getBoundingClientRect()
      const b = here.getBoundingClientRect()
      // From the page's own top left, which lies still on the strip as the band does.
      badge = { from: [a.left - box.left, a.top - box.top], to: [b.left - box.left, b.top - box.top], grow: a.width / b.width }
      return true
    }

    const apply = () => {
      const p = Math.min(1, Math.max(0, (strip.offsetWidth - folded) / (opened - folded)))
      const band = strip.querySelector<HTMLElement>('[data-fold-band]')
      const page = strip.querySelector<HTMLElement>('[data-fold-page]')
      const state = p <= 0.001 && !open ? 'band' : p >= 0.999 && open ? 'page' : 'moving'
      const moving = state === 'moving'
      if (state !== was) {
        // Each time the strip starts to move it is measured again, for the window may have changed size since.
        if (moving) badge = null
        was = state
      }

      if (kind === 'badge') {
        if (moving && !badge && !measure(band, page)) return
        if (band) band.style.visibility = state === 'band' ? 'visible' : 'hidden'
        if (page) page.style.visibility = state === 'band' ? 'hidden' : 'visible'
        const inner = page?.querySelector<HTMLElement>('[data-page]')
        if (!inner) return
        if (!moving || !badge) {
          inner.style.transform = ''
          return
        }
        // The card's place on the screen goes straight from the band's to the page's, and it grows evenly.
        const grow = badge.grow ** (1 - p)
        const x = badge.from[0] + (badge.to[0] - badge.from[0]) * p - grow * badge.to[0]
        const y = badge.from[1] + (badge.to[1] - badge.from[1]) * p - grow * badge.to[1]
        inner.style.transform = `translateX(${x}px) translateY(${y}px) scale(${grow})`
        return
      }

      root.style.visibility = moving ? 'visible' : 'hidden'
      if (band) {
        band.style.visibility = state === 'page' ? 'hidden' : 'visible'
        band.style.opacity = moving ? String(1 - ramp(FADE.band, p)) : ''
      }
      if (page) page.style.visibility = state === 'page' ? 'visible' : 'hidden'
      if (rest) rest.style.opacity = moving ? ramp(FADE.page, p).toFixed(3) : '1'
    }

    apply()
    const watching = new ResizeObserver(apply)
    watching.observe(strip)
    return () => watching.disconnect()
  }, [kind, open, folded, opened])

  return (
    <div ref={layer} aria-hidden inert className={`pointer-events-none invisible z-2 overflow-hidden ${light ? 'mix-blend-screen' : ''}`} style={style}>
      {children && <div data-fold-rest className="absolute inset-0">{children}</div>}
    </div>
  )
}
