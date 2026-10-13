import type { Like, Social } from '../../types'
import { BAKED, PROP, SKIN } from './classes'

type KeyBunchProps = {
  name: string
  career: string
  company: Social
  /** The sports cars like, which the car key stands for. */
  car: Like
}

/**
 * A bunch of keys: a stitched leather tag stamped in gold foil with the name and the work, and a red car key
 * on the same split ring. The words are in the render and are here for readers only. The company's name is
 * a link, laid over where the foil has it. The key stands for the sports cars like, which is told to screen
 * readers and printed nowhere.
 */
export function KeyBunch({ name, career, company, car }: KeyBunchProps) {
  return (
    <article data-prop="name" className={`${PROP} z-5 h-[9.625em] w-[30em] [--bleed:2] [--tall:0.8] stacked:[--k:0.93]`}>
      <i aria-hidden className={`${SKIN} bg-[url(/objects/mat/name.avif)]`} />
      <h2 className="sr-only">{name}</h2>
      <p>
        <span className="sr-only">{career} </span>
        <a
          href={company.href}
          target="_blank"
          rel="noreferrer"
          draggable={false}
          className={`${BAKED} absolute top-[7.15em] left-[6.9em] h-[1.35em] w-[4.45em] -rotate-3 overflow-hidden`}
        >
          {company.label}
        </a>
      </p>
      <p className="sr-only">
        {car.subject}: {car.title}. {car.note}
      </p>
    </article>
  )
}
