import type { Like } from '../../types'
import { PROP } from './classes'

type KeyBunchProps = {
  name: string
  /** The sports cars like, which the car key stands for. */
  car: Like
}

/**
 * A bunch of keys: a stitched leather tag with the name blind stamped into it and Lacoste's crocodile on its
 * tab, and a red car key on the same split ring. All of it is in the plate. The key stands for the sports
 * cars like, which is told to screen readers and printed nowhere.
 */
export function KeyBunch({ name, car }: KeyBunchProps) {
  return (
    <article data-prop="name" className={`${PROP} z-5 h-[9.625em] w-[30em]`}>
      <h2 className="sr-only">{name}</h2>
      <p className="sr-only">
        {car.subject}: {car.title}. {car.note}
      </p>
    </article>
  )
}
