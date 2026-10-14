import { StripHouse } from './StripHouse'
import { StripPoster } from './StripPoster'
import { StripTicket } from './ticket/StripTicket'

type ArtProps = {
  index: number
  /** Whether the strip is unfolded, with its page over the art. */
  open: boolean
  /** Whether the work page was last open as its poster, so its strip shows the poster folded. */
  poster?: boolean
}

/** Cropped decorative fragments shown on a folded strip. The first page has none: it shows its badge. The desk's
 * strip shows the desk itself (SiteShell). */
export function Art({ index, open, poster }: ArtProps) {
  if (index === 1) {
    // The letter's own drawings, date and signature, down the edge of its sheet (studio/letter.py).
    return (
      <img
        aria-hidden
        src="/objects/letter-strip.avif"
        alt=""
        className="absolute inset-x-0 top-[1.5%] h-[97%] w-full object-contain"
      />
    )
  }

  if (index === 2) return poster ? <StripPoster /> : <StripHouse open={open} />

  return <StripTicket />
}
