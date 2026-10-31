/**
 * The work page's poster folded into its strip (studio/poster folded_film): a strip of old film as wide as the strip,
 * running on past its top and foot, its frames five of the poster's windows, with the sign's light laid down it. Its
 * holes and the white round it are clear, so the strip's paper shows through them. It is light printed on that paper,
 * as the page is, so it is laid over the paper as a screen. It fades into the poster as the strip opens, and back as
 * it folds (Fold).
 */
export const StripPoster = () => (
  // Half a tear in from either side: the picture runs a tear's width under the strip before it and past this strip's
  // own edge, and the film's outer edge is only as wide as half of that, so its holes always show.
  <div aria-hidden className="absolute inset-y-0 inset-x-2 mix-blend-screen">
    <img src="/objects/poster-strip.avif" alt="" draggable={false} className="size-full max-w-none object-cover select-none" />
  </div>
)
