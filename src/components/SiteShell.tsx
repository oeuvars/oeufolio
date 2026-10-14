import { Link, useRouterState } from '@tanstack/react-router'
import { MotionConfig, motion, useReducedMotion } from 'motion/react'
import type { CSSProperties } from 'react'
import { useId } from 'react'

import { profile } from '../content'
import type { NavItem } from '../types'
import { Art } from './Art'
import { Badge } from './Badge'
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
 * the next without a seam. Each seed tears it differently. nicks is how many small bites are out of each
 * length, and how deep, in px. Along calm, spans of the edge from and to in px, the edge runs straight,
 * easing out of the tear and back into it, where a tab grows out of it.
 */
function tear(seed: number, reach: number, grain: Grain, calm: Array<[number, number]> = [], nicks = { count: 0, depth: 0 }) {
  let state = seed
  const random = () => {
    state = (state + 0x6d2b79f5) | 0
    let t = Math.imul(state ^ (state >>> 15), 1 | state)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
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
  const bites = Array.from({ length: nicks.count }, () => ({ at: random() * TEAR_LENGTH, wide: 3 + 5 * random(), deep: nicks.depth * (0.5 + random()) }))
  const ramp = 36
  const settled = (y: number) =>
    calm.reduce((least, [from, to]) => {
      const away = Math.max(from - y, y - to, 0) / ramp
      const f = Math.min(away, 1)
      return Math.min(least, f * f * (3 - 2 * f))
    }, 1)
  const points = Array.from({ length: TEAR_LENGTH + 1 }, (_, y) => {
    const bitten = bites.reduce((sum, { at, wide, deep }) => sum + deep * Math.max(0, 1 - ((y - at) / wide) ** 2), 0)
    const x = TEAR_WIDTH - settled(y) * (reach * scales.reduce((sum, scale) => sum + scale(y), 0) + bitten)
    return `${x.toFixed(2)} ${y}`
  })
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${TEAR_WIDTH}" height="${TEAR_LENGTH}" viewBox="0 0 ${TEAR_WIDTH} ${TEAR_LENGTH}"><path d="M0 0 L${points.join(' L')} L0 ${TEAR_LENGTH} Z"/></svg>`
  return `url("data:image/svg+xml,${encodeURIComponent(svg)}")`
}

/**
 * A strip's edge, as the style that carries it: its surface, and what shows past the surface, both from one
 * tear. Paper tears ragged, its core fraying out past the surface in its own colour. Leather is cut, and worn:
 * its edge wanders slowly and is bitten here and there, and past its grain shows its own edge, burnished dark.
 */
function torn(seed: number, calm: Array<[number, number]> = [], leather = false) {
  if (leather) {
    const grain = (fine: number) => [
      { every: 110, amount: 0.55 },
      { every: 30, amount: 0.3 },
      { every: 2, amount: fine },
    ]
    const nicks = { count: 9, depth: 2.2 }
    return {
      '--torn-surface': tear(seed, 6, grain(0.02), calm, nicks),
      '--torn-core': tear(seed, 4.4, grain(0.1), calm, nicks),
    } as CSSProperties
  }
  const grain = (fray: number) => [
    { every: 60, amount: 0.55 },
    { every: 14, amount: 0.3 },
    { every: 3, amount: fray },
  ]
  return { '--torn-surface': tear(seed, 11, grain(0.2), calm), '--torn-core': tear(seed, 7, grain(0.55), calm) } as CSSProperties
}
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
  current?: boolean
  /** A render of what is stuck on the tab. The tab carries no words, so the label is only what a link to it is called. */
  src: string
  /** The strip's page lies over its band, so the tab has no foot on the band: only what stands out of the strip is paper. */
  footless?: boolean
  /** The tab is cut from the page's own leather mat, not from paper. */
  leather?: boolean
  /** The tab is cut from the surface the page lies on, this tile of it, not from paper. */
  surface?: string
}

/**
 * The outline of a folder tab, as the reference cuts it: it leaves the strip's edge on a slant, runs
 * straight down and slants back in, with every corner eased. Its foot is the length of band it grows out of.
 * Returns the path and how far its joins reach.
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

function Tab({ label, shape, to, current, src, footless, leather, surface }: TabProps) {
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
        // The leather is the mat's, so it is in the mat's light: the lamp's, the dusk's and the dark. The mat
        // lends this its hour, its lamp and where its map of the lamp's light lies (mat/Mat.tsx). The clip
        // isolates what is in it, so the layers multiply on white and the whole multiplies the leather.
        <div
          aria-hidden
          data-mat-light
          className="pointer-events-none absolute left-0 bg-white mix-blend-multiply"
          style={{ top: -reach, width, height: shape.height + 2 * reach, clipPath: `url(#${cut})` }}
        >
          <div
            className="absolute inset-0 bg-no-repeat opacity-[calc(var(--lit,0)*(1-var(--day,1)))] mix-blend-multiply"
            style={{ backgroundColor: 'var(--light-rim)', backgroundImage: 'var(--light-image)', backgroundSize: 'var(--light-size)', backgroundPosition: 'var(--light-at)' }}
          />
          <div className="absolute inset-0 bg-golden opacity-[calc(var(--warmth,0)*0.5)] mix-blend-multiply" />
          <div className="absolute inset-0 bg-[rgb(10_14_24)] opacity-[calc((1-var(--day,1))*(1-var(--lit,0))*0.82)] mix-blend-multiply" />
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
  // eased joins meet a straight edge.
  const tears = pageTones.map((_, i) => {
    const shape = tabShape(i + 1)
    const top = tabTops[i + 1] * metrics.rem
    const { reach } = tabOutline(shape)
    return torn(31 + 17 * i, [[top - reach, top + shape.height + reach]], pageTones[i].fills || pageTones[i].roll)
  })
  const fixed = mobile ? 0 : spine + end
  const gaps = mobile ? count - 1 : count + 1
  // A strip whose page is a picture is folded half as wide again, to give its own picture room. The ticket's
  // strip shows only its roll, so it folds narrower than the rest.
  const folded = (i: number) => (pageTones[i].bleeds ? 1.5 * strip : pageTones[i].roll ? (mobile ? 0.7 * strip : contact) : strip)
  const shut = profile.nav.reduce((sum, _, i) => (i === index ? sum : sum + folded(i)), 0)
  const openWidth = metrics.width - fixed - shut + gaps * overlap
  // How wide a strip is when its page is open, whichever page is open now.
  const openWidthOf = (i: number) => (i === index ? openWidth : openWidth + folded(i) - folded(index))
  // A page laid out as it is when open, at the width it is then.
  const page = (i: number): CSSProperties => ({ width: openWidthOf(i) - band, minWidth: 0, paddingLeft: overlap + protrude + 16 })
  // The desk lies under its strip and goes with the strip's tab: it is laid at the width it has open, its
  // right edge kept to the strip's, so that the strip opening uncovers it from the left and folding covers
  // it again, and nothing on it moves.
  const underTab = (i: number): CSSProperties => ({ ...page(i), marginLeft: `calc(100% - ${openWidthOf(i)}px)` })

  const lefts: number[] = []
  let cursor = mobile ? 0 : spine - overlap
  for (let i = 0; i < count; i++) {
    lefts.push(cursor)
    cursor += (i === index ? openWidth : folded(i)) - overlap
  }

  // The mat's strip is leather, not paper, so the sheet's grain and creases are cut away over it (styles.css):
  // a column from where the strip before it ends to its own edge. They are put back in the shape of the paper
  // that lies on the mat there: the tab of the strip before it with its piece, and the piece on the mat's own tab.
  const mat = pageTones.findIndex((tone) => tone.fills)
  const matFrom = lefts[mat] + overlap
  const matTo = lefts[mat] + (mat === index ? openWidth : folded(mat))
  const tabWidth = band + protrude
  const pieceMargin = (tabMargin * tabWidth) / tabSpan
  const tabBefore = { shape: tabShape(mat), top: tabTops[mat] * metrics.rem, src: pageTones[mat - 1].tab }
  const tabOwn = { shape: tabShape(mat + 1), top: tabTops[mat + 1] * metrics.rem, src: pageTones[mat].tab }
  const paper = tabOutline(tabBefore.shape)
  const paperHeight = tabBefore.shape.height + 2 * paper.reach
  const paperMask = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 ${-paper.reach} ${tabWidth} ${paperHeight}" preserveAspectRatio="none"><path d="${paper.path}"/></svg>`
  // The same goes for a strip whose panel is a surface of its own, the ticket's leather: a second column, cut the same way.
  const skin = pageTones.findIndex((tone) => tone.surface)
  const skinFrom = lefts[skin] + overlap
  // Its tab is cut from the same leather and stands out past the strip's edge, so the cut runs on over it.
  const skinTo = lefts[skin] + (skin === index ? openWidth : folded(skin)) + protrude
  const column =
    'linear-gradient(to right, #000 calc(var(--mat-from) * 1px), transparent 0, transparent calc(var(--mat-to) * 1px), #000 0, #000 calc(var(--skin-from) * 1px), transparent 0, transparent calc(var(--skin-to) * 1px), #000 0)'
  const grainCut = {
    '--grain-cut': `${column}, url("data:image/svg+xml,${encodeURIComponent(paperMask)}"), url(${tabBefore.src}), url(${tabOwn.src})`,
    '--grain-cut-size': [
      '100% 100%',
      `${tabWidth}px ${paperHeight}px`,
      `${tabWidth + 2 * pieceMargin}px ${tabBefore.shape.height + 2 * pieceMargin}px`,
      `${tabWidth + 2 * pieceMargin}px ${tabOwn.shape.height + 2 * pieceMargin}px`,
    ].join(', '),
    '--grain-cut-position': [
      '0 0',
      `calc(var(--mat-from) * 1px - ${band}px) ${tabBefore.top - paper.reach}px`,
      `calc(var(--mat-from) * 1px - ${band + pieceMargin}px) ${tabBefore.top - pieceMargin}px`,
      `calc(var(--mat-to) * 1px - ${band + pieceMargin}px) ${tabOwn.top - pieceMargin}px`,
    ].join(', '),
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
            style={{ ...stripStyle(spineTone, 0, stack + 1, { left: 0, width: spine }), ...torn(7) }}
          >
            <div aria-hidden className="torn torn-core" />
            <div aria-hidden className="torn torn-surface" />
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
              className="strip"
              initial={false}
              animate={{ left: lefts[i], width: open ? openWidth : folded(i) }}
              transition={transition}
              style={{ ...stripStyle(pageTones[i], i + 1, stack - i), ...tears[i] }}
            >
              <div aria-hidden className={`torn torn-core ${pageTones[i].fills || pageTones[i].roll ? 'torn-leather' : ''}`} />
              <div aria-hidden className="torn torn-surface" />
              <div className={`panel scroll-quiet overflow-x-hidden overflow-y-auto ${pageTones[i].hangs || pageTones[i].bleeds || pageTones[i].fills || pageTones[i].roll ? 'panel-hangs' : ''}`}>
                {pageTones[i].surface && (
                  <div
                    aria-hidden
                    className="pointer-events-none absolute inset-0"
                    style={{
                      // The hide falls off a little into shadow toward the edges of the light.
                      backgroundImage: `radial-gradient(120% 85% at 50% 42%, transparent 50%, rgb(20 2 1 / 0.3)), url(${pageTones[i].surface})`,
                      backgroundSize: '100% 100%, 256px 256px',
                    }}
                  />
                )}
                {pageTones[i].hangs ? (
                  <Badge badge={profile.badge} page={openWidth} margin={band + protrude} open={open} />
                ) : pageTones[i].fills ? null : (
                  <motion.div
                    aria-hidden
                    className="absolute inset-y-0"
                    style={{ left: overlap, width: folded(i) - band - overlap }}
                    initial={false}
                    animate={{ opacity: open ? 0 : 1 }}
                    // A picture page folds back into its strip's picture, which has to be there at once to take over.
                    transition={{ duration: pageTones[i].bleeds && !open ? 0 : 0.35 }}
                  >
                    <Art index={i} open={open} />
                  </motion.div>
                )}

                {pageTones[i].fills ? (
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
                    initial={pageTones[i].bleeds ? false : { opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.45, delay: 0.3, ease: [0.215, 0.61, 0.355, 1] }}
                  >
                    <div className="grid flex-1 content-center py-[4vh]">{children}</div>
                  </motion.div>
                ) : null}
                {!open && <Link to={item.to} tabIndex={-1} aria-hidden className="absolute inset-0 z-10" />}
              </div>
              {(pageTones[i].fills || pageTones[i].roll) && <div aria-hidden className="torn torn-wear" />}
              <Tab label={item.label} shape={tabShape(i + 1)} to={item.to} current={open} src={pageTones[i].tab} footless={pageTones[i].fills || pageTones[i].roll} leather={pageTones[i].fills} surface={pageTones[i].surface} />
            </motion.section>
          )
        })}

        {!mobile && <div aria-hidden className="absolute inset-y-0 right-0 z-0 bg-[#1f1e1b]" style={{ width: end }} />}
      </motion.main>
    </MotionConfig>
  )
}
