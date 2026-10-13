import type { Role } from '../types'
import { Still } from './Still'
import { Furnishing } from './scenes/Furnishing'
import { Lift } from './scenes/Lift'

type FloorProps = {
  role: Role
  /** The floor's number, counted from the ground: the first job is part one. */
  part: number
  /** Its place down the building, which picks its room and which side that is on. */
  index: number
}

const papers = ['#f0c04f', '#cbb4dc', '#a9d6c2']

/**
 * One job as a floor of the building, cut open: a furnished room, a room with the job's notice hung on its
 * wall, and the lift's landing at the end. The rooms change sides from floor to floor, so no wall stands
 * over another. On a narrow sheet the notice's room goes under the other two.
 */
export function Floor({ role, part, index }: FloorProps) {
  const flipped = index % 2 === 1

  return (
    <article className={`grid grid-cols-[1fr_15cqw] gap-[1.3cqw] ${flipped ? '@md:grid-cols-[7fr_5fr_9cqw]' : '@md:grid-cols-[5fr_7fr_9cqw]'}`}>
      <div className={`relative aspect-[2/1] overflow-hidden @md:aspect-auto @md:min-h-[31cqw] ${flipped ? '@md:order-2' : '@md:order-1'}`}>
        <Still index={index} sign={role.org} />
      </div>
      <div className="relative overflow-hidden @md:order-3">
        <Lift part={part} open={index === 0} />
      </div>
      <div
        className={`relative col-span-2 flex items-center gap-[1.6cqw] border-b-[1.7cqw] border-[#5b3a2e] bg-(--paper) bg-[repeating-linear-gradient(90deg,rgb(255_255_255/0.2)_0_0.55em,transparent_0.55em_1.1em)] px-[2.2cqw] pt-[2.4cqw] pb-[1.6cqw] @md:col-span-1 ${flipped ? '@md:order-1 @md:flex-row-reverse' : '@md:order-2'}`}
        style={{ '--paper': papers[index % papers.length] } as React.CSSProperties}
      >
        <div className="min-w-0 flex-1 bg-cream px-[0.9em] py-[0.8em] text-cocoa shadow-[0_0_0_1.5px_var(--color-cocoa),0_0_0_0.3em_var(--color-cream),0_0_0_calc(0.3em+1.5px)_var(--color-cocoa),0.25em_0.4em_0_0.3em_rgb(59_31_26/0.18)]">
          <h3 className="text-[1.3em] leading-none font-extrabold tracking-[0.05em] text-brick uppercase [filter:url(#print-fine)]">{role.org}</h3>
          <p className="mt-[0.7em] flex flex-wrap gap-x-[0.8em] text-[0.66em] leading-[1.5] font-bold tracking-[0.2em] uppercase">
            <span className="whitespace-nowrap">{role.role}</span>
            <span className="whitespace-nowrap">
              <span aria-hidden className="mr-[0.8em]">★</span>
              {role.period}
            </span>
          </p>
          <p className="mt-[0.5em] text-[0.94em] leading-[1.35]">{role.summary}</p>
        </div>
        <div aria-hidden className="-mb-[1.6cqw] hidden w-[7cqw] shrink-0 self-end @md:block">
          <Furnishing index={index} />
        </div>
      </div>
    </article>
  )
}
