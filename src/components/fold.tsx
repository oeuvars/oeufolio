import type { CSSProperties, ReactNode } from 'react'
import { useLayoutEffect, useRef } from 'react'

import type { FoldKind, FoldPiece } from '../types'
import fold from './fold.json'

const SIZES = fold.sizes as unknown as Record<string, [number, number]>
// The contact strip's pieces as a phone's band has them. The letter and the poster have none (FADE).
const PIECES = fold.contact as unknown as FoldPiece[]
// How far open the strip is when a piece goes over from the band's picture of itself to the page's, at once and in
// mid-flight, where it moves fastest. The two are two photographs of the contact set, from cameras a little apart, so
// faded one into the other they would show it twice, a little apart.
const TAKES_ON = 0.5
// The letter and the poster have no pieces: the folded picture fades out over the first part of the opening and the
// page fades in over the rest, overlapping in the middle.
const FADE = { band: [0, 0.6], page: [0.25, 1] }

const ramp = ([from, to]: number[], p: number) => {
  const t = Math.min(1, Math.max(0, (p - from) / (to - from)))
  return t * t * (3 - 2 * t)
}

/** Outlines in a picture's pixels as a path laid k pixels to one of them, from (x, y). */
const path = (clip: [number, number][][], k: number, x: number, y: number) =>
  clip.map((outline) => `M${outline.map(([px, py]) => `${((px - x) * k).toFixed(2)} ${((py - y) * k).toFixed(2)}`).join(' L')} Z`).join(' ')

const bounds = (clip: [number, number][][]) => {
  const xs = clip.flat().map(([x]) => x)
  const ys = clip.flat().map(([, y]) => y)
  return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)]
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
 * A folded strip growing into its page and back. Folded, the strip shows its band ([data-fold-band]), a picture of
 * its own made of pieces of its page (studio/fold.py); open, its page ([data-fold-page]). In between, as far as the
 * strip is open, each piece travels from where the band has it to where the page has it, turning and growing on the
 * way, over the rest of the page, which the strip uncovers as it opens, with each piece's place left empty. It goes as the strip goes, whether a spring or a finger moves it, and back the
 * same way. Only the contact strip has pieces. The card's band is its own page laid smaller, so the page itself goes there and back. The letter and the poster only fade from their
 * band to their page (FADE).
 */
export const Fold = ({ kind, open, folded, opened, style, children }: FoldProps) => {
  const layer = useRef<HTMLDivElement>(null)
  const pieces = kind === 'contact' ? PIECES : []
  // The poster's pieces are light, screened over the paper and over each other.
  const light = kind === 'poster'

  useLayoutEffect(() => {
    const root = layer.current
    const strip = root?.closest<HTMLElement>('section')
    if (!root || !strip) return
    const faces = [...root.querySelectorAll<HTMLElement>('[data-piece]')]
    const rest = root.querySelector<HTMLElement>('[data-fold-rest]')
    let laid: Array<{ from: [number, number]; to: [number, number]; grow: number; turn: number }> | null = null
    let badge: { from: [number, number]; to: [number, number]; grow: number } | null = null
    let was = ''
    let waiting = false

    const find = (inside: Element | null | undefined, src: string) => inside?.querySelector<HTMLElement>(`[src="${src}"], [data-src="${src}"]`)
    // Where a picture is drawn on the screen: its box, or within it, for one fitted into its box whole.
    const drawn = (element: HTMLElement, src: string) => {
      const box = element.getBoundingClientRect()
      if (getComputedStyle(element).objectFit !== 'contain') return { left: box.left, top: box.top, width: box.width }
      const [w, h] = SIZES[src]
      const k = Math.min(box.width / w, box.height / h)
      return { left: box.left + (box.width - w * k) / 2, top: box.top + (box.height - h * k) / 2, width: w * k }
    }

    // Where everything lies, measured once the strip starts to move: the band and the page both lie still on the
    // strip as it opens, from its edge, so they stay where they were measured.
    const measure = (band: HTMLElement | null, page: HTMLElement | null) => {
      const frame = root.getBoundingClientRect()
      if (kind === 'badge') {
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
      const next = []
      waiting = false
      for (const [n, piece] of pieces.entries()) {
        const bandImage = find(band, piece.band.src)
        const pageImage = find(page, piece.page.src)
        if (!bandImage || !pageImage) return false
        const b = drawn(bandImage, piece.band.src)
        const p = drawn(pageImage, piece.page.src)
        const kb = b.width / SIZES[piece.band.src][0]
        const kp = p.width / SIZES[piece.page.src][0]
        const from: [number, number] = [b.left - frame.left + piece.band.at[0] * kb, b.top - frame.top + piece.band.at[1] * kb]
        const to: [number, number] = [p.left - frame.left + piece.page.at[0] * kp, p.top - frame.top + piece.page.at[1] * kp]
        const grow = (piece.scale * kp) / kb
        const bandFace = faces[n].children[0] as HTMLCanvasElement
        const turning = faces[n].children[1] as HTMLElement
        const pageFace = turning.children[0] as HTMLCanvasElement
        // Each face is drawn on a canvas, cut from the picture as the strip already shows it, at the screen's own
        // pixels as large as it grows on its way, or as many as the picture has: a large picture laid again as a
        // background would be decoded afresh on every frame (paint).
        const lay = (face: HTMLCanvasElement, side: FoldPiece['band'], k: number, source: HTMLElement, largest: number) => {
          const [x0, y0, x1, y1] = bounds(side.clip)
          const drawn = source instanceof HTMLImageElement ? source.naturalWidth : (source as HTMLCanvasElement).width
          const ratio = Math.min((window.devicePixelRatio || 1) * largest, (drawn || 1) / (SIZES[side.src][0] * k))
          Object.assign(face.style, {
            left: `${(x0 - side.at[0]) * k}px`,
            top: `${(y0 - side.at[1]) * k}px`,
            width: `${(x1 - x0) * k}px`,
            height: `${(y1 - y0) * k}px`,
            clipPath: `path(evenodd, "${path(side.clip, k, x0, y0)}")`,
          })
          face.width = Math.max(1, Math.round((x1 - x0) * k * ratio))
          face.height = Math.max(1, Math.round((y1 - y0) * k * ratio))
          if (!drawn) return false
          const into = drawn / SIZES[side.src][0]
          face.getContext('2d')?.drawImage(source as CanvasImageSource, x0 * into, y0 * into, (x1 - x0) * into, (y1 - y0) * into, 0, 0, face.width, face.height)
          return true
        }
        // A picture not yet loaded is drawn again on the next frame.
        if (!lay(bandFace, piece.band, kb, bandImage, Math.max(1, grow)) || !lay(pageFace, piece.page, kp, pageImage, 1)) waiting = true
        // The page's picture of the piece is carried back by the piece's turn and growth, so the two meet where it lands.
        turning.style.transform = `rotate(${-piece.turn}deg) scale(${1 / grow})`
        next.push({ from, to, grow, turn: piece.turn })
      }
      laid = next
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
        if (moving) laid = badge = null
        was = state
      }
      if (moving && ((!laid && !badge) || waiting) && !measure(band, page)) return
      root.style.visibility = moving && kind !== 'badge' ? 'visible' : 'hidden'

      if (kind === 'badge') {
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

      if (kind === 'letter' || kind === 'poster') {
        if (band) {
          band.style.visibility = state === 'page' ? 'hidden' : 'visible'
          band.style.opacity = moving ? String(1 - ramp(FADE.band, p)) : ''
        }
        if (page) page.style.visibility = state === 'page' ? 'visible' : 'hidden'
        if (rest) rest.style.opacity = moving ? ramp(FADE.page, p).toFixed(3) : '1'
        return
      }
      if (band) band.style.visibility = state === 'band' ? 'visible' : 'hidden'
      if (page) page.style.visibility = state === 'page' ? 'visible' : 'hidden'
      if (!moving || !laid) return
      const takes = p >= TAKES_ON
      laid.forEach(({ from, to, grow, turn }, n) => {
        const face = faces[n]
        const x = from[0] + (to[0] - from[0]) * p
        const y = from[1] + (to[1] - from[1]) * p
        face.style.transform = `translate(${x}px, ${y}px) rotate(${turn * p}deg) scale(${grow ** p})`
        const bandFace = face.children[0] as HTMLElement
        const turning = face.children[1] as HTMLElement
        // The page's picture of the piece is laid over the band's as it settles, and the band's goes once it is covered.
        bandFace.style.opacity = takes ? '0' : '1'
        turning.style.opacity = takes ? '1' : '0'
      })
    }

    apply()
    const watching = new ResizeObserver(apply)
    watching.observe(strip)
    return () => watching.disconnect()
  }, [kind, open, folded, opened, pieces])

  return (
    // The poster's layer is light as a whole, screened over the paper under it: a layer of its own, its pieces screened
    // within it would only be screened over nothing.
    <div ref={layer} aria-hidden inert className={`pointer-events-none invisible z-2 overflow-hidden ${light ? 'mix-blend-screen' : ''}`} style={style}>
      {children && <div data-fold-rest className="absolute inset-0">{children}</div>}
      <div className="absolute inset-0">
        {pieces.map((_, n) => (
          // A piece moves as one layer of its own, so it is the piece that is screened, not its pictures.
          <div key={n} data-piece className={`absolute top-0 left-0 origin-top-left will-change-transform ${light ? 'mix-blend-screen' : ''}`}>
            <canvas className="absolute" />
            <div className="absolute top-0 left-0 origin-top-left">
              <canvas className="absolute" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
