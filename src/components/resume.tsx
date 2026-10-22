import { Link } from '@tanstack/react-router'

import type { Resume as ResumeData } from '../types'
import frame from './resume.json'
import { ResumeCat } from './resume-cat'

type ResumeProps = {
  resume: ResumeData
  /** The window's height, in rem. */
  room: number
  /** The strip is a phone's, which runs only the window's width (SiteShell): the roll is laid among the cats, with a
   * cat before it and as many after its tag as there is room for (along). */
  across?: boolean
  /** On a phone, where the last folder's tab stands up into the strip, in rem from its start: the first cat lies before
   * it and the roll after it, as on a wide screen the cat lies above the tab and the roll below. */
  clear?: [number, number]
}

// What the photograph's desk falls to at its foot, far from the lamp: the strip under a window taller than it.
const FOOT = '#0a0605'
// The least desk left between one cat and the next, and kept clear under the tag and at the window's foot, in rem.
const APART = 0.6

/**
 * Where the cats lie, as their tops in rem: the first above the last folder's tab, the rest under the tag, as many
 * as the window has room for, in order, with the desk left over shared out evenly between them.
 */
const spread = (room: number) => {
  const [first, ...rest] = frame.cats.laid
  const from = frame.link[1] + frame.link[3] + APART
  const space = room - APART - from
  const shown: typeof rest = []
  let used = 0
  for (const cat of rest) {
    if (used + cat.size[1] + shown.length * APART > space) break
    shown.push(cat)
    used += cat.size[1]
  }
  const gap = (space - used) / (shown.length + 1)
  let top = from + gap
  const laid = shown.map((cat) => {
    const at = top
    top += cat.size[1] + gap
    return { ...cat, top: at }
  })
  return [{ ...first, top: frame.cats.above - first.size[1] / 2 }, ...laid]
}

/**
 * On a phone's strip, which is only the window's width: a cat, the last folder's tab where it stands (clear), the roll
 * and its tag, and as many of the other cats as the strip has room for after the tag, in order, with the desk left
 * over shared out evenly between them. Returns the cats' tops and how far back the photograph is laid for the roll to
 * lie where it falls, in rem.
 */
const along = (room: number, [from, to]: [number, number]) => {
  const [first, ...rest] = frame.cats.laid
  const roll = frame.link[3]
  const shown: typeof rest = []
  let used = roll
  for (const cat of rest) {
    if (to + used + cat.size[1] + (shown.length + 2) * APART > room) break
    shown.push(cat)
    used += cat.size[1]
  }
  const gap = (room - to - used) / (shown.length + 2)
  const rollTop = to + gap
  let top = rollTop + roll + gap
  const laid = shown.map((cat) => {
    const at = top
    top += cat.size[1] + gap
    return { ...cat, top: at }
  })
  return { cats: [{ ...first, top: (from - first.size[1]) / 2 }, ...laid], shift: frame.link[1] - rollTop }
}

/** How much of the strip past the last folder's tab a phone's roll needs: the roll and its tag, with desk either side. */
export const RESUME_ROLL = frame.link[3] + 2 * APART

/**
 * The strip of desk to the right of the folders, photographed (studio/resume): walnut under a satin lacquer, from
 * the top of the window down, with the resume lying on it, printed, rolled up and tied to a stamped tag. The roll and
 * the tag open the résumé page (/resume). The photograph runs a bleed past the strip on every side, out under the last folder, which
 * lies over the strip's first rem, and past the window's edge. Turkish Vans cut out of photographs taken from above lie
 * about the desk, each with the shadow the desk's lamp gives it (studio/resume/cats.py), so they can be spread over
 * whatever desk the window shows. The rigged ones breathe and move (resume-cat.tsx).
 */
export const Resume = ({ resume, room, across = false, clear = [0, 0] }: ResumeProps) => {
  const [width, height] = frame.size
  const [left, top, linkWidth, linkHeight] = frame.link
  const bleed = frame.bleed
  const { cats, shift } = across ? along(room, clear) : { cats: spread(room), shift: 0 }

  return (
    <div className="absolute inset-y-0 right-0 z-0" style={{ width: `${width}rem`, backgroundColor: FOOT }}>
      <img
        alt=""
        src={resume.src}
        draggable={false}
        className="pointer-events-none absolute max-w-none select-none"
        style={{ left: `${-bleed}rem`, top: `${-bleed - shift}rem`, width: `${width + 2 * bleed}rem`, height: `${height + 2 * bleed}rem` }}
      />
      {cats.map((cat) => (
        <ResumeCat
          key={cat.src}
          src={cat.src}
          style={{
            left: `${cat.x - cat.size[0] / 2 - frame.cats.bleed}rem`,
            top: `${cat.top - frame.cats.bleed}rem`,
            width: `${cat.size[0] + 2 * frame.cats.bleed}rem`,
            height: `${cat.size[1] + 2 * frame.cats.bleed}rem`,
          }}
        />
      ))}
      <Link
        to="/resume"
        aria-label={resume.alt}
        className="absolute block rounded-sm focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-[#efe6cb]"
        style={{ left: `${left}rem`, top: `${top - shift}rem`, width: `${linkWidth}rem`, height: `${linkHeight}rem` }}
      />
    </div>
  )
}
