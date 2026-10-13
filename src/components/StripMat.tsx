import { Rulers } from './mat/Rulers'

type PieceProps = {
  /** Where its middle lies on the strip and how wide it is, as classes. */
  place: string
  turn: number
  children: React.ReactNode
}

/** An object on the strip's mat. Its shadow falls the way the page's shadows do, however it is turned. */
function Piece({ place, turn, children }: PieceProps) {
  return (
    <span className={`absolute -translate-x-1/2 -translate-y-1/2 [filter:drop-shadow(-0.3px_0.5px_0.5px_rgb(30_16_0/0.3))_drop-shadow(-1.2px_1.8px_1.8px_rgb(46_26_0/0.16))] ${place}`}>
      <span className="flex" style={{ rotate: `${turn}deg` }}>
        {children}
      </span>
    </span>
  )
}

/**
 * The extras page's mat on a folded strip: its left edge, with the leather, the rulings and the rulers
 * where the page has them, so that the page opens out of the strip. The strip's panel has no frame, so the
 * mat runs on under the tab to the strip's edge. Three of the page's objects lie on it, at about the size
 * the page shows them.
 */
export function StripMat() {
  return (
    <div
      aria-hidden
      className="mat @container absolute inset-y-0 left-0 w-[calc(100%+var(--band-w))] overflow-hidden before:pointer-events-none before:absolute before:inset-0 before:bg-mat-grain before:bg-size-[220px_220px] before:opacity-20 before:mix-blend-multiply"
    >
      <Rulers cut />
      <Piece place="top-[9%] left-[40cqw] w-[34cqw]" turn={24}>
        <img src="/objects/mat/pick-fin.avif" alt="" draggable={false} className="w-full" />
      </Piece>
      <Piece place="top-[12.5%] left-[58cqw] w-[31cqw]" turn={-38}>
        <img src="/objects/mat/pick-wedge.avif" alt="" draggable={false} className="w-full" />
      </Piece>
      <Piece place="top-[42%] left-[42cqw] w-[102cqw]" turn={-80}>
        <img src="/objects/mat/ticket-stub.avif" alt="" draggable={false} className="w-[16.5%]" />
        <img src="/objects/mat/ticket-main.avif" alt="" draggable={false} className="w-[83.5%]" />
      </Piece>
      <Piece place="top-[76%] left-[52cqw] w-[97cqw]" turn={-56}>
        <img src="/objects/mat/razor.avif" alt="" draggable={false} className="w-full" />
      </Piece>
    </div>
  )
}
