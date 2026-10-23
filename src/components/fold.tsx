import type { CSSProperties, ReactNode } from 'react'
import { useLayoutEffect, useRef } from 'react'

import type { FoldKind, FoldPiece } from '../types'
import fold from './fold.json'

/** Where the poster band's layers lie in its middle (studio/fold.py), in its pixels: the sign's two words over the
 * windows behind them. */
export const POSTER_SIGN = fold.layers.poster as unknown as Record<'size', [number, number]> & Record<'behind' | 'human' | 'experience', [number, number, number, number]>

const SIZES = fold.sizes as unknown as Record<string, [number, number]>
const PIECES = {
  letter: fold.letter,
  poster: fold.poster,
  desk: fold.desk,
  contact: fold.contact,
} as unknown as Record<Exclude<FoldKind, 'badge'>, FoldPiece[]>
// The page's picture under the pieces, which keeps a hole where each piece lands until it is there.
const PAGE_SRC: Partial<Record<FoldKind, string>> = { letter: '/objects/letter.avif', poster: '/objects/poster.avif', desk: '/objects/mat/desk-wide.avif' }
// How far open the strip is when a piece has taken on the page's picture of itself, from and to, and when the rest of
// the page has come in. A piece keeps the band's look until it is most of the way to its place.
const TAKES_ON = [0.45, 0.92]
const REST_IN = [0.12, 0.8]
// The desk's band is its mat in the band's light, which goes over to the page's mat in its own by then.
const LIGHT_GOES = 0.7
// The page's light has the things' shadows and the dark under them in it, so it takes over from the light without them
// (bare_light in studio/fold.py) only as they settle onto the mat.
const SHADOWS_IN = [0.88, 1]

const ramp = ([from, to]: number[], p: number) => {
  const t = Math.min(1, Math.max(0, (p - from) / (to - from)))
  return t * t * (3 - 2 * t)
}

/** Outlines in a picture's pixels as a path laid k pixels to one of them, from (x, y). */
const path = (clip: [number, number][][], k: number, x: number, y: number) =>
  clip.map((outline) => `M${outline.map(([px, py]) => `${((px - x) * k).toFixed(2)} ${((py - y) * k).toFixed(2)}`).join(' L')} Z`).join(' ')

/** A picture's mask with a hole where each piece lands on it, black on white: it masks by luminance. */
const holes = (src: string, pieces: FoldPiece[]) => {
  const [w, h] = SIZES[src]
  const cut = pieces.map((piece) => `<path fill-rule="evenodd" d="${path(piece.page.clip, 1, 0, 0)}"/>`).join('')
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><rect width="${w}" height="${h}" fill="#fff"/><g fill="#000">${cut}</g></svg>`
  return `url("data:image/svg+xml,${encodeURIComponent(svg)}")`
}

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
  /** The page's picture, laid as the page lays it, for the pieces to land in: the letter's and the poster's, whose
   * pages are only there while they are open. */
  children?: ReactNode
}

/**
 * A folded phone strip growing into its page and back. Folded, the strip shows its band ([data-fold-band]), a picture
 * of its own made of pieces of its page set in a row (studio/fold.py); open, its page ([data-fold-page]). In between,
 * as far as the strip is open, each piece travels from where the band has it to where the page has it, turning and
 * growing on the way, and takes on the page's picture of itself as it nears it, while the rest of the page comes in
 * round it. It goes as the strip goes, whether a spring or a finger moves it, and back the same way. The card's band is
 * its own page laid smaller, so the page itself goes there and back.
 */
export const Fold = ({ kind, open, folded, opened, style, children }: FoldProps) => {
  const layer = useRef<HTMLDivElement>(null)
  const pieces = kind === 'badge' ? [] : PIECES[kind]
  // The poster's pieces are light, screened over the paper and over each other. The letter's are ink with nothing
  // round it, so the band's picture of each goes as the page's comes; the others' pictures are opaque, and the page's
  // lies over the band's until it covers it.
  const light = kind === 'poster'
  const crossing = kind === 'letter'

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
    const desk = kind === 'desk' ? holes(PAGE_SRC.desk!, pieces) : ''

    const find = (inside: Element | null | undefined, src: string) => inside?.querySelector<HTMLElement>(`[src="${src}"], [data-src="${src}"]`)

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
        const pageImage = find(kind === 'letter' || kind === 'poster' ? rest : page, piece.page.src)
        if (!bandImage || !pageImage) return false
        const b = bandImage.getBoundingClientRect()
        const p = pageImage.getBoundingClientRect()
        const kb = b.width / SIZES[piece.band.src][0]
        const kp = p.width / SIZES[piece.page.src][0]
        const from: [number, number] = [b.left - frame.left + piece.band.at[0] * kb, b.top - frame.top + piece.band.at[1] * kb]
        const to: [number, number] = [p.left - frame.left + piece.page.at[0] * kp, p.top - frame.top + piece.page.at[1] * kp]
        const grow = (piece.scale * kp) / kb
        const bandFace = faces[n].children[0] as HTMLCanvasElement
        const turning = faces[n].children[1] as HTMLElement
        const pageFace = turning.children[0] as HTMLCanvasElement
        // Each face is drawn on a canvas, cut from the picture as the strip already shows it, at the screen's own
        // pixels: a large picture laid again as a background would be decoded afresh on every frame (paint).
        const lay = (face: HTMLCanvasElement, side: FoldPiece['band'], k: number, source: HTMLElement) => {
          const [x0, y0, x1, y1] = bounds(side.clip)
          const drawn = source instanceof HTMLImageElement ? source.naturalWidth : (source as HTMLCanvasElement).width
          const ratio = window.devicePixelRatio || 1
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
        if (!lay(bandFace, piece.band, kb, bandImage) || !lay(pageFace, piece.page, kp, pageImage)) waiting = true
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
        // The mat lays its tabs' light off where it lies on the screen, so it is laid again once its page has settled.
        else if (was) window.dispatchEvent(new Event('scroll'))
        was = state
      }
      if (moving && ((!laid && !badge) || waiting) && !measure(band, page)) return
      root.style.visibility = moving && kind !== 'badge' ? 'visible' : 'hidden'
      const restIn = ramp(REST_IN, p)

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

      if (kind === 'desk') {
        // The page's mat lies under the band's, in its own light, its things coming in round the pieces; the band's
        // mat goes, and its things are the pieces.
        if (band) {
          band.style.visibility = state === 'page' ? 'hidden' : 'visible'
          band.style.opacity = moving ? String(1 - ramp([0, LIGHT_GOES], p)) : ''
          band.style.zIndex = moving ? '1' : ''
          // Its things have left it, so it is lit as it is without them.
          band.style.setProperty('--fold-takes', moving ? '0' : '1')
          const plate = find(band, '/objects/mat/desk-band.avif')
          if (plate) plate.style.visibility = moving ? 'hidden' : ''
        }
        if (page) {
          page.style.visibility = state === 'band' ? 'hidden' : 'visible'
          page.style.setProperty('--fold-rest', moving ? restIn.toFixed(3) : '1')
          page.style.setProperty('--fold-holes', moving ? desk : 'none')
          // The lamp's light on the mat is the light without the pieces until they land (bare_light in studio/fold.py).
          page.style.setProperty('--fold-takes', moving ? ramp(SHADOWS_IN, p).toFixed(3) : '1')
        }
      } else {
        if (band) band.style.visibility = state === 'band' ? 'visible' : 'hidden'
        if (page) page.style.visibility = state === 'page' ? 'visible' : 'hidden'
      }
      if (rest) rest.style.opacity = restIn.toFixed(3)

      if (!moving || !laid) return
      const takes = ramp(TAKES_ON, p)
      laid.forEach(({ from, to, grow, turn }, n) => {
        const face = faces[n]
        const x = from[0] + (to[0] - from[0]) * p
        const y = from[1] + (to[1] - from[1]) * p
        face.style.transform = `translate(${x}px, ${y}px) rotate(${turn * p}deg) scale(${grow ** p})`
        const bandFace = face.children[0] as HTMLElement
        const turning = face.children[1] as HTMLElement
        bandFace.style.opacity = crossing ? String(1 - takes) : takes >= 1 ? '0' : '1'
        turning.style.opacity = String(takes)
      })
    }

    // The page's picture keeps a hole where each piece lands, while they are on their way.
    const picture = rest && PAGE_SRC[kind] ? find(rest, PAGE_SRC[kind]!) : null
    if (picture) {
      picture.style.maskImage = holes(PAGE_SRC[kind]!, pieces)
      picture.style.maskSize = '100% 100%'
      picture.style.maskMode = 'luminance'
    }

    apply()
    const watching = new ResizeObserver(apply)
    watching.observe(strip)
    return () => watching.disconnect()
  }, [kind, open, folded, opened, pieces, crossing])

  return (
    <div ref={layer} aria-hidden inert className="pointer-events-none invisible z-2 overflow-hidden" style={style}>
      {children && <div data-fold-rest className="absolute inset-0">{children}</div>}
      <div className={`absolute inset-0 ${light ? 'mix-blend-screen' : ''}`}>
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
