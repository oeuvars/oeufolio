import { PROP, SKIN } from './classes'

/**
 * Apple's wired EarPods, left where they were dropped: the cable in the coil it was wound in, the two buds
 * out of the top of it and the USB-C plug at the end of its run.
 */
export function Earphones() {
  return (
    <div aria-hidden data-prop="earpods" className={`${PROP} z-2 h-[22.2em] w-[19.8em] [--bleed:1.2] [--tall:0.3]`}>
      <i className={`${SKIN} bg-[url(/objects/mat/earpods.avif)]`} />
    </div>
  )
}
