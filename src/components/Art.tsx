import { StripHouse } from './StripHouse'
import { StripMat } from './StripMat'

type ArtProps = {
  index: number
  /** Whether the strip is unfolded, with its page over the art. */
  open: boolean
}

/** Cropped decorative fragments shown on a folded strip. The first page has none: it shows its badge. */
export function Art({ index, open }: ArtProps) {
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

  if (index === 2) return <StripHouse open={open} />

  return <StripMat />
}
