import { Link, useRouter } from '@tanstack/react-router'
import type { ErrorComponentProps } from '@tanstack/react-router'
import type { CSSProperties } from 'react'
import { createContext, useContext } from 'react'
import { createPortal } from 'react-dom'

import errorCss from './error-page.css?url'

/** A random number between 0 and 1 from a seed, the same on the server and in the browser. */
function seeded(seed: number) {
  let state = seed
  return () => {
    state = (state * 16807) % 2147483647
    return (state - 1) / 2147483646
  }
}

/**
 * A torn edge of washi, as a clip-path: the edge runs through the given points, in percent of the box, wandering
 * a little between them, and the shape closes round the given corners.
 */
function torn(seed: number, edge: Array<[number, number]>, corners: Array<[number, number]>) {
  const random = seeded(seed)
  const points: string[] = []
  edge.forEach(([x, y], i) => {
    const next = edge[i + 1]
    if (!next) {
      points.push(`${x}% ${y}%`)
      return
    }
    for (let step = 0; step < 9; step++) {
      const f = step / 9
      const wander = (random() - 0.5) * 2.4
      points.push(`${(x + (next[0] - x) * f).toFixed(2)}% ${(y + (next[1] - y) * f + wander).toFixed(2)}%`)
    }
  })
  return `polygon(${[...points, ...corners.map(([x, y]) => `${x}% ${y}%`)].join(', ')})`
}

// Two sheets of dyed paper joined on to the spread along torn edges: pale indigo under the poem, wisteria over the
// translation.
const INDIGO = torn(7, [[0, 58], [34, 64], [62, 79], [100, 72]], [[100, 100], [0, 100]])
const WISTERIA = torn(19, [[100, 30], [70, 24], [38, 33], [0, 22]], [[0, 0], [100, 0]])

type Flake = { left: number; top: number; size: number; turn: number; cut: number; tone: number }

/**
 * Cut gold leaf sprinkled on the paper in drifts, as it was over the papers of the Heian anthologies: each drift a
 * centre in percent of the spread, how far it spreads, and how many flakes fell in it.
 */
function sprinkle(): Flake[] {
  const random = seeded(1112)
  const drifts: Array<[number, number, number, number]> = [
    [76, 12, 14, 16],
    [58, 62, 10, 14],
    [88, 80, 9, 10],
    [18, 30, 14, 14],
    [30, 86, 12, 12],
    [4, 64, 6, 6],
  ]
  return drifts.flatMap(([x, y, spread, count]) =>
    Array.from({ length: count }, () => {
      const r = spread * Math.sqrt(random())
      const a = random() * Math.PI * 2
      return {
        left: x + r * Math.cos(a),
        top: y + r * Math.sin(a) * 1.6,
        size: 3 + random() ** 2 * 17,
        turn: random() * 90,
        cut: Math.floor(random() * 4),
        tone: Math.floor(random() * 3),
      }
    }),
  )
}

const FLAKES = sprinkle()

// Blossom petals coming down over the page: where each starts across it, how long it takes to fall, when it sets
// out, and how big it is, in px.
const PETALS: Array<[number, number, number, number]> = [
  [12, 19, -2, 19],
  [27, 24, -11, 14],
  [44, 21, -6, 17],
  [61, 26, -17, 13],
  [73, 18, -9, 18],
  [86, 23, -3, 15],
  [94, 28, -20, 12],
]

const POEM = ['ひさかたの', '光のどけき', '春の日に', 'しづ心なく', '花の散るらむ']

/**
 * Whether what renders here is inside the stack of folders. A page that breaks as it renders there is caught inside
 * its strip, which is masked to its torn edge, so the error page is lifted out on to the body to cover the window.
 */
export const InStack = createContext(false)

/**
 * The page for a page that broke: a spread from an old book of poems, its papers dyed and joined, sprinkled with
 * gold leaf under bands of gold mist, with Ki no Tomonori's poem on blossoms that fall on a calm day for no reason
 * anyone can give, and what happened, and how to open the page again.
 */
export function ErrorPage({ error, reset }: ErrorComponentProps) {
  const router = useRouter()
  const inStack = useContext(InStack)
  const again = () => {
    reset()
    router.invalidate()
  }

  const page = (
    <main className="ep">
      {/* Only this page loads its styles and its faces. React lifts the link into the head. */}
      <link rel="stylesheet" href={errorCss} precedence="default" />
      <svg aria-hidden width="0" height="0" className="absolute">
        <defs>
          {/* A torn edge of washi: ragged, with its fibres feathering out past the tear. */}
          <filter id="ep-fray" x="-5%" y="-5%" width="110%" height="110%">
            <feTurbulence type="fractalNoise" baseFrequency="0.09" numOctaves="3" seed="5" result="warp" />
            <feDisplacementMap in="SourceGraphic" in2="warp" scale="9" xChannelSelector="R" yChannelSelector="G" />
          </filter>
          {/* Sumi ink, a little taken up by the paper. */}
          <filter id="ep-ink" x="-5%" y="-5%" width="110%" height="110%">
            <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2" seed="3" result="grain" />
            <feDisplacementMap in="SourceGraphic" in2="grain" scale="1.6" xChannelSelector="R" yChannelSelector="G" result="soaked" />
            <feGaussianBlur in="soaked" stdDeviation="0.25" />
          </filter>
          {/* The seal's vermilion, pressed unevenly. */}
          <filter id="ep-seal" x="-5%" y="-5%" width="110%" height="110%">
            <feTurbulence type="fractalNoise" baseFrequency="0.5" numOctaves="2" seed="13" result="grain" />
            <feDisplacementMap in="SourceGraphic" in2="grain" scale="2.5" xChannelSelector="R" yChannelSelector="G" result="rough" />
            <feTurbulence type="fractalNoise" baseFrequency="1.1" numOctaves="1" seed="2" result="specks" />
            <feColorMatrix in="specks" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -6 4.4" result="taken" />
            <feComposite in="rough" in2="taken" operator="in" />
          </filter>
          <linearGradient id="ep-petal" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#fbe9ec" />
            <stop offset="1" stopColor="#eab8c3" />
          </linearGradient>
        </defs>
      </svg>

      <div className="ep-book">
        {/* The right-hand page comes first in a Japanese book: the poem. */}
        <section className="ep-page ep-page-poem" lang="ja">
          <div aria-hidden className="ep-joined">
            <div className="ep-sheet ep-sheet-indigo" style={{ clipPath: INDIGO }} />
          </div>
          <div aria-hidden className="ep-mist ep-mist-high" />
          <div aria-hidden className="ep-mist ep-mist-high-2" />
          <div className="ep-poem">
            <p className="ep-verse">
              {POEM.map((line) => (
                <span key={line} className="ep-line">
                  {line}
                </span>
              ))}
            </p>
            <p className="ep-poet">紀友則</p>
          </div>
          <span aria-hidden className="ep-seal">
            <span>散</span>
            <span>花</span>
          </span>
        </section>

        <section className="ep-page ep-page-reading">
          <div aria-hidden className="ep-joined">
            <div className="ep-sheet ep-sheet-wisteria" style={{ clipPath: WISTERIA }} />
          </div>
          <div aria-hidden className="ep-mist ep-mist-low" />
          <div aria-hidden className="ep-mist ep-mist-low-2" />
          <div className="ep-reading">
            <blockquote className="ep-translation">
              <p>
                The light of far heaven
                <br />
                lies calm on this spring day.
                <br />
                Why, then, do the blossoms
                <br />
                fall with such unsettled hearts?
              </p>
              <footer>Ki no Tomonori, Kokinshū 84</footer>
            </blockquote>

            <h1 className="ep-message">This page hit an error while it was opening.</h1>
            {import.meta.env.DEV && error instanceof Error && <p className="ep-detail">{error.message}</p>}
            <p className="ep-actions">
              <button type="button" onClick={again}>
                Open it again
              </button>
              <Link to="/" onClick={reset}>
                Go to the first page
              </Link>
            </p>
          </div>
        </section>

        <div aria-hidden className="ep-gold">
          {FLAKES.map((flake, i) => (
            <span
              key={i}
              className={`ep-flake ep-cut-${flake.cut} ep-tone-${flake.tone}`}
              style={{ left: `${flake.left}%`, top: `${flake.top}%`, width: flake.size, height: flake.size * (flake.cut === 3 ? 0.18 : 0.8), rotate: `${flake.turn}deg` }}
            />
          ))}
        </div>
        <div aria-hidden className="ep-gutter" />
      </div>

      <div aria-hidden className="ep-petals">
        {PETALS.map(([left, fall, delay, size], i) => (
          <svg
            key={i}
            className="ep-petal"
            viewBox="0 0 24 28"
            width={size}
            height={size * (28 / 24)}
            style={{ left: `${left}%`, animationDuration: `${fall}s, ${fall / 4}s`, animationDelay: `${delay}s, ${delay}s` } as CSSProperties}
          >
            <path d="M12 5 L9.2 0.6 C3 6 -0.5 16 12 27.5 C24.5 16 21 6 14.8 0.6 Z" fill="url(#ep-petal)" />
          </svg>
        ))}
      </div>
    </main>
  )

  // Only the browser renders a page that broke in the stack: the server hands a page that throws to the browser.
  return inStack && typeof document !== 'undefined' ? createPortal(page, document.body) : page
}
