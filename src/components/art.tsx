import { StripHouse } from './strip-house'
import { StripPoster } from './strip-poster'

type ArtProps = {
  index: number
  /** Whether the strip is unfolded, with its page over the art. */
  open: boolean
  /** Whether the work page was last open as its poster, not its building, so its strip shows the poster folded. */
  poster?: boolean
}

/** Cropped decorative fragments shown on a folded strip. The first page has none: it shows its badge. The desk's
 * and the ticket's strips show the desk and the ticket themselves (SiteShell). */
export const Art = ({ index, open, poster }: ArtProps) => {
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

  if (index === 2) return poster ? <StripPoster open={open} /> : <StripHouse open={open} />

  return null
}
