import { StripHouse } from './strip-house'
import { StripPoster } from './strip-poster'

type ArtProps = {
  index: number
  /** Whether the strip is unfolded, with its page over the art. */
  open: boolean
  /** Whether the work page was last open as its poster, not its building, so its strip shows the poster folded. */
  poster?: boolean
  /** On a phone, where the strip lies across the window, how deep the band it folds to shows, in px from its edge. */
  band?: number
}

/** Cropped decorative fragments shown on a folded strip. The first page has none: it shows its badge. The desk's
 * and the ticket's strips show the desk and the ticket themselves (SiteShell). */
export const Art = ({ index, open, poster, band }: ArtProps) => {
  if (index === 1 && band) {
    // The same drawings set side by side along the band (studio/letter.py), clear of the frayed linen lying over its foot.
    return (
      <img
        aria-hidden
        src="/objects/letter-band.avif"
        alt=""
        className="absolute left-1/2 max-w-[calc(100%-2rem)] -translate-x-1/2 object-contain"
        style={{ top: 1, height: band - 10 }}
      />
    )
  }

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
