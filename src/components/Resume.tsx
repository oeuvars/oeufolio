import type { Resume as ResumeData } from '../types'
import frame from './resume.json'

type ResumeProps = {
  resume: ResumeData
}

/**
 * The resume, printed and rolled up, lying on the desk to the right of the folders with a tag tied to it
 * (studio/resume). It opens the PDF. Its frame is the desk's width, the last folder lying over the first rem
 * of it, and the render runs a bleed past the frame on every side for the shadow, out under the folder and
 * past the window's edge.
 */
export function Resume({ resume }: ResumeProps) {
  const [width, height] = frame.size
  const bleed = `${frame.bleed}rem`

  return (
    <a
      href={resume.href}
      target="_blank"
      rel="noopener"
      className="absolute right-0 z-0 block rounded-sm focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-[#efe6cb]"
      style={{ top: `${frame.top}rem`, width: `${width}rem`, height: `${height}rem` }}
    >
      <img
        alt={resume.alt}
        src={resume.src}
        draggable={false}
        className="pointer-events-none absolute max-w-none select-none"
        style={{ left: `-${bleed}`, top: `-${bleed}`, width: `calc(100% + 2 * ${bleed})`, height: `calc(100% + 2 * ${bleed})` }}
      />
    </a>
  )
}
