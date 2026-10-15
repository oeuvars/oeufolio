import contact from './contact.json'

const ACROSS = 8.4 // em across the strip (studio/ticket/scene.py's ACROSS)
const [X, Y, W, H] = contact.strip

/**
 * The contact page on a folded strip, composed for the strip as the letter's and the house's are: one photograph
 * (studio/ticket/scene.py strip) of a coil of the page's Indian stamps running down the red leather past both ends,
 * and the Leica from the page lying across it low down, its strap trailing up over the stamps, under the page's one
 * lamp. Its em is measured from the strip's middle down.
 */
export function StripTicket() {
  return (
    // The leather has no band beside it: the strip is leather to its torn edge, so the photograph is laid across all of
    // it, the band's width included, short of the tear.
    <div aria-hidden className="absolute inset-y-0 left-0 w-[calc(100%+var(--band-w)-12px)] overflow-hidden [container-type:size]">
      <div className="absolute inset-0" style={{ fontSize: `calc(100cqw / ${ACROSS})` }}>
        <img
          src="/objects/contact-strip.avif"
          alt=""
          draggable={false}
          className="absolute max-w-none"
          style={{ left: `${X}em`, top: `calc(50cqh + ${Y}em)`, width: `${W}em`, height: `${H}em` }}
        />
      </div>
    </div>
  )
}
