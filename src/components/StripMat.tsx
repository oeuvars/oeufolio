import { Rulers } from './mat/Rulers'

/**
 * The extras page's mat on a folded strip: its left edge, with the leather, the rulings and the rulers
 * where the page has them, so that the page opens out of the strip. The strip's panel has no frame, so the
 * mat runs on under the tab to the strip's edge. What lies on it is a slice of the page's own tall plate,
 * the same photograph, at about the size the page shows it.
 */
export function StripMat() {
  return (
    <div
      aria-hidden
      className="mat @container absolute inset-y-0 left-0 w-[calc(100%+var(--band-w))] overflow-hidden before:pointer-events-none before:absolute before:inset-0 before:bg-mat-grain before:bg-size-[220px_220px] before:opacity-20 before:mix-blend-multiply"
    >
      <Rulers cut />
      <img src="/objects/mat/desk-tall.avif" alt="" draggable={false} className="absolute -top-[455cqw] -left-[15cqw] w-[222cqw] max-w-none" />
    </div>
  )
}
