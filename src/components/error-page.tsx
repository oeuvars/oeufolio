import { Link, useRouter } from '@tanstack/react-router'
import type { ErrorComponentProps } from '@tanstack/react-router'
import type { CSSProperties, ReactNode } from 'react'
import { createContext, useContext } from 'react'
import { createPortal } from 'react-dom'

import type { ErrorPlate } from '../types'
import places from './error.json'

const PLATES = places as Record<'wide' | 'tall', ErrorPlate>
// How much of the window's own room is kept round the pages, as a fraction of the plate, when cropping it.
const AIR = 0.02

/**
 * Whether what renders here is inside the stack of folders. A page that breaks as it renders there is caught inside
 * its strip, which is masked to its torn edge, so the error page is lifted out on to the body to cover the window.
 */
export const InStack = createContext(false)

type PlateProps = {
  name: 'wide' | 'tall'
  className: string
  again: () => void
  home: () => void
}

/**
 * One photograph of the book (studio/error/book.py), as large as the window holds it whole, the dark cloth it lies on
 * carried on out to the window's edges. Every word is in the photograph; over each lies the same text, clear, where it lies, so it can be read aloud,
 * selected and copied, and the two things to do are links over their printed words.
 */
function Plate({ name, className, again, home }: PlateProps) {
  const plate = PLATES[name]
  const [w, h] = plate.size
  const ratio = w / h
  const [x0, y0, x1, y1] = plate.pages
  const width = `min(max(100vw, ${ratio} * 100dvh), calc(100vw / ${x1 - x0 + 2 * AIR}), calc(${ratio} * 100dvh / ${y1 - y0 + 2 * AIR}))`
  const ids = Object.keys(plate.boxes)
  const group = (prefix: string) => ids.filter((id) => id.startsWith(`${prefix}-`))

  // A word's place, and its type sized to the printed word's: a column's width, or a line's height (its ascent and
  // descent together are 1.02 em in book.py).
  const at = (id: string): CSSProperties => {
    const { box, vertical } = plate.boxes[id]
    const [left, top, width, height] = box
    return {
      left: `${left * 100}%`,
      top: `${top * 100}%`,
      width: `${width * 100}%`,
      height: `${height * 100}%`,
      fontSize: vertical ? `${width * 100}cqw` : `${(height * 100) / ratio / 1.02}cqw`,
    }
  }
  const words = (id: string, extra: string): ReactNode => (
    <span key={id} className={`absolute block whitespace-nowrap ${extra}`} style={at(id)}>
      {plate.boxes[id].text}
    </span>
  )
  const column = '[writing-mode:vertical-rl] tracking-[0.1em] leading-none'
  // A line is clipped to its printed word's box, as the live face runs a little wider than the printed one.
  const line = 'overflow-hidden leading-[1.02]'
  const action = `absolute block cursor-pointer whitespace-nowrap rounded-[2px] p-0 text-left ${line} focus-visible:outline-[1.5px] focus-visible:outline-offset-4 focus-visible:outline-[#2a2622]`

  return (
    <div className={`absolute inset-0 items-center justify-center overflow-hidden ${className}`} style={{ backgroundColor: plate.edge }}>
      <div className="@container relative shrink-0" style={{ width, aspectRatio: `${w} / ${h}` }}>
        <img alt="" aria-hidden src={`/objects/error-${name}.avif`} loading="lazy" draggable={false} className="absolute inset-0 size-full select-none" />
        <div className="absolute inset-0 font-[Georgia,serif] text-transparent selection:bg-[#c9a24f]/35 selection:text-transparent">
          <p lang="ja" className="m-0">
            {group('poem').map((id) => words(id, column))}
            {words('poet', column)}
          </p>
          <blockquote className="m-0">
            <p className="m-0">{group('reading').map((id) => words(id, line))}</p>
            <footer>{words('source-0', line)}</footer>
          </blockquote>
          <h1 className="m-0 font-normal">{group('message').map((id) => words(id, line))}</h1>
          <button type="button" onClick={again} className={action} style={at('again-0')}>
            {plate.boxes['again-0'].text}
          </button>
          <Link to="/" onClick={home} className={action} style={at('home-0')}>
            {plate.boxes['home-0'].text}
          </Link>
        </div>
      </div>
    </div>
  )
}

/**
 * The page for a page that broke: a photograph of a book of poems lying open on a dark cloth, painted after the gold
 * screens of the Momoyama court with an old black pine, rocks, the sun and a great wave breaking toward Mount Fuji,
 * with Ki no Tomonori's poem on blossoms that fall on a calm day for no reason anyone can give, what
 * happened, and how to open the page again. A window at least 0.95 times as wide as it is tall shows the open book; a
 * narrower one, one loose page of it.
 */
export function ErrorPage({ error, reset }: ErrorComponentProps) {
  const router = useRouter()
  const inStack = useContext(InStack)
  const again = () => {
    reset()
    router.invalidate()
  }

  const page = (
    <main className="fixed inset-0 z-50 overflow-hidden" style={{ backgroundColor: PLATES.wide.edge }}>
      <Plate name="wide" className="hidden [@media(min-aspect-ratio:19/20)]:flex" again={again} home={reset} />
      <Plate name="tall" className="flex [@media(min-aspect-ratio:19/20)]:hidden" again={again} home={reset} />
      {import.meta.env.DEV && error instanceof Error && <p className="absolute bottom-2 left-3 m-0 font-mono text-[11px] text-black/60">{error.message}</p>}
    </main>
  )

  // Only the browser renders a page that broke in the stack: the server hands a page that throws to the browser.
  return inStack && typeof document !== 'undefined' ? createPortal(page, document.body) : page
}
