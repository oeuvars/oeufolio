import { PROP, SKIN } from './classes'

/**
 * A used tube of Proraso shaving soap lying crimp to the left, squeezed flat toward the crimp, with its
 * ribbed green cap screwed on.
 */
export function ShavingCream() {
  return (
    <div aria-hidden data-prop="proraso" className={`${PROP} z-2 h-[7.95em] w-[25.5em] [--bleed:1] [--tall:0.8]`}>
      <i className={`${SKIN} bg-[url(/objects/mat/proraso.avif)]`} />
    </div>
  )
}
