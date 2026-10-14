/**
 * The contact page on a folded strip: a length of old 35 mm film lying down the leather, both its ends curled up
 * into rolls, photographed under the same light as the ticket (studio/ticket/film.py). It is fitted to the strip
 * whole, so both rolls show.
 */
export function StripTicket() {
  return (
    <div aria-hidden className="absolute inset-0 flex items-center justify-center overflow-hidden">
      <img src="/objects/ticket-film.avif" alt="" draggable={false} className="size-full object-contain" />
    </div>
  )
}
