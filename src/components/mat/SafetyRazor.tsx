import { PROP, SKIN } from './classes'

/** A Merkur 23C safety razor in chrome, lying on one edge of its head with the knurled handle to the right. */
export function SafetyRazor() {
  return (
    <div aria-hidden data-prop="razor" className={`${PROP} z-2 h-[7.3em] w-[17.5em] [--bleed:1] [--tall:0.5]`}>
      <i className={`${SKIN} bg-[url(/objects/mat/razor.avif)]`} />
    </div>
  )
}
