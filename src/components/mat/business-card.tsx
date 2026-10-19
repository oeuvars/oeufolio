import { PROP } from './classes'

type BusinessCardProps = {
  name: string
}

/** The business card, front up, under its acrylic slab. The print is in the plate. */
export function BusinessCard({ name }: BusinessCardProps) {
  return (
    <article data-prop="card" aria-label={`${name}'s business card`} className={`${PROP} z-2 h-[8.46em] w-[14.8em] [--k:1.3]`}>
      <p className="sr-only">{name}, with two birds and a car drawn over a strip of flowers.</p>
    </article>
  )
}
