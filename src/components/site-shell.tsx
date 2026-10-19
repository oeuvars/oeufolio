import { Link, useRouterState } from '@tanstack/react-router'
import { MotionConfig, motion, useReducedMotion } from 'motion/react'
import type { CSSProperties } from 'react'
import { useEffect, useId, useState } from 'react'

import { profile } from '../content'
import type { NavItem, VersionSearch } from '../types'
import { Art } from './art'
import { Badge } from './badge'
import { POSTER } from './house'
import { Desk } from './mat/desk'
import { Resume } from './resume'
import tabcut from './tabcut.json'
import { Ticket } from './ticket/ticket'
import { useStackMetrics } from './use-stack-metrics'

/** A material as a tile that repeats without a seam, and how many CSS pixels square it is shown. */
type Paper = {
  src: string
  size: number
}

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
  /** The strip is a plain page, cut straight down its edge, not torn. */
  cut?: boolean
  /** The strip is cloth, cut down its edge with scissors: this mask of the cut, its weft ends frayed past it
   * (studio/linen.py --edge), in place of a straight cut. Cloth casts no drop shadow: it leaves its own (cast). */
  frayed?: string
  /** The shadow the cloth leaves on the page beyond its cut, rendered from the same mask (studio/linen.py --shadow):
   * a tile down the edge, CAST_WIDTH px wide from the mask's left, laid under the cloth and out over the next strip. */
  cast?: string
  /** The strip is handmade paper, its edge the deckle the pulp stopped at, thinning to loose fibres: this mask of
   * it (studio/paper/edge.py), in place of a straight cut. Paper casts its shadow, as the strip's own does. */
  deckled?: string
  /** What the page is made of, as a tile that repeats, size CSS pixels square: the poster's wall (studio/poster) or
   * the letter's handmade sheet (studio/paper). The page covers its whole strip, and the strip and its tab are cut
   * from it, so they are the page's own paper and not a flat colour. */
  paper?: Paper
  /** What the page is made of when it is one photographed plate, not a tile: light yellow linen (studio/linen.py). It
   * is laid from the strip's top left at least as big as the window, so opening the strip uncovers more of the same
   * plate, and it is not paper, so it has none of the paper's grain over it. */
  plate?: string
  /** What is stuck on the strip's paper tab in place of words: a render from studio/tabs.py. */
  tab: string
}

// The spine has no tab. Its edge is torn down its whole length, as every strip's is.
const spineTone: Omit<Tone, 'tab'> = { band: '#eeede8', bandInk: '#1d1d1b', panel: '#eeede8', panelInk: '#1d1d1b' }

// A torn edge's mask: how wide it is and how long one length of it runs before it repeats, in px.
const TEAR_WIDTH = 16
const TEAR_LENGTH = 1600
// How far in from its right the cut runs down a cloth's frayed edge mask (studio/linen.py edge): the mask lies that
// far out past the strip, so the cut is the strip's edge, meeting its tab's straight foot, and the weft ends lie over the next strip.
const FRAY_PAST = 9
// How wide the cloth's shadow tile is, from the frayed mask's left (studio/linen.py SHADOW_FRAME).
const CAST_WIDTH = 40
// The same for a handmade sheet's deckle mask (studio/paper/edge.py, DECKLE_PAST).
const DECKLE_PAST = 9

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
const tear = (seed: number, reach: number, grain: Grain, calm: Array<[number, number]> = [], outward = false) => {
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
const torn = (seed: number, calm: Array<[number, number]>, edge: Edge, outward = false): CSSProperties => {
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
const edgeOf = (tone: Tone): Edge => (tone.fills || tone.cut ? 'cut' : tone.roll ? 'worn' : 'torn')

/** The work strip's colours when its page is the poster: the poster's own dark, so nothing of the building's night is left. */
// Its tile is PAPER_SIZE in studio/poster/poster.py, written at twice the size it is shown.
const posterTone = { band: '#100e0c', panel: '#100e0c', paper: { src: '/objects/poster-paper.avif', size: 140 } }

/** Whether a strip's page covers the whole strip, band and all. Only a page that sits framed on its band shows it. */
/** Whether a strip's page is paper, one sheet with its tab: all but the mat and the ticket's leather. */
const sheets = (tone: Tone) => !tone.fills && !tone.roll

const hangs = (tone: Tone) => Boolean(tone.hangs || tone.bleeds || tone.fills || tone.roll || tone.paper)

const pageTones: Tone[] = [
  // The plate is cut, not torn, and its colours are the linen's middle tone, under the plate before it loads.
  { band: '#ede3a1', bandInk: '#2e2418', panel: '#ede3a1', panelInk: '#2e2418', hangs: true, cut: true, frayed: '/objects/linen-edge.png', cast: '/objects/linen-shadow.png', plate: '/objects/linen.avif', tab: '/objects/tab-lacoste.avif' },
  // The letter's handmade sheet (studio/paper), TILE in paper.py written at twice the size it is shown.
  { band: '#ebe7e1', bandInk: '#24242a', panel: '#ebe7e1', panelInk: '#24242a', cut: true, deckled: '/objects/likes-edge.png', paper: { src: '/objects/likes-paper.avif', size: 768 }, tab: '/objects/tab-prs.avif' },
  { band: '#1e2740', bandInk: '#f1e3c4', panel: '#1e2740', panelInk: '#f1e3c4', bleeds: true, tab: '/objects/tab-teenage.avif' },
  { band: '#d9d4c2', bandInk: '#1e1d19', panel: '#236653', panelInk: '#0b1a15', fills: true, tab: '/objects/tab-proraso.avif' },
  { band: '#8a8b78', bandInk: '#20241a', panel: '#651415', panelInk: '#efe6cb', roll: true, surface: '/objects/leather.avif', tab: '/objects/tab-tagheuer.avif' },
]
// The hide's tile: the contact page's leather (studio/ticket/leather.py), the one texture its strip and tab are. It is
// TILE (8) em of the ticket's spread across, and the spread is 90vh tall for its 29.85 em (ticket/ticket.tsx), so the
// hide's grain is the size it was beside the ticket in the scene's photograph.
const HIDE = `calc(90vh * ${8 / 29.85})`
const tabTops = [5, 9, 4, 6.5, 8.5, 4.5]
const tabHeights = [11, 10, 10, 10, 10, 11.5]
// A tab's width on a wide screen and the room a render of its piece keeps round the tab, in rem: WIDTH
// and MARGIN in studio/tabs.py. The heights above are for a tab of this width.
const tabSpan = 4
const tabMargin = 0.3

// The grain of a sheet of paper and the creases it was crumpled into, as background layers to lay over the paper's
// colour and under whatever lies on it, so the objects on a page are clean of it. The crease photograph is laid at
// a size of its own, so each strip is its own crumpled sheet and it moves with the strip.
const GRAIN = {
  image: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='320' height='320'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.15 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"), url('/photos/crumple-soft.jpg')`,
  size: '320px 320px, 1800px auto',
  blend: 'multiply, soft-light',
}
/** A paper surface: the grain over an optional tile of the paper itself, all over the element's own colour. */
const grained = (paper?: Paper): CSSProperties => ({
  backgroundImage: paper ? `${GRAIN.image}, url(${paper.src})` : GRAIN.image,
  backgroundSize: paper ? `${GRAIN.size}, ${paper.size}px` : GRAIN.size,
  backgroundBlendMode: paper ? `${GRAIN.blend}, normal` : GRAIN.blend,
})

// A page's frame: its margins and type.
const PAGE = '@container relative flex min-h-full flex-col pr-[clamp(1rem,2.6vw,3rem)] py-[2.4vh] text-[clamp(14px,0.35vw+1.1vh,19px)] leading-[1.5]'
const slide = { type: 'spring', stiffness: 150, damping: 21, mass: 1 } as const
const instant = { duration: 0 } as const

const stripStyle = (tone: Omit<Tone, 'tab'>, slot: number, z: number, extra: Record<string, string | number> = {}): CSSProperties => {
  return {
    '--band': tone.band,
    '--band-ink': tone.bandInk,
    '--panel': tone.panel,
    '--panel-ink': tone.panelInk,
    '--paper': tone.panel,
    '--ink': tone.panelInk,
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
  /** The tab is cut from the page's paper, which the panel draws under it (SiteShell's sheet), so it is clear here. */
  paper?: boolean
  /** The tab's cut, rendered (studio/tabcut): where its render lies, in pixels from the tab's top left. */
  cut: TabCut
}

/** A rendered cut over a tab: the light and shadow of its edge, and where that lies from the tab's top left. */
type TabCut = {
  src: string
  left: number
  top: number
  width: number
  height: number
}

/**
 * The outline of a folder tab, as the reference cuts it: it leaves the strip's edge on a slant, runs
 * straight down and slants back in, with every corner eased. Its foot is the length of band it grows out of, when
 * the band shows. A footless tab can lap this far back over the strip. Returns the path and how far its joins reach.
 */
const tabOutline = ({ band, protrude, height }: TabShape, footless = false, overlap = 0) => {
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
  const foot = footless ? band - overlap : 0
  return { reach, path: `M${foot} ${-reach} L${band} ${-reach} ${turns.join(' ')} L${band} ${height + reach} L${foot} ${height + reach} Z` }
}

const Tab = ({ label, shape, to, search, current, src, footless, leather, surface, paper, cut: edge }: TabProps) => {
  // A leather tab laps a pixel back over its strip, so the two never meet edge to edge, where each would let
  // through a little of what is under both and the seam would show as a line.
  const { reach, path } = tabOutline(shape, footless, leather ? 1 : 0)
  const hide = useId()
  const cut = useId()
  const width = shape.band + shape.protrude
  const margin = (tabMargin * width) / tabSpan
  const inside = (
    <>
      {leather ? (
        // The leather is the mat's, so it is in the mat's light. The mat lends that where its map of the light
        // lies (mat/mat.tsx). The leather and its light are cut out together, at one edge: cut apart, the edge
        // would show the leather unlit.
        <div
          aria-hidden
          className="pointer-events-none absolute left-0 isolate"
          style={{ top: -reach, width, height: shape.height + 2 * reach, clipPath: `url(#${cut})` }}
        >
          <svg width={width} height={shape.height + 2 * reach} className="absolute inset-0" viewBox={`0 ${-reach} ${width} ${shape.height + 2 * reach}`}>
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
            <rect y={-reach} width={width} height={shape.height + 2 * reach} fill={`url(#${hide})`} />
          </svg>
          {/* The map multiplies on white in its own group, and the whole multiplies the leather. */}
          <div data-mat-light className="absolute inset-0 isolate bg-white mix-blend-multiply">
            <div
              className="absolute inset-0 bg-no-repeat mix-blend-multiply"
              style={{ backgroundColor: 'var(--light-rim, white)', backgroundImage: 'var(--light-image)', backgroundSize: 'var(--light-size)', backgroundPosition: 'var(--light-at)' }}
            />
          </div>
          {/* Where the lamp lights the leather brighter than it was photographed, the mat adds the rest of its light
              over it, and so does the tab. The ruler's band darkens that light too, so it comes in as dark here. */}
          <div
            data-mat-light
            className="absolute inset-0 bg-no-repeat opacity-84 mix-blend-plus-lighter"
            style={{ backgroundImage: 'var(--light-past)', backgroundSize: 'var(--light-size)', backgroundPosition: 'var(--light-at)' }}
          />
        </div>
      ) : (
        <svg
          aria-hidden
          className="tab-shape"
          width={width}
          height={shape.height + 2 * reach}
          viewBox={`0 ${-reach} ${width} ${shape.height + 2 * reach}`}
          style={{ top: -reach }}
        >
          {/* A tab cut from the page's own hide has the strip's hide laid under it (SiteShell's hideOver), so it is clear here. */}
          <path d={path} fill={surface || paper ? 'none' : undefined} />
        </svg>
      )}
      {/* The cut itself, rendered: the light its edge catches and turns from, and the shadow it leaves on the page
          below as the tab lifts off the folder. It is only light, so it lies over whatever the strip is made of. */}
      <img aria-hidden alt="" src={edge.src} draggable={false} className="tab-cut" style={{ left: edge.left, top: edge.top, width: edge.width, height: edge.height }} />
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

export const SiteShell = ({ children }: SiteShellProps) => {
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
  // The render of a tab's cut for this layout and the tab's height, in pixels.
  const tabCut = (slot: number): TabCut => {
    const { src, x, y, width, height } = tabcut[`${mobile ? 'phone' : 'wide'}-${tabHeights[slot]}` as keyof typeof tabcut]
    const rem = metrics.rem
    return { src, left: x * rem, top: y * rem, width: width * rem, height: height * rem }
  }
  // The tab of a strip whose page is a hide is cut from that hide: the same tile, anchored at the strip's top left as
  // the panel's is, laid over the strip and out past its edge and masked to the tab, so the hide runs on unbroken. The
  // mask is pinned to the layer's right edge, which is the tab's, however wide the strip is as it opens and folds.
  const hideOver = (i: number): CSSProperties => {
    const shape = tabShape(i + 1)
    const { reach, path } = tabOutline(shape)
    const w = shape.band + shape.protrude
    const h = shape.height + 2 * reach
    const outline = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 ${-reach} ${w} ${h}" preserveAspectRatio="none"><path d="${path}"/></svg>`
    return {
      width: `calc(100% + ${shape.protrude}px)`,
      backgroundImage: `url(${pageTones[i].surface})`,
      backgroundSize: `${HIDE} ${HIDE}`,
      backgroundPosition: '0 0',
      maskImage: `url("data:image/svg+xml,${encodeURIComponent(outline)}")`,
      maskSize: `${w}px ${h}px`,
      maskPosition: `right 0 top ${tabTops[i + 1] * metrics.rem - reach}px`,
      maskRepeat: 'no-repeat',
    }
  }
  // A page of paper is one sheet with its tab: the panel itself runs out past the strip's edge under the tab, and
  // is cut to the strip, its edge torn or cut as the strip's is, and to the tab's outline, so the tab is the same
  // piece of paper as the page, its tile and grain running on unbroken, with no join between them.
  const sheet = (i: number, { paper, plate }: Tone): CSSProperties => {
    const shape = tabShape(i + 1)
    // The outline with its foot, so the tab and the page overlap over the band and no hairline opens between them.
    const { reach, path } = tabOutline(shape)
    const w = shape.band + shape.protrude
    const h = shape.height + 2 * reach
    const outline = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 ${-reach} ${w} ${h}" preserveAspectRatio="none"><path d="${path}"/></svg>`
    // How far past the strip's edge its tear reaches, over the strip after it.
    const out = reachesOver(i) ? TEAR_WIDTH : tones[i].frayed ? FRAY_PAST : tones[i].deckled ? DECKLE_PAST : 0
    return {
      right: -shape.protrude,
      // The plate is 36 by 24 em (studio/linen.py), 3 by 2.
      ...(plate ? { backgroundImage: `url(${plate})`, backgroundSize: 'max(100vw, 150vh) auto', backgroundPosition: '0 0' } : grained(paper)),
      maskImage: `linear-gradient(#000, #000), var(--torn-core, linear-gradient(#000, #000)), url("data:image/svg+xml,${encodeURIComponent(outline)}")`,
      // The page runs a pixel into its edge's strip, so no hairline opens where they meet.
      maskSize: `calc(100% - ${shape.protrude - out + TEAR_WIDTH - 1}px) 100%, ${TEAR_WIDTH}px ${TEAR_LENGTH}px, ${w}px ${h}px`,
      maskPosition: `left 0 top 0, right ${shape.protrude - out}px top 0, right 0 top ${tabTops[i + 1] * metrics.rem - reach}px`,
      maskRepeat: 'no-repeat, repeat-y, no-repeat',
    }
  }
  // Each page's edge is torn its own way, and runs straight where its tab grows out of it, so the tab's
  // eased joins meet a straight edge. Open, the mat is laid from the edge of the strip before it, and it cannot
  // be laid any wider without moving everything on it, so that strip's tear reaches out over the mat instead.
  const reachesOver = (i: number) => Boolean(tones[i + 1]?.fills)
  const tears = tones.map((_, i) => {
    const shape = tabShape(i + 1)
    const top = tabTops[i + 1] * metrics.rem
    const { reach } = tabOutline(shape)
    const { frayed, deckled } = tones[i]
    if (frayed) return { '--torn-core': `url(${frayed})`, filter: 'none' } as CSSProperties
    if (deckled) return { '--torn-core': `url(${deckled})` } as CSSProperties
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
        className="fixed inset-0 overflow-hidden bg-[#1f1e1b]"
        style={{ '--band-w': `${band}px`, '--protrude': `${protrude}px` } as CSSProperties}
      >
        {!mobile && (
          <aside
            className="strip"
            style={{ ...stripStyle(spineTone, 0, stack + 1, { left: 0, width: spine }), ...torn(7, [], 'torn') }}
          >
            <div aria-hidden className="torn" style={grained()} />
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
              {tones[i].cast && (
                <div
                  aria-hidden
                  className="pointer-events-none absolute inset-y-0"
                  style={{
                    left: `calc(100% + ${FRAY_PAST - TEAR_WIDTH}px)`,
                    width: CAST_WIDTH,
                    backgroundImage: `url(${tones[i].cast})`,
                    backgroundSize: `${CAST_WIDTH}px ${TEAR_LENGTH}px`,
                    backgroundRepeat: 'repeat-y',
                  }}
                />
              )}
              <div
                className={`panel scroll-quiet overflow-x-hidden overflow-y-auto ${hangs(tones[i]) ? 'panel-hangs' : ''}`}
                style={sheets(tones[i]) ? sheet(i, tones[i]) : undefined}
              >
                {tones[i].surface && (
                  <div
                    aria-hidden
                    className="pointer-events-none absolute inset-0"
                    style={{
                      // Under the photograph of the set, which covers it: only a window taller than the photograph shows it.
                      backgroundImage: `url(${tones[i].surface})`,
                      backgroundSize: `${HIDE} ${HIDE}`,
                    }}
                  />
                )}
                {tones[i].hangs ? (
                  <Badge badge={profile.badge} page={openWidth} margin={band + protrude} open={open} past={protrude} />
                ) : tones[i].fills || tones[i].roll ? null : (
                  <motion.div
                    aria-hidden
                    className="absolute inset-y-0"
                    // A picture runs on under the strip before it as far as that strip's tear can bite, and out to its
                    // panel's edge past its own tear's reach, as the open page does, so no tear uncovers bare panel.
                    // The poster hands over to its page and back in the same frame, the two lying on each other, and its
                    // page hides and shows it (Poster, StripPoster), so it is always here, not faded.
                    style={{
                      ...(tones[i].bleeds ? { left: overlap - TEAR_WIDTH, width: folded(i) - overlap + TEAR_WIDTH + (reachesOver(i) ? TEAR_WIDTH : 0) } : { left: overlap, width: folded(i) - band - overlap }),
                      ...(tones[i].bleeds && workPoster ? { opacity: 1 } : {}),
                    }}
                    initial={false}
                    animate={tones[i].bleeds && workPoster ? undefined : { opacity: open ? 0 : 1 }}
                    // A picture page folds back into its strip's picture, which has to be there at once to take over.
                    transition={{ duration: tones[i].bleeds && !open ? 0 : 0.35 }}
                  >
                    <Art index={i} open={open} poster={workPoster} />
                  </motion.div>
                )}

                {tones[i].fills || tones[i].roll ? (
                  // The desk and the ticket are always here, open or folded, laid at the page's open width and pinned
                  // to the strip's edge: folded, the strip shows the edge of them beside the tab, and opening it only
                  // uncovers the rest where it lies. Neither is laid again, so whatever is on it stays as it was left.
                  <div className={PAGE} style={underTab(i)} inert={!open} aria-hidden={!open || undefined}>
                    <div className="grid flex-1 content-center py-[4vh]">
                      {open && children}
                      {tones[i].fills ? <Desk /> : <Ticket open={open} />}
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
              {pageTones[i].surface && <div aria-hidden className="pointer-events-none absolute inset-y-0 left-0 z-2" style={hideOver(i)} />}
              <Tab label={item.label} shape={tabShape(i + 1)} to={item.to} search={searchOf(item.to)} current={open} src={tones[i].tab} footless={hangs(tones[i])} leather={tones[i].fills} surface={tones[i].surface} paper={sheets(tones[i])} cut={tabCut(i + 1)} />
            </motion.section>
          )
        })}

        {!mobile && <div aria-hidden className="absolute inset-y-0 right-0 z-0 bg-[#1f1e1b]" style={{ width: end }} />}
        {!mobile && <Resume resume={profile.resume} room={metrics.height / metrics.rem} />}
      </motion.main>
    </MotionConfig>
  )
}
