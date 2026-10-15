import type { Resume as ResumeData } from '../types'
import frame from './resume.json'

type ResumeProps = {
  resume: ResumeData
}

// What the photograph's desk falls to at its foot, far from the lamp: the strip under a window taller than it.
const FOOT = '#0a0605'

/**
 * The strip of desk to the right of the folders, photographed (studio/resume): walnut under a satin lacquer, from
 * the top of the window down, with the resume lying on it, printed, rolled up and tied to a stamped tag. The roll and
 * the tag open the PDF. The photograph runs a bleed past the strip on every side, out under the last folder, which
 * lies over the strip's first rem, and past the window's edge.
 */
export function Resume({ resume }: ResumeProps) {
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
        style={{ left: `${-bleed}rem`, top: `${-bleed}rem`, width: `${width + 2 * bleed}rem`, height: `${height + 2 * bleed}rem` }}
      />
      <a
        href={resume.href}
        target="_blank"
        rel="noopener"
        aria-label={resume.alt}
        className="absolute block rounded-sm focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-[#efe6cb]"
        style={{ left: `${left}rem`, top: `${top}rem`, width: `${linkWidth}rem`, height: `${linkHeight}rem` }}
      />
    </div>
  )
}
