import type { Work } from '../types'

type ShopProps = {
  work: Work
  /** Its place along the street, which picks its paint. */
  index: number
}

const paints = ['#b3291b', '#2f8f8a', '#c9862a', '#5a3566']

/**
 * One project as a shop on the building's ground floor: its name on the fascia, a striped awning with a
 * scalloped edge, and a lit window with what it is written up in it. The whole front is the link. Hovering
 * turns the lights up and lets the awning down a little.
 */
export function Shop({ work, index }: ShopProps) {
  return (
    <a
      href={work.href}
      target="_blank"
      rel="noreferrer"
      className="group flex h-full flex-col bg-(--paint) text-cocoa no-underline"
      style={{ '--paint': paints[index % paints.length] } as React.CSSProperties}
    >
      <span className="px-[0.5em] pt-[0.6em] pb-[0.5em] text-center text-[1.02em] leading-[1.05] font-extrabold tracking-[0.07em] text-cream uppercase">
        {work.title}
      </span>
      <span
        aria-hidden
        className="relative z-10 -mx-[0.25em] -mb-[0.9em] block h-[2.1em] origin-top bg-[repeating-linear-gradient(90deg,var(--paint)_0_0.8em,var(--color-cream)_0.8em_1.6em)] drop-shadow-[0_0.15em_0_rgb(59_31_26/0.35)] transition-transform duration-200 [mask:linear-gradient(#000_0_0)_top/100%_calc(100%-0.4em)_no-repeat,radial-gradient(circle_0.4em_at_0.4em_calc(100%-0.4em),#000_97%,#0000)_bottom_left/0.8em_100%_repeat-x] group-hover:scale-y-[1.12] motion-reduce:transition-none"
      />
      <span className="mx-[0.45em] flex flex-1 flex-col border-[0.2em] border-cocoa bg-[#f8e3a3] px-[0.6em] pt-[1.3em] pb-[0.5em] text-center transition-colors duration-200 group-hover:bg-[#fbd464] motion-reduce:transition-none">
        <span className="text-[0.86em] leading-[1.3]">{work.summary}</span>
        <span className="mono mt-auto pt-[0.6em] !text-[0.62em]">
          {work.category} · {work.year}
        </span>
      </span>
      <span aria-hidden className="h-[0.9em] bg-[linear-gradient(rgb(59_31_26/0.35),rgb(59_31_26/0.35))]" />
    </a>
  )
}
