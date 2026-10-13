import { PROP, SKIN } from './classes'

/** A Dunlop Tortex Fin, .60 mm. */
export function FinPick() {
  return (
    <div aria-hidden data-prop="pick-fin" className={`${PROP} z-0 h-[3.3em] w-[3.145em] [--bleed:0.6] [--k:1.6] [--tall:0.06]`}>
      <i className={`${SKIN} bg-[url(/objects/mat/pick-fin.avif)]`} />
    </div>
  )
}

/** A Dunlop Tortex Wedge, 1.0 mm. */
export function WedgePick() {
  return (
    <div aria-hidden data-prop="pick-wedge" className={`${PROP} z-0 h-[3.125em] w-[2.76em] [--bleed:0.6] [--k:1.6] [--tall:0.1]`}>
      <i className={`${SKIN} bg-[url(/objects/mat/pick-wedge.avif)]`} />
    </div>
  )
}
