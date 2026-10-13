import type { Role } from '../types'
import { Still } from './Still'
import { Doodle } from './scenes/Doodle'
import { Furnishing } from './scenes/Furnishing'
import { Lift } from './scenes/Lift'

type FloorProps = {
  role: Role
  /** Its place down the building, which picks which side its room is on. */
  index: number
}

const papers = ['#f0c04f', '#cbb4dc', '#a9d6c2']

/** A blackboard that has been wiped a good many times: the sweep of the duster, and the dust it left. */
const slate =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='640' height='320'%3E%3Cfilter id='w' x='0' y='0' width='100%25' height='100%25'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.004 0.06' numOctaves='3' seed='7'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 1.1 0 0 0 -0.42'/%3E%3C/filter%3E%3Cfilter id='d' x='0' y='0' width='100%25' height='100%25'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.014' numOctaves='4' seed='3'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0.9 0 0 0 -0.3'/%3E%3C/filter%3E%3Cfilter id='g' x='0' y='0' width='100%25' height='100%25'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='1.1' numOctaves='2' seed='5'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0.5 0 0 0 -0.2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23w)' opacity='0.5'/%3E%3Crect width='100%25' height='100%25' filter='url(%23d)' opacity='0.45'/%3E%3Crect width='100%25' height='100%25' filter='url(%23g)' opacity='0.5'/%3E%3C/svg%3E\")"

/**
 * One job as a floor of the building, cut open: a furnished room, a long room with a blackboard on its
 * wall, and the lift's landing at the end. The job is chalked on the board the way a café chalks its menu:
 * the dates in a box with an arrow between them, the company in fat capitals, and at either end a drawing
 * of something from its trade. The rooms change sides from floor to floor, so no wall stands over another.
 * On a narrow sheet the board's room goes under the other two.
 */
export function Floor({ role, index }: FloorProps) {
  const flipped = index % 2 === 1
  const [from, to] = role.period.split(' to ')

  return (
    <article className={`grid grid-cols-[1fr_15cqw] gap-[1.3cqw] ${flipped ? '@md/box:grid-cols-[minmax(0,7.2fr)_minmax(0,2.8fr)_7cqw]' : '@md/box:grid-cols-[minmax(0,2.8fr)_minmax(0,7.2fr)_7cqw]'}`}>
      <div className={`relative aspect-[3/2] overflow-hidden @md/box:aspect-auto @md/box:min-h-[24cqw] ${flipped ? '@md/box:order-2' : '@md/box:order-1'}`}>
        <Still room={role.room} sign={role.org} />
      </div>
      <div className="relative overflow-hidden @md/box:order-3">
        <Lift open={index === 0} />
      </div>
      <div
        className={`relative col-span-2 flex items-center gap-[0.5em] border-b-[0.55em] border-[#5b3a2e] bg-(--paper) bg-[repeating-linear-gradient(90deg,rgb(255_255_255/0.2)_0_0.55em,transparent_0.55em_1.1em)] px-[0.7em] pt-[0.65em] pb-[0.55em] @md/box:col-span-1 ${flipped ? '@md/box:order-1 @md/box:flex-row-reverse' : '@md/box:order-2'}`}
        style={{ '--paper': papers[index % papers.length] } as React.CSSProperties}
      >
        <div className="relative min-w-0 flex-1 self-stretch bg-[#161514] bg-cover px-[0.9em] py-[0.55em] text-[#f5f1e6] shadow-[0.12em_0.2em_0_rgb(59_31_26/0.25)]" style={{ backgroundImage: slate }}>
          <div className="flex h-full items-center justify-center gap-[0.6em]">
            <div aria-hidden className="w-[2.7em] shrink-0 -rotate-6 [filter:url(#chalk-fine)]">
              <Doodle room={role.room} />
            </div>
            <div className="flex min-w-0 flex-col items-center text-center">
              <p className="flex rotate-1 items-center gap-[0.45em] rounded-[0.3em_0.55em_0.35em_0.5em] border-[0.13em] border-current px-[0.55em] pt-[0.12em] font-block text-[1.25em] leading-[1.15] tracking-[0.07em] whitespace-nowrap uppercase [filter:url(#chalk-fine)]">
                {from}
                {to && (
                  <>
                    <span className="sr-only">to</span>
                    <svg viewBox="0 0 30 12" aria-hidden className="h-[0.55em] w-auto" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M2 6.500c8-1 16 .5 25-.5M21 1.500l6 4.500-6 4.500" />
                    </svg>
                    {to}
                  </>
                )}
              </p>
              <h3 className="mt-[0.14em] -rotate-[1.5deg] font-block text-[3.2em] leading-[0.92] tracking-[0.02em] uppercase [filter:url(#chalk)]">{role.org}</h3>
            </div>
            <div aria-hidden className="w-[2.7em] shrink-0 rotate-6 [filter:url(#chalk-fine)]">
              <Doodle room={role.room} second />
            </div>
          </div>
        </div>
        <div aria-hidden className="-mb-[0.55em] hidden w-[5.5cqw] shrink-0 self-end @md/box:block">
          <Furnishing index={index} />
        </div>
      </div>
    </article>
  )
}
