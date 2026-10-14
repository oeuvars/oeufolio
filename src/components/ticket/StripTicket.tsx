/**
 * The contact page on a folded strip: a roll of the same ticket at a third of its size, joined edge to edge
 * where the bites of one meet the next and running off the top and bottom of the strip, photographed under the
 * same light as the ticket (studio/ticket/ticket.py). The page's ticket is the one torn off it.
 */
export function StripTicket() {
  return (
    <div aria-hidden className="absolute inset-0 flex items-center justify-center overflow-hidden">
      <img src="/objects/ticket-roll.avif" alt="" draggable={false} className="w-full max-w-none" />
    </div>
  )
}
