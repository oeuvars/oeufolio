import { Link, useNavigate, useRouterState } from '@tanstack/react-router'
import { MotionConfig, motion, useReducedMotion } from 'motion/react'
import type { CSSProperties, HTMLAttributes } from 'react'
import { useEffect, useId, useRef, useState } from 'react'

import { profile } from '../content'
import type { FoldKind, NavItem, VersionSearch } from '../types'
import { Art } from './art'
import { Badge } from './badge'
import { Fold, POSTER_SIGN } from './fold'
import { POSTER } from './house'
import { Letter } from './letter'
import { PosterPicture } from './poster'
import { Desk } from './mat/desk'
import { RESUME_ROW, Resume } from './resume'
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
  /** The strip is cut straight down its edge, not torn: a plain page, or a leather mat. */
  cut?: boolean
  /** The strip is cloth, cut down its edge with scissors: this mask of the cut, its weft ends frayed past it
   * (studio/linen.py --edge), in place of a straight cut. Cloth casts no drop shadow: it leaves its own (cast). */
  frayed?: string
  /** The shadow the cloth leaves on the page beyond its cut, rendered from the same mask (studio/linen.py --shadow):
   * a tile down the edge, CAST_WIDTH px wide from the mask's left, laid under the cloth and out over the next strip. */
  cast?: string
  /** What the strip's edge does to the light where it lies on the strip after it, rendered (studio/edgecast) in place of
   * a drop shadow: the shadow it leaves there, and its own cut's turn from the light and catch of it. A tile down the
   * edge, from EDGECAST_FROM px in over the strip to EDGECAST_SPAN px across, as long as the length it repeats over,
   * for each layout, as the edge is torn straight in a different place for each one's tab. A leather edge's light has a
   * tile of its own (light), laid over it in colour-dodge, so it brightens the leather and keeps its colour. */
  edgecast?: Record<'wide' | 'phone', string> & { length: number; light?: string }
  /** The strip is handmade paper, its edge the deckle the pulp stopped at, thinning to loose fibres, rendered fibre by
   * fibre (studio/paper/edge.py): the mask of it (edge), in place of a straight cut, and the shadow it leaves on the
   * strip after it (cast), in place of a drop shadow, for each layout, as the deckle runs on round its tab, which lies
   * in a different place for each. */
  deckled?: Record<'wide' | 'phone', { edge: string; cast: string }>
  /** The strip is printed paper torn by hand, rendered (studio/poster/tear.py): the mask its print is cut with (edge),
   * in place of a drawn tear, and the white paper the tear bares past the print, with its fibres (core), for each
   * layout, as the tear runs straight in a different place for each one's tab. Both, and its shadow (edgecast), lie
   * under the print. */
  tear?: Record<'wide' | 'phone', { edge: string; core: string }>
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
  /** The same piece for a phone, where the stack is turned on its side: its marks are turned a quarter the other way
   * (studio/tabs.py --turned), so they stand upright there. A piece whose marks read as well either way has none. */
  turnedTab?: string
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
// The cloth's tab, cut from it with the same scissors (studio/linentab.py), for each layout: the mask the tab is cut
// with and the render of its yarn ends and shadow, from the frayed mask's left and from the strip's top, in CSS px.
// The render takes over from the strip's own over CLOTH_TAB_HANDOVER px at either end, where the two are the same.
const CLOTH_TAB = {
  wide: { edge: '/objects/linen-tab-edge-wide.webp', cast: '/objects/linen-tab-wide.webp', top: 90, height: 268, width: 43, castWidth: 57 },
  phone: { edge: '/objects/linen-tab-edge-phone.webp', cast: '/objects/linen-tab-phone.webp', top: 217, height: 175, width: 26, castWidth: 40 },
}
const CLOTH_TAB_HANDOVER = 20
// Where a strip's rendered edge lies, from its edge, and how wide it runs (studio/edgecast FRAME).
const EDGECAST_FROM = -6
const EDGECAST_SPAN = 40
// The spine's, its tear biting further in (studio/edgecast SPINE_FRAME): its paper on the linen strip's card, as
// it lies there, in place of a drop shadow. It runs one tear's length down, and the spine has no tab to leave room for.
const SPINE_CAST: CSSProperties = {
  left: 'calc(100% - 16px)',
  width: 50,
  backgroundImage: 'url(/objects/spine-cast.webp)',
  backgroundSize: `50px ${TEAR_LENGTH}px`,
  backgroundRepeat: 'repeat-y',
}
// A handmade sheet's deckle mask runs round its tab too (studio/paper/edge.py): it begins DECKLE_IN px in from the
// strip's edge and runs out 9 px past the tab, this wide for each layout (edge_width).
const DECKLE_IN = 7
const DECKLE_WIDTH = { wide: 50, phone: 33 }
// Its shadow runs on this much further out (CAST_PAST).
const DECKLE_CAST_PAST = 8

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
  { band: '#ede3a1', bandInk: '#2e2418', panel: '#ede3a1', panelInk: '#2e2418', hangs: true, cut: true, frayed: '/objects/linen-edge.webp', cast: '/objects/linen-shadow.webp', plate: '/objects/linen.avif', tab: '/objects/tab-lacoste.avif', turnedTab: '/objects/tab-lacoste-turned.avif' },
  // The letter's handmade sheet (studio/paper), TILE in paper.py written at twice the size it is shown.
  { band: '#ebe7e1', bandInk: '#24242a', panel: '#ebe7e1', panelInk: '#24242a', cut: true, deckled: { wide: { edge: '/objects/likes-edge-wide.webp', cast: '/objects/likes-cast-wide.webp' }, phone: { edge: '/objects/likes-edge-phone.webp', cast: '/objects/likes-cast-phone.webp' } }, paper: { src: '/objects/likes-paper.avif', size: 768 }, tab: '/objects/tab-prs.avif', turnedTab: '/objects/tab-prs-turned.avif' },
  // The poster is paper torn down its edge, lying on the mat; the mat is leather 2.5 mm thick, lying on the contact hide.
  { band: '#1e2740', bandInk: '#f1e3c4', panel: '#1e2740', panelInk: '#f1e3c4', bleeds: true, edgecast: { wide: '/objects/poster-cast-wide.webp', phone: '/objects/poster-cast-phone.webp', length: TEAR_LENGTH }, tear: { wide: { edge: '/objects/poster-edge-wide.webp', core: '/objects/poster-core-wide.webp' }, phone: { edge: '/objects/poster-edge-phone.webp', core: '/objects/poster-core-phone.webp' } }, tab: '/objects/tab-teenage.avif', turnedTab: '/objects/tab-teenage-turned.avif' },
  { band: '#d9d4c2', bandInk: '#1e1d19', panel: '#236653', panelInk: '#0b1a15', fills: true, edgecast: { wide: '/objects/mat-cast.webp', phone: '/objects/mat-cast.webp', length: 1, light: '/objects/mat-cast-light.webp' }, tab: '/objects/tab-proraso.avif' },
  // The contact strip's hide is a leather mat too, cut straight and burnished as the green one is, lying on the walnut.
  { band: '#8a8b78', bandInk: '#20241a', panel: '#651415', panelInk: '#efe6cb', roll: true, cut: true, surface: '/objects/leather.avif', edgecast: { wide: '/objects/contact-cast.webp', phone: '/objects/contact-cast.webp', length: 1, light: '/objects/contact-cast-light.webp' }, tab: '/objects/tab-tagheuer.avif' },
]
// The hide's tile: the contact page's leather (studio/ticket/leather.py), the one texture its strip and tab are. It is
// TILE (8) em of the ticket's spread across, and the spread is 90vh tall for its 29.85 em (ticket/ticket.tsx), so the
// hide's grain is the size it was beside the ticket in the scene's photograph.
const HIDE = `calc(90vh * ${8 / 29.85})`
const tabTops = [5, 9, 4, 6.5, 8.5, 4.5]
// On a phone the badge's ring rises to the strip's edge its tab stands on (Badge), so the tab stands past the ring.
const phoneTabTops = [5, 16.5, 4, 6.5, 8.5, 4.5]
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
// How far of the way a tab pulled on a phone has to be taken for its strip to open when it is let go.
const PULL_OPENS = 0.3
// On a phone the résumé's desk runs across the window's top, at most this much its size.
const RESUME_LARGEST = 0.7
// The row of the page a folded phone strip shows, as a part of the way down the page laid for it: the card's name.
const FOLD_AT = { badge: 0.27 }
// The contact strip's folded band (studio/ticket/scene.py BAND): 22 rem along the strip and as deep as the strip shows.
const CONTACT_BAND = { long: '22rem', deep: '4.25rem' }
// The work strip's folded band: as deep as the strip shows, the poster's windows at its ends as tall as that lets them
// be, and its sign between them.
const POSTER_BAND = { deep: '3.875rem', windows: '3.25rem', sign: '13rem' }
// The desk strip's folded band: its plate as deep as the strip shows, in rem, on a mat deep enough to run on under the
// torn edge of the strip after it.
const DESK_BAND = { deep: 3.375, mat: '4.25rem' }
// How long the card's page laid for its folded phone strip is, as a part of how wide it is.
const FOLD_TALL = 1.7
// The letter's strip, whose band is its drawings (Art).
const LETTER = 1
// The card is laid for its strip at most this wide, in rem, so its name stays within the band on a wide phone.
const FOLD_CARD = 22.5
const instant = { duration: 0 } as const

const stripStyle = (tone: Omit<Tone, 'tab'>, slot: number, z: number, extra: Record<string, string | number> = {}, tops = tabTops): CSSProperties => {
  return {
    '--band': tone.band,
    '--band-ink': tone.bandInk,
    '--panel': tone.panel,
    '--panel-ink': tone.panelInk,
    '--paper': tone.panel,
    '--ink': tone.panelInk,
    '--tab-top': `${tops[slot]}rem`,
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
  /** The tab's cut, rendered (studio/tabcut): where its render lies, in pixels from the tab's top left. A deckled or a
   * frayed tab has none: its edge is its strip's own, deckle or fray, and so is its shadow. */
  cut?: TabCut
  /** On a phone the tab can be taken and pulled, to open its strip by hand (SiteShell's pull). */
  pull?: Pick<HTMLAttributes<HTMLElement>, 'onPointerDown' | 'onPointerMove' | 'onPointerUp' | 'onPointerCancel' | 'onClickCapture'>
}

/** A rendered cut over a tab: the light and shadow of its edge, and where that lies from the tab's top left. */
type TabCut = {
  src: string
  /** A leather cut's light, apart, laid over it in colour-dodge, so it brightens the leather and keeps its colour. */
  light?: string
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

const Tab = ({ label, shape, to, search, current, src, footless, leather, surface, paper, cut: edge, pull }: TabProps) => {
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
          {/* The mat copies the part of each map that lies under the tab onto its canvas. */}
          <div data-mat-light className="absolute inset-0 isolate bg-white mix-blend-multiply">
            <div className="absolute inset-0 mix-blend-multiply" style={{ backgroundColor: 'var(--light-rim, white)' }}>
              <canvas data-light="light" className="absolute inset-0 size-full" />
            </div>
          </div>
          {/* Where the lamp lights the leather brighter than it was photographed, the mat adds the rest of its light
              over it, and so does the tab. The ruler's band darkens that light too, so it comes in as dark here. */}
          <canvas data-mat-light data-light="past" className="absolute inset-0 size-full opacity-84 mix-blend-plus-lighter" />
          {/* The light the cut's edge catches brightens the leather and keeps its colour (colour-dodge), here inside
              its cut, where the leather lies under it to brighten. */}
          {edge?.light && (
            <img aria-hidden alt="" src={edge.light} draggable={false} className="tab-cut mix-blend-color-dodge" style={{ left: edge.left, top: edge.top + reach, width: edge.width, height: edge.height }} />
          )}
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
      {edge && <img aria-hidden alt="" src={edge.src} draggable={false} className="tab-cut" style={{ left: edge.left, top: edge.top, width: edge.width, height: edge.height }} />}
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
      style={{ height: shape.height, touchAction: pull ? 'none' : undefined }}
      {...pull}
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
  const tops = mobile ? phoneTabTops : tabTops
  const tabShape = (slot: number): TabShape => ({ band, protrude, height: (tabHeights[slot] * (band + protrude)) / tabSpan })
  // The render of a tab's cut for this layout and the tab's height, in pixels.
  // The mat's tab is its thick leather, and the contact strip's its hide, each of which has a render of its own.
  const tabCut = (slot: number, stuff?: 'leather' | 'hide'): TabCut => {
    const cut: { src: string; light?: string; x: number; y: number; width: number; height: number } =
      tabcut[`${mobile ? 'phone' : 'wide'}-${tabHeights[slot]}${stuff ? `-${stuff}` : ''}` as keyof typeof tabcut]
    const rem = metrics.rem
    return { src: cut.src, light: cut.light, left: cut.x * rem, top: cut.y * rem, width: cut.width * rem, height: cut.height * rem }
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
      backgroundPosition: pinnedToEdge(pageTones[i]) ? `right ${shape.protrude}px top 0` : '0 0',
      maskImage: `url("data:image/svg+xml,${encodeURIComponent(outline)}")`,
      maskSize: `${w}px ${h}px`,
      maskPosition: `right 0 top ${tops[i + 1] * metrics.rem - reach}px`,
      maskRepeat: 'no-repeat',
    }
  }
  // Where the render of a cloth's tab takes over from the strip's own render of its edge, and hands back: the strip's
  // fades out over CLOTH_TAB_HANDOVER px and the tab's in, at either end of the tab's.
  const clothTabHandover = (tab: boolean) => {
    const { top, height } = CLOTH_TAB[mobile ? 'phone' : 'wide']
    const [from, to] = tab ? [0, height] : [top, top + height]
    const [outside, inside] = tab ? ['transparent', '#000'] : ['#000', 'transparent']
    return `linear-gradient(${outside} ${from}px, ${inside} ${from + CLOTH_TAB_HANDOVER}px, ${inside} ${to - CLOTH_TAB_HANDOVER}px, ${outside} ${to}px)`
  }
  const clothTabCast = (): CSSProperties => {
    const tab = CLOTH_TAB[mobile ? 'phone' : 'wide']
    return {
      left: `calc(100% + ${FRAY_PAST - TEAR_WIDTH}px)`,
      top: tab.top,
      width: tab.castWidth,
      height: tab.height,
      backgroundImage: `url(${tab.cast})`,
      backgroundSize: '100% 100%',
      maskImage: clothTabHandover(true),
    }
  }
  // A handmade sheet's shadow, under its sheet, from where its deckle mask begins.
  const deckleCast = (deckled: NonNullable<Tone['deckled']>): CSSProperties => {
    const layout = mobile ? 'phone' : 'wide'
    const width = DECKLE_WIDTH[layout] + DECKLE_CAST_PAST
    return {
      left: `calc(100% - ${DECKLE_IN}px)`,
      width,
      backgroundImage: `url(${deckled[layout].cast})`,
      backgroundSize: `${width}px ${TEAR_LENGTH}px`,
      backgroundRepeat: 'repeat-y',
    }
  }
  // The tab's cut is leather when the tab is cut from a leather mat: the mat's own, or the hide the page lies on.
  const stuffOf = (tone: Tone) => (tone.fills ? 'leather' : tone.surface ? 'hide' : undefined)
  const hideLight = (i: number) => {
    const { light, left, top, width, height } = tabCut(i + 1, 'hide')
    if (!light) return null
    return (
      <img
        aria-hidden
        alt=""
        src={light}
        draggable={false}
        className="pointer-events-none absolute z-2 max-w-none mix-blend-color-dodge select-none"
        style={{ left: `calc(100% - ${band}px + ${left}px)`, top: tops[i + 1] * metrics.rem + top, width, height }}
      />
    )
  }
  // What a strip is made of is laid from the edge its page is pinned to, so the two move as one sheet. Laid from the
  // other end, the material would slide under the page each time the strip opened or folded, as one end moves and the
  // other does not. On a phone every page is pinned to its strip's edge, where its tab is (upright); on a wide screen the
  // badge, the desk and the ticket are (Badge, underTab), and the letter and the poster are laid from the strip's left.
  // layers is how many background layers the material has, each laid the same.
  const pinnedToEdge = (tone: Tone) => mobile || Boolean(tone.hangs || tone.fills || tone.roll)
  const laidFromEdge = (i: number, layers: number): CSSProperties =>
    pinnedToEdge(tones[i]) ? { backgroundPosition: Array.from({ length: layers }, () => `right ${overhang(i)}px top 0`).join(', ') } : {}
  // A page of paper is one sheet with its tab: the panel itself runs out past the strip's edge under the tab, and
  // is cut to the strip, its edge torn or cut as the strip's is, and to the tab's outline, so the tab is the same
  // piece of paper as the page, its tile and grain running on unbroken, with no join between them.
  const sheet = (i: number, { paper, plate, deckled, frayed }: Tone): CSSProperties => {
    const shape = tabShape(i + 1)
    // A cloth's tab is cut out of it with the same scissors (studio/linentab.py), so its mask is the cut round the tab.
    if (frayed) {
      const tab = CLOTH_TAB[mobile ? 'phone' : 'wide']
      const inset = TEAR_WIDTH - FRAY_PAST
      return {
        right: inset - tab.width,
        ...(plate ? { backgroundImage: `url(${plate})`, backgroundSize: 'max(100vw, 150vh) auto', backgroundPosition: '0 0' } : grained(paper)),
        ...laidFromEdge(i, plate ? 1 : paper ? 3 : 2),
        maskImage: `linear-gradient(#000, #000), var(--torn-core), url(${tab.edge})`,
        maskSize: `calc(100% - ${tab.width - 1}px) 100%, ${TEAR_WIDTH}px ${TEAR_LENGTH}px, ${tab.width}px ${tab.height}px`,
        maskPosition: `left 0 top 0, right ${tab.width - TEAR_WIDTH}px top 0, right 0 top ${tab.top}px`,
        maskRepeat: 'no-repeat, repeat-y, no-repeat',
      }
    }
    // A handmade sheet's deckle runs on round its tab, so its mask is the tab's outline as well as its edge.
    if (deckled) {
      const layout = mobile ? 'phone' : 'wide'
      const w = DECKLE_WIDTH[layout]
      return {
        right: DECKLE_IN - w,
        ...grained(paper),
        ...laidFromEdge(i, paper ? 3 : 2),
        maskImage: `linear-gradient(#000, #000), url(${deckled[layout].edge})`,
        maskSize: `calc(100% - ${w - 1}px) 100%, ${w}px ${TEAR_LENGTH}px`,
        maskPosition: 'left 0 top 0, right 0 top 0',
        maskRepeat: 'no-repeat, repeat-y',
      }
    }
    // The outline with its foot, so the tab and the page overlap over the band and no hairline opens between them.
    const { reach, path } = tabOutline(shape)
    const w = shape.band + shape.protrude
    const h = shape.height + 2 * reach
    const outline = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 ${-reach} ${w} ${h}" preserveAspectRatio="none"><path d="${path}"/></svg>`
    // How far past the strip's edge its tear reaches, over the strip after it.
    const out = reachesOver(i) ? TEAR_WIDTH : 0
    return {
      right: -shape.protrude,
      // The plate is 36 by 24 em (studio/linen.py), 3 by 2.
      ...(plate ? { backgroundImage: `url(${plate})`, backgroundSize: 'max(100vw, 150vh) auto', backgroundPosition: '0 0' } : grained(paper)),
      ...laidFromEdge(i, plate ? 1 : paper ? 3 : 2),
      maskImage: `linear-gradient(#000, #000), var(--torn-core, linear-gradient(#000, #000)), url("data:image/svg+xml,${encodeURIComponent(outline)}")`,
      // The page runs a pixel into its edge's strip, so no hairline opens where they meet.
      maskSize: `calc(100% - ${shape.protrude - out + TEAR_WIDTH - 1}px) 100%, ${TEAR_WIDTH}px ${TEAR_LENGTH}px, ${w}px ${h}px`,
      maskPosition: `left 0 top 0, right ${shape.protrude - out}px top 0, right 0 top ${tops[i + 1] * metrics.rem - reach}px`,
      maskRepeat: 'no-repeat, repeat-y, no-repeat',
    }
  }
  // Each page's edge is torn its own way, and runs straight where its tab grows out of it, so the tab's
  // eased joins meet a straight edge. Open, the mat is laid from the edge of the strip before it, and it cannot
  // be laid any wider without moving everything on it, so that strip's tear reaches out over the mat instead.
  const reachesOver = (i: number) => Boolean(tones[i + 1]?.fills)
  const tears = tones.map((_, i) => {
    const shape = tabShape(i + 1)
    const top = tops[i + 1] * metrics.rem
    const { reach } = tabOutline(shape)
    const { frayed, deckled, tear: tearOf } = tones[i]
    // A torn print's edge is rendered, and lies on the strip after it with its own shadow.
    if (tearOf) return { '--torn-core': `url(${tearOf[mobile ? 'phone' : 'wide'].edge})`, filter: 'none' } as CSSProperties
    if (frayed) return { '--torn-core': `url(${frayed})`, filter: 'none' } as CSSProperties
    // A handmade sheet's deckle is rendered lying on the strip after it, so it casts no drop shadow: it leaves its own.
    if (deckled) return { '--torn-core': `url(${deckled[mobile ? 'phone' : 'wide'].edge})`, filter: 'none' } as CSSProperties
    const edge = torn(31 + 17 * i, [[top - reach, top + shape.height + reach]], edgeOf(tones[i]), reachesOver(i))
    // An edge rendered as it lies on the next strip casts no drop shadow: it leaves its own (edgecast).
    return tones[i].edgecast ? { ...edge, filter: 'none' } : edge
  })
  // A strip's rendered edge, laid down it over its own edge and out over the strip after it. Where its tab grows out,
  // the tab's cut is rendered with the edge beside it (studio/tabcut), fading out within the tab's joins as t ** 1.5
  // over 0.6 of their reach, so the strip's own fades in there as much.
  const edgecastOf = (i: number, cast: NonNullable<Tone['edgecast']>, src = cast[mobile ? 'phone' : 'wide'], fades = true): CSSProperties => {
    const shape = tabShape(i + 1)
    const top = tops[i + 1] * metrics.rem
    const { reach } = tabOutline(shape)
    const ramp = 0.6 * reach
    const steps = [0, 0.25, 0.5, 0.75, 1]
    const into = steps.map((t) => `rgb(0 0 0 / ${(1 - t ** 1.5).toFixed(3)}) ${(top - reach + t * ramp).toFixed(1)}px`)
    const out = steps.map((t) => `rgb(0 0 0 / ${(1 - (1 - t) ** 1.5).toFixed(3)}) ${(top + shape.height + reach - ramp + t * ramp).toFixed(1)}px`)
    // The lit rim stops square at the tab's joins, where the tab's leather covers the strip's edge and its own rim
    // runs on at full (studio/tabcut): faded as the shadow is, neither showed along the joins.
    const square = `linear-gradient(#000 ${(top - reach).toFixed(1)}px, transparent 0 ${(top + shape.height + reach).toFixed(1)}px, #000 0)`
    return {
      left: `calc(100% + ${EDGECAST_FROM}px)`,
      width: EDGECAST_SPAN,
      backgroundImage: `url(${src})`,
      backgroundSize: `${EDGECAST_SPAN}px ${cast.length}px`,
      backgroundRepeat: 'repeat-y',
      maskImage: !fades ? undefined : src === cast.light ? square : `linear-gradient(#000 0, ${[...into, ...out].join(', ')})`,
    }
  }
  // On a phone the last strip leaves room past it for the desk the résumé lies on, which the last strip's tab stands out
  // over as it does on a wide screen. As there the roll lies clear of the tab, past it across the window, and the desk
  // is as large as lets the roll, its tag and two cats after it fit there, and no larger than RESUME_LARGEST.
  const lastTab = (() => {
    const shape = tabShape(count)
    const { reach } = tabOutline(shape)
    const from = tops[count] * metrics.rem - reach
    return [from, from + shape.height + 2 * reach]
  })()
  const resumeScale = Math.min(RESUME_LARGEST, (metrics.height - lastTab[1]) / metrics.rem / RESUME_ROW)
  const fixed = mobile ? spine + end * resumeScale : spine + end
  const gaps = mobile ? count : count + 1
  // A strip whose page is a picture is folded half as wide again, to give its own picture room. The ticket's
  // strip shows only its roll, so it folds narrower than the rest. On a phone every strip folds to one band, as
  // the dividers in a drawer do.
  const folds = (i: number) => (mobile ? strip : tones[i].bleeds ? 1.5 * strip : tones[i].roll ? contact : strip)
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

  // On a phone the stack is turned on its side, a quarter turn back, so that each strip lies across the window with
  // its tab standing up off its top edge, the first strip at the foot and in front, as dividers stand in a drawer.
  // Every edge, cut and shadow is the strip's own, turned with it. What lies on a strip is turned upright again.

  // How far a strip's panel runs on past its edge, under its tab or for its tear's reach.
  const overhang = (i: number) => {
    const tone = tones[i]
    if (!sheets(tone)) return 0
    if (tone.frayed) return CLOTH_TAB[mobile ? 'phone' : 'wide'].width - (TEAR_WIDTH - FRAY_PAST)
    if (tone.deckled) return DECKLE_WIDTH[mobile ? 'phone' : 'wide'] - DECKLE_IN
    return protrude
  }
  // A page upright on its turned strip: as wide as the window and as tall as the strip is open, its top at the strip's
  // edge, so the strip opening uncovers it downward and folding covers it again from below, and nothing on it moves.
  // A phone page is never scrolled: it is laid to fit between its margins, the room it is given (--page-room).
  const upright: CSSProperties = { position: 'absolute', top: 0, left: '100%', width: metrics.height, transformOrigin: '0 0', transform: 'rotate(90deg)' }
  // The foot of an open page that the strip before lies over, its edge and its tab, kept clear.
  const under = (i: number) => (i > 0 ? overlap + protrude : overlap)
  // A page's margins on a phone: clear of its own edge's tear at its top, and of the strip before at its foot. The desk
  // and the ticket lie on a mat cut straight, so they run up to its edge. The desk's mat is the strip itself, so it runs
  // on to the strip's end, under the strip before and its tab, as it does on a wide screen: stopped short of them, it
  // would leave a band of bare panel between its foot and the strip before.
  const marginsOf = (i: number) => {
    const covers = tones[i].fills || tones[i].roll
    return { top: covers ? 0 : TEAR_WIDTH + 12, foot: tones[i].fills ? 0 : under(i) + (covers ? 0 : 12) }
  }
  const uprightOf = (i: number): CSSProperties => {
    const { top, foot } = marginsOf(i)
    return { ...upright, height: openWidthOf(i), '--page-top': `${top}px`, '--page-foot': `${foot}px`, '--page-room': `${openWidthOf(i) - top - foot}px` } as CSSProperties
  }
  // A page laid upright along a folded phone strip, slid so its row `at` (a part of the way down it) lies in the middle
  // of what shows of the strip: past the strip before and its tab, and short of the band the strip's own tab stands on.
  const foldCard = Math.min(metrics.height, FOLD_CARD * metrics.rem)
  const foldBand = (i: number, at: number, height?: number): CSSProperties =>
    ({
      ...upright,
      height,
      '--page-room': '200vh',
      transform: `rotate(90deg) translateY(calc(${(strip + band - under(i)) / 2}px - ${at * 100}%))`,
    }) as CSSProperties
  // Which way a folded phone strip's band grows into its page (Fold): the building, the work page's other version,
  // has no band of pieces, and only crosses over its strip's picture.
  const foldOf = (i: number): FoldKind | null =>
    tones[i].hangs ? 'badge' : i === LETTER ? 'letter' : tones[i].bleeds ? (workPoster ? 'poster' : null) : tones[i].fills ? 'desk' : tones[i].roll ? 'contact' : null
  const turnedPage = (i: number): CSSProperties => ({
    paddingLeft: '1rem',
    paddingRight: '1rem',
    paddingTop: marginsOf(i).top,
    paddingBottom: marginsOf(i).foot,
  })

  const lefts: number[] = []
  let cursor = spine - overlap
  for (let i = 0; i < count; i++) {
    lefts.push(cursor)
    cursor += (i === index ? openWidth : folded(i)) - overlap
  }
  const widths = profile.nav.map((_, i) => (i === index ? openWidth : folded(i)))

  // On a phone a tab can be taken and pulled to open its strip by hand. The stack is laid as it would be with that
  // strip open, and the pull carries it there as far as the finger has gone, along the strip edge that moves furthest
  // between the two: pulled past PULL_OPENS of the way, the strip opens, and short of it, the stack falls back. A phone
  // opens every strip to the room the others leave it, so the stack with a strip open is laid as roomFor says.
  const stackWith = (k: number) => {
    const sizes = profile.nav.map((_, i) => (i === k ? roomFor(k) : folds(i)))
    const at: number[] = []
    sizes.reduce((left, size) => (at.push(left), left + size - overlap), spine - overlap)
    return { lefts: at, widths: sizes }
  }
  const navigate = useNavigate()
  const [pulling, setPulling] = useState<{ k: number; amount: number } | null>(null)
  const pullRef = useRef<{ k: number; from: number; travel: number; amount: number; moved: boolean } | null>(null)
  // A pull let go is not a tap: the click that follows it is swallowed.
  const pulledOff = useRef(false)
  const pullOf = (k: number): TabProps['pull'] => {
    if (!mobile || k === index) return undefined
    return {
      onPointerDown: (event) => {
        if (event.button !== 0) return
        // Where each strip's edge lies on the window, from its top, now and with this strip open.
        const target = stackWith(k)
        const moves = lefts.map((left, i) => left + widths[i] - (target.lefts[i] + target.widths[i]))
        const travel = moves.reduce((most, move) => (Math.abs(move) > Math.abs(most) ? move : most), 0)
        pulledOff.current = false
        if (Math.abs(travel) < 1) return
        pullRef.current = { k, from: event.clientY, travel, amount: 0, moved: false }
        event.currentTarget.setPointerCapture(event.pointerId)
      },
      onPointerMove: (event) => {
        const pull = pullRef.current
        if (!pull) return
        const gone = event.clientY - pull.from
        if (!pull.moved && Math.abs(gone) < 6) return
        pull.moved = true
        pull.amount = Math.min(1, Math.max(0, gone / pull.travel))
        setPulling({ k: pull.k, amount: pull.amount })
      },
      onPointerUp: () => {
        const pull = pullRef.current
        pullRef.current = null
        if (!pull?.moved) return
        pulledOff.current = true
        setPulling(null)
        if (pull.amount >= PULL_OPENS) {
          const item = profile.nav[pull.k]
          navigate({ to: item.to, search: searchOf(item.to) })
        }
      },
      onPointerCancel: () => {
        pullRef.current = null
        setPulling(null)
      },
      onClickCapture: (event) => {
        if (!pulledOff.current) return
        pulledOff.current = false
        event.preventDefault()
        event.stopPropagation()
      },
    }
  }
  // The stack as the pull has it, between where it lies and where it would with the pulled strip open.
  const pulled = pulling && stackWith(pulling.k)
  const lerp = (from: number, to: number) => from + (to - from) * (pulling?.amount ?? 0)

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
        {/* On a phone the stack, turned on its side: its start at the window's foot, its depth across the window. */}
        <div
          className={mobile ? 'absolute top-0 left-0 origin-top-left' : 'contents'}
          style={mobile ? { width: metrics.width, height: metrics.height, transform: `translateY(${metrics.width}px) rotate(-90deg)` } : undefined}
        >
          {/* The spine, first in the stack and in front of it: on a phone, along the window's foot. */}
          <aside
            className="strip"
            style={{ ...stripStyle(spineTone, 0, stack + 1, { left: 0, width: spine }), ...torn(7, [], 'torn'), filter: 'none' }}
          >
            <div aria-hidden className="torn" style={grained()} />
            {/* A traffic signal printed in four colours, a rose, a sunflower with an eye and a lily pad for its
                lamps (studio/signal). It runs out to the tear, which cuts it as it cuts the paper, and its post runs on down
                past the foot of the strip, so a short window cuts it there. */}
            <Link to="/" aria-label={profile.handle} className="torn">
              <img alt="" src="/objects/signal.avif" draggable={false} className="size-full object-cover object-top mix-blend-multiply" />
            </Link>
            <div aria-hidden className="pointer-events-none absolute inset-y-0" style={SPINE_CAST} />
          </aside>
          {/* The desk past the last folder, with the résumé on it, turned with the stack, so it lies across the top. */}
          {mobile && (
            <div
              className="absolute top-0 right-0 z-0 origin-top-right"
              style={{ width: end, height: metrics.height / resumeScale, transform: `scale(${resumeScale})` }}
            >
              <Resume
                resume={profile.resume}
                room={metrics.height / metrics.rem / resumeScale}
                across
                clear={[lastTab[0] / metrics.rem / resumeScale, lastTab[1] / metrics.rem / resumeScale]}
              />
            </div>
          )}
          {profile.nav.map((item, i) => {
            const open = i === index

            return (
              <motion.section
                key={item.to}
                data-strip={i}
                className={`strip ${reachesOver(i) ? 'strip-reaches' : ''}`}
                initial={false}
                animate={pulled ? { left: lerp(lefts[i], pulled.lefts[i]), width: lerp(widths[i], pulled.widths[i]) } : { left: lefts[i], width: widths[i] }}
                transition={pulled ? instant : transition}
                style={{ ...stripStyle(tones[i], i + 1, stack - i, {}, tops), ...tears[i] }}
              >
                {/* A page that hangs covers its whole strip, so the strip has no paper of its own to show at the tear. */}
                {!hangs(tones[i]) && <div aria-hidden className="torn" />}
                {tones[i].cast && (
                  <>
                    <div
                      aria-hidden
                      className="pointer-events-none absolute inset-y-0"
                      style={{
                        left: `calc(100% + ${FRAY_PAST - TEAR_WIDTH}px)`,
                        width: CAST_WIDTH,
                        backgroundImage: `url(${tones[i].cast})`,
                        backgroundSize: `${CAST_WIDTH}px ${TEAR_LENGTH}px`,
                        backgroundRepeat: 'repeat-y',
                        maskImage: clothTabHandover(false),
                      }}
                    />
                    <div aria-hidden className="pointer-events-none absolute" style={clothTabCast()} />
                  </>
                )}
                {tones[i].deckled && <div aria-hidden className="pointer-events-none absolute inset-y-0" style={deckleCast(tones[i].deckled)} />}
                {/* A torn print's shadow and the paper its tear bares lie under the print, which its mask cuts back to its own line. */}
                {tones[i].tear && tones[i].edgecast && (
                  <>
                    <div aria-hidden className="pointer-events-none absolute inset-y-0" style={edgecastOf(i, tones[i].edgecast)} />
                    <div aria-hidden className="pointer-events-none absolute inset-y-0" style={edgecastOf(i, tones[i].edgecast, tones[i].tear[mobile ? 'phone' : 'wide'].core, false)} />
                  </>
                )}
                <div
                  className={`panel scroll-quiet overflow-x-hidden ${mobile ? 'overflow-y-hidden' : 'overflow-y-auto'} ${hangs(tones[i]) ? 'panel-hangs' : ''}`}
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
                        ...laidFromEdge(i, 1),
                      }}
                    />
                  )}
                  {mobile ? (
                    // The strip itself, short of its panel's overhang, so what lies on it upright is pinned to its edge.
                    <div className="absolute inset-y-0 left-0" style={{ right: overhang(i) }}>
                      {/* Folded, a strip shows a picture made for its band, upright and along it, every piece of it
                          whole and clear of the tabs over it: the contact set and the desk's things put down in a row,
                          the poster's sign between its windows, the letter's drawings. The card's band is its own page
                          laid again, still, and slid so its name lies in the middle of what the strip shows (FOLD_AT).
                          Open, it shows its page. Between the two, the band's pieces go to their places on the page
                          and back as the strip opens and folds (Fold), which shows one or the other once it is still. */}
                      {tones[i].roll ? (
                        // The set put down in a row along the strip for it (studio/ticket/scene.py band), laid in the
                        // strip's rem from its start, so its pieces fall clear of the tabs over it.
                        <div data-fold-band aria-hidden className="pointer-events-none" style={{ ...upright, height: CONTACT_BAND.deep }}>
                          <img src="/objects/contact-band.avif" alt="" draggable={false} className="absolute top-0 left-0 max-w-none select-none" style={{ width: CONTACT_BAND.long, height: CONTACT_BAND.deep }} />
                        </div>
                      ) : tones[i].fills ? (
                        // The desk's band plate, a few of the things on the desk put down in a row along the strip
                        // (studio/desk/desk.py --plate band), on the mat, which runs on under the strip's torn neighbour.
                        <div data-fold-band aria-hidden inert className="pointer-events-none" style={{ ...upright, height: DESK_BAND.mat }}>
                          <Desk band={DESK_BAND.deep * metrics.rem} grows />
                        </div>
                      ) : tones[i].hangs ? (
                        <div data-fold-band aria-hidden inert className="pointer-events-none" style={foldBand(i, FOLD_AT.badge, FOLD_TALL * foldCard)}>
                          <Badge badge={profile.badge} page={foldCard} margin={1.5 * metrics.rem} open={false} past={(metrics.height - foldCard) / 2} />
                        </div>
                      ) : tones[i].bleeds && workPoster ? (
                        <div data-fold-band aria-hidden className="pointer-events-none mix-blend-screen" style={{ ...upright, height: POSTER_BAND.deep }}>
                          {/* The poster's sign in one line over the windows it crosses on the poster, small enough to
                              lie between the tabs above and below it, between windows at the strip's two ends. Its
                              words and the windows behind them are laid apart, as light over light, for each goes to
                              its own place on the poster. */}
                          <div className="flex h-full items-center justify-between px-1.5">
                            <img src="/objects/poster-band-start.avif" alt="" draggable={false} className="w-auto max-w-none select-none" style={{ height: POSTER_BAND.windows }} />
                            <div className="relative" style={{ width: POSTER_BAND.sign, aspectRatio: `${POSTER_SIGN.size[0]} / ${POSTER_SIGN.size[1]}` }}>
                              {(['behind', 'human', 'experience'] as const).map((layer) => {
                                const [x, y, w, h] = POSTER_SIGN[layer]
                                const [across, down] = POSTER_SIGN.size
                                return (
                                  <img
                                    key={layer}
                                    src={`/objects/poster-band-${layer}.avif`}
                                    alt=""
                                    draggable={false}
                                    className="absolute max-w-none mix-blend-screen select-none"
                                    style={{ left: `${(100 * x) / across}%`, top: `${(100 * y) / down}%`, width: `${(100 * w) / across}%`, height: `${(100 * h) / down}%` }}
                                  />
                                )
                              })}
                            </div>
                            <img src="/objects/poster-band-end.avif" alt="" draggable={false} className="w-auto max-w-none select-none" style={{ height: POSTER_BAND.windows }} />
                          </div>
                        </div>
                      ) : i === LETTER ? (
                        <div data-fold-band aria-hidden style={uprightOf(i)}>
                          <Art index={i} open={open} band={strip - overlap} />
                        </div>
                      ) : (
                        // The building is laid as on a wide screen, turned with the strip, on what shows of it between
                        // the strip before and its tab and the band the strip's own tab stands on.
                        <motion.div
                          aria-hidden
                          style={{ position: 'absolute', top: 0, bottom: 0, left: under(i), width: strip - band - under(i) }}
                          initial={false}
                          animate={{ opacity: open ? 0 : 1 }}
                          transition={{ duration: open ? 0.35 : 0 }}
                        >
                          <Art index={i} open={open} poster={workPoster} band={strip - overlap} turned />
                        </motion.div>
                      )}
                      {tones[i].hangs ? (
                        // The ring runs up out of shot at the strip's edge, under its tab, and not on into the cloth the tab is cut from.
                        <div data-fold-page className="overflow-hidden" style={uprightOf(i)}>
                          <div data-page className="absolute inset-0 origin-top-left">
                            <Badge badge={profile.badge} page={metrics.height} margin={1.5 * metrics.rem} open={open} past={0} />
                          </div>
                        </div>
                      ) : tones[i].fills || tones[i].roll ? (
                        <div data-fold-page className="overflow-hidden" style={uprightOf(i)} inert={!open} aria-hidden={!open || undefined}>
                          <div className="grid min-h-full content-center" style={{ paddingBottom: marginsOf(i).foot }}>
                            {open && children}
                            {tones[i].fills ? <Desk grows /> : <Ticket />}
                          </div>
                        </div>
                      ) : open ? (
                        <div data-fold-page className="overflow-hidden" style={uprightOf(i)}>
                          <div className={PAGE} style={turnedPage(i)}>
                            <div className="grid flex-1 content-center">{children}</div>
                          </div>
                        </div>
                      ) : null}
                      {foldOf(i) && (
                        <Fold kind={foldOf(i)!} open={open} folded={folds(i)} opened={roomFor(i)} style={uprightOf(i)}>
                          {/* The letter's and the poster's pages are only here while they are open, so their pictures are
                              laid here as their pages lay them, for the pieces to land in. */}
                          {foldOf(i) === 'letter' ? (
                            <div className={PAGE} style={turnedPage(i)}>
                              <div className="grid flex-1 content-center">
                                <div>
                                  <Letter letter={profile.letter} />
                                </div>
                              </div>
                            </div>
                          ) : foldOf(i) === 'poster' ? (
                            <div className={PAGE} style={turnedPage(i)}>
                              <div className="grid flex-1 content-center">
                                <PosterPicture />
                              </div>
                            </div>
                          ) : null}
                        </Fold>
                      )}
                    </div>
                  ) : (
                    <>
                      {tones[i].hangs ? (
                        <Badge badge={profile.badge} page={openWidthOf(i)} margin={band + protrude} open={open} past={protrude} />
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
                            {tones[i].fills ? <Desk /> : <Ticket />}
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
                    </>
                  )}
                  {!open && <Link to={item.to} search={searchOf(item.to)} tabIndex={-1} aria-hidden className="absolute inset-0 z-10" style={mobile ? { touchAction: 'none' } : undefined} {...pullOf(i)} />}
                </div>
                {/* The ticket's leather is a photograph that runs to the tear, its own cut edge and wear in it, so it has none laid over it. */}
                {edgeOf(tones[i]) === 'worn' && !tones[i].surface && (
                  <>
                    <div aria-hidden className="torn-fray" />
                    <div aria-hidden className="torn torn-wear" />
                  </>
                )}
                {tones[i].edgecast && !tones[i].tear && <div aria-hidden className="pointer-events-none absolute inset-y-0" style={edgecastOf(i, tones[i].edgecast)} />}
                {tones[i].edgecast?.light && (
                  <div aria-hidden className="pointer-events-none absolute inset-y-0 mix-blend-color-dodge" style={edgecastOf(i, tones[i].edgecast, tones[i].edgecast.light)} />
                )}
                {pageTones[i].surface && <div aria-hidden className="pointer-events-none absolute inset-y-0 left-0 z-2" style={hideOver(i)} />}
                {/* The light a hide tab's cut catches brightens the hide laid over it here, outside the tab, which is
                    a layer of its own with nothing under it to brighten. */}
                {pageTones[i].surface && hideLight(i)}
                <Tab label={item.label} shape={tabShape(i + 1)} to={item.to} search={searchOf(item.to)} current={open} src={(mobile && tones[i].turnedTab) || tones[i].tab} footless={hangs(tones[i])} leather={tones[i].fills} surface={tones[i].surface} paper={sheets(tones[i])} cut={tones[i].deckled || tones[i].frayed ? undefined : tabCut(i + 1, stuffOf(tones[i]))} pull={pullOf(i)} />
              </motion.section>
            )
          })}
        </div>

        {!mobile && <div aria-hidden className="absolute inset-y-0 right-0 z-0 bg-[#1f1e1b]" style={{ width: end }} />}
        {!mobile && <Resume resume={profile.resume} room={metrics.height / metrics.rem} />}
      </motion.main>
    </MotionConfig>
  )
}
