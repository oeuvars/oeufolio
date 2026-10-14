import { Link, useRouterState } from '@tanstack/react-router'
import { MotionConfig, motion, useReducedMotion } from 'motion/react'
import type { CSSProperties } from 'react'

import { profile } from '../content'
import type { NavItem } from '../types'
import { Art } from './Art'
import { Badge } from './Badge'
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
  /** A paper's grain for the panel, as a tile that darkens its colour (studio/letter.py). */
  grain?: string
  /** What is stuck on the strip's paper tab in place of words: a render from studio/tabs.py. */
  tab: string
}

const spineTone: Tone = { band: '#bfa391', bandInk: '#3a281c', panel: '#bfa391', panelInk: '#3a281c', tab: '/objects/tab-tagheuer.avif' }
const pageTones: Tone[] = [
  { band: '#e3d3c1', bandInk: '#3a281c', panel: '#e3d3c1', panelInk: '#3a281c', hangs: true, tab: '/objects/tab-lacoste.avif' },
  { band: '#7a8597', bandInk: '#121820', panel: '#cfcecb', panelInk: '#24242a', grain: '/photos/laid.avif', tab: '/objects/tab-prs.avif' },
  { band: '#1e2740', bandInk: '#f1e3c4', panel: '#1e2740', panelInk: '#f1e3c4', bleeds: true, tab: '/objects/tab-apple.avif' },
  { band: '#d9d4c2', bandInk: '#1e1d19', panel: '#236653', panelInk: '#0b1a15', fills: true, tab: '/objects/tab-proraso.avif' },
  { band: '#8a8b78', bandInk: '#20241a', panel: '#10150f', panelInk: '#efe6cb', roll: true, tab: '/objects/tab-van.avif' },
]
const tabTops = [5, 9, 4, 6.5, 8.5, 4.5]
const tabHeights = [11, 10, 10, 10, 10, 11.5]
// A tab's width on a wide screen and the room a render of its piece keeps round the tab, in rem: WIDTH
// and MARGIN in studio/tabs.py. The heights above are for a tab of this width.
const tabSpan = 4
const tabMargin = 0.3

const slide = { type: 'spring', stiffness: 150, damping: 21, mass: 1 } as const
const instant = { duration: 0 } as const

function stripStyle(tone: Tone, slot: number, z: number, extra: Record<string, string | number> = {}): CSSProperties {
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

function Tab({ label, shape, to, current, src, footless }: TabProps) {
  const { reach, path } = tabOutline(shape, footless)
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
        <path d={path} />
      </svg>
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
  const fixed = mobile ? 0 : spine + end
  const gaps = mobile ? count - 1 : count + 1
  // A strip whose page is a picture is folded half as wide again, to give its own picture room. The ticket's
  // strip shows only its roll, so it folds narrower than the rest.
  const folded = (i: number) => (pageTones[i].bleeds ? 1.5 * strip : pageTones[i].roll ? (mobile ? 0.7 * strip : contact) : strip)
  const shut = profile.nav.reduce((sum, _, i) => (i === index ? sum : sum + folded(i)), 0)
  const openWidth = metrics.width - fixed - shut + gaps * overlap
  const panelWidth = openWidth - band

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
  const tabBefore = { shape: tabShape(mat), top: tabTops[mat] * metrics.rem, src: (mat > 0 ? pageTones[mat - 1] : spineTone).tab }
  const tabOwn = { shape: tabShape(mat + 1), top: tabTops[mat + 1] * metrics.rem, src: pageTones[mat].tab }
  const paper = tabOutline(tabBefore.shape)
  const paperHeight = tabBefore.shape.height + 2 * paper.reach
  const paperMask = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 ${-paper.reach} ${tabWidth} ${paperHeight}" preserveAspectRatio="none"><path d="${paper.path}"/></svg>`
  const column = 'linear-gradient(to right, #000 calc(var(--mat-from) * 1px), transparent 0, transparent calc(var(--mat-to) * 1px), #000 0)'
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
        animate={{ '--mat-from': matFrom, '--mat-to': matTo }}
        transition={transition}
      >
        {!mobile && (
          <aside className="strip" style={stripStyle(spineTone, 0, stack + 1, { left: 0, width: spine })}>
            <div className="absolute inset-y-0 left-0 flex flex-col py-[3vh]" style={{ right: band }}>
              <Link
                to="/"
                aria-label={profile.handle}
                className="display vertical ml-[1.1rem] self-start whitespace-nowrap text-[min(6.4vh,5vw)] no-underline"
              >
                {profile.handle}_01-0{count}
              </Link>
              <div className="mt-auto ml-[1.1rem] flex items-end gap-[0.9rem]">
                <p className="caption vertical leading-[1.7] whitespace-nowrap">
                  Product Studies:
                  <br />
                  Type · Image · Craft
                </p>
              </div>
              <p className="caption mt-[1.4rem] ml-[1.1rem] !font-bold">FILE_01//</p>
            </div>
            <Tab label="Home" shape={tabShape(0)} to="/" current={false} src={spineTone.tab} />
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
              style={stripStyle(pageTones[i], i + 1, stack - i)}
            >
              <div className={`panel scroll-quiet overflow-x-hidden overflow-y-auto ${pageTones[i].hangs || pageTones[i].bleeds || pageTones[i].fills || pageTones[i].roll ? 'panel-hangs' : ''}`}>
                {pageTones[i].hangs ? (
                  <Badge badge={profile.badge} page={openWidth} margin={band + protrude} open={open} />
                ) : (
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

                {open ? (
                  <motion.div
                    className="@container relative flex min-h-full flex-col pr-[clamp(1rem,2.6vw,3rem)] py-[2.4vh] text-[clamp(14px,0.35vw+1.1vh,19px)] leading-[1.5]"
                    style={{ width: panelWidth, minWidth: 0, paddingLeft: overlap + protrude + 16 }}
                    // A page that is a picture grows out of its strip's own picture, so it is there from the start.
                    initial={pageTones[i].bleeds ? false : { opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.45, delay: 0.3, ease: [0.215, 0.61, 0.355, 1] }}
                  >
                    <div className="grid flex-1 content-center py-[4vh]">{children}</div>
                  </motion.div>
                ) : (
                  <Link to={item.to} tabIndex={-1} aria-hidden className="absolute inset-0 z-10" />
                )}
              </div>
              <Tab label={item.label} shape={tabShape(i + 1)} to={item.to} current={open} src={pageTones[i].tab} footless={pageTones[i].fills || pageTones[i].roll} />
            </motion.section>
          )
        })}

        {!mobile && <div aria-hidden className="absolute inset-y-0 right-0 z-0 bg-[#1f1e1b]" style={{ width: end }} />}
      </motion.main>
    </MotionConfig>
  )
}
