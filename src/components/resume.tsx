import { Link } from '@tanstack/react-router'

import type { Resume as ResumeData } from '../types'
import frame from './resume.json'
import { ResumeCat } from './resume-cat'

type ResumeProps = {
  resume: ResumeData
  /** The window's height, in rem. */
  room: number
  /** How far back along the strip the photograph and its roll are laid, in rem, for a strip too short to show the
   * roll where it lies: a phone's, which runs only the window's width (SiteShell). The cats lie where they would. */
  shift?: number
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
 * The strip of desk to the right of the folders, photographed (studio/resume): walnut under a satin lacquer, from
 * the top of the window down, with the resume lying on it, printed, rolled up and tied to a stamped tag. The roll and
 * the tag open the résumé page (/resume). The photograph runs a bleed past the strip on every side, out under the last folder, which
 * lies over the strip's first rem, and past the window's edge. Turkish Vans cut out of photographs taken from above lie
 * about the desk, each with the shadow the desk's lamp gives it (studio/resume/cats.py), so they can be spread over
 * whatever desk the window shows. The rigged ones breathe and move (resume-cat.tsx).
 */
export const Resume = ({ resume, room, shift = 0 }: ResumeProps) => {
  const [width, height] = frame.size
  const [left, top, linkWidth, linkHeight] = frame.link
  const bleed = frame.bleed

  return (
    <div className="absolute inset-y-0 right-0 z-0" style={{ width: `${width}rem`, backgroundColor: FOOT }}>
      <img
        alt=""
        src={resume.src}
        draggable={false}
        className="pointer-events-none absolute max-w-none select-none"
        style={{ left: `${-bleed}rem`, top: `${-bleed - shift}rem`, width: `${width + 2 * bleed}rem`, height: `${height + 2 * bleed}rem` }}
      />
      {spread(room).map((cat) => (
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
