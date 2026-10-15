import { Link, useRouterState } from '@tanstack/react-router'
import { MotionConfig, motion, useReducedMotion } from 'motion/react'
import type { CSSProperties } from 'react'
import { useEffect, useId, useState } from 'react'

import { profile } from '../content'
import type { NavItem, VersionSearch } from '../types'
import { Art } from './Art'
import { Badge } from './Badge'
import { POSTER } from './house'
import { Desk } from './mat/Desk'
import { useStackMetrics } from './useStackMetrics'

type Tone = {
  band: string
  bandInk: string
  panel: string
  panelInk: string
  /** The page is the badge. Its panel runs to the top of the strip, where the badge's ring leaves it. */
  hangs?: boolean
  /** The page is a picture that runs to the strip's edges, so its panel has no frame either. Its band shows only as its tab's paper, which is the colour of the picture's sky so as to be lost in it. */
  bleeds?: boolean
  /** The page is a mat that takes the whole strip, band and all, so its panel has no frame. The band shows only as its tab's paper. */
  fills?: boolean
  /** The page is a ticket off a roll, lying on a panel that takes the whole strip, band and all. Folded, its strip
   * is only as wide as the roll, narrower than the others. */
  roll?: boolean
  /** What the panel is made of: a photographed square of it that repeats (studio/ticket/leather.py). It is not
   * paper, so the sheet's grain and creases are cut away over it. */
  surface?: string
  /** A paper's grain for the panel, as a tile that darkens its colour (studio/letter.py). */
  grain?: string
  /** What is stuck on the strip's paper tab in place of words: a render from studio/tabs.py. */
  tab: string
}

// The spine has no tab. Its edge is torn down its whole length, as every strip's is.
const spineTone: Omit<Tone, 'tab'> = { band: '#eeede8', bandInk: '#1d1d1b', panel: '#eeede8', panelInk: '#1d1d1b' }

// A torn edge's mask: how wide it is and how long one length of it runs before it repeats, in px.
const TEAR_WIDTH = 16
const TEAR_LENGTH = 1600

type Grain = Array<{ every: number; amount: number }>

/**
 * A strip's torn or worn edge, as a mask that repeats down the edge: solid to the left of the edge, clear to
 * its right. The edge wanders in and out at a few scales at once, grain giving each scale's length in px and
 * its share of reach, the most in px it wanders. It comes back to where it began, so one length of it meets
 * the next without a seam. Each seed tears it differently. Along calm, spans of the edge from and to in px,
 * the edge runs straight, easing out of the tear and back into it, where a tab grows out of it. outward tears
 * the paper out past the strip's edge, its deepest bites coming back only as far as the edge, for a strip over
 * something that starts right at its edge, so the tear never uncovers what is not there; the edge is then at
 * the mask's left, and the mask lies just past the strip.
 */
function tear(seed: number, reach: number, grain: Grain, calm: Array<[number, number]> = [], outward = false) {
  let state = seed
  const random = () => {
    state = (state + 0x6d2b79f5) | 0
    let t = Math.imul(state ^ (state >>> 15), 1 | state)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
  const most = grain.reduce((sum, { amount }) => sum + amount, 0)
  const scales = grain.map(({ every, amount }) => {
    const knots = Array.from({ length: Math.round(TEAR_LENGTH / every) }, random)
    return (y: number) => {
      const at = (y / TEAR_LENGTH) * knots.length
      const i = Math.floor(at)
      const f = at - i
      const ease = f * f * (3 - 2 * f)
      return amount * (knots[i % knots.length] * (1 - ease) + knots[(i + 1) % knots.length] * ease)
    }
  })
  const ramp = 36
  const settled = (y: number) =>
    calm.reduce((least, [from, to]) => {
      const away = Math.max(from - y, y - to, 0) / ramp
      const f = Math.min(away, 1)
      return Math.min(least, f * f * (3 - 2 * f))
    }, 1)
  const points = Array.from({ length: TEAR_LENGTH + 1 }, (_, y) => {
    const wander = scales.reduce((sum, scale) => sum + scale(y), 0)
    const x = outward ? settled(y) * reach * (most - wander) : TEAR_WIDTH - settled(y) * reach * wander
    return `${x.toFixed(2)} ${y}`
  })
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${TEAR_WIDTH}" height="${TEAR_LENGTH}" viewBox="0 0 ${TEAR_WIDTH} ${TEAR_LENGTH}"><path d="M0 0 L${points.join(' L')} L0 ${TEAR_LENGTH} Z"/></svg>`
  return `url("data:image/svg+xml,${encodeURIComponent(svg)}")`
}

/** How a strip's edge was made: paper torn, leather worn at a cut edge, or a mat cut clean. */
type Edge = 'torn' | 'worn' | 'cut'

/**
 * A strip's edge, as the style that carries it: where its surface ends, and where the stuff under the surface
 * ends, a little further out, both from one tear. Paper tears ragged, its core fraying out past the surface in
 * the colour of whatever is on it. Leather is cut, and worn only a little: its edge wanders slowly, and past
 * its grain shows its own edge, burnished dark. A mat is cut clean and straight, so it has no style at all.
 */
function torn(seed: number, calm: Array<[number, number]>, edge: Edge, outward = false): CSSProperties {
  if (edge === 'cut') return {}
  if (edge === 'worn') {
    const grain = (fine: number) => [
      { every: 140, amount: 0.65 },
      { every: 40, amount: 0.35 },
      { every: 4, amount: fine },
    ]
    // The wear eases out where the edge runs straight, as the tear does, so it never runs on into a tab.
    const quiet = calm.map(([from, to]) => `#000 ${from - 36}px, transparent ${from}px, transparent ${to}px, #000 ${to + 36}px`)
    return {
      '--torn-surface': tear(seed, 3, grain(0), calm),
      '--torn-core': tear(seed, 2.2, grain(0.08), calm),
      '--torn-calm': `linear-gradient(to bottom, #000 0, ${quiet.join(', ')}, #000 100%)`,
    } as CSSProperties
  }
  const grain = (fray: number) => [
    { every: 60, amount: 0.55 },
    { every: 14, amount: 0.3 },
    { every: 3, amount: fray },
  ]
  return { '--torn-surface': tear(seed, 11, grain(0.2), calm, outward), '--torn-core': tear(seed, 7, grain(0.55), calm, outward) } as CSSProperties
}

/** How a strip's own edge was made. */
const edgeOf = (tone: Tone): Edge => (tone.fills ? 'cut' : tone.roll ? 'worn' : 'torn')

/** The work strip's colours when its page is the poster: the poster's own dark, so nothing of the building's night is left. */
const posterTone = { band: '#100e0c', panel: '#100e0c' }

/** Whether a strip's page covers the whole strip, band and all. Only a page that sits framed on its band shows it. */
const hangs = (tone: Tone) => Boolean(tone.hangs || tone.bleeds || tone.fills || tone.roll)

const pageTones: Tone[] = [
  { band: '#e3d3c1', bandInk: '#3a281c', panel: '#e3d3c1', panelInk: '#3a281c', hangs: true, tab: '/objects/tab-lacoste.avif' },
  { band: '#7a8597', bandInk: '#121820', panel: '#cfcecb', panelInk: '#24242a', grain: '/photos/laid.avif', tab: '/objects/tab-prs.avif' },
  { band: '#1e2740', bandInk: '#f1e3c4', panel: '#1e2740', panelInk: '#f1e3c4', bleeds: true, tab: '/objects/tab-apple.avif' },
  { band: '#d9d4c2', bandInk: '#1e1d19', panel: '#236653', panelInk: '#0b1a15', fills: true, tab: '/objects/tab-proraso.avif' },
  { band: '#8a8b78', bandInk: '#20241a', panel: '#651415', panelInk: '#efe6cb', roll: true, surface: '/objects/leather.avif', tab: '/objects/tab-tagheuer.avif' },
]
const tabTops = [5, 9, 4, 6.5, 8.5, 4.5]
const tabHeights = [11, 10, 10, 10, 10, 11.5]
// A tab's width on a wide screen and the room a render of its piece keeps round the tab, in rem: WIDTH
// and MARGIN in studio/tabs.py. The heights above are for a tab of this width.
const tabSpan = 4
const tabMargin = 0.3

// A page's frame: its margins and type.
const PAGE = '@container relative flex min-h-full flex-col pr-[clamp(1rem,2.6vw,3rem)] py-[2.4vh] text-[clamp(14px,0.35vw+1.1vh,19px)] leading-[1.5]'
const slide = { type: 'spring', stiffness: 150, damping: 21, mass: 1 } as const
const instant = { duration: 0 } as const

function stripStyle(tone: Omit<Tone, 'tab'>, slot: number, z: number, extra: Record<string, string | number> = {}): CSSProperties {
  return {
    '--band': tone.band,
    '--band-ink': tone.bandInk,
    '--panel': tone.panel,
    '--panel-ink': tone.panelInk,
    '--paper': tone.panel,
    '--ink': tone.panelInk,
    '--panel-grain': tone.grain ? `url(${tone.grain})` : 'none',
    '--tab-top': `${tabTops[slot]}rem`,
    zIndex: z,
    ...extra,
  } as CSSProperties
}

type TabShape = {
  band: number
  protrude: number
  height: number
}

type TabProps = {
  label: string
  shape: TabShape
  to?: NavItem['to']
  /** The version of the page to open, if not its current one (the work page's building). */
  search?: VersionSearch
  /** The strip's page lies over its band, so the tab has no foot on the band: only what stands out of the strip is paper. */
  footless?: boolean
  current?: boolean
  /** A render of what is stuck on the tab. The tab carries no words, so the label is only what a link to it is called. */
  src: string
  /** The tab is cut from the page's own leather mat, not from paper. */
  leather?: boolean
  /** The tab is cut from the surface the page lies on, this tile of it, not from paper. */
  surface?: string
}

/**
 * The outline of a folder tab, as the reference cuts it: it leaves the strip's edge on a slant, runs
 * straight down and slants back in, with every corner eased. Its foot is the length of band it grows out of, when
 * the band shows. Returns the path and how far its joins reach.
 */
function tabOutline({ band, protrude, height }: TabShape, footless = false) {
  const rise = protrude * 0.33
  const ease = protrude * 0.2
  const reach = ease * 2
  const corners = [
    [band, -reach],
    [band, 0],
    [band + protrude, rise],
    [band + protrude, height - rise],
    [band, height],
    [band, height + reach],
  ]
  const toward = (from: number[], to: number[]) => {
    const length = Math.hypot(to[0] - from[0], to[1] - from[1])
    return [from[0] + ((to[0] - from[0]) / length) * ease, from[1] + ((to[1] - from[1]) / length) * ease]
  }
  const turns = corners.slice(1, -1).map((corner, i) => {
    const before = toward(corner, corners[i])
    const after = toward(corner, corners[i + 2])
    return `L${before[0]} ${before[1]} Q${corner[0]} ${corner[1]} ${after[0]} ${after[1]}`
  })
  const foot = footless ? band : 0
  return { reach, path: `M${foot} ${-reach} L${band} ${-reach} ${turns.join(' ')} L${band} ${height + reach} L${foot} ${height + reach} Z` }
}

function Tab({ label, shape, to, search, current, src, footless, leather, surface }: TabProps) {
  const { reach, path } = tabOutline(shape, footless)
  const hide = useId()
  const cut = useId()
  const width = shape.band + shape.protrude
  const margin = (tabMargin * width) / tabSpan
  const inside = (
    <>
      <svg
        aria-hidden
        className="tab-shape"
        width={width}
        height={shape.height + 2 * reach}
        viewBox={`0 ${-reach} ${width} ${shape.height + 2 * reach}`}
        style={{ top: -reach }}
      >
        {leather && (
          <defs>
            <pattern id={hide} patternUnits="userSpaceOnUse" width="160" height="160">
              <rect width="160" height="160" className="fill-mat" />
              <image href="/objects/mat/leather.avif" width="160" height="160" />
              {/* The tab grows out of the mat's ruler, so it is as dark as the ruler's band. */}
              <rect width="160" height="160" fill="black" opacity="0.16" />
            </pattern>
            <clipPath id={cut}>
              <path d={path} transform={`translate(0 ${reach})`} />
            </clipPath>
          </defs>
        )}
        {surface && !leather && (
          <defs>
            {/* The same tile, at the same size, as the panel the tab grows out of. */}
            <pattern id={hide} patternUnits="userSpaceOnUse" width="256" height="256">
              <image href={surface} width="256" height="256" />
            </pattern>
          </defs>
        )}
        <path d={path} fill={leather || surface ? `url(#${hide})` : undefined} />
      </svg>
      {leather && (
        // The leather is the mat's, so it is in the mat's light: the lamp's, or the dark. The mat
        // lends this its lamp and where its map of the lamp's light lies (mat/Mat.tsx). The clip
        // isolates what is in it, so the layers multiply on white and the whole multiplies the leather.
        <div
          aria-hidden
          data-mat-light
          className="pointer-events-none absolute left-0 bg-white mix-blend-multiply"
          style={{ top: -reach, width, height: shape.height + 2 * reach, clipPath: `url(#${cut})` }}
        >
          <div
            className="absolute inset-0 bg-no-repeat opacity-[var(--lit,0)] mix-blend-multiply"
            style={{ backgroundColor: 'var(--light-rim)', backgroundImage: 'var(--light-image)', backgroundSize: 'var(--light-size)', backgroundPosition: 'var(--light-at)' }}
          />
          <div className="absolute inset-0 bg-[rgb(10_14_24)] opacity-[calc((1-var(--lit,0))*0.82)] mix-blend-multiply" />
        </div>
      )}
      <img
        aria-hidden
        alt=""
        src={src}
        draggable={false}
        className="tab-piece"
        style={{ left: -margin, top: -margin, width: width + 2 * margin, height: shape.height + 2 * margin }}
      />
    </>
  )

  if (!to) {
    return (
      <div className="tab" style={{ height: shape.height }}>
        {inside}
      </div>
    )
  }

  return (
    <Link
      to={to}
      search={search}
      activeOptions={{ exact: true }}
      aria-label={label}
      aria-current={current ? 'page' : undefined}
      className="tab"
      style={{ height: shape.height }}
    >
      {inside}
    </Link>
  )
}

type SiteShellProps = {
  children: React.ReactNode
}

export function SiteShell({ children }: SiteShellProps) {
  const pathname = useRouterState({ select: (state) => state.location.pathname })
  const poster = useRouterState({ select: (state) => state.location.pathname === '/work' && Number((state.location.search as { v?: unknown }).v) !== 1 })
  // The version of the work page last open: its strip shows that version folded, and opens to it again.
  const [workPoster, setWorkPoster] = useState(true)
  useEffect(() => {
    if (pathname === '/work') setWorkPoster(poster)
  }, [pathname, poster])
  const searchOf = (to: NavItem['to']): VersionSearch | undefined => (to === '/work' && !workPoster ? { v: 1 } : undefined)
  // Each strip is the colour of the page it holds, so the work strip takes the poster's when the poster is its page.
  const tones = pageTones.map((tone) => (tone.bleeds && workPoster ? { ...tone, ...posterTone } : tone))
  const index = Math.max(
    0,
    profile.nav.findIndex((item) => item.to === pathname),
  )
  const count = profile.nav.length
  const stack = count + 2
  const { metrics, ready } = useStackMetrics()
  const reduced = useReducedMotion()
  const transition = ready && !reduced ? slide : instant

  const { overlap, band, protrude, strip, spine, contact, end, mobile } = metrics
  const tabShape = (slot: number): TabShape => ({ band, protrude, height: (tabHeights[slot] * (band + protrude)) / tabSpan })
  // Each page's edge is torn its own way, and runs straight where its tab grows out of it, so the tab's
  // eased joins meet a straight edge. Open, the mat is laid from the edge of the strip before it, and it cannot
  // be laid any wider without moving everything on it, so that strip's tear reaches out over the mat instead.
  const reachesOver = (i: number) => Boolean(tones[i + 1]?.fills)
  const tears = tones.map((_, i) => {
    const shape = tabShape(i + 1)
    const top = tabTops[i + 1] * metrics.rem
    const { reach } = tabOutline(shape)
    return torn(31 + 17 * i, [[top - reach, top + shape.height + reach]], edgeOf(tones[i]), reachesOver(i))
  })
  const fixed = mobile ? 0 : spine + end
  const gaps = mobile ? count - 1 : count + 1
  // A strip whose page is a picture is folded half as wide again, to give its own picture room. The ticket's
  // strip shows only its roll, so it folds narrower than the rest.
  const folds = (i: number) => (tones[i].bleeds ? 1.5 * strip : tones[i].roll ? (mobile ? 0.7 * strip : contact) : strip)
  // How wide a strip is open: the room the others leave it, folded.
  const roomFor = (i: number) => metrics.width - fixed - profile.nav.reduce((sum, _, j) => (j === i ? sum : sum + folds(j)), 0) + gaps * overlap
  // The work page's poster runs the window's height and out to the strip's torn edge, so its strip opens only as wide
  // as the poster is at that height, past the part under the strip before it. The room left over is shared among the
  // folded strips.
  const room = roomFor(index)
  const openWidth = poster && !mobile ? Math.min(room, (metrics.height * POSTER.width) / POSTER.height + overlap) : room
  const spare = (room - openWidth) / (count - 1)
  const folded = (i: number) => folds(i) + spare
  // How wide a strip is when its page is open, whichever page is open now.
  const openWidthOf = (i: number) => (i === index ? openWidth : roomFor(i))
  // A page laid out as it is when open, at the width it is then, and as wide as its panel: the whole strip when the
  // page covers it, out to the torn edge and over the tear's reach past it, so what the page lays out to its edges
  // is what the tear cuts; and short of the band when the page sits framed on it.
  const page = (i: number): CSSProperties => ({
    width: hangs(tones[i]) ? openWidthOf(i) + (reachesOver(i) ? TEAR_WIDTH : 0) : openWidthOf(i) - band,
    minWidth: 0,
    paddingLeft: overlap + protrude + 16,
  })
  // The desk lies under its strip and goes with the strip's tab: it is laid at the width it has open, its
  // right edge kept to the strip's, so that the strip opening uncovers it from the left and folding covers
  // it again, and nothing on it moves.
  const underTab = (i: number): CSSProperties => ({ ...page(i), width: openWidthOf(i) - band, marginLeft: `calc(100% - ${openWidthOf(i)}px)` })

  const lefts: number[] = []
  let cursor = mobile ? 0 : spine - overlap
  for (let i = 0; i < count; i++) {
    lefts.push(cursor)
    cursor += (i === index ? openWidth : folded(i)) - overlap
  }

  // The mat's strip is leather, not paper, so the sheet's grain and creases are cut away over it (styles.css):
  // a column from where the strip before it ends to its own edge. They are put back in the shape of the paper
  // that lies on the mat there: the tab of the strip before it with its piece, and the piece on the mat's own tab.
  const mat = tones.findIndex((tone) => tone.fills)
  const matFrom = lefts[mat] + overlap
  const matTo = lefts[mat] + (mat === index ? openWidth : folded(mat))
  const tabWidth = band + protrude
  const pieceMargin = (tabMargin * tabWidth) / tabSpan
  const tabBefore = { shape: tabShape(mat), top: tabTops[mat] * metrics.rem, src: tones[mat - 1].tab }
  const tabOwn = { shape: tabShape(mat + 1), top: tabTops[mat + 1] * metrics.rem, src: tones[mat].tab }
  const paper = tabOutline(tabBefore.shape)
  const paperHeight = tabBefore.shape.height + 2 * paper.reach
  const paperMask = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 ${-paper.reach} ${tabWidth} ${paperHeight}" preserveAspectRatio="none"><path d="${paper.path}"/></svg>`
  // The same goes for a strip whose panel is a surface of its own, the ticket's leather: a second column, cut the same way.
  const skin = tones.findIndex((tone) => tone.surface)
  const skinFrom = lefts[skin] + overlap
  // Its tab is cut from the same leather and stands out past the strip's edge. It is the last strip, so the cut runs on
  // to the window's edge: over the tab, and over the dark beyond it, so no line is left in the dark where it ends.
  const skinTo = lefts[skin] + (skin === index ? openWidth : folded(skin)) + 4000
  // The strip before the mat tears out over it: the paper on the mat past that strip's edge, its frayed core
  // with it, is put back by the tear's own mask.
  const column =
    `linear-gradient(to right, #000 calc(var(--mat-from) * 1px), transparent 0, transparent calc(var(--mat-to) * 1px), #000 0, #000 calc(var(--skin-from) * 1px), transparent 0, transparent calc(var(--skin-to) * 1px), #000 0)`
  const grainCut = {
    '--grain-cut': `${column}, ${(tears[mat - 1] as Record<string, string>)['--torn-core']}, url("data:image/svg+xml,${encodeURIComponent(paperMask)}"), url(${tabBefore.src}), url(${tabOwn.src})`,
    '--grain-cut-size': [
      '100% 100%',
      `${TEAR_WIDTH}px ${TEAR_LENGTH}px`,
      `${tabWidth}px ${paperHeight}px`,
      `${tabWidth + 2 * pieceMargin}px ${tabBefore.shape.height + 2 * pieceMargin}px`,
      `${tabWidth + 2 * pieceMargin}px ${tabOwn.shape.height + 2 * pieceMargin}px`,
    ].join(', '),
    '--grain-cut-position': [
      '0 0',
      'calc(var(--mat-from) * 1px) 0',
      `calc(var(--mat-from) * 1px - ${band}px) ${tabBefore.top - paper.reach}px`,
      `calc(var(--mat-from) * 1px - ${band + pieceMargin}px) ${tabBefore.top - pieceMargin}px`,
      `calc(var(--mat-to) * 1px - ${band + pieceMargin}px) ${tabOwn.top - pieceMargin}px`,
    ].join(', '),
    '--grain-cut-repeat': 'no-repeat, repeat-y, no-repeat, no-repeat, no-repeat',
  }

  return (
    <MotionConfig reducedMotion="user">
      <svg aria-hidden width="0" height="0" className="absolute">
        <defs>
          {/* Ink on paper: a ragged edge, then flecks where the ink did not take. */}
          <filter id="print" x="-5%" y="-5%" width="110%" height="110%" colorInterpolationFilters="sRGB">
            <feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="2" seed="3" result="edge" />
            <feDisplacementMap in="SourceGraphic" in2="edge" scale="1.3" xChannelSelector="R" yChannelSelector="G" result="rough" />
            <feGaussianBlur in="rough" stdDeviation="0.3" result="soft" />
            <feTurbulence type="fractalNoise" baseFrequency="0.95" numOctaves="3" seed="8" result="grain" />
            <feColorMatrix in="grain" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  1.7 0 0 0 0.2" result="taken" />
            <feComposite in="soft" in2="taken" operator="in" />
          </filter>
          <filter id="print-fine" x="-5%" y="-10%" width="110%" height="120%" colorInterpolationFilters="sRGB">
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="5" result="edge" />
            <feDisplacementMap in="SourceGraphic" in2="edge" scale="0.6" xChannelSelector="R" yChannelSelector="G" result="rough" />
            <feTurbulence type="fractalNoise" baseFrequency="1.3" numOctaves="2" seed="11" result="grain" />
            <feColorMatrix in="grain" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  1.4 0 0 0 0.36" result="taken" />
            <feComposite in="rough" in2="taken" operator="in" />
          </filter>
        </defs>
      </svg>
      <motion.main
        className="grain fixed inset-0 overflow-hidden bg-[#1f1e1b]"
        style={{ '--band-w': `${band}px`, '--protrude': `${protrude}px`, ...grainCut } as CSSProperties}
        initial={false}
        // The cut follows the mat's strip as it slides: both are on the same spring.
        animate={{ '--mat-from': matFrom, '--mat-to': matTo, '--skin-from': skinFrom, '--skin-to': skinTo }}
        transition={transition}
      >
        {!mobile && (
          <aside
            className="strip"
            style={{ ...stripStyle(spineTone, 0, stack + 1, { left: 0, width: spine }), ...torn(7, [], 'torn') }}
          >
            <div aria-hidden className="torn" />
            {/* A traffic signal printed in four colours, a rose, a sunflower with an eye and a lily pad for its
                lamps (studio/signal). It runs out to the tear, which cuts it as it cuts the paper, and its post runs on down
                past the foot of the strip, so a short window cuts it there. */}
            <Link to="/" aria-label={profile.handle} className="torn">
              <img alt="" src="/objects/signal.avif" draggable={false} className="size-full object-cover object-top mix-blend-multiply" />
            </Link>
          </aside>
        )}

        {profile.nav.map((item, i) => {
          const open = i === index

          return (
            <motion.section
              key={item.to}
              className={`strip ${reachesOver(i) ? 'strip-reaches' : ''}`}
              initial={false}
              animate={{ left: lefts[i], width: open ? openWidth : folded(i) }}
              transition={transition}
              style={{ ...stripStyle(tones[i], i + 1, stack - i), ...tears[i] }}
            >
              {/* A page that hangs covers its whole strip, so the strip has no paper of its own to show at the tear. */}
              {!hangs(tones[i]) && <div aria-hidden className="torn" />}
              <div className={`panel scroll-quiet overflow-x-hidden overflow-y-auto ${hangs(tones[i]) ? 'panel-hangs' : ''}`}>
                {tones[i].surface && (
                  <div
                    aria-hidden
                    className="pointer-events-none absolute inset-0"
                    style={{
                      // Under the photograph of the set, which covers it: only a window taller than the photograph shows it.
                      backgroundImage: `url(${tones[i].surface})`,
                      backgroundSize: '256px 256px',
                    }}
                  />
                )}
                {tones[i].hangs ? (
                  <Badge badge={profile.badge} page={openWidth} margin={band + protrude} open={open} />
                ) : tones[i].fills ? null : (
                  <motion.div
                    aria-hidden
                    className="absolute inset-y-0"
                    // A picture runs on under the strip before it as far as that strip's tear can bite, so the tear
                    // never uncovers bare panel.
                    style={tones[i].bleeds ? { left: overlap - TEAR_WIDTH, width: folded(i) - band - overlap + TEAR_WIDTH } : { left: overlap, width: folded(i) - band - overlap }}
                    initial={false}
                    animate={{ opacity: open ? 0 : 1 }}
                    // A picture page folds back into its strip's picture, which has to be there at once to take over.
                    transition={{ duration: tones[i].bleeds && !open ? 0 : 0.35 }}
                  >
                    <Art index={i} open={open} poster={workPoster} />
                  </motion.div>
                )}

                {tones[i].fills ? (
                  // The desk is always here, open or folded: folded, the strip shows the edge of it beside the
                  // tab. It is never laid again, so whatever is on it stays as it was left.
                  <div className={PAGE} style={underTab(i)} inert={!open} aria-hidden={!open || undefined}>
                    <div className="grid flex-1 content-center py-[4vh]">
                      {open && children}
                      <Desk />
                    </div>
                  </div>
                ) : open ? (
                  <motion.div
                    className={PAGE}
                    style={page(i)}
                    // A page that is a picture grows out of its strip's own picture, so it is there from the start.
                    initial={tones[i].bleeds ? false : { opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.45, delay: 0.3, ease: [0.215, 0.61, 0.355, 1] }}
                  >
                    <div className="grid flex-1 content-center py-[4vh]">{children}</div>
                  </motion.div>
                ) : null}
                {!open && <Link to={item.to} search={searchOf(item.to)} tabIndex={-1} aria-hidden className="absolute inset-0 z-10" />}
              </div>
              {/* The ticket's leather is a photograph that runs to the tear, its own cut edge and wear in it, so it has none laid over it. */}
              {edgeOf(tones[i]) === 'worn' && !tones[i].surface && (
                <>
                  <div aria-hidden className="torn-fray" />
                  <div aria-hidden className="torn torn-wear" />
                </>
              )}
              <Tab label={item.label} shape={tabShape(i + 1)} to={item.to} search={searchOf(item.to)} current={open} src={tones[i].tab} footless={hangs(tones[i])} leather={tones[i].fills} surface={tones[i].surface} />
            </motion.section>
          )
        })}

        {!mobile && <div aria-hidden className="absolute inset-y-0 right-0 z-0 bg-[#1f1e1b]" style={{ width: end }} />}
      </motion.main>
    </MotionConfig>
  )
}
